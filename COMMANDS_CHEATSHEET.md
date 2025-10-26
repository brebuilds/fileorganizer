# 🚀 Commands Cheatsheet

Quick reference for all features.

---

## 📋 Essential Commands

### Start the App
```bash
cd "/Users/bre/file organizer"
./one/bin/python file_organizer_app.py
```

### Run All Tests (Verify Everything Works)
```bash
./one/bin/python test_system.py
# Should show: 6/6 tests passed ✅
```

---

## 📤 Export Your File Index

### Export to All Formats (JSON, CSV, HTML, Markdown)
```bash
./one/bin/python export_manager.py
```

### View Interactive HTML Catalog
```bash
# After exporting
open ~/.fileorganizer/exports/file_index_*.html
```

### Export to Specific Location
```python
from export_manager import ExportManager
from file_indexer import FileDatabase

db = FileDatabase()
em = ExportManager(db)

# Custom location
em.export_to_html('/Users/bre/Desktop/my_files.html')
em.export_to_csv('/Users/bre/Desktop/my_files.csv')

db.close()
```

---

## ☁️ Cloud Storage

### Detect Cloud Services
```bash
./one/bin/python cloud_storage.py
```

### Check if File is in Cloud
```python
from cloud_storage import CloudStorageDetector

detector = CloudStorageDetector()
is_cloud = detector.is_cloud_path('/Users/bre/Dropbox/file.pdf')
service = detector.get_service_for_path('/Users/bre/Dropbox/file.pdf')
```

---

## 🔍 Vector Search (Semantic)

### Test Vector Search
```bash
./one/bin/python vector_store.py
```

### Index All Files with Vectors
```python
from vector_store import VectorSearchIntegration
from file_indexer import FileDatabase

db = FileDatabase()
vs = VectorSearchIntegration(db)

# Index everything
indexed = vs.index_all_files()
print(f'Indexed {indexed} files')

db.close()
```

### Semantic Search
```python
# Find files by meaning
results = vs.semantic_search("project documentation", top_k=10)
for r in results:
    print(f"{r['filename']} - similarity: {r['similarity']:.2f}")
```

### Find Related Files
```python
# Find files similar to a specific file
related = vs.find_related_files(
    "/Users/bre/Documents/proposal.pdf",
    top_k=5
)
```

---

## 🕸️ Graph Database

### Build Graph from Database
```bash
./one/bin/python graph_store.py
```

### Graph Queries
```python
from graph_store import FileGraphIntegration
from file_indexer import FileDatabase

db = FileDatabase()
graph = FileGraphIntegration(db)

# Build graph
stats = graph.build_graph_from_database()

# Find all files in a project
files = graph.find_all_project_files("ProjectName")

# Find files by tag
files = graph.find_files_by_tag("invoice")

db.close()
```

---

## 🔌 Automation API

### Start API Server
```bash
./one/bin/python automation_api.py
# Runs on: http://localhost:8765
```

### Test API
```bash
# Health check
curl http://localhost:8765/api/health

# Get stats
curl http://localhost:8765/api/stats

# Search files
curl http://localhost:8765/api/search?q=invoice

# Organize folder
curl -X POST http://localhost:8765/api/organize \
  -H "Content-Type: application/json" \
  -d '{"folder": "/Users/bre/Downloads", "type": "by_type"}'
```

---

## 🎯 Hazel Integration

### Setup Hazel Scripts
```bash
./one/bin/python hazel_integration.py
```

### Scripts Location
```
~/.fileorganizer/hazel_scripts/
  - organize_by_type.scpt
  - ai_tag.scpt
  - smart_move.scpt
```

### Test Python Bridge
```bash
# Organize a folder
./one/bin/python hazel_bridge.py organize "/Users/bre/Downloads"

# Tag a file
./one/bin/python hazel_bridge.py tag "/Users/bre/Documents/file.pdf"

# Smart move
./one/bin/python hazel_bridge.py smart_move "/Users/bre/Desktop/file.pdf"
```

---

## 🤖 OpenAI Integration (Optional)

### Setup
```bash
./one/bin/python openai_integration.py
# Follow prompts to enter API key
```

### Tag Files with OpenAI
```bash
# Interactive mode
./one/bin/python openai_integration.py
```

### Programmatic Tagging
```python
from openai_integration import OpenAITagger
from file_indexer import FileDatabase

db = FileDatabase()
tagger = OpenAITagger()

# Tag 10 untagged files
stats = tagger.batch_tag_files(db, limit=10)

print(f"Tagged: {stats['tagged']}")
print(f"Tokens: {stats['total_tokens']}")
print(f"Cost: ${stats['total_tokens'] * 0.00000015:.4f}")

db.close()
```

---

## 🗄️ Database Operations

