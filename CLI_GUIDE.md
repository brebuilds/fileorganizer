# 🧙‍♂️ Cheesy CLI Guide

## The Fun, Fast Way to Organize Files

Instead of typing long commands, just use the **@ symbol** and **?** shortcuts!

---

## 🚀 Installation (One-Time Setup)

### Option 1: Use the wrapper (easiest)
```bash
cd "/Users/bre/file organizer"
./o HELP
```

### Option 2: Add to your PATH
```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'export PATH="$PATH:/Users/bre/file organizer"' >> ~/.zshrc
echo 'alias o="/Users/bre/file\ organizer/o"' >> ~/.zshrc
source ~/.zshrc

# Now you can use from anywhere:
o @Desktop
```

---

## 🎯 Basic Commands (The Cheesy Ones!)

### SORT@ - Organize folders
```bash
./o SORT@Desktop          # Sort Desktop by file type
./o SORT@Downloads        # Sort Downloads
./o @Desktop              # Shortcut!
./o @Downloads            # Even shorter!
```

**What it does:**
- Sorts files into folders: Documents/, Images/, Archives/, etc.
- Safe - doesn't delete anything
- Shows you what it moved

### TAG@ - AI Tag files
```bash
./o TAG@Documents         # Tag files in Documents with AI
./o TAG@~/Dropbox/Work    # Tag files in Dropbox
```

**What it does:**
- Scans folder for files
- Uses AI to create summaries and tags
- Detects projects automatically

### FIND@ or ? - Search files
```bash
./o FIND@invoice          # Find all invoices
./o ?invoice              # Shortcut!
./o ?"client proposal"    # Search with quotes
```

**What it does:**
- Searches your entire indexed database
- Shows filenames, summaries, locations
- Fast semantic search

### GRAPH@ - Show relationships
```bash
./o GRAPH@ProjectX        # Show all files for ProjectX
./o GRAPH@ClientA         # Show ClientA files
```

**What it does:**
- Uses graph database to find connections
- Shows all files related to a project
- Includes related tags and files

### SIMILAR@ - Find related files
```bash
./o SIMILAR@proposal.pdf
./o SIMILAR@~/Documents/important.pdf
```

**What it does:**
- Uses vector search to find similar files
- Shows similarity scores
- Great for finding related documents

---

## 📊 Utility Commands

### STATS - Show statistics
```bash
./o STATS
```

Shows:
- Total files indexed
- Folders monitored
- File types
- Top tags
- Learned patterns

### EXPORT - Export catalog
```bash
./o EXPORT
```

Creates 4 files:
- JSON (data)
- CSV (spreadsheet)
- HTML (interactive catalog)
- Markdown (docs)

---

## 💡 Pro Tips

### 1. Create an alias for super-fast access
```bash
# Add to ~/.zshrc
alias o="/Users/bre/file\ organizer/o"

# Now just type:
o @Desktop
o ?invoice
o STATS
```

### 2. Common folder shortcuts work
```bash
./o @Desktop     # ~/Desktop
./o @Downloads   # ~/Downloads
./o @Documents   # ~/Documents
./o @Pictures    # ~/Pictures
```

### 3. Use quotes for paths with spaces
```bash
./o TAG@"My Files"
./o SIMILAR@"Important Documents/file.pdf"
```

### 4. Chain with other commands
```bash
# Export then open
./o EXPORT && open ~/.fileorganizer/exports/*.html

# Find then count
./o ?invoice | wc -l
```

---

## 🎨 Examples by Scenario

### Morning Cleanup Routine
```bash
# Clean up Downloads from yesterday
./o @Downloads

# Check what you have
./o STATS

# Find that important file
./o ?proposal
```

### Starting a New Project
```bash
# Tag your project folder
./o TAG@~/Documents/NewProject

# See what got indexed
./o GRAPH@NewProject
```

### Looking for Files
```bash
# Quick search
./o ?invoice

# Find similar to a file you have
./o SIMILAR@example.pdf

# Check specific project
./o GRAPH@ClientX
```

### End of Week Archive
```bash
# Export your catalog
./o EXPORT

# View stats
./o STATS

# Clean up desktop
./o @Desktop
```

---

## 🔥 The Cheat Sheet

| Command | Shortcut | What It Does |
|---------|----------|--------------|
| `SORT@Desktop` | `@Desktop` | Organize Desktop |
| `FIND@query` | `?query` | Search files |
| `TAG@folder` | - | AI tag folder |
| `GRAPH@project` | - | Show project files |
| `SIMILAR@file` | - | Find similar |
| `STATS` | - | Show statistics |
| `EXPORT` | - | Export catalog |

---

## 🎭 Why "Cheesy"?

Because commands like:
```bash
organize SORT@Desktop
```

...are way more fun and memorable than:
```bash
python /Users/bre/file\ organizer/file_operations.py --action organize --folder ~/Desktop --method by_type
```

**It's cheesy, but it works!** 🧀✨

---

## 🐛 Troubleshooting

### "Command not found"
```bash
# Make sure wrapper is executable
chmod +x "/Users/bre/file organizer/o"

# Or use full path
"/Users/bre/file organizer/o" HELP
```

### "No files found"
```bash
# Index your folders first
./o TAG@Desktop
./o TAG@Downloads

# Then search
./o ?invoice
```

### "Folder not found"
```bash
# Use full path
./o SORT@~/Documents

# Or use quotes
./o SORT@"My Folder"
```

---

## 🚀 Advanced Usage

### Combine with shell scripts
```bash
#!/bin/bash
# morning-cleanup.sh

echo "🌅 Morning cleanup routine..."

./o @Desktop
./o @Downloads
./o STATS

echo "✅ Done!"
```

### Use in cron jobs
```bash
# Organize Downloads every day at 6 PM
0 18 * * * cd "/Users/bre/file organizer" && ./o @Downloads
```

### Pipe results
```bash
# Count invoices
./o ?invoice | grep "Found" | cut -d' ' -f2

# Export to specific location
./o EXPORT && cp ~/.fileorganizer/exports/*.html ~/Dropbox/
```

---

## 📚 Full Command Reference

```bash
# Organizing
./o SORT@Desktop          # or CLEAN@Desktop
./o @Desktop              # shortcut

# Tagging
./o TAG@/path/to/folder

# Searching
./o FIND@"search query"
./o ?query                # shortcut

# Relationships
./o GRAPH@ProjectName

# Similarity
./o SIMILAR@file.pdf

# Utilities
./o STATS
./o EXPORT
./o HELP
```

---

## 🎊 Make It Yours

Want even more shortcuts? Edit the `organize` file:

```python
# Add your own shortcuts
if arg == '!!':
    # Emergency cleanup!
    return 'SORT', 'Desktop'

if arg.startswith('>>'):
    # Quick export
    return 'EXPORT', None
```

---

**The CLI is ready! Start organizing with style!** 🧙‍♂️✨

```bash
./o @Desktop    # Try it now!
```

