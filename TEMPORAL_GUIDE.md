# ⏰ Temporal Tracking Guide

## Ask About Files Over Time!

Your File Organizer now tracks **when** files appeared and lets you query them with natural language!

---

## 🎯 Quick Examples

### In the Chat
```
You: What files did I download yesterday?
AI: I found 1 file from yesterday: PowerPoint presentation from 4:51 AM

You: Show me files from last week
AI: Found 20 files from Oct 13 to Oct 20...

You: What did I get today?
AI: You have 3 new files today...
```

### In the CLI
```bash
# Using shortcuts
./o !yesterday              # Files from yesterday
./o !today                  # Files from today
./o !'last week'            # Files from last week

# Using full commands
./o WHEN@yesterday
./o WHEN@"last 3 days"
./o WHEN@"this morning"
```

---

## 📅 Supported Time Expressions

### Relative Times
- `yesterday` - All files from yesterday
- `today` - Files from today so far
- `this morning` - Today's morning files
- `this afternoon` - Today's afternoon files

### Ranges
- `last week` - Files from 7 days ago
- `this week` - Files since Monday
- `last month` - Files from the past ~30 days
- `this month` - Files since the 1st

### Specific Periods
- `last 3 days` - Files from the last 3 days
- `last 7 days` - Last week
- `2 hours ago` - Files from the last 2 hours
- `5 days ago` - Files from exactly 5 days ago

---

## 🔍 Query Types

The AI understands different types of temporal queries:

### Downloads
```
"What files did I download yesterday?"
"Show me what I downloaded last week"
"What did I get this morning?"
```

### Modifications
```
"What files changed yesterday?"
"Show me modified files from last week"
"What did I edit today?"
```

### Access
```
"What files did I open yesterday?"
"Show me recently accessed files"
"What did I look at this morning?"
```

### General Activity
```
"What happened yesterday?"
"Show me recent files"
"Any activity from last week?"
```

---

## 🧠 How It Works

### File Events Tracked
The system tracks:
1. **Discovered** - First time the system saw the file
2. **Downloaded** - File appeared in Downloads folder
3. **Modified** - File was changed
4. **Accessed** - File was opened/viewed
5. **Moved** - File was relocated
6. **Tagged** - File was AI-tagged

### Database
All events are stored in the `file_events` table with timestamps, so you can query your file history at any time.

### Natural Language Parsing
The `TemporalTracker` parses phrases like "yesterday" and "last week" into actual date ranges automatically.

---

## 💡 Use Cases

### Morning Review
```bash
# What came in overnight?
./o !yesterday

# Or in chat:
"What files did I download yesterday?"
```

### Weekly Cleanup
```bash
# See what accumulated this week
./o WHEN@'this week'

# Or:
"Show me all files from this week"
```

### Finding Recent Work
```bash
# What was I working on?
./o WHEN@'last 3 days'

# Or in chat:
"What files did I modify in the last 3 days?"
```

### Tracking Downloads
```bash
# Check recent downloads
./o WHEN@'today'

# Or:
"What did I download today?"
```

---

## 🎨 Chat Integration

The conversational AI automatically detects temporal queries and provides smart responses:

```
You: What files did I download yesterday?

AI: I found 1 file from yesterday:

1. V2.Parents-Kids-and-Money.pptx
   📁 /Users/bre/Downloads/Presentations
   🕐 2025-10-24 04:51
   PowerPoint presentation about financial literacy...
```

The AI will:
- Parse your time expression
- Search the database
- Format results nicely
- Log the interaction for learning

---

## 🚀 Advanced Features

### Activity Summary
Get a quick overview of recent activity:

```python
from temporal_tracker import TemporalTracker
from file_indexer import FileDatabase

db = FileDatabase()
tracker = TemporalTracker(db)

summary = tracker.get_activity_summary(days=7)
print(f"New files: {summary['discovered']}")
print(f"Modified: {summary['modified']}")
print(f"Accessed: {summary['accessed']}")
```

### File Timeline
See the complete history of a specific file:

```python
timeline = tracker.get_file_timeline(file_id=123)
print(f"File: {timeline['filename']}")
print(f"Created: {timeline['created']}")
print(f"Accessed {timeline['access_count']} times")

for event in timeline['events']:
    print(f"  {event['timestamp']}: {event['type']}")
```

---

## 🔧 Technical Details

### Database Schema
```sql
CREATE TABLE file_events (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    event_type TEXT NOT NULL,  -- discovered, modified, accessed, etc.
    event_timestamp TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id)
);

-- Indexed for fast temporal queries
CREATE INDEX idx_event_timestamp ON file_events(event_timestamp);
CREATE INDEX idx_event_type ON file_events(event_type);
```

### Intent Detection
The conversational AI checks for temporal keywords:
- `yesterday`, `today`, `last week`
- `downloaded`, `got`, `received`
- `when did`, `ago`, `this morning`

When detected, it routes to the temporal handler instead of general chat.

---

## 📊 Statistics & Monitoring

### View Activity
```bash
# See overall stats including recent activity
./o STATS
```

Output includes:
```
📊 File Organizer Statistics

   📁 Total Files: 220
   📂 Folders: 9
   📄 File Types: 10

   🏷️  Top Tags:
      • automation: 4
      • n8n: 3
      • ai: 2

   🧠 Learned 1 patterns
```

---

## 🎯 Tips & Tricks

### 1. Check Before Cleanup
```bash
# See what you have before organizing
./o !yesterday
./o @Desktop    # Then cleanup
```

### 2. Track Project Files
```bash
# Find when project files were added
./o WHEN@'last month'

# Then see relationships
./o GRAPH@ProjectName
```

### 3. Monitor Downloads Folder
```bash
# Daily check
./o WHEN@today

# If lots of files, clean up
./o @Downloads
```

### 4. Use in Scripts
```bash
#!/bin/bash
# morning-review.sh

echo "📅 Yesterday's files:"
./o !yesterday

echo -e "\n📊 Overall stats:"
./o STATS
```

---

## 🐛 Troubleshooting

### "No files found from that time period"

**Solution:** Files must be indexed first
```bash
# Index your folders
./o TAG@Desktop
./o TAG@Downloads

# Then query
./o !yesterday
```

### Time range seems wrong

The parser uses these defaults:
- If unsure, defaults to last 24 hours
- "Last week" = 7 days ago to today
- "Yesterday" = previous day, 00:00 to 23:59

### Want more specific times?

Use full date queries:
```bash
./o WHEN@'last 2 hours'    # More specific
./o WHEN@'last 10 days'    # Longer range
```

---

## 🎊 Next Steps

1. **Try it in chat:**
   ```
   "What did I download yesterday?"
   ```

2. **Use CLI shortcuts:**
   ```bash
   ./o !yesterday
   ./o !today
   ```

3. **Combine with other features:**
   ```bash
   # Find similar to yesterday's files
   ./o !yesterday
   # Pick a file, then:
   ./o SIMILAR@thatfile.pdf
   ```

4. **Set up monitoring:**
   Add to your cron or daily script!

---

**Your files are now time-aware!** ⏰✨

Ask the AI "what files did I download yesterday?" and watch the magic happen!

