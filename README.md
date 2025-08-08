# Google Drive to Pinecone CLI

A powerful command-line interface for indexing Google Drive documents into Pinecone vector database and performing semantic search across your organization's content.

## Features

- **Dual Operation Modes**: Owner mode (full access) and Connected mode (read-only)
- **Comprehensive File Support**: Google Docs, Sheets, and Slides
- **Intelligent Chunking**: Smart text processing with configurable chunk sizes
- **Semantic Search**: Natural language queries with relevance scoring
- **Incremental Updates**: Efficient refresh of modified files only
- **Interactive Results**: Click to open files directly in your browser
- **Rate Limiting**: Built-in API rate limit management
- **Rich UI**: Beautiful progress bars and status displays

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd google-drive-pinecone-integration

# Install dependencies
pip install -r requirements.txt

# Install the CLI
pip install -e .
```

### 2. Setup

#### Owner Mode (Full Access)

```bash
# Set up owner mode with both Google Drive and Pinecone credentials
gdrive-pinecone-search setup-owner \
  --credentials [path/to/gdrive-credentials.json] \
  --api-key [YOUR_PINECONE_API_KEY] \
  --index-name [index-name]
```

#### Connected Mode (Read-Only)

```bash
# Connect to existing Pinecone index
gdrive-pinecone-search connect [index_name] --api-key [YOUR_PINECONE_API_KEY]
```

### 3. Index Your Documents

```bash
# Index all Google Drive files
gdrive-pinecone-search index

# Index specific file types
gdrive-pinecone-search index --file-types docs,sheets

# Limit number of files (for testing)
gdrive-pinecone-search index --limit 100

# Dry run to see what would be indexed
gdrive-pinecone-search index --dry-run
```

### 4. Search Your Content

```bash
# Basic search
gdrive-pinecone-search search "quarterly planning"

# Search with filters
gdrive-pinecone-search search "budget analysis" --file-types docs,sheets --limit 5

# Interactive search with file opening
gdrive-pinecone-search search "team meeting notes" --interactive
```

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `connect` | Connect to existing Pinecone index |
| `index` | Index Google Drive files (owner mode) |
| `refresh` | Refresh index with updates (owner mode) |
| `search` | Search indexed content |
| `status` | Show configuration and connection status |

### Setup Commands

| Command | Description |
|---------|-------------|
| `setup-owner` | Configure owner mode with Google Drive credentials |
| `setup-connected` | Configure connected mode with Pinecone credentials |

### Utility Commands

| Command | Description |
|---------|-------------|
| `help` | Show detailed help information |

## Configuration

### Getting Google Drive Credentials

To access Google Drive files, you need OAuth 2.0 credentials. Follow these steps:

1. **Go to Google Cloud Console**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
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

**Note**: The first time you run the CLI, it will open a browser window for you to authenticate with your Google account.

### Getting Pinecone Credentials

To use Pinecone for vector storage, follow these steps:

1. **Sign up for Pinecone**
   - Visit [Pinecone Console](https://app.pinecone.io/)
   - Sign up for a free Starter plan account

2. **Get your API Key**
   - After signing up, go to your project dashboard
   - Click on "API Keys" in the left sidebar
   - Copy your API key (starts with something like `sk-...`)

3. **Create an Index**
   - In your Pinecone project, click "Create Index"
   - Choose a name for your index (e.g., `google-drive-pinecone-integration`)
   - Select an embedding model for your database to be tuned for (e.g., multilingual-e5-large)
   - Select your preferred cloud provider (e.g., AWS) and region (e.g., us-east-1)
   - Click "Create Index"

4. **Note your Index Name**
   - After creating the index, note the index name
   - You'll need this for the setup command

### Environment Variables

```bash
# Pinecone Configuration
export PINECONE_API_KEY="your_pinecone_api_key"
export PINECONE_INDEX_NAME="company-gdrive-index"

# Google Drive Configuration (Owner Mode Only)
export GDRIVE_CREDENTIALS_JSON="path/to/credentials.json"

