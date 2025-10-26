# 📦 Distribution Guide - File Organizer v4.0

Quick guide for packaging and distributing the File Organizer.

---

## 🎯 Distribution Options

### Option 1: Source Distribution (Easiest)

**Best for:** Sharing with other developers, personal use

```bash
# Clone and run
git clone https://github.com/brebuilds/fileorganizer.git
cd fileorganizer
pip install -r requirements.txt
python file_organizer_app.py
```

**Pros:**
- Simple and reliable
- Easy to update
- Full access to source

**Cons:**
- Requires Python and dependencies
- Not a "double-click" app

---

### Option 2: macOS App Bundle (py2app)

**Best for:** macOS-only distribution, native feel

```bash
./build_app.sh
```

**Status:** Build infrastructure is ready. May need tweaking for your specific Python/macOS version.

**Known Issues:**
- Complex dependency tree (PyQt6, numpy, etc.)
- Setuptools vendored packages can conflict
- Large app size (~200-300 MB)

**Workarounds:**
- Use PyInstaller instead (see below)
- Use Alias mode for development
- Exclude problematic packages

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for complete documentation.

---

### Option 3: PyInstaller (Alternative)

**Best for:** Cross-platform, simpler builds

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --name="File Organizer" \
            --windowed \
            --add-data="*.py:." \
            --hidden-import=PyQt6 \
            --hidden-import=ollama \
            --hidden-import=PIL \
            --hidden-import=numpy \
            --collect-all PyQt6 \
            file_organizer_app.py

# App will be in dist/
open dist
```

**Pros:**
- Often handles complex dependencies better
- Good documentation and community
- Works on Windows/Linux too

**Cons:**
- Still large app size
- May need additional `--hidden-import` flags

---

### Option 4: Launcher Script (Recommended for Now)

**Best for:** Quick distribution, easy maintenance

Create a simple launcher that sets up the environment:

```bash
#!/bin/bash
# File: File Organizer.command

cd "$(dirname "$0")"

# Check for venv
if [ ! -d "venv" ]; then
    echo "Setting up File Organizer..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the app
python file_organizer_app.py
```

Make it executable:
```bash
chmod +x "File Organizer.command"
```

**Pros:**
- Simple and reliable
- Small download (~50KB + dependencies)
- Easy to update (just `git pull`)
- No build issues

**Cons:**
- Requires Python 3.10+
- Not a "real" .app bundle

---

## 📤 Distribution Methods

### GitHub Releases

```bash
# Tag the release
git tag -a v4.0.0 -m "File Organizer v4.0 - 16 new features!"
git push origin v4.0.0

# Create release with GitHub CLI
gh release create v4.0.0 \
                  --title "File Organizer v4.0" \
                  --notes "See README.md for details"
                  
# If you have a .app or DMG:
gh release upload v4.0.0 FileOrganizer-v4.0.dmg
```

### Homebrew Tap

Create a Formula:
```ruby
class FileOrganizer < Formula
  desc "ADHD-friendly AI-powered file organizer"
  homepage "https://github.com/brebuilds/fileorganizer"
  url "https://github.com/brebuilds/fileorganizer/archive/v4.0.0.tar.gz"
  sha256 "..."  # Calculate with: shasum -a 256 *.tar.gz
  
  depends_on "python@3.13"
  depends_on "ollama"
  
  def install
    virtualenv_install_with_resources
  end
  
  test do
    system "#{bin}/organize", "HELP"
  end
end
```

### Direct Download

Package as ZIP:
```bash
# Create distribution package
mkdir FileOrganizer-v4.0
cp -R *.py requirements.txt README.md FileOrganizer-v4.0/
zip -r FileOrganizer-v4.0.zip FileOrganizer-v4.0/
```

---

## 🚀 Recommended Distribution Strategy

**For v4.0, I recommend:**

1. **GitHub Release** with source code
2. **Launcher script** (`launch.command`) for easy macOS use
3. **Clear README** with installation instructions
4. **Optional:** DMG with app bundle (when py2app issues are resolved)

**Why?**
- Reliable and works for everyone
- Easy to update and maintain
- No complex build issues
- Users who want .app can build themselves

---

## 📝 Creating a Release

### 1. Prepare Release Notes

Create `RELEASE_NOTES.md`:
```markdown
# File Organizer v4.0 🎉

## What's New

- 16 major new features!
- Smart reminders, screenshots, duplicates, bulk ops, and more
- See NEW_FEATURES_GUIDE.md for complete list

## Installation

### Quick Start (macOS)
1. Download and unzip
2. Double-click `launch.command`
3. Install Ollama: https://ollama.ai
4. Run: `ollama pull llama3.2:3b`

### Full Install
```bash
pip install -r requirements.txt
python file_organizer_app.py
```

## Requirements
- macOS 13.0+ (or Linux/Windows with Python)
- Python 3.10+
- Ollama (for AI features)

## Links
- Documentation: [README.md](README.md)
- Features Guide: [NEW_FEATURES_GUIDE.md](NEW_FEATURES_GUIDE.md)
- Issues: https://github.com/brebuilds/fileorganizer/issues
```

### 2. Create the Release

```bash
# Tag
git tag -a v4.0.0 -m "Version 4.0 - Massive Feature Update"
git push origin v4.0.0

# Release on GitHub
gh release create v4.0.0 \
  --title "🎉 File Organizer v4.0" \
  --notes-file RELEASE_NOTES.md \
  --latest
```

### 3. Announce

- Update README.md badges
- Tweet/post on social media
- Update project website

---

## 🔮 Future: Mac App Store

To distribute on the Mac App Store, you'll need:

1. **Apple Developer Account** ($99/year)
2. **Code signing certificate**
3. **App sandboxing**
4. **Entitlements file**
5. **App Store metadata**

This is a bigger project but totally doable! The current build infrastructure is a good starting point.

---

## 💡 Tips

### Reducing App Size

If building with py2app/PyInstaller:

```python
# Exclude unnecessary packages
'excludes': [
    'test', 'unittest', 'doctest',
    'tkinter', 'matplotlib', 'scipy', 'pandas',
    'PIL.ImageTk',  # Tkinter integration
    'numpy.tests',  # Test files
]
```

### Testing Builds

Always test on a clean macOS install or VM:
```bash
# Create test VM with UTM or Parallels
# Install only:
# - macOS
# - Ollama
# Then try your .app
```

### User Feedback

Make it easy for users to report issues:
- Include version number in app
- Add "Report Issue" menu item
- Log errors to `~/Library/Logs/FileOrganizer/`

---

## 📚 Resources

- [py2app Documentation](https://py2app.readthedocs.io/)
- [PyInstaller Manual](https://pyinstaller.org/)
- [Apple Distribution Guide](https://developer.apple.com/documentation/xcode/distributing-your-app-to-registered-devices)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)

---

## ✅ Current Status

**v4.0 Distribution:**
- ✅ Source code on GitHub
- ✅ Comprehensive README
- ✅ Build scripts ready
- ✅ `.gitignore` configured
- ✅ CLI working great
- ⚠️  macOS app bundle (needs testing)
- 📋 DMG installer (pending)
- 📋 Homebrew formula (pending)
- 📋 Mac App Store (future)

---

**Ready to share? Just push to GitHub and create a release! 🚀**

Users can clone and run immediately with the launcher script.

