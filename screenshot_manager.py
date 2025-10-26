#!/usr/bin/env python3
"""
Screenshot Manager
Special handling for screenshots with OCR and smart naming
"""

import os
import re
from datetime import datetime
from pathlib import Path


class ScreenshotManager:
    """Manage screenshots with OCR and organization"""
    
    def __init__(self, file_db, ocr_processor=None):
        self.db = file_db
        self.ocr = ocr_processor
    
    def is_screenshot(self, filepath):
        """Detect if file is a screenshot"""
        filename = Path(filepath).name.lower()
        
        patterns = [
            r'^screenshot',
            r'^screen[ _]shot',
            r'^scr_\d+',
            r'^img_\d{8}',
            r'screen.*\d{4}-\d{2}-\d{2}',
        ]
        
        return any(re.search(pattern, filename) for pattern in patterns)
    
    def get_all_screenshots(self):
        """Get all screenshots from database"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, path, filename, created_date, ocr_text
            FROM files
            WHERE is_screenshot = 1
            AND status = 'active'
            AND hide_from_app = 0
            ORDER BY created_date DESC
        """)
        
        screenshots = []
        for row in cursor.fetchall():
            screenshots.append({
                'id': row[0],
                'path': row[1],
                'filename': row[2],
                'created': row[3],
                'ocr_text': row[4]
            })
        
        return screenshots
    
    def process_screenshot(self, file_id, filepath):
        """Process a screenshot: OCR + smart naming"""
        # Mark as screenshot
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE files SET is_screenshot = 1 WHERE id = ?", (file_id,))
        self.db.conn.commit()
        
        # Run OCR if processor available
        if self.ocr:
            text = self.ocr.process_file(file_id, filepath)
            if text:
                return {
                    'file_id': file_id,
                    'ocr_success': True,
                    'text_length': len(text)
                }
        
        return {
            'file_id': file_id,
            'ocr_success': False
        }
    
    def suggest_rename(self, file_id):
        """Suggest better filename based on OCR content"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT filename, ocr_text, created_date
            FROM files
            WHERE id = ?
        """, (file_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        filename, ocr_text, created = result
        
        if not ocr_text:
            return None
        
        # Extract keywords from OCR text
        words = ocr_text.lower().split()
        keywords = [w for w in words if len(w) > 4][:3]
        
        # Create suggestion
        date_str = created[:10] if created else datetime.now().strftime("%Y-%m-%d")
        keyword_part = "-".join(keywords) if keywords else "screenshot"
        
        ext = Path(filename).suffix
        suggested = f"Screenshot-{date_str}-{keyword_part}{ext}"
        
        return suggested
    
    def cleanup_old_screenshots(self, days=30, dry_run=True):
        """Clean up old screenshots"""
        from datetime import timedelta
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, path, created_date
            FROM files
            WHERE is_screenshot = 1
            AND created_date < ?
            AND status = 'active'
        """, (cutoff,))
        
        old_screenshots = cursor.fetchall()
        
        if dry_run:
            return {
                'would_clean': len(old_screenshots),
                'dry_run': True
            }
        else:
            # Mark as deleted
            for file_id, *_ in old_screenshots:
                cursor.execute("""
                    UPDATE files SET status = 'archived' WHERE id = ?
                """, (file_id,))
            
            self.db.conn.commit()
            
            return {
                'cleaned': len(old_screenshots),
                'dry_run': False
            }
    
    def search_screenshots(self, query):
        """Search within screenshot OCR text"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, ocr_text, created_date
            FROM files
            WHERE is_screenshot = 1
            AND ocr_text LIKE ?
            AND status = 'active'
            AND hide_from_app = 0
            ORDER BY created_date DESC
            LIMIT 20
        """, (f'%{query}%',))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'path': row[2],
                'ocr_preview': row[3][:100] + '...' if row[3] and len(row[3]) > 100 else row[3],
                'created': row[4]
            })
        
        return results


if __name__ == "__main__":
    print("📸 Screenshot Manager")
    print("="*60)
    
    from file_indexer import FileDatabase
    from ocr_processor import OCRProcessor
    
    db = FileDatabase()
    ocr = OCRProcessor(db)
    screenshots = ScreenshotManager(db, ocr)
    
    # Find all screenshots
    all_screenshots = screenshots.get_all_screenshots()
    print(f"\n📷 Found {len(all_screenshots)} screenshot(s)")
    
    if all_screenshots:
        print("\n Recent screenshots:\n")
        for s in all_screenshots[:5]:
            print(f"   • {s['filename']}")
            print(f"     Created: {s['created'][:10] if s['created'] else 'unknown'}")
            if s['ocr_text']:
                preview = s['ocr_text'][:60] + '...' if len(s['ocr_text']) > 60 else s['ocr_text']
                print(f"     OCR: {preview}")
            print()
    
    # Check for cleanup
    cleanup_info = screenshots.cleanup_old_screenshots(days=30, dry_run=True)
    if cleanup_info['would_clean'] > 0:
        print(f"\n💡 {cleanup_info['would_clean']} screenshots older than 30 days could be cleaned")
    
    db.close()

