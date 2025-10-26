#!/usr/bin/env python3
"""
Visual Enhancements for File Organizer GUI
Thumbnails, color coding, progress tracking, notifications
"""

import os
from pathlib import Path

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# PyQt6 for GUI elements
try:
    from PyQt6.QtWidgets import QProgressBar
    from PyQt6.QtCore import QObject, pyqtSignal, QThread
    from PyQt6.QtGui import QPixmap, QIcon, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class ThumbnailGenerator:
    """Generate thumbnails for various file types"""
    
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.fileorganizer/thumbnails")
        
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.thumbnail_size = (128, 128)
        self.supported_images = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    def generate_thumbnail(self, file_path, force=False):
        """
        Generate thumbnail for file
        
        Args:
            file_path: Path to file
            force: Force regeneration even if cached
        
        Returns:
            Path to thumbnail or None
        """
        if not PIL_AVAILABLE:
            return None
        
        # Check cache first
        cache_key = Path(file_path).stem + '_' + str(hash(file_path))
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")
        
        if os.path.exists(cache_path) and not force:
            return cache_path
        
        # Generate thumbnail based on file type
        ext = Path(file_path).suffix.lower()
        
        if ext in self.supported_images:
            return self._generate_image_thumbnail(file_path, cache_path)
        
        elif ext == '.pdf':
            return self._generate_pdf_thumbnail(file_path, cache_path)
        
        else:
            # Return icon based on file type
            return self._get_file_type_icon(ext)
    
    def _generate_image_thumbnail(self, file_path, output_path):
        """Generate thumbnail for image file"""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Generate thumbnail
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(output_path, 'PNG')
                return output_path
        
        except Exception as e:
            print(f"Error generating image thumbnail: {e}")
            return None
    
    def _generate_pdf_thumbnail(self, file_path, output_path):
        """Generate thumbnail for PDF (first page)"""
        # Would need pdf2image library
        # For now, return PDF icon
        return self._get_file_type_icon('.pdf')
    
    def _get_file_type_icon(self, extension):
        """Get icon path for file type"""
        # These would be actual icon files in production
        icon_map = {
            '.pdf': 'pdf_icon',
            '.doc': 'word_icon',
            '.docx': 'word_icon',
            '.xls': 'excel_icon',
            '.xlsx': 'excel_icon',
            '.ppt': 'powerpoint_icon',
            '.pptx': 'powerpoint_icon',
            '.txt': 'text_icon',
            '.md': 'markdown_icon',
            '.py': 'python_icon',
            '.js': 'javascript_icon',
            '.html': 'html_icon',
            '.css': 'css_icon',
            '.zip': 'archive_icon',
            '.rar': 'archive_icon',
            '.mp4': 'video_icon',
            '.mov': 'video_icon',
            '.mp3': 'audio_icon',
            '.wav': 'audio_icon',
        }
        
        return icon_map.get(extension, 'generic_file_icon')
    
    def clear_cache(self):
        """Clear thumbnail cache"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)


class FileTypeColorCoder:
    """Color coding system for different file types"""
    
    def __init__(self):
        self.color_scheme = {
            # Documents
            'document': {'color': '#3b82f6', 'extensions': ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf']},
            # Spreadsheets
            'spreadsheet': {'color': '#10b981', 'extensions': ['.xls', '.xlsx', '.csv', '.numbers']},
            # Presentations
            'presentation': {'color': '#f59e0b', 'extensions': ['.ppt', '.pptx', '.key']},
            # Images
            'image': {'color': '#ec4899', 'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']},
            # Videos
            'video': {'color': '#8b5cf6', 'extensions': ['.mp4', '.mov', '.avi', '.mkv', '.wmv']},
            # Audio
            'audio': {'color': '#06b6d4', 'extensions': ['.mp3', '.wav', '.flac', '.aac', '.m4a']},
            # Archives
            'archive': {'color': '#f97316', 'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz']},
            # Code
            'code': {'color': '#14b8a6', 'extensions': ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.swift']},
            # Web
            'web': {'color': '#a855f7', 'extensions': ['.html', '.css', '.scss', '.jsx', '.tsx', '.vue']},
            # Default
            'other': {'color': '#6b7280', 'extensions': []}
        }
    
    def get_color_for_file(self, filename):
        """
        Get color code for file based on extension
        
        Returns:
            Hex color code (e.g., '#3b82f6')
        """
        ext = Path(filename).suffix.lower()
        
        for category, info in self.color_scheme.items():
            if ext in info['extensions']:
                return info['color']
        
        return self.color_scheme['other']['color']
    
    def get_category_for_file(self, filename):
        """Get category name for file"""
        ext = Path(filename).suffix.lower()
        
        for category, info in self.color_scheme.items():
            if ext in info['extensions']:
                return category
        
        return 'other'
    
    def get_qcolor_for_file(self, filename):
        """Get QColor object for PyQt6"""
        if not PYQT_AVAILABLE:
            return None
        
        hex_color = self.get_color_for_file(filename)
        return QColor(hex_color)


class ProgressTracker(QObject if PYQT_AVAILABLE else object):
    """Track progress of long-running operations"""
    
    if PYQT_AVAILABLE:
        progress_updated = pyqtSignal(int, int, str)  # current, total, message
        operation_complete = pyqtSignal(dict)  # result
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.current = 0
        self.total = 0
        self.message = ""
    
    def start(self, total, message="Processing..."):
        """Start tracking progress"""
        self.total = total
        self.current = 0
        self.message = message
        self._emit_progress()
    
    def update(self, current=None, message=None):
        """Update progress"""
        if current is not None:
            self.current = current
        if message is not None:
            self.message = message
        self._emit_progress()
    
    def increment(self, message=None):
        """Increment progress by 1"""
        self.current += 1
        if message:
            self.message = message
        self._emit_progress()
    
    def complete(self, result=None):
        """Mark operation as complete"""
        self.current = self.total
        self._emit_progress()
        
        if PYQT_AVAILABLE and hasattr(self, 'operation_complete'):
            self.operation_complete.emit(result or {})
    
    def _emit_progress(self):
        """Emit progress signal if PyQt is available"""
        if PYQT_AVAILABLE and hasattr(self, 'progress_updated'):
            self.progress_updated.emit(self.current, self.total, self.message)
    
    def get_percentage(self):
        """Get progress as percentage"""
        if self.total == 0:
            return 0
        return int((self.current / self.total) * 100)


class NotificationHelper:
    """Helper for macOS notifications"""
    
    def __init__(self):
        self.app_name = "File Organizer"
    
    def send_notification(self, title, message, subtitle=None):
        """
        Send macOS notification
        
        Args:
            title: Notification title
            message: Notification message
            subtitle: Optional subtitle
        """
        try:
            import subprocess
            
            # Use osascript for macOS notifications
            script = f'display notification "{message}" with title "{self.app_name}" subtitle "{title}"'
            
            if subtitle:
                script = f'display notification "{message}" with title "{self.app_name}" subtitle "{subtitle}"'
            
            subprocess.run(['osascript', '-e', script], check=False, capture_output=True)
        
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def notify_completion(self, operation, count=None):
        """Send completion notification"""
        message = f"{operation} completed"
        if count:
            message += f" ({count} items)"
        
        self.send_notification("Operation Complete", message)
    
    def notify_reminder(self, file_name, message):
        """Send reminder notification"""
        self.send_notification(
            "File Reminder",
            message,
            subtitle=file_name
        )
    
    def notify_nudge(self, message):
        """Send nudge notification"""
        self.send_notification("Smart Suggestion", message)


class DarkModeHelper:
    """Helper for dark mode support"""
    
    def __init__(self):
        self.is_dark_mode = self._detect_dark_mode()
    
    def _detect_dark_mode(self):
        """Detect if macOS is in dark mode"""
        try:
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and 'Dark' in result.stdout
        except:
            return False
    
    def get_background_color(self):
        """Get appropriate background color"""
        return '#1e1e1e' if self.is_dark_mode else '#ffffff'
    
    def get_text_color(self):
        """Get appropriate text color"""
        return '#ffffff' if self.is_dark_mode else '#000000'
    
    def get_border_color(self):
        """Get appropriate border color"""
        return '#404040' if self.is_dark_mode else '#d1d5db'
    
    def get_accent_color(self):
        """Get appropriate accent color"""
        return '#3b82f6' if self.is_dark_mode else '#2563eb'
    
    def apply_dark_mode_stylesheet(self):
        """Get PyQt6 stylesheet for dark mode"""
        if not self.is_dark_mode:
            return ""
        
        return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QListWidget {
            background-color: #2d2d2d;
            border: 1px solid #404040;
        }
        QTextEdit {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #404040;
        }
        QPushButton {
            background-color: #3b82f6;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #2563eb;
        }
        QLineEdit {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #404040;
            padding: 6px;
            border-radius: 4px;
        }
        """


