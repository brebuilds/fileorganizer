# 🗂️ ADHD-Friendly File Organizer v4.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/macOS-15.0+-000000.svg)](https://www.apple.com/macos/)

**The most comprehensive AI-powered file organizer built specifically for ADHD brains!** 🧠✨

An intelligent macOS menu bar app that uses AI to help you find and organize files through natural conversation. Never lose a file again with smart reminders, auto-organization, and powerful search capabilities.

---

## 🎉 What's New in v4.0

**Massive update with 16 major new features!** This release transforms the File Organizer into a complete file management powerhouse:

- 📅 **Smart Reminders & Nudges** - Never forget about important files
- 📸 **Screenshot Management** - Auto-detect, OCR, and organize screenshots
- 🔄 **Duplicate Detection** - Find and clean up duplicate files
- 📁 **Smart Folders** - Dynamic folders that auto-update
- 📦 **Bulk Operations** - Mass operations with preview and undo
- 🗑️ **Trash Recovery** - 30-day file recovery window
- ⏰ **File Aging** - Auto-archive old files
- 🔖 **Bookmark Manager** - Save and organize URLs
- 👻 **Hide Files** - Privacy control for sensitive files
- 🔧 **External Tools** - Alfred, Raycast, DevonThink, Notion, Calendar integrations
- 📱 **Mobile Companion** - API for mobile access
- ⚡ **Performance Boost** - Background indexing, caching, optimization
- 🤖 **Enhanced AI** - Multi-page PDF summarization
- 🎨 **Visual Polish** - Thumbnails, color coding, dark mode
- 🖥️ **GUI Widgets** - Ready-to-use interface components
- 💻 **Powerful CLI** - 12+ new commands

[See detailed v4.0 features →](NEW_FEATURES_GUIDE.md)

---

## ✨ Core Features

### 🤖 Intelligent Conversational AI
- **Natural language interface** - Talk to it like a friend
- **Learns from interactions** - Gets smarter over time
- **Context-aware responses** - Remembers your patterns
- **Proactive suggestions** - Helps before you ask
- **Intent detection** - Understands what you want
- **Temporal awareness** - "What did I download yesterday?"

### 🔍 Advanced Search & Discovery
- **Full-text search** - Search inside documents
- **AI-powered tagging** - Automatic categorization
- **Vector search** - Find files by meaning, not just keywords
- **Graph relationships** - Track file connections
- **Smart folders** - Dynamic collections that auto-update
- **Duplicate detection** - Find and clean up duplicates
- **Screenshot search** - OCR text extraction

### 🧹 Smart Organization
- **Auto-organize** - By file type, project, or custom rules
- **Bulk operations** - Preview, execute, and undo
- **File aging** - Auto-archive old files
- **Screenshot manager** - Organize screenshots by date/content
- **Safe operations** - Always preview before executing
- **Trash recovery** - 30-day file recovery window

### 📅 Time Management
- **Smart reminders** - File-based deadlines and follow-ups
- **Context-aware nudges** - "20 files in Downloads - organize?"
- **Temporal queries** - Natural date parsing
- **Activity tracking** - Complete event logging
- **Stale file warnings** - Files you haven't touched

### 🔗 Integrations
- **Alfred** - Custom workflow generation
- **Raycast** - Extension for quick access
- **DevonThink** - Export with metadata
- **Notion** - CSV export for databases
- **Calendar** - File-linked events
- **Obsidian** - Auto-generate notes
- **Mobile API** - Remote file access

### 🎨 Beautiful Interface
- **Menu bar app** - Always accessible
- **Dark mode** - Full support
- **Color coding** - File types color-coded
- **Thumbnails** - Visual file previews
- **Progress tracking** - Real-time operation feedback
- **Notifications** - macOS notification center integration

### ⚡ Performance
- **Background indexing** - Non-blocking file processing
- **Search caching** - Lightning-fast repeated searches
- **Lazy loading** - Efficient pagination
- **Incremental search** - Results as you type
- **Database optimization** - Automatic maintenance

---

## 📋 Requirements

