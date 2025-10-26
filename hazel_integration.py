#!/usr/bin/env python3
"""
Hazel Integration for File Organizer
Exports file organization rules for Hazel and provides AppleScript bridges
"""

import os
import json
from pathlib import Path


class HazelRuleExporter:
    """Creates Hazel-compatible rules from File Organizer settings"""
    
    def __init__(self, user_profile=None):
        self.user_profile = user_profile or {}
        self.rules = []
    
    def create_organization_rule(self, folder, action='organize_by_type'):
        """Create a Hazel rule for automatic organization"""
        
        rule = {
            'name': f'Auto-organize {Path(folder).name}',
            'folder': folder,
            'conditions': [
                {
                    'type': 'kind',
                    'operator': 'is',
                    'value': 'any'
                }
            ],
            'actions': []
        }
        
        if action == 'organize_by_type':
            # Create rules for each file type
            file_type_mappings = {
                'PDF': ['pdf'],
                'Images': ['jpg', 'jpeg', 'png', 'gif', 'heic', 'svg'],
                'Documents': ['doc', 'docx', 'txt', 'md', 'pages'],
                'Spreadsheets': ['xlsx', 'xls', 'csv', 'numbers'],
                'Archives': ['zip', 'rar', '7z', 'tar', 'gz']
            }
            
            rule['actions'] = [{
                'type': 'script',
                'script': self.generate_applescript('organize_by_type', folder)
            }]
        
        elif action == 'ai_tag':
            rule['actions'] = [{
                'type': 'script',
                'script': self.generate_applescript('ai_tag', folder)
            }]
        
        self.rules.append(rule)
        return rule
    
    def generate_applescript(self, action, folder=''):
        """Generate AppleScript for Hazel integration"""
        
        app_path = '/Users/bre/file organizer'
        python_path = f'{app_path}/one/bin/python'
        
        if action == 'organize_by_type':
            script = f'''
-- Hazel Script: Auto-organize by type
on hazelProcessFile(theFile)
    set filePath to POSIX path of theFile
    set folderPath to "{folder}"
    
    set pythonScript to "{app_path}/hazel_bridge.py"
    set pythonCmd to "{python_path} " & quoted form of pythonScript & " organize " & quoted form of folderPath
    
    try
        do shell script pythonCmd
        return true
    on error errMsg
        log "Error organizing file: " & errMsg
        return false
    end try
end hazelProcessFile
'''
        
        elif action == 'ai_tag':
            script = f'''
-- Hazel Script: AI Tag File
on hazelProcessFile(theFile)
    set filePath to POSIX path of theFile
    
    set pythonScript to "{app_path}/hazel_bridge.py"
    set pythonCmd to "{python_path} " & quoted form of pythonScript & " tag " & quoted form of filePath
    
    try
        do shell script pythonCmd
        return true
    on error errMsg
        log "Error tagging file: " & errMsg
        return false
    end try
end hazelProcessFile
'''
        
        elif action == 'smart_move':
            script = f'''
-- Hazel Script: Smart Move (AI Decision)
on hazelProcessFile(theFile)
    set filePath to POSIX path of theFile
    
    set pythonScript to "{app_path}/hazel_bridge.py"
    set pythonCmd to "{python_path} " & quoted form of pythonScript & " smart_move " & quoted form of filePath
    
    try
        set result to do shell script pythonCmd
        -- Result will be the new path
        if result is not "" then
            return true
        else
            return false
        end if
    on error errMsg
        log "Error moving file: " & errMsg
        return false
    end try
end hazelProcessFile
'''
        
        else:
            script = '-- Unknown action'
        
        return script.strip()
    
    def export_rules(self, output_file=None):
        """Export rules to file"""
        if output_file is None:
            config_dir = os.path.expanduser("~/.fileorganizer")
            os.makedirs(config_dir, exist_ok=True)
            output_file = os.path.join(config_dir, "hazel_rules.json")
        
        with open(output_file, 'w') as f:
            json.dump({
                'version': '1.0',
                'rules': self.rules,
                'instructions': 'Import these rules into Hazel. '
                               'Copy the AppleScript from each rule into Hazel\'s script editor.'
            }, f, indent=2)
        
        return output_file
    
    def export_applescripts(self, output_dir=None):
        """Export AppleScript files that can be used in Hazel"""
        if output_dir is None:
            output_dir = os.path.expanduser("~/.fileorganizer/hazel_scripts")
        
        os.makedirs(output_dir, exist_ok=True)
        
        scripts = {
            'organize_by_type.scpt': self.generate_applescript('organize_by_type'),
            'ai_tag.scpt': self.generate_applescript('ai_tag'),
            'smart_move.scpt': self.generate_applescript('smart_move')
        }
        
        exported = []
        for filename, script in scripts.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(script)
            exported.append(filepath)
        
        return exported


