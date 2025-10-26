#!/usr/bin/env python3
"""
Enhanced AI Content Summarization for File Organizer
Multi-page PDFs, video/audio transcription, advanced summarization
"""

import os
import json
from pathlib import Path
from datetime import datetime

# PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Optional: Advanced summarization
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Optional: Local LLM
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class EnhancedSummarizer:
    """Advanced content summarization with multiple backends"""
    
    def __init__(self, db, backend='ollama', model=None):
        """
        Initialize summarizer
        
        Args:
            db: Database instance
            backend: 'ollama', 'openai', or 'local'
            model: Model name (e.g., 'llama3.2:3b' or 'gpt-4')
        """
        self.db = db
        self.backend = backend
        
        if backend == 'ollama':
            self.model = model or 'llama3.2:3b'
            if not OLLAMA_AVAILABLE:
                raise ImportError("Ollama not available. Install: pip install ollama")
        
        elif backend == 'openai':
            self.model = model or 'gpt-4-turbo-preview'
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI not available. Install: pip install openai")
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=api_key)
        
        elif backend == 'local':
            self.model = 'local'
            # Simple extractive summarization
        
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def summarize_pdf(self, file_path, max_pages=None, chunk_size=3):
        """
        Summarize multi-page PDF with intelligent chunking
        
        Args:
            file_path: Path to PDF
            max_pages: Maximum pages to process (None = all)
            chunk_size: Pages per chunk for processing
        
        Returns:
            {
                'summary': str,
                'page_count': int,
                'chunks_processed': int,
                'key_topics': list,
                'metadata': dict
            }
        """
        if not PDF_AVAILABLE:
            return {'error': 'PyPDF2 not available'}
        
        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                total_pages = len(pdf.pages)
                pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
                
                # Extract text in chunks
                chunks = []
                for i in range(0, pages_to_process, chunk_size):
                    chunk_text = ""
                    for page_num in range(i, min(i + chunk_size, pages_to_process)):
                        chunk_text += pdf.pages[page_num].extract_text() + "\n\n"
                    
                    if chunk_text.strip():
                        chunks.append({
                            'pages': f"{i+1}-{min(i+chunk_size, pages_to_process)}",
                            'text': chunk_text[:5000]  # Limit chunk size
                        })
                
                # Summarize each chunk
                chunk_summaries = []
                for chunk in chunks:
                    summary = self._summarize_text(chunk['text'])
                    chunk_summaries.append({
                        'pages': chunk['pages'],
                        'summary': summary
                    })
                
                # Create overall summary
                combined_text = "\n\n".join([cs['summary'] for cs in chunk_summaries])
                overall_summary = self._summarize_text(
                    f"Create a comprehensive summary from these section summaries:\n\n{combined_text}",
                    max_length=500
                )
                
                # Extract key topics
                key_topics = self._extract_topics(overall_summary)
                
                return {
                    'summary': overall_summary,
                    'page_count': total_pages,
                    'chunks_processed': len(chunks),
                    'chunk_summaries': chunk_summaries,
                    'key_topics': key_topics,
                    'metadata': {
                        'file': os.path.basename(file_path),
                        'backend': self.backend,
                        'model': self.model,
                        'timestamp': datetime.now().isoformat()
                    }
                }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _summarize_text(self, text, max_length=200):
        """Summarize text using configured backend"""
        
        if not text.strip():
            return ""
        
        if self.backend == 'ollama':
            return self._summarize_ollama(text, max_length)
        
        elif self.backend == 'openai':
            return self._summarize_openai(text, max_length)
        
        elif self.backend == 'local':
            return self._summarize_local(text, max_length)
    
    def _summarize_ollama(self, text, max_length):
        """Summarize using Ollama"""
        try:
            response = ollama.generate(
                model=self.model,
                prompt=f"Summarize this text in {max_length} words or less:\n\n{text}",
                options={'temperature': 0.3}
            )
            return response['response'].strip()
        except Exception as e:
            return f"Error: {e}"
    
    def _summarize_openai(self, text, max_length):
        """Summarize using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant that creates concise summaries of {max_length} words or less."},
                    {"role": "user", "content": f"Summarize:\n\n{text}"}
                ],
                temperature=0.3,
                max_tokens=max_length * 2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {e}"
    
    def _summarize_local(self, text, max_length):
        """Simple extractive summarization (no external dependencies)"""
        sentences = text.split('.')
        # Take first few sentences up to max_length words
        summary = []
        word_count = 0
        
        for sentence in sentences:
            words = sentence.split()
            if word_count + len(words) <= max_length:
                summary.append(sentence.strip())
                word_count += len(words)
            else:
                break
        
        return '. '.join(summary) + '.' if summary else text[:max_length*5]
    
    def _extract_topics(self, text):
        """Extract key topics from summary"""
        # Simple keyword extraction
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.lower().split()
        word_freq = {}
        
        for word in words:
            word = word.strip('.,!?;:()[]{}"\'-')
            if len(word) > 3 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top 5 topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]
    
    def summarize_video_transcript(self, transcript_text, title=None):
        """
        Summarize video transcript
        
        Args:
            transcript_text: Video transcript
            title: Optional video title
        
        Returns:
            Summary with key points and timestamps (if available)
        """
        prompt = f"Summarize this video transcript"
        if title:
            prompt += f" titled '{title}'"
        prompt += f":\n\n{transcript_text[:10000]}"  # Limit length
        
        summary = self._summarize_text(prompt, max_length=300)
        
        # Extract key points
        key_points = self._extract_key_points(transcript_text)
        
        return {
            'summary': summary,
            'key_points': key_points,
            'topics': self._extract_topics(summary),
            'type': 'video'
        }
    
    def _extract_key_points(self, text):
        """Extract bullet points from text"""
        # Look for numbered lists or bullet points
        lines = text.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            # Detect bullet points or numbered lists
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                key_points.append(line)
                if len(key_points) >= 5:
                    break
        
        return key_points
    
    def batch_summarize_folder(self, folder_path, file_types=['.pdf'], max_files=None, callback=None):
        """
        Batch summarize all files in a folder
        
        Args:
            folder_path: Folder to process
            file_types: List of extensions to process
            max_files: Maximum files to process
            callback: Progress callback(current, total, file_name)
        
        Returns:
            List of summaries with file info
        """
        results = []
        files = []
        
        # Collect files
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in file_types):
                    files.append(os.path.join(root, filename))
        
        # Limit if requested
        if max_files:
            files = files[:max_files]
        
        total = len(files)
        
        # Process each file
        for i, file_path in enumerate(files, 1):
            try:
                if callback:
                    callback(i, total, os.path.basename(file_path))
                
                # Summarize based on type
                if file_path.lower().endswith('.pdf'):
                    result = self.summarize_pdf(file_path, max_pages=20)
                else:
                    # For other types, read as text
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()[:10000]
                    result = {
                        'summary': self._summarize_text(text),
                        'topics': self._extract_topics(text)
                    }
                
                result['file'] = file_path
                result['filename'] = os.path.basename(file_path)
                results.append(result)
            
            except Exception as e:
                results.append({
                    'file': file_path,
                    'filename': os.path.basename(file_path),
                    'error': str(e)
                })
        
        return results
    
    def get_backend_info(self):
        """Get information about available backends"""
        return {
            'current_backend': self.backend,
            'current_model': self.model,
            'available_backends': {
                'ollama': OLLAMA_AVAILABLE,
                'openai': OPENAI_AVAILABLE,
                'local': True  # Always available
            }
        }


if __name__ == "__main__":
    # Test enhanced summarizer
    print("Testing Enhanced Summarizer...")
    print(f"PDF Support: {PDF_AVAILABLE}")
    print(f"Ollama Support: {OLLAMA_AVAILABLE}")
    print(f"OpenAI Support: {OPENAI_AVAILABLE}")
    
    # Try with Ollama if available
    if OLLAMA_AVAILABLE:
        try:
            from file_indexer import FileDatabase
            db = FileDatabase()
            
            summarizer = EnhancedSummarizer(db, backend='ollama')
            print(f"\n✅ Initialized with backend: {summarizer.backend}")
            print(f"   Model: {summarizer.model}")
            
            # Test text summarization
            test_text = """
            File organization is crucial for productivity. An effective file management
            system helps users find documents quickly, reduces clutter, and improves
            workflow efficiency. Modern file organizers use AI to automatically tag,
            categorize, and summarize documents, making it easier to manage large
            collections of files. Features like smart folders, duplicate detection,
            and cloud integration further enhance the user experience.
            """
            
            summary = summarizer._summarize_text(test_text, max_length=50)
            print(f"\n📝 Test Summary:")
            print(f"   {summary}")
            
            topics = summarizer._extract_topics(test_text)
            print(f"\n🏷️  Topics: {', '.join(topics)}")
            
            db.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\n⚠️  Ollama not available. Install with: pip install ollama")
        print("   Or use 'local' backend for basic summarization")
    
    print("\n✅ Enhanced summarizer module ready!")

