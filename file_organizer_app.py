#!/usr/bin/env python3
"""
ADHD-Friendly File Organizer
A menu bar app with AI-powered chat for finding and organizing files
"""

import sys
import os
import ollama
from setup_wizard import SetupWizard, needs_setup, save_user_profile, load_user_profile
from file_indexer import FileDatabase, FileIndexer
from ai_tagger import AITagger
from file_operations import FileOperations
from conversational_ai import ConversationalAI
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QTabWidget, QSystemTrayIcon, QMenu, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
    QColorDialog, QFontDialog, QScrollArea, QComboBox, 
    QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QTextCursor, QFont
import datetime
import json

class OllamaThread(QThread):
    """Background thread for Ollama API calls with enhanced AI"""
    response_ready = pyqtSignal(dict)  # Changed to dict to pass more info
    error_occurred = pyqtSignal(str)
    
    def __init__(self, conversational_ai, message, conversation_history):
        super().__init__()
        self.conversational_ai = conversational_ai
        self.message = message
        self.conversation_history = conversation_history
    
    def run(self):
        try:
            # Use enhanced conversational AI
            result = self.conversational_ai.chat(
                self.message,
                self.conversation_history
            )
            
            self.response_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")


class ActivityLogWidget(QWidget):
    """Tab for showing file organization activity"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Activity table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "Action", "File", "Details"])
        
        # Make columns resize appropriately
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
    
    def add_activity(self, action, filename, details):
        """Add an activity log entry"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.table.setItem(row, 1, QTableWidgetItem(action))
        self.table.setItem(row, 2, QTableWidgetItem(filename))
        self.table.setItem(row, 3, QTableWidgetItem(details))
        
        # Scroll to bottom
        self.table.scrollToBottom()


