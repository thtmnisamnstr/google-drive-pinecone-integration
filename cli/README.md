# Google Drive to Pinecone CLI

A command-line tool for indexing and searching Google Drive documents using Pinecone's hybrid search. Combines semantic understanding with keyword matching for superior search results.

## ✨ Key Features

- **🔍 Hybrid Search**: Best-in-class search combining semantic + keyword matching
- **📁 Smart File Support**: Google Workspace files + 39 plaintext file types (code, config, docs)
- **⚡ Fast Setup**: Get running in minutes with simple configuration
- **🔄 Incremental Updates**: Only processes changed files for efficiency
- **🎯 Two Modes**: Owner mode (full access) or Connected mode (read-only)

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** 
- **Pinecone Account** ([free tier available](https://app.pinecone.io/))
- **Google Cloud Project** with Drive API enabled (for Owner mode)

**Platform Requirements:**
```bash
# macOS
brew install libmagic

# Ubuntu/Debian  
sudo apt-get install libmagic1

# Windows: No additional requirements
```

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd google-drive-pinecone-integration/cli

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install
pip install -r requirements.txt
pip install -e .

# Verify installation
gdrive-pinecone-search --help
```

### Setup

**Option 1: Environment Variables (Recommended)**
```bash
# Create .env file
export PINECONE_API_KEY="your-api-key"
export PINECONE_DENSE_INDEX_NAME="company-dense"
export PINECONE_SPARSE_INDEX_NAME="company-sparse"
export GDRIVE_CREDENTIALS_JSON="path/to/credentials.json"  # Owner mode only

# Setup
gdrive-pinecone-search owner setup --validate
```

**Option 2: Command Line**
```bash
# Owner mode (full access)
gdrive-pinecone-search owner setup \
  --credentials path/to/credentials.json \
  --api-key your-api-key \
  --dense-index-name company-dense \
  --sparse-index-name company-sparse

# Connected mode (read-only)
gdrive-pinecone-search connect \
  --api-key your-api-key \
  --dense-index-name company-dense \
  --sparse-index-name company-sparse
```

## 📖 Essential Usage

### Index Documents (Owner mode only)
```bash
# Index all files
gdrive-pinecone-search owner index

# Index specific file types
gdrive-pinecone-search owner index --file-types docs,sheets,py,json

# Index by category
gdrive-pinecone-search owner index --file-types code,config

# Limit for testing
gdrive-pinecone-search owner index --limit 100 --dry-run
```

### Search Content
```bash
# Basic search
gdrive-pinecone-search search "quarterly planning"

# Search with filters
gdrive-pinecone-search search "API documentation" --file-types py,md --limit 10

# Interactive results
gdrive-pinecone-search search "meeting notes" --interactive
```

### Update Index (Owner mode only)
```bash
# Incremental refresh (only changed files)
gdrive-pinecone-search owner refresh

# Refresh specific types
gdrive-pinecone-search owner refresh --file-types code --limit 50

# Force full refresh
gdrive-pinecone-search owner refresh --force-full
```

## 🔧 File Types & Categories

**Supported Files (39 types):**
- **Google Workspace**: `docs`, `sheets`, `slides`
- **Code**: `py`, `js`, `ts`, `java`, `cpp`, `go`, `rs`, `php`, etc.
- **Config**: `json`, `yaml`, `toml`, `ini`, `cfg`, `conf`
- **Text**: `txt`, `md`, `rst`, `log`
- **Web**: `html`, `css`, `xml`
- **Data**: `csv`, `tsv`, `sql`

**Categories for easy selection:**
- `code` - All programming files
- `config` - Configuration files  
- `txt` - Text and documentation
- `web` - Web development files
- `data` - Data files

## 🔍 How Hybrid Search Works

1. **Dense Embeddings**: Understand context and meaning
2. **Sparse Embeddings**: Match exact keywords and technical terms  
3. **Intelligent Reranking**: Pinecone's hosted model optimizes relevance
4. **Best of Both**: Catches conceptual AND literal matches

## ⚙️ Environment Variables

```bash
# Required
PINECONE_API_KEY="your-api-key"
PINECONE_DENSE_INDEX_NAME="your-dense-index"  
PINECONE_SPARSE_INDEX_NAME="your-sparse-index"

# Owner mode only
GDRIVE_CREDENTIALS_JSON="path/to/credentials.json"

# Optional
CHUNK_SIZE="450"
CHUNK_OVERLAP="75"
RERANKING_MODEL="pinecone-rerank-v0"
```

## 🔧 Troubleshooting

**Common Issues:**

1. **CLI not found**: `pip install -e .` or use `python -m gdrive_pinecone_search.cli.main`
2. **Tests failing**: Ensure virtual environment is active and `pytest` is installed
3. **Permission errors**: Use virtual environment or `pip install --user`
4. **API errors**: Check credentials and index names in environment variables

**Get Help:**
```bash
gdrive-pinecone-search --help
gdrive-pinecone-search search --help  
gdrive-pinecone-search owner --help
```

## 📚 Advanced Topics

### Getting Credentials

**Pinecone:**
1. Sign up at [app.pinecone.io](https://app.pinecone.io)
2. Create project and get API key
3. Create indexes: one with `multilingual-e5-large`, one with `pinecone-sparse-english-v0`

**Google Drive (Owner mode):**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project and enable Drive/Docs/Sheets/Slides APIs
3. Create OAuth 2.0 Desktop credentials
4. Download JSON file

### Operation Modes

- **Owner Mode**: Full access - index, refresh, search (requires Google Drive + Pinecone)
- **Connected Mode**: Read-only search of existing indexes (requires Pinecone only)

### Testing

```bash
# Run full test suite (91 tests in 0.49 seconds)
pytest tests/ -v

# Test categories
pytest tests/test_smoke.py -v              # Basic functionality  
pytest tests/test_cli_commands.py -v       # CLI commands
pytest tests/test_search_pipeline.py -v    # Search functionality
```

---

**For detailed technical documentation, see [REQUIREMENTS.md](../REQUIREMENTS.md)**