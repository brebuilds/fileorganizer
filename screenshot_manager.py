#!/usr/bin/env python3
"""
Screenshot Manager for File Organizer
Auto-detect, OCR, and organize screenshots intelligently
"""

import os
import re
from datetime import datetime
from pathlib import Path
import sqlite3

# Optional OCR support
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Note: OCR not available. Install pytesseract and Pillow for text extraction")


class ScreenshotManager:
    """Manages screenshot detection, OCR, and organization"""
    
    def __init__(self, db):
        self.db = db
        self.screenshot_patterns = [
            r'Screen Shot \d{4}-\d{2}-\d{2} at',  # macOS default
            r'Screenshot \d{4}-\d{2}-\d{2}',       # Windows/Linux
            r'screenshot_\d+',                      # Generic
            r'CleanShot \d{4}-\d{2}-\d{2}',        # CleanShot X
            r'SCR_\d+',                             # Android
            r'IMG_\d+\.PNG'                         # iOS screenshots (uppercase PNG)
        ]
        
        self.image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
    
    def is_screenshot(self, filepath):
        """
        Detect if a file is a screenshot based on filename patterns
        """
        filename = os.path.basename(filepath)
        
        # Check filename patterns
        for pattern in self.screenshot_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        
        # Check if PNG in Downloads/Desktop (likely screenshot)
        if filepath.lower().endswith('.png'):
            folder = os.path.dirname(filepath)
            if 'Downloads' in folder or 'Desktop' in folder:
                return True
        
        return False
    
    def detect_screenshots_in_database(self):
        """
        Scan existing files in database and mark screenshots
        """
        cursor = self.db.conn.cursor()
        
        # Get all image files
        cursor.execute("""
            SELECT id, path, filename
            FROM files
            WHERE extension IN ('.png', '.jpg', '.jpeg', '.gif')
              AND status = 'active'
              AND is_screenshot = 0
        """)
        
        files = cursor.fetchall()
        screenshot_count = 0
        
        for file_id, path, filename in files:
            if self.is_screenshot(path):
                # Mark as screenshot
                cursor.execute("""
                    UPDATE files
                    SET is_screenshot = 1
                    WHERE id = ?
                """, (file_id,))
                screenshot_count += 1
        
        self.db.conn.commit()
        return screenshot_count
    
    def extract_text_from_screenshot(self, filepath):
        """
        Extract text from screenshot using OCR
        """
        if not OCR_AVAILABLE:
            return None
        
        try:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)
            return text.strip() if text else None
        except Exception as e:
            print(f"Error extracting text from {filepath}: {e}")
            return None
    
    def process_screenshot(self, file_id, filepath):
        """
        Process a screenshot: extract text, detect source app, save metadata
        """
        cursor = self.db.conn.cursor()
        
        # Check if already processed
        cursor.execute("""
            SELECT id FROM screenshot_metadata WHERE file_id = ?
        """, (file_id,))
        
        if cursor.fetchone():
            return  # Already processed
        
        # Extract text if OCR available
        extracted_text = None
        has_text = 0
        
        if OCR_AVAILABLE:
            extracted_text = self.extract_text_from_screenshot(filepath)
            has_text = 1 if extracted_text else 0
        
        # Detect source app (from filename if possible)
        source_app = self._detect_source_app(filepath)
        
        # Get capture date from file
        stat = os.stat(filepath)
        capture_date = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Save metadata
        cursor.execute("""
            INSERT INTO screenshot_metadata
            (file_id, capture_date, source_app, has_text, extracted_text)
            VALUES (?, ?, ?, ?, ?)
        """, (file_id, capture_date, source_app, has_text, extracted_text))
        
        # Update file with OCR text
        if extracted_text:
            cursor.execute("""
                UPDATE files
                SET ocr_text = ?
                WHERE id = ?
            """, (extracted_text, file_id))
        
        self.db.conn.commit()
    
    def _detect_source_app(self, filepath):
        """Detect which app created the screenshot"""
        filename = os.path.basename(filepath)
        
        if 'CleanShot' in filename:
            return 'CleanShot X'
        elif 'Screen Shot' in filename:
            return 'macOS Screenshot'
        elif 'Snagit' in filename:
            return 'Snagit'
        elif 'Skitch' in filename:
            return 'Skitch'
        else:
            return 'Unknown'
    
    def organize_screenshots_by_date(self, destination_base):
        """
        Organize screenshots into folders by date
        destination_base: Base folder for organization (e.g., ~/Pictures/Screenshots)
        """
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT f.id, f.path, f.filename, f.modified_date
            FROM files f
            WHERE f.is_screenshot = 1
              AND f.status = 'active'
            ORDER BY f.modified_date DESC
        """)
        
        screenshots = cursor.fetchall()
        operations = []
        
        for file_id, path, filename, modified_date in screenshots:
            # Parse date
            date = datetime.fromisoformat(modified_date)
            
            # Create destination folder: YYYY/MM/
            year_folder = os.path.join(destination_base, str(date.year))
            month_folder = os.path.join(year_folder, f"{date.month:02d}-{date.strftime('%B')}")
            
            # New path
            new_path = os.path.join(month_folder, filename)
            
            operations.append({
                'file_id': file_id,
                'old_path': path,
                'new_path': new_path,
                'folder': month_folder
            })
        
        return operations
    
    def organize_screenshots_by_content(self, destination_base):
        """
        Organize screenshots by detected content (if OCR available)
        """
        if not OCR_AVAILABLE:
            return []
        
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT f.id, f.path, f.filename, sm.extracted_text
            FROM files f
            JOIN screenshot_metadata sm ON f.id = sm.file_id
            WHERE f.is_screenshot = 1
              AND f.status = 'active'
              AND sm.has_text = 1
        """)
        
        screenshots = cursor.fetchall()
        operations = []
        
        for file_id, path, filename, text in screenshots:
            # Simple content classification
            category = self._classify_screenshot_content(text)
            
            # Create destination folder
            dest_folder = os.path.join(destination_base, category)
            new_path = os.path.join(dest_folder, filename)
            
            operations.append({
                'file_id': file_id,
                'old_path': path,
                'new_path': new_path,
                'folder': dest_folder,
                'category': category
            })
        
        return operations
    
    def _classify_screenshot_content(self, text):
        """Classify screenshot content based on extracted text"""
        if not text:
            return "Uncategorized"
        
        text_lower = text.lower()
        
        # Check for common keywords
        if any(word in text_lower for word in ['error', 'exception', 'failed', 'warning']):
            return "Errors"
        elif any(word in text_lower for word in ['code', 'function', 'class', 'import', 'def']):
            return "Code"
        elif any(word in text_lower for word in ['email', 'subject:', 'from:', 'to:']):
            return "Emails"
        elif any(word in text_lower for word in ['tweet', 'twitter', 'retweet', '@']):
            return "Social Media"
        elif any(word in text_lower for word in ['meeting', 'zoom', 'calendar', 'schedule']):
            return "Meetings"
        elif any(word in text_lower for word in ['receipt', 'invoice', 'payment', '$', 'total:']):
            return "Receipts"
        elif any(word in text_lower for word in ['article', 'blog', 'read', 'author']):
            return "Articles"
        else:
            return "General"
    
    def search_screenshots(self, query):
        """
        Search screenshots by OCR text
        """
        cursor = self.db.conn.cursor()
        
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT f.id, f.path, f.filename, f.modified_date, sm.extracted_text
            FROM files f
            JOIN screenshot_metadata sm ON f.id = sm.file_id
            WHERE f.is_screenshot = 1
              AND f.status = 'active'
              AND sm.extracted_text LIKE ?
            ORDER BY f.modified_date DESC
        """, (search_pattern,))
        
        columns = ['id', 'path', 'filename', 'modified_date', 'text']
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def get_screenshot_stats(self):
        """Get statistics about screenshots"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        # Total screenshots
        cursor.execute("""
            SELECT COUNT(*), SUM(size)
            FROM files
            WHERE is_screenshot = 1 AND status = 'active'
        """)
        
        row = cursor.fetchone()
        stats['total_count'] = row[0] or 0
        stats['total_size_mb'] = (row[1] or 0) / (1024 * 1024)
        
        # Screenshots with text
        cursor.execute("""
            SELECT COUNT(*)
            FROM screenshot_metadata
            WHERE has_text = 1
        """)
        stats['with_text'] = cursor.fetchone()[0] or 0
        
        # By source app
        cursor.execute("""
            SELECT source_app, COUNT(*)
            FROM screenshot_metadata
            GROUP BY source_app
        """)
        stats['by_app'] = dict(cursor.fetchall())
        
        # Recent screenshots (last 7 days)
        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE is_screenshot = 1
              AND status = 'active'
              AND modified_date > ?
        """, ((datetime.now().replace(day=datetime.now().day-7)).isoformat(),))
        
        stats['recent_7days'] = cursor.fetchone()[0] or 0
        
        return stats
    
    def find_duplicate_screenshots(self):
        """
        Find screenshots that might be duplicates
        (This is a simple version - visual similarity would be better)
        """
        cursor = self.db.conn.cursor()
        
        # Find screenshots with same size and similar dates
        cursor.execute("""
            SELECT f1.id, f1.path, f1.filename, f1.size, f1.modified_date,
                   f2.id, f2.path, f2.filename
            FROM files f1
            JOIN files f2 ON f1.size = f2.size 
                         AND f1.id < f2.id
                         AND ABS(JULIANDAY(f1.modified_date) - JULIANDAY(f2.modified_date)) < 0.01
            WHERE f1.is_screenshot = 1 
              AND f2.is_screenshot = 1
              AND f1.status = 'active'
              AND f2.status = 'active'
        """)
        
        duplicates = []
        for row in cursor.fetchall():
            duplicates.append({
                'file1_id': row[0],
                'file1_path': row[1],
                'file1_name': row[2],
                'size': row[3],
                'file2_id': row[5],
                'file2_path': row[6],
                'file2_name': row[7]
            })
        
        return duplicates


if __name__ == "__main__":
    # Test the screenshot manager
    from file_indexer import FileDatabase
    
    print("Testing Screenshot Manager...")
    print(f"OCR Available: {OCR_AVAILABLE}")
    
    db = FileDatabase()
    manager = ScreenshotManager(db)
    
    # Detect screenshots
    print("\n🔍 Detecting screenshots in database...")
    count = manager.detect_screenshots_in_database()
    print(f"Found and marked {count} screenshots")
    
    # Get stats
    print("\n📊 Screenshot Statistics:")
    stats = manager.get_screenshot_stats()
    print(f"Total screenshots: {stats['total_count']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"With extracted text: {stats['with_text']}")
    print(f"Recent (7 days): {stats['recent_7days']}")
    
    if stats['by_app']:
        print("\nBy app:")
        for app, count in stats['by_app'].items():
            print(f"  - {app}: {count}")
    
    db.close()
    print("\n✅ Screenshot manager test complete!")