class ChatWidget(QWidget):
    """Main chat interface with enhanced conversational AI"""
    
    def __init__(self, activity_log, user_profile=None, file_db=None, file_ops=None):
        super().__init__()
        self.model = "llama3.2:3b"
        self.activity_log = activity_log
        self.ollama_thread = None
        self.user_profile = user_profile or {}
        self.file_db = file_db
        self.file_ops = file_ops
        
        # Initialize enhanced conversational AI
        self.conversational_ai = ConversationalAI(
            model=self.model,
            user_profile=self.user_profile,
            file_db=self.file_db
        )
        
        # Store for dragged files
        self.dragged_files = []
        
        # Simplified conversation history (system prompt now handled by ConversationalAI)
        self.conversation_history = []
        
        self.init_ui()
    
    def build_system_prompt_legacy(self):
        """Build personalized system prompt from user profile"""
        
        # Get settings
        settings = self.user_profile.get('settings', {})
        assistant_name = settings.get('assistant_name', 'Assistant')
        tone = settings.get('tone', 'Casual & Friendly')
        
        if not self.user_profile:
            # Default prompt if no profile
            return f"""You are {assistant_name}, a helpful file organization assistant built into a macOS menu bar app. 

Your user struggles with file organization - files pile up everywhere with chaotic naming and no structure.

Your job is to:
- Help them find files through natural conversation
- Suggest ways to organize their files
- Be encouraging and understanding about the chaos
- Keep responses concise and practical

Currently you're in chat-only mode. Soon you'll be able to actually search and organize their files. For now, just chat naturally and help them think through their organization strategy.

Be warm, casual, and friendly - no judgment, just helpful."""
        
        # Personalized prompt
        name = self.user_profile.get("name", "there")
        job = self.user_profile.get("job", "")
        industry = self.user_profile.get("industry", "")
        projects = self.user_profile.get("projects", [])
        folders = self.user_profile.get("monitored_folders", [])
        file_types = self.user_profile.get("file_types", [])
        org_style = self.user_profile.get("organization_style", "project")
        pain_points = self.user_profile.get("pain_points", "")
        
        prompt = f"""You are {assistant_name}, {name}'s personal file organization assistant, built into a macOS menu bar app.

ABOUT {name.upper()}:
- Job/Role: {job}"""
        
        if industry and industry != "Not specified":
            prompt += f"\n- Industry: {industry}"
        
        if projects:
            prompt += f"\n- Main projects/clients: {', '.join(projects)}"
        
        if folders:
            prompt += f"\n- Monitored folders: {', '.join(folders)}"
        
        if file_types:
            prompt += f"\n- Works with: {', '.join(file_types)}"
        
        prompt += f"\n- Thinks about files: By {org_style}"
        
        if pain_points:
            prompt += f"\n\nTHEIR BIGGEST CHALLENGE:\n{pain_points}"
        
        prompt += f"""

YOUR JOB:
- Help {name} find files through natural conversation
- Suggest organization strategies that fit THEIR way of thinking
- Be encouraging and understanding - they struggle with organization
- Keep responses concise and practical
- Remember their projects/clients when they mention them

CURRENT STATUS:
You can search through their indexed files AND help organize them through natural conversation!

HOW TO INTERACT:
- Chat naturally - don't just execute commands robotically
- Ask clarifying questions when needed
- Suggest what you could do based on what they're saying
- Confirm before taking ANY file action (moving, renaming, deleting)
- Explain what you're about to do and why

EXAMPLES OF GOOD INTERACTIONS:

User: "I need to find something"
You: "Sure! What are you looking for? A specific file name, project, or type of document?"

User: "my downloads are a mess"  
You: "I can help! I have [number] files indexed in your Downloads. Want me to organize them by type (PDFs together, images together, etc.) or would you prefer a different approach?"

User: "organize my downloads"
You: "I can sort your Downloads into folders by file type - Documents, Images, Spreadsheets, Archives, etc. Should I go ahead with that? (It won't delete anything, just organize into subfolders)"

User: "yes"
You: [Actually execute the organization and report results]

SEARCHING:
When they want to find files, search the database naturally:
- "find my outline" → search for "outline"  
- "where's that Phoenix doc?" → search for "Phoenix"

Then tell them what you found conversationally, not like a robot listing results.

EXECUTING ACTIONS:
When you've confirmed with the user and they say yes/ok/sure/go ahead, you can execute actions:

To search: Add [SEARCH: query terms] in your response
Example: "Let me find that for you! [SEARCH: outline]"

To organize: Add [ORGANIZE: downloads] or [ORGANIZE: desktop] in your response  
Example: "I'll organize your Downloads now! [ORGANIZE: downloads]"

The system will execute the action and add results to your response automatically.

IMPORTANT: Only use action tags AFTER getting user confirmation!

DRAG & DROP FILES:
Users can drag files directly into the chat! When they do, you'll receive:
- File path, name, and metadata
- AI-generated summary and tags (if available)
- Project associations

Use this context to answer questions like:
- "What is this file about?"
- "Find files related to this"
- "Which project does this belong to?"
- "Move this to [folder]"
- "Summarize this document"

Always acknowledge the file they dropped and respond based on what they're asking about it.

TONE:
Be warm, casual, and friendly - like a helpful friend who gets it. No judgment, just helpful. Use their name occasionally to make it personal.

CONVERSATION STYLE ({tone}):"""
        
        if tone == "Casual & Friendly":
            prompt += """
- Keep it relaxed and conversational
- Use casual language, contractions, occasional humor
- Be encouraging and supportive
- It's okay to be playful"""
        elif tone == "Professional":
            prompt += """
- Maintain professionalism while being helpful
- Use clear, precise language
- Focus on efficiency and results
- Be respectful and courteous"""
        elif tone == "Concise":
            prompt += """
- Keep responses brief and to the point
- No unnecessary pleasantries
- Focus on actionable information
- Direct and efficient communication"""
        
        return prompt
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        font = QFont("Menlo", 11)
        self.chat_display.setFont(font)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything about your files...")
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)
        
        self.setLayout(layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Welcome message
        self.append_message("Assistant", "Hey! I'm your file organizer assistant. I know things are probably chaotic right now - files everywhere, can't find anything. That's exactly what I'm here to help with. Right now we can chat and plan your organization strategy. Soon I'll be able to actually search and organize your files for you. What's the biggest pain point with your files right now?")
    
    def append_message(self, sender, message):
        """Add a message to the chat display"""
        # Get time format preference
        settings = self.user_profile.get('settings', {})
        use_12hr = settings.get('time_12hr', True)
        
        if use_12hr:
            timestamp = datetime.datetime.now().strftime("%I:%M %p")
        else:
            timestamp = datetime.datetime.now().strftime("%H:%M")
        
        # Get assistant name
        assistant_name = settings.get('assistant_name', 'Assistant')
        
        if sender == "You":
            formatted = f'<div style="color: #0066cc;"><b>[{timestamp}] You:</b> {message}</div>'
        else:
            formatted = f'<div style="color: #009900;"><b>[{timestamp}] {assistant_name}:</b> {message}</div>'
        
        self.chat_display.append(formatted)
        self.chat_display.append("")  # Empty line for spacing
        
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)
    
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle file drop"""
        urls = event.mimeData().urls()
        self.dragged_files = []
        
        for url in urls:
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.dragged_files.append(file_path)
        
        if self.dragged_files:
            # Show dropped files
            file_names = [os.path.basename(f) for f in self.dragged_files]
            if len(file_names) == 1:
                self.append_message("System", f"📎 File attached: {file_names[0]}")
                self.input_field.setPlaceholderText(f"Ask me about {file_names[0]}...")
            else:
                self.append_message("System", f"📎 {len(file_names)} files attached: {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''}")
                self.input_field.setPlaceholderText(f"Ask me about these {len(file_names)} files...")
            
            # Focus input so user can type
            self.input_field.setFocus()
    
    def send_message(self):
        """Send user message to Ollama"""
        message = self.input_field.text().strip()
        
        if not message:
            return
        
        # Check for force execute shortcut (Cmd+Enter will be handled separately)
        force_execute = False
        
        # Clear input
        self.input_field.clear()
        self.input_field.setPlaceholderText("Ask me anything about your files...")
        
        # Show user message
        self.append_message("You", message)
        
        # Log activity
        self.activity_log.add_activity(
            "Chat Message",
            "User",
            message[:50] + ("..." if len(message) > 50 else "")
        )
        
        # Add file context if files were dragged
        if self.dragged_files:
            file_context = self.build_file_context()
            message = f"{message}\n\n[FILES PROVIDED BY USER:\n{file_context}]"
            self.dragged_files = []  # Clear after use
        
        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("Thinking...")
        
        # Start Ollama thread with enhanced AI
        self.ollama_thread = OllamaThread(
            self.conversational_ai,
            message,
            self.conversation_history
        )
        self.ollama_thread.response_ready.connect(self.handle_response)
        self.ollama_thread.error_occurred.connect(self.handle_error)
        self.ollama_thread.start()
    
    def enrich_message_with_context(self, message):
        """Add available capabilities and file info to the message context"""
        
        # Start with the original message
        enriched = message
        
        # Add available capabilities
        capabilities = "\n\n[SYSTEM: Available capabilities:\n"
        
        if self.file_db:
            # Get quick stats
            stats = self.file_db.get_stats()
            capabilities += f"- SEARCH: Can search {stats['total_files']} indexed files by name, content, tags, or project\n"
        
        if self.file_ops:
            capabilities += "- ORGANIZE: Can move/rename files, organize by type or project\n"
            capabilities += "- Available folders to organize: Downloads, Desktop, Documents\n"
        
        # Check if message seems to reference specific files
        if 'this' in message.lower() or 'that' in message.lower() or 'these' in message.lower():
            capabilities += "- Note: If user says 'this' or 'that' file, ask them to be more specific\n"
        
        capabilities += "]\n"
        
        return enriched + capabilities
    
    def build_file_context(self):
        """Build context about dragged files from database"""
        context = ""
        
        for file_path in self.dragged_files:
            filename = os.path.basename(file_path)
            
            # Try to get file info from database
            cursor = self.file_db.conn.cursor()
            cursor.execute("""
                SELECT filename, extension, ai_summary, ai_tags, project, 
                       folder_location, modified_date
                FROM files WHERE path = ?
            """, (file_path,))
            
            result = cursor.fetchone()
            
            if result:
                fname, ext, summary, tags, project, folder, modified = result
                context += f"- {fname}\n"
                context += f"  Path: {file_path}\n"
                if summary:
                    context += f"  Summary: {summary}\n"
                if tags:
                    context += f"  Tags: {tags}\n"
                if project:
                    context += f"  Project: {project}\n"
                context += f"  Location: {folder}\n"
                context += f"  Modified: {modified}\n"
            else:
                # File not in database yet
                context += f"- {filename}\n"
                context += f"  Path: {file_path}\n"
                context += f"  (Not yet indexed - run a scan to analyze this file)\n"
            
            context += "\n"
        
        return context
    
    def should_search(self, message):
        """Detect if message is a search request"""
        search_keywords = [
            'find', 'search', 'look for', 'where', 'show me',
            'locate', 'get me', 'pull up', 'need', 'looking for'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in search_keywords)
    
    def should_organize(self, message):
        """Detect if message is a file organization request"""
        organize_keywords = [
            'move', 'organize', 'rename', 'delete', 'sort',
            'put', 'file', 'clean up', 'tidy'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in organize_keywords)
    
    def handle_search_request(self, message):
        """Handle file search"""
        # Extract search terms (simple approach - remove common words)
        stop_words = ['find', 'search', 'for', 'show', 'me', 'the', 'my', 'a', 'an', 
                     'where', 'is', 'are', 'that', 'those', 'this', 'these',
                     'look', 'looking', 'get', 'pull', 'up', 'need']
        
        words = message.lower().split()
        search_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not search_terms:
            self.append_message("Assistant", "What would you like me to search for?")
            return
        
        # Search database
        query = ' '.join(search_terms)
        results = self.file_db.search_files(query, limit=10)
        
        # Format response
        if results:
            response = f"I found {len(results)} file(s) matching '{query}':\n\n"
            for r in results[:5]:  # Show top 5
                response += f"📄 **{r['filename']}**\n"
                if r['ai_summary']:
                    response += f"   {r['ai_summary']}\n"
                response += f"   📁 {r['folder_location']}\n\n"
            
            if len(results) > 5:
                response += f"...and {len(results) - 5} more files."
        else:
            response = f"I couldn't find any files matching '{query}'. Try different search terms?"
        
        self.append_message("Assistant", response)
    
    def handle_organize_request(self, message):
        """Handle file organization commands"""
        import os
        
        message_lower = message.lower()
        
        # Check if user is confirming a previous organize request
        if hasattr(self, 'pending_organize'):
            if 'yes' in message_lower or 'ok' in message_lower or 'sure' in message_lower or 'go ahead' in message_lower:
                # Execute the pending operation
                pending = self.pending_organize
                delattr(self, 'pending_organize')
                
                if pending['type'] == 'downloads':
                    downloads = os.path.expanduser("~/Downloads")
                    response = "Organizing your Downloads folder by file type...\n\n"
                    results = self.file_ops.organize_by_type(downloads)
                    
                    response += f"✅ Moved {results['moved']} files\n"
                    response += f"⏭️  Skipped {results['skipped']} files\n"
                    
                    if results['errors']:
                        response += f"\n⚠️ {len(results['errors'])} errors:\n"
                        for error in results['errors'][:3]:
                            response += f"  - {error}\n"
                    
                    self.append_message("Assistant", response)
                    return
                    
                elif pending['type'] == 'desktop':
                    desktop = os.path.expanduser("~/Desktop")
                    response = "Organizing your Desktop by file type...\n\n"
                    results = self.file_ops.organize_by_type(desktop)
                    
                    response += f"✅ Moved {results['moved']} files\n"
                    response += f"⏭️  Skipped {results['skipped']} files\n"
                    
                    if results['errors']:
                        response += f"\n⚠️ {len(results['errors'])} errors:\n"
                        for error in results['errors'][:3]:
                            response += f"  - {error}\n"
                    
                    self.append_message("Assistant", response)
                    return
                    
                elif pending['type'] == 'project':
                    cursor = self.file_db.conn.cursor()
                    cursor.execute("""
                        SELECT id FROM files 
                        WHERE project IS NOT NULL AND project != ''
                        AND status = 'active'
                    """)
                    
                    file_ids = [row[0] for row in cursor.fetchall()]
                    
                    response = "Organizing files by project...\n\n"
                    results = self.file_ops.organize_by_project(file_ids, self.user_profile)
                    
                    if 'error' in results:
                        response += f"❌ {results['error']}"
                    else:
                        response += f"✅ Moved {results['moved']} files to project folders\n"
                        response += f"⏭️  Skipped {results['skipped']} files\n"
                    
                    self.append_message("Assistant", response)
                    return
                    
            elif 'no' in message_lower or 'cancel' in message_lower or 'nevermind' in message_lower:
                delattr(self, 'pending_organize')
                self.append_message("Assistant", "No problem! Let me know if you want to organize something else.")
                return
        
        # Organize Downloads by type
        if 'organize' in message_lower and 'download' in message_lower:
            self.pending_organize = {'type': 'downloads'}
            self.append_message("Assistant", 
                "I can organize your Downloads folder by sorting files into subfolders:\n\n"
                "📄 Documents/ - PDFs, Word docs, text files\n"
                "🖼️ Images/ - Photos and screenshots\n"
                "📊 Spreadsheets/ - Excel, CSV files\n"
                "📦 Archives/ - ZIP files\n"
                "💻 Code/ - Programming files\n"
                "...and more!\n\n"
                "Should I go ahead and organize it? (yes/no)"
            )
            return
        
        # Organize Desktop by type
        if 'organize' in message_lower and 'desktop' in message_lower:
            self.pending_organize = {'type': 'desktop'}
            self.append_message("Assistant", 
                "I can organize your Desktop by sorting files into subfolders by type "
                "(Documents, Images, Spreadsheets, etc.).\n\n"
                "Should I go ahead? (yes/no)"
            )
            return
        
        # Organize by project
        if 'organize' in message_lower and 'project' in message_lower:
            # Check if we have project-tagged files
            cursor = self.file_db.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM files 
                WHERE project IS NOT NULL AND project != ''
                AND status = 'active'
            """)
            
            count = cursor.fetchone()[0]
            
            if count == 0:
                self.append_message("Assistant", 
                    "I couldn't find any files tagged with projects yet. "
                    "Let me analyze some files first to figure out which projects they belong to!")
                return
            
            self.pending_organize = {'type': 'project'}
            self.append_message("Assistant", 
                f"I found {count} files tagged with projects. I can move them into "
                f"project folders in ~/Documents/Organized Files/.\n\n"
                f"Should I organize them? (yes/no)"
            )
            return
        
        # Default: explain what we can do
        self.append_message("Assistant", 
            "I can help organize your files! Here are some options:\n\n"
            "📥 'organize my Downloads' - Sort by file type\n"
            "🖥️ 'organize my Desktop' - Sort Desktop by type\n"
            "📁 'organize by project' - Sort into project folders\n\n"
            "Which would you like to try?"
        )
    
    def handle_response(self, result):
        """Handle enhanced AI response"""
        # Extract response and metadata
        response = result.get('response', '')
        intent = result.get('intent', '')
        action = result.get('action', '')
        
        # Log AI response activity
        self.activity_log.add_activity(
            "AI Response",
            "Assistant",
            f"Intent: {intent or 'chat'}" + (f", Action: {action}" if action else "")
        )
        
        # Add to conversation history (simplified format)
        self.conversation_history.append({"role": "user", "content": self.input_field.text()})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep conversation history manageable (last 20 messages)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        # Check if AI wants to execute an action
        if "[SEARCH:" in response:
            # AI wants to search - extract query
            import re
            match = re.search(r'\[SEARCH:\s*([^\]]+)\]', response)
            if match:
                query = match.group(1).strip()
                results = self.file_db.search_files(query, limit=10)
                
                # Log the search
                self.file_db.log_search(query, len(results), success=(len(results) > 0))
                
                # Format results
                if results:
                    search_results = f"\n\n📄 Found {len(results)} files:\n"
                    for r in results[:5]:
                        search_results += f"\n• {r['filename']}"
                        if r['ai_summary']:
                            search_results += f"\n  {r['ai_summary']}"
                        search_results += f"\n  📁 {r['folder_location']}\n"
                    
                    if len(results) > 5:
                        search_results += f"\n...and {len(results) - 5} more"
                    
                    # Learn from successful search
                    if len(results) > 0:
                        self.conversational_ai.learn_from_interaction(
                            query, 'SEARCH', f'found_{len(results)}_results', True
                        )
                else:
                    search_results = f"\n\n❌ No files found matching '{query}'"
                
                # Remove the [SEARCH:] tag and add results
                response = re.sub(r'\[SEARCH:[^\]]+\]', '', response).strip()
                response += search_results
        
        if "[ORGANIZE:" in response:
            # AI wants to organize - extract type
            import re
            match = re.search(r'\[ORGANIZE:\s*([^\]]+)\]', response)
            if match:
                org_type = match.group(1).strip().lower()
                
                if 'downloads' in org_type:
                    import os
                    downloads = os.path.expanduser("~/Downloads")
                    results = self.file_ops.organize_by_type(downloads)
                    
                    org_results = f"\n\n✅ Organized Downloads:\n"
                    org_results += f"• Moved: {results['moved']} files\n"
                    org_results += f"• Skipped: {results['skipped']} files\n"
                    
                    response = re.sub(r'\[ORGANIZE:[^\]]+\]', '', response).strip()
                    response += org_results
                
                elif 'desktop' in org_type:
                    import os
                    desktop = os.path.expanduser("~/Desktop")
                    results = self.file_ops.organize_by_type(desktop)
                    
                    org_results = f"\n\n✅ Organized Desktop:\n"
                    org_results += f"• Moved: {results['moved']} files\n"
                    org_results += f"• Skipped: {results['skipped']} files\n"
                    
                    response = re.sub(r'\[ORGANIZE:[^\]]+\]', '', response).strip()
                    response += org_results
        
        # Show response
        self.append_message("Assistant", response)
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        self.input_field.setFocus()
    
    def handle_error(self, error_msg):
        """Handle errors"""
        self.append_message("System", f"⚠️ {error_msg}")
        
        # Re-enable input
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")


