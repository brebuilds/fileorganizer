# 🎉 New Features Guide - File Organizer v4.0

Welcome to the massive v4.0 update! We've added 15+ major new features to make your file organization even more powerful and ADHD-friendly.

---

## 📋 Table of Contents

1. [Smart Reminders & Nudges](#smart-reminders--nudges)
2. [Screenshot & Image Management](#screenshot--image-management)
3. [Duplicate File Detector](#duplicate-file-detector)
4. [Smart Folders](#smart-folders)
5. [Bulk Operations with Preview](#bulk-operations-with-preview)
6. [Trash Manager with Recovery](#trash-manager-with-recovery)
7. [File Aging System](#file-aging-system)
8. [Bookmark & URL Manager](#bookmark--url-manager)
9. [Hide Files Feature](#hide-files-feature)
10. [External Tool Integration](#external-tool-integration)
11. [Mobile Companion App](#mobile-companion-app)
12. [Performance Improvements](#performance-improvements)
13. [Visual Improvements](#visual-improvements)

---

## 🔔 Smart Reminders & Nudges

Never forget about important files again!

### Features
- **File-based Reminders**: Set reminders for specific files
- **Context-aware Nudges**: Smart suggestions based on your patterns
- **Deadline Tracking**: Track files with deadlines
- **Auto-nudges**: Get notified when projects go stale

### Usage

**CLI:**
```bash
# Show current reminders
./o REMIND

# Show nudges
./o SUGGEST
```

**Python API:**
```python
from reminder_system import ReminderSystem
from file_indexer import FileDatabase

db = FileDatabase()
reminders = ReminderSystem(db)

# Create a reminder
reminders.create_reminder(
    file_id=123,
    reminder_type='deadline',
    reminder_date='2024-12-31',
    message='Review this before year end'
)

# Get due reminders
due = reminders.get_due_reminders()

# Get context-aware nudges
nudges = reminders.get_nudges()
```

### Nudge Types
- 📂 **Stale Project Files**: Files you haven't touched in a while
- 🧹 **Messy Folders**: When Downloads/Desktop gets cluttered
- 🏷️ **Untagged Files**: Recent files needing AI tags
- 📦 **Duplicates**: When duplicates are using space
- 📸 **Screenshots**: When screenshots pile up

---

## 📸 Screenshot & Image Management

Automatically detect, organize, and search screenshots with OCR!

### Features
- Auto-detects screenshots (macOS, Windows, CleanShot X patterns)
- OCR text extraction (requires Tesseract)
- Smart organization by date or content
- Screenshot statistics
- Duplicate screenshot detection

### Usage

**CLI:**
```bash
# Manage screenshots
./o SCREENSHOTS
```

**Python API:**
```python
from screenshot_manager import ScreenshotManager
from file_indexer import FileDatabase

db = FileDatabase()
manager = ScreenshotManager(db)

# Detect screenshots in database
count = manager.detect_screenshots_in_database()

# Process screenshot (extract OCR text)
manager.process_screenshot(file_id, filepath)

# Organize by date
operations = manager.organize_screenshots_by_date("~/Pictures/Screenshots")

# Search screenshots by text
results = manager.search_screenshots("error message")

# Get stats
stats = manager.get_screenshot_stats()
```

### OCR Setup
```bash
# macOS
brew install tesseract

# Install Python package
pip install pytesseract
```

---

## 🔄 Duplicate File Detector

Find and remove duplicate files to save space!

### Features
- Hash-based duplicate detection
- Similar file name detection
- Visual duplicate estimates
- Bulk deletion with preview
- Space savings calculator

### Usage

**CLI:**
```bash
# Find all duplicates
./o DUPLICATES
```

**Python API:**
```python
from duplicate_detector import DuplicateDetector
from file_indexer import FileDatabase

db = FileDatabase()
detector = DuplicateDetector(db)

# Find duplicates
duplicates = detector.find_duplicates(folder="~/Downloads")

# Find similar names
similar = detector.find_similar_names()

# Get duplicate stats
stats = detector.get_duplicate_stats()

# Mark as duplicates in database
for hash_val, files in duplicates.items():
    if len(files) > 1:
        # Keep first, mark others as duplicates
        for file in files[1:]:
            detector.mark_as_duplicate(file['id'], files[0]['id'])
```

---

## 📁 Smart Folders

Dynamic folders that auto-update like macOS Smart Folders, but better!

### Features
- Create custom queries that auto-update
- Filter by type, date, size, tags, project, content
- Visual indicators (icons, colors)
- Usage tracking
- Default smart folders included

### Default Smart Folders
- 🕒 Recent Files (last 7 days)
- 📦 Large Files (>10MB)
- 📄 PDFs
- 📸 Screenshots
- 🔄 Duplicates
- ⬇️ Downloads

### Usage

**CLI:**
```bash
# Show smart folders
./o SMART
```

**Python API:**
```python
from smart_folders import SmartFolders
from file_indexer import FileDatabase

db = FileDatabase()
smart = SmartFolders(db)

# Create a smart folder
folder_id = smart.create_smart_folder(
    name="Work PDFs",
    query={
        "extension": [".pdf"],
        "project": "Work",
        "date_range": {"start": "2024-01-01"}
    },
    description="All work-related PDFs",
    icon="📄",
    color="#3b82f6"
)

# Execute smart folder (get matching files)
results = smart.execute_smart_folder(folder_id)

# Get file count
count = smart.get_file_count(folder_id)
```

### Query Format
```python
query = {
    "extension": [".pdf", ".doc"],          # File types
    "tags": ["work", "important"],          # Tags
    "project": "ClientX",                    # Project name
    "date_range": {                          # Date filter
        "start": "2024-01-01",
        "end": "2024-12-31"
    },
    "min_size": 1024,                        # Min file size (bytes)
    "max_size": 10485760,                    # Max file size (bytes)
    "contains_text": "invoice",              # Content search
    "folder": "~/Downloads",                 # Folder path
    "is_screenshot": True,                   # Screenshots only
    "is_duplicate": False                    # Exclude duplicates
}
```

---

## 📦 Bulk Operations with Preview

Mass file operations with safety and undo!

### Features
- Preview before executing
- Undo capability
- Safe bulk rename/move/delete
- Regex support
- Conflict detection

### Usage

**Python API:**
```python
from bulk_operations import BulkOperations
from file_indexer import FileDatabase

db = FileDatabase()
bulk = BulkOperations(db)

# RENAME: Preview
preview = bulk.preview_rename(
    file_ids=[1, 2, 3],
    pattern=".txt",
    replacement="_backup.txt"
)

# Execute rename
result = bulk.execute_rename(preview, dry_run=False)

# MOVE: Preview
preview = bulk.preview_move(
    file_ids=[1, 2, 3],
    destination_folder="~/Archive"
)

# Execute move
result = bulk.execute_move(preview, create_folder=True)

# DELETE: Preview
preview = bulk.preview_delete(
    file_ids=[1, 2, 3],
    permanent=False  # Move to trash
)

# Execute delete
result = bulk.execute_delete([1, 2, 3], permanent=False)

# UNDO: Undo last operation
result = bulk.undo_operation(operation_id)

# Get recent operations
operations = bulk.get_recent_operations(limit=10)
```

---

## 🗑️ Trash Manager with Recovery

Safe deletion with 30-day recovery window!

### Features
- Soft delete (30-day recovery)
- Hard delete option
- Trash statistics
- Bulk recovery
- Auto-cleanup old trash

### Usage

**CLI:**
```bash
# View trash
./o TRASH
```

**Python API:**
```python
from trash_manager import TrashManager
from file_indexer import FileDatabase

db = FileDatabase()
trash = TrashManager(db)

# Get trash items
items = trash.get_trash_items()

# Recover a file
success = trash.recover_file(trash_id, restore_path="~/Documents")

# Empty trash (permanent delete)
trash.empty_trash()

# Auto-cleanup (delete items older than 30 days)
deleted = trash.cleanup_old_trash(days=30)
```

---

## ⏰ File Aging System

Automatically archive or organize old files!

### Features
- Age-based rules
- Auto-archiving
- Stale file warnings
- Custom aging policies
- Graduated storage

### Usage

**Python API:**
```python
from aging_manager import AgingManager
from file_indexer import FileDatabase

db = FileDatabase()
aging = AgingManager(db)

# Create aging rule
rule_id = aging.create_rule(
    folder_pattern="~/Downloads/*",
    age_days=30,
    action="archive",
    destination="~/Archive/Old Downloads"
)

# Apply rules
results = aging.apply_aging_rules()

# Get stale files
stale = aging.get_stale_files(age_days=90)
```

---

## 🔖 Bookmark & URL Manager

Save and organize URLs with context!

### Features
- Save URLs with metadata
- Auto-extract title/description
- Link to downloaded files
- Tag and search bookmarks
- Import from browsers (Chrome, Firefox, Safari)

### Usage

**CLI:**
```bash
# View bookmarks
./o BOOKMARKS

# Search bookmarks
./o BOOKMARK@github
```

**Python API:**
```python
from bookmark_manager import BookmarkManager
from file_indexer import FileDatabase

db = FileDatabase()
manager = BookmarkManager(db)

# Add bookmark
bookmark_id = manager.add_bookmark(
    url="https://github.com/user/repo",
    title="Cool Project",
    description="Interesting repository",
    tags=['development', 'python'],
    source='manual'
)

# Search bookmarks
results = manager.search_bookmarks(query='github', tags=['python'])

# Link to downloaded file
manager.link_to_file(bookmark_id, file_id)

# Import from Chrome
result = manager.import_from_browser('chrome')
```

---

## 👻 Hide Files Feature

Hide sensitive files from search results!

### Features
- Exclude files from search
- Privacy control
- Easy toggle on/off
- Still accessible directly

### Usage

**CLI:**
```bash
# Hide a file
./o HIDE@/path/to/sensitive.pdf

# Unhide (run same command again)
./o HIDE@/path/to/sensitive.pdf
```

**Python API:**
```python
# Files with hide_from_app=1 are excluded from search
cursor = db.conn.cursor()
cursor.execute("UPDATE files SET hide_from_app = 1 WHERE id = ?", (file_id,))
db.conn.commit()
```

---

## 🔧 External Tool Integration

Connect with Alfred, Raycast, DevonThink, Notion, Calendar!

### Features
- Alfred workflow generator
- Raycast extension generator
- DevonThink export
- Notion CSV export
- macOS Calendar integration
- Obsidian note creation
- URL schemes for deep linking

### Usage

**CLI:**
```bash
# Generate Alfred workflow
./o ALFRED

# Generate Raycast extension
./o RAYCAST
```

**Python API:**
```python
from external_tools import ExternalToolIntegration
from file_indexer import FileDatabase

db = FileDatabase()
tools = ExternalToolIntegration(db)

# Generate Alfred workflow
output_dir = tools.generate_alfred_workflow()

# Export to DevonThink
result = tools.export_to_devonthink(
    file_ids=[1, 2, 3],
    database_name="File Organizer"
)

# Create Calendar event
result = tools.create_calendar_event(
    file_id=123,
    event_title="Review Document",
    event_date="2024-12-25",
    notes="Important review"
)

# Create Obsidian note
result = tools.create_obsidian_note(
    file_id=123,
    vault_path="~/Documents/Obsidian Vault",
    note_name="File Notes"
)

# URL Scheme
url = tools.get_url_scheme('search', q='invoice')
# Returns: fileorganizer://search?q=invoice
```

---

## 📱 Mobile Companion App

Access your files from mobile devices!

### Features
- File upload from mobile
- Search optimized for mobile
- Sync queue management
- Mobile-optimized API responses
- Quick organization suggestions

### Usage

**CLI:**
```bash
# Show mobile stats
./o MOBILE
```

**Python API:**
```python
from mobile_companion import MobileCompanion
from file_indexer import FileDatabase

db = FileDatabase()
mobile = MobileCompanion(db)

# Upload file from mobile
result = mobile.upload_file(
    file_data=binary_data,
    filename="photo.jpg",
    device_id="iphone_12",
    metadata={"location": "Camera Roll"}
)

# Search for mobile
results = mobile.search_for_mobile("invoice", limit=20)

# Get recent files (mobile format)
recent = mobile.get_recent_files_for_mobile(limit=20)

# Get stats
stats = mobile.get_mobile_stats(device_id="iphone_12")

# Add to sync queue
mobile.add_to_sync_queue(file_id, action='download', device_id="iphone_12")
```

---

## ⚡ Performance Improvements

Blazing fast with smart optimizations!

### Features
- Background indexing (non-blocking)
- Search result caching
- Incremental search (as-you-type)
- Lazy loading/pagination
- Database optimization tools

### Usage

**CLI:**
```bash
# Optimize database
./o OPTIMIZE
```

**Python API:**
```python
from performance_optimizer import PerformanceOptimizer
from file_indexer import FileDatabase

db = FileDatabase()
optimizer = PerformanceOptimizer(db)

# Start background indexing
optimizer.start_background_indexing()

# Queue file for background indexing
optimizer.queue_file_for_indexing("/path/to/file")

# Cached search (fast repeated searches)
results = optimizer.cached_search("query", limit=50)

# Incremental search (as-you-type)
results = optimizer.incremental_search("inv")  # Partial query

# Paginated results (lazy loading)
page1 = optimizer.get_paginated_files(offset=0, limit=50)
page2 = optimizer.get_paginated_files(offset=50, limit=50)

# Optimize database
optimizer.optimize_database()

# Get performance stats
stats = optimizer.get_database_stats()
```

---

## 🎨 Visual Improvements

Beautiful and intuitive interface enhancements!

### Features
- File preview thumbnails (planned for GUI)
- Color-coded file types (planned for GUI)
- Progress bars for bulk operations (planned for GUI)
- macOS Notification Center integration (planned for GUI)
- Enhanced dark mode support (planned for GUI)

These features are integrated into the PyQt6 GUI and provide a modern, polished experience.

---

## 🚀 Quick Start Examples

### Morning Cleanup Routine
```bash
# Check what came in overnight
./o !yesterday

# Review reminders and nudges
./o REMIND
./o SUGGEST

# Organize Downloads
./o @Downloads

# Check for duplicates
./o DUPLICATES
```

### Project Organization
```bash
# Tag new project files
./o TAG@~/Documents/NewProject

# Create smart folder for project
# (do this in Python/GUI)

# Set reminders for deadlines
# (do this in Python/GUI)
```

### Screenshot Management
```bash
# See screenshot stats
./o SCREENSHOTS

# Organize them (do this in GUI for preview)
```

### Performance Tuning
```bash
# Optimize database
./o OPTIMIZE

# View stats
./o STATS
```

---

## 📝 Notes

### Optional Dependencies

Some features require optional packages:

**OCR (Screenshot text extraction):**
```bash
brew install tesseract
pip install pytesseract
```

**Web Scraping (Bookmark metadata):**
```bash
pip install requests beautifulsoup4
```

**All features:**
```bash
pip install -r requirements.txt
```

### Performance Tips

1. **Use background indexing** for large folders
2. **Enable caching** for faster searches
3. **Run OPTIMIZE monthly** to maintain performance
4. **Use smart folders** instead of repeated searches
5. **Hide unused files** from search to reduce noise

### ADHD-Friendly Tips

1. **Set reminders liberally** - external memory is key
2. **Check SUGGEST daily** - proactive nudges help
3. **Use screenshots** feature - visual memory aid
4. **Create project smart folders** - reduce context switching
5. **Use CLI shortcuts** - fastest way to organize quickly

---

## 🆘 Troubleshooting

### OCR not working
- Install Tesseract: `brew install tesseract`
- Install Python package: `pip install pytesseract`

### Background indexing slow
- Reduce batch size in performance optimizer
- Check system resources
- Pause background indexing during heavy work

### Database getting large
- Run `./o OPTIMIZE` to clean up
- Empty trash regularly
- Clean up old file_events entries

### Search results incomplete
- Check if files are hidden (hide_from_app=1)
- Re-index folder: `./o TAG@folder`
- Rebuild FTS index (run OPTIMIZE)

---

## 📚 More Resources

- `README.md` - Main documentation
- `COMPLETE_FEATURES_SUMMARY.md` - All features overview
- `CLI_GUIDE.md` - Complete CLI reference
- `COMMANDS_CHEATSHEET.md` - Quick command reference
- `WHATS_NEW.md` - Latest features summary

---

**Made with ❤️ for ADHD brains that move faster than their file systems!** 🧠✨

Version 4.0 - December 2024