def create_hazel_bridge():
    """Create the Python bridge script that Hazel will call"""
    
    bridge_script = '''#!/usr/bin/env python3
"""
Hazel Bridge Script
Called by Hazel AppleScript rules to perform file operations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_indexer import FileDatabase, FileIndexer
from file_operations import FileOperations
from ai_tagger import AITagger
from setup_wizard import load_user_profile


def organize_folder(folder_path):
    """Organize folder by type"""
    db = FileDatabase()
    ops = FileOperations(db)
    
    results = ops.organize_by_type(folder_path)
    
    db.close()
    print(f"Organized: {results['moved']} files")
    return results['moved']


def tag_file(file_path):
    """Tag file with AI"""
    db = FileDatabase()
    profile = load_user_profile()
    
    # First index the file if not already
    indexer = FileIndexer(db)
    indexer.index_file(file_path)
    
    # Then tag it
    tagger = AITagger(user_profile=profile)
    
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT filename, extension, content_text 
        FROM files WHERE path = ?
    """, (file_path,))
    
    result = cursor.fetchone()
    if result:
        filename, extension, content = result
        tags = tagger.tag_file(filename, content or '', extension or '')
        
        cursor.execute("""
            UPDATE files 
            SET ai_summary = ?, ai_tags = ?, project = ?
            WHERE path = ?
        """, (tags['summary'], ','.join(tags['tags']), tags['project'], file_path))
        db.conn.commit()
        
        print(f"Tagged: {tags['tags']}")
    
    db.close()
    return True


def smart_move(file_path):
    """Use AI to decide where to move file"""
    db = FileDatabase()
    profile = load_user_profile()
    ops = FileOperations(db)
    
    # Tag file first
    tag_file(file_path)
    
    # Get project
    cursor = db.conn.cursor()
    cursor.execute("SELECT project FROM files WHERE path = ?", (file_path,))
    result = cursor.fetchone()
    
    if result and result[0]:
        project = result[0]
        # Move to project folder
        docs = os.path.expanduser("~/Documents")
        organized = os.path.join(docs, "Organized Files", project)
        
        new_path, error = ops.move_file(file_path, organized)
        if new_path:
            print(new_path)
        else:
            print("")
    
    db.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hazel_bridge.py <action> [args]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    try:
        if action == "organize" and len(sys.argv) >= 3:
            folder = sys.argv[2]
            organize_folder(folder)
        
        elif action == "tag" and len(sys.argv) >= 3:
            file_path = sys.argv[2]
            tag_file(file_path)
        
        elif action == "smart_move" and len(sys.argv) >= 3:
            file_path = sys.argv[2]
            smart_move(file_path)
        
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
'''
    
    bridge_path = "/Users/bre/file organizer/hazel_bridge.py"
    with open(bridge_path, 'w') as f:
        f.write(bridge_script)
    
    # Make executable
    os.chmod(bridge_path, 0o755)
    
    return bridge_path


if __name__ == "__main__":
    print("🎯 Hazel Integration Setup")
    print("="*60)
    
    # Create bridge script
    print("\n1️⃣  Creating Hazel bridge script...")
    bridge = create_hazel_bridge()
    print(f"   ✅ Created: {bridge}")
    
    # Create example rules
    print("\n2️⃣  Creating example Hazel rules...")
    exporter = HazelRuleExporter()
    
    # Add some example rules
    exporter.create_organization_rule(
        os.path.expanduser("~/Downloads"),
        action='organize_by_type'
    )
    exporter.create_organization_rule(
        os.path.expanduser("~/Desktop"),
        action='ai_tag'
    )
    
    # Export
    rules_file = exporter.export_rules()
    print(f"   ✅ Rules exported: {rules_file}")
    
    scripts = exporter.export_applescripts()
    print(f"   ✅ AppleScripts exported:")
    for script in scripts:
        print(f"      → {script}")
    
    print("\n3️⃣  Setup Instructions:")
    print("""
    To use with Hazel:
    
    1. Open Hazel preferences
    2. Add a folder to monitor (e.g., ~/Downloads)
    3. Create a new rule
    4. Add conditions (e.g., "Kind is Document")
    5. Add action: "Run AppleScript"
    6. Copy script from ~/.fileorganizer/hazel_scripts/
    7. Enable the rule
    
    Available scripts:
    • organize_by_type.scpt - Auto-organize by file type
    • ai_tag.scpt - Tag files with AI
    • smart_move.scpt - AI decides where to move files
    """)
    
    print("="*60)
    print("✅ Hazel integration ready!")

