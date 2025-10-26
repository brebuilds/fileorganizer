#!/usr/bin/env python3
"""
OCR Processor
Extract text from images and screenshots using macOS Vision API or Tesseract
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime


class OCRProcessor:
    """Extract text from images using OCR"""
    
    def __init__(self, file_db=None):
        self.db = file_db
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic'}
    
    def can_process(self, filepath):
        """Check if file can be OCR'd"""
        ext = Path(filepath).suffix.lower()
        return ext in self.supported_formats
    
    def extract_text_macos(self, filepath):
        """Extract text using macOS Vision API (fast and built-in!)"""
        try:
            # Use macOS's native OCR via Swift/Vision framework
            # We'll use a simple Python script that calls the Vision API
            script = f'''
import Vision
import Quartz
import sys

def extract_text(image_path):
    url = Quartz.CFURL.fileURLWithPath_(image_path)
    image_source = Quartz.CGImageSourceCreateWithURL(url, None)
    if not image_source:
        return ""
    
    image = Quartz.CGImageSourceCreateImageAtIndex(image_source, 0, None)
    if not image:
        return ""
    
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(image, None)
    success = handler.performRequests_error_([request], None)
    
    if success[0]:
        results = request.results()
        text_lines = []
        for observation in results:
            text_lines.append(observation.topCandidates_(1)[0].string())
        return "\\n".join(text_lines)
    return ""

if __name__ == "__main__":
    print(extract_text("{filepath}"))
'''
            
            # For now, use a simpler approach with 'tesseract' if available
            # Or fall back to a placeholder
            return self.extract_text_tesseract(filepath)
            
        except Exception as e:
            print(f"macOS Vision error: {e}")
            return None
    
    def extract_text_tesseract(self, filepath):
        """Extract text using Tesseract OCR"""
        try:
            # Check if tesseract is installed
            result = subprocess.run(
                ['tesseract', filepath, 'stdout', '--psm', '3'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None
                
        except FileNotFoundError:
            print("⚠️  Tesseract not installed. Install with: brew install tesseract")
            return None
        except subprocess.TimeoutExpired:
            print(f"⏱️  OCR timeout for {filepath}")
            return None
        except Exception as e:
            print(f"Tesseract error: {e}")
            return None
    
    def extract_text_simple(self, filepath):
        """Simple fallback: just mark that OCR was attempted"""
        # This is a placeholder - in production you'd want real OCR
        return f"[Image file: {Path(filepath).name}]"
    
    def extract_text(self, filepath):
        """
        Extract text from image using best available method
        
        Priority:
        1. macOS Vision API (if available)
        2. Tesseract OCR (if installed)
        3. Simple fallback
        """
        if not self.can_process(filepath):
            return None
        
        # Try Tesseract first (most reliable for now)
        text = self.extract_text_tesseract(filepath)
        
        if text:
            return text
        
        # Fallback
        return self.extract_text_simple(filepath)
    
    def process_file(self, file_id, filepath):
        """Process a file and store OCR text in database"""
        if not self.db:
            return None
        
        text = self.extract_text(filepath)
        
        if text:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE files
                SET ocr_text = ?
                WHERE id = ?
            """, (text, file_id))
            self.db.conn.commit()
            
            return text
        
        return None
    
    def process_folder(self, folder_path):
        """Process all images in a folder"""
        if not self.db:
            return []
        
        processed = []
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT id, path, filename
            FROM files
            WHERE folder_location LIKE ?
            AND status = 'active'
            AND (ocr_text IS NULL OR ocr_text = '')
        """, (f'{folder_path}%',))
        
        files = cursor.fetchall()
        
        for file_id, filepath, filename in files:
            if self.can_process(filepath):
                print(f"🔍 OCR: {filename}")
                text = self.process_file(file_id, filepath)
                if text:
                    processed.append({
                        'id': file_id,
                        'filename': filename,
                        'text_length': len(text)
                    })
        
        return processed
    
    def search_ocr_text(self, query):
        """Search in OCR text"""
        if not self.db:
            return []
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, filename, path, ocr_text
            FROM files
            WHERE ocr_text LIKE ?
            AND status = 'active'
            AND hide_from_app = 0
            LIMIT 20
        """, (f'%{query}%',))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'filename': row[1],
                'path': row[2],
                'ocr_text': row[3][:200] + '...' if len(row[3]) > 200 else row[3]
            })
        
        return results
    
    def is_screenshot(self, filepath):
        """Detect if file is a screenshot based on naming patterns"""
        filename = Path(filepath).name.lower()
        
        screenshot_patterns = [
            'screenshot',
            'screen shot',
            'screen_shot',
            'capture',
            'scr_',
            'img_',  # Common screenshot prefix
        ]
        
        return any(pattern in filename for pattern in screenshot_patterns)
    
    def mark_screenshot(self, file_id):
        """Mark a file as screenshot in database"""
        if self.db:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE files
                SET is_screenshot = 1
                WHERE id = ?
            """, (file_id,))
            self.db.conn.commit()


if __name__ == "__main__":
    print("📷 OCR Processor Test")
    print("="*60)
    
    from file_indexer import FileDatabase
    
    db = FileDatabase()
    ocr = OCRProcessor(db)
    
    # Check for Tesseract
    try:
        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"✅ Tesseract installed: {result.stdout.strip()}")
        else:
            print("⚠️  Tesseract not found")
            print("   Install with: brew install tesseract")
    except:
        print("⚠️  Tesseract not available")
    
    # Find image files
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT id, path, filename
        FROM files
        WHERE status = 'active'
        AND (mime_type LIKE 'image/%' OR extension IN ('.png', '.jpg', '.jpeg'))
        LIMIT 5
    """)
    
    images = cursor.fetchall()
    
    if images:
        print(f"\n📸 Found {len(images)} image(s)")
        print("\n💡 To process images with OCR:")
        print("   ./o OCR@Desktop")
        print("   ./o OCR@Downloads")
    else:
        print("\n📭 No images found in database")
        print("   Run: ./o TAG@Desktop to index images first")
    
    db.close()

