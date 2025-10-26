#!/usr/bin/env python3
"""
Bulk Operations
Perform actions on multiple files at once
"""

import os
import shutil
import re
from pathlib import Path
from datetime import datetime


class BulkOperations:
    """Perform bulk file operations"""
    
    def __init__(self, file_db):
        self.db = file_db
    
    def select_files(self, pattern=None, query=None, folder=None, file_ids=None):
        """
        Select files for bulk operation
        
        Args:
            pattern: Glob pattern (e.g., "*.pdf")
            query: Search query
            folder: Folder path
            file_ids: List of specific file IDs
        """
        cursor = self.db.conn.cursor()
        
        if file_ids:
            placeholders = ','.join('?' * len(file_ids))
            cursor.execute(f"""
                SELECT id, path, filename
                FROM files
                WHERE id IN ({placeholders})
                AND status = 'active'
            """, file_ids)
        
        elif pattern:
            # Convert glob pattern to SQL LIKE
            sql_pattern = pattern.replace('*', '%').replace('?', '_')
            cursor.execute("""
                SELECT id, path, filename
                FROM files
                WHERE filename LIKE ?
                AND status = 'active'
                AND hide_from_app = 0
            """, (sql_pattern,))
        
        elif query:
            cursor.execute("""
                SELECT id, path, filename
                FROM files
                WHERE (filename LIKE ? OR ai_tags LIKE ? OR ai_summary LIKE ?)
                AND status = 'active'
                AND hide_from_app = 0
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        elif folder:
            cursor.execute("""
                SELECT id, path, filename
                FROM files
                WHERE folder_location LIKE ?
                AND status = 'active'
                AND hide_from_app = 0
            """, (f'%{folder}%',))
        
        else:
            return []
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'id': row[0],
                'path': row[1],
                'filename': row[2]
            })
        
        return files
    
    def bulk_tag(self, files, tag, dry_run=True):
        """Add tag to multiple files"""
        cursor = self.db.conn.cursor()
        actions = []
        
        for file in files:
            # Get current tags
            cursor.execute("SELECT ai_tags FROM files WHERE id = ?", (file['id'],))
            current_tags = cursor.fetchone()[0] or ""
            
            if tag not in current_tags:
                new_tags = f"{current_tags}, {tag}" if current_tags else tag
                
                if not dry_run:
                    cursor.execute("""
                        UPDATE files SET ai_tags = ? WHERE id = ?
                    """, (new_tags, file['id']))
                
                actions.append({
                    'file': file['filename'],
                    'action': 'tag',
                    'tag': tag,
                    'applied': not dry_run
                })
        
        if not dry_run:
            self.db.conn.commit()
        
        return actions
    
    def bulk_move(self, files, destination, dry_run=True):
        """Move multiple files to destination"""
        os.makedirs(destination, exist_ok=True)
        cursor = self.db.conn.cursor()
        actions = []
        
        for file in files:
            source = file['path']
            dest_path = os.path.join(destination, file['filename'])
            
            # Handle conflicts
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(dest_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dest_path = f"{base}_{counter}{ext}"
            
            if not dry_run and os.path.exists(source):
                try:
                    shutil.move(source, dest_path)
                    
                    # Update database
                    cursor.execute("""
                        UPDATE files SET path = ?, folder_location = ? WHERE id = ?
                    """, (dest_path, destination, file['id']))
                    
                    actions.append({
                        'file': file['filename'],
                        'action': 'move',
                        'from': source,
                        'to': dest_path,
                        'success': True
                    })
                except Exception as e:
                    actions.append({
                        'file': file['filename'],
                        'action': 'move',
                        'error': str(e),
                        'success': False
                    })
            else:
                actions.append({
                    'file': file['filename'],
                    'action': 'move',
                    'from': source,
                    'to': dest_path,
                    'dry_run': True
                })
        
        if not dry_run:
            self.db.conn.commit()
        
        return actions
    
    def bulk_rename(self, files, pattern, dry_run=True):
        """
        Rename multiple files using a pattern
        
        Pattern supports:
        - {name} = original filename
        - {date} = current date
        - {n} = sequential number
        """
        cursor = self.db.conn.cursor()
        actions = []
        
        for i, file in enumerate(files, 1):
            old_name = file['filename']
            old_path = file['path']
            
            # Parse pattern
            name_without_ext = Path(old_name).stem
            ext = Path(old_name).suffix
            
            new_name = pattern
            new_name = new_name.replace('{name}', name_without_ext)
            new_name = new_name.replace('{date}', datetime.now().strftime("%Y-%m-%d"))
            new_name = new_name.replace('{n}', str(i))
            
            # Add extension if not in pattern
            if not new_name.endswith(ext):
                new_name += ext
            
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            
            if not dry_run and os.path.exists(old_path):
                try:
                    os.rename(old_path, new_path)
                    
                    # Update database
                    cursor.execute("""
                        UPDATE files SET path = ?, filename = ? WHERE id = ?
                    """, (new_path, new_name, file['id']))
                    
                    actions.append({
                        'old_name': old_name,
                        'new_name': new_name,
                        'success': True
                    })
                except Exception as e:
                    actions.append({
                        'old_name': old_name,
                        'error': str(e),
                        'success': False
                    })
            else:
                actions.append({
                    'old_name': old_name,
                    'new_name': new_name,
                    'dry_run': True
                })
        
        if not dry_run:
            self.db.conn.commit()
        
        return actions
    
    def bulk_delete(self, files, dry_run=True):
        """Delete multiple files"""
        cursor = self.db.conn.cursor()
        actions = []
        
        for file in files:
            if not dry_run:
                cursor.execute("""
                    UPDATE files SET status = 'deleted' WHERE id = ?
                """, (file['id'],))
            
            actions.append({
                'file': file['filename'],
                'action': 'delete',
                'applied': not dry_run
            })
        
        if not dry_run:
            self.db.conn.commit()
        
        return actions


if __name__ == "__main__":
    print("⚡ Bulk Operations")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    bulk = BulkOperations(db)
    
    # Example: Find all PDFs
    pdfs = bulk.select_files(pattern="*.pdf")
    print(f"\n📄 Found {len(pdfs)} PDF file(s)")
    
    # Example: Show what bulk tag would do
    if pdfs:
        actions = bulk.bulk_tag(pdfs[:3], "document", dry_run=True)
        print(f"\n💡 Bulk tag preview ({len(actions)} files):")
        for action in actions:
            print(f"   {action['file']} → add tag '{action['tag']}'")
    
    db.close()

