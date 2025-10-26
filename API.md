# 🔌 REST API Documentation

Complete API reference for integrating with the File Organizer RAG system.

---

## Getting Started

### Enable the API

**GUI:** Settings → Automations & APIs → ☑ Enable REST API

**CLI:**
```bash
python automation_api.py
```

### Base URL

```
http://localhost:5000
```

### Authentication

Currently: **None** (localhost only)

For production: Implement token authentication (see Security section)

---

## Core Endpoints

### Health Check

**GET** `/api/health`

Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "version": "4.0.0",
  "timestamp": "2025-10-26T14:23:45"
}
```

---

### Statistics

**GET** `/api/stats`

Get system statistics and file counts.

**Response:**
```json
{
  "total_files": 1247,
  "by_extension": {
    ".pdf": 234,
    ".jpg": 456,
    ".txt": 123
  },
  "by_folder": {
    "Downloads": 567,
    "Documents": 345
  },
  "by_project": {
    "Phoenix": 89,
    "Acme Corp": 45
  },
  "indexed_notes": 247,
  "total_tags": 456,
  "last_indexed": "2025-10-26T14:00:00"
}
```

---

## Search Endpoints

### Basic Search

**GET** `/api/search`

Full-text keyword search across all indexed files.

**Parameters:**
- `q` (required): Search query
- `limit` (optional): Max results (default: 20)
- `offset` (optional): Pagination offset (default: 0)
- `extension` (optional): Filter by file type (e.g., ".pdf")
- `project` (optional): Filter by project name

**Example:**
```bash
curl "http://localhost:5000/api/search?q=invoice&limit=10"
```

**Response:**
```json
{
  "query": "invoice",
  "total": 15,
  "limit": 10,
  "offset": 0,
  "results": [
    {
      "id": 123,
      "filename": "invoice_2024.pdf",
      "path": "/Users/me/Documents/invoice_2024.pdf",
      "size": 245678,
      "modified": "2024-10-15T10:30:00",
      "project": "Phoenix",
      "tags": ["finance", "client"],
      "summary": "Invoice for Phoenix project services",
      "relevance_score": 0.95
    }
  ]
}
```

---

### Semantic Search

**GET** `/api/semantic-search`

AI-powered semantic search using vector embeddings.

**Parameters:**
- `q` (required): Natural language query
- `limit` (optional): Max results (default: 10)

**Example:**
```bash
curl "http://localhost:5000/api/semantic-search?q=design+mockups+for+web+project"
```

**Response:**
```json
{
  "query": "design mockups for web project",
  "results": [
    {
      "id": 456,
      "filename": "homepage_mockup.fig",
      "path": "/Users/me/Design/homepage_mockup.fig",
      "similarity_score": 0.87,
      "summary": "Homepage design mockup for Phoenix website"
    }
  ]
}
```

---

### Temporal Search

**GET** `/api/temporal-search`

Search files by time-based queries.

**Parameters:**
- `query` (required): Time expression ("yesterday", "last week", etc.)
- `limit` (optional): Max results (default: 20)

**Example:**
```bash
curl "http://localhost:5000/api/temporal-search?query=yesterday&limit=10"
```

**Response:**
```json
{
  "query": "yesterday",
  "date_range": {
    "start": "2025-10-25T00:00:00",
    "end": "2025-10-25T23:59:59"
  },
  "results": [
    {
      "id": 789,
      "filename": "meeting_notes.txt",
      "modified": "2025-10-25T14:30:00"
    }
  ]
}
```

---

## File Operations

### Get File Details

**GET** `/api/file/{file_id}`

Get complete metadata for a specific file.

**Example:**
```bash
curl "http://localhost:5000/api/file/123"
```

**Response:**
```json
{
  "id": 123,
  "filename": "invoice_2024.pdf",
  "path": "/Users/me/Documents/invoice_2024.pdf",
  "extension": ".pdf",
  "size": 245678,
  "created": "2024-10-10T09:00:00",
  "modified": "2024-10-15T10:30:00",
  "last_accessed": "2024-10-20T15:00:00",
  "access_count": 5,
  "file_hash": "a1b2c3d4e5f6...",
  "mime_type": "application/pdf",
  "project": "Phoenix",
  "tags": ["finance", "client"],
  "ai_summary": "Invoice for Phoenix project services",
  "source": "filesystem",
  "is_duplicate": false
}
```

---

### Get File Content

**GET** `/api/file/{file_id}/content`

Get the extracted text content of a file.

**Response:**
```json
{
  "id": 123,
  "filename": "invoice_2024.pdf",
  "content": "INVOICE\\nDate: October 15, 2024\\nAmount: $5,000..."
}
```

---

### Get File Summary

**GET** `/api/file/{file_id}/summary`

Get AI-generated summary of file content.

**Response:**
```json
{
  "id": 123,
  "filename": "invoice_2024.pdf",
  "summary": "Invoice for Phoenix project services totaling $5,000 for October 2024",
  "key_points": [
    "Invoice date: October 15, 2024",
    "Client: Phoenix Corp",
    "Amount: $5,000",
    "Due date: November 15, 2024"
  ]
}
```

---

## Knowledge Graph

### Get Related Files

**GET** `/api/graph/file/{file_id}/related`

Find files related to a specific file through projects, tags, or co-occurrence.

**Example:**
```bash
curl "http://localhost:5000/api/graph/file/123/related"
```

**Response:**
```json
{
  "file_id": 123,
  "filename": "invoice_2024.pdf",
  "related_files": [
    {
      "id": 124,
      "filename": "contract_phoenix.pdf",
      "relation_type": "same_project",
      "relation_strength": 0.9
    },
    {
      "id": 125,
      "filename": "proposal_phoenix.docx",
      "relation_type": "same_tags",
      "relation_strength": 0.75
    }
  ]
}
```

---

### Get Files by Project

**GET** `/api/graph/project/{project_name}/files`

Get all files associated with a project.

**Example:**
```bash
curl "http://localhost:5000/api/graph/project/Phoenix/files"
```

**Response:**
```json
{
  "project": "Phoenix",
  "file_count": 45,
  "files": [
    {
      "id": 123,
      "filename": "invoice_2024.pdf",
      "path": "/Users/me/Documents/invoice_2024.pdf"
    }
  ]
}
```

---

### Get Files by Tag

**GET** `/api/graph/tag/{tag_name}/files`

Get all files with a specific tag.

**Example:**
```bash
curl "http://localhost:5000/api/graph/tag/design/files"
```

---

## AI & RAG

### Chat with RAG

**POST** `/api/chat`

Natural language chat with full RAG context.

**Request Body:**
```json
{
  "message": "Find design files from last week for Phoenix project",
  "use_rag": true,
  "conversation_history": []
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find design files from last week",
    "use_rag": true
  }'
