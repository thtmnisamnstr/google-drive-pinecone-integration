# Google Drive to Pinecone CLI

> **Note**: This CLI is part of the [Google Drive Pinecone Integration monorepo](../README.md). For the complete project overview, see the [main README](../README.md).

A powerful command-line interface for indexing Google Drive documents into Pinecone vector database and performing **hybrid search** (combining dense and sparse vectors) across your organization's content. This CLI provides seamless integration between Google Drive and Pinecone with intelligent text processing, automatic vector generation, and superior search relevance through reranking.

## Features

- **Hybrid Search**: Combines semantic understanding with keyword matching for superior search results
- **Google Drive Integration**: Index and search across Google Docs, Sheets, and Slides
- **Two Operation Modes**: Full access (owner) or read-only (connected) depending on your needs
- **Smart Updates**: Intelligent incremental indexing using last refresh timestamp for optimal performance
- **Interactive Results**: Click to open files directly in your browser
- **Easy Setup**: Simple configuration with environment variable support

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd google-drive-pinecone-integration/cli

# Install dependencies
pip install -r requirements.txt

# Install the CLI
pip install -e .
```

### 2. Setup

#### Owner Mode (Full Access)

```bash
# Set up owner mode with both Google Drive and Pinecone credentials
gdrive-pinecone-search owner setup \
  --credentials [path/to/gdrive-credentials.json] \
  --api-key [YOUR_PINECONE_API_KEY] \
  --dense-index-name [dense-index-name] \
  --sparse-index-name [sparse-index-name] \
  --validate

# Set up using environment variables
export GDRIVE_CREDENTIALS_JSON="path/to/gdrive-credentials.json"
export PINECONE_API_KEY="YOUR_PINECONE_API_KEY"
export PINECONE_DENSE_INDEX_NAME="company-gdrive-dense-index"
export PINECONE_SPARSE_INDEX_NAME="company-gdrive-sparse-index"

gdrive-pinecone-search owner setup --validate
```

#### Connected Mode (Read-Only)

```bash
# Connect to existing Pinecone indexes
gdrive-pinecone-search connect \
  --dense-index-name [dense-index-name] \
  --sparse-index-name [sparse-index-name] \
  --api-key [YOUR_PINECONE_API_KEY] \
  --validate

# Or rely on environment/.env values
export PINECONE_API_KEY="YOUR_PINECONE_API_KEY"
export PINECONE_DENSE_INDEX_NAME="company-gdrive-dense-index"
export PINECONE_SPARSE_INDEX_NAME="company-gdrive-sparse-index"
gdrive-pinecone-search connect --validate
```

### 3. Index Your Documents (Owner Mode only)

```bash
# Index all Google Drive files with hybrid embeddings
gdrive-pinecone-search owner index

# Index specific file types
gdrive-pinecone-search owner index --file-types docs,sheets

# Limit number of files (for testing)
gdrive-pinecone-search owner index --limit 100

# Dry run to see what would be indexed
gdrive-pinecone-search owner index --dry-run
```

### 3.5. Refresh Your Index (Optional, Owner Mode only)

```bash
# Incremental refresh using last refresh time
gdrive-pinecone-search owner refresh

# Refresh files modified since a specific date
gdrive-pinecone-search owner refresh --since 2024-01-15

# Force full refresh of all files
gdrive-pinecone-search owner refresh --force-full

# Refresh specific file types with limit
gdrive-pinecone-search owner refresh --file-types docs,sheets --limit 50

# Dry run to see what would be refreshed
gdrive-pinecone-search owner refresh --dry-run
```

### 4. Search Your Content

```bash
# Basic hybrid search with reranking
gdrive-pinecone-search search "quarterly planning"

# Search with filters
gdrive-pinecone-search search "team meeting notes" --file-types docs --limit 5

# Interactive search results
gdrive-pinecone-search search "project timeline" --interactive
```

## Hybrid Search

This CLI implements **hybrid search** as recommended by [Pinecone's hybrid search guide](https://docs.pinecone.io/guides/search/hybrid-search), combining the strengths of both dense and sparse embeddings with intelligent reranking:

### How It Works

1. **Integrated Embedding**: Uses Pinecone's integrated embedding models for automatic vector generation
2. **Dense Embeddings**: Capture semantic meaning and relationships
3. **Sparse Embeddings**: Capture exact keyword matches and domain-specific terminology
4. **Intelligent Reranking**: Uses Pinecone's hosted `pinecone-rerank-v0` model for optimal relevance

### Benefits

- **Automatic Vector Generation**: No need to generate embeddings separately
- **Better Semantic Understanding**: Dense vectors understand context and synonyms
- **Precise Keyword Matching**: Sparse vectors catch exact terms and technical jargon
- **Intelligent Reranking**: Hosted reranking model provides superior relevance scoring
- **Comprehensive Coverage**: Catches both conceptual and literal matches

### Default Models

- **Suggested Dense Model**: `multilingual-e5-large` (integrated into dense index, default chunking is tailored for this model)
- **Suggested Sparse Model**: `pinecone-sparse-english-v0` (integrated into sparse index)
- **Suggested Reranking Model**: `pinecone-rerank-v0` (hosted, configured at build time)

## Environment Variables

You can use environment variables to avoid passing credentials on the command line:

```bash
# Pinecone Configuration
export PINECONE_API_KEY="your_pinecone_api_key"
export PINECONE_DENSE_INDEX_NAME="company-gdrive-dense-index"
export PINECONE_SPARSE_INDEX_NAME="company-gdrive-sparse-index"

