# 🍎 Building File Organizer for macOS

Complete guide to building a standalone macOS application bundle for File Organizer v4.0.

---

## 🎯 Overview

The File Organizer can be packaged as a native macOS `.app` bundle that users can:
- Double-click to launch
- Drag to Applications folder
- Distribute via DMG installer
- Code sign and notarize for distribution

---

## 📋 Prerequisites

### Required
- **macOS** 13.0+ (Ventura or later recommended)
- **Python** 3.10+ (3.13 recommended)
- **Xcode Command Line Tools**
  ```bash
  xcode-select --install
  ```

### Optional
- **Ollama** - For AI features (required at runtime)
  ```bash
  # Install from ollama.ai or:
  brew install ollama
  ollama pull llama3.2:3b
  ```
- **Tesseract** - For OCR in screenshots
  ```bash
  brew install tesseract
  ```

---

## 🚀 Quick Build

### One-Command Build

```bash
chmod +x build_app.sh
./build_app.sh
```

This will:
1. Create/activate virtual environment
2. Install all dependencies
3. Clean previous builds
4. Build the .app bundle
5. Optionally create a DMG installer
6. Open the dist folder

### Manual Build

```bash
# 1. Set up environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install py2app

# 3. Clean and build
rm -rf build dist
python setup.py py2app

# 4. Your app is ready!
open dist
```

---

## 📦 What Gets Built

### File Structure
```
dist/
└── File Organizer.app/
    ├── Contents/
    │   ├── MacOS/
    │   │   └── File Organizer           # Executable
    │   ├── Resources/
    │   │   ├── lib/
    │   │   │   └── python3.x/          # Python runtime
    │   │   │       └── ...              # All dependencies
    │   │   └── ...
    │   └── Info.plist                    # App metadata
    └── ...
```

### Size
- **Expected size**: ~150-250 MB
- Includes:
  - Python runtime
  - PyQt6 framework
  - All dependencies
  - Your application code

---

## 🎨 Customization

### Adding an Icon

1. Create or obtain a 1024x1024 PNG icon
2. Convert to .icns format:
   ```bash
   # Create iconset folder
   mkdir FileOrganizer.iconset
   
   # Generate required sizes (use sips or other tool)
   sips -z 16 16     icon.png --out FileOrganizer.iconset/icon_16x16.png
   sips -z 32 32     icon.png --out FileOrganizer.iconset/icon_16x16@2x.png
   sips -z 32 32     icon.png --out FileOrganizer.iconset/icon_32x32.png
   sips -z 64 64     icon.png --out FileOrganizer.iconset/icon_32x32@2x.png
   sips -z 128 128   icon.png --out FileOrganizer.iconset/icon_128x128.png
   sips -z 256 256   icon.png --out FileOrganizer.iconset/icon_128x128@2x.png
   sips -z 256 256   icon.png --out FileOrganizer.iconset/icon_256x256.png
   sips -z 512 512   icon.png --out FileOrganizer.iconset/icon_256x256@2x.png
   sips -z 512 512   icon.png --out FileOrganizer.iconset/icon_512x512.png
   sips -z 1024 1024 icon.png --out FileOrganizer.iconset/icon_512x512@2x.png
   
   # Convert to .icns
   iconutil -c icns FileOrganizer.iconset -o FileOrganizer.icns
   ```

3. Update `setup.py`:
   ```python
   'iconfile': 'FileOrganizer.icns',
   ```

### Menu Bar Only Mode

To make the app show only in the menu bar (no dock icon):

Edit `setup.py`:
```python
'LSUIElement': True,  # Change to True
```

### Version Numbers

Update in `setup.py`:
```python
'CFBundleVersion': '4.0.0',
'CFBundleShortVersionString': '4.0.0',
```

---

## 📀 Creating a DMG Installer

### Automatic (via build script)

Run `./build_app.sh` and answer `y` when prompted.

### Manual

```bash
# Basic DMG
hdiutil create -volname "File Organizer v4.0" \
               -srcfolder "dist/File Organizer.app" \
               -ov -format UDZO \
               FileOrganizer-v4.0.dmg

# Advanced DMG with background and layout
# (requires additional setup - see below)
```

### Custom DMG with Background Image

1. **Create a template folder:**
   ```bash
   mkdir dmg_template
   cp -R "dist/File Organizer.app" dmg_template/
   ln -s /Applications dmg_template/Applications
   ```

2. **Create background image** (600x400px recommended)
   - Save as `background.png`

3. **Build DMG:**
   ```bash
   # Create writable DMG
   hdiutil create -volname "File Organizer" \
                  -srcfolder dmg_template \
                  -ov -format UDRW \
                  temp.dmg
   
   # Mount and customize
   hdiutil attach temp.dmg
   # ... customize appearance in Finder ...
   hdiutil detach "/Volumes/File Organizer"
   
   # Convert to compressed final DMG
   hdiutil convert temp.dmg \
                   -format UDZO \
                   -o FileOrganizer-v4.0.dmg
   rm temp.dmg
   ```

---

## 🔐 Code Signing & Notarization

**Required for distribution outside of personal use.**

### 1. Get Apple Developer Account

