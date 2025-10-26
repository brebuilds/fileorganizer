# 🗂️ ADHD-Friendly File Organizer

An intelligent macOS menu bar app that uses AI to help you find and organize files through natural conversation. Built specifically for people who struggle with file organization.

## ✨ Features

### 🤖 Intelligent Conversational AI
- **Natural language interface** - Just talk to it like a friend
- **Learns from every interaction** - Gets smarter over time
- **Context-aware responses** - Remembers your patterns and preferences
- **Proactive suggestions** - Helps you before you ask

### 🔍 Smart File Search
- **Full-text search** - Search inside documents
- **AI-powered tagging** - Automatically categorizes files
- **Project detection** - Recognizes which project files belong to
- **Learns search patterns** - Predicts what you're looking for

### 🧹 Automatic Organization
- **Organize by file type** - PDFs, images, documents, etc.
- **Organize by project** - Sorts into project folders
- **Safe operations** - Always confirms before moving files
- **Undo capability** - Operation history tracking

### 📊 Learning & Insights
- **Conversation memory** - Remembers past interactions
- **Pattern recognition** - Learns your organizational preferences
- **Usage analytics** - Tracks frequently accessed files
- **Smart suggestions** - Proactively recommends actions

### 🎨 Personalized Experience
- **Setup wizard** - Customizes to your workflow
- **Customizable personality** - Choose assistant's tone
- **Adaptive prompts** - Context changes based on your habits
- **Activity logging** - See all file operations

## 📋 Requirements

- **macOS** (tested on macOS 15.0+)
- **Python 3.13+**
- **Ollama** - Local AI model runtime
  - Install from [ollama.ai](https://ollama.ai)
  - Pull the model: `ollama pull llama3.2:3b`

## 🚀 Installation

### Option 1: Run from Source

1. **Clone or download this repository**

2. **Navigate to the project directory**
   ```bash
   cd "/Users/bre/file organizer"
   ```

3. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies** (if not already installed)
   ```bash
   pip install -r requirements.txt
   ```

5. **Make sure Ollama is running**
   ```bash
   ollama serve
   ```

6. **Run the application**
   ```bash
   python file_organizer_app.py
   ```

### Option 2: Build as macOS App

1. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

2. **Run the build script**
   ```bash
   chmod +x build_app.sh
   ./build_app.sh
   ```

3. **The app will be in the `dist/` folder**
   ```
   File Organizer.app
   ```

4. **Move to Applications**
   ```bash
   cp -r "dist/File Organizer.app" /Applications/
   ```

### Option 3: Quick Launch Script

Double-click `launch.command` to start the app quickly.

## 🎯 First-Time Setup

1. **Launch the app** - A setup wizard will appear
2. **Tell it about yourself**
   - Your name and role
   - Projects/clients you work with
   - Which folders to monitor
   - File types you work with
   - How you think about files

3. **Initial file scan** - Let it index your files
4. **Start chatting!** - Ask it to find or organize files

## 💬 How to Use

### Finding Files

Just ask naturally:
```
"Find that invoice from Phoenix"
"Where's my outline?"
"Show me PDFs from last week"
"I need something from ClientX"
```

### Organizing Files

Tell it what's messy:
```
"My downloads are a mess"
"Organize my desktop"
"Sort files by project"
"Clean up my documents"
```

The AI will:
1. Understand what you want
2. Explain what it will do
3. Ask for confirmation
4. Execute and report results

### Learning & Suggestions

The more you use it, the smarter it gets:
- Learns your search patterns
- Remembers organizational preferences
- Suggests actions proactively
- Predicts what you need

## 🗄️ Database Schema

The app uses SQLite with these tables:

### Files Table
- Stores all indexed files
- Tracks access patterns
- Includes AI-generated summaries and tags

### Conversations Table
- Logs all interactions
- Tracks intents and actions
- Used for learning

### Learned Patterns Table
- Stores user preferences
- Pattern recognition
- Confidence scoring

### Search History Table
- Tracks all searches
- Success metrics
- Helps improve results

### File Relationships Table
- Files accessed together
- Project associations
- Collaboration patterns

## 🧠 AI Architecture

### Conversational AI Module (`conversational_ai.py`)
- **Context-aware prompting** - Builds prompts based on user history
- **Intent detection** - Understands what you want
- **Pattern learning** - Learns from successful interactions
- **Smart suggestions** - Proactive recommendations

### Database Integration (`file_indexer.py`)
- **Full-text search** - FTS5 virtual tables
- **Conversation logging** - All interactions tracked
- **Pattern storage** - Learned behaviors
- **Usage analytics** - Access tracking

### AI Tagging (`ai_tagger.py`)
- **Content analysis** - Reads PDFs, text files
- **Project detection** - Matches to your projects
- **Tag generation** - Relevant, searchable tags
- **Batch processing** - Handles multiple files

### File Operations (`file_operations.py`)
- **Safe operations** - Prevents overwrites
- **Undo history** - Operation tracking
- **Activity logging** - All changes recorded
- **Error handling** - Graceful failures

## ⚙️ Configuration

Config stored in: `~/.fileorganizer/`

### Files:
- `config.json` - User profile and settings
- `files.db` - SQLite database

### Customization Options:
- Assistant name
- Conversation tone (Casual, Professional, Concise)
- Font size
- Time format
- Auto-scan settings
- Auto-tagging

## 🔧 Development

### Project Structure
```
/Users/bre/file organizer/
├── file_organizer_app.py      # Main GUI application
├── file_indexer.py             # Database & file indexing
├── conversational_ai.py        # Enhanced AI module
├── ai_tagger.py                # AI file tagging
├── file_operations.py          # File manipulation
├── setup_wizard.py             # First-run setup
├── requirements.txt            # Python dependencies
├── setup.py                    # py2app configuration
├── build_app.sh               # Build script
└── launch.command             # Quick launch script
```

### Adding Features

1. **Extend ConversationalAI** - Add new intents or learning patterns
2. **Database schema** - Migrations handled automatically
3. **File operations** - Add to `FileOperations` class
4. **UI components** - Modify `ChatWidget` or add new tabs

### Testing

Run individual modules:
```bash
# Test file indexing
python file_indexer.py

# Test AI tagging
python ai_tagger.py

# Test file operations
python file_operations.py

# Test setup wizard
python setup_wizard.py
```

## 🐛 Troubleshooting

### "Ollama not responding"
- Make sure Ollama is running: `ollama serve`
- Check model is downloaded: `ollama pull llama3.2:3b`
- Try restarting Ollama

### "No files found"
- Run initial scan from Settings
- Check monitored folders in Settings
- Verify file permissions

### "Database locked"
- Close all app instances
- Delete `~/.fileorganizer/files.db` to reset (loses history)

### "Import errors"
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

## 📈 Roadmap

- [ ] iCloud Drive integration
- [ ] File content previews
- [ ] Advanced analytics dashboard
- [ ] Smart file recommendations
- [ ] Duplicate file detection
- [ ] Automated cleanup schedules
- [ ] Multi-user support
- [ ] Cloud backup integration

## 🤝 Contributing

This is a personal project, but suggestions welcome!

## 📄 License

Personal use. Modify as needed for your own workflow.

## 🙏 Credits

Built with:
- **PyQt6** - GUI framework
- **Ollama** - Local AI runtime
- **SQLite** - Database
- **PyPDF2** - PDF processing

---

**Made for people who think faster than they can organize** 🧠✨

For questions or issues, check the database at `~/.fileorganizer/files.db` or review conversation logs in the database.

