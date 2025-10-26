# 🚀 Advanced Features - Complete Integration Guide

## Overview

Your File Organizer now has **enterprise-grade capabilities**:
- ✅ **Hybrid Database**: Vector + Graph + Relational
- ✅ **Cloud Storage**: Auto-detection of 8+ cloud services
- ✅ **Automation**: REST API for n8n, Make.com, webhooks
- ✅ **Hazel Integration**: AppleScript bridges
- ✅ **Semantic Search**: Vector embeddings
- ✅ **Graph Queries**: Relationship mapping

---

## 🗄️ Database Architecture

### **Hybrid Storage System**

Your database is now **3-in-1**:

#### 1. **Relational (SQLite)**
- Traditional file metadata
- Fast indexed queries
- ACID transactions
- Location: `~/.fileorganizer/files.db`

#### 2. **Vector Store** 
- Semantic embeddings for similarity search
- Find files by meaning, not just keywords
- Location: `~/.fileorganizer/vectors.pkl`
- **Features**:
  - Fast similarity search
  - Find related files
  - No external dependencies (simple mode)
  - Optional Ollama embeddings for better quality

#### 3. **Graph Database**
- File relationships and connections
- Project/tag network mapping
- Path finding between files
- Built on SQLite with graph schema

### **What This Means**

```python
# Traditional search (keyword matching)
"find invoice" → searches for word "invoice"

# Vector search (semantic meaning)
"find invoice" → finds invoices, bills, receipts, payments

# Graph search (relationships)
"find everything related to Project X" → files, tags, related projects
```

---

## ☁️ Cloud Storage Integration

### **Auto-Detected Services** (8+ services)

#### ✅ Currently Supported:
- 📦 **Dropbox** - Full sync folder
- ☁️ **iCloud Drive** - Including Desktop/Documents sync
- 🔵 **Google Drive** - Both personal and business
- 🔷 **OneDrive** - Personal and business accounts
- 📫 **Box**
- 🔴 **MEGA**
- 🔄 **Sync.com**
- 💾 **pCloud**

### **How It Works**

1. **Automatic Detection**
   - Scans common locations
   - Reads config files
   - Detects active sync folders

2. **Setup Wizard Integration**
   - Cloud folders shown during setup
   - Pre-selected for monitoring
   - Custom paths still supported

3. **Path Intelligence**
   - Knows which files are in cloud storage
   - Can identify service for any file
   - Tracks sync status

### **Usage Example**

```python
from cloud_storage import CloudStorageDetector

detector = CloudStorageDetector()
print(detector.detected_services)
# {
#   'Dropbox': {'path': '/Users/bre/Dropbox', 'icon': '📦'},
#   'iCloud Drive': {'path': '/Users/bre/Library/Mobile Documents/...'},
#   'Google Drive': {'path': '/Users/bre/Library/CloudStorage/GoogleDrive-...'}
# }

# Check if file is in cloud storage
is_cloud = detector.is_cloud_path('/Users/bre/Dropbox/Work/file.pdf')
# True

service = detector.get_service_for_path('/Users/bre/Dropbox/Work/file.pdf')
# 'Dropbox'
```

### **Test Your Cloud Detection**

```bash
cd "/Users/bre/file organizer"
./one/bin/python cloud_storage.py
```

---

## 🔌 Automation API

### **REST API for Integrations**

Full REST API running on `localhost:8765` for automation tools:

#### **Supported Platforms:**
- ✅ **n8n** - Workflow automation
- ✅ **Make.com** (Integromat) - Visual automation
- ✅ **Zapier** - App connections
- ✅ **Custom webhooks** - Any HTTP client

### **API Endpoints**

#### **GET Endpoints**
```http
GET /api/health           # Health check
GET /api/stats            # File statistics
GET /api/search?q=query   # Search files
GET /api/folders          # List monitored folders
```

#### **POST Endpoints**
```http
POST /api/organize        # Organize files
POST /api/tag             # AI tag a file
POST /api/chat            # Chat with AI
POST /api/index           # Index a folder
```

### **Usage Examples**

#### **n8n Workflow**
```javascript
// In n8n HTTP Request node
{
  "method": "POST",
  "url": "http://localhost:8765/api/search",
  "body": {
    "q": "invoices from last month"
  }
}
```

#### **Make.com Scenario**
```
1. Watch Folder (Dropbox) →
2. HTTP Request to File Organizer API →
3. Organize file automatically →
4. Send notification (Slack/Email)
```

#### **curl Example**
```bash
# Search files
curl http://localhost:8765/api/search?q=python

# Organize Downloads
curl -X POST http://localhost:8765/api/organize \
  -H "Content-Type: application/json" \
  -d '{"folder": "/Users/bre/Downloads", "type": "by_type"}'

# Tag a file with AI
curl -X POST http://localhost:8765/api/tag \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/bre/Documents/file.pdf"}'

# Chat with AI
curl -X POST http://localhost:8765/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find my recent invoices"}'
```

### **Start the API Server**

The API can run standalone or integrated with the main app:

