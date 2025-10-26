#!/usr/bin/env python3
"""
Bulk Operations Manager for File Organizer
Mass file operations with preview and undo capabilities
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import re


class BulkOperations:
    """Manages bulk file operations with safety features"""
    
    def __init__(self, db):
        self.db = db
    
    def preview_rename(self, file_ids, pattern, replacement=None, use_regex=False):
        """
        Preview bulk rename operation
        
        Args:
            file_ids: List of file IDs
            pattern: Search pattern
            replacement: Replacement string (or function for advanced renaming)
            use_regex: Use regex matching
        
        Returns:
            List of {file_id, old_name, new_name, old_path, new_path}
        """
        cursor = self.db.conn.cursor()
        
        placeholders = ','.join(['?' for _ in file_ids])
        cursor.execute(f"""
            SELECT id, path, filename, folder_location
            FROM files
            WHERE id IN ({placeholders})
              AND status = 'active'
        """, file_ids)
        
        files = cursor.fetchall()
        preview = []
        
        for file_id, path, filename, folder in files:
            # Generate new filename
            if use_regex:
                new_filename = re.sub(pattern, replacement or '', filename)
            else:
                new_filename = filename.replace(pattern, replacement or '')
            
            # Only include if name changes
            if new_filename != filename:
                new_path = os.path.join(folder, new_filename)
                preview.append({
                    'file_id': file_id,
                    'old_name': filename,
                    'new_name': new_filename,
                    'old_path': path,
                    'new_path': new_path,
                    'safe': not os.path.exists(new_path)  # Check if target exists
                })
        
        return preview
    
    def execute_rename(self, preview_items, dry_run=False):
        """
        Execute bulk rename based on preview
        
        Args:
            preview_items: Output from preview_rename()
            dry_run: If True, don't actually rename, just return what would happen
        
        Returns:
            {success: [], failed: [], operation_id: ...}
        """
        if dry_run:
            return {
                'success': [item['old_name'] + ' → ' + item['new_name'] for item in preview_items],
                'failed': [],
                'operation_id': None
            }
        
        cursor = self.db.conn.cursor()
        success = []
        failed = []
        
        # Save operation for undo
        operation_data = {
            'type': 'bulk_rename',
            'files': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for item in preview_items:
            try:
                # Check if target exists
                if not item['safe']:
                    failed.append({
                        'item': item,
                        'error': 'Target file already exists'
                    })
                    continue
                
                # Rename file
                os.rename(item['old_path'], item['new_path'])
                
                # Update database
                cursor.execute("""
                    UPDATE files
                    SET path = ?, filename = ?
                    WHERE id = ?
                """, (item['new_path'], item['new_name'], item['file_id']))
                
                success.append(item)
                operation_data['files'].append({
                    'file_id': item['file_id'],
                    'old_path': item['old_path'],
                    'new_path': item['new_path']
                })
                
            except Exception as e:
                failed.append({
                    'item': item,
                    'error': str(e)
                })
        
        # Save operation to database
        operation_id = None
        if success:
            cursor.execute("""
                INSERT INTO bulk_operations
                (operation_type, operation_date, files_affected, original_state, new_state, can_undo, completed)
                VALUES (?, ?, ?, ?, ?, 1, 1)
            """, (
                'rename',
                datetime.now().isoformat(),
                json.dumps([f['file_id'] for f in success]),
                json.dumps(operation_data),
                json.dumps({'success': len(success), 'failed': len(failed)}),
            ))
            operation_id = cursor.lastrowid
        
        self.db.conn.commit()
        
        return {
            'success': success,
            'failed': failed,
            'operation_id': operation_id
        }
    
    def preview_move(self, file_ids, destination_folder):
        """Preview bulk move operation"""
        cursor = self.db.conn.cursor()
        
        placeholders = ','.join(['?' for _ in file_ids])
        cursor.execute(f"""
            SELECT id, path, filename, folder_location
            FROM files
            WHERE id IN ({placeholders})
              AND status = 'active'
        """, file_ids)
        
        files = cursor.fetchall()
        preview = []
        
        # Ensure destination exists
        destination_folder = os.path.expanduser(destination_folder)
        
        for file_id, path, filename, folder in files:
            new_path = os.path.join(destination_folder, filename)
            
            preview.append({
                'file_id': file_id,
                'filename': filename,
                'old_path': path,
                'new_path': new_path,
                'old_folder': folder,
                'new_folder': destination_folder,
                'safe': not os.path.exists(new_path)
            })
        
        return preview
    
    def execute_move(self, preview_items, create_folder=True, dry_run=False):
        """Execute bulk move operation"""
        if dry_run:
            return {
                'success': [item['filename'] for item in preview_items],
                'failed': [],
                'operation_id': None
            }
        
        cursor = self.db.conn.cursor()
        success = []
        failed = []
        
        # Create destination folder if needed
        if create_folder and preview_items:
            dest = preview_items[0]['new_folder']
            os.makedirs(dest, exist_ok=True)
        
        operation_data = {
            'type': 'bulk_move',
            'files': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for item in preview_items:
            try:
                if not item['safe']:
                    failed.append({
                        'item': item,
                        'error': 'Target file already exists'
                    })
                    continue
                
                # Move file
                shutil.move(item['old_path'], item['new_path'])
                
                # Update database
                cursor.execute("""
                    UPDATE files
                    SET path = ?, folder_location = ?
                    WHERE id = ?
                """, (item['new_path'], item['new_folder'], item['file_id']))
                
                success.append(item)
                operation_data['files'].append({
                    'file_id': item['file_id'],
                    'old_path': item['old_path'],
                    'new_path': item['new_path']
                })
                
            except Exception as e:
                failed.append({
                    'item': item,
                    'error': str(e)
                })
        
        # Save operation
        operation_id = None
        if success:
            cursor.execute("""
                INSERT INTO bulk_operations
                (operation_type, operation_date, files_affected, original_state, new_state, can_undo, completed)
                VALUES (?, ?, ?, ?, ?, 1, 1)
            """, (
                'move',
                datetime.now().isoformat(),
                json.dumps([f['file_id'] for f in success]),
                json.dumps(operation_data),
                json.dumps({'success': len(success), 'failed': len(failed)}),
            ))
            operation_id = cursor.lastrowid
        
        self.db.conn.commit()
        
        return {
            'success': success,
            'failed': failed,
            'operation_id': operation_id
        }
    
    def preview_delete(self, file_ids, permanent=False):
        """Preview bulk delete operation"""
        cursor = self.db.conn.cursor()
        
        placeholders = ','.join(['?' for _ in file_ids])
        cursor.execute(f"""
            SELECT id, path, filename, size
            FROM files
            WHERE id IN ({placeholders})
              AND status = 'active'
        """, file_ids)
        
        files = cursor.fetchall()
        preview = []
        total_size = 0
        
        for file_id, path, filename, size in files:
            preview.append({
                'file_id': file_id,
                'filename': filename,
                'path': path,
                'size': size,
                'exists': os.path.exists(path)
            })
            total_size += size
        
        return {
            'files': preview,
            'total_count': len(preview),
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'permanent': permanent
        }
    
    def execute_delete(self, file_ids, permanent=False, dry_run=False):
        """
        Execute bulk delete
        If permanent=False, files are moved to trash table for recovery
        """
        if dry_run:
            preview = self.preview_delete(file_ids, permanent)
            return {
                'success': [f['filename'] for f in preview['files']],
                'failed': [],
                'operation_id': None
            }
        
        cursor = self.db.conn.cursor()
        success = []
        failed = []
        
        for file_id in file_ids:
            try:
                # Get file info
                cursor.execute("""
                    SELECT id, path, filename, size, created_date, modified_date, 
                           content_text, ai_summary, ai_tags
                    FROM files
                    WHERE id = ?
                """, (file_id,))
                
                file_info = cursor.fetchone()
                if not file_info:
                    continue
                
                file_id, path, filename, size, created, modified, content, summary, tags = file_info
                
                if permanent:
                    # Permanent delete
                    if os.path.exists(path):
                        os.remove(path)
                    
                    # Remove from database
                    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                else:
                    # Move to trash
                    metadata = json.dumps({
                        'size': size,
                        'created_date': created,
                        'modified_date': modified,
                        'content_text': content,
                        'ai_summary': summary,
                        'ai_tags': tags
                    })
                    
                    cursor.execute("""
                        INSERT INTO trash
                        (original_path, filename, deleted_date, deleted_by, metadata, can_recover)
                        VALUES (?, ?, ?, 'user', ?, 1)
                    """, (path, filename, datetime.now().isoformat(), metadata))
                    
                    # Mark as deleted in files table
                    cursor.execute("""
                        UPDATE files
                        SET status = 'deleted'
                        WHERE id = ?
                    """, (file_id,))
                
                success.append(filename)
                
            except Exception as e:
                failed.append({
                    'file_id': file_id,
                    'error': str(e)
                })
        
        self.db.conn.commit()
        
        return {
            'success': success,
            'failed': failed,
            'operation_id': None
        }
    
    def undo_operation(self, operation_id):
        """Undo a bulk operation"""
        cursor = self.db.conn.cursor()
        
        # Get operation details
        cursor.execute("""
            SELECT operation_type, original_state, can_undo, completed
            FROM bulk_operations
            WHERE id = ?
        """, (operation_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'success': False, 'error': 'Operation not found'}
        
        op_type, original_state, can_undo, completed = row
        
        if not can_undo:
            return {'success': False, 'error': 'Operation cannot be undone'}
        
        if not completed:
            return {'success': False, 'error': 'Operation not completed'}
        
        # Parse original state
        state = json.loads(original_state)
        
        try:
            if op_type == 'rename' or op_type == 'move':
                # Reverse renames/moves
                for file_info in state['files']:
                    if os.path.exists(file_info['new_path']):
                        os.rename(file_info['new_path'], file_info['old_path'])
                        
                        # Update database
                        cursor.execute("""
                            UPDATE files
                            SET path = ?, filename = ?
                            WHERE id = ?
                        """, (
                            file_info['old_path'],
                            os.path.basename(file_info['old_path']),
                            file_info['file_id']
                        ))
            
            # Mark operation as undone
            cursor.execute("""
                UPDATE bulk_operations
                SET can_undo = 0
                WHERE id = ?
            """, (operation_id,))
            
            self.db.conn.commit()
            
            return {'success': True, 'undone': len(state['files'])}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_recent_operations(self, limit=10):
        """Get recent bulk operations"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, operation_type, operation_date, files_affected, new_state, can_undo
            FROM bulk_operations
            WHERE completed = 1
            ORDER BY operation_date DESC
            LIMIT ?
        """, (limit,))
        
        operations = []
        for row in cursor.fetchall():
            op_id, op_type, op_date, files, state, can_undo = row
            operations.append({
                'id': op_id,
                'type': op_type,
                'date': op_date,
                'file_count': len(json.loads(files)),
                'details': json.loads(state),
                'can_undo': bool(can_undo)
            })
        
        return operations


if __name__ == "__main__":
    # Test bulk operations
    from file_indexer import FileDatabase
    
    print("Testing Bulk Operations...")
    
    db = FileDatabase()
    bulk = BulkOperations(db)
    
    # Get some files for testing
    cursor = db.conn.cursor()
    cursor.execute("SELECT id FROM files WHERE status = 'active' LIMIT 5")
    test_file_ids = [row[0] for row in cursor.fetchall()]
    
    if test_file_ids:
        print(f"\n📋 Testing with {len(test_file_ids)} files")
        
        # Preview rename
        print("\n🔄 Preview Rename (add _backup):")
        preview = bulk.preview_rename(test_file_ids, pattern='.', replacement='_backup.', use_regex=False)
        for item in preview[:3]:
            print(f"  {item['old_name']} → {item['new_name']}")
        
        # Preview move
        print("\n📦 Preview Move to ~/Desktop/Test:")
        preview = bulk.preview_move(test_file_ids, "~/Desktop/Test")
        for item in preview[:3]:
            print(f"  {item['filename']}: {item['old_folder']} → {item['new_folder']}")
        
        # Preview delete
        print("\n🗑️  Preview Delete:")
        preview = bulk.preview_delete(test_file_ids, permanent=False)
        print(f"  {preview['total_count']} files, {preview['total_size_mb']:.2f} MB")
    
    # Get recent operations
    print("\n📜 Recent Operations:")
    recent = bulk.get_recent_operations(5)
    if recent:
        for op in recent:
            print(f"  [{op['type']}] {op['date']}: {op['file_count']} files (undo: {op['can_undo']})")
    else:
        print("  No recent operations")
    
    db.close()
    print("\n✅ Bulk operations test complete!")
