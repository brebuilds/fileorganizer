# 📤 Export & OpenAI Integration Guide

## Two New Powerful Features

### ✅ Feature 1: Export File Index
Export your entire file catalog to multiple formats for backup, analysis, or sharing.

### ✅ Feature 2: OpenAI Integration (Optional)
Get high-quality AI summaries using OpenAI's GPT models - better than local Ollama for detailed analysis.

---

## 📤 Export Manager

### What It Does

Creates comprehensive index files of all your organized files in multiple formats:

- **JSON** - Complete data export, machine-readable
- **CSV** - Spreadsheet-friendly (Excel, Google Sheets)
- **HTML** - Beautiful interactive catalog with search
- **Markdown** - Human-readable documentation

### Export Formats

#### 1. **JSON Export** (Complete Data)
```json
{
  "metadata": {
    "export_date": "2025-10-25T18:28:19",
    "total_files": 220,
    "database_stats": {...},
    "learned_patterns_count": 3
  },
  "files": [
    {
      "id": 1,
      "filename": "document.pdf",
      "path": "/Users/bre/Documents/document.pdf",
      "ai_summary": "Project proposal for Client X",
      "ai_tags": "proposal, client, project",
      "project": "ClientX",
      "access_count": 5,
      ...
    }
  ],
  "statistics": {...},
  "learned_patterns": [...]
}
```

**Use Cases:**
- Backup your entire file index
- Import into other tools
- Data analysis
- API consumption

#### 2. **CSV Export** (Spreadsheet)
```csv
Filename,Extension,Size,Modified Date,Location,Summary,Tags,Project,Access Count,Full Path
document.pdf,.pdf,245632,2025-10-20,Documents,"Project proposal...",proposal,ClientX,5,/Users/bre/...
```

**Use Cases:**
- Open in Excel/Numbers/Google Sheets
- Sort and filter files
- Create reports
- Share with team

#### 3. **HTML Export** (Interactive Catalog)
- **Beautiful visual design**
- **Live search** - filter as you type
- **Responsive** - works on all devices
- **Statistics dashboard**
- **Clickable tags and projects**

**Use Cases:**
- Browse your file catalog in a browser
- Share with clients (read-only view)
- Create searchable archives
- Visualize your file organization

#### 4. **Markdown Export** (Documentation)
```markdown
# 📁 File Index

## 📊 Statistics
- Total Files: 220
- Folders Monitored: 5

## 📂 Files by Project

### ClientX
**proposal_v3.pdf**
- Summary: Final project proposal with pricing
- Tags: proposal, pricing, final
- Location: Documents
...
```

**Use Cases:**
- GitHub repositories
- Documentation
- Knowledge bases
- Notes/wikis

### How to Use

#### Quick Export (All Formats)
```bash
cd "/Users/bre/file organizer"
./one/bin/python export_manager.py
```

This creates 4 files in `~/.fileorganizer/exports/`:
- `file_index_YYYYMMDD_HHMMSS.json`
- `file_index_YYYYMMDD_HHMMSS.csv`
- `file_index_YYYYMMDD_HHMMSS.html` ← **Open this in browser!**
- `file_index_YYYYMMDD_HHMMSS.md`

#### Programmatic Export
```python
from export_manager import ExportManager
from file_indexer import FileDatabase

db = FileDatabase()
exporter = ExportManager(db)

# Export specific format
json_path, count = exporter.export_to_json()
print(f"Exported {count} files to {json_path}")

# Export with full content (large file)
json_path, count = exporter.export_to_json(
    include_content=True  # Includes full file text
)

# Export all formats
results = exporter.export_all_formats()

db.close()
```

#### Custom Export Location
```python
# Specify custom output path
exporter.export_to_html('/Users/bre/Desktop/my_files.html')
exporter.export_to_csv('/Users/bre/Desktop/my_files.csv')
```

### Example: Opening HTML Catalog

```bash
# After exporting
open ~/.fileorganizer/exports/file_index_*.html

# Or with full path
open "/Users/bre/.fileorganizer/exports/file_index_20251025_182819.html"
```

The HTML catalog includes:
- 📊 Statistics dashboard
- 🔍 Live search box
- 📁 File listings with summaries
- 🏷️ Tag visualization
- 📂 Project organization

---

## 🤖 OpenAI Integration (Optional)

### ⚠️ IMPORTANT - Read This First