class MainWindow(QMainWindow):
    """Main application window with tabs"""
    
    def __init__(self, user_profile=None):
        super().__init__()
        self.is_expanded = False
        self.user_profile = user_profile
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("File Organizer")
        
        # Initialize file database
        self.file_db = FileDatabase()
        
        # Initialize file operations
        # We'll pass activity_log after creating it
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Activity log (create first so chat can reference it)
        self.activity_log = ActivityLogWidget()
        
        # Initialize file operations with activity log
        self.file_ops = FileOperations(self.file_db, self.activity_log)
        
        # Chat tab with user profile, file database, and file operations
        self.chat_widget = ChatWidget(self.activity_log, self.user_profile, 
                                     self.file_db, self.file_ops)
        
        # Add tabs
        self.tabs.addTab(self.chat_widget, "💬 Chat")
        self.tabs.addTab(self.activity_log, "📋 Activity Log")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings")
        
        self.setCentralWidget(self.tabs)
        
        # Start in compact mode
        self.set_compact_mode()
        
        # Window flags
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
    
    def create_settings_tab(self):
        """Create the settings panel"""
        settings_widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        main_layout = QVBoxLayout()
        
        # Assistant Name Section
        name_group = QGroupBox("Assistant Identity")
        name_layout = QVBoxLayout()
        
        name_label = QLabel("Assistant Name:")
        self.assistant_name_input = QLineEdit()
        self.assistant_name_input.setText(self.get_setting('assistant_name', 'Assistant'))
        self.assistant_name_input.setPlaceholderText("e.g., Alfred, Jarvis, Helper...")
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.assistant_name_input)
        name_group.setLayout(name_layout)
        main_layout.addWidget(name_group)
        
        # Appearance Section
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        
        # Font size
        font_label = QLabel("Font Size:")
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Small", "Medium", "Large"])
        current_size = self.get_setting('font_size', 'Medium')
        self.font_size_combo.setCurrentText(current_size)
        
        # Theme
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        current_theme = self.get_setting('theme', 'Light')
        self.theme_combo.setCurrentText(current_theme)
        
        # Time format
        time_label = QLabel("Time Format:")
        self.time_format_check = QCheckBox("Use 12-hour format")
        self.time_format_check.setChecked(self.get_setting('time_12hr', True))
        
        appearance_layout.addWidget(font_label)
        appearance_layout.addWidget(self.font_size_combo)
        appearance_layout.addSpacing(10)
        appearance_layout.addWidget(theme_label)
        appearance_layout.addWidget(self.theme_combo)
        appearance_layout.addSpacing(10)
        appearance_layout.addWidget(time_label)
        appearance_layout.addWidget(self.time_format_check)
        
        appearance_group.setLayout(appearance_layout)
        main_layout.addWidget(appearance_group)
        
        # Personality Section
        personality_group = QGroupBox("Personality")
        personality_layout = QVBoxLayout()
        
        tone_label = QLabel("Conversation Style:")
        self.tone_combo = QComboBox()
        self.tone_combo.addItems(["Casual & Friendly", "Professional", "Concise"])
        current_tone = self.get_setting('tone', 'Casual & Friendly')
        self.tone_combo.setCurrentText(current_tone)
        
        personality_layout.addWidget(tone_label)
        personality_layout.addWidget(self.tone_combo)
        personality_group.setLayout(personality_layout)
        main_layout.addWidget(personality_group)
        
        # Auto-Organization Section
        auto_org_group = QGroupBox("Auto-Organization")
        auto_org_layout = QVBoxLayout()
        
        self.auto_scan_check = QCheckBox("Auto-scan for new files every hour")
        self.auto_scan_check.setChecked(self.get_setting('auto_scan', False))
        
        self.auto_tag_check = QCheckBox("Auto-tag new files with AI")
        self.auto_tag_check.setChecked(self.get_setting('auto_tag', False))
        
        auto_org_layout.addWidget(self.auto_scan_check)
        auto_org_layout.addWidget(self.auto_tag_check)
        auto_org_group.setLayout(auto_org_layout)
        main_layout.addWidget(auto_org_group)
        
        # Save Button
        save_button = QPushButton("💾 Save Settings")
        save_button.clicked.connect(self.save_settings)
        save_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        main_layout.addWidget(save_button)
        
        main_layout.addStretch()
        
        settings_widget.setLayout(main_layout)
        scroll.setWidget(settings_widget)
        
        return scroll
    
    def get_setting(self, key, default):
        """Get a setting from user profile"""
        settings = self.user_profile.get('settings', {})
        return settings.get(key, default)
    
    def save_settings(self):
        """Save all settings"""
        # Update settings in profile
        if 'settings' not in self.user_profile:
            self.user_profile['settings'] = {}
        
        self.user_profile['settings']['assistant_name'] = self.assistant_name_input.text()
        self.user_profile['settings']['font_size'] = self.font_size_combo.currentText()
        self.user_profile['settings']['theme'] = self.theme_combo.currentText()
        self.user_profile['settings']['time_12hr'] = self.time_format_check.isChecked()
        self.user_profile['settings']['tone'] = self.tone_combo.currentText()
        self.user_profile['settings']['auto_scan'] = self.auto_scan_check.isChecked()
        self.user_profile['settings']['auto_tag'] = self.auto_tag_check.isChecked()
        
        # Save to file
        save_user_profile(self.user_profile)
        
        # Apply settings immediately
        self.apply_settings()
        
        # Show confirmation
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved!")
    
    def apply_settings(self):
        """Apply settings to the UI"""
        settings = self.user_profile.get('settings', {})
        
        # Apply font size
        font_size_map = {'Small': 10, 'Medium': 12, 'Large': 14}
        font_size = font_size_map.get(settings.get('font_size', 'Medium'), 12)
        
        # Update chat widget font
        font = self.chat_widget.chat_display.font()
        font.setPointSize(font_size)
        self.chat_widget.chat_display.setFont(font)
        
        # Reload conversational AI with updated profile
        self.chat_widget.conversational_ai = ConversationalAI(
            model=self.chat_widget.model,
            user_profile=self.user_profile,
            file_db=self.file_db
        )
    
    def set_compact_mode(self):
        """Set window to compact size"""
        self.resize(500, 400)
        self.is_expanded = False
        
        # Position near top right corner
        screen = self.screen().geometry()
        self.move(screen.width() - self.width() - 20, 40)
    
    def set_expanded_mode(self):
        """Set window to expanded size"""
        self.resize(900, 700)
        self.is_expanded = True
    
    def toggle_size(self):
        """Toggle between compact and expanded"""
        if self.is_expanded:
            self.set_compact_mode()
        else:
            self.set_expanded_mode()


