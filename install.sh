#!/bin/bash

# Google Drive to Pinecone CLI Installation Script

set -e

echo "🚀 Installing Google Drive to Pinecone CLI..."
echo "=============================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    exit 1
fi

echo "✓ pip3 detected"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Install the CLI
echo "🔧 Installing CLI..."
pip3 install -e .

# Test installation
echo "🧪 Testing installation..."
python3 test_cli.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Set up your Pinecone API key:"
    echo "   export PINECONE_API_KEY='your-pinecone-api-key'"
    echo ""
    echo "2. For owner mode (full access), set up Google Drive credentials:"
    echo "   gdrive-search setup-owner --credentials path/to/credentials.json"
    echo ""
    echo "3. For connected mode (read-only), connect to existing index:"
    echo "   gdrive-search connect my-index --api-key YOUR_PINECONE_API_KEY"
    echo ""
    echo "4. Get help:"
    echo "   gdrive-search help"
    echo ""
    echo "For more information, see the README.md file."
else
    echo "❌ Installation test failed. Please check the error messages above."
    exit 1
fi 