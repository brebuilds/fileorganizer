#!/usr/bin/env python3
"""
File Aging & Auto-Archive Manager
Automatically move old files to archive based on configurable rules
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import json


class AgingManager:
    """Manage file aging and auto-archive rules"""
    
    def __init__(self, file_db):
        self.db = file_db
        self.archive_dir = os.path.expanduser("~/.fileorganizer/archive")
        os.makedirs(self.archive_dir, exist_ok=True)
    
    def create_rule(self, folder_pattern, age_days, action='archive', destination=None, enabled=True):
        """
        Create an aging rule
        
        Args:
            folder_pattern: Folder to monitor (e.g., "Downloads", "%Downloads%")
            age_days: Number of days before action triggers
            action: 'archive', 'delete', or 'move'
            destination: Where to move files (for 'move' action)
            enabled: Whether rule is active
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            INSERT INTO aging_rules (folder_pattern, age_days, action, destination, enabled, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (folder_pattern, age_days, action, destination, 1 if enabled else 0, datetime.now().isoformat()))
        
        self.db.conn.commit()
        return cursor.lastrowid
    
    def get_all_rules(self):
        """Get all aging rules"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, folder_pattern, age_days, action, destination, enabled, created_date
            FROM aging_rules
            ORDER BY age_days
        """)
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row[0],
                'folder_pattern': row[1],
                'age_days': row[2],
                'action': row[3],
                'destination': row[4],
                'enabled': bool(row[5]),
                'created_date': row[6]
            })
        
        return rules
    
    def toggle_rule(self, rule_id, enabled):
        """Enable or disable a rule"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE aging_rules SET enabled = ? WHERE id = ?
        """, (1 if enabled else 0, rule_id))
        self.db.conn.commit()
    
    def delete_rule(self, rule_id):
        """Delete a rule"""
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM aging_rules WHERE id = ?", (rule_id,))
        self.db.conn.commit()
    
    def find_aged_files(self, rule_id=None):
        """
        Find files that match aging rules
        
        Args:
            rule_id: Specific rule to check (None = all rules)
        """
        cursor = self.db.conn.cursor()
        
        if rule_id:
            rules = [self.get_rule_by_id(rule_id)]
        else:
            rules = [r for r in self.get_all_rules() if r['enabled']]
        
        aged_files = []
        
        for rule in rules:
            cutoff = (datetime.now() - timedelta(days=rule['age_days'])).isoformat()
            pattern = rule['folder_pattern']
            
            cursor.execute("""
                SELECT id, path, filename, created_date, modified_date, folder_location
                FROM files
                WHERE folder_location LIKE ?
                AND created_date < ?
                AND status = 'active'
                AND hide_from_app = 0
            """, (f'%{pattern}%', cutoff))
            
            for row in cursor.fetchall():
                aged_files.append({
                    'file_id': row[0],
                    'path': row[1],
                    'filename': row[2],
                    'created_date': row[3],
                    'modified_date': row[4],
                    'folder': row[5],
                    'rule_id': rule['id'],
                    'rule_action': rule['action'],
                    'rule_destination': rule['destination'],
                    'age_days': (datetime.now() - datetime.fromisoformat(row[3])).days
                })
        
        return aged_files
    
    def get_rule_by_id(self, rule_id):
        """Get rule by ID"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, folder_pattern, age_days, action, destination, enabled, created_date
            FROM aging_rules
            WHERE id = ?
        """, (rule_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'folder_pattern': row[1],
                'age_days': row[2],
                'action': row[3],
                'destination': row[4],
                'enabled': bool(row[5]),
                'created_date': row[6]
            }
        return None
    
    def apply_aging(self, dry_run=True):
        """
        Apply aging rules to files
        
        Args:
            dry_run: If True, only show what would happen
        """
        aged_files = self.find_aged_files()
        
        if not aged_files:
            return {
                'aged_files': 0,
                'actions': [],
                'dry_run': dry_run
            }
        
        actions = []
        cursor = self.db.conn.cursor()
        
        for file_info in aged_files:
            file_id = file_info['file_id']
            filepath = file_info['path']
            action = file_info['rule_action']
            
            if action == 'archive':
                # Move to archive
                if os.path.exists(filepath):
                    archive_path = os.path.join(
                        self.archive_dir,
                        Path(filepath).name
                    )
                    
                    # Handle conflicts
                    if os.path.exists(archive_path):
                        base, ext = os.path.splitext(archive_path)
                        counter = 1
                        while os.path.exists(f"{base}_{counter}{ext}"):
                            counter += 1
                        archive_path = f"{base}_{counter}{ext}"
                    
                    if not dry_run:
                        try:
                            shutil.move(filepath, archive_path)
                            
                            cursor.execute("""
                                UPDATE files
                                SET path = ?, folder_location = ?, status = 'archived'
                                WHERE id = ?
                            """, (archive_path, self.archive_dir, file_id))
                            
                            actions.append({
                                'file': file_info['filename'],
                                'action': 'archived',
                                'to': archive_path,
                                'success': True
                            })
                        except Exception as e:
                            actions.append({
                                'file': file_info['filename'],
                                'action': 'archive_failed',
                                'error': str(e),
                                'success': False
                            })
                    else:
                        actions.append({
                            'file': file_info['filename'],
                            'action': 'would_archive',
                            'to': archive_path,
                            'age_days': file_info['age_days']
                        })
            
            elif action == 'delete':
                if not dry_run:
                    cursor.execute("""
                        UPDATE files SET status = 'deleted' WHERE id = ?
                    """, (file_id,))
                    
                    actions.append({
                        'file': file_info['filename'],
                        'action': 'deleted',
                        'success': True
                    })
                else:
                    actions.append({
                        'file': file_info['filename'],
                        'action': 'would_delete',
                        'age_days': file_info['age_days']
                    })
        
        if not dry_run:
            self.db.conn.commit()
        
        return {
            'aged_files': len(aged_files),
            'actions': actions,
            'dry_run': dry_run
        }
    
    def create_default_rules(self):
        """Create some sensible default rules"""
        defaults = [
            {
                'folder_pattern': 'Downloads',
                'age_days': 30,
                'action': 'archive',
                'enabled': False  # Disabled by default
            },
            {
                'folder_pattern': 'Desktop',
                'age_days': 90,
                'action': 'archive',
                'enabled': False
            }
        ]
        
        cursor = self.db.conn.cursor()
        created = []
        
        for rule in defaults:
            # Check if similar rule exists
            cursor.execute("""
                SELECT id FROM aging_rules
                WHERE folder_pattern = ? AND age_days = ?
            """, (rule['folder_pattern'], rule['age_days']))
            
            if not cursor.fetchone():
                self.create_rule(**rule)
                created.append(f"{rule['folder_pattern']} ({rule['age_days']} days)")
        
        return created


if __name__ == "__main__":
    print("📦 File Aging & Auto-Archive Manager")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    aging = AgingManager(db)
    
    # Create default rules
    print("\n🎯 Creating default aging rules...")
    created = aging.create_default_rules()
    if created:
        print(f"   Created: {', '.join(created)}")
    else:
        print("   Rules already exist")
    
    # Show all rules
    rules = aging.get_all_rules()
    print(f"\n📋 Aging Rules ({len(rules)}):\n")
    
    for rule in rules:
        status = "✅ Enabled" if rule['enabled'] else "⏸️  Disabled"
        print(f"   {status} - {rule['folder_pattern']}")
        print(f"      Age: {rule['age_days']} days")
        print(f"      Action: {rule['action']}")
        print()
    
    # Find aged files
    print("🔍 Finding aged files...")
    aged = aging.find_aged_files()
    
    if aged:
        print(f"\n📊 Found {len(aged)} aged file(s)")
        print("\n💡 To apply aging rules:")
        print("   ./o AGING --apply")
    else:
        print("✨ No aged files found")
    
    print("\n⚙️  To enable auto-archiving:")
    print("   ./o AGING --enable Downloads")
    
    db.close()