```python
from automation_api import AutomationAPIServer
from file_indexer import FileDatabase

db = FileDatabase()
api = AutomationAPIServer(port=8765, file_db=db)
api.start()

# Server runs in background thread
# Access at: http://localhost:8765/api
```

---

## 🎯 Hazel Integration

### **What is Hazel?**

Hazel is a macOS automation tool that watches folders and runs rules automatically. Your File Organizer now integrates with it via AppleScript bridges.

### **Features**

1. **AppleScript Bridges** - Hazel → File Organizer
2. **Rule Export** - Generate Hazel-compatible rules
3. **Bidirectional** - Hazel triggers File Organizer AI

### **Available Scripts**

#### **1. Auto-Organize by Type**
```applescript
-- Automatically sorts files into type-based folders
-- PDF → Documents/, Images → Images/, etc.
```

#### **2. AI Tag Files**
```applescript
-- Tags new files with AI
-- Extracts project, summary, tags
```

#### **3. Smart Move**
```applescript
-- AI decides where to move file
-- Based on content, project, patterns
```

### **Setup Instructions**

1. **Generate Hazel Scripts**
   ```bash
   cd "/Users/bre/file organizer"
   ./one/bin/python hazel_integration.py
   ```

2. **In Hazel**:
   - Open Hazel preferences
   - Add folder to monitor (e.g., Downloads)
   - Create new rule
   - Add condition: "Kind is Document"
   - Add action: "Run AppleScript"
   - Copy script from `~/.fileorganizer/hazel_scripts/organize_by_type.scpt`

3. **Example Hazel Rule**:
   ```
   Name: Auto-organize Downloads
   Folder: ~/Downloads
   
   Conditions:
   - If all of the following are true:
     - Kind is any
   
   Actions:
   - Run AppleScript (embedded):
     [Paste organize_by_type.scpt content]
   ```

### **How It Works**

```
File appears in Downloads
      ↓
Hazel detects it
      ↓
Runs AppleScript
      ↓
Calls File Organizer Python bridge
      ↓
AI analyzes & organizes file
      ↓
Returns result to Hazel
```

### **Test the Bridge**

```bash
./one/bin/python hazel_bridge.py organize "/Users/bre/Downloads"
./one/bin/python hazel_bridge.py tag "/Users/bre/Documents/test.pdf"
```

---

## 🔍 Vector Search (Semantic Similarity)

### **What Is It?**

Traditional search finds exact keyword matches. Vector search understands **meaning**.

### **How It Works**

1. Files are converted to **embeddings** (mathematical vectors)
2. Similar meanings = similar vectors
3. Search by concept, not keywords

### **Examples**

```python
# Traditional keyword search
"python programming" → finds files with words "python" OR "programming"

# Vector semantic search
"python programming" → finds:
  - python_tutorial.pdf (direct match)
  - pandas_guide.pdf (related: data science)
  - coding_basics.md (related: programming)
  - NOT: snake_species.pdf (different meaning of "python")
```

### **Two Modes**

#### **Simple Mode** (Default)
- Fast, no dependencies
- Good for most use cases
- Uses word frequency + n-grams

#### **Ollama Mode** (Advanced)
- High-quality embeddings
- Better semantic understanding
- Requires Ollama with embedding model

```bash
# Install embedding model for better results
ollama pull nomic-embed-text
```

### **Usage**

```python
from vector_store import VectorSearchIntegration
from file_indexer import FileDatabase

db = FileDatabase()
vector_search = VectorSearchIntegration(db)

# Index all files (one-time)
vector_search.index_all_files()

# Semantic search
results = vector_search.semantic_search("project documentation", top_k=5)
for r in results:
    print(f"{r['filename']} - {r['similarity']:.2f}")
```

### **Find Related Files**

```python
# Find files similar to a specific file
related = vector_search.find_related_files(
    "/Users/bre/Documents/proposal.pdf",
    top_k=5
)
# Returns files with similar content/meaning
```

---

## 🕸️ Graph Database (Relationships)

### **What Is It?**

Files don't exist in isolation. The graph database maps:
- Which files belong to which projects
- Which files share tags
- Which files are accessed together
- Paths between related files

### **Graph Structure**

#### **Nodes** (Things):
- Files
- Projects
- Tags
- People (future)

#### **Edges** (Relationships):
- `belongs_to` - File → Project
- `tagged_with` - File → Tag
- `related_to` - File → File
- `accessed_with` - File → File

### **Powerful Queries**

#### **1. Find All Project Files**
```python
from graph_store import FileGraphIntegration
from file_indexer import FileDatabase

db = FileDatabase()
graph = FileGraphIntegration(db)

# Build graph once
graph.build_graph_from_database()

# Find everything related to a project
files = graph.find_all_project_files("ClientX")
# Returns ALL files connected to ClientX project
```

#### **2. Find by Tag**
```python
files = graph.find_files_by_tag("invoice")
# All files tagged with "invoice"
```

#### **3. Get File's Neighborhood**
```python
subgraph = graph.graph.get_subgraph('file', '123', max_depth=2)
# Returns all files within 2 connections
```