if __name__ == "__main__":
    print("Testing Visual Enhancements...")
    print(f"PIL Available: {PIL_AVAILABLE}")
    print(f"PyQt6 Available: {PYQT_AVAILABLE}")
    
    # Test color coder
    print("\n🎨 Testing Color Coder:")
    coder = FileTypeColorCoder()
    test_files = ['document.pdf', 'data.xlsx', 'presentation.pptx', 'image.jpg', 'code.py']
    for file in test_files:
        color = coder.get_color_for_file(file)
        category = coder.get_category_for_file(file)
        print(f"  {file}: {category} → {color}")
    
    # Test thumbnail generator
    print("\n📸 Testing Thumbnail Generator:")
    thumbnailer = ThumbnailGenerator()
    print(f"  Cache dir: {thumbnailer.cache_dir}")
    print(f"  Supported: {', '.join(thumbnailer.supported_images)}")
    
    # Test notifications
    print("\n🔔 Testing Notifications:")
    notifier = NotificationHelper()
    print("  Notification helper initialized")
    # notifier.send_notification("Test", "This is a test notification")
    
    # Test dark mode
    print("\n🌓 Testing Dark Mode:")
    dark_mode = DarkModeHelper()
    print(f"  Dark mode active: {dark_mode.is_dark_mode}")
    print(f"  Background: {dark_mode.get_background_color()}")
    print(f"  Text: {dark_mode.get_text_color()}")
    
    # Test progress tracker
    print("\n📊 Testing Progress Tracker:")
    tracker = ProgressTracker()
    tracker.start(100, "Test operation")
    tracker.update(50, "Halfway done")
    print(f"  Progress: {tracker.get_percentage()}%")
    
    print("\n✅ Visual enhancements module ready!")