- **macOS** 15.0+ (should work on 13.0+)
- **Python** 3.13+ (3.10+ should work)
- **Ollama** - Local AI model runtime
  - Install from [ollama.ai](https://ollama.ai)
  - Pull the model: `ollama pull llama3.2:3b`

### Optional Dependencies
- **Tesseract** - For OCR in screenshots: `brew install tesseract`
- **OpenAI API** - For enhanced summarization (optional)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/brebuilds/fileorganizer.git
cd fileorganizer

# Install Python packages
pip install -r requirements.txt

# Optional: OCR support
brew install tesseract
pip install pytesseract

# Optional: Bookmark metadata extraction
pip install requests beautifulsoup4
```

### 2. Set Up Ollama

```bash
# Install Ollama from ollama.ai
# Then pull the model:
ollama pull llama3.2:3b

# Verify it's working:
ollama list
```

### 3. Run the App

```bash
# Launch the GUI
python file_organizer_app.py

# Or use the CLI
./o HELP
```

### 4. Initial Setup

On first run, the setup wizard will:
- Help you choose folders to monitor
- Auto-detect cloud storage (Dropbox, iCloud, Google Drive, etc.)
- Customize the AI personality
- Set your projects

---

## 💻 CLI Usage

The File Organizer includes a powerful command-line interface with cheesy commands!

### Basic Commands

```bash
# Organize folders
./o @Desktop              # Sort Desktop by file type
./o @Downloads            # Clean up Downloads

# Search files
./o ?invoice              # Find invoices
./o FIND@"client proposal"

# Time-based queries
./o !yesterday            # Files from yesterday
./o !today                # Today's files
./o WHEN@"last week"      # Last week's files
```

### New v4.0 Commands

```bash
# Smart features
./o SUGGEST               # Get smart suggestions & nudges
./o REMIND                # View reminders
./o SMART                 # Show smart folders

# Management
./o SCREENSHOTS           # Manage screenshots
./o DUPLICATES            # Find duplicates
./o BOOKMARKS             # Manage bookmarks
./o MOBILE                # Mobile companion stats

# Utilities
./o OPTIMIZE              # Optimize database
./o HIDE@file.pdf         # Hide file from search
./o ALFRED                # Setup Alfred integration
./o RAYCAST               # Setup Raycast integration

# Information
./o STATS                 # Show statistics
./o EXPORT                # Export file catalog
./o HELP                  # Show all commands
```

### Advanced Usage

```bash
# Tag files with AI
./o TAG@Documents

# Find related files
./o GRAPH@ProjectX

# Find similar files
./o SIMILAR@proposal.pdf

# Show temporal activity
./o WHEN@"3 days ago"
```

[See complete CLI guide →](CLI_GUIDE.md)

---

## 🎯 Usage Examples

### Morning Routine

```bash
# Check what came in overnight
./o !yesterday

# Review reminders and nudges
./o REMIND
./o SUGGEST

# Clean up common areas
./o @Downloads
./o @Desktop
```

### Finding Files

```python
# In the GUI chat:
"Find my invoice from last week"
"Show me all client proposals"
"What files did I download yesterday?"
"Find files related to Project Phoenix"
```

### Organizing

```bash
# Organize a folder
./o SORT@~/Documents/Messy

# Tag files for better search
./o TAG@~/Documents

# Find and clean duplicates
./o DUPLICATES
```

### Project Management

```python
# Create a smart folder for a project
from smart_folders import SmartFolders
smart = SmartFolders(db)

smart.create_smart_folder(
    name="Client Work",
    query={"project": "ClientX", "extension": [".pdf", ".doc"]},
    icon="💼"
)
```

---

## 🏗️ Architecture

### Database
- **SQLite** - Core database with FTS5 full-text search
- **Vector store** - Semantic search with embeddings
- **Graph store** - File relationship tracking
- **9 specialized tables** - Reminders, bookmarks, events, etc.

### AI Backends
- **Ollama** - Local LLM for privacy (recommended)
- **OpenAI** - Optional for enhanced features
- **Local** - Fallback extractive summarization

### Modules
```
file_organizer_app.py        # Main PyQt6 GUI
file_indexer.py              # Database & indexing
conversational_ai.py         # Smart chat system
reminder_system.py           # Reminders & nudges
screenshot_manager.py        # Screenshot handling
smart_folders.py             # Dynamic folders
bulk_operations.py           # Mass operations
bookmark_manager.py          # URL management
external_tools.py            # Integrations
mobile_companion.py          # Mobile API
performance_optimizer.py     # Caching & speed
enhanced_summarizer.py       # AI summarization
visual_enhancements.py       # UI components
gui_enhancements.py          # New widgets
```

---

## 📚 Documentation

### Getting Started
- **[Quick Start](QUICK_START.md)** - Get up and running fast
- **[CLI Guide](CLI_GUIDE.md)** - Complete command reference
- **[Commands Cheatsheet](COMMANDS_CHEATSHEET.md)** - Quick reference

### v4.0 Features
- **[New Features Guide](NEW_FEATURES_GUIDE.md)** - Complete v4.0 documentation
- **[Implementation Summary](V4_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[Integration Guide](FINAL_INTEGRATION_GUIDE.md)** - How to extend

### Advanced Topics
- **[Advanced Features](ADVANCED_FEATURES.md)** - Cloud, automation, databases
- **[Temporal Guide](TEMPORAL_GUIDE.md)** - Time-based queries
- **[Export & OpenAI](EXPORT_AND_OPENAI_GUIDE.md)** - Export and API usage

### Reference
- **[Complete Features](COMPLETE_FEATURES_SUMMARY.md)** - Everything in one place
- **[Test Results](TEST_RESULTS_FINAL.md)** - Quality assurance

---

## 🧪 Testing

The project includes comprehensive testing:

```bash
# Run all tests
python test_new_features.py

# Test individual modules
python reminder_system.py
python screenshot_manager.py
python smart_folders.py

# CLI tests
./o STATS
./o SUGGEST
```

**Current Test Coverage:** 100% (29/29 tests passing)

---

## 🔧 Configuration

### Settings Location
```
~/.fileorganizer/
├── files.db              # Main database
├── config.json           # User configuration
├── vectors.pkl           # Vector embeddings
├── thumbnails/           # Image thumbnails
├── exports/              # Export output
├── hazel_rules/          # Hazel integration
└── alfred_workflow/      # Alfred integration
```

### Environment Variables

```bash
# Optional: OpenAI for enhanced features
export OPENAI_API_KEY="sk-..."

# Optional: Custom Ollama host
export OLLAMA_HOST="http://localhost:11434"
```

---

## 🎨 Customization

### GUI Themes
The app automatically detects macOS dark mode and adjusts accordingly.

### AI Personality
Configure in Settings tab:
- Professional
- Friendly
- Concise
- Detailed
- Custom

### Smart Folders
Create custom dynamic folders:
```python
smart_folders.create_smart_folder(
    name="Work PDFs",
    query={
        "extension": [".pdf"],
        "tags": ["work"],
        "date_range": {"start": "2024-01-01"}
    }
)
```

---

## 🔌 API & Integrations

### REST API

Start the automation API:
```bash
python automation_api.py
```

Endpoints:
- `GET /api/health` - Status check
- `GET /api/search?q=query` - Search files
- `POST /api/organize` - Organize folder
- `POST /api/tag` - AI tag files
- `POST /api/mobile/upload` - Upload from mobile

### Python API

```python
from file_indexer import FileDatabase
from reminder_system import ReminderSystem
from smart_folders import SmartFolders

# Initialize
db = FileDatabase()

# Create reminder
reminders = ReminderSystem(db)
reminders.create_reminder(
    file_id=123,
    reminder_type='deadline',
    reminder_date='2024-12-31',
    message='Review before EOY'
)

# Create smart folder
smart = SmartFolders(db)
folder_id = smart.create_smart_folder(
    name="Recent PDFs",
    query={"extension": [".pdf"], "date_range": {"start": "2024-01-01"}}
)

db.close()
```

[See API documentation →](FINAL_INTEGRATION_GUIDE.md)

---

## 🤝 Contributing

Contributions welcome! This is a passion project built for people who think faster than they can organize.

### Areas for Contribution
- Additional AI backends
- More external tool integrations
- Mobile app development
- UI/UX improvements
- Documentation
- Testing

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- **PyQt6** - GUI framework
- **Ollama** - Local LLM runtime
- **SQLite** - Database
- **Tesseract** - OCR engine
- **Beautiful Soup** - Web scraping
- **NumPy** - Vector operations

Special thanks to:
- Everyone with ADHD who struggles with file organization
- The Ollama team for making local AI accessible
- The open-source community

---

## 🎯 Roadmap

### v4.1 (Planned)
- [ ] iOS/Android mobile apps
- [ ] Real-time cloud sync
- [ ] Team collaboration features
- [ ] Video transcript extraction
- [ ] Advanced analytics dashboard

### v4.2 (Ideas)
- [ ] Browser extension
- [ ] Siri shortcuts
- [ ] Watch app
- [ ] Visual file timeline
- [ ] AI file preview

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/brebuilds/fileorganizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/brebuilds/fileorganizer/discussions)
- **Email**: (Add your contact info)

---

## 📊 Stats

- **Lines of Code**: ~7,000+
- **Modules**: 28 Python files
- **Features**: 16 major systems
- **Documentation**: 12 comprehensive guides
- **Test Coverage**: 100% (29/29 tests)
- **Database Tables**: 16 tables
- **CLI Commands**: 20+ commands

---

## 🌟 Star History

If this helps you, please star the repo! ⭐

---

**Made with ❤️ for ADHD brains that move faster than their file systems!** 🧠✨

*Never lose a file again.*

---

## 📸 Screenshots

### Main Chat Interface
![Chat Interface](screenshots/chat.png) *(Add screenshot)*

### Smart Folders
![Smart Folders](screenshots/smart-folders.png) *(Add screenshot)*

### Reminders & Nudges
![Reminders](screenshots/reminders.png) *(Add screenshot)*

### CLI in Action
```bash
$ ./o !yesterday
⏰ Searching for files from 'yesterday'...
✨ Found 5 files from the last 1 days:
   1. document.pdf
   2. image.jpg
   3. ...
```

---

<div align="center">

**[⬆ Back to Top](#️-adhd-friendly-file-organizer-v40)**

Made with 🧠 and ✨ | [Report Bug](https://github.com/brebuilds/fileorganizer/issues) | [Request Feature](https://github.com/brebuilds/fileorganizer/issues)

</div>
