#!/usr/bin/env python3
"""
Temporal Tracker - Track when files appear and support time-based queries
Answers questions like "what did I download yesterday?"
"""

from datetime import datetime, timedelta
import re


class TemporalTracker:
    """Tracks file timeline and parses natural language dates"""
    
    def __init__(self, file_db):
        self.db = file_db
        self.init_temporal_tables()
    
    def init_temporal_tables(self):
        """Create tables for temporal tracking"""
        cursor = self.db.conn.cursor()
        
        # File events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                event_type TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # Index for fast temporal queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_timestamp 
            ON file_events(event_timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_type 
            ON file_events(event_type)
        """)
        
        self.db.conn.commit()
    
    def log_file_event(self, file_id, event_type, details=None):
        """
        Log a file event
        
        Event types:
        - 'discovered' - First time we saw this file
        - 'downloaded' - File appeared in Downloads folder
        - 'modified' - File was changed
        - 'accessed' - File was opened/viewed
        - 'moved' - File was moved
        - 'tagged' - File was tagged by AI
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO file_events (file_id, event_type, event_timestamp, details)
            VALUES (?, ?, ?, ?)
        """, (file_id, event_type, datetime.now().isoformat(), details))
        self.db.conn.commit()
    
    def parse_natural_date(self, text):
        """
        Parse natural language dates
        
        Supports:
        - "yesterday", "today", "this morning"
        - "last week", "last month"
        - "3 days ago", "2 hours ago"
        - "October 24", "Oct 24"
        - Date ranges: "last 7 days"
        """
        text = text.lower().strip()
        now = datetime.now()
        
        # Today
        if 'today' in text or 'this morning' in text or 'this afternoon' in text:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now
        
        # Yesterday
        if 'yesterday' in text:
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start, end
        
        # Last X days/hours/weeks
        patterns = [
            (r'last (\d+) days?', 'days'),
            (r'past (\d+) days?', 'days'),
            (r'last (\d+) hours?', 'hours'),
            (r'last (\d+) weeks?', 'weeks'),
            (r'last (\d+) months?', 'months'),
            (r'(\d+) days? ago', 'days'),
            (r'(\d+) hours? ago', 'hours'),
            (r'(\d+) weeks? ago', 'weeks'),
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, text)
            if match:
                n = int(match.group(1))
                if unit == 'hours':
                    start = now - timedelta(hours=n)
                elif unit == 'days':
                    start = now - timedelta(days=n)
                elif unit == 'weeks':
                    start = now - timedelta(weeks=n)
                elif unit == 'months':
                    start = now - timedelta(days=n*30)
                return start, now
        
        # This week
        if 'this week' in text:
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now
        
        # Last week
        if 'last week' in text:
            start = now - timedelta(days=now.weekday() + 7)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end
        
        # This month
        if 'this month' in text:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, now
        
        # Default: last 24 hours
        return now - timedelta(days=1), now
    
    def query_files_by_time(self, query, limit=20):
        """
        Query files using natural language time expressions
        
        Examples:
        - "files downloaded yesterday"
        - "files from last week"
        - "what did I get today"
        """
        # Parse the time expression
        start_time, end_time = self.parse_natural_date(query)
        
        # Detect what they're asking about
        is_download = any(word in query.lower() for word in ['download', 'got', 'received', 'new'])
        is_modified = any(word in query.lower() for word in ['changed', 'modified', 'edited', 'updated'])
        is_accessed = any(word in query.lower() for word in ['opened', 'viewed', 'accessed', 'looked at'])
        
        cursor = self.db.conn.cursor()
        
        # Query based on what they're asking
        if is_download:
            # Files that appeared in Downloads or were discovered in time range
            cursor.execute("""
                SELECT DISTINCT f.id, f.filename, f.path, f.created_date, 
                       f.folder_location, f.ai_summary
                FROM files f
                LEFT JOIN file_events e ON f.id = e.file_id
                WHERE f.status = 'active'
                AND (
                    (e.event_type IN ('discovered', 'downloaded') 
                     AND e.event_timestamp BETWEEN ? AND ?)
                    OR
                    (f.created_date BETWEEN ? AND ?)
                )
                ORDER BY f.created_date DESC
                LIMIT ?
            """, (start_time.isoformat(), end_time.isoformat(),
                  start_time.isoformat(), end_time.isoformat(), limit))
        
        elif is_modified:
            # Files modified in time range
            cursor.execute("""
                SELECT DISTINCT f.id, f.filename, f.path, f.modified_date,
                       f.folder_location, f.ai_summary
                FROM files f
                LEFT JOIN file_events e ON f.id = e.file_id
                WHERE f.status = 'active'
                AND (
                    (e.event_type = 'modified' 
                     AND e.event_timestamp BETWEEN ? AND ?)
                    OR
                    (f.modified_date BETWEEN ? AND ?)
                )
                ORDER BY f.modified_date DESC
                LIMIT ?
            """, (start_time.isoformat(), end_time.isoformat(),
                  start_time.isoformat(), end_time.isoformat(), limit))
        
        elif is_accessed:
            # Files accessed in time range
            cursor.execute("""
                SELECT f.id, f.filename, f.path, f.last_accessed,
                       f.folder_location, f.ai_summary, f.access_count
                FROM files f
                WHERE f.status = 'active'
                AND f.last_accessed BETWEEN ? AND ?
                ORDER BY f.last_accessed DESC
                LIMIT ?
            """, (start_time.isoformat(), end_time.isoformat(), limit))
        
        else:
            # Default: any activity in time range
            cursor.execute("""
                SELECT DISTINCT f.id, f.filename, f.path, f.created_date,
                       f.folder_location, f.ai_summary
                FROM files f
                LEFT JOIN file_events e ON f.id = e.file_id
                WHERE f.status = 'active'
                AND (
                    e.event_timestamp BETWEEN ? AND ?
                    OR f.created_date BETWEEN ? AND ?
                    OR f.modified_date BETWEEN ? AND ?
                )
                ORDER BY COALESCE(e.event_timestamp, f.modified_date, f.created_date) DESC
                LIMIT ?
            """, (start_time.isoformat(), end_time.isoformat(),
                  start_time.isoformat(), end_time.isoformat(),
                  start_time.isoformat(), end_time.isoformat(), limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'path': row[2],
                'timestamp': row[3],
                'location': row[4],
                'summary': row[5] if len(row) > 5 else None
            })
        
        return results, start_time, end_time
    
    def get_file_timeline(self, file_id):
        """Get complete timeline of a file"""
        cursor = self.db.conn.cursor()
        
        # Get file info
        cursor.execute("""
            SELECT filename, created_date, modified_date, last_accessed, access_count
            FROM files WHERE id = ?
        """, (file_id,))
        
        file_info = cursor.fetchone()
        if not file_info:
            return None
        
        # Get all events
        cursor.execute("""
            SELECT event_type, event_timestamp, details
            FROM file_events
            WHERE file_id = ?
            ORDER BY event_timestamp
        """, (file_id,))
        
        events = cursor.fetchall()
        
        return {
            'filename': file_info[0],
            'created': file_info[1],
            'modified': file_info[2],
            'last_accessed': file_info[3],
            'access_count': file_info[4],
            'events': [
                {
                    'type': e[0],
                    'timestamp': e[1],
                    'details': e[2]
                }
                for e in events
            ]
        }
    
    def get_activity_summary(self, days=7):
        """Get summary of recent activity"""
        start = datetime.now() - timedelta(days=days)
        cursor = self.db.conn.cursor()
        
        # Files discovered
        cursor.execute("""
            SELECT COUNT(DISTINCT file_id)
            FROM file_events
            WHERE event_type IN ('discovered', 'downloaded')
            AND event_timestamp > ?
        """, (start.isoformat(),))
        discovered = cursor.fetchone()[0]
        
        # Files modified
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE modified_date > ?
            AND status = 'active'
        """, (start.isoformat(),))
        modified = cursor.fetchone()[0]
        
        # Files accessed
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE last_accessed > ?
            AND status = 'active'
        """, (start.isoformat(),))
        accessed = cursor.fetchone()[0]
        
        return {
            'days': days,
            'discovered': discovered,
            'modified': modified,
            'accessed': accessed
        }


if __name__ == "__main__":
    print("⏰ Temporal Tracker - Track Files Over Time")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    tracker = TemporalTracker(db)
    
    # Test natural language parsing
    print("\n🧪 Testing natural language date parsing:\n")
    
    test_queries = [
        "yesterday",
        "today",
        "last week",
        "last 3 days",
        "2 hours ago",
        "this month"
    ]
    
    for query in test_queries:
        start, end = tracker.parse_natural_date(query)
        print(f"   '{query}'")
        print(f"      → {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
    
    # Test temporal queries
    print("\n\n🔍 Testing temporal file queries:\n")
    
    results, start, end = tracker.query_files_by_time("files from yesterday")
    print(f"   Files from yesterday: {len(results)} files")
    
    results, start, end = tracker.query_files_by_time("what did I download this week")
    print(f"   Downloads this week: {len(results)} files")
    
    # Activity summary
    print("\n\n📊 Recent Activity (Last 7 Days):\n")
    summary = tracker.get_activity_summary(days=7)
    print(f"   📁 New files: {summary['discovered']}")
    print(f"   ✏️  Modified: {summary['modified']}")
    print(f"   👁️  Accessed: {summary['accessed']}")
    
    print("\n" + "="*60)
    print("✅ Temporal tracking ready!")
    print("\nNow you can ask:")
    print("  • 'What did I download yesterday?'")
    print("  • 'Files from last week'")
    print("  • 'What changed today?'")
    
    db.close()