```

**Response:**
```json
{
  "response": "I found 5 design files from last week for the Phoenix project. Here they are:\n\n1. homepage_mockup.fig (Oct 20)\n2. logo_variations.psd (Oct 21)\n...",
  "retrieved_files": [
    {
      "id": 456,
      "filename": "homepage_mockup.fig",
      "relevance": 0.92
    }
  ],
  "intent": "SEARCH",
  "confidence": 0.95
}
```

---

### Generate Summary

**POST** `/api/summarize`

Generate AI summary for a file or text.

**Request Body:**
```json
{
  "file_id": 123
}
```
or
```json
{
  "text": "Long text to summarize..."
}
```

**Response:**
```json
{
  "summary": "Brief summary of the content",
  "key_points": ["point 1", "point 2"]
}
```

---

## Indexing

### Index File

**POST** `/api/index/file`

Add a single file to the index.

**Request Body:**
```json
{
  "path": "/Users/me/Documents/newfile.pdf"
}
```

**Response:**
```json
{
  "success": true,
  "file_id": 789,
  "filename": "newfile.pdf",
  "indexed_at": "2025-10-26T14:30:00"
}
```

---

### Index Folder

**POST** `/api/index/folder`

Scan and index all files in a folder.

**Request Body:**
```json
{
  "path": "/Users/me/Documents",
  "recursive": true
}
```

**Response:**
```json
{
  "success": true,
  "indexed": 45,
  "skipped": 12,
  "total": 57
}
```

---

### Index Apple Notes

**POST** `/api/index/notes`

Index all Apple Notes.

**Response:**
```json
{
  "success": true,
  "indexed": 247,
  "skipped": 5,
  "total": 252
}
```

---

## User Memory

### Get Learned Patterns

**GET** `/api/memory/patterns`

Get AI-learned patterns about the user.

**Response:**
```json
{
  "work_context": ["designer", "freelancer"],
  "projects": ["Phoenix", "Acme Corp"],
  "tools": ["Figma", "VSCode"],
  "file_habits": ["organizes by project", "uses tags"],
  "preferences": ["prefers visual previews"]
}
```

---

### Get User Facts

**GET** `/api/memory/facts`

Get remembered facts about the user from conversations.

**Response:**
```json
{
  "facts": [
    {
      "category": "work_context",
      "value": "I'm a designer working on Phoenix in Figma",
      "confidence": 0.9,
      "last_updated": "2025-10-20T10:00:00"
    }
  ]
}
```

---

## Webhooks (Future)

### Register Webhook

**POST** `/api/webhooks`

Register a webhook for file events.

**Request Body:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["file.indexed", "file.modified", "file.deleted"]
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": true,
  "message": "Description of the error",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-26T14:30:00"
}
```

