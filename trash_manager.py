#!/usr/bin/env python3
"""
Smart Trash Manager
Track deletions, enable recovery, and provide "undo delete" functionality
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path


class TrashManager:
    """Manage deleted files with recovery support"""
    
    def __init__(self, file_db):
        self.db = file_db
        self.trash_dir = os.path.expanduser("~/.fileorganizer/trash")
        os.makedirs(self.trash_dir, exist_ok=True)
    
    def delete_file(self, file_id, move_to_trash=True):
        """
        Delete a file (soft delete with recovery option)
        
        Args:
            file_id: Database file ID
            move_to_trash: If True, copy file to trash for recovery
        """
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT path, filename FROM files WHERE id = ?", (file_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, "File not found in database"
        
        filepath, filename = result
        
        # Copy to trash if file still exists
        if move_to_trash and os.path.exists(filepath):
            try:
                # Create unique trash filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                trash_filename = f"{timestamp}_{filename}"
                trash_path = os.path.join(self.trash_dir, trash_filename)
                
                # Copy file
                shutil.copy2(filepath, trash_path)
                
                # Store metadata
                metadata = {
                    'original_path': filepath,
                    'file_id': file_id,
                    'trash_path': trash_path,
                    'deleted_date': datetime.now().isoformat()
                }
                
                # Insert into trash table
                cursor.execute("""
                    INSERT INTO trash (original_path, filename, deleted_date, metadata, can_recover)
                    VALUES (?, ?, ?, ?, 1)
                """, (filepath, filename, datetime.now().isoformat(), json.dumps(metadata)))
                
            except Exception as e:
                print(f"Warning: Could not copy to trash: {e}")
        
        # Mark as deleted in database
        cursor.execute("""
            UPDATE files SET status = 'deleted' WHERE id = ?
        """, (file_id,))
        
        self.db.conn.commit()
        
        return True, "File moved to trash"
    
    def get_recent_deletions(self, days=30):
        """Get recently deleted files"""
        cursor = self.db.conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT id, original_path, filename, deleted_date, metadata, can_recover
            FROM trash
            WHERE deleted_date > ?
            AND can_recover = 1
            ORDER BY deleted_date DESC
        """, (cutoff,))
        
        deletions = []
        for row in cursor.fetchall():
            metadata = json.loads(row[4]) if row[4] else {}
            deletions.append({
                'trash_id': row[0],
                'original_path': row[1],
                'filename': row[2],
                'deleted_date': row[3],
                'metadata': metadata,
                'can_recover': row[5]
            })
        
        return deletions
    
    def recover_file(self, trash_id, destination=None):
        """
        Recover a deleted file
        
        Args:
            trash_id: ID in trash table
            destination: Optional destination path (None = original location)
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT original_path, filename, metadata
            FROM trash
            WHERE id = ? AND can_recover = 1
        """, (trash_id,))
        
        result = cursor.fetchone()
        if not result:
            return False, "File not found in trash or cannot be recovered"
        
        original_path, filename, metadata_json = result
        metadata = json.loads(metadata_json) if metadata_json else {}
        trash_path = metadata.get('trash_path')
        
        if not trash_path or not os.path.exists(trash_path):
            return False, "Trash file no longer exists"
        
        # Determine destination
        if destination is None:
            destination = original_path
        
        # Check if destination exists
        if os.path.exists(destination):
            # Create unique name
            base, ext = os.path.splitext(destination)
            counter = 1
            while os.path.exists(f"{base}_recovered_{counter}{ext}"):
                counter += 1
            destination = f"{base}_recovered_{counter}{ext}"
        
        try:
            # Restore file
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(trash_path, destination)
            
            # Update database
            file_id = metadata.get('file_id')
            if file_id:
                cursor.execute("""
                    UPDATE files SET status = 'active', path = ? WHERE id = ?
                """, (destination, file_id))
            
            # Mark as recovered in trash
            cursor.execute("""
                UPDATE trash SET can_recover = 0 WHERE id = ?
            """, (trash_id,))
            
            self.db.conn.commit()
            
            return True, f"Recovered to: {destination}"
            
        except Exception as e:
            return False, f"Recovery failed: {e}"
    
    def clean_old_trash(self, days=30):
        """Remove trash files older than specified days"""
        cursor = self.db.conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT id, metadata
            FROM trash
            WHERE deleted_date < ?
        """, (cutoff,))
        
        cleaned = []
        for trash_id, metadata_json in cursor.fetchall():
            metadata = json.loads(metadata_json) if metadata_json else {}
            trash_path = metadata.get('trash_path')
            
            if trash_path and os.path.exists(trash_path):
                try:
                    os.remove(trash_path)
                    cleaned.append(trash_path)
                except Exception as e:
                    print(f"Could not remove {trash_path}: {e}")
            
            # Remove from database
            cursor.execute("DELETE FROM trash WHERE id = ?", (trash_id,))
        
        self.db.conn.commit()
        
        return cleaned
    
    def get_trash_stats(self):
        """Get statistics about trash"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(LENGTH(metadata)) FROM trash")
        count, size = cursor.fetchone()
        
        # Count files in trash directory
        trash_files = list(Path(self.trash_dir).glob('*'))
        trash_size = sum(f.stat().st_size for f in trash_files if f.is_file())
        
        return {
            'items_in_trash': count or 0,
            'trash_size_bytes': trash_size,
            'trash_size_mb': round(trash_size / (1024 * 1024), 2),
            'trash_dir': self.trash_dir
        }


if __name__ == "__main__":
    print("🗑️  Smart Trash Manager")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    trash = TrashManager(db)
    
    # Show statistics
    stats = trash.get_trash_stats()
    print(f"\n📊 Trash Statistics:")
    print(f"   Items in trash: {stats['items_in_trash']}")
    print(f"   Trash size: {stats['trash_size_mb']} MB")
    print(f"   Location: {stats['trash_dir']}")
    
    # Show recent deletions
    deletions = trash.get_recent_deletions(days=30)
    
    if deletions:
        print(f"\n🗑️  Recent Deletions ({len(deletions)}):\n")
        for d in deletions[:5]:
            print(f"   {d['filename']}")
            print(f"      Deleted: {d['deleted_date'][:10]}")
            print(f"      Original: {d['original_path']}")
            print()
    else:
        print("\n✨ No recent deletions")
    
    print("\n💡 To recover a file:")
    print("   ./o UNDELETE@filename")
    
    db.close()