#### **4. Find Path Between Files**
```python
path = graph.graph.find_path(
    'file', '123',
    'file', '456',
    max_depth=5
)
# How are these files connected?
```

### **Graph Statistics**

```python
stats = graph.graph.get_stats()
# {
#   'total_nodes': 265,
#   'total_edges': 55,
#   'nodes_by_type': {'file': 220, 'project': 1, 'tag': 44},
#   'edges_by_type': {'belongs_to': 1, 'tagged_with': 54}
# }
```

---

## 🎛️ Integration Examples

### **n8n Workflow: Auto-organize New Files**

```
Trigger: Dropbox - New File
   ↓
HTTP Request: POST /api/tag (analyze file)
   ↓
HTTP Request: POST /api/organize (move to project folder)
   ↓
Slack: Send notification
```

### **Make.com Scenario: Invoice Processing**

```
Watch Folder: ~/Downloads
   ↓
Filter: If filename contains "invoice"
   ↓
HTTP: Tag with AI
   ↓
HTTP: Move to Accounting folder
   ↓
Google Sheets: Add to invoice log
```

### **Hazel Rule: Smart Desktop Cleanup**

```
Monitor: ~/Desktop
Conditions: File age > 7 days
Actions: Run AppleScript (smart_move.scpt)
Result: AI moves file to appropriate folder
```

---

## 📊 Performance & Stats

### **Current Capabilities** (Your System)

```
Database:
• 220 files indexed
• Full-text search ready
• 10 files with vector embeddings
• 265 graph nodes, 55 edges

Cloud Storage:
• 3 services detected
• Dropbox, iCloud, Google Drive
• Ready to monitor any folder

API:
• 8 REST endpoints
• JSON responses
• CORS enabled
• Ready for automation
```

---

## 🚀 Quick Start Guide

### **1. Enable Vector Search**

```bash
cd "/Users/bre/file organizer"
./one/bin/python -c "
from vector_store import VectorSearchIntegration
from file_indexer import FileDatabase

db = FileDatabase()
vs = VectorSearchIntegration(db)
print('Indexing files with vectors...')
indexed = vs.index_all_files()
print(f'✅ Indexed {indexed} files')
db.close()
"
```

### **2. Build Graph Database**

```bash
./one/bin/python -c "
from graph_store import FileGraphIntegration
from file_indexer import FileDatabase

db = FileDatabase()
graph = FileGraphIntegration(db)
stats = graph.build_graph_from_database()
print(f'✅ Graph: {stats[\"total_nodes\"]} nodes, {stats[\"total_edges\"]} edges')
db.close()
"
```

### **3. Start API Server**

```bash
./one/bin/python automation_api.py
# Server runs on http://localhost:8765
# Test: curl http://localhost:8765/api/health
```

### **4. Setup Hazel Integration**

```bash
./one/bin/python hazel_integration.py
# Scripts exported to ~/.fileorganizer/hazel_scripts/
```

---

## 📝 Updated Requirements

All dependencies are in `requirements.txt`:

```
# New additions:
numpy>=1.24.0          # For vector operations
# (No additional deps needed! Everything else is built-in)
```

---

## 🎓 Advanced Use Cases

### **Use Case 1: Semantic File Discovery**

```python
# User: "I need something about machine learning from last month"
# Traditional search: looks for exact words
# Vector search: understands concepts

results = vector_search.semantic_search(
    "machine learning neural networks",
    top_k=10
)
# Finds: ML papers, AI tutorials, related research
```

### **Use Case 2: Project Intelligence**

```python
# User: "Show me everything for Project Phoenix"

# Graph query gets:
- All files tagged with Phoenix
- Related files (accessed together)
- Files from team members
- Connected projects
```

### **Use Case 3: Automated Workflows**

```
New invoice arrives → Hazel detects it
    ↓
Calls File Organizer API
    ↓
AI tags with: client name, date, amount
    ↓
Moves to: ~/Documents/Accounting/2025/ClientName/
    ↓
n8n workflow triggers:
    • Updates spreadsheet
    • Sends Slack notification
    • Archives to cloud
```

---

## ✅ Summary

You now have:

| Feature | Status | Integration |
|---------|--------|-------------|
| **Vector Search** | ✅ Working | Built-in |
| **Graph Database** | ✅ Working | Built-in |
| **Cloud Detection** | ✅ Working | 8 services |
| **REST API** | ✅ Ready | n8n, Make, Zapier |
| **Hazel Bridge** | ✅ Ready | AppleScript |
| **Semantic Search** | ✅ Working | 2 modes |
| **Relationship Queries** | ✅ Working | Graph |

---

**Your File Organizer is now enterprise-grade!** 🚀

Test everything:
```bash
./one/bin/python vector_store.py   # Test vectors
./one/bin/python graph_store.py    # Test graph
./one/bin/python cloud_storage.py  # Test cloud detection
./one/bin/python automation_api.py # Test API
./one/bin/python hazel_integration.py  # Setup Hazel
```

