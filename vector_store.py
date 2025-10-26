#!/usr/bin/env python3
"""
Vector Store for Semantic Search
Uses embeddings for similarity-based file discovery
Integrates with File Organizer's existing SQLite database
"""

import numpy as np
import json
import os
from pathlib import Path
import pickle


class VectorStore:
    """
    Lightweight vector store for semantic file search
    Uses sentence embeddings to find semantically similar files
    """
    
    def __init__(self, db_path=None):
        if db_path is None:
            config_dir = os.path.expanduser("~/.fileorganizer")
            os.makedirs(config_dir, exist_ok=True)
            db_path = os.path.join(config_dir, "vectors.pkl")
        
        self.db_path = db_path
        self.embeddings = {}  # file_id -> embedding vector
        self.metadata = {}    # file_id -> metadata dict
        
        # Load existing vectors if available
        self.load()
    
    def generate_embedding(self, text, method='simple'):
        """
        Generate embedding for text
        
        Methods:
        - 'simple': TF-IDF style (fast, no dependencies)
        - 'ollama': Use Ollama embeddings (requires ollama)
        """
        
        if method == 'simple':
            return self._simple_embedding(text)
        elif method == 'ollama':
            return self._ollama_embedding(text)
        else:
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text):
        """
        Simple embedding using character n-grams and word frequency
        Fast and no external dependencies
        """
        if not text:
            return np.zeros(128)
        
        text = text.lower()
        words = text.split()
        
        # Create a fixed-size vector
        vector = np.zeros(128)
        
        # Hash words into buckets
        for word in words[:50]:  # Limit to first 50 words
            hash_val = hash(word) % 128
            vector[hash_val] += 1
        
        # Add character n-grams for better semantic matching
        for i in range(len(text) - 2):
            trigram = text[i:i+3]
            hash_val = hash(trigram) % 128
            vector[hash_val] += 0.5
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def _ollama_embedding(self, text):
        """
        Use Ollama's embedding models for high-quality vectors
        Falls back to simple if Ollama unavailable
        """
        try:
            import ollama
            
            # Use Ollama's embedding model
            response = ollama.embeddings(
                model="nomic-embed-text",  # or "mxbai-embed-large"
                prompt=text[:1000]  # Limit text length
            )
            
            embedding = np.array(response['embedding'])
            return embedding
            
        except Exception as e:
            print(f"Ollama embedding failed, using simple: {e}")
            return self._simple_embedding(text)
    
    def add(self, file_id, text, metadata=None):
        """Add or update a file's embedding"""
        embedding = self.generate_embedding(text)
        
        self.embeddings[file_id] = embedding
        self.metadata[file_id] = metadata or {}
        
        # Auto-save after adding
        self.save()
    
    def search(self, query, top_k=10, min_similarity=0.1):
        """
        Search for similar files using cosine similarity
        
        Returns list of (file_id, similarity_score, metadata)
        """
        if not self.embeddings:
            return []
        
        query_embedding = self.generate_embedding(query)
        
        # Calculate similarities
        similarities = []
        for file_id, embedding in self.embeddings.items():
            similarity = self.cosine_similarity(query_embedding, embedding)
            
            if similarity >= min_similarity:
                similarities.append((
                    file_id,
                    float(similarity),
                    self.metadata.get(file_id, {})
                ))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def find_similar_files(self, file_id, top_k=5):
        """Find files similar to a given file"""
        if file_id not in self.embeddings:
            return []
        
        file_embedding = self.embeddings[file_id]
        
        similarities = []
        for other_id, embedding in self.embeddings.items():
            if other_id == file_id:
                continue
            
            similarity = self.cosine_similarity(file_embedding, embedding)
            similarities.append((
                other_id,
                float(similarity),
                self.metadata.get(other_id, {})
            ))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def remove(self, file_id):
        """Remove a file's embedding"""
        if file_id in self.embeddings:
            del self.embeddings[file_id]
        if file_id in self.metadata:
            del self.metadata[file_id]
        self.save()
    
    def save(self):
        """Save vectors to disk"""
        with open(self.db_path, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'metadata': self.metadata
            }, f)
    
    def load(self):
        """Load vectors from disk"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data.get('embeddings', {})
                    self.metadata = data.get('metadata', {})
            except Exception as e:
                print(f"Error loading vectors: {e}")
                self.embeddings = {}
                self.metadata = {}
    
    def get_stats(self):
        """Get statistics about the vector store"""
        return {
            'total_vectors': len(self.embeddings),
            'vector_dimension': len(next(iter(self.embeddings.values()))) if self.embeddings else 0,
            'storage_size_mb': os.path.getsize(self.db_path) / (1024*1024) if os.path.exists(self.db_path) else 0
        }


class VectorSearchIntegration:
    """Integrates vector search with existing File Organizer database"""
    
    def __init__(self, file_db, vector_store=None):
        self.file_db = file_db
        self.vector_store = vector_store or VectorStore()
    
    def index_file_content(self, file_id):
        """Create vector embedding for a file"""
        cursor = self.file_db.conn.cursor()
        cursor.execute("""
            SELECT path, filename, content_text, ai_summary, ai_tags
            FROM files WHERE id = ?
        """, (file_id,))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        path, filename, content, summary, tags = result
        
        # Combine all text for embedding
        text_parts = [filename]
        if content:
            text_parts.append(content[:2000])  # Limit content
        if summary:
            text_parts.append(summary)
        if tags:
            text_parts.append(tags)
        
        combined_text = " ".join(text_parts)
        
        # Create embedding
        self.vector_store.add(
            file_id,
            combined_text,
            metadata={
                'path': path,
                'filename': filename
            }
        )
        
        return True
    
    def index_all_files(self, limit=None):
        """Index all files in database"""
        cursor = self.file_db.conn.cursor()
        
        query = "SELECT id FROM files WHERE status = 'active'"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        file_ids = [row[0] for row in cursor.fetchall()]
        
        indexed = 0
        for file_id in file_ids:
            if self.index_file_content(file_id):
                indexed += 1
        
        return indexed
    
    def semantic_search(self, query, top_k=10):
        """Search files using semantic similarity"""
        # Get vector search results
        vector_results = self.vector_store.search(query, top_k=top_k)
        
        if not vector_results:
            return []
        
        # Enrich with database info
        enriched = []
        for file_id, similarity, metadata in vector_results:
            cursor = self.file_db.conn.cursor()
            cursor.execute("""
                SELECT filename, path, ai_summary, ai_tags, project, modified_date
                FROM files WHERE id = ?
            """, (file_id,))
            
            result = cursor.fetchone()
            if result:
                enriched.append({
                    'file_id': file_id,
                    'filename': result[0],
                    'path': result[1],
                    'ai_summary': result[2],
                    'ai_tags': result[3],
                    'project': result[4],
                    'modified_date': result[5],
                    'similarity': similarity
                })
        
        return enriched
    
    def find_related_files(self, file_path, top_k=5):
        """Find files related to a given file"""
        # Get file_id
        cursor = self.file_db.conn.cursor()
        cursor.execute("SELECT id FROM files WHERE path = ?", (file_path,))
        result = cursor.fetchone()
        
        if not result:
            return []
        
        file_id = result[0]
        
        # Find similar
        similar = self.vector_store.find_similar_files(file_id, top_k=top_k)
        
        # Enrich results
        enriched = []
        for other_id, similarity, metadata in similar:
            cursor.execute("""
                SELECT filename, path, ai_summary
                FROM files WHERE id = ?
            """, (other_id,))
            
            result = cursor.fetchone()
            if result:
                enriched.append({
                    'filename': result[0],
                    'path': result[1],
                    'ai_summary': result[2],
                    'similarity': similarity
                })
        
        return enriched


if __name__ == "__main__":
    print("🔍 Vector Store & Semantic Search")
    print("="*60)
    
    # Test vector store
    print("\n1️⃣  Testing Vector Store...")
    vs = VectorStore()
    
    # Add some test documents
    vs.add(1, "Python programming tutorial for beginners", {'filename': 'python_tutorial.pdf'})
    vs.add(2, "JavaScript web development guide", {'filename': 'js_guide.pdf'})
    vs.add(3, "Python data science with pandas", {'filename': 'pandas_intro.pdf'})
    vs.add(4, "Invoice from Acme Corporation", {'filename': 'invoice_2024.pdf'})
    
    print(f"   ✅ Added 4 test documents")
    print(f"   📊 Stats: {vs.get_stats()}")
    
    # Test search
    print("\n2️⃣  Testing Semantic Search...")
    query = "python programming"
    results = vs.search(query, top_k=3)
    
    print(f"   Query: '{query}'")
    print(f"   Results:")
    for file_id, similarity, metadata in results:
        print(f"      • {metadata.get('filename', 'unknown')} (similarity: {similarity:.3f})")
    
    # Test with actual database
    print("\n3️⃣  Testing Database Integration...")
    try:
        from file_indexer import FileDatabase
        
        db = FileDatabase()
        integration = VectorSearchIntegration(db, vs)
        
        stats = db.get_stats()
        print(f"   📁 Database has {stats['total_files']} files")
        
        # Index first 10 files
        print("   🔄 Indexing files...")
        indexed = integration.index_all_files(limit=10)
        print(f"   ✅ Indexed {indexed} files with vector embeddings")
        
        # Test semantic search
        if indexed > 0:
            print("\n   Testing semantic search on real files...")
            results = integration.semantic_search("project document", top_k=3)
            for r in results:
                print(f"      • {r['filename']} ({r['similarity']:.3f})")
        
        db.close()
        
    except Exception as e:
        print(f"   ⚠️  Database integration test skipped: {e}")
    
    print("\n" + "="*60)
    print("✅ Vector search ready!")
    print("\nFeatures:")
    print("  • Semantic similarity search")
    print("  • Find related files")
    print("  • No external dependencies (simple mode)")
    print("  • Optional Ollama integration for better embeddings")

