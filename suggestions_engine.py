#!/usr/bin/env python3
"""
Smart Suggestions Engine
AI-powered proactive suggestions with popup notifications
"""

import json
from datetime import datetime, timedelta
from collections import Counter


class SuggestionsEngine:
    """Generate smart suggestions based on file patterns and AI analysis"""
    
    def __init__(self, file_db):
        self.db = file_db
    
    def generate_all_suggestions(self):
        """Generate all types of suggestions"""
        suggestions = []
        
        suggestions.extend(self._suggest_duplicates())
        suggestions.extend(self._suggest_related_files())
        suggestions.extend(self._suggest_untagged())
        suggestions.extend(self._suggest_organization())
        suggestions.extend(self._suggest_smart_folders())
        suggestions.extend(self._suggest_cleanup())
        
        # Store in database
        self._store_suggestions(suggestions)
        
        return suggestions
    
    def _suggest_duplicates(self):
        """Suggest cleaning up duplicate files"""
        from duplicate_detector import DuplicateDetector
        
        detector = DuplicateDetector(self.db)
        stats = detector.get_duplicate_stats()
        
        if stats['duplicate_groups'] > 0:
            return [{
                'type': 'cleanup_duplicates',
                'priority': 8,
                'title': f"🔍 Found {stats['duplicate_groups']} groups of duplicate files",
                'message': f"You could save {stats['wasted_space_mb']} MB by removing duplicates. Want me to show them?",
                'action_data': json.dumps({'stats': stats}),
                'action_command': 'DUPES'
            }]
        
        return []
    
    def _suggest_related_files(self):
        """Suggest grouping related files into projects"""
        cursor = self.db.conn.cursor()
        
        # Find files with common tags
        cursor.execute("""
            SELECT ai_tags, COUNT(*) as count
            FROM files
            WHERE ai_tags IS NOT NULL AND ai_tags != ''
            AND status = 'active'
            AND hide_from_app = 0
            AND (project IS NULL OR project = '')
            GROUP BY ai_tags
            HAVING count >= 3
            ORDER BY count DESC
            LIMIT 3
        """)
        
        suggestions = []
        for tags, count in cursor.fetchall():
            # Get first significant tag
            tag_list = [t.strip() for t in tags.split(',')]
            main_tag = tag_list[0] if tag_list else tags
            
            suggestions.append({
                'type': 'group_related',
                'priority': 7,
                'title': f"📁 {count} files seem related to '{main_tag}'",
                'message': f"Should I create a project '{main_tag}' and group these files?",
                'action_data': json.dumps({'tag': main_tag, 'count': count}),
                'action_command': f'GROUP@{main_tag}'
            })
        
        return suggestions
    
    def _suggest_untagged(self):
        """Suggest tagging untagged files"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE (ai_tags IS NULL OR ai_tags = '')
            AND status = 'active'
            AND hide_from_app = 0
        """)
        
        count = cursor.fetchone()[0]
        
        if count >= 5:
            return [{
                'type': 'tag_files',
                'priority': 6,
                'title': f"🏷️  {count} files haven't been tagged yet",
                'message': "Want me to AI-tag them? It helps with search and organization.",
                'action_data': json.dumps({'count': count}),
                'action_command': 'TAG-ALL'
            }]
        
        return []
    
    def _suggest_organization(self):
        """Suggest organizing cluttered folders"""
        cursor = self.db.conn.cursor()
        
        # Check Downloads
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE folder_location LIKE '%Downloads%'
            AND status = 'active'
        """)
        
        downloads_count = cursor.fetchone()[0]
        
        suggestions = []
        
        if downloads_count >= 20:
            suggestions.append({
                'type': 'organize_folder',
                'priority': 7,
                'title': f"🧹 Downloads has {downloads_count} files",
                'message': "That's getting crowded! Want me to organize it by type?",
                'action_data': json.dumps({'folder': 'Downloads', 'count': downloads_count}),
                'action_command': 'SORT@Downloads'
            })
        
        # Check Desktop
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE folder_location LIKE '%Desktop%'
            AND status = 'active'
        """)
        
        desktop_count = cursor.fetchone()[0]
        
        if desktop_count >= 15:
            suggestions.append({
                'type': 'organize_folder',
                'priority': 6,
                'title': f"🖥️  Desktop has {desktop_count} files",
                'message': "Want to clean up your desktop? I can organize it for you!",
                'action_data': json.dumps({'folder': 'Desktop', 'count': desktop_count}),
                'action_command': 'SORT@Desktop'
            })
        
        return suggestions
    
    def _suggest_smart_folders(self):
        """Suggest creating smart folders for common searches"""
        cursor = self.db.conn.cursor()
        
        # Check search history for common queries
        cursor.execute("""
            SELECT query, COUNT(*) as count
            FROM search_history
            GROUP BY query
            HAVING count >= 3
            ORDER BY count DESC
            LIMIT 3
        """)
        
        suggestions = []
        for query, count in cursor.fetchall():
            suggestions.append({
                'type': 'create_smart_folder',
                'priority': 5,
                'title': f"💡 You search for '{query}' often",
                'message': f"Want to create a Smart Folder for quick access?",
                'action_data': json.dumps({'query': query, 'count': count}),
                'action_command': f'SMART-CREATE@{query}'
            })
        
        return suggestions
    
    def _suggest_cleanup(self):
        """Suggest cleanup actions"""
        cursor = self.db.conn.cursor()
        
        # Check for old screenshots
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE is_screenshot = 1
            AND created_date < datetime('now', '-30 days')
            AND status = 'active'
        """)
        
        old_screenshots = cursor.fetchone()[0]
        
        if old_screenshots >= 10:
            return [{
                'type': 'cleanup_screenshots',
                'priority': 4,
                'title': f"📸 {old_screenshots} old screenshots taking up space",
                'message': "These are over 30 days old. Archive them?",
                'action_data': json.dumps({'count': old_screenshots}),
                'action_command': 'CLEAN-SCREENSHOTS'
            }]
        
        return []
    
    def _store_suggestions(self, suggestions):
        """Store suggestions in database"""
        cursor = self.db.conn.cursor()
        
        # Clear old suggestions
        cursor.execute("DELETE FROM suggestions WHERE created_date < datetime('now', '-7 days')")
        
        # Add new ones
        for sug in suggestions:
            # Check if similar suggestion already exists
            cursor.execute("""
                SELECT id FROM suggestions
                WHERE suggestion_type = ?
                AND dismissed = 0
                AND accepted = 0
            """, (sug['type'],))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO suggestions (suggestion_type, message, action_data, priority, created_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sug['type'],
                    f"{sug['title']}\n{sug['message']}",
                    sug['action_data'],
                    sug['priority'],
                    datetime.now().isoformat()
                ))
        
        self.db.conn.commit()
    
    def get_active_suggestions(self):
        """Get all active (not dismissed/accepted) suggestions"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, suggestion_type, message, action_data, priority, created_date
            FROM suggestions
            WHERE dismissed = 0
            AND accepted = 0
            ORDER BY priority DESC, created_date DESC
        """)
        
        suggestions = []
        for row in cursor.fetchall():
            suggestions.append({
                'id': row[0],
                'type': row[1],
                'message': row[2],
                'action_data': json.loads(row[3]) if row[3] else {},
                'priority': row[4],
                'created_date': row[5]
            })
        
        return suggestions
    
    def dismiss_suggestion(self, suggestion_id):
        """Dismiss a suggestion"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE suggestions SET dismissed = 1 WHERE id = ?
        """, (suggestion_id,))
        self.db.conn.commit()
    
    def accept_suggestion(self, suggestion_id):
        """Mark suggestion as accepted"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE suggestions SET accepted = 1 WHERE id = ?
        """, (suggestion_id,))
        self.db.conn.commit()
    
    def get_suggestion_stats(self):
        """Get statistics about suggestions"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM suggestions WHERE dismissed = 0 AND accepted = 0")
        active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM suggestions WHERE accepted = 1")
        accepted = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM suggestions WHERE dismissed = 1")
        dismissed = cursor.fetchone()[0]
        
        return {
            'active': active,
            'accepted': accepted,
            'dismissed': dismissed
        }


if __name__ == "__main__":
    print("💡 Smart Suggestions Engine")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    engine = SuggestionsEngine(db)
    
    print("\n🧠 Generating suggestions...")
    suggestions = engine.generate_all_suggestions()
    
    if suggestions:
        print(f"\n🎯 Generated {len(suggestions)} suggestion(s):\n")
        
        for i, sug in enumerate(suggestions, 1):
            print(f"{i}. {sug['title']}")
            print(f"   {sug['message']}")
            print(f"   Priority: {sug['priority']}/10")
            if 'action_command' in sug:
                print(f"   Action: ./o {sug['action_command']}")
            print()
    else:
        print("\n✨ Everything looks great! No suggestions needed.")
    
    # Stats
    stats = engine.get_suggestion_stats()
    print(f"📊 Suggestion Stats:")
    print(f"   Active: {stats['active']}")
    print(f"   Accepted: {stats['accepted']}")
    print(f"   Dismissed: {stats['dismissed']}")
    
    db.close()

