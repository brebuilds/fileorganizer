#!/usr/bin/env python3
"""
Duplicate File Detector
Finds and manages duplicate files to save space and reduce clutter
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class DuplicateDetector:
    """Detect and manage duplicate files"""
    
    def __init__(self, file_db):
        self.db = file_db
    
    def find_duplicates(self, folder=None, min_size=1024):
        """
        Find duplicate files by hash
        
        Args:
            folder: Specific folder to scan (None = all files)
            min_size: Minimum file size to consider (default 1KB)
        
        Returns:
            dict: {hash: [file1, file2, ...]}
        """
        cursor = self.db.conn.cursor()
        
        if folder:
            cursor.execute("""
                SELECT id, path, filename, size, file_hash, modified_date
                FROM files
                WHERE folder_location LIKE ? 
                AND status = 'active'
                AND size >= ?
                AND hide_from_app = 0
                ORDER BY file_hash
            """, (f'{folder}%', min_size))
        else:
            cursor.execute("""
                SELECT id, path, filename, size, file_hash, modified_date
                FROM files
                WHERE status = 'active'
                AND size >= ?
                AND hide_from_app = 0
                ORDER BY file_hash
            """, (min_size,))
        
        files = cursor.fetchall()
        
        # Group by hash
        hash_groups = defaultdict(list)
        for file_data in files:
            file_id, path, filename, size, file_hash, modified = file_data
            if file_hash:
                hash_groups[file_hash].append({
                    'id': file_id,
                    'path': path,
                    'filename': filename,
                    'size': size,
                    'modified': modified
                })
        
        # Filter to only groups with duplicates
        duplicates = {h: files for h, files in hash_groups.items() if len(files) > 1}
        
        return duplicates
    
    def find_similar_names(self, threshold=0.8):
        """Find files with similar names (fuzzy matching)"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, size
            FROM files
            WHERE status = 'active'
            AND hide_from_app = 0
        """)
        
        files = cursor.fetchall()
        similar_groups = []
        
        # Simple similarity check (can be enhanced with fuzzywuzzy)
        for i, file1 in enumerate(files):
            for file2 in files[i+1:]:
                # Check if names are similar (ignoring extensions)
                name1 = Path(file1[1]).stem.lower()
                name2 = Path(file2[1]).stem.lower()
                
                # Simple similarity: check if one contains the other or very similar
                if (name1 in name2 or name2 in name1) and name1 != name2:
                    similar_groups.append({
                        'file1': {'id': file1[0], 'filename': file1[1], 'path': file1[2], 'size': file1[3]},
                        'file2': {'id': file2[0], 'filename': file2[1], 'path': file2[2], 'size': file2[3]},
                        'similarity': 'name_match'
                    })
        
        return similar_groups
    
    def mark_as_duplicate(self, file_id, original_id):
        """Mark a file as duplicate of another"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE files
            SET is_duplicate = 1, duplicate_of = ?
            WHERE id = ?
        """, (original_id, file_id))
        self.db.conn.commit()
    
    def get_duplicate_stats(self):
        """Get statistics about duplicates"""
        cursor = self.db.conn.cursor()
        
        # Find all duplicate groups
        duplicates = self.find_duplicates()
        
        total_duplicates = sum(len(group) - 1 for group in duplicates.values())
        total_wasted_space = 0
        
        for group in duplicates.values():
            if len(group) > 1:
                file_size = group[0]['size']
                wasted = file_size * (len(group) - 1)
                total_wasted_space += wasted
        
        return {
            'duplicate_groups': len(duplicates),
            'total_duplicates': total_duplicates,
            'wasted_space_bytes': total_wasted_space,
            'wasted_space_mb': round(total_wasted_space / (1024 * 1024), 2)
        }
    
    def suggest_cleanup(self, duplicates):
        """Suggest which duplicates to keep/delete"""
        suggestions = []
        
        for file_hash, group in duplicates.items():
            # Keep the oldest file (most likely original)
            sorted_group = sorted(group, key=lambda x: x['modified'])
            keep = sorted_group[0]
            delete = sorted_group[1:]
            
            suggestions.append({
                'keep': keep,
                'delete': delete,
                'savings_bytes': sum(f['size'] for f in delete),
                'reason': 'oldest_file'
            })
        
        return suggestions
    
    def auto_cleanup(self, dry_run=True):
        """
        Automatically clean up duplicates
        
        Args:
            dry_run: If True, only simulate (don't delete)
        
        Returns:
            list: Actions taken or would take
        """
        duplicates = self.find_duplicates()
        suggestions = self.suggest_cleanup(duplicates)
        
        actions = []
        for suggestion in suggestions:
            keep_file = suggestion['keep']
            
            for dup in suggestion['delete']:
                action = {
                    'action': 'delete' if not dry_run else 'would_delete',
                    'file': dup['filename'],
                    'path': dup['path'],
                    'size': dup['size'],
                    'kept_original': keep_file['filename']
                }
                
                if not dry_run:
                    # Move to trash instead of deleting
                    try:
                        # We'll integrate with trash_manager later
                        self.db.conn.cursor().execute("""
                            UPDATE files SET status = 'deleted' WHERE id = ?
                        """, (dup['id'],))
                        self.db.conn.commit()
                        action['success'] = True
                    except Exception as e:
                        action['success'] = False
                        action['error'] = str(e)
                
                actions.append(action)
        
        return actions
    
    def interactive_cleanup(self, duplicates):
        """
        Interactive cleanup (for CLI)
        
        Args:
            duplicates: Dict of duplicate groups
        
        Returns:
            list: User decisions
        """
        decisions = []
        
        print(f"\n🔍 Found {len(duplicates)} groups of duplicate files\n")
        
        for i, (file_hash, group) in enumerate(duplicates.items(), 1):
            print(f"\n━━━ Group {i}/{len(duplicates)} ━━━")
            print(f"File size: {group[0]['size'] / 1024:.1f} KB")
            print(f"Duplicates: {len(group)}")
            print()
            
            for j, file in enumerate(group, 1):
                print(f"   {j}. {file['filename']}")
                print(f"      📁 {file['path']}")
                print(f"      📅 Modified: {file['modified'][:10]}")
                print()
            
            # For now, return the data (will add interactive prompts later)
            decisions.append({
                'group': group,
                'action': 'keep_oldest'  # Default action
            })
        
        return decisions


if __name__ == "__main__":
    print("🔍 Duplicate File Detector")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    detector = DuplicateDetector(db)
    
    print("\n📊 Scanning for duplicates...")
    duplicates = detector.find_duplicates()
    
    if not duplicates:
        print("✅ No duplicates found!")
    else:
        stats = detector.get_duplicate_stats()
        
        print(f"\n🎯 Results:")
        print(f"   Duplicate groups: {stats['duplicate_groups']}")
        print(f"   Total duplicates: {stats['total_duplicates']}")
        print(f"   Wasted space: {stats['wasted_space_mb']} MB")
        
        print(f"\n💡 Suggestions:")
        suggestions = detector.suggest_cleanup(duplicates)
        
        total_savings = sum(s['savings_bytes'] for s in suggestions)
        print(f"   Could save: {total_savings / (1024 * 1024):.2f} MB")
        print(f"   by removing {len(suggestions)} duplicate(s)")
    
    db.close()