# Google Drive Configuration (Owner Mode Only)
export GDRIVE_CREDENTIALS_JSON="path/to/credentials.json"

# Optional Settings
export CHUNK_SIZE="450"
export CHUNK_OVERLAP="75"
export RERANKING_MODEL="pinecone-rerank-v0"
```

Notes:
- The CLI automatically loads a `.env` file at startup.
- Precedence: CLI option > environment/.env > saved config.
- When using environment variables, you can run `owner setup` without command-line arguments:
```bash
gdrive-pinecone-search owner setup --validate
```

### Configuration File

The CLI stores configuration in `~/.config/gdrive-pinecone-search/config.json`:

```json
{
  "mode": "owner",
  "connection": {
    "pinecone_api_key": "...",
    "dense_index_name": "company-gdrive-dense-index",
    "sparse_index_name": "company-gdrive-sparse-index",
    "created_at": "2024-01-15T12:00:00Z"
  },
  "owner_config": {
    "google_drive_credentials_path": "...",
    "last_refresh_time": "2024-01-15T12:00:00Z",
    "total_files_indexed": 1250
  },
  "settings": {
    "chunk_size": 450,
    "chunk_overlap": 75,
    "reranking_model": "pinecone-rerank-v0"
  }
}
```

## Operation Modes

### Owner Mode

Full access to both Google Drive and Pinecone:
- Index Google Drive → Pinecone (both dense and sparse indexes)
- Refresh/update existing indexes
- Search indexed content using hybrid search
- Requires: Google Drive API access + Pinecone API key

### Connected Mode

Read-only access to existing Pinecone indexes:
- Search existing Pinecone indexes using hybrid search
- View index statistics
- Requires: Pinecone API key only

## File Types Supported

- **Google Docs** (`application/vnd.google-apps.document`)
- **Google Sheets** (`application/vnd.google-apps.spreadsheet`)
- **Google Slides** (`application/vnd.google-apps.presentation`)

## Limitations

- **Metadata Size Limit**: Pinecone has a 40,960 byte limit per vector metadata. The CLI uses minimal metadata (file name, type, link, and essential fields) and automatically truncates long file names to stay within limits.
- **File Access**: Files must be accessible for export/download to be indexed.
- **Rate Limits**: Built-in rate limiting prevents API quota exhaustion.

## Search Features

### Query Examples

```bash
# Find planning documents (semantic + keyword matching with reranking)
gdrive-pinecone-search search "Q4 planning and objectives"

# Search for budget information
gdrive-pinecone-search search "budget allocation department spending"

# Find meeting notes (semantic focus with reranking)
gdrive-pinecone-search search "team meeting notes action items"

# Search specific file types
gdrive-pinecone-search search "quarterly reports" --file-types docs,sheets
```

### Search Options

- `--limit`: Number of results to return (default: 10, max: 100)
- `--file-types`: Filter by file types (docs, sheets, slides)
- `--interactive`: Enable interactive result selection

**Note**: The maximum limit of 100 results is enforced due to Pinecone's reranking API constraints. For optimal performance and relevance, we recommend using limits of 50 or less to ensure full reranking capabilities.

## Metadata Structure

Each vector stores minimal, essential metadata to optimize storage and performance:

```json
{
  "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "file_name": "Q4 Planning Meeting Notes",
  "file_type": "docs",
  "chunk_index": 2,
  "modified_time": "2024-01-15T10:30:00Z",
  "web_view_link": "https://docs.google.com/document/d/..."
}
```

**Fields**:
- **`file_id`**: Google Drive file ID (required for refresh/cleanup operations)
- **`file_name`**: Display name for search results
- **`file_type`**: File type for filtering (docs, sheets, slides)
- **`chunk_index`**: Position within document (required for vector uniqueness)
- **`modified_time`**: Last modified timestamp (required for incremental refresh)
- **`web_view_link`**: Direct link to open file in Google Drive

## Getting Pinecone Credentials

To use Pinecone for vector storage, follow these steps:

1. **Sign up for Pinecone**
   - Visit [Pinecone Console](https://app.pinecone.io/)
   - Sign up for a free Starter plan account

2. **Get your API Key**
   - After signing up, you'll be prompted to create a new project
   - After you create a new project, it will give you an API key
   - Copy your API key (starts with something like `pcsk-...`)

3. **Create Dense and Sparse Indexes**
   - In your Pinecone project, click "Create Index"
   - Create two indexes:
     - **Dense Index**: Choose `multilingual-e5-large` model
     - **Sparse Index**: Choose `pinecone-sparse-english-v0` model
   - Select your preferred cloud provider (e.g., AWS) and region (e.g., us-east-1)
   - Click "Create Index"

4. **Note your Index Names**
   - After creating the indexes, note both index names
   - You'll need these for the setup command

## Getting Google Drive Credentials

To use Google Drive API, follow these steps:

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Drive API**
   - Go to "APIs & Services" → "Library"
   - Enable for the following services:
     - Google Drive API
     - Google Docs API
     - Google Sheets API
     - Google Slides API
     - Drive Activity API

3. **Create Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as the application type
   - Download the JSON file

4. **Use the Credentials**
   - Save the downloaded JSON file securely
   - Reference it in the setup command: `--credentials path/to/credentials.json`

**Note**: The first time you run the CLI and whenever your Google Cloud auth token expires, the CLI will open a browser window for you to authenticate with your Google account.
