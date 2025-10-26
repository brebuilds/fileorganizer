#!/usr/bin/env python3
"""
External Tool Integration for File Organizer
Integrations with Alfred, Raycast, DevonThink, Notion, Calendar, etc.
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path


class ExternalToolIntegration:
    """Manages integrations with external productivity tools"""
    
    def __init__(self, db):
        self.db = db
        self.config_dir = os.path.expanduser("~/.fileorganizer")
        os.makedirs(self.config_dir, exist_ok=True)
    
    # ===== Alfred Integration =====
    
    def generate_alfred_workflow(self, output_dir=None):
        """
        Generate Alfred workflow for file search
        Creates a script filter that searches the database
        """
        if output_dir is None:
            output_dir = os.path.join(self.config_dir, "alfred_workflow")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create workflow info.plist
        plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>bundleid</key>
    <string>com.fileorganizer.alfred</string>
    <key>name</key>
    <string>File Organizer</string>
    <key>version</key>
    <string>1.0</string>
    <key>description</key>
    <string>Search and organize files with AI</string>
</dict>
</plist>'''
        
        with open(os.path.join(output_dir, "info.plist"), 'w') as f:
            f.write(plist_content)
        
        # Create Python search script
        script_content = f'''#!/usr/bin/env python3
import sys
import json
import sqlite3
import os

db_path = os.path.expanduser("~/.fileorganizer/files.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

query = sys.argv[1] if len(sys.argv) > 1 else ""

cursor.execute("""
    SELECT filename, path, ai_summary
    FROM files
    WHERE filename LIKE ? OR content_text LIKE ?
    LIMIT 20
""", (f"%{{query}}%", f"%{{query}}%"))

items = []
for filename, path, summary in cursor.fetchall():
    items.append({{
        "title": filename,
        "subtitle": summary or path,
        "arg": path,
        "type": "file"
    }})

print(json.dumps({{"items": items}}))
conn.close()
'''
        
        script_path = os.path.join(output_dir, "search.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        
        return output_dir
    
    # ===== Raycast Integration =====
    
    def generate_raycast_extension(self, output_dir=None):
        """Generate Raycast extension for file search"""
        if output_dir is None:
            output_dir = os.path.join(self.config_dir, "raycast_extension")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create package.json
        package_json = {
            "name": "file-organizer",
            "title": "File Organizer",
            "description": "Search and organize files with AI",
            "icon": "📁",
            "author": "File Organizer",
            "license": "MIT",
            "commands": [
                {
                    "name": "search-files",
                    "title": "Search Files",
                    "description": "Search indexed files",
                    "mode": "view"
                }
            ]
        }
        
        with open(os.path.join(output_dir, "package.json"), 'w') as f:
            json.dump(package_json, f, indent=2)
        
        return output_dir
    
    # ===== DevonThink Integration =====
    
    def export_to_devonthink(self, file_ids, database_name="File Organizer"):
        """
        Export files to DevonThink
        Uses AppleScript to import files
        """
        if not file_ids:
            return {'success': False, 'error': 'No files provided'}
        
        cursor = self.db.conn.cursor()
        placeholders = ','.join(['?' for _ in file_ids])
        cursor.execute(f"""
            SELECT path, filename, ai_summary, ai_tags
            FROM files
            WHERE id IN ({placeholders})
        """, file_ids)
        
        files = cursor.fetchall()
        imported = []
        failed = []
        
        for path, filename, summary, tags in files:
            if not os.path.exists(path):
                failed.append({'file': filename, 'error': 'File not found'})
                continue
            
            # Create AppleScript to import into DevonThink
            applescript = f'''
            tell application "DEVONthink 3"
                set theDatabase to open database "{database_name}"
                set theRecord to import "{path}" to theDatabase
                if "{summary}" is not "" then
                    set comment of theRecord to "{summary}"
                end if
                if "{tags}" is not "" then
                    set tags of theRecord to "{tags}"
                end if
            end tell
            '''
            
            try:
                subprocess.run(['osascript', '-e', applescript], check=True, capture_output=True)
                imported.append(filename)
            except subprocess.CalledProcessError as e:
                failed.append({'file': filename, 'error': str(e)})
        
        return {
            'success': True,
            'imported': len(imported),
            'failed': len(failed),
            'details': {'imported': imported, 'failed': failed}
        }
    
    # ===== Notion Integration =====
    
    def prepare_notion_export(self, file_ids):
        """
        Prepare files for Notion import
        Creates a CSV that can be imported into Notion
        """
        cursor = self.db.conn.cursor()
        placeholders = ','.join(['?' for _ in file_ids])
        cursor.execute(f"""
            SELECT filename, ai_summary, ai_tags, project, path, modified_date
            FROM files
            WHERE id IN ({placeholders})
        """, file_ids)
        
        files = cursor.fetchall()
        
        # Create CSV content
        csv_lines = ["Name,Summary,Tags,Project,Path,Date"]
        
        for filename, summary, tags, project, path, date in files:
            # Escape quotes and commas
            filename = filename.replace('"', '""')
            summary = (summary or '').replace('"', '""')
            tags = (tags or '').replace('"', '""')
            project = (project or '').replace('"', '""')
            
            csv_lines.append(f'"{filename}","{summary}","{tags}","{project}","{path}","{date}"')
        
        csv_content = '\n'.join(csv_lines)
        
        # Save to file
        output_path = os.path.join(self.config_dir, f"notion_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(output_path, 'w') as f:
            f.write(csv_content)
        
        return {
            'success': True,
            'file': output_path,
            'count': len(files)
        }
    
    # ===== Calendar Integration =====
    
    def create_calendar_event(self, file_id, event_title, event_date, notes=None):
        """
        Create a calendar event linked to a file
        Uses macOS Calendar app
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT filename, path, ai_summary
            FROM files
            WHERE id = ?
        """, (file_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'success': False, 'error': 'File not found'}
        
        filename, path, summary = row
        
        # Build notes
        event_notes = f"File: {filename}\nPath: {path}"
        if summary:
            event_notes += f"\n\nSummary: {summary}"
        if notes:
            event_notes += f"\n\n{notes}"
        
        # Create AppleScript for Calendar
        applescript = f'''
        tell application "Calendar"
            tell calendar "File Organizer"
                set theEvent to make new event with properties {{summary:"{event_title}", start date:date "{event_date}", end date:date "{event_date}"}}
                set description of theEvent to "{event_notes}"
            end tell
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', applescript], check=True, capture_output=True)
            
            # Create reminder in our database too
            from reminder_system import ReminderSystem
            reminder_system = ReminderSystem(self.db)
            reminder_system.create_reminder(
                file_id=file_id,
                reminder_type='calendar_event',
                reminder_date=event_date,
                message=event_title
            )
            
            return {'success': True, 'event': event_title}
        except subprocess.CalledProcessError as e:
            return {'success': False, 'error': str(e)}
    
    # ===== Obsidian/Markdown Notes Integration =====
    
    def create_obsidian_note(self, file_id, vault_path, note_name=None):
        """
        Create an Obsidian note linked to a file
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT filename, path, ai_summary, ai_tags, content_text
            FROM files
            WHERE id = ?
        """, (file_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'success': False, 'error': 'File not found'}
        
        filename, path, summary, tags, content = row
        
        # Generate note name
        if not note_name:
            note_name = Path(filename).stem
        
        # Create markdown content
        markdown = f"""# {filename}