**Common Error Codes:**
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (file/resource doesn't exist)
- `500` - Internal Server Error

---

## Rate Limiting

**Current:** No rate limiting (localhost only)

**Production:** Recommended 100 requests/minute per IP

---

## Security

### Current State
- **Localhost only** (0.0.0.0 binding disabled)
- **No authentication** required
- **CORS disabled** by default

### Production Recommendations

1. **Enable Token Authentication:**
```python
headers = {"Authorization": "Bearer YOUR_TOKEN"}
```

2. **Use HTTPS:**
```
https://your-domain.com/api/...
```

3. **Whitelist IPs:**
```python
ALLOWED_IPS = ['192.168.1.0/24']
```

4. **Enable CORS for specific domains:**
```python
CORS(app, origins=['https://your-frontend.com'])
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Search files
response = requests.get(f"{BASE_URL}/search", params={"q": "invoice"})
files = response.json()["results"]

# Chat with RAG
response = requests.post(f"{BASE_URL}/chat", json={
    "message": "Find design files from last week",
    "use_rag": True
})
answer = response.json()["response"]

# Index file
response = requests.post(f"{BASE_URL}/index/file", json={
    "path": "/path/to/file.pdf"
})
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:5000/api';

// Search files
fetch(`${BASE_URL}/search?q=invoice`)
  .then(res => res.json())
  .then(data => console.log(data.results));

// Chat with RAG
fetch(`${BASE_URL}/chat`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'Find design files',
    use_rag: true
  })
})
  .then(res => res.json())
  .then(data => console.log(data.response));
```

### curl

```bash
# Search
curl "http://localhost:5000/api/search?q=invoice&limit=10"

# Chat
curl -X POST "http://localhost:5000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Find PDFs", "use_rag": true}'

# Get file
curl "http://localhost:5000/api/file/123"

# Index folder
curl -X POST "http://localhost:5000/api/index/folder" \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/me/Documents", "recursive": true}'
```

---

## Integration Examples

### n8n Workflow

```
1. Webhook Trigger (new file uploaded)
   ↓
2. HTTP Request: POST /api/index/file
   ↓
3. HTTP Request: GET /api/file/{id}/summary
   ↓
4. Slack: Post message with summary
   ↓
5. HTTP Request: POST /api/chat (classify file)
   ↓
6. Move file to correct folder
```

### Zapier

```
Trigger: New file in Google Drive
Action 1: HTTP POST to /api/index/file
Action 2: HTTP POST to /api/chat (get category)
Action 3: Move file based on AI response
```

### Alfred Workflow

```applescript
on alfred_script(q)
  set apiURL to "http://localhost:5000/api/search?q=" & q
  do shell script "curl '" & apiURL & "'"
end alfred_script
```

---

## Performance

**Typical Response Times:**
- Search: < 50ms
- Semantic search: < 200ms
- Chat with RAG: 1-3 seconds
- Index file: 100-500ms
- Index folder: 30s per 1000 files

**Optimization Tips:**
- Use pagination for large result sets
- Cache frequent queries
- Index in background
- Use semantic search sparingly (slower but more accurate)

---

## Support

**Issues:** [GitHub Issues](https://github.com/brebuilds/fileorganizer/issues)

**API Questions:** Tag issue with `api` label

**Feature Requests:** Tag with `enhancement` and `api`

---

**Ready to build something awesome? 🚀**