# Optional Settings
export EMBEDDING_MODEL="multilingual-e5-large"
export CHUNK_SIZE="800"
export CHUNK_OVERLAP="150"
```

### Configuration File

The CLI stores configuration in `~/.config/gdrive-pinecone-search/config.json`:

```json
{
  "mode": "owner",
  "connection": {
    "pinecone_api_key": "...",
    "index_name": "company-gdrive-index",
    "created_at": "2024-01-15T12:00:00Z"
  },
  "owner_config": {
    "google_drive_credentials_path": "...",
    "last_refresh_time": "2024-01-15T12:00:00Z",
    "total_files_indexed": 1250
  },
  "settings": {
    "embedding_model": "multilingual-e5-large",
    "chunk_size": 800,
    "chunk_overlap": 150
  }
}
```

## Operation Modes

### Owner Mode

Full access to both Google Drive and Pinecone:
- Index Google Drive → Pinecone
- Refresh/update existing index
- Search indexed content
- Requires: Google Drive API access + Pinecone API key

### Connected Mode

Read-only access to existing Pinecone index:
- Search existing Pinecone index
- View index statistics
- Requires: Pinecone API key only

## File Types Supported

- **Google Docs** (`application/vnd.google-apps.document`)
- **Google Sheets** (`application/vnd.google-apps.spreadsheet`)
- **Google Slides** (`application/vnd.google-apps.presentation`)

## Search Features

### Query Examples

```bash
# Find planning documents
gdrive-pinecone-search search "Q4 planning and objectives"

# Search for budget information
gdrive-pinecone-search search "budget allocation department spending"

# Find meeting notes
gdrive-pinecone-search search "team meeting notes action items"

# Search specific file types
gdrive-pinecone-search search "quarterly reports" --file-types docs,sheets
```

### Search Options

- `--limit`: Number of results to return (default: 10)
- `--file-types`: Filter by file types (docs,sheets,slides)
- `--min-score`: Minimum similarity score (0.0-1.0, default: 0.7)
- `--interactive`: Enable interactive result selection

### Interactive Search

When using `--interactive`, you can:
- View detailed result information
- Open files directly in your browser
- Copy file links to clipboard

## Advanced Usage

### Incremental Updates

```bash
# Refresh files modified since last update
gdrive-search refresh

# Refresh files modified since specific date
gdrive-search refresh --since 2024-01-15

# Force full refresh
gdrive-search refresh --force-full
```

### Batch Processing

```bash
# Process files in batches
gdrive-search index --limit 50

# Process specific file types
gdrive-search index --file-types docs

# Dry run to preview
gdrive-search index --dry-run
```

### Connection Management

```bash
# Check connection status
gdrive-search status

# Test all connections
gdrive-search status --test-connections

# Show detailed configuration
gdrive-search status --verbose
```

## API Rate Limits

The CLI automatically handles API rate limits:

- **Google Drive**: 100 requests per 100 seconds per user
- **Pinecone**: 1000 requests per minute

The application implements exponential backoff and retry logic for failed requests.

## Error Handling

The CLI provides comprehensive error handling:

- **Authentication Errors**: Clear guidance for credential issues
- **API Errors**: Rate limit warnings and retry logic
- **Configuration Errors**: Helpful setup instructions
- **Network Errors**: Graceful degradation and recovery

## Performance

### Indexing Performance

- **1000 documents**: ~10 minutes
- **100 changed documents**: ~2 minutes
- **Memory usage**: <500MB during indexing

### Search Performance

- **Response time**: <3 seconds
- **Result ranking**: Configurable similarity thresholds
- **Caching**: Recent searches cached for improved performance

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   ```bash
   # Check credentials
   gdrive-search status --test-connections
   
   # Re-authenticate
   gdrive-search setup-owner --credentials path/to/credentials.json
   ```

2. **Index Not Found**
   ```bash
   # Check Pinecone configuration
   gdrive-search status
   
   # Reconnect to index
   gdrive-search connect my-index --validate
   ```

3. **Rate Limit Exceeded**
   - The CLI automatically handles rate limits
   - Wait for automatic retry or reduce batch sizes

### Debug Mode

```bash
# Enable verbose logging
export GDRIVE_SEARCH_DEBUG=1
gdrive-search status --verbose
```

## Development

### Project Structure

```
gdrive_search/
├── cli/                    # Command-line interface
│   ├── commands/          # Individual commands
│   ├── ui/               # User interface components
│   └── main.py           # Entry point
├── services/             # External service integrations
│   ├── auth_service.py   # Google Drive authentication
│   ├── gdrive_service.py # Google Drive operations
│   ├── pinecone_service.py # Pinecone operations
│   └── document_processor.py # Text processing
└── utils/                # Utilities
    ├── config_manager.py # Configuration management
    ├── rate_limiter.py   # API rate limiting
    └── exceptions.py     # Custom exceptions
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the help command: `gdrive-search help`
- Open an issue on GitHub

## Roadmap

- [ ] Support for additional file types (PDFs, images)
- [ ] Advanced embedding models
- [ ] Collaborative filtering
- [ ] Web interface
- [ ] Real-time indexing
- [ ] Advanced analytics
