#!/usr/bin/env python3
"""
Smart Folders - Saved Searches
Virtual folders that show files matching specific criteria
"""

import json
from datetime import datetime


class SmartFolders:
    """Manage smart folders (saved searches)"""
    
    def __init__(self, file_db):
        self.db = file_db
    
    def create(self, name, query, description=None, icon='📁', color='#3b82f6'):
        """
        Create a new smart folder
        
        Args:
            name: Folder name
            query: Search query/criteria
            description: Optional description
            icon: Emoji icon
            color: Hex color code
        """
        cursor = self.db.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO smart_folders (name, description, query, icon, color, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, description, query, icon, color, datetime.now().isoformat()))
            
            self.db.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating smart folder: {e}")
            return None
    
    def get_all(self):
        """Get all smart folders"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, name, description, query, icon, color, created_date, last_used, use_count
            FROM smart_folders
            ORDER BY use_count DESC, name
        """)
        
        folders = []
        for row in cursor.fetchall():
            folders.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'query': row[3],
                'icon': row[4],
                'color': row[5],
                'created_date': row[6],
                'last_used': row[7],
                'use_count': row[8]
            })
        
        return folders
    
    def get_by_id(self, folder_id):
        """Get smart folder by ID"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, name, description, query, icon, color, created_date, last_used, use_count
            FROM smart_folders
            WHERE id = ?
        """, (folder_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'query': row[3],
                'icon': row[4],
                'color': row[5],
                'created_date': row[6],
                'last_used': row[7],
                'use_count': row[8]
            }
        return None
    
    def execute_query(self, folder_id):
        """Execute a smart folder query and return results"""
        folder = self.get_by_id(folder_id)
        if not folder:
            return []
        
        # Update usage
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE smart_folders
            SET last_used = ?, use_count = use_count + 1
            WHERE id = ?
        """, (datetime.now().isoformat(), folder_id))
        self.db.conn.commit()
        
        # Execute the query
        query = folder['query']
        return self._execute_search(query)
    
    def _execute_search(self, query):
        """Execute a search query"""
        cursor = self.db.conn.cursor()
        
        # Parse query (simple version - can be enhanced)
        # Format: "tag:invoice" or "project:ClientX" or "type:pdf" or plain text
        
        if ':' in query:
            # Structured query
            key, value = query.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'tag':
                cursor.execute("""
                    SELECT id, filename, path, ai_summary, ai_tags
                    FROM files
                    WHERE ai_tags LIKE ?
                    AND status = 'active'
                    AND hide_from_app = 0
                    ORDER BY modified_date DESC
                """, (f'%{value}%',))
            
            elif key == 'project':
                cursor.execute("""
                    SELECT id, filename, path, ai_summary, ai_tags
                    FROM files
                    WHERE project LIKE ?
                    AND status = 'active'
                    AND hide_from_app = 0
                    ORDER BY modified_date DESC
                """, (f'%{value}%',))
            
            elif key == 'type' or key == 'ext':
                cursor.execute("""
                    SELECT id, filename, path, ai_summary, ai_tags
                    FROM files
                    WHERE extension LIKE ?
                    AND status = 'active'
                    AND hide_from_app = 0
                    ORDER BY modified_date DESC
                """, (f'%{value}%',))
            
            elif key == 'folder':
                cursor.execute("""
                    SELECT id, filename, path, ai_summary, ai_tags
                    FROM files
                    WHERE folder_location LIKE ?
                    AND status = 'active'
                    AND hide_from_app = 0
                    ORDER BY modified_date DESC
                """, (f'%{value}%',))
            
            else:
                # Unknown key, do plain search
                return self._plain_search(query)
        else:
            # Plain text search
            return self._plain_search(query)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'path': row[2],
                'summary': row[3],
                'tags': row[4]
            })
        
        return results
    
    def _plain_search(self, query):
        """Plain text search across filename, content, summary, tags"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, ai_summary, ai_tags
            FROM files
            WHERE (
                filename LIKE ? 
                OR content_text LIKE ?
                OR ai_summary LIKE ?
                OR ai_tags LIKE ?
            )
            AND status = 'active'
            AND hide_from_app = 0
            ORDER BY modified_date DESC
            LIMIT 100
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'path': row[2],
                'summary': row[3],
                'tags': row[4]
            })
        
        return results
    
    def delete(self, folder_id):
        """Delete a smart folder"""
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM smart_folders WHERE id = ?", (folder_id,))
        self.db.conn.commit()
    
    def update(self, folder_id, **kwargs):
        """Update smart folder properties"""
        allowed_fields = {'name', 'description', 'query', 'icon', 'color'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return
        
        cursor = self.db.conn.cursor()
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [folder_id]
        
        cursor.execute(f"UPDATE smart_folders SET {set_clause} WHERE id = ?", values)
        self.db.conn.commit()
    
    def create_default_folders(self):
        """Create some useful default smart folders"""
        defaults = [
            {
                'name': 'Recent Invoices',
                'query': 'tag:invoice',
                'description': 'All files tagged as invoices',
                'icon': '💰',
                'color': '#10b981'
            },
            {
                'name': 'Urgent Files',
                'query': 'urgent',
                'description': 'Files marked as urgent',
                'icon': '🔥',
                'color': '#ef4444'
            },
            {
                'name': 'PDFs',
                'query': 'type:pdf',
                'description': 'All PDF documents',
                'icon': '📄',
                'color': '#ef4444'
            },
            {
                'name': 'Screenshots',
                'query': 'type:.png',
                'description': 'All screenshot images',
                'icon': '📸',
                'color': '#8b5cf6'
            },
            {
                'name': 'Recent Downloads',
                'query': 'folder:Downloads',
                'description': 'Files in Downloads folder',
                'icon': '📥',
                'color': '#3b82f6'
            }
        ]
        
        created = []
        for folder in defaults:
            # Check if it already exists
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id FROM smart_folders WHERE name = ?", (folder['name'],))
            if not cursor.fetchone():
                folder_id = self.create(**folder)
                if folder_id:
                    created.append(folder['name'])
        
        return created


if __name__ == "__main__":
    print("📁 Smart Folders System")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    smart = SmartFolders(db)
    
    # Create default folders
    print("\n🎯 Creating default smart folders...")
    created = smart.create_default_folders()
    if created:
        print(f"   Created: {', '.join(created)}")
    else:
        print("   All default folders already exist")
    
    # List all smart folders
    folders = smart.get_all()
    print(f"\n📂 Smart Folders ({len(folders)}):\n")
    
    for folder in folders:
        icon = folder['icon']
        name = folder['name']
        query = folder['query']
        use_count = folder['use_count']
        
        print(f"   {icon} {name}")
        print(f"      Query: {query}")
        if use_count:
            print(f"      Used: {use_count} times")
        print()
    
    # Test a query
    if folders:
        print(f"\n🔍 Testing first folder: {folders[0]['name']}")
        results = smart.execute_query(folders[0]['id'])
        print(f"   Found {len(results)} files")
    
    db.close()

