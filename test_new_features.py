#!/usr/bin/env python3
"""
Test Script for File Organizer v4.0 New Features
Tests all newly implemented modules
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_imports():
    """Test that all new modules can be imported"""
    print("🧪 Testing Module Imports...")
    
    modules = [
        ('reminder_system', 'ReminderSystem'),
        ('screenshot_manager', 'ScreenshotManager'),
        ('smart_folders', 'SmartFolders'),
        ('bulk_operations', 'BulkOperations'),
        ('bookmark_manager', 'BookmarkManager'),
        ('external_tools', 'ExternalToolIntegration'),
        ('mobile_companion', 'MobileCompanion'),
        ('performance_optimizer', 'PerformanceOptimizer'),
    ]
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print(f"  ✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name}: {e}")
            return False
    
    return True


def test_database_schema():
    """Test that new database tables exist"""
    print("\n🗄️  Testing Database Schema...")
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    cursor = db.conn.cursor()
    
    # Check for new tables
    tables = [
        'reminders',
        'suggestions',
        'aging_rules',
        'file_events',
        'bookmarks',
        'bulk_operations',
        'screenshot_metadata',
        'mobile_sync_queue',
        'smart_folders'
    ]
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if cursor.fetchone():
            print(f"  ✅ Table '{table}' exists")
        else:
            print(f"  ❌ Table '{table}' missing")
            return False
    
    # Check for new columns in files table
    cursor.execute("PRAGMA table_info(files)")
    columns = {row[1] for row in cursor.fetchall()}
    
    new_columns = ['is_duplicate', 'duplicate_of', 'ocr_text', 'is_screenshot', 'hide_from_app']
    
    for col in new_columns:
        if col in columns:
            print(f"  ✅ Column 'files.{col}' exists")
        else:
            print(f"  ❌ Column 'files.{col}' missing")
    
    db.close()
    return True


def test_reminder_system():
    """Test reminder system"""
    print("\n⏰ Testing Reminder System...")
    
    from reminder_system import ReminderSystem
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    reminders = ReminderSystem(db)
    
    try:
        # Test nudges
        nudges = reminders.get_nudges(limit=5)
        print(f"  ✅ Got {len(nudges)} nudges")
        
        # Test reminders
        due = reminders.get_due_reminders()
        print(f"  ✅ Got {len(due)} due reminders")
        
        upcoming = reminders.get_upcoming_reminders(days_ahead=7)
        print(f"  ✅ Got {len(upcoming)} upcoming reminders")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_screenshot_manager():
    """Test screenshot manager"""
    print("\n📸 Testing Screenshot Manager...")
    
    from screenshot_manager import ScreenshotManager
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    manager = ScreenshotManager(db)
    
    try:
        # Detect screenshots
        count = manager.detect_screenshots_in_database()
        print(f"  ✅ Detected {count} screenshots")
        
        # Get stats
        stats = manager.get_screenshot_stats()
        print(f"  ✅ Total screenshots: {stats['total_count']}")
        print(f"  ✅ Total size: {stats['total_size_mb']:.2f} MB")
        print(f"  ✅ With text: {stats['with_text']}")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_smart_folders():
    """Test smart folders"""
    print("\n📁 Testing Smart Folders...")
    
    from smart_folders import SmartFolders
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    smart = SmartFolders(db)
    
    try:
        # Create default folders (if not exist)
        created = smart.create_default_smart_folders()
        if created:
            print(f"  ✅ Created {len(created)} default smart folders")
        
        # Get all folders
        folders = smart.get_all_smart_folders()
        print(f"  ✅ Found {len(folders)} smart folders")
        
        # Test executing a folder
        if folders:
            results = smart.execute_smart_folder(folders[0]['id'])
            print(f"  ✅ Executed '{folders[0]['name']}': {len(results)} files")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_bulk_operations():
    """Test bulk operations"""
    print("\n📦 Testing Bulk Operations...")
    
    from bulk_operations import BulkOperations
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    bulk = BulkOperations(db)
    
    try:
        # Get recent operations
        operations = bulk.get_recent_operations(limit=5)
        print(f"  ✅ Found {len(operations)} recent operations")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_bookmark_manager():
    """Test bookmark manager"""
    print("\n🔖 Testing Bookmark Manager...")
    
    from bookmark_manager import BookmarkManager
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    manager = BookmarkManager(db)
    
    try:
        # Get bookmarks
        bookmarks = manager.get_all_bookmarks(limit=10)
        print(f"  ✅ Found {len(bookmarks)} bookmarks")
        
        # Get stats
        stats = manager.get_bookmark_stats()
        print(f"  ✅ Total bookmarks: {stats['total']}")
        print(f"  ✅ With files: {stats['with_files']}")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_external_tools():
    """Test external tools integration"""
    print("\n🔧 Testing External Tools...")
    
    from external_tools import ExternalToolIntegration
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    tools = ExternalToolIntegration(db)
    
    try:
        # Test URL scheme generation
        url = tools.get_url_scheme('search', q='test')
        print(f"  ✅ Generated URL scheme: {url}")
        
        # Export config
        config_path = tools.export_integration_config()
        print(f"  ✅ Config exported to: {config_path}")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_mobile_companion():
    """Test mobile companion"""
    print("\n📱 Testing Mobile Companion...")
    
    from mobile_companion import MobileCompanion
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    mobile = MobileCompanion(db)
    
    try:
        # Get stats
        stats = mobile.get_mobile_stats()
        print(f"  ✅ Total files: {stats['total_files']}")
        print(f"  ✅ Total size: {stats['total_size_mb']:.1f} MB")
        
        # Get suggestions
        suggestions = mobile.quick_organize_suggestion()
        print(f"  ✅ Got {len(suggestions)} suggestions")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_performance_optimizer():
    """Test performance optimizer"""
    print("\n⚡ Testing Performance Optimizer...")
    
    from performance_optimizer import PerformanceOptimizer
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    optimizer = PerformanceOptimizer(db)
    
    try:
        # Get stats
        stats = optimizer.get_database_stats()
        print(f"  ✅ DB Size: {stats['db_size_mb']:.2f} MB")
        print(f"  ✅ Indexes: {stats['index_count']}")
        print(f"  ✅ Cache size: {stats['search_cache_size']}")
        
        # Test pagination
        page1 = optimizer.get_paginated_files(offset=0, limit=5)
        print(f"  ✅ Pagination works: {len(page1)} files")
        
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.close()
        return False


def test_cli_commands():
    """Test CLI command parsing"""
    print("\n🎯 Testing CLI Commands...")
    
    try:
        # Import CLI
        from organize import MagicalCLI
        
        cli = MagicalCLI()
        
        # Test command parsing
        test_commands = [
            ('@Desktop', ('SORT', 'Desktop')),
            ('?invoice', ('FIND', 'invoice')),
            ('!yesterday', ('WHEN', 'yesterday')),
            ('BOOKMARKS', ('BOOKMARKS', None)),
            ('OPTIMIZE', ('OPTIMIZE', None)),
        ]
        
        for input_cmd, expected in test_commands:
            result = cli.parse_command(input_cmd)
            if result == expected:
                print(f"  ✅ Parse '{input_cmd}' → {result}")
            else:
                print(f"  ❌ Parse '{input_cmd}' → {result} (expected {expected})")
                return False
        
        cli.db.close()
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 File Organizer v4.0 - New Features Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_module_imports),
        ("Database Schema", test_database_schema),
        ("Reminder System", test_reminder_system),
        ("Screenshot Manager", test_screenshot_manager),
        ("Smart Folders", test_smart_folders),
        ("Bulk Operations", test_bulk_operations),
        ("Bookmark Manager", test_bookmark_manager),
        ("External Tools", test_external_tools),
        ("Mobile Companion", test_mobile_companion),
        ("Performance Optimizer", test_performance_optimizer),
        ("CLI Commands", test_cli_commands),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Final Score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! File Organizer v4.0 is ready!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

