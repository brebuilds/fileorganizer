#!/usr/bin/env python3
"""
Advanced Conversational AI Module
Handles intelligent conversations with learning and context management
"""

import ollama
import json
import re
from datetime import datetime, timedelta
from temporal_tracker import TemporalTracker


class ConversationalAI:
    """Enhanced AI assistant with learning and context awareness"""
    
    def __init__(self, model, user_profile, file_db):
        self.model = model
        self.user_profile = user_profile
        self.file_db = file_db
        self.conversation_context = []
        self.session_start = datetime.now()
        
        # Initialize temporal tracker
        self.temporal_tracker = TemporalTracker(file_db)
        
        # Load learned patterns
        self.learned_patterns = self._load_learned_patterns()
        
    def _load_learned_patterns(self):
        """Load all learned patterns from database"""
        patterns = self.file_db.get_learned_patterns()
        
        organized = {
            'search_terms': {},
            'file_preferences': {},
            'organization_style': {},
            'common_tasks': {}
        }
        
        for pattern in patterns:
            ptype = pattern['pattern_type']
            if ptype in organized:
                organized[ptype][pattern['pattern_key']] = {
                    'value': pattern['pattern_value'],
                    'confidence': pattern['confidence'],
                    'frequency': pattern['frequency']
                }
        
        return organized
    
    def build_context_aware_prompt(self, user_message):
        """Build an intelligent prompt with learned context"""
        
        settings = self.user_profile.get('settings', {})
        assistant_name = settings.get('assistant_name', 'Assistant')
        name = self.user_profile.get("name", "there")
        
        # Get recent activity insights
        recent_convos = self.file_db.get_recent_conversations(limit=5)
        frequent_files = self.file_db.get_frequently_accessed_files(limit=10)
        
        # Build contextual system prompt
        context_prompt = f"""You are {assistant_name}, {name}'s intelligent personal file assistant.

CONTEXT AWARENESS:
You learn from every interaction to become more helpful over time.

RECENT ACTIVITY INSIGHTS:"""
        
        # Add insights from recent conversations
        if recent_convos:
            recent_topics = set()
            for conv in recent_convos[:3]:
                if conv.get('intent'):
                    recent_topics.add(conv['intent'])
            
            if recent_topics:
                context_prompt += f"\n- Recent topics: {', '.join(recent_topics)}"
        
        # Add frequently accessed files context
        if frequent_files:
            top_projects = {}
            for f in frequent_files[:5]:
                if f.get('project'):
                    top_projects[f['project']] = top_projects.get(f['project'], 0) + 1
            
            if top_projects:
                sorted_projects = sorted(top_projects.items(), key=lambda x: x[1], reverse=True)
                context_prompt += f"\n- Active projects: {', '.join([p[0] for p in sorted_projects[:3]])}"
        
        # Add learned search patterns
        if self.learned_patterns['search_terms']:
            common_searches = sorted(
                self.learned_patterns['search_terms'].items(),
                key=lambda x: x[1]['frequency'],
                reverse=True
            )[:3]
            if common_searches:
                context_prompt += f"\n- Common searches: {', '.join([s[0] for s in common_searches])}"
        
        # Add learned organizational preferences
        if self.learned_patterns['organization_style']:
            context_prompt += "\n\nLEARNED PREFERENCES:"
            for key, data in list(self.learned_patterns['organization_style'].items())[:3]:
                if data['confidence'] > 0.5:
                    context_prompt += f"\n- {key}: {data['value']}"
        
        # Add stats about their files
        stats = self.file_db.get_stats()
        if stats['total_files'] > 0:
            context_prompt += f"\n\nFILE SYSTEM STATUS:"
            context_prompt += f"\n- Total indexed files: {stats['total_files']}"
            if stats.get('by_folder'):
                top_folders = sorted(stats['by_folder'].items(), key=lambda x: x[1], reverse=True)[:2]
                context_prompt += f"\n- Main locations: {', '.join([f[0].split('/')[-1] for f in top_folders])}"
        
        context_prompt += f"""

CONVERSATION GUIDELINES:
1. **TAKE ACTION IMMEDIATELY** - Don't ask permission, just do it!
2. Be direct and helpful - {name} has ADHD, fewer words = better
3. When they ask for something, DO IT RIGHT AWAY
4. Only ask questions if truly ambiguous (rare!)
5. Use context to fill in blanks yourself
6. After acting, briefly say what you did

INTENT DETECTION:
Detect the user's intent from their message:
- SEARCH: Looking for specific files
- ORGANIZE: Want to organize/move files
- INFO: Asking about file status or statistics
- HELP: Need guidance or unsure what to do
- CHAT: General conversation or thinking out loud

RESPONSE FORMAT:
Always respond naturally, but include structured tags when taking action:
- [INTENT: detected_intent] - Your understanding of what they want
- [SEARCH: query] - When you need to search for files (DO IT NOW!)
- [ORGANIZE: location] - When organizing files (DO IT NOW!)
- [LEARN: pattern_type|key|value] - When you detect a pattern to remember

EXAMPLES OF ACTION-FIRST RESPONSES:

User: "I need that thing from yesterday"
You: "[INTENT: SEARCH] [SEARCH: modified:yesterday] Got it! Here are your files from yesterday: [list results]"

User: "everything is a mess again"
You: "[INTENT: ORGANIZE] [ORGANIZE: Downloads] On it! Organizing your Downloads by project now..."

User: "find the Phoenix invoice"
You: "[INTENT: SEARCH] [SEARCH: Phoenix invoice] Found it! [show result]"

User: "organize my desktop"
You: "[INTENT: ORGANIZE] [ORGANIZE: Desktop] Sorting Desktop by file type right now!"

NOW RESPOND TO THE USER'S ACTUAL MESSAGE:
- BE BRIEF (1-2 sentences max)
- TAKE ACTION IMMEDIATELY
- Use tags to trigger actual functions
        
        return context_prompt
    
    def detect_intent(self, message):
        """Intelligently detect user intent"""
        message_lower = message.lower()
        
        # Temporal intents (check FIRST - most specific)
        temporal_keywords = ['yesterday', 'today', 'last week', 'this morning', 'this afternoon',
                            'downloaded', 'got', 'received', 'when did', 'ago', 'last month',
                            'this week', 'last night', 'recent']
        if any(kw in message_lower for kw in temporal_keywords):
            # Make sure they're asking about files
            file_keywords = ['file', 'download', 'document', 'pdf', 'what', 'show', 'did i']
            if any(kw in message_lower for kw in file_keywords):
                return 'TEMPORAL'
        
        # Search intents
        search_keywords = ['find', 'search', 'where', 'show', 'look', 'locate', 'get', 'need', 'looking for']
        if any(kw in message_lower for kw in search_keywords):
            return 'SEARCH'
        
        # Organize intents
        organize_keywords = ['organize', 'sort', 'clean', 'tidy', 'arrange', 'move', 'fix']
        if any(kw in message_lower for kw in organize_keywords):
            return 'ORGANIZE'
        
        # Help/guidance intents
        help_keywords = ['help', 'how', 'what can', 'stuck', 'confused', 'don\'t know']
        if any(kw in message_lower for kw in help_keywords):
            return 'HELP'
        
        # Info/status intents
        info_keywords = ['status', 'how many', 'what\'s', 'tell me', 'show me']
        if any(kw in message_lower for kw in info_keywords):
            return 'INFO'
        
        # Default to chat
        return 'CHAT'
    
    def extract_search_terms(self, message):
        """Extract meaningful search terms from message"""
        # Remove common stop words
        stop_words = {
            'find', 'search', 'for', 'the', 'a', 'an', 'where', 'is', 'are',
            'my', 'that', 'this', 'those', 'these', 'i', 'need', 'want',
            'show', 'me', 'get', 'looking', 'look'
        }
        
        words = re.findall(r'\b\w+\b', message.lower())
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        return ' '.join(meaningful_words)
    
    def learn_from_interaction(self, user_message, intent, action_taken, success):
        """Learn patterns from successful interactions"""
        
        # Learn search patterns
        if intent == 'SEARCH' and success:
            search_terms = self.extract_search_terms(user_message)
            if search_terms:
                self.file_db.learn_pattern(
                    'search_terms',
                    search_terms,
                    action_taken or '',
                    confidence=0.7 if success else 0.3
                )
        
        # Learn organizational preferences
        if intent == 'ORGANIZE' and action_taken:
            if 'by project' in action_taken.lower():
                self.file_db.learn_pattern(
                    'organization_style',
                    'prefers_by_project',
                    'true',
                    confidence=0.8
                )
            elif 'by type' in action_taken.lower():
                self.file_db.learn_pattern(
                    'organization_style',
                    'prefers_by_type',
                    'true',
                    confidence=0.8
                )
        
        # Learn common task patterns
        if intent in ['SEARCH', 'ORGANIZE', 'INFO']:
            self.file_db.learn_pattern(
                'common_tasks',
                intent.lower(),
                user_message[:100],  # Store snippet of request
                confidence=0.6
            )
    
    async def chat_async(self, user_message, conversation_history):
        """Async chat with enhanced intelligence"""
        # Detect intent
        intent = self.detect_intent(user_message)
        
        # Build context-aware prompt
        enhanced_prompt = self.build_context_aware_prompt(user_message)
        
        # Prepare messages with enhanced context
        messages = [
            {"role": "system", "content": enhanced_prompt}
        ] + conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        # Call Ollama
        response = ollama.chat(
            model=self.model,
            messages=messages
        )
        
        assistant_response = response['message']['content']
        
        # Parse structured tags from response
        extracted_intent = intent
        intent_match = re.search(r'\[INTENT:\s*([^\]]+)\]', assistant_response)
        if intent_match:
            extracted_intent = intent_match.group(1).strip()
            # Remove tag from visible response
            assistant_response = re.sub(r'\[INTENT:[^\]]+\]', '', assistant_response).strip()
        
        # Extract learning tags
        learn_matches = re.findall(r'\[LEARN:\s*([^\]]+)\]', assistant_response)
        for learn_tag in learn_matches:
            parts = learn_tag.split('|')
            if len(parts) == 3:
                self.file_db.learn_pattern(parts[0], parts[1], parts[2], confidence=0.7)
            # Remove tag from visible response
            assistant_response = re.sub(r'\[LEARN:[^\]]+\]', '', assistant_response).strip()
        
        # Log conversation
        action_taken = None
        if '[SEARCH:' in assistant_response:
            action_taken = 'search'
        elif '[ORGANIZE:' in assistant_response:
            action_taken = 'organize'
        
        self.file_db.log_conversation(
            user_message,
            assistant_response,
            intent=extracted_intent,
            action_taken=action_taken,
            success=True
        )
        
        return {
            'response': assistant_response,
            'intent': extracted_intent,
            'action': action_taken
        }
    
    def handle_temporal_query(self, message):
        """Handle temporal queries directly without calling Ollama"""
        results, start_time, end_time = self.temporal_tracker.query_files_by_time(message)
        
        if not results:
            time_desc = self._format_time_range(start_time, end_time)
            return f"I didn't find any files from {time_desc}. Would you like to search for something else?"
        
        time_desc = self._format_time_range(start_time, end_time)
        response = f"I found {len(results)} file(s) from {time_desc}:\n\n"
        
        for i, item in enumerate(results[:10], 1):
            response += f"{i}. {item['filename']}\n"
            response += f"   📁 {item['location']}\n"
            timestamp = item['timestamp'][:16].replace('T', ' ')
            response += f"   🕐 {timestamp}\n"
            if item.get('summary'):
                response += f"   {item['summary'][:80]}...\n"
            response += "\n"
        
        if len(results) > 10:
            response += f"...and {len(results) - 10} more files."
        
        return response
    
    def _format_time_range(self, start, end):
        """Format a time range in human-readable form"""
        now = datetime.now()
        
        # Same day?
        if start.date() == end.date():
            if start.date() == now.date():
                return "today"
            elif start.date() == (now - timedelta(days=1)).date():
                return "yesterday"
            else:
                return start.strftime("%B %d")
        
        # Same week?
        diff = (now - start).days
        if diff <= 7:
            return f"the last {diff} days"
        
        # Format as range
        return f"{start.strftime('%b %d')} to {end.strftime('%b %d')}"
    
    def chat(self, user_message, conversation_history):
        """Synchronous version of chat"""
        # Detect intent
        intent = self.detect_intent(user_message)
        
        # Handle temporal queries directly (fast path)
        if intent == 'TEMPORAL':
            assistant_response = self.handle_temporal_query(user_message)
            
            # Log the interaction
            self.file_db.log_conversation(
                user_message,
                assistant_response,
                intent='TEMPORAL',
                action_taken='temporal_search',
                success=True
            )
            
            return {
                'response': assistant_response,
                'intent': 'TEMPORAL',
                'action': 'temporal_search'
            }
        
        # Build context-aware prompt
        enhanced_prompt = self.build_context_aware_prompt(user_message)
        
        # Prepare messages with enhanced context
        messages = [
            {"role": "system", "content": enhanced_prompt}
        ] + conversation_history + [
            {"role": "user", "content": user_message}
        ]
        
        # Call Ollama
        response = ollama.chat(
            model=self.model,
            messages=messages
        )
        
        assistant_response = response['message']['content']
        
        # Parse structured tags from response
        extracted_intent = intent
        intent_match = re.search(r'\[INTENT:\s*([^\]]+)\]', assistant_response)
        if intent_match:
            extracted_intent = intent_match.group(1).strip()
            # Remove tag from visible response
            assistant_response = re.sub(r'\[INTENT:[^\]]+\]', '', assistant_response).strip()
        
        # Extract learning tags
        learn_matches = re.findall(r'\[LEARN:\s*([^\]]+)\]', assistant_response)
        for learn_tag in learn_matches:
            parts = learn_tag.split('|')
            if len(parts) == 3:
                self.file_db.learn_pattern(parts[0], parts[1], parts[2], confidence=0.7)
            # Remove tag from visible response
            assistant_response = re.sub(r'\[LEARN:[^\]]+\]', '', assistant_response).strip()
        
        # Log conversation
        action_taken = None
        if '[SEARCH:' in assistant_response:
            action_taken = 'search'
        elif '[ORGANIZE:' in assistant_response:
            action_taken = 'organize'
        
        self.file_db.log_conversation(
            user_message,
            assistant_response,
            intent=extracted_intent,
            action_taken=action_taken,
            success=True
        )
        
        # Learn from this interaction
        self.learn_from_interaction(user_message, extracted_intent, action_taken, True)
        
        return {
            'response': assistant_response,
            'intent': extracted_intent,
            'action': action_taken
        }
    
    def get_smart_suggestions(self):
        """Generate smart suggestions based on learned patterns and current state"""
        suggestions = []
        
        # Check for unorganized files
        stats = self.file_db.get_stats()
        if 'Downloads' in stats.get('by_folder', {}):
            download_count = stats['by_folder']['Downloads']
            if download_count > 20:
                suggestions.append({
                    'type': 'organize',
                    'message': f'Your Downloads has {download_count} files. Want me to organize them?',
                    'action': 'organize_downloads',
                    'priority': 'high'
                })
        
        # Suggest based on learned organization preference
        org_prefs = self.learned_patterns.get('organization_style', {})
        if org_prefs.get('prefers_by_project', {}).get('confidence', 0) > 0.7:
            # Check for unorganized files with project tags
            cursor = self.file_db.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM files 
                WHERE project IS NOT NULL AND project != ''
                AND folder_location LIKE '%Downloads%'
                AND status = 'active'
            """)
            count = cursor.fetchone()[0]
            
            if count > 5:
                suggestions.append({
                    'type': 'organize',
                    'message': f'Found {count} project files in Downloads. Organize them into project folders?',
                    'action': 'organize_by_project',
                    'priority': 'medium'
                })
        
        # Suggest files that might need attention
        frequent_files = self.file_db.get_frequently_accessed_files(limit=5)
        if frequent_files:
            recent_file = frequent_files[0]
            suggestions.append({
                'type': 'quick_access',
                'message': f'Quick access: {recent_file["filename"]}',
                'action': f'open_file:{recent_file["path"]}',
                'priority': 'low'
            })
        
        return sorted(suggestions, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)

