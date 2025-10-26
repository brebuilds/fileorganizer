#!/usr/bin/env python3
"""
Performance Optimizer for File Organizer
Background indexing, caching, incremental search, lazy loading
"""

import os
import json
import threading
import queue
import time
from datetime import datetime, timedelta
from functools import lru_cache
import sqlite3


class PerformanceOptimizer:
    """Manages performance optimizations and background tasks"""
    
    def __init__(self, db):
        self.db = db
        self.indexing_queue = queue.Queue()
        self.search_cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.background_thread = None
        self.running = False
    
    # ===== Background Indexing =====
    
    def start_background_indexing(self):
        """Start background indexing thread"""
        if self.background_thread and self.background_thread.is_alive():
            return
        
        self.running = True
        self.background_thread = threading.Thread(target=self._background_indexer, daemon=True)
        self.background_thread.start()
    
    def stop_background_indexing(self):
        """Stop background indexing"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=2)
    
    def queue_file_for_indexing(self, filepath):
        """Add file to indexing queue"""
        self.indexing_queue.put(filepath)
    
    def _background_indexer(self):
        """Background thread that indexes files from queue"""
        from file_indexer import FileIndexer
        indexer = FileIndexer(self.db)
        
        while self.running:
            try:
                # Get file from queue with timeout
                filepath = self.indexing_queue.get(timeout=1)
                
                # Index the file
                try:
                    indexer.index_file(filepath)
                    print(f"✓ Indexed: {os.path.basename(filepath)}")
                except Exception as e:
                    print(f"✗ Error indexing {filepath}: {e}")
                
                self.indexing_queue.task_done()
                
                # Small delay to avoid overwhelming system
                time.sleep(0.1)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Background indexer error: {e}")
    
    # ===== Search Caching =====
    
    def cached_search(self, query, limit=50, ttl=None):
        """
        Search with caching
        Results are cached for faster repeated searches
        """
        if ttl is None:
            ttl = self.cache_timeout
        
        cache_key = f"{query}:{limit}"
        
        # Check cache
        if cache_key in self.search_cache:
            cached_data, cached_time = self.search_cache[cache_key]
            
            # Check if cache is still valid
            if (datetime.now() - cached_time).total_seconds() < ttl:
                return cached_data
        
        # Perform search
        results = self.db.search_files(query, limit=limit)
        
        # Cache results
        self.search_cache[cache_key] = (results, datetime.now())
        
        return results
    
    def clear_search_cache(self):
        """Clear search cache"""
        self.search_cache = {}
    
    def invalidate_cache_for_file(self, file_path):
        """Invalidate cache entries that might include this file"""
        # For now, just clear all cache when a file changes
        # Could be more sophisticated in future
        self.clear_search_cache()
    
    # ===== Incremental Search =====
    
    def incremental_search(self, query, limit=20, min_length=2):
        """
        Incremental search that returns results as you type
        Optimized for fast response with partial queries
        """
        if len(query) < min_length:
            return []
        
        # Use cached search for speed
        return self.cached_search(query, limit=limit, ttl=60)
    
    # ===== Lazy Loading =====
    
    def get_paginated_files(self, offset=0, limit=50, folder=None, order_by='modified_date'):
        """
        Get files with pagination (lazy loading)
        Loads files in chunks for better performance
        """
        cursor = self.db.conn.cursor()
        
        valid_orders = ['modified_date', 'filename', 'size', 'created_date']
        if order_by not in valid_orders:
            order_by = 'modified_date'
        
        if folder:
            cursor.execute(f"""
                SELECT id, path, filename, size, modified_date, ai_summary
                FROM files
                WHERE folder_location LIKE ? AND status = 'active'
                ORDER BY {order_by} DESC
                LIMIT ? OFFSET ?
            """, (f'{folder}%', limit, offset))
        else:
            cursor.execute(f"""
                SELECT id, path, filename, size, modified_date, ai_summary
                FROM files
                WHERE status = 'active'
                ORDER BY {order_by} DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        
        columns = ['id', 'path', 'filename', 'size', 'modified_date', 'ai_summary']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def get_file_count(self, folder=None):
        """Get total file count for pagination"""
        cursor = self.db.conn.cursor()
        
        if folder:
            cursor.execute("""
                SELECT COUNT(*) FROM files
                WHERE folder_location LIKE ? AND status = 'active'
            """, (f'{folder}%',))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM files
                WHERE status = 'active'
            """)
        
        return cursor.fetchone()[0]
    
    # ===== Database Optimization =====
    
    def optimize_database(self):
        """
        Optimize database performance
        Runs VACUUM, ANALYZE, and rebuilds indexes
        """
        cursor = self.db.conn.cursor()
        
        print("Optimizing database...")
        
        # Analyze query performance
        cursor.execute("ANALYZE")
        print("✓ Analyzed tables")
        
        # Rebuild FTS index
        cursor.execute("INSERT INTO files_fts(files_fts) VALUES('rebuild')")
        print("✓ Rebuilt full-text search index")
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        print("✓ Vacuumed database")
        
        self.db.conn.commit()
        
        print("Database optimization complete!")
    
    def get_database_stats(self):
        """Get database performance statistics"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        # Database size
        db_path = self.db.db_path
        stats['db_size_mb'] = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
        
        # Table sizes
        cursor.execute("""
            SELECT name, COUNT(*) as count
            FROM sqlite_master
            WHERE type = 'table'
            GROUP BY name
        """)
        stats['tables'] = dict(cursor.fetchall())
        
        # Index count
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type = 'index'
        """)
        stats['index_count'] = cursor.fetchone()[0]
        
        # Cache stats
        stats['search_cache_size'] = len(self.search_cache)
        stats['queue_size'] = self.indexing_queue.qsize()
        
        return stats
    
    # ===== Batch Operations =====
    
    def batch_index_folder(self, folder_path, batch_size=10, callback=None):
        """
        Index folder in batches for better performance
        
        Args:
            folder_path: Folder to index
            batch_size: Files per batch
            callback: Optional callback(progress, total)
        """
        from file_indexer import FileIndexer
        indexer = FileIndexer(self.db)
        
        # Get all files first
        all_files = []
        for root, dirs, files in os.walk(folder_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                if indexer.should_index_file(filepath):
                    all_files.append(filepath)
        
        total = len(all_files)
        indexed = 0
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = all_files[i:i + batch_size]
            
            for filepath in batch:
                try:
                    indexer.index_file(filepath)
                    indexed += 1
                except Exception as e:
                    print(f"Error indexing {filepath}: {e}")
            
            # Commit after each batch
            self.db.conn.commit()
            
            # Call progress callback
            if callback:
                callback(indexed, total)
            
            # Small delay between batches
            time.sleep(0.05)
        
        return indexed
    
    # ===== Preloading =====
    
    def preload_frequently_accessed(self):
        """Preload frequently accessed files into cache"""
        frequent = self.db.get_frequently_accessed_files(limit=50)
        
        # Cache in memory for faster access
        for file_info in frequent:
            cache_key = f"file:{file_info['path']}"
            self.search_cache[cache_key] = (file_info, datetime.now())
        
        return len(frequent)
    
    # ===== Cleanup =====
    
    def cleanup_old_cache(self, max_age_seconds=3600):
        """Remove old cache entries"""
        now = datetime.now()
        to_remove = []
        
        for key, (data, timestamp) in self.search_cache.items():
            if (now - timestamp).total_seconds() > max_age_seconds:
                to_remove.append(key)
        
        for key in to_remove:
            del self.search_cache[key]
        
        return len(to_remove)


if __name__ == "__main__":
    # Test performance optimizer
    from file_indexer import FileDatabase
    
    print("Testing Performance Optimizer...")
    
    db = FileDatabase()
    optimizer = PerformanceOptimizer(db)
    
    # Get database stats
    print("\n📊 Database Stats:")
    stats = optimizer.get_database_stats()
    print(f"DB Size: {stats['db_size_mb']:.2f} MB")
    print(f"Indexes: {stats['index_count']}")
    print(f"Cache entries: {stats['search_cache_size']}")
    print(f"Queue size: {stats['queue_size']}")
    
    # Test pagination
    print("\n📄 Testing Pagination:")
    page1 = optimizer.get_paginated_files(offset=0, limit=5)
    print(f"Page 1: {len(page1)} files")
    for file in page1:
        print(f"  - {file['filename']}")
    
    # Test cached search
    print("\n🔍 Testing Cached Search:")
    start = time.time()
    results1 = optimizer.cached_search("test", limit=10)
    time1 = time.time() - start
    print(f"First search: {len(results1)} results in {time1*1000:.2f}ms")
    
    start = time.time()
    results2 = optimizer.cached_search("test", limit=10)
    time2 = time.time() - start
    print(f"Cached search: {len(results2)} results in {time2*1000:.2f}ms")
    print(f"Speedup: {time1/time2 if time2 > 0 else 'infinite'}x")
    
    # Test background indexing
    print("\n⚙️  Starting background indexing...")
    optimizer.start_background_indexing()
    print("Background indexer running")
    
    # Add some files to queue (example)
    # optimizer.queue_file_for_indexing("/path/to/file")
    
    time.sleep(1)
    optimizer.stop_background_indexing()
    print("Background indexer stopped")
    
    db.close()
    print("\n✅ Performance optimizer test complete!")

