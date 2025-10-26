"""
Setup script for building File Organizer macOS app v4.0
"""

from setuptools import setup

APP = ['file_organizer_app.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,  # Add icon file path here when you have one
    'plist': {
        'CFBundleName': 'File Organizer',
        'CFBundleDisplayName': 'File Organizer',
        'CFBundleIdentifier': 'com.fileorganizer.app',
        'CFBundleVersion': '4.0.0',
        'CFBundleShortVersionString': '4.0.0',
        'LSUIElement': False,  # Set to True for menu bar only app
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,  # Dark mode support
    },
    'packages': [
        'PyQt6',
        'ollama',
        'PyPDF2',
        'PIL',
        'sqlite3',
        'json',
        'hashlib',
        'mimetypes',
        'datetime',
        'pathlib',
        'numpy',
        'httpx',
        'requests',
        'bs4',  # BeautifulSoup4
        'pytesseract',
        'watchdog',
        'dateutil',
    ],
    'includes': [
        # Core modules
        'file_indexer',
        'ai_tagger',
        'file_operations',
        'setup_wizard',
        'conversational_ai',
        'temporal_tracker',
        'vector_store',
        'graph_store',
        'export_manager',
        
        # v4.0 New modules
        'reminder_system',
        'screenshot_manager',
        'duplicate_detector',
        'smart_folders',
        'bulk_operations',
        'trash_manager',
        'aging_manager',
        'bookmark_manager',
        'external_tools',
        'mobile_companion',
        'performance_optimizer',
        'enhanced_summarizer',
        'visual_enhancements',
        'gui_enhancements',
        
        # Integration modules
        'openai_integration',
        'automation_api',
        'hazel_integration',
        'ocr_processor',
        'suggestions_engine',
        'file_watcher',
        'relationship_visualizer',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'test',
        'unittest',
        'doctest',
        'setuptools',
        'distutils',
        'pkg_resources',
        'wheel',
    ],
    'strip': False,  # Don't strip debug symbols (helps with debugging)
    'semi_standalone': False,  # Full standalone mode
}

setup(
    name='File Organizer',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

