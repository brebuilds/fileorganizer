#!/usr/bin/env python3
"""
Smart Folders System for File Organizer
Dynamic folders that auto-update based on queries (like macOS Smart Folders but better)
"""

import os
import json
from datetime import datetime, timedelta
import sqlite3


class SmartFolders:
    """Manages dynamic smart folders (saved searches with auto-updates)"""
    
    def __init__(self, db):
        self.db = db
    
    def create_smart_folder(self, name, query, description=None, icon='📁', color='#3b82f6'):
        """
        Create a new smart folder
        
        Args:
            name: Display name
            query: Search query/filter (JSON format)
            description: Optional description
            icon: Emoji icon
            color: Hex color code
        
        Returns:
            Smart folder ID
        """
        cursor = self.db.conn.cursor()
        
        # Convert query dict to JSON if needed
        if isinstance(query, dict):
            query = json.dumps(query)
        
        try:
            cursor.execute("""
                INSERT INTO smart_folders
                (name, description, query, icon, color, created_date, last_used, use_count)
                VALUES (?, ?, ?, ?, ?, ?, NULL, 0)
            """, (name, description, query, icon, color, datetime.now().isoformat()))
            
            self.db.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Smart folder with this name already exists
            return None
    
    def get_smart_folder(self, smart_folder_id):
        """Get smart folder details"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, query, icon, color, created_date, last_used, use_count
            FROM smart_folders
            WHERE id = ?
        """, (smart_folder_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'query': json.loads(row[3]),
                'icon': row[4],
                'color': row[5],
                'created_date': row[6],
                'last_used': row[7],
                'use_count': row[8]
            }
        return None
    
    def get_all_smart_folders(self):
        """Get all smart folders"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, query, icon, color, created_date, last_used, use_count
            FROM smart_folders
            ORDER BY use_count DESC, name ASC
        """)
        
        folders = []
        for row in cursor.fetchall():
            folders.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'query': json.loads(row[3]),
                'icon': row[4],
                'color': row[5],
                'created_date': row[6],
                'last_used': row[7],
                'use_count': row[8]
            })
        
        return folders
    
    def execute_smart_folder(self, smart_folder_id):
        """
        Execute a smart folder query and return matching files
        Also updates last_used and use_count
        """
        folder = self.get_smart_folder(smart_folder_id)
        if not folder:
            return []
        
        query = folder['query']
        results = self._execute_query(query)
        
        # Update usage stats
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE smart_folders
            SET last_used = ?, use_count = use_count + 1
            WHERE id = ?
        """, (datetime.now().isoformat(), smart_folder_id))
        self.db.conn.commit()
        
        return results
    
    def _execute_query(self, query):
        """
        Execute a smart folder query
        
        Query format (JSON):
        {
            "extension": [".pdf", ".doc"],
            "tags": ["work", "important"],
            "project": "ClientX",
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "min_size": 1024,
            "max_size": 10485760,
            "contains_text": "invoice",
            "folder": "~/Downloads"
        }
        """
        cursor = self.db.conn.cursor()
        
        # Build SQL query dynamically based on filters
        sql = "SELECT DISTINCT f.* FROM files f LEFT JOIN tags t ON f.id = t.file_id WHERE f.status = 'active'"
        params = []
        
        # Extension filter
        if 'extension' in query and query['extension']:
            exts = query['extension'] if isinstance(query['extension'], list) else [query['extension']]
            placeholders = ','.join(['?' for _ in exts])
            sql += f" AND f.extension IN ({placeholders})"
            params.extend(exts)
        
        # Tags filter
        if 'tags' in query and query['tags']:
            tags = query['tags'] if isinstance(query['tags'], list) else [query['tags']]
            placeholders = ','.join(['?' for _ in tags])
            sql += f" AND t.tag IN ({placeholders})"
            params.extend(tags)
        
        # Project filter
        if 'project' in query and query['project']:
            sql += " AND f.project = ?"
            params.append(query['project'])
        
        # Date range filter
        if 'date_range' in query:
            if 'start' in query['date_range']:
                sql += " AND f.modified_date >= ?"
                params.append(query['date_range']['start'])
            if 'end' in query['date_range']:
                sql += " AND f.modified_date <= ?"
                params.append(query['date_range']['end'])
        
        # Size filters
        if 'min_size' in query:
            sql += " AND f.size >= ?"
            params.append(query['min_size'])
        
        if 'max_size' in query:
            sql += " AND f.size <= ?"
            params.append(query['max_size'])
        
        # Text content filter
        if 'contains_text' in query and query['contains_text']:
            text = query['contains_text']
            sql += " AND (f.content_text LIKE ? OR f.ai_summary LIKE ? OR f.ocr_text LIKE ?)"
            params.extend([f"%{text}%", f"%{text}%", f"%{text}%"])
        
        # Folder filter
        if 'folder' in query and query['folder']:
            folder = os.path.expanduser(query['folder'])
            sql += " AND f.folder_location LIKE ?"
            params.append(f"{folder}%")
        
        # Screenshot filter
        if 'is_screenshot' in query:
            sql += " AND f.is_screenshot = ?"
            params.append(1 if query['is_screenshot'] else 0)
        
        # Has duplicates filter
        if 'is_duplicate' in query:
            sql += " AND f.is_duplicate = ?"
            params.append(1 if query['is_duplicate'] else 0)
        
        sql += " ORDER BY f.modified_date DESC LIMIT 1000"
        
        cursor.execute(sql, params)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def update_smart_folder(self, smart_folder_id, name=None, query=None, description=None, icon=None, color=None):
        """Update smart folder properties"""
        cursor = self.db.conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if query is not None:
            if isinstance(query, dict):
                query = json.dumps(query)
            updates.append("query = ?")
            params.append(query)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if icon is not None:
            updates.append("icon = ?")
            params.append(icon)
        
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        
        if updates:
            params.append(smart_folder_id)
            sql = f"UPDATE smart_folders SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            self.db.conn.commit()
            return True
        
        return False
    
    def delete_smart_folder(self, smart_folder_id):
        """Delete a smart folder"""
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM smart_folders WHERE id = ?", (smart_folder_id,))
        self.db.conn.commit()
    
    def get_file_count(self, smart_folder_id):
        """Get count of files in smart folder without fetching all"""
        folder = self.get_smart_folder(smart_folder_id)
        if not folder:
            return 0
        
        # Execute query but only count
        results = self._execute_query(folder['query'])
        return len(results)
    
    def create_default_smart_folders(self):
        """Create helpful default smart folders"""
        defaults = [
            {
                'name': 'Recent Files',
                'description': 'Files modified in the last 7 days',
                'icon': '🕒',
                'color': '#10b981',
                'query': {
                    'date_range': {
                        'start': (datetime.now() - timedelta(days=7)).isoformat()
                    }
                }
            },
            {
                'name': 'Large Files',
                'description': 'Files larger than 10 MB',
                'icon': '📦',
                'color': '#f59e0b',
                'query': {
                    'min_size': 10 * 1024 * 1024
                }
            },
            {
                'name': 'PDFs',
                'description': 'All PDF documents',
                'icon': '📄',
                'color': '#ef4444',
                'query': {
                    'extension': ['.pdf']
                }
            },
            {
                'name': 'Screenshots',
                'description': 'All screenshots',
                'icon': '📸',
                'color': '#8b5cf6',
                'query': {
                    'is_screenshot': True
                }
            },
            {
                'name': 'Duplicates',
                'description': 'Duplicate files',
                'icon': '🔄',
                'color': '#ec4899',
                'query': {
                    'is_duplicate': True
                }
            },
            {
                'name': 'Downloads',
                'description': 'Files in Downloads folder',
                'icon': '⬇️',
                'color': '#06b6d4',
                'query': {
                    'folder': '~/Downloads'
                }
            }
        ]
        
        created = []
        for folder_def in defaults:
            folder_id = self.create_smart_folder(
                name=folder_def['name'],
                query=folder_def['query'],
                description=folder_def['description'],
                icon=folder_def['icon'],
                color=folder_def['color']
            )
            if folder_id:
                created.append(folder_def['name'])
        
        return created


if __name__ == "__main__":
    # Test smart folders
    from file_indexer import FileDatabase
    
    print("Testing Smart Folders...")
    
    db = FileDatabase()
    smart = SmartFolders(db)
    
    # Create default folders
    print("\n📁 Creating default smart folders...")
    created = smart.create_default_smart_folders()
    print(f"Created: {', '.join(created)}")
    
    # Get all smart folders
    print("\n📂 All Smart Folders:")
    folders = smart.get_all_smart_folders()
    for folder in folders:
        count = smart.get_file_count(folder['id'])
        print(f"{folder['icon']} {folder['name']}: {count} files")
    
    # Test executing a smart folder
    if folders:
        print(f"\n🔍 Testing '{folders[0]['name']}'...")
        results = smart.execute_smart_folder(folders[0]['id'])
        print(f"Found {len(results)} files")
        for i, file in enumerate(results[:5], 1):
            print(f"  {i}. {file['filename']}")
    
    db.close()
    print("\n✅ Smart folders test complete!")
