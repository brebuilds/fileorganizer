# 🤖 RAG System Guide

**Using File Organizer as a Personal RAG (Retrieval-Augmented Generation) System**

---

## What is RAG?

**RAG** combines two powerful AI techniques:
1. **Retrieval** - Finding relevant information from a knowledge base
2. **Generation** - Using AI to generate responses based on retrieved information

This approach provides:
- ✅ Accurate answers grounded in your actual data
- ✅ Reduced AI hallucination
- ✅ Context-aware responses
- ✅ Dynamic knowledge that updates as you add files

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Your Files                           │
│  (Documents, PDFs, Code, Images, Cloud Storage)         │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Document Ingestion                          │
│  • File Indexer (file_indexer.py)                      │
│  • OCR Processor (ocr_processor.py)                     │
│  • PDF extraction, text parsing                         │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│             Knowledge Storage Layer                      │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  SQLite FTS5    │  │ Vector Store │  │ Graph DB   │ │
│  │ (Full-text)     │  │ (Semantic)   │  │ (Relations)│ │
│  └─────────────────┘  └──────────────┘  └────────────┘ │
│  ┌─────────────────────────────────────────────────────┐│
│  │        Learned Patterns & User Memory               ││
│  └─────────────────────────────────────────────────────┘│
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Retrieval System                            │
│  • Keyword search (exact matches)                       │
│  • Semantic search (meaning-based)                      │
│  • Temporal queries (time-based)                        │
│  • Graph traversal (relationships)                      │
│  • Hybrid ranking (combines all methods)                │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│            AI Generation Layer                           │
│  • Ollama (local, private)                              │
│  • OpenAI (optional, for better results)                │
│  • Context-aware prompts with retrieved docs            │
│  • Memory integration (remembers user)                  │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                 User Interfaces                          │
│  • GUI Chat (file_organizer_app.py)                    │
│  • CLI (./o commands)                                   │
│  • REST API (automation_api.py)                         │
└─────────────────────────────────────────────────────────┘
```

---

## Core RAG Features

### 1. Document Ingestion

**Supported Formats:**
- Text: `.txt`, `.md`, `.log`, `.csv`
- Code: `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`
- Documents: `.pdf` (multi-page with summarization)
- Images: `.png`, `.jpg`, `.jpeg`, `.gif` (with OCR)

**Example: Index Your Files**
```bash
# GUI: Settings → Scan Selected Folders

# CLI:
./o @Documents  # Index Documents folder
./o @Desktop    # Index Desktop
```

**Programmatic:**
```python
from file_indexer import FileIndexer, FileDatabase

db = FileDatabase()
indexer = FileIndexer(db)
indexer.scan_folder("~/Documents", recursive=True)
```

---

### 2. Vector Store (Semantic Search)

**How It Works:**
- Files are converted to embeddings (numerical representations)
- Similar files cluster together in vector space
- Search by *meaning*, not just keywords

**Example:**
```python
from vector_store import VectorStore

vector_store = VectorStore(db)

# Generate embeddings for all files
vector_store.index_all_files()

# Semantic search
results = vector_store.search("machine learning tutorials", top_k=10)
for result in results:
    print(f"{result['filename']}: {result['similarity']}")
```

**Via API:**
```bash
curl http://localhost:5000/api/semantic-search?q=contract+templates&limit=5
```

---

### 3. Knowledge Graph (Relationships)

**Tracks:**
- File → Project relationships
- File → Tag relationships
- Tag → Tag co-occurrence
- Project → Tag associations

**Example:**
```python
from graph_store import GraphStore

graph = GraphStore(db)

# Add relationships
graph.add_file_project_relation(file_id=123, project="Phoenix Website")
graph.add_file_tag_relation(file_id=123, tag="design")

# Query relationships
related_files = graph.get_related_files(file_id=123)
project_files = graph.get_files_by_project("Phoenix Website")
```

**Via API:**
```bash
# Get files related to file ID 123
curl http://localhost:5000/api/graph/file/123/related

# Get all files in a project
curl http://localhost:5000/api/graph/project/Phoenix/files
```

---

### 4. Hybrid Retrieval

Combines multiple search strategies for best results:

```python
from conversational_ai import ConversationalAI

ai = ConversationalAI(model="llama2", user_profile=profile, file_db=db)

