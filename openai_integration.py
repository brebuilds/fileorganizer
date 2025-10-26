#!/usr/bin/env python3
"""
OpenAI Integration (Optional)
Provides high-quality file summaries using OpenAI's GPT models

⚠️ PRIVACY NOTICE:
This module sends file content to OpenAI's servers.
Only use if you're comfortable with OpenAI's privacy policy.
Files are NOT stored by OpenAI after processing (per their API policy).
"""

import os
import json
from datetime import datetime


class OpenAITagger:
    """
    Optional OpenAI integration for high-quality summaries
    
    ⚠️  REQUIRES: OpenAI API key
    ⚠️  PRIVACY: Sends file content to OpenAI
    ⚠️  COST: Uses OpenAI API (paid service)
    """
    
    def __init__(self, api_key=None, model="gpt-4o-mini", user_profile=None):
        """
        Initialize OpenAI tagger
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (gpt-4o-mini is fastest/cheapest)
            user_profile: User profile for context
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.user_profile = user_profile or {}
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter.\n"
                "Get key from: https://platform.openai.com/api-keys"
            )
        
        # Try to import openai
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Install with:\n"
                "pip install openai"
            )
    
    def build_tagging_prompt(self, filename, content, file_type):
        """Build prompt for OpenAI"""
        projects = self.user_profile.get('projects', [])
        projects_str = ", ".join(projects) if projects else "unknown"
        
        prompt = f"""Analyze this file and provide a detailed analysis.

USER'S PROJECTS/CLIENTS: {projects_str}

FILENAME: {filename}
FILE TYPE: {file_type}
CONTENT (first 3000 chars):
{content[:3000]}