#### Privacy Notice
- **File content is sent to OpenAI** for analysis
- OpenAI processes but **does not store** your files (per their API policy)
- Only use if you're comfortable with OpenAI's privacy policy
- Consider sensitive documents before enabling

#### Cost Notice
- **This is a PAID service** - you need an OpenAI API account
- Approximate cost: **$0.001 per file** (very affordable)
- Example: 100 files = ~$0.10
- You control what gets sent

### Why Use OpenAI Instead of Ollama?

| Feature | Local Ollama | OpenAI |
|---------|-------------|---------|
| **Quality** | Good | Excellent |
| **Detail** | Brief | Comprehensive |
| **Speed** | Medium | Fast |
| **Privacy** | 100% Local | Sent to OpenAI |
| **Cost** | Free | ~$0.001/file |
| **Entity Extraction** | Basic | Advanced |

**OpenAI Advantages:**
- More detailed, nuanced summaries
- Better entity extraction (people, companies, dates, amounts)
- Understands context better
- Handles complex documents
- Structured JSON output

### Setup

#### Step 1: Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-...`)

#### Step 2: Configure

**Option A: Interactive Setup**
```bash
cd "/Users/bre/file organizer"
./one/bin/python openai_integration.py
# Follow the prompts
```

**Option B: Manual Setup**
```bash
# Set environment variable
export OPENAI_API_KEY='sk-your-key-here'

# Or save to file (more permanent)
echo 'sk-your-key-here' > ~/.fileorganizer/openai_key
chmod 600 ~/.fileorganizer/openai_key
```

#### Step 3: Install OpenAI Library (if needed)
```bash
./one/bin/pip install openai
```

### Using OpenAI Tagging

#### Quick Start - Tag 10 Files
```bash
cd "/Users/bre/file organizer"
./one/bin/python openai_integration.py
# Follow prompts to tag files
```

#### Programmatic Usage
```python
from openai_integration import OpenAITagger
from file_indexer import FileDatabase
from setup_wizard import load_user_profile

# Setup
db = FileDatabase()
profile = load_user_profile()
tagger = OpenAITagger(user_profile=profile)

# Tag untagged files (with confirmation)
stats = tagger.batch_tag_files(db, limit=10)
print(f"Tagged {stats['tagged']} files")
print(f"Cost: ${stats['total_tokens'] * 0.00000015:.4f}")

db.close()
```

#### Tag a Single File
```python
# Analyze one file
result = tagger.tag_file(
    filename="proposal.pdf",
    content="[file content here]",
    file_type=".pdf"
)

print(result)
# {
#   'summary': 'Detailed project proposal for ClientX...',
#   'tags': ['proposal', 'client', 'project', 'pricing'],
#   'project': 'ClientX',
#   'topic': 'Business Proposal',
#   'entities': {
#     'people': ['John Smith'],
#     'companies': ['ClientX Corp'],
#     'dates': ['2025-11-01'],
#     'amounts': ['$50,000']
#   },
#   'confidence': 0.95,
#   'tokens_used': 1523
# }
```

### What You Get

OpenAI provides **richer analysis**:

#### Example Comparison

**Local Ollama:**
```
Summary: "Invoice document"
Tags: ["invoice", "billing", "payment"]
Project: "ClientX"
```

**OpenAI GPT-4:**
```
Summary: "Monthly service invoice for ClientX dated October 2025, 
         covering cloud infrastructure services totaling $5,240 USD, 
         payment due November 15th"
         
Tags: ["invoice", "billing", "cloud-services", "monthly", 
       "infrastructure", "recurring", "october-2025"]
       
Project: "ClientX"
Topic: "Financial - Invoicing"

Entities:
  People: []
  Companies: ["ClientX Corp", "AWS"]
  Dates: ["2025-10-01", "2025-10-31", "2025-11-15"]
  Amounts: ["$5,240.00", "$3,200.00 (compute)", "$2,040.00 (storage)"]
  
Confidence: 0.95
```

### Cost Management

#### Estimate Costs
```python
# Get count of files to tag
cursor = db.conn.cursor()
cursor.execute("""
    SELECT COUNT(*) FROM files 
    WHERE ai_summary IS NULL 
    AND content_text IS NOT NULL
""")
count = cursor.fetchone()[0]

print(f"Files to tag: {count}")
print(f"Estimated cost: ${count * 0.001:.2f}")
```

#### Tag in Batches
```python
# Tag in small batches to control cost
tagger.batch_tag_files(db, limit=10)  # First 10
# Review results...
tagger.batch_tag_files(db, limit=10)  # Next 10
```