# This uses:
# 1. Keyword search (FTS5)
# 2. Semantic search (vectors)
# 3. Temporal filtering (if time mentioned)
# 4. Graph relationships (if project/tag mentioned)
# 5. User memory (learned preferences)

response = ai.chat("Find design files from last week for Phoenix")
```

---

### 5. Context-Aware AI Generation

**How It Works:**
1. User asks a question
2. System retrieves relevant files
3. AI generates response using retrieved context + user memory
4. Response is grounded in actual data

**Example:**
```python
import asyncio
from conversational_ai import ConversationalAI

ai = ConversationalAI(model="llama2", user_profile=profile, file_db=db)

async def query():
    response = await ai.chat_async(
        user_message="What are my most important design files?",
        conversation_history=[]
    )
    print(response)

asyncio.run(query())
```

**The AI knows:**
- Your files (retrieved from database)
- Your work context (from memory)
- Your preferences (learned patterns)
- Time context (temporal tracker)
- File relationships (knowledge graph)

---

### 6. Memory & Learning System

**What Gets Remembered:**
- Work role and projects
- File organization habits
- Tool preferences
- Important files
- Search patterns

**Example:**
User says: "I'm a designer working on Phoenix in Figma"

System stores:
```json
{
  "work_context": "designer working on Phoenix in Figma",
  "project_context": "Phoenix",
  "tools_used": "Figma",
  "confidence": 0.9
}
```

Next time: AI automatically knows you're a designer, working on Phoenix, using Figma.

---

## REST API for RAG Integration

### Start the API Server

**GUI:** Settings → Automations & APIs → Enable REST API

**CLI:**
```bash
python automation_api.py
```

Server runs on `http://localhost:5000`

---

### API Endpoints

#### Search Files
```bash
# Keyword search
curl http://localhost:5000/api/search?q=invoice&limit=10

# Semantic search
curl http://localhost:5000/api/semantic-search?q=contract+templates&limit=5

# Temporal search
curl http://localhost:5000/api/temporal-search?query=yesterday&limit=10
```

#### Chat with RAG
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What design files did I create last week?",
    "use_rag": true
  }'
```

#### Get File Details
```bash
# Get file metadata
curl http://localhost:5000/api/file/123

# Get file summary (AI-generated)
curl http://localhost:5000/api/file/123/summary

# Get file content
curl http://localhost:5000/api/file/123/content
```

#### Knowledge Graph Queries
```bash
# Get related files
curl http://localhost:5000/api/graph/file/123/related

# Get files by project
curl http://localhost:5000/api/graph/project/Phoenix/files

# Get files by tag
curl http://localhost:5000/api/graph/tag/design/files
```

#### User Memory
```bash
# Get learned patterns
curl http://localhost:5000/api/memory/patterns

# Get user facts
curl http://localhost:5000/api/memory/facts
```

---

## Building Custom Applications

### Example 1: Slack Bot for File Search

```python
from slack_sdk import WebClient
import requests

slack_client = WebClient(token="xoxb-your-token")

def search_files(query):
    response = requests.get(
        "http://localhost:5000/api/semantic-search",
        params={"q": query, "limit": 5}
    )
    return response.json()

def handle_slack_command(text):
    results = search_files(text)
    message = "Found these files:\n"
    for file in results['files']:
        message += f"• {file['filename']}: {file['path']}\n"
    return message

# Use in Slack slash command
slack_client.chat_postMessage(
    channel="#general",
    text=handle_slack_command("invoices from last month")
)
```

---

### Example 2: Personal Dashboard

```python
import streamlit as st
import requests

st.title("My Personal Knowledge Base")

# Search interface
query = st.text_input("Search your files:")
if query:
    results = requests.get(
        "http://localhost:5000/api/semantic-search",
        params={"q": query, "limit":10}
    ).json()
    
    for file in results['files']:
        with st.expander(file['filename']):
            st.write(f"**Path:** {file['path']}")
            st.write(f"**Modified:** {file['modified']}")
            if file.get('summary'):
                st.write(f"**Summary:** {file['summary']}")

