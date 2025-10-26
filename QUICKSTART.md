# ⚡ Quick Start Guide

Get up and running with your Personal RAG System in **5 minutes**!

---

## Step 1: Install Ollama (2 minutes)

**What is Ollama?**
Free, open-source AI that runs entirely on your Mac. No cloud, no API keys, works offline!

1. Download: [https://ollama.ai](https://ollama.ai)
2. Install: Double-click the downloaded file
3. Open Terminal and run:
```bash
ollama pull llama2
```

**Why Ollama?**
- ✅ 100% local & private
- ✅ No monthly costs
- ✅ Works offline
- ✅ Fast responses

**Alternative:** Use OpenAI API (Settings → Enable OpenAI) but this costs money and sends data externally.

---

## Step 2: Install File Organizer (1 minute)

**Option A: Download App Bundle (Recommended)**
1. Download `FileOrganizer.app` from [Releases](https://github.com/brebuilds/fileorganizer/releases)
2. Drag to Applications folder
3. Double-click to open

**Option B: Run from Source**
```bash
git clone https://github.com/brebuilds/fileorganizer.git
cd fileorganizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python file_organizer_app.py
```

---

## Step 3: Index Your First Files (1 minute)

The app opens in your menu bar!

1. Click the app icon → **Settings** tab
2. Under "File Sources & Indexing":
   - ☑ Check **Downloads** (everyone has stuff here!)
   - ☑ Check **Documents** (if you want)
   - ☑ Check **Index Apple Notes** (if available)
3. Click **"🔍 Scan Selected Folders"**
4. Wait ~30 seconds while it indexes

**You'll see:**
```
✅ Indexed 247 items
⏭️ Skipped 12 items
```

---

## Step 4: Try Your First Query (30 seconds)

Go to the **💬 Chat** tab and try these:

### Example 1: Find Recent Files
```
What files did I download yesterday?
```

### Example 2: Search by Content
```
Find documents about invoices
```

### Example 3: Semantic Search
```
Show me design files
```
*(Finds .psd, .fig, .sketch, mockups, etc.)*

### Example 4: Apple Notes
```
What notes do I have about meetings?
```

---

## Step 5: Enable Advanced Features (30 seconds)

### Want Better Summaries? Enable OpenAI
**Settings → AI Enhancements**
- ☑ Enable OpenAI
- Enter API key: `sk-...`
- ⚠️ Warning appears: data sent to OpenAI

### Want API Access? Enable REST API
**Settings → Automations & APIs**
- ☑ Enable REST API
- Click "View API Documentation"
- Server runs on `http://localhost:5000`

---

## 🎉 You're Ready!

### What You Can Do Now:

#### Via Chat (Natural Language)
- "Find that contract I got last month"
- "Show me all Phoenix project files"
- "What screenshots do I have?"
- "Organize my desktop by project"

#### Via CLI (Power Users)
```bash
cd /path/to/fileorganizer
./o ?invoice              # Search for "invoice"
./o !yesterday            # Files from yesterday
./o @Desktop              # Organize Desktop
./o STATS                 # Show statistics
./o HELP                  # All commands
```

#### Via API (Developers)
```bash
# Search files
curl http://localhost:5000/api/search?q=invoice

# Chat with RAG
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find design files from last week"}'
```

---

## 🚀 Next Steps

### Learn More:
- [Complete Feature Guide](GUIDE.md) - All features explained
- [RAG System Documentation](RAG_GUIDE.md) - Technical deep dive
- [API Reference](API.md) - Complete API docs
- [CLI Commands](CLI_GUIDE.md) - Terminal power user guide

### Customize:
- **Settings → About You** - Tell it about yourself
- **Settings → Features** - Toggle features on/off
- **Settings → Assistant Identity** - Change AI personality

### Get Help:
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [GitHub Issues](https://github.com/brebuilds/fileorganizer/issues)
- [Community Discord](#) *(coming soon)*

---

## ⚡ Power User Tips

### 1. Auto-Scan for New Files
**Settings → Auto-Organization**
- ☑ Auto-scan for new files every hour

### 2. Index Everything
Check these sources in Settings:
- 📁 Local: Downloads, Documents, Desktop, Pictures
- ☁️ Cloud: Dropbox, iCloud, Google Drive
- 📝 Notes: Apple Notes
- 🔧 Tools: Alfred, Raycast, DevonThink

### 3. Use Smart Folders
```bash
./o SMART
```
6 default smart folders auto-organize files!

### 4. Build Workflows with API
Connect to n8n, Make.com, Zapier:
```
New file in Downloads
  ↓
Auto-index with RAG
  ↓
AI generates summary
  ↓
Post to Slack
```

---

## 🎯 Common First Queries

**Not sure what to ask? Try these:**

```
Show me my most recent files
What PDFs do I have?
Find files I haven't opened in 6 months
What did I work on last week?
Show me everything about [project name]
What files are taking up the most space?
Do I have any duplicate files?
What's in my Downloads folder?
Show me all my screenshots
What notes did I write today?
```

---

## 🆘 Quick Troubleshooting

### "No results found"
→ Go to Settings and scan your folders first!

### "Ollama not responding"
→ Open Terminal: `ollama serve`

### "Apple Notes shows 0 notes"
→ System Preferences → Privacy → Full Disk Access → Add app

### "API not working"
→ Settings → Enable REST API checkbox

### "Slow performance"
→ Settings → Features → Disable unused features

---

## 📊 What's Being Indexed?

Check the **📋 Activity Log** tab to see real-time progress:

```
[14:23:45] Indexed    invoice.pdf       Added to database (ID: 1247)
[14:23:46] Indexed    Screenshot.png    Added to database (ID: 1248)
[14:23:47] Indexed    Meeting Notes     Apple Note added (ID: 1249)
[14:23:48] Complete   Batch Scan        Indexed 247 files
```

---

**Ready to become a file organization wizard? Let's go! 🧙‍♂️✨**

