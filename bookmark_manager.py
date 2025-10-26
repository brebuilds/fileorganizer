#!/usr/bin/env python3
"""
Bookmark & URL Manager for File Organizer
Save and manage URLs with context, metadata extraction
"""

import os
import json
from datetime import datetime
from urllib.parse import urlparse
import sqlite3

# Optional web scraping support
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    print("Note: Web scraping not available. Install requests and beautifulsoup4 for full features")


class BookmarkManager:
    """Manages bookmarks and URLs with context"""
    
    def __init__(self, db):
        self.db = db
    
    def add_bookmark(self, url, title=None, description=None, tags=None, source=None, download_file_id=None):
        """
        Add a bookmark/URL
        
        Args:
            url: The URL to bookmark
            title: Optional title (auto-extracted if not provided)
            description: Optional description
            tags: Comma-separated tags or list
            source: Where the bookmark came from
            download_file_id: If this URL was downloaded, link to file
        
        Returns:
            Bookmark ID
        """
        cursor = self.db.conn.cursor()
        
        # Auto-extract metadata if available
        if not title and WEB_SCRAPING_AVAILABLE:
            metadata = self._fetch_metadata(url)
            if metadata:
                title = title or metadata.get('title')
                description = description or metadata.get('description')
        
        # Format tags
        if isinstance(tags, list):
            tags = ','.join(tags)
        
        # Create metadata JSON
        metadata_dict = {
            'domain': urlparse(url).netloc,
            'added_via': source or 'manual',
            'fetch_date': datetime.now().isoformat()
        }
        
        cursor.execute("""
            INSERT INTO bookmarks
            (url, title, description, tags, source, created_date, access_count, downloaded_file_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
        """, (
            url,
            title or url,
            description,
            tags,
            source,
            datetime.now().isoformat(),
            download_file_id,
            json.dumps(metadata_dict)
        ))
        
        self.db.conn.commit()
        return cursor.lastrowid
    
    def _fetch_metadata(self, url):
        """Fetch metadata from URL (title, description, etc.)"""
        if not WEB_SCRAPING_AVAILABLE:
            return None
        
        try:
            response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.string
            elif soup.find('meta', property='og:title'):
                title = soup.find('meta', property='og:title')['content']
            
            # Extract description
            description = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content')
            elif soup.find('meta', property='og:description'):
                description = soup.find('meta', property='og:description')['content']
            
            return {
                'title': title,
                'description': description
            }
        except Exception as e:
            print(f"Error fetching metadata from {url}: {e}")
            return None
    
    def get_bookmark(self, bookmark_id):
        """Get bookmark by ID"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, url, title, description, tags, source, created_date, 
                   last_accessed, access_count, downloaded_file_id, metadata
            FROM bookmarks
            WHERE id = ?
        """, (bookmark_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'description': row[3],
                'tags': row[4].split(',') if row[4] else [],
                'source': row[5],
                'created_date': row[6],
                'last_accessed': row[7],
                'access_count': row[8],
                'downloaded_file_id': row[9],
                'metadata': json.loads(row[10]) if row[10] else {}
            }
        return None
    
    def search_bookmarks(self, query=None, tags=None, domain=None, limit=50):
        """Search bookmarks"""
        cursor = self.db.conn.cursor()
        
        sql = "SELECT id, url, title, description, tags, created_date, access_count FROM bookmarks WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (title LIKE ? OR description LIKE ? OR url LIKE ?)"
            search = f"%{query}%"
            params.extend([search, search, search])
        
        if tags:
            tag_conditions = []
            for tag in (tags if isinstance(tags, list) else [tags]):
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            sql += f" AND ({' OR '.join(tag_conditions)})"
        
        if domain:
            sql += " AND url LIKE ?"
            params.append(f"%{domain}%")
        
        sql += " ORDER BY access_count DESC, created_date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        
        bookmarks = []
        for row in cursor.fetchall():
            bookmarks.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'description': row[3],
                'tags': row[4].split(',') if row[4] else [],
                'created_date': row[5],
                'access_count': row[6]
            })
        
        return bookmarks
    
    def get_all_bookmarks(self, sort_by='created_date', limit=100):
        """Get all bookmarks"""
        cursor = self.db.conn.cursor()
        
        valid_sorts = ['created_date', 'access_count', 'title']
        if sort_by not in valid_sorts:
            sort_by = 'created_date'
        
        cursor.execute(f"""
            SELECT id, url, title, description, tags, created_date, access_count
            FROM bookmarks
            ORDER BY {sort_by} DESC
            LIMIT ?
        """, (limit,))
        
        bookmarks = []
        for row in cursor.fetchall():
            bookmarks.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'description': row[3],
                'tags': row[4].split(',') if row[4] else [],
                'created_date': row[5],
                'access_count': row[6]
            })
        
        return bookmarks
    
    def record_access(self, bookmark_id):
        """Record that a bookmark was accessed"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE bookmarks
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), bookmark_id))
        self.db.conn.commit()
    
    def update_bookmark(self, bookmark_id, title=None, description=None, tags=None):
        """Update bookmark details"""
        cursor = self.db.conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if tags is not None:
            if isinstance(tags, list):
                tags = ','.join(tags)
            updates.append("tags = ?")
            params.append(tags)
        
        if updates:
            params.append(bookmark_id)
            sql = f"UPDATE bookmarks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            self.db.conn.commit()
            return True
        
        return False
    
    def delete_bookmark(self, bookmark_id):
        """Delete a bookmark"""
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        self.db.conn.commit()
    
    def link_to_file(self, bookmark_id, file_id):
        """Link a bookmark to a downloaded file"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE bookmarks
            SET downloaded_file_id = ?
            WHERE id = ?
        """, (file_id, bookmark_id))
        self.db.conn.commit()
    
    def get_bookmarks_for_file(self, file_id):
        """Get all bookmarks linked to a file"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, url, title, created_date
            FROM bookmarks
            WHERE downloaded_file_id = ?
        """, (file_id,))
        
        bookmarks = []
        for row in cursor.fetchall():
            bookmarks.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'created_date': row[3]
            })
        
        return bookmarks
    
    def get_popular_domains(self, limit=10):
        """Get most bookmarked domains"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT json_extract(metadata, '$.domain') as domain, COUNT(*) as count
            FROM bookmarks
            GROUP BY domain
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        return dict(cursor.fetchall())
    
    def get_bookmark_stats(self):
        """Get bookmark statistics"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        # Total bookmarks
        cursor.execute("SELECT COUNT(*) FROM bookmarks")
        stats['total'] = cursor.fetchone()[0]
        
        # With linked files
        cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE downloaded_file_id IS NOT NULL")
        stats['with_files'] = cursor.fetchone()[0]
        
        # Recent (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM bookmarks
            WHERE created_date > ?
        """, ((datetime.now().replace(day=datetime.now().day-7)).isoformat(),))
        stats['recent_7days'] = cursor.fetchone()[0]
        
        # Most accessed
        cursor.execute("""
            SELECT title, access_count FROM bookmarks
            ORDER BY access_count DESC LIMIT 5
        """)
        stats['most_accessed'] = [{'title': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Top tags
        cursor.execute("SELECT tags FROM bookmarks WHERE tags IS NOT NULL AND tags != ''")
        tag_counts = {}
        for (tags_str,) in cursor.fetchall():
            for tag in tags_str.split(','):
                tag = tag.strip()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        stats['top_tags'] = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return stats
    
    def import_from_browser(self, browser='chrome', profile='Default'):
        """
        Import bookmarks from browser (macOS)
        Supports Chrome, Firefox, Safari
        """
        bookmarks_paths = {
            'chrome': os.path.expanduser(f'~/Library/Application Support/Google/Chrome/{profile}/Bookmarks'),
            'firefox': os.path.expanduser('~/Library/Application Support/Firefox/Profiles/'),
            'safari': os.path.expanduser('~/Library/Safari/Bookmarks.plist')
        }
        
        path = bookmarks_paths.get(browser.lower())
        if not path or not os.path.exists(path):
            return {'success': False, 'error': f'Bookmarks not found for {browser}'}
        
        imported = 0
        
        try:
            if browser.lower() == 'chrome':
                # Chrome bookmarks are JSON
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Parse Chrome bookmark structure
                def parse_chrome_bookmarks(node, folder=''):
                    nonlocal imported
                    if node.get('type') == 'url':
                        self.add_bookmark(
                            url=node['url'],
                            title=node['name'],
                            tags=folder,
                            source='Chrome Import'
                        )
                        imported += 1
                    elif node.get('type') == 'folder':
                        for child in node.get('children', []):
                            parse_chrome_bookmarks(child, node['name'])
                
                # Start parsing
                roots = data.get('roots', {})
                for key in ['bookmark_bar', 'other', 'synced']:
                    if key in roots:
                        for child in roots[key].get('children', []):
                            parse_chrome_bookmarks(child)
            
            return {'success': True, 'imported': imported}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


if __name__ == "__main__":
    # Test bookmark manager
    from file_indexer import FileDatabase
    
    print("Testing Bookmark Manager...")
    print(f"Web scraping available: {WEB_SCRAPING_AVAILABLE}")
    
    db = FileDatabase()
    manager = BookmarkManager(db)
    
    # Add test bookmark
    print("\n🔖 Adding test bookmark...")
    bookmark_id = manager.add_bookmark(
        url="https://github.com",
        title="GitHub",
        description="Where the world builds software",
        tags=['development', 'code', 'git'],
        source='test'
    )
    print(f"Added bookmark ID: {bookmark_id}")
    
    # Search bookmarks
    print("\n🔍 Searching bookmarks...")
    results = manager.search_bookmarks(query='github')
    print(f"Found {len(results)} bookmarks")
    
    # Get stats
    print("\n📊 Bookmark Statistics:")
    stats = manager.get_bookmark_stats()
    print(f"Total bookmarks: {stats['total']}")
    print(f"Recent (7 days): {stats['recent_7days']}")
    print(f"With files: {stats['with_files']}")
    
    if stats['most_accessed']:
        print("\nMost accessed:")
        for item in stats['most_accessed'][:3]:
            print(f"  - {item['title']}: {item['count']} times")
    
    db.close()
    print("\n✅ Bookmark manager test complete!")

