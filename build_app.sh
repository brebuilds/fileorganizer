#!/bin/bash
set -e

echo "🚀 Building File Organizer v4.0.app..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing build dependencies..."
pip install --upgrade pip setuptools wheel py2app > /dev/null 2>&1

echo "📥 Installing app dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "🔨 Building macOS app bundle..."
python setup.py py2app

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    
    # Get app size
    APP_SIZE=$(du -sh "dist/File Organizer.app" | cut -f1)
    echo "📦 App size: $APP_SIZE"
    echo "📍 Location: dist/File Organizer.app"
    echo ""
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo "⚠️  WARNING: Ollama not detected!"
        echo "   Install from: https://ollama.ai"
        echo ""
    fi
    
    # Optional: Create DMG
    read -p "Create DMG installer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📀 Creating DMG installer..."
        DMG_NAME="FileOrganizer-v4.0.dmg"
        
        # Remove old DMG if exists
        rm -f "$DMG_NAME"
        
        # Create DMG
        hdiutil create -volname "File Organizer v4.0" \
                       -srcfolder "dist/File Organizer.app" \
                       -ov -format UDZO \
                       "$DMG_NAME"
        
        if [ $? -eq 0 ]; then
            DMG_SIZE=$(du -sh "$DMG_NAME" | cut -f1)
            echo "✅ DMG created: $DMG_NAME ($DMG_SIZE)"
        fi
    fi
    
    echo ""
    echo "🎉 All done! Opening dist folder..."
    open dist
else
    echo ""
    echo "❌ Build failed. Check errors above."
    exit 1
fi
