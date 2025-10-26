"""
Setup script for building File Organizer macOS app
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
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': False,  # Set to True for menu bar only app
        'NSHighResolutionCapable': True,
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
    ],
    'includes': [
        'file_indexer',
        'ai_tagger',
        'file_operations',
        'setup_wizard',
    ],
}

setup(
    name='File Organizer',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

