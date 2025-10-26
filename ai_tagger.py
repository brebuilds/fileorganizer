#!/usr/bin/env python3
"""
AI Tagging System
Uses Ollama to analyze file content and generate tags/summaries
"""

import ollama
from file_indexer import FileDatabase


class AITagger:
    """Uses Ollama to tag and summarize files"""
    
    def __init__(self, model="llama3.2:3b", user_profile=None):
        self.model = model
        self.user_profile = user_profile or {}
    
    def build_tagging_prompt(self, filename, content, file_type):
        """Build prompt for AI tagging"""
        
        # Get user's projects/clients for context
        projects = self.user_profile.get('projects', [])
        projects_str = ", ".join(projects) if projects else "unknown"
        
        prompt = f"""Analyze this file and provide:
1. A brief 1-sentence summary
2. 3-5 relevant tags
3. Which project/client it belongs to (if any)

USER'S PROJECTS/CLIENTS: {projects_str}

FILENAME: {filename}
FILE TYPE: {file_type}
CONTENT (first 2000 chars):
{content[:2000]}

Respond in JSON format:
{{
  "summary": "one sentence summary",
  "tags": ["tag1", "tag2", "tag3"],
  "project": "project name or empty string"
}}

IMPORTANT: 
- Tags should be lowercase, simple words
- Only assign to a project if you're confident it matches
- Be concise"""
        
        return prompt
    
    def tag_file(self, filename, content, file_type):
        """Use AI to tag a single file"""
        
        if not content or len(content.strip()) < 10:
            # Not enough content to analyze
            return {
                'summary': '',
                'tags': [],
                'project': ''
            }
        
        try:
            prompt = self.build_tagging_prompt(filename, content, file_type)
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response['message']['content']
            
            # Try to parse JSON response
            import json
            # Strip markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]
            
            result = json.loads(response_text.strip())
            
            return {
                'summary': result.get('summary', ''),
                'tags': result.get('tags', []),
                'project': result.get('project', '')
            }
            
        except Exception as e:
            print(f"Error tagging {filename}: {e}")
            return {
                'summary': '',
                'tags': [],
                'project': ''
            }
    
    def tag_untagged_files(self, db, limit=10):
        """Tag files that don't have AI tags yet"""
        
        cursor = db.conn.cursor()
        
        # Find files without AI tags
        cursor.execute("""
            SELECT id, path, filename, extension, content_text
            FROM files
            WHERE (ai_summary IS NULL OR ai_summary = '')
            AND content_text IS NOT NULL
            AND content_text != ''
            AND status = 'active'
            LIMIT ?
        """, (limit,))
        
        files = cursor.fetchall()
        
        tagged_count = 0
        
        for file_id, path, filename, extension, content in files:
            print(f"Tagging: {filename}")
            
            result = self.tag_file(filename, content, extension)
            
            if result['summary'] or result['tags']:
                # Update database
                cursor.execute("""
                    UPDATE files
                    SET ai_summary = ?, ai_tags = ?, project = ?
                    WHERE id = ?
                """, (
                    result['summary'],
                    ','.join(result['tags']),
                    result['project'],
                    file_id
                ))
                
                # Add individual tags
                cursor.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
                for tag in result['tags']:
                    cursor.execute("INSERT INTO tags (file_id, tag) VALUES (?, ?)", 
                                 (file_id, tag.lower()))
                
                db.conn.commit()
                tagged_count += 1
        
        return tagged_count


if __name__ == "__main__":
    # Test tagging
    print("Testing AI Tagging...")
    
    from setup_wizard import load_user_profile
    
    profile = load_user_profile()
    db = FileDatabase()
    tagger = AITagger(user_profile=profile)
    
    # Tag some files
    tagged = tagger.tag_untagged_files(db, limit=5)
    
    print(f"\nTagged {tagged} files")
    
    # Show example
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT filename, ai_summary, ai_tags, project
        FROM files
        WHERE ai_summary IS NOT NULL AND ai_summary != ''
        LIMIT 3
    """)
    
    print("\nExample tagged files:")
    for row in cursor.fetchall():
        print(f"\nFile: {row[0]}")
        print(f"Summary: {row[1]}")
        print(f"Tags: {row[2]}")
        print(f"Project: {row[3]}")
    
    db.close()