### View Stats
```python
from file_indexer import FileDatabase

db = FileDatabase()
stats = db.get_stats()

print(f"Total files: {stats['total_files']}")
print(f"By folder: {stats['by_folder']}")
print(f"By extension: {stats['by_extension']}")

db.close()
```

### Search Files
```python
# Keyword search
results = db.search_files("invoice", limit=20)

# Get recent files
recent = db.get_recent_files(limit=10)

# Get frequently accessed
frequent = db.get_frequently_accessed_files(limit=10)
```

### View Learned Patterns
```python
# Get what AI has learned
patterns = db.get_learned_patterns()
for p in patterns:
    print(f"{p['pattern_key']}: {p['confidence']:.2f} ({p['frequency']}x)")
```

### View Conversation History
```python
# Get recent conversations
convos = db.get_recent_conversations(limit=20)
for c in convos:
    print(f"You: {c['user_message']}")
    print(f"AI: {c['assistant_response'][:100]}...")
```

---

## 📊 One-Liners

### Check System Status
```bash
./one/bin/python -c "from file_indexer import FileDatabase; db = FileDatabase(); print(f\"Files: {db.get_stats()['total_files']}\"); db.close()"
```

### Quick Export
```bash
./one/bin/python -c "from export_manager import ExportManager; from file_indexer import FileDatabase; db = FileDatabase(); em = ExportManager(db); results = em.export_all_formats(); print('✅ Exported to ~/.fileorganizer/exports/'); db.close()"
```

### Index with Vectors
```bash
./one/bin/python -c "from vector_store import VectorSearchIntegration; from file_indexer import FileDatabase; db = FileDatabase(); vs = VectorSearchIntegration(db); n = vs.index_all_files(); print(f'Indexed {n} files'); db.close()"
```

### Build Graph
```bash
./one/bin/python -c "from graph_store import FileGraphIntegration; from file_indexer import FileDatabase; db = FileDatabase(); g = FileGraphIntegration(db); s = g.build_graph_from_database(); print(f\"Graph: {s['total_nodes']} nodes, {s['total_edges']} edges\"); db.close()"
```

---

## 🔧 Maintenance

### Reset Database (Fresh Start)
```bash
rm ~/.fileorganizer/files.db
rm ~/.fileorganizer/vectors.pkl
# App will rebuild on next launch
```

### Re-index Everything
```python
from file_indexer import FileDatabase, FileIndexer
from setup_wizard import load_user_profile

db = FileDatabase()
indexer = FileIndexer(db)
profile = load_user_profile()

for folder in profile['monitored_folders']:
    print(f"Scanning {folder}...")
    indexed, skipped = indexer.scan_folder(folder)
    print(f"  Indexed: {indexed}, Skipped: {skipped}")

db.close()
```

### Update Vector Embeddings
```python
from vector_store import VectorSearchIntegration
from file_indexer import FileDatabase

db = FileDatabase()
vs = VectorSearchIntegration(db)

# Re-index everything (force update)
indexed = vs.index_all_files(limit=None)
print(f'Re-indexed {indexed} files')

db.close()
```

---

## 📁 File Locations

```
Config & Data:
  ~/.fileorganizer/config.json        # User profile
  ~/.fileorganizer/files.db           # Main database
  ~/.fileorganizer/vectors.pkl        # Vector embeddings
  ~/.fileorganizer/openai_key         # OpenAI API key (if set)
  
Exports:
  ~/.fileorganizer/exports/           # All exported indexes
  
Hazel:
  ~/.fileorganizer/hazel_scripts/     # AppleScript files
  
Source Code:
  /Users/bre/file organizer/          # All .py files
```

---

## 🆘 Troubleshooting

### "Module not found"
```bash
cd "/Users/bre/file organizer"
./one/bin/pip install -r requirements.txt
```

### "Ollama not responding"
```bash
# In another terminal
ollama serve

# Check models
ollama list

# Pull required model
ollama pull llama3.2:3b
```

### "API not accessible"
```bash
# Check if running
curl http://localhost:8765/api/health

# Start it
./one/bin/python automation_api.py
```

### "Export failed"
```bash
# Check permissions
ls -la ~/.fileorganizer/exports/

# Create directory if needed
mkdir -p ~/.fileorganizer/exports
```

---

## 🎓 Learning Resources

- `QUICK_START.md` - Get started fast
- `WHATS_NEW.md` - All new features
- `ADVANCED_FEATURES.md` - Complete guide
- `EXPORT_AND_OPENAI_GUIDE.md` - Export & AI details
- `README.md` - Full manual
- `FINAL_SUMMARY.md` - Complete overview

---

## ✅ Daily Usage

```bash
# Morning routine
cd "/Users/bre/file organizer"

# Start the app
./one/bin/python file_organizer_app.py

# Or start API for automation
./one/bin/python automation_api.py &

# Weekly: Export for backup
./one/bin/python export_manager.py
```

---

*Keep this file handy for quick reference!*

