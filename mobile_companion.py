#!/usr/bin/env python3
"""
Mobile Companion API for File Organizer
API endpoints and utilities for mobile app integration
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
import hashlib


class MobileCompanion:
    """Handles mobile app integration and file sync"""
    
    def __init__(self, db):
        self.db = db
        self.upload_dir = os.path.expanduser("~/.fileorganizer/mobile_uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def upload_file(self, file_data, filename, device_id=None, metadata=None):
        """
        Upload a file from mobile device
        
        Args:
            file_data: File content (bytes or base64)
            filename: Original filename
            device_id: Device identifier
            metadata: Additional metadata from mobile
        
        Returns:
            {file_id, path, success}
        """
        try:
            # Decode if base64
            if isinstance(file_data, str):
                file_data = base64.b64decode(file_data)
            
            # Generate safe filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Index file
            from file_indexer import FileIndexer
            indexer = FileIndexer(self.db)
            file_id = indexer.index_file(file_path)
            
            # Add mobile metadata
            if file_id and metadata:
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    INSERT INTO mobile_sync_queue
                    (file_id, action, sync_date, synced, device_id)
                    VALUES (?, 'upload', ?, 1, ?)
                """, (file_id, datetime.now().isoformat(), device_id))
                self.db.conn.commit()
            
            return {
                'success': True,
                'file_id': file_id,
                'path': file_path,
                'size': len(file_data)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_for_mobile(self, file_id, include_content=False):
        """
        Get file info formatted for mobile app
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, path, filename, extension, size, modified_date,
                   ai_summary, ai_tags, project, mime_type
            FROM files
            WHERE id = ? AND status = 'active'
        """, (file_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        file_info = {
            'id': row[0],
            'filename': row[2],
            'extension': row[3],
            'size': row[4],
            'size_mb': row[4] / (1024 * 1024) if row[4] else 0,
            'modified_date': row[5],
            'summary': row[6],
            'tags': row[7].split(',') if row[7] else [],
            'project': row[8],
            'mime_type': row[9],
            'preview_url': f'/api/preview/{row[0]}'
        }
        
        # Include content for small text files
        if include_content and row[4] < 100000:  # < 100KB
            path = row[1]
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    
                    # Check if text file
                    if row[9] and 'text' in row[9]:
                        file_info['content'] = content.decode('utf-8', errors='ignore')
                    else:
                        # Return base64 for binary files
                        file_info['content_base64'] = base64.b64encode(content).decode('utf-8')
                except:
                    pass
        
        return file_info
    
    def search_for_mobile(self, query, limit=50):
        """Search optimized for mobile (lighter response)"""
        results = self.db.search_files(query, limit=limit)
        
        # Simplify response for mobile
        mobile_results = []
        for file in results:
            mobile_results.append({
                'id': file['id'],
                'filename': file['filename'],
                'summary': file['ai_summary'][:100] if file['ai_summary'] else None,
                'tags': file['ai_tags'].split(',')[:5] if file['ai_tags'] else [],
                'modified_date': file['modified_date'],
                'size_mb': round(file['size'] / (1024 * 1024), 2) if file['size'] else 0
            })
        
        return mobile_results
    
    def get_recent_files_for_mobile(self, limit=20):
        """Get recent files optimized for mobile"""
        recent = self.db.get_recent_files(limit=limit)
        
        mobile_results = []
        for file in recent:
            mobile_results.append({
                'id': file['id'],
                'filename': file['filename'],
                'summary': file['ai_summary'][:100] if file['ai_summary'] else None,
                'modified_date': file['modified_date'],
                'thumbnail_url': f'/api/thumbnail/{file["id"]}'
            })
        
        return mobile_results
    
    def get_sync_queue(self, device_id=None):
        """Get files pending sync to mobile"""
        cursor = self.db.conn.cursor()
        
        if device_id:
            cursor.execute("""
                SELECT msq.id, msq.file_id, msq.action, msq.sync_date,
                       f.filename, f.size
                FROM mobile_sync_queue msq
                JOIN files f ON msq.file_id = f.id
                WHERE msq.synced = 0 AND msq.device_id = ?
                ORDER BY msq.sync_date DESC
                LIMIT 100
            """, (device_id,))
        else:
            cursor.execute("""
                SELECT msq.id, msq.file_id, msq.action, msq.sync_date,
                       f.filename, f.size
                FROM mobile_sync_queue msq
                JOIN files f ON msq.file_id = f.id
                WHERE msq.synced = 0
                ORDER BY msq.sync_date DESC
                LIMIT 100
            """)
        
        queue = []
        for row in cursor.fetchall():
            queue.append({
                'queue_id': row[0],
                'file_id': row[1],
                'action': row[2],
                'sync_date': row[3],
                'filename': row[4],
                'size': row[5]
            })
        
        return queue
    
    def mark_synced(self, queue_id):
        """Mark a sync queue item as synced"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE mobile_sync_queue
            SET synced = 1
            WHERE id = ?
        """, (queue_id,))
        self.db.conn.commit()
    
    def add_to_sync_queue(self, file_id, action='download', device_id=None):
        """Add file to sync queue"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO mobile_sync_queue
            (file_id, action, sync_date, synced, device_id)
            VALUES (?, ?, ?, 0, ?)
        """, (file_id, action, datetime.now().isoformat(), device_id))
        self.db.conn.commit()
        return cursor.lastrowid
    
    def get_mobile_stats(self, device_id=None):
        """Get statistics for mobile app"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        # Total files
        cursor.execute("SELECT COUNT(*), SUM(size) FROM files WHERE status = 'active'")
        row = cursor.fetchone()
        stats['total_files'] = row[0]
        stats['total_size_mb'] = (row[1] or 0) / (1024 * 1024)
        
        # Recent files (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM files
            WHERE status = 'active'
              AND modified_date > datetime('now', '-7 days')
        """)
        stats['recent_files'] = cursor.fetchone()[0]
        
        # Files by type
        cursor.execute("""
            SELECT extension, COUNT(*) as count
            FROM files
            WHERE status = 'active'
            GROUP BY extension
            ORDER BY count DESC
            LIMIT 5
        """)
        stats['top_types'] = dict(cursor.fetchall())
        
        # Top tags
        cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 5
        """)
        stats['top_tags'] = dict(cursor.fetchall())
        
        # Uploads from this device
        if device_id:
            cursor.execute("""
                SELECT COUNT(*) FROM mobile_sync_queue
                WHERE device_id = ? AND action = 'upload'
            """, (device_id,))
            stats['device_uploads'] = cursor.fetchone()[0]
        
        return stats
    
    def quick_organize_suggestion(self):
        """
        Get quick organization suggestion for mobile
        (Lightweight version of suggestion engine)
        """
        cursor = self.db.conn.cursor()
        
        suggestions = []
        
        # Check Downloads folder
        cursor.execute("""
            SELECT COUNT(*) FROM files
            WHERE folder_location LIKE '%Downloads%'
              AND status = 'active'
        """)
        downloads_count = cursor.fetchone()[0]
        
        if downloads_count > 10:
            suggestions.append({
                'type': 'organize',
                'priority': 'high',
                'message': f'{downloads_count} files in Downloads',
                'action': 'organize_downloads'
            })
        
        # Check untagged files
        cursor.execute("""
            SELECT COUNT(*) FROM files
            WHERE (ai_tags IS NULL OR ai_tags = '')
              AND status = 'active'
              AND modified_date > datetime('now', '-7 days')
        """)
        untagged = cursor.fetchone()[0]
        
        if untagged > 5:
            suggestions.append({
                'type': 'tag',
                'priority': 'medium',
                'message': f'{untagged} recent files need tagging',
                'action': 'tag_files'
            })
        
        return suggestions[:3]  # Return top 3


if __name__ == "__main__":
    # Test mobile companion
    from file_indexer import FileDatabase
    
    print("Testing Mobile Companion API...")
    
    db = FileDatabase()
    mobile = MobileCompanion(db)
    
    # Get stats
    print("\n📊 Mobile Stats:")
    stats = mobile.get_mobile_stats()
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Recent (7 days): {stats['recent_files']}")
    
    if stats['top_types']:
        print("\nTop file types:")
        for ext, count in list(stats['top_types'].items())[:3]:
            print(f"  {ext}: {count} files")
    
    # Get recent files
    print("\n📱 Recent Files (mobile format):")
    recent = mobile.get_recent_files_for_mobile(limit=5)
    for i, file in enumerate(recent[:3], 1):
        print(f"{i}. {file['filename']} ({file['size_mb']}MB)")
    
    # Get suggestions
    print("\n💡 Quick Suggestions:")
    suggestions = mobile.quick_organize_suggestion()
    for sug in suggestions:
        print(f"[{sug['priority']}] {sug['message']}")
    
    # Check sync queue
    print("\n📤 Sync Queue:")
    queue = mobile.get_sync_queue()
    print(f"{len(queue)} items pending sync")
    
    db.close()
    print("\n✅ Mobile companion test complete!")

