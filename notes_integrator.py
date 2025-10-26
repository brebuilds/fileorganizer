#!/usr/bin/env python3
"""
Apple Notes Integration Module
Indexes notes from Apple Notes app for RAG system
"""

import sqlite3
import os
import gzip
from datetime import datetime
import re


class NotesIntegrator:
    """Integrate Apple Notes into the RAG system"""
    
    def __init__(self, file_db):
        self.file_db = file_db
        # Apple Notes database location
        self.notes_db_path = os.path.expanduser(
            "~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
        )
    
    def is_notes_available(self):
        """Check if Apple Notes database exists"""
        return os.path.exists(self.notes_db_path)
    
    def get_all_notes(self):
        """Extract all notes from Apple Notes database"""
        if not self.is_notes_available():
            print("❌ Apple Notes database not found")
            return []
        
        notes = []
        
        try:
            # Connect to Notes database (read-only)
            conn = sqlite3.connect(f"file:{self.notes_db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            # Query to get notes with their content
            # Apple Notes stores content in ZICCLOUDSYNCINGOBJECT table
            query = """
                SELECT 
                    z.Z_PK as id,
                    z.ZTITLE1 as title,
                    z.ZSNIPPET as snippet,
                    datetime(z.ZCREATIONDATE1 + 978307200, 'unixepoch') as created,
                    datetime(z.ZMODIFICATIONDATE1 + 978307200, 'unixepoch') as modified,
                    n.ZDATA as content_data,
                    f.ZFILENAME as attachment_filename
                FROM ZICCLOUDSYNCINGOBJECT z
                LEFT JOIN ZICNOTEDATA n ON z.ZNOTEDATA = n.Z_PK
                LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON z.Z_PK = f.ZNOTE
                WHERE z.ZTITLE1 IS NOT NULL
                    AND z.ZMARKEDFORDELETION = 0
                ORDER BY z.ZMODIFICATIONDATE1 DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                note_id, title, snippet, created, modified, content_data, attachment = row
                
                # Extract text content from compressed data
                content = ""
                if content_data:
                    try:
                        # Apple Notes stores content as gzipped protobuf
                        # We'll try to decompress and extract text
                        decompressed = gzip.decompress(content_data)
                        # Simple text extraction (not perfect, but works for most notes)
                        content = decompressed.decode('utf-8', errors='ignore')
                        # Clean up protobuf artifacts
                        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
                        content = ' '.join(content.split())
                    except:
                        # If decompression fails, use snippet
                        content = snippet or ""
                
                # Fallback to snippet if content extraction failed
                if not content or len(content) < 10:
                    content = snippet or title or ""
                
                notes.append({
                    'id': note_id,
                    'title': title or 'Untitled Note',
                    'content': content,
                    'snippet': snippet or '',
                    'created': created,
                    'modified': modified,
                    'attachment': attachment,
                    'source': 'Apple Notes'
                })
            
            conn.close()
            return notes
            
        except sqlite3.Error as e:
            print(f"❌ Error reading Apple Notes database: {e}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return []
    
    def index_notes(self, activity_log=None):
        """Index all Apple Notes into the file database"""
        if not self.is_notes_available():
            print("❌ Apple Notes not available on this system")
            return 0, 0
        
        notes = self.get_all_notes()
        
        if not notes:
            print("⚠️ No notes found in Apple Notes")
            return 0, 0
        
        indexed_count = 0
        skipped_count = 0
        
        for note in notes:
            try:
                # Check if note already indexed
                existing = self.file_db.conn.execute(
                    "SELECT id FROM files WHERE source = ? AND source_id = ?",
                    ('Apple Notes', str(note['id']))
                ).fetchone()
                
                if existing:
                    # Update existing note
                    self.file_db.conn.execute("""
                        UPDATE files 
                        SET content = ?,
                            modified_date = ?,
                            summary = ?
                        WHERE id = ?
                    """, (
                        note['content'][:5000],  # Store first 5000 chars
                        note['modified'],
                        note['snippet'][:500],
                        existing[0]
                    ))
                    skipped_count += 1
                else:
                    # Add new note
                    file_info = {
                        'filename': note['title'],
                        'filepath': f"notes://{note['id']}",
                        'extension': '.note',
                        'size': len(note['content']),
                        'created': note['created'],
                        'modified': note['modified'],
                        'content': note['content'][:5000],
                        'summary': note['snippet'][:500],
                        'source': 'Apple Notes',
                        'source_id': str(note['id'])
                    }
                    
                    file_id = self.file_db.add_file(file_info)
                    
                    # Log activity
                    if activity_log:
                        activity_log.add_activity(
                            "Indexed",
                            note['title'],
                            f"Apple Note added (ID: {file_id})"
                        )
                    
                    indexed_count += 1
            
            except Exception as e:
                print(f"❌ Error indexing note '{note['title']}': {e}")
                if activity_log:
                    activity_log.add_activity(
                        "Error",
                        note['title'],
                        f"Failed to index: {str(e)}"
                    )
                skipped_count += 1
        
        self.file_db.conn.commit()
        return indexed_count, skipped_count
    
    def get_note_by_id(self, note_id):
        """Get a specific note by ID"""
        notes = self.get_all_notes()
        for note in notes:
            if note['id'] == note_id:
                return note
        return None
    
    def search_notes(self, query):
        """Search Apple Notes"""
        notes = self.get_all_notes()
        query_lower = query.lower()
        
        results = []
        for note in notes:
            # Search in title and content
            if (query_lower in note['title'].lower() or 
                query_lower in note['content'].lower()):
                results.append(note)
        
        return results
    
    def get_stats(self):
        """Get Apple Notes statistics"""
        notes = self.get_all_notes()
        
        if not notes:
            return {
                'total': 0,
                'indexed': 0,
                'available': False
            }
        
        # Check how many are already indexed
        cursor = self.file_db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files WHERE source = 'Apple Notes'")
        indexed_count = cursor.fetchone()[0]
        
        return {
            'total': len(notes),
            'indexed': indexed_count,
            'available': True,
            'unindexed': len(notes) - indexed_count
        }


def test_notes_integration():
    """Test Apple Notes integration"""
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    integrator = NotesIntegrator(db)
    
    print("🔍 Checking Apple Notes availability...")
    if not integrator.is_notes_available():
        print("❌ Apple Notes database not found")
        return
    
    print("✅ Apple Notes found!")
    
    print("\n📊 Getting Apple Notes statistics...")
    stats = integrator.get_stats()
    print(f"Total notes: {stats['total']}")
    print(f"Already indexed: {stats['indexed']}")
    print(f"Not yet indexed: {stats['unindexed']}")
    
    print("\n📝 Fetching first 5 notes...")
    notes = integrator.get_all_notes()[:5]
    for i, note in enumerate(notes, 1):
        print(f"\n{i}. {note['title']}")
        print(f"   Modified: {note['modified']}")
        print(f"   Preview: {note['snippet'][:100]}...")
    
    print("\n🔄 Indexing notes...")
    indexed, skipped = integrator.index_notes()
    print(f"✅ Indexed: {indexed}")
    print(f"⏭️ Skipped: {skipped}")


if __name__ == "__main__":
    test_notes_integration()

