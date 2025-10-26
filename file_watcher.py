#!/usr/bin/env python3
"""
Real-Time File Watcher
Monitor folders and automatically organize files as they arrive!
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileOrganizerHandler(FileSystemEventHandler):
    """Handle file system events"""
    
    def __init__(self, file_db, ai_tagger=None, auto_organize=True):
        self.db = file_db
        self.ai_tagger = ai_tagger
        self.auto_organize = auto_organize
        self.processing = set()  # Avoid duplicate processing
    
    def on_created(self, event):
        """Called when a file is created"""
        if event.is_directory:
            return
        
        filepath = event.src_path
        
        # Avoid processing same file multiple times
        if filepath in self.processing:
            return
        
        self.processing.add(filepath)
        
        # Wait a bit for file to be fully written
        time.sleep(0.5)
        
        if not os.path.exists(filepath):
            self.processing.discard(filepath)
            return
        
        print(f"📥 New file detected: {Path(filepath).name}")
        
        try:
            # Index the file
            from file_indexer import FileIndexer
            indexer = FileIndexer(self.db)
            
            file_info = indexer.extract_file_info(filepath)
            if file_info:
                file_id = self.db.add_file(file_info)
                
                # Auto-tag with AI
                if self.ai_tagger and file_id:
                    print(f"   🤖 AI tagging...")
                    self.ai_tagger.tag_file(file_id, filepath)
                
                # Auto-organize
                if self.auto_organize:
                    self._auto_organize(filepath, file_info)
                
                print(f"   ✅ Processed: {Path(filepath).name}")
        
        except Exception as e:
            print(f"   ❌ Error processing {filepath}: {e}")
        
        finally:
            self.processing.discard(filepath)
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
        
        filepath = event.src_path
        
        # Update in database if already indexed
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM files WHERE path = ?", (filepath,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute("""
                UPDATE files
                SET modified_date = ?
                WHERE path = ?
            """, (datetime.now().isoformat(), filepath))
            self.db.conn.commit()
    
    def _auto_organize(self, filepath, file_info):
        """Auto-organize file based on type"""
        folder = Path(filepath).parent
        
        # Only organize if in Downloads or Desktop
        if 'Downloads' not in str(folder) and 'Desktop' not in str(folder):
            return
        
        # Determine category
        extension = file_info.get('extension', '').lower()
        
        categories = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.heic'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv'],
            'Music': ['.mp3', '.wav', '.flac', '.m4a', '.aac'],
            'Archives': ['.zip', '.tar', '.gz', '.rar', '.7z'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp'],
            'Spreadsheets': ['.xlsx', '.xls', '.csv', '.ods'],
            'Presentations': ['.pptx', '.ppt', '.key', '.odp']
        }
        
        target_category = None
        for category, extensions in categories.items():
            if extension in extensions:
                target_category = category
                break
        
        if target_category:
            target_folder = folder / target_category
            target_folder.mkdir(exist_ok=True)
            
            target_path = target_folder / Path(filepath).name
            
            # Avoid conflicts
            if target_path.exists():
                base = target_path.stem
                ext = target_path.suffix
                counter = 1
                while (target_folder / f"{base}_{counter}{ext}").exists():
                    counter += 1
                target_path = target_folder / f"{base}_{counter}{ext}"
            
            try:
                import shutil
                shutil.move(filepath, target_path)
                print(f"   📁 Moved to: {target_category}/")
                
                # Update database
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    UPDATE files
                    SET path = ?, folder_location = ?
                    WHERE path = ?
                """, (str(target_path), str(target_folder), filepath))
                self.db.conn.commit()
                
            except Exception as e:
                print(f"   ⚠️  Could not move file: {e}")


class FileWatcher:
    """Watch folders for changes and auto-organize"""
    
    def __init__(self, file_db, ai_tagger=None):
        self.db = file_db
        self.ai_tagger = ai_tagger
        self.observers = {}
        self.running = False
    
    def start_watching(self, folders, auto_organize=True):
        """
        Start watching folders
        
        Args:
            folders: List of folder paths to watch
            auto_organize: Whether to auto-organize new files
        """
        if self.running:
            print("⚠️  File watcher already running")
            return
        
        self.running = True
        
        for folder in folders:
            folder = os.path.expanduser(folder)
            if not os.path.exists(folder):
                print(f"⚠️  Folder not found: {folder}")
                continue
            
            handler = FileOrganizerHandler(self.db, self.ai_tagger, auto_organize)
            observer = Observer()
            observer.schedule(handler, folder, recursive=True)
            observer.start()
            
            self.observers[folder] = observer
            print(f"👁️  Watching: {folder}")
        
        print(f"\n✨ File watcher active! Monitoring {len(self.observers)} folder(s)")
        print("   New files will be automatically indexed and organized")
        print("   Press Ctrl+C to stop\n")
    
    def stop_watching(self):
        """Stop all watchers"""
        if not self.running:
            return
        
        for folder, observer in self.observers.items():
            observer.stop()
            observer.join()
            print(f"🛑 Stopped watching: {folder}")
        
        self.observers.clear()
        self.running = False
        print("✅ File watcher stopped")
    
    def watch_in_background(self, folders, auto_organize=True):
        """Start watching in background thread"""
        if self.running:
            return
        
        thread = threading.Thread(
            target=self.start_watching,
            args=(folders, auto_organize),
            daemon=True
        )
        thread.start()
        
        return thread


if __name__ == "__main__":
    print("👁️  Real-Time File Watcher")
    print("="*60)
    
    from file_indexer import FileDatabase
    from ai_tagger import AITagger
    
    db = FileDatabase()
    ai_tagger = AITagger(db)
    watcher = FileWatcher(db, ai_tagger)
    
    # Default folders to watch
    default_folders = [
        "~/Downloads",
        "~/Desktop"
    ]
    
    print("\n🎯 This will watch folders and auto-organize files as they arrive!")
    print("\nDefault folders:")
    for folder in default_folders:
        print(f"   • {folder}")
    
    print("\n💡 Usage:")
    print("   python file_watcher.py")
    print("\n   Or from CLI:")
    print("   ./o WATCH@Downloads")
    print("   ./o WATCH --start")
    print("   ./o WATCH --stop")
    
    print("\n⚠️  To actually start watching, use the CLI command above")
    print("   (This prevents accidental background processes)\n")
    
    db.close()