#### Force Retag Specific Files
```python
# Retag files even if they have summaries
tagger.batch_tag_files(
    db, 
    limit=5, 
    force_retag=True  # Re-analyze with OpenAI
)
```

### Privacy Best Practices

1. **Review files before tagging**
   - Don't send sensitive documents
   - Check what content will be sent

2. **Use selective tagging**
   ```python
   # Only tag specific folders
   cursor.execute("""
       SELECT id, filename, content_text
       FROM files
       WHERE folder_location = '/Users/bre/Public'
       AND ai_summary IS NULL
   """)
   ```

3. **Monitor what's sent**
   - The script shows which files before sending
   - Requires confirmation before processing
   - Shows estimated cost

4. **Alternative: Keep using Ollama**
   - 100% local processing
   - No data leaves your computer
   - Free
   - Good quality (just less detailed)

---

## 🎯 Use Cases

### Use Case 1: Create File Catalog for Team
```bash
# Export to HTML
./one/bin/python export_manager.py

# Share the HTML file
cp ~/.fileorganizer/exports/file_index_*.html ~/Dropbox/team/
# Team can browse without accessing actual files
```

### Use Case 2: High-Quality Summaries for Important Files
```python
# Use OpenAI for critical documents
from openai_integration import OpenAITagger
from file_indexer import FileDatabase

db = FileDatabase()
tagger = OpenAITagger()

# Tag only files in specific folder
cursor = db.conn.cursor()
cursor.execute("""
    SELECT id FROM files
    WHERE folder_location LIKE '%Contracts%'
    AND ai_summary IS NULL
""")

contract_ids = [row[0] for row in cursor.fetchall()]
print(f"Tagging {len(contract_ids)} contracts with OpenAI...")

# Would need custom loop here
```

### Use Case 3: Monthly Archive Export
```bash
# Create monthly backup
mkdir ~/Archives/FileIndex_$(date +%Y-%m)
./one/bin/python -c "
from export_manager import ExportManager
from file_indexer import FileDatabase

db = FileDatabase()
em = ExportManager(db)
em.export_all_formats()
db.close()
"

# Copy to archive
cp ~/.fileorganizer/exports/* ~/Archives/FileIndex_$(date +%Y-%m)/
```

### Use Case 4: Hybrid Approach
```bash
# Use Ollama (free) for most files
# Use OpenAI (paid) for important files only

# 1. Let Ollama tag everything
./one/bin/python ai_tagger.py

# 2. Use OpenAI for specific project
# (custom script to tag only project files)
```

---

## 📊 Feature Comparison

| Feature | Export Manager | OpenAI Integration |
|---------|----------------|-------------------|
| **Purpose** | Create file catalogs | High-quality summaries |
| **Privacy** | 100% local | Sends to OpenAI |
| **Cost** | Free | ~$0.001/file |
| **Output** | JSON/CSV/HTML/MD | Enhanced summaries |
| **Use When** | Backup, share, analyze | Need detailed analysis |
| **Dependencies** | None | OpenAI API key |

---

## 🚀 Quick Commands

```bash
# Export everything
./one/bin/python export_manager.py

# View HTML catalog
open ~/.fileorganizer/exports/file_index_*.html

# Setup OpenAI
./one/bin/python openai_integration.py

# Tag 10 files with OpenAI
./one/bin/python -c "
from openai_integration import OpenAITagger
from file_indexer import FileDatabase
db = FileDatabase()
t = OpenAITagger()
stats = t.batch_tag_files(db, limit=10)
print(f'Tagged: {stats[\"tagged\"]}')
db.close()
"
```

---

## ✅ Summary

**Export Manager**
- ✅ 4 export formats (JSON, CSV, HTML, Markdown)
- ✅ Beautiful interactive HTML catalog
- ✅ 100% local, no privacy concerns
- ✅ Free, no API needed
- ✅ Ready to use now

**OpenAI Integration**
- ✅ High-quality detailed summaries
- ✅ Advanced entity extraction
- ✅ Better than local Ollama
- ⚠️ Sends data to OpenAI (consider privacy)
- ⚠️ Paid service (~$0.001/file)
- ✅ Optional - use if you need it

**You control everything:**
- What gets exported
- What gets sent to OpenAI
- When and how often
- Which files to prioritize

---

*Both features are ready to use!*
*Test with: `./one/bin/python export_manager.py`*

