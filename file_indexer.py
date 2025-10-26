#!/usr/bin/env python3
"""
File Indexer for File Organizer
Scans folders, extracts content, and stores in SQLite database
"""

import os
import sqlite3
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
import PyPDF2


class FileDatabase:
    """Manages SQLite database for file index"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            config_dir = os.path.expanduser("~/.fileorganizer")
            os.makedirs(config_dir, exist_ok=True)
            db_path = os.path.join(config_dir, "files.db")
        
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Check if this is a new database or needs migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
        files_table_exists = cursor.fetchone() is not None
        
        # Files table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                extension TEXT,
                size INTEGER,
                created_date TEXT,
                modified_date TEXT,
                last_indexed TEXT,
                file_hash TEXT,
                mime_type TEXT,
                folder_location TEXT,
                content_text TEXT,
                ai_summary TEXT,
                ai_tags TEXT,
                project TEXT,
                status TEXT DEFAULT 'active',
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                is_duplicate INTEGER DEFAULT 0,
                duplicate_of INTEGER,
                ocr_text TEXT,
                is_screenshot INTEGER DEFAULT 0,
                hide_from_app INTEGER DEFAULT 0,
                source TEXT DEFAULT 'filesystem',
                source_id TEXT
            )
        """)
        
        # Tags table (for easy filtering)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                tag TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # Conversation history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                intent TEXT,
                files_mentioned TEXT,
                action_taken TEXT,
                success INTEGER DEFAULT 1
            )
        """)
        
        # User preferences and learned patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_key TEXT NOT NULL,
                pattern_value TEXT,
                frequency INTEGER DEFAULT 1,
                last_used TEXT,
                confidence REAL DEFAULT 0.5,
                UNIQUE(pattern_type, pattern_key)
            )
        """)
        
        # File interaction patterns (what files user accesses together)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file1_id INTEGER,
                file2_id INTEGER,
                relationship_type TEXT,
                strength REAL DEFAULT 1.0,
                last_observed TEXT,
                FOREIGN KEY (file1_id) REFERENCES files(id),
                FOREIGN KEY (file2_id) REFERENCES files(id)
            )
        """)
        
        # Search history for learning search patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                results_count INTEGER,
                clicked_file_id INTEGER,
                success INTEGER DEFAULT 0,
                FOREIGN KEY (clicked_file_id) REFERENCES files(id)
            )
        """)
        
        # Migrate existing files table if needed
        if files_table_exists:
            # Check if new columns exist
            cursor.execute("PRAGMA table_info(files)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'access_count' not in columns:
                cursor.execute("ALTER TABLE files ADD COLUMN access_count INTEGER DEFAULT 0")
            if 'last_accessed' not in columns:
                cursor.execute("ALTER TABLE files ADD COLUMN last_accessed TEXT")
        
        # Indexes for faster searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filename ON files(filename)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON tags(tag)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project ON files(project)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content ON files(content_text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversations(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern_type ON learned_patterns(pattern_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_query ON search_history(query)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_accessed ON files(last_accessed)")
        
        # Full-text search virtual table for better content search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                filename, content_text, ai_summary, ai_tags, 
                content=files, content_rowid=id
            )
        """)
        
        # Smart folders (saved searches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                query TEXT NOT NULL,
                icon TEXT DEFAULT '📁',
                color TEXT DEFAULT '#3b82f6',
                created_date TEXT NOT NULL,
                last_used TEXT,
                use_count INTEGER DEFAULT 0
            )
        """)
        
        # Trash/deleted files tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trash (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                deleted_date TEXT NOT NULL,
                deleted_by TEXT DEFAULT 'user',
                file_data BLOB,
                metadata TEXT,
                can_recover INTEGER DEFAULT 1
            )
        """)
        
        # Reminders and nudges
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                reminder_type TEXT NOT NULL,
                reminder_date TEXT NOT NULL,
                message TEXT,
                is_active INTEGER DEFAULT 1,
                created_date TEXT NOT NULL,
                triggered_date TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # Smart suggestions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_type TEXT NOT NULL,
                message TEXT NOT NULL,
                action_data TEXT,
                priority INTEGER DEFAULT 5,
                created_date TEXT NOT NULL,
                dismissed INTEGER DEFAULT 0,
                accepted INTEGER DEFAULT 0
            )
        """)
        
        # File aging rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aging_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_pattern TEXT NOT NULL,
                age_days INTEGER NOT NULL,
                action TEXT NOT NULL,
                destination TEXT,
                enabled INTEGER DEFAULT 1,
                created_date TEXT NOT NULL
            )
        """)
        
        # File events for temporal tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                event_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # Bookmarks and URLs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                description TEXT,
                tags TEXT,
                source TEXT,
                created_date TEXT NOT NULL,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                downloaded_file_id INTEGER,
                metadata TEXT,
                FOREIGN KEY (downloaded_file_id) REFERENCES files(id)
            )
        """)
        
        # Bulk operations history (for undo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bulk_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                operation_date TEXT NOT NULL,
                files_affected TEXT NOT NULL,
                original_state TEXT NOT NULL,
                new_state TEXT,
                can_undo INTEGER DEFAULT 1,
                completed INTEGER DEFAULT 0
            )
        """)
        
        # Screenshot metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshot_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                capture_date TEXT,
                source_app TEXT,
                screen_region TEXT,
                has_text INTEGER DEFAULT 0,
                extracted_text TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # Mobile sync queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mobile_sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                action TEXT NOT NULL,
                sync_date TEXT NOT NULL,
                synced INTEGER DEFAULT 0,
                device_id TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        """)
        
        # Indices for new tables
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_events_date ON file_events(event_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_url ON bookmarks(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bulk_ops_date ON bulk_operations(operation_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenshot_file ON screenshot_metadata(file_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(reminder_date)")
        
        self.conn.commit()
        
        # Migrate existing database to add new columns
        self._migrate_database()
    
    def _migrate_database(self):
        """Add new columns to existing tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Check and add new columns to files table
        cursor.execute("PRAGMA table_info(files)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = {
            'is_duplicate': 'INTEGER DEFAULT 0',
            'duplicate_of': 'INTEGER',
            'ocr_text': 'TEXT',
            'is_screenshot': 'INTEGER DEFAULT 0',
            'hide_from_app': 'INTEGER DEFAULT 0',
            'source': 'TEXT DEFAULT "filesystem"',
            'source_id': 'TEXT'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"Note: Could not add {col_name}: {e}")
        
        self.conn.commit()
    
    def get_file_hash(self, filepath):
        """Generate hash of file for change detection"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"Error hashing {filepath}: {e}")
            return None
    
    def file_exists(self, filepath):
        """Check if file is already in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, file_hash FROM files WHERE path = ?", (filepath,))
        return cursor.fetchone()
    
    def add_file(self, file_info):
        """Add or update file in database"""
        cursor = self.conn.cursor()
        
        # Check if file exists
        existing = self.file_exists(file_info['path'])
        
        if existing:
            # Update existing file
            cursor.execute("""
                UPDATE files SET
                    filename = ?,
                    extension = ?,
                    size = ?,
                    modified_date = ?,
                    last_indexed = ?,
                    file_hash = ?,
                    content_text = ?,
                    ai_summary = ?,
                    ai_tags = ?,
                    project = ?
                WHERE path = ?
            """, (
                file_info['filename'],
                file_info['extension'],
                file_info['size'],
                file_info['modified_date'],
                file_info['last_indexed'],
                file_info['file_hash'],
                file_info.get('content_text', ''),
                file_info.get('ai_summary', ''),
                file_info.get('ai_tags', ''),
                file_info.get('project', ''),
                file_info['path']
            ))
            file_id = existing[0]
        else:
            # Insert new file
            cursor.execute("""
                INSERT INTO files (
                    path, filename, extension, size, created_date,
                    modified_date, last_indexed, file_hash, mime_type,
                    folder_location, content_text, ai_summary, ai_tags, project
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_info['path'],
                file_info['filename'],
                file_info['extension'],
                file_info['size'],
                file_info['created_date'],
                file_info['modified_date'],
                file_info['last_indexed'],
                file_info['file_hash'],
                file_info['mime_type'],
                file_info['folder_location'],
                file_info.get('content_text', ''),
                file_info.get('ai_summary', ''),
                file_info.get('ai_tags', ''),
                file_info.get('project', '')
            ))
            file_id = cursor.lastrowid
        
        # Add tags
        if 'tags' in file_info and file_info['tags']:
            # Clear old tags
            cursor.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
            # Add new tags
            for tag in file_info['tags']:
                cursor.execute("INSERT INTO tags (file_id, tag) VALUES (?, ?)", (file_id, tag))
        
        self.conn.commit()
        return file_id
    
    def remove_file(self, filepath):
        """Remove file from database (when file is deleted)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE path = ?", (filepath,))
        self.conn.commit()
    
    def search_files(self, query, limit=50):
        """Search files by name, content, tags, or project"""
        cursor = self.conn.cursor()
        
        # Search in multiple fields
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT DISTINCT f.* FROM files f
            LEFT JOIN tags t ON f.id = t.file_id
            WHERE 
                f.filename LIKE ? OR
                f.content_text LIKE ? OR
                f.ai_summary LIKE ? OR
                f.ai_tags LIKE ? OR
                f.project LIKE ? OR
                t.tag LIKE ?
            AND f.status = 'active'
            ORDER BY f.modified_date DESC
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, 
              search_pattern, search_pattern, search_pattern, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def get_recent_files(self, limit=20):
        """Get recently modified files"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM files
            WHERE status = 'active'
            ORDER BY modified_date DESC
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def get_stats(self):
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total files
        cursor.execute("SELECT COUNT(*) FROM files WHERE status = 'active'")
        stats['total_files'] = cursor.fetchone()[0]
        
        # Files by folder
        cursor.execute("""
            SELECT folder_location, COUNT(*) as count 
            FROM files 
            WHERE status = 'active'
            GROUP BY folder_location
        """)
        stats['by_folder'] = dict(cursor.fetchall())
        
        # Files by extension
        cursor.execute("""
            SELECT extension, COUNT(*) as count 
            FROM files 
            WHERE status = 'active'
            GROUP BY extension
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['by_extension'] = dict(cursor.fetchall())
        
        # Top tags
        cursor.execute("""
            SELECT tag, COUNT(*) as count 
            FROM tags t
            JOIN files f ON t.file_id = f.id
            WHERE f.status = 'active'
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 20
        """)
        stats['top_tags'] = dict(cursor.fetchall())
        
        return stats
    
    def log_conversation(self, user_message, assistant_response, intent=None, files_mentioned=None, action_taken=None, success=True):
        """Log a conversation for learning"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conversations 
            (timestamp, user_message, assistant_response, intent, files_mentioned, action_taken, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_message,
            assistant_response,
            intent,
            files_mentioned,
            action_taken,
            1 if success else 0
        ))
        self.conn.commit()
    
    def get_recent_conversations(self, limit=10):
        """Get recent conversation history"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, user_message, assistant_response, intent, action_taken
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        columns = ['timestamp', 'user_message', 'assistant_response', 'intent', 'action_taken']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def learn_pattern(self, pattern_type, pattern_key, pattern_value, confidence=0.5):
        """Learn or reinforce a user pattern"""
        cursor = self.conn.cursor()
        
        # Check if pattern exists
        cursor.execute("""
            SELECT id, frequency, confidence FROM learned_patterns
            WHERE pattern_type = ? AND pattern_key = ?
        """, (pattern_type, pattern_key))
        
        existing = cursor.fetchone()
        
        if existing:
            # Reinforce existing pattern
            pattern_id, frequency, old_confidence = existing
            new_frequency = frequency + 1
            # Update confidence using exponential moving average
            new_confidence = old_confidence * 0.7 + confidence * 0.3
            
            cursor.execute("""
                UPDATE learned_patterns
                SET frequency = ?, confidence = ?, last_used = ?, pattern_value = ?
                WHERE id = ?
            """, (new_frequency, new_confidence, datetime.now().isoformat(), pattern_value, pattern_id))
        else:
            # Create new pattern
            cursor.execute("""
                INSERT INTO learned_patterns 
                (pattern_type, pattern_key, pattern_value, frequency, last_used, confidence)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (pattern_type, pattern_key, pattern_value, datetime.now().isoformat(), confidence))
        
        self.conn.commit()
    
    def get_learned_patterns(self, pattern_type=None, min_confidence=0.3):
        """Get learned patterns, optionally filtered by type"""
        cursor = self.conn.cursor()
        
        if pattern_type:
            cursor.execute("""
                SELECT pattern_type, pattern_key, pattern_value, frequency, confidence
                FROM learned_patterns
                WHERE pattern_type = ? AND confidence >= ?
                ORDER BY frequency DESC, confidence DESC
            """, (pattern_type, min_confidence))
        else:
            cursor.execute("""
                SELECT pattern_type, pattern_key, pattern_value, frequency, confidence
                FROM learned_patterns
                WHERE confidence >= ?
                ORDER BY frequency DESC, confidence DESC
            """, (min_confidence,))
        
        columns = ['pattern_type', 'pattern_key', 'pattern_value', 'frequency', 'confidence']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def get_learned_patterns_by_type(self, pattern_type):
        """Get all learned patterns of a specific type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT pattern_type, pattern_key, pattern_value, frequency, confidence, last_used
            FROM learned_patterns
            WHERE pattern_type = ?
            ORDER BY last_used DESC, frequency DESC
        """, (pattern_type,))
        
        columns = ['pattern_type', 'pattern_key', 'pattern_value', 'frequency', 'confidence', 'last_used']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def log_search(self, query, results_count, clicked_file_id=None, success=False):
        """Log a search for learning search patterns"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO search_history (timestamp, query, results_count, clicked_file_id, success)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), query, results_count, clicked_file_id, 1 if success else 0))
        self.conn.commit()
    
    def record_file_access(self, file_path):
        """Record when a file is accessed"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE files 
            SET access_count = access_count + 1, last_accessed = ?
            WHERE path = ?
        """, (datetime.now().isoformat(), file_path))
        self.conn.commit()
    
    def get_frequently_accessed_files(self, limit=20):
        """Get most frequently accessed files"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT path, filename, access_count, last_accessed, project
            FROM files
            WHERE status = 'active' AND access_count > 0
            ORDER BY access_count DESC, last_accessed DESC
            LIMIT ?
        """, (limit,))
        
        columns = ['path', 'filename', 'access_count', 'last_accessed', 'project']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class FileIndexer:
    """Scans folders and indexes files"""
    
    def __init__(self, db, activity_log=None):
        self.db = db
        self.activity_log = activity_log
        self.supported_text_extensions = [
            '.txt', '.md', '.py', '.js', '.html', '.css', 
            '.json', '.xml', '.csv', '.log'
        ]
        self.supported_pdf_extensions = ['.pdf']
        self.supported_image_extensions = ['.png', '.jpg', '.jpeg', '.gif']
    
    def log_activity(self, action, filename, details):
        """Log activity to the activity log widget"""
        if self.activity_log:
            self.activity_log.add_activity(action, filename, details)
    
    def should_index_file(self, filepath):
        """Determine if file should be indexed"""
        # Skip hidden files
        if os.path.basename(filepath).startswith('.'):
            return False
        
        # Skip system files
        if '__MACOSX' in filepath or '.DS_Store' in filepath:
            return False
        
        # Skip very large files (>50MB)
        try:
            if os.path.getsize(filepath) > 50 * 1024 * 1024:
                return False
        except:
            return False
        
        return True
    
    def extract_text_content(self, filepath):
        """Extract text content from file"""
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            # Plain text files
            if ext in self.supported_text_extensions:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()[:10000]  # First 10k chars
            
            # PDFs
            elif ext in self.supported_pdf_extensions:
                return self.extract_pdf_text(filepath)
            
            # Images (OCR - optional, requires tesseract)
            # elif ext in self.supported_image_extensions:
            #     return self.extract_image_text(filepath)
            
        except Exception as e:
            print(f"Error extracting text from {filepath}: {e}")
        
        return ""
    
    def extract_pdf_text(self, filepath):
        """Extract text from PDF"""
        try:
            text = ""
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                # Read first 10 pages max
                for page_num in range(min(10, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text[:10000]  # First 10k chars
        except Exception as e:
            print(f"Error reading PDF {filepath}: {e}")
            return ""
    
    def index_file(self, filepath):
        """Index a single file"""
        if not self.should_index_file(filepath):
            return None
        
        try:
            stat = os.stat(filepath)
            file_hash = self.db.get_file_hash(filepath)
            
            # Check if file needs updating
            existing = self.db.file_exists(filepath)
            if existing and existing[1] == file_hash:
                # File hasn't changed, skip
                return None
            
            # Extract file info
            file_info = {
                'path': filepath,
                'filename': os.path.basename(filepath),
                'extension': os.path.splitext(filepath)[1].lower(),
                'size': stat.st_size,
                'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'last_indexed': datetime.now().isoformat(),
                'file_hash': file_hash,
                'mime_type': mimetypes.guess_type(filepath)[0] or 'unknown',
                'folder_location': os.path.dirname(filepath)
            }
            
            # Extract content
            content = self.extract_text_content(filepath)
            if content:
                file_info['content_text'] = content
            
            # Add to database (AI tagging will happen in next step)
            file_id = self.db.add_file(file_info)
            
            # Log activity
            self.log_activity(
                "Indexed",
                file_info['filename'],
                f"Added to database (ID: {file_id})"
            )
            
            return file_id
            
        except Exception as e:
            print(f"Error indexing {filepath}: {e}")
            self.log_activity(
                "Error",
                os.path.basename(filepath),
                f"Failed to index: {str(e)}"
            )
            return None
    
    def scan_folder(self, folder_path, recursive=True):
        """Scan a folder and index all files"""
        indexed_count = 0
        skipped_count = 0
        
        if not os.path.exists(folder_path):
            print(f"Folder not found: {folder_path}")
            self.log_activity("Error", folder_path, "Folder not found")
            return indexed_count, skipped_count
        
        print(f"Scanning: {folder_path}")
        self.log_activity(
            "Scan Started",
            os.path.basename(folder_path),
            f"Scanning folder {'(recursive)' if recursive else '(non-recursive)'}"
        )
        
        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        result = self.index_file(filepath)
                        if result:
                            indexed_count += 1
                        else:
                            skipped_count += 1
            else:
                for filename in os.listdir(folder_path):
                    filepath = os.path.join(folder_path, filename)
                    if os.path.isfile(filepath):
                        result = self.index_file(filepath)
                        if result:
                            indexed_count += 1
                        else:
                            skipped_count += 1
        
        except Exception as e:
            print(f"Error scanning folder {folder_path}: {e}")
            self.log_activity("Error", os.path.basename(folder_path), f"Scan failed: {str(e)}")
        
        # Log completion
        self.log_activity(
            "Scan Complete",
            os.path.basename(folder_path),
            f"Indexed {indexed_count} files, skipped {skipped_count}"
        )
        
        return indexed_count, skipped_count


if __name__ == "__main__":
    # Test the indexer
    print("Testing File Indexer...")
    
    db = FileDatabase()
    indexer = FileIndexer(db)
    
    # Index Downloads folder
    downloads = os.path.expanduser("~/Downloads")
    indexed, skipped = indexer.scan_folder(downloads, recursive=False)
    
    print(f"\nIndexed: {indexed} files")
    print(f"Skipped: {skipped} files")
    
    # Show stats
    stats = db.get_stats()
    print(f"\nDatabase Stats:")
    print(f"Total files: {stats['total_files']}")
    print(f"By extension: {stats['by_extension']}")
    
    db.close()