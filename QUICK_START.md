# 🚀 Quick Start Guide

## TL;DR

Your file organizer now has **advanced AI with machine learning**. It learns from every interaction and gets smarter over time!

## Start in 3 Steps

### 1. Test Everything Works
```bash
cd "/Users/bre/file organizer"
./one/bin/python test_system.py
```

Expected: `6/6 tests passed (100%) 🎉`

### 2. Launch the App
```bash
./one/bin/python file_organizer_app.py
```

Or double-click: `launch.command`

### 3. Start Chatting!
Just talk naturally:
- "Find my invoice from last week"
- "My downloads are a mess"
- "Show me stuff from ClientX"

## What's New?

### 🧠 AI That Learns
- Remembers your search patterns
- Learns how you like to organize
- Makes smart suggestions
- Gets better with each use

### 📊 Full Conversation Tracking
- Every chat is logged
- Patterns are learned
- Suggestions improve over time

### 🎯 Proactive Suggestions
- Notices when folders are messy
- Suggests organization based on your preferences
- Offers quick access to frequent files

## Using the Virtual Environment

The working environment is in the `one/` directory:

```bash
# Activate
source ./one/bin/activate

# Run app
python file_organizer_app.py

# Run tests
python test_system.py

# Deactivate when done
deactivate
```

## File Locations

### Your Data
```
~/.fileorganizer/
├── config.json      # Your settings & profile
└── files.db         # File index & learning data
```

### Source Code
```
/Users/bre/file organizer/
├── file_organizer_app.py   # Main app
├── conversational_ai.py    # AI brain (NEW!)
├── file_indexer.py         # Database (enhanced!)
├── ai_tagger.py            # File tagging
├── file_operations.py      # File management
└── test_system.py          # Test suite
```

## Common Commands

### Run the app
```bash
./one/bin/python file_organizer_app.py
```

### Run tests
```bash
./one/bin/python test_system.py
```

### Index new files
Open app → Settings → "Scan folders now"

### Check what AI learned
```bash
./one/bin/python -c "
from file_indexer import FileDatabase
db = FileDatabase()
patterns = db.get_learned_patterns()
for p in patterns[:10]:
    print(f\"{p['pattern_key']}: {p['confidence']:.2f}\")
db.close()
"
```

### View conversation history
```bash
./one/bin/python -c "
from file_indexer import FileDatabase
db = FileDatabase()
convos = db.get_recent_conversations(10)
for c in convos:
    print(f\"You: {c['user_message'][:50]}...\")
    print(f\"AI: {c['assistant_response'][:50]}...\")
    print()
db.close()
"
```

## Example Conversations

### Finding Files
```
You: "I need that Phoenix thing"
AI:  "Looking for Phoenix files! I see you've accessed Phoenix 
      project files recently. Want me to show all Phoenix files 
      or something specific?"
```

### Organizing
```
You: "everything is chaos"
AI:  "I can help! Based on your past preferences, you usually 
      organize by project. Want me to sort your Downloads into 
      project folders?"
```

### Learning in Action
```
Week 1: You search for invoices 3 times
Week 2: AI suggests: "Want me to create an Invoices folder?"
Week 3: AI automatically prioritizes invoice-related results
```

## Settings

Access via app → Settings tab:
- **Assistant Name** - Customize AI's name
- **Conversation Style** - Casual / Professional / Concise
- **Font Size** - Adjust readability
- **Auto-scan** - Automatic file indexing
- **Auto-tag** - AI tags new files

## Troubleshooting

### "Module not found"
```bash
cd "/Users/bre/file organizer"
./one/bin/pip install -r requirements.txt
```

### "Ollama not responding"
```bash
# In another terminal
ollama serve

# Check model is downloaded
ollama list
ollama pull llama3.2:3b
```

### "Database error"
```bash
# Backup first
cp ~/.fileorganizer/files.db ~/.fileorganizer/files.db.backup

# Re-run app - it will migrate automatically
./one/bin/python file_organizer_app.py
```

### "App won't start"
```bash
# Run tests to diagnose
./one/bin/python test_system.py
```

## Tips for Best Results

1. **Use it daily** - AI learns from regular use
2. **Complete actions** - Don't just search, click results
3. **Be natural** - Talk like you would to a friend
4. **Trust suggestions** - AI learns what works for you
5. **Give it a week** - Needs 5-10 interactions to really learn

## What Gets Better Over Time?

- **Search**: Learns what terms you use
- **Organization**: Remembers your preferred style
- **Suggestions**: Gets more accurate with use
- **Context**: Understands your projects better
- **Speed**: Faster responses as patterns solidify

## Need More Info?

- **Full details**: See `README.md`
- **Technical deep-dive**: See `ENHANCEMENTS_SUMMARY.md`
- **Test results**: Run `test_system.py`

## Ready? Let's Go!

```bash
cd "/Users/bre/file organizer"
./one/bin/python file_organizer_app.py
```

Start chatting and watch it get smarter! 🧠✨

---

**Questions?** Check the database at `~/.fileorganizer/files.db` for all conversation logs and learned patterns.