class FileOrganizerApp:
    """Main application with system tray"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Check if setup is needed
        if needs_setup():
            self.run_setup()
        
        # Load user profile
        self.user_profile = load_user_profile()
        
        # Main window with profile
        self.window = MainWindow(self.user_profile)
        
        # System tray
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self.create_icon())
        
        # Tray menu
        self.menu = QMenu()
        
        show_action = self.menu.addAction("Show Chat")
        show_action.triggered.connect(self.show_window)
        
        toggle_action = self.menu.addAction("Toggle Size")
        toggle_action.triggered.connect(self.window.toggle_size)
        
        self.menu.addSeparator()
        
        quit_action = self.menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(self.menu)
        
        # Click tray icon to show window
        self.tray_icon.activated.connect(self.tray_icon_clicked)
        
        self.tray_icon.show()
    
    def run_setup(self):
        """Run the setup wizard"""
        wizard = SetupWizard()
        if wizard.exec():
            profile = wizard.get_user_profile()
            save_user_profile(profile)
        else:
            # User cancelled - create a minimal profile
            minimal_profile = {
                "name": "there",
                "job": "User",
                "setup_completed": True
            }
            save_user_profile(minimal_profile)
        
    def create_icon(self):
        """Create a simple folder icon"""
        # For now, using a Unicode character
        # In production, you'd use an actual icon file
        from PyQt6.QtGui import QPixmap, QPainter, QColor
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a simple folder shape
        painter.setBrush(QColor("#FFB84D"))
        painter.setPen(QColor("#CC8800"))
        
        # Folder body
        painter.drawRect(8, 20, 48, 36)
        
        # Folder tab
        painter.drawRect(8, 14, 20, 10)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def tray_icon_clicked(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()
    
    def show_window(self):
        """Show and focus the main window"""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.chat_widget.input_field.setFocus()
    
    def quit_app(self):
        """Quit the application"""
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """Run the application"""
        return self.app.exec()


def main():
    """Entry point"""
    app = FileOrganizerApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