- Sign up at [developer.apple.com](https://developer.apple.com)
- Cost: $99/year

### 2. Create Certificates

```bash
# List available signing identities
security find-identity -v -p codesigning
```

### 3. Sign the App

```bash
codesign --deep --force --verify --verbose \
         --sign "Developer ID Application: Your Name (XXXXXXXXXX)" \
         "dist/File Organizer.app"
```

### 4. Verify Signature

```bash
codesign --verify --verbose "dist/File Organizer.app"
spctl -a -vv "dist/File Organizer.app"
```

### 5. Notarize with Apple

```bash
# Create DMG first
hdiutil create -volname "File Organizer v4.0" \
               -srcfolder "dist/File Organizer.app" \
               -ov -format UDZO \
               FileOrganizer-v4.0.dmg

# Submit for notarization
xcrun notarytool submit FileOrganizer-v4.0.dmg \
                       --apple-id "your@email.com" \
                       --password "app-specific-password" \
                       --team-id "XXXXXXXXXX" \
                       --wait

# Staple the notarization ticket
xcrun stapler staple FileOrganizer-v4.0.dmg
```

---

## 🧪 Testing the Build

### Basic Tests

```bash
# Check if app launches
open "dist/File Organizer.app"

# Check dependencies are included
otool -L "dist/File Organizer.app/Contents/MacOS/File Organizer"

# Check Info.plist
plutil -p "dist/File Organizer.app/Contents/Info.plist"

# Verify code signature (if signed)
codesign --verify --verbose "dist/File Organizer.app"
```

### Runtime Tests

1. **Launch the app**
   - Should open without errors
   - Menu bar icon should appear

2. **Test AI features**
   - Requires Ollama to be running
   - Check conversational interface

3. **Test file operations**
   - Index a folder
   - Search for files
   - Organize files

4. **Test new v4.0 features**
   - Smart folders
   - Reminders
   - Bookmarks
   - etc.

---

## 🐛 Troubleshooting

### Build Fails

**Issue**: `ModuleNotFoundError`
```bash
# Solution: Add missing module to setup.py includes
```

**Issue**: `ImportError` for PyQt6
```bash
# Solution: Ensure PyQt6 is in packages list
pip install --upgrade PyQt6
```

**Issue**: Build succeeds but app won't launch
```bash
# Check console logs
open /Applications/Utilities/Console.app
# Filter for "File Organizer"
```

### App Won't Launch

**Issue**: "File Organizer is damaged and can't be opened"
```bash
# Remove quarantine attribute
xattr -cr "dist/File Organizer.app"
```

**Issue**: Python errors on launch
```bash
# Check if all dependencies are included in setup.py
# Look at Console.app for specific missing modules
```

### Large App Size

**Issue**: App is >500 MB
```bash
# Add more packages to excludes in setup.py:
'excludes': [
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    'test',
    'unittest',
]
```

### Ollama Not Found

**Issue**: AI features don't work in bundled app
```bash
# Ollama must be installed separately
# Users need to:
brew install ollama
ollama pull llama3.2:3b
```

---

## 📤 Distribution

### For Personal Use
- Just copy the `.app` to Applications folder
- Or send the `.app` directly (may be flagged by Gatekeeper)

### For Public Distribution
1. **Code sign** the app
2. **Notarize** with Apple
3. **Create DMG** installer
4. Upload to:
   - GitHub Releases
   - Your website
   - Mac App Store (requires additional setup)

### GitHub Release

```bash
# Create a release on GitHub
gh release create v4.0.0 \
                  FileOrganizer-v4.0.dmg \
                  --title "File Organizer v4.0" \
                  --notes "Release notes here..."
```

---

## 🎯 Alternative: PyInstaller

If py2app gives you trouble, try PyInstaller:

```bash
pip install pyinstaller

pyinstaller --name="File Organizer" \
            --windowed \
            --icon=FileOrganizer.icns \
            --add-data="file_indexer.py:." \
            --add-data="ai_tagger.py:." \
            --hidden-import=PyQt6 \
            --hidden-import=ollama \
            file_organizer_app.py
```

---

## 📚 Resources

- [py2app Documentation](https://py2app.readthedocs.io/)
- [PyInstaller Manual](https://pyinstaller.org/)
- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [DMG Creation Guide](https://www.ej-technologies.com/resources/install4j/help/doc/concepts/dmgStyling.html)

---

## ✅ Checklist

Before distributing:

- [ ] App builds without errors
- [ ] App launches successfully
- [ ] All features work in bundled app
- [ ] Ollama dependency documented for users
- [ ] App icon added (optional)
- [ ] Version numbers updated
- [ ] Code signed (for distribution)
- [ ] Notarized (for distribution)
- [ ] DMG created
- [ ] DMG tested on clean macOS install
- [ ] Release notes written
- [ ] GitHub release created

---

## 🎉 Success!

Once built, users can:
1. Download the DMG
2. Open and drag to Applications
3. Install Ollama (if not already)
4. Launch File Organizer
5. Enjoy AI-powered file organization!

---

**Need help?** Open an issue on GitHub!

**Made with 🧠 and ✨ for ADHD brains!**