## File Information
- **Path**: `{path}`
- **Tags**: {tags or 'None'}

## Summary
{summary or 'No summary available'}

## Content Preview
```
{(content or '')[:500]}...
```

## Links
- [[File path: {path}]]

---
Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        # Save to vault
        vault_path = os.path.expanduser(vault_path)
        note_path = os.path.join(vault_path, f"{note_name}.md")
        
        try:
            with open(note_path, 'w') as f:
                f.write(markdown)
            
            return {'success': True, 'note_path': note_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ===== URL Schemes =====
    
    def get_url_scheme(self, action, **params):
        """
        Generate URL scheme for deep linking
        e.g., fileorganizer://search?q=invoice
        """
        base = "fileorganizer://"
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base}{action}?{param_str}"
    
    # ===== Export Integration Config =====
    
    def export_integration_config(self):
        """Export configuration for all integrations"""
        config = {
            'alfred_workflow': os.path.join(self.config_dir, "alfred_workflow"),
            'raycast_extension': os.path.join(self.config_dir, "raycast_extension"),
            'api_endpoint': 'http://localhost:8765',
            'database_path': os.path.join(self.config_dir, "files.db"),
            'url_scheme': 'fileorganizer://',
            'supported_integrations': [
                'Alfred',
                'Raycast',
                'DevonThink',
                'Notion',
                'Calendar',
                'Obsidian'
            ]
        }
        
        config_path = os.path.join(self.config_dir, "integrations.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_path


if __name__ == "__main__":
    # Test external tools integration
    from file_indexer import FileDatabase
    
    print("Testing External Tool Integration...")
    
    db = FileDatabase()
    tools = ExternalToolIntegration(db)
    
    # Generate Alfred workflow
    print("\n🔮 Generating Alfred workflow...")
    alfred_dir = tools.generate_alfred_workflow()
    print(f"Created at: {alfred_dir}")
    
    # Generate Raycast extension
    print("\n⚡ Generating Raycast extension...")
    raycast_dir = tools.generate_raycast_extension()
    print(f"Created at: {raycast_dir}")
    
    # Export integration config
    print("\n⚙️  Exporting integration config...")
    config_path = tools.export_integration_config()
    print(f"Config saved to: {config_path}")
    
    # Show URL scheme examples
    print("\n🔗 URL Scheme Examples:")
    print(f"  Search: {tools.get_url_scheme('search', q='invoice')}")
    print(f"  Open file: {tools.get_url_scheme('open', id='123')}")
    print(f"  Organize: {tools.get_url_scheme('organize', folder='Downloads')}")
    
    db.close()
    print("\n✅ External tools integration test complete!")