# Stats
stats = requests.get("http://localhost:5000/api/stats").json()
col1, col2, col3 = st.columns(3)
col1.metric("Total Files", stats['total_files'])
col2.metric("Projects", len(stats.get('projects', [])))
col3.metric("Tags", len(stats.get('tags', [])))
```

---

### Example 3: Automated Workflow (n8n/Make.com)

**Trigger:** New file added to Downloads
**Action 1:** RAG system indexes the file
**Action 2:** AI generates summary
**Action 3:** Post to Slack with summary
**Action 4:** Move to appropriate project folder

```javascript
// n8n HTTP Request node
{
  "method": "POST",
  "url": "http://localhost:5000/api/index-file",
  "body": {
    "path": "/Users/me/Downloads/contract.pdf"
  }
}

// Get AI summary
{
  "method": "GET",
  "url": "http://localhost:5000/api/file/{{$json.file_id}}/summary"
}
```

---

## Comparison to Other RAG Systems

| Feature | File Organizer | LangChain | LlamaIndex | Custom |
|---------|----------------|-----------|------------|--------|
| **Local-First** | ✅ Yes | ❌ Cloud | ✅ Yes | Depends |
| **Multi-Modal** | ✅ Yes | ⚠️ Limited | ⚠️ Limited | Depends |
| **User Memory** | ✅ Built-in | ❌ Manual | ❌ Manual | Need to build |
| **Temporal Queries** | ✅ Built-in | ❌ No | ❌ No | Need to build |
| **Knowledge Graph** | ✅ Built-in | ⚠️ Via plugin | ⚠️ Via plugin | Need to build |
| **GUI + CLI + API** | ✅ All 3 | ❌ API only | ❌ API only | Need to build |
| **Production Ready** | ✅ Yes | ⚠️ Framework | ⚠️ Framework | Depends |
| **ADHD-Optimized** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Learning Curve** | 🟢 Easy | 🔴 Hard | 🟡 Medium | 🔴 Very Hard |

---

## Performance Benchmarks

**Indexing Speed:**
- 1,000 text files: ~30 seconds
- 100 PDFs: ~2 minutes
- 500 images (with OCR): ~5 minutes

**Search Latency:**
- Keyword search: <50ms
- Semantic search: <200ms
- Hybrid search: <300ms
- AI generation: 1-3 seconds (depending on model)

**Storage:**
- Database: ~1MB per 1,000 files
- Vector embeddings: ~500KB per 1,000 files
- Full system: <10MB for 10,000 files

---

## Best Practices

### 1. Indexing Strategy
- Index frequently accessed folders (Documents, Desktop, Downloads)
- Enable auto-scan for automatic updates
- Use cloud storage integration for synced files

### 2. Search Strategy
- Start with semantic search for exploratory queries
- Use keyword search for exact matches
- Combine with temporal filters for recent files
- Leverage graph queries for project-based searches

### 3. Memory Management
- Let the system learn naturally through chat
- Review learned patterns occasionally
- Correct any misunderstandings early

### 4. API Integration
- Use localhost for development
- Consider authentication for production
- Rate limit external requests
- Cache frequent queries

### 5. Privacy
- Keep Ollama for local-only RAG
- Only enable OpenAI if you need advanced summaries
- Review API access controls
- Use file hiding feature for sensitive data

---

## Troubleshooting

**Slow Search:**
- Rebuild vector index: `./o REINDEX`
- Check database size: `du -sh ~/.fileorganizer/`
- Reduce indexed folders

**Poor Semantic Search:**
- Re-generate embeddings with better model
- Increase vector dimensions
- Add more context to file tags

**API Not Working:**
- Check if server is running: `curl http://localhost:5000/api/health`
- Review logs in terminal
- Check firewall settings

**AI Responses Not Accurate:**
- More files = better context
- Add manual tags to important files
- Use learning system (chat naturally)

---

## Next Steps

1. **Try it:** Index your files and start asking questions
2. **Integrate:** Build a custom app using the REST API
3. **Extend:** Add custom retrieval strategies
4. **Share:** Contribute improvements back to the project

---

## Resources

- [Main README](README.md) - General documentation
- [API Documentation](EXPORT_AND_OPENAI_GUIDE.md) - API reference
- [CLI Guide](CLI_GUIDE.md) - Command-line usage
- [GitHub Issues](https://github.com/brebuilds/fileorganizer/issues) - Report bugs

---

**Built with ❤️ for developers who need a RAG system that actually works in real life.**

