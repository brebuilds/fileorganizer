#!/usr/bin/env python3
"""
File Operations Module
Handles moving, renaming, organizing files with safety checks
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


class FileOperations:
    """Safe file operations with undo capability"""
    
    def __init__(self, db, activity_log=None):
        self.db = db
        self.activity_log = activity_log
        self.operation_history = []
    
    def log_activity(self, action, filename, details):
        """Log activity to the activity log widget"""
        if self.activity_log:
            self.activity_log.add_activity(action, filename, details)
    
    def ensure_folder_exists(self, folder_path):
        """Create folder if it doesn't exist"""
        Path(folder_path).mkdir(parents=True, exist_ok=True)
    
    def move_file(self, source_path, dest_folder, new_name=None):
        """
        Move file to destination folder
        
        Args:
            source_path: Full path to source file
            dest_folder: Destination folder path
            new_name: Optional new filename
            
        Returns:
            New file path if successful, None if failed
        """
        
        if not os.path.exists(source_path):
            return None, f"Source file not found: {source_path}"
        
        # Ensure destination folder exists
        self.ensure_folder_exists(dest_folder)
        
        # Determine destination filename
        if new_name:
            dest_filename = new_name
        else:
            dest_filename = os.path.basename(source_path)
        
        dest_path = os.path.join(dest_folder, dest_filename)
        
        # Check if destination already exists
        if os.path.exists(dest_path):
            # Add timestamp to avoid collision
            base, ext = os.path.splitext(dest_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_filename = f"{base}_{timestamp}{ext}"
            dest_path = os.path.join(dest_folder, dest_filename)
        
        try:
            # Move the file
            shutil.move(source_path, dest_path)
            
            # Update database
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE files 
                SET path = ?, folder_location = ?, filename = ?
                WHERE path = ?
            """, (dest_path, dest_folder, dest_filename, source_path))
            self.db.conn.commit()
            
            # Log activity
            self.log_activity(
                "Moved",
                os.path.basename(source_path),
                f"From: {os.path.dirname(source_path)}\nTo: {dest_folder}"
            )
            
            # Save to history for undo
            self.operation_history.append({
                'type': 'move',
                'source': source_path,
                'dest': dest_path,
                'timestamp': datetime.now()
            })
            
            return dest_path, None
            
        except Exception as e:
            return None, f"Error moving file: {str(e)}"
    
    def rename_file(self, file_path, new_name):
        """
        Rename a file
        
        Args:
            file_path: Full path to file
            new_name: New filename (without path)
            
        Returns:
            New file path if successful, None if failed
        """
        
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
        
        folder = os.path.dirname(file_path)
        new_path = os.path.join(folder, new_name)
        
        # Check if new name already exists
        if os.path.exists(new_path):
            return None, f"A file named '{new_name}' already exists in that location"
        
        try:
            # Rename
            os.rename(file_path, new_path)
            
            # Update database
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE files 
                SET path = ?, filename = ?
                WHERE path = ?
            """, (new_path, new_name, file_path))
            self.db.conn.commit()
            
            # Log activity
            self.log_activity(
                "Renamed",
                os.path.basename(file_path),
                f"New name: {new_name}"
            )
            
            # Save to history
            self.operation_history.append({
                'type': 'rename',
                'old_path': file_path,
                'new_path': new_path,
                'timestamp': datetime.now()
            })
            
            return new_path, None
            
        except Exception as e:
            return None, f"Error renaming file: {str(e)}"
    
    def organize_by_type(self, source_folder, base_dest_folder=None):
        """
        Organize files by type into subfolders
        
        Args:
            source_folder: Folder to organize
            base_dest_folder: Base destination (defaults to source_folder)
        """
        
        if base_dest_folder is None:
            base_dest_folder = source_folder
        
        type_folders = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.md', '.pages'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.heic', '.svg'],
            'Spreadsheets': ['.xlsx', '.xls', '.csv', '.numbers'],
            'Presentations': ['.pptx', '.ppt', '.key'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Code': ['.py', '.js', '.html', '.css', '.json', '.xml'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv'],
            'Audio': ['.mp3', '.wav', '.m4a', '.flac']
        }
        
        results = {
            'moved': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Get files from database in this folder
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT path, filename, extension 
            FROM files 
            WHERE folder_location = ? AND status = 'active'
        """, (source_folder,))
        
        files = cursor.fetchall()
        
        for file_path, filename, ext in files:
            if not ext:
                results['skipped'] += 1
                continue
            
            # Find appropriate folder
            dest_subfolder = 'Other'
            for folder_name, extensions in type_folders.items():
                if ext.lower() in extensions:
                    dest_subfolder = folder_name
                    break
            
            # Don't move if already in correct subfolder
            if os.path.basename(os.path.dirname(file_path)) == dest_subfolder:
                results['skipped'] += 1
                continue
            
            # Move file
            dest_folder = os.path.join(base_dest_folder, dest_subfolder)
            new_path, error = self.move_file(file_path, dest_folder)
            
            if new_path:
                results['moved'] += 1
            else:
                results['errors'].append(f"{filename}: {error}")
                results['skipped'] += 1
        
        return results
    
    def organize_by_project(self, files_to_organize, user_profile):
        """
        Organize files by project based on AI tags
        
        Args:
            files_to_organize: List of file paths or file IDs
            user_profile: User profile with projects list
        """
        
        projects = user_profile.get('projects', [])
        if not projects:
            return {'moved': 0, 'error': 'No projects defined in profile'}
        
        # Create project folders in Documents
        docs_folder = os.path.expanduser("~/Documents")
        organized_folder = os.path.join(docs_folder, "Organized Files")
        
        results = {
            'moved': 0,
            'skipped': 0,
            'errors': []
        }
        
        cursor = self.db.conn.cursor()
        
        for file_ref in files_to_organize:
            # Get file info
            if isinstance(file_ref, int):
                cursor.execute("SELECT path, filename, project FROM files WHERE id = ?", (file_ref,))
            else:
                cursor.execute("SELECT path, filename, project FROM files WHERE path = ?", (file_ref,))
            
            result = cursor.fetchone()
            if not result:
                results['skipped'] += 1
                continue
            
            file_path, filename, project = result
            
            if not project or project not in projects:
                results['skipped'] += 1
                continue
            
            # Move to project folder
            project_folder = os.path.join(organized_folder, project)
            new_path, error = self.move_file(file_path, project_folder)
            
            if new_path:
                results['moved'] += 1
            else:
                results['errors'].append(f"{filename}: {error}")
                results['skipped'] += 1
        
        return results
    
    def delete_file(self, file_path, permanent=False):
        """
        Delete a file (move to trash or permanent delete)
        
        Args:
            file_path: Path to file
            permanent: If True, permanently delete. If False, move to trash.
        """
        
        if not os.path.exists(file_path):
            return False, "File not found"
        
        try:
            if permanent:
                os.remove(file_path)
                action = "Deleted (permanent)"
            else:
                # Move to trash (macOS)
                from subprocess import run
                run(['osascript', '-e', 
                     f'tell application "Finder" to delete POSIX file "{file_path}"'])
                action = "Moved to Trash"
            
            # Update database
            cursor = self.db.conn.cursor()
            cursor.execute("UPDATE files SET status = 'deleted' WHERE path = ?", (file_path,))
            self.db.conn.commit()
            
            # Log activity
            self.log_activity(
                action,
                os.path.basename(file_path),
                f"From: {os.path.dirname(file_path)}"
            )
            
            return True, None
            
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"


if __name__ == "__main__":
    # Test file operations
    from file_indexer import FileDatabase
    
    print("Testing File Operations...")
    
    db = FileDatabase()
    ops = FileOperations(db)
    
    # Test: Get some files from Downloads
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT path, filename 
        FROM files 
        WHERE folder_location LIKE '%Downloads%' 
        AND status = 'active'
        LIMIT 3
    """)
    
    files = cursor.fetchall()
    print(f"\nFound {len(files)} test files in Downloads")
    for path, name in files:
        print(f"  - {name}")
    
    print("\nFile operations module ready!")
    print("Use this module to move, rename, and organize files safely.")
    
    db.close()