Provide:
1. A detailed 2-3 sentence summary of what this file is about
2. 5-10 relevant, searchable tags
3. Which project/client it belongs to (from the user's list, or empty if uncertain)
4. The main topic/category
5. Key entities mentioned (people, companies, dates, amounts)

Respond in JSON format:
{{
  "summary": "detailed summary here",
  "tags": ["tag1", "tag2", "tag3", ...],
  "project": "project name or empty string",
  "topic": "main topic/category",
  "entities": {{
    "people": ["person1", "person2"],
    "companies": ["company1"],
    "dates": ["date1"],
    "amounts": ["amount1"]
  }},
  "confidence": 0.0-1.0
}}

Make the summary detailed and useful for search. Include key information.
Tags should be lowercase and searchable.
Only assign to a project if you're confident (confidence > 0.7).
"""
        
        return prompt
    
    def tag_file(self, filename, content, file_type):
        """
        Use OpenAI to analyze and tag a file
        
        ⚠️  PRIVACY: This sends file content to OpenAI
        
        Returns:
            dict with summary, tags, project, topic, entities
        """
        
        if not content or len(content.strip()) < 10:
            return {
                'summary': '',
                'tags': [],
                'project': '',
                'topic': '',
                'entities': {},
                'confidence': 0.0,
                'source': 'skipped'
            }
        
        try:
            prompt = self.build_tagging_prompt(filename, content, file_type)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a file analysis expert. Provide detailed, accurate summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Add metadata
            result['source'] = 'openai'
            result['model'] = self.model
            result['tokens_used'] = response.usage.total_tokens
            
            return result
            
        except Exception as e:
            print(f"Error with OpenAI tagging {filename}: {e}")
            return {
                'summary': '',
                'tags': [],
                'project': '',
                'topic': '',
                'entities': {},
                'confidence': 0.0,
                'source': 'error',
                'error': str(e)
            }
    
    def batch_tag_files(self, file_db, limit=None, force_retag=False):
        """
        Tag multiple files with OpenAI
        
        Args:
            file_db: FileDatabase instance
            limit: Max files to tag (None for all)
            force_retag: Retag files even if they have summaries
        
        Returns:
            dict with statistics
        """
        cursor = file_db.conn.cursor()
        
        # Find files to tag
        if force_retag:
            query = """
                SELECT id, path, filename, extension, content_text
                FROM files
                WHERE content_text IS NOT NULL
                AND content_text != ''
                AND status = 'active'
            """
        else:
            query = """
                SELECT id, path, filename, extension, content_text
                FROM files
                WHERE (ai_summary IS NULL OR ai_summary = '')
                AND content_text IS NOT NULL
                AND content_text != ''
                AND status = 'active'
            """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        files = cursor.fetchall()
        
        if not files:
            return {
                'tagged': 0,
                'skipped': 0,
                'errors': 0,
                'message': 'No files to tag'
            }
        
        print(f"\n⚠️  PRIVACY NOTICE:")
        print(f"About to send content from {len(files)} files to OpenAI.")
        print(f"OpenAI will process but not store the content.")
        print(f"Cost estimate: ~${len(files) * 0.001:.3f} (approximate)")
        
        response = input(f"\nContinue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            return {
                'tagged': 0,
                'skipped': len(files),
                'errors': 0,
                'message': 'Cancelled by user'
            }
        
        stats = {
            'tagged': 0,
            'skipped': 0,
            'errors': 0,
            'total_tokens': 0
        }
        
        for i, (file_id, path, filename, extension, content) in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] Tagging: {filename}")
            
            result = self.tag_file(filename, content, extension)
            
            if result.get('source') == 'error':
                stats['errors'] += 1
                print(f"  ❌ Error: {result.get('error', 'Unknown')}")
                continue
            
            if result.get('source') == 'skipped':
                stats['skipped'] += 1
                print(f"  ⏭️  Skipped (no content)")
                continue
            
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
                cursor.execute(
                    "INSERT INTO tags (file_id, tag) VALUES (?, ?)",
                    (file_id, tag.lower())
                )
            
            file_db.conn.commit()
            
            stats['tagged'] += 1
            stats['total_tokens'] += result.get('tokens_used', 0)
            
            print(f"  ✅ Summary: {result['summary'][:60]}...")
            print(f"  🏷️  Tags: {', '.join(result['tags'][:5])}")
            if result['project']:
                print(f"  📁 Project: {result['project']}")
        
        return stats


def setup_openai_api():
    """Interactive setup for OpenAI API key"""
    print("🔑 OpenAI API Setup")
    print("="*60)
    print("\n⚠️  IMPORTANT - Privacy & Cost Information:")
    print("  • File content will be sent to OpenAI for analysis")
    print("  • OpenAI processes but does not store your files")
    print("  • This is a PAID service (costs ~$0.001 per file)")
    print("  • You need an OpenAI API key")
    print()
    print("Get your API key from:")
    print("  https://platform.openai.com/api-keys")
    print()
    
    api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("\n❌ Skipped. You can set it later with:")
        print("   export OPENAI_API_KEY='your-key-here'")
        return None
    
    # Test the API key
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple request
        print("\n🧪 Testing API key...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        print("✅ API key is valid!")
        
        # Save to environment
        config_file = os.path.expanduser("~/.fileorganizer/openai_key")
        with open(config_file, 'w') as f:
            f.write(api_key)
        os.chmod(config_file, 0o600)  # Secure permissions
        
        print(f"\n✅ API key saved to: {config_file}")
        print("   (Secure permissions: read-only for you)")
        
        return api_key
        
    except ImportError:
        print("\n❌ OpenAI library not installed.")
        print("   Install with: pip install openai")
        return None
    
    except Exception as e:
        print(f"\n❌ API key test failed: {e}")
        print("   Please check your API key and try again.")
        return None


if __name__ == "__main__":
    print("🤖 OpenAI Integration for File Organizer")
    print("="*60)
    
    # Check if API key exists
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        # Try to load from saved config
        config_file = os.path.expanduser("~/.fileorganizer/openai_key")
        if os.path.exists(config_file):
            with open(config_file) as f:
                api_key = f.read().strip()
    
    if not api_key:
        print("\n⚠️  No OpenAI API key found.")
        api_key = setup_openai_api()
        
        if not api_key:
            print("\nSetup cancelled or failed.")
            exit(1)
    
    # Test tagging
    print("\n" + "="*60)
    print("Testing OpenAI file tagging...")
    
    from file_indexer import FileDatabase
    from setup_wizard import load_user_profile
    
    db = FileDatabase()
    profile = load_user_profile()
    
    try:
        tagger = OpenAITagger(api_key=api_key, user_profile=profile)
        
        print("\n📊 Database has", db.get_stats()['total_files'], "files")
        print("\nWould you like to tag some files with OpenAI?")
        print("(This will send file content to OpenAI)")
        
        response = input("\nTag how many files? (Enter number or 0 to skip): ")
        
        try:
            limit = int(response)
            if limit > 0:
                print(f"\n🚀 Tagging {limit} files...")
                stats = tagger.batch_tag_files(db, limit=limit)
                
                print("\n" + "="*60)
                print("✅ Tagging complete!")
                print(f"\nResults:")
                print(f"  • Tagged: {stats['tagged']} files")
                print(f"  • Skipped: {stats['skipped']} files")
                print(f"  • Errors: {stats['errors']} files")
                print(f"  • Tokens used: {stats['total_tokens']}")
                print(f"  • Estimated cost: ${stats['total_tokens'] * 0.00000015:.4f}")
        except ValueError:
            print("Invalid number. Exiting.")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        db.close()

