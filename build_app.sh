#!/bin/bash

echo "Building File Organizer.app..."

source venv/bin/activate

pip install py2app 2>/dev/null

rm -rf build dist

python setup.py py2app

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "Your app is at: dist/File Organizer.app"
    echo ""
    open dist
else
    echo ""
    echo "❌ Build failed. Check errors above."
fi
