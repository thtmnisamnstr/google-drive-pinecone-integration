# Google Drive Pinecone Integration - Technical Requirements

## Description

A sophisticated CLI tool that integrates Google Drive with Pinecone for **hybrid search** across organizational documents. The application leverages Google Drive API to extract content from Google Docs, Sheets, and Slides, processes them into intelligent chunks, and stores them in Pinecone's vector database using **integrated embedding models** (automatic vector generation). The CLI supports dual operation modes: **owner mode** (full access for indexing and searching) and **connected mode** (read-only search access to existing indexes).

The tool implements Pinecone's recommended hybrid search approach, combining dense semantic embeddings with sparse keyword embeddings, enhanced by intelligent reranking for superior search relevance. The system provides smart incremental updates, interactive search results, and direct file access from search results.

**Key Features:**
- **Hybrid Search**: Combines dense (semantic) and sparse (keyword) vectors with reranking for optimal results
- **Integrated Embedding**: Automatic vector generation using Pinecone's hosted models (no external API calls)
- **Dual Operation Modes**: Full access (owner) or read-only (connected) depending on requirements
- **Smart Incremental Updates**: Intelligent refresh using timestamp tracking for optimal performance
- **Interactive Results**: Rich CLI interface with direct browser file opening
- **Production-Ready**: Built-in rate limiting, error handling, and quota protection
- **Monorepo Structure**: Organized for future expansion with web UI component

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ Commands Layer                                                  │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │ owner setup │ │ owner index │ │ owner refresh│ │   search    ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │   connect   │ │   status    │ │     help    │ │     UI      ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ Service Layer                                                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │SearchService│ │GDriveService│ │DocProcessor │ │ AuthService ││
│ │(Hybrid)     │ │             │ │             │ │             ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ Utilities Layer                                                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │ConfigManager│ │RateLimiter  │ │ConnectionMgr│ │ Exceptions  ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ External APIs                                                   │
│ ┌─────────────┐ ┌─────────────┐                                │
│ │  Pinecone   │ │Google Drive │                                │
│ │Dense+Sparse │ │     API     │                                │
│ │+ Reranking  │ │             │                                │
│ └─────────────┘ └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Local Storage   │
                       │ - Config JSON   │
                       │ - Auth Tokens   │
                       │ - Connection    │
                       │   State         │
                       └─────────────────┘
```

### Repository Structure (Monorepo)

```
google-drive-pinecone-integration/
├── README.md                    # Main monorepo overview
├── LICENSE                      # MIT license
├── REQUIREMENTS.md              # This file - technical requirements
├── .gitignore                  # Root gitignore (includes macOS files)
├── web-ui/                     # Future web interface
│   ├── README.md               # "Coming eventually"
│   └── LICENSE                 # MIT license
└── cli/                        # Current CLI implementation
    ├── README.md               # CLI-specific documentation
    ├── LICENSE                 # MIT license
    ├── setup.py                # Package configuration
    ├── requirements.txt        # Python dependencies
    ├── env.example             # Environment variables template
    ├── install.sh              # Installation script
    ├── COMPLETION_SUMMARY.md   # Implementation details
    ├── creds/                  # Google Drive credentials (gitignored)
    ├── gdrive_pinecone_search/
    │   ├── __init__.py
    │   ├── cli/
    │   │   ├── main.py          # CLI entry point & command registration
    │   │   ├── commands/
    │   │   │   ├── setup_owner.py   # Owner mode setup
    │   │   │   ├── connect.py       # Connect to existing indexes
    │   │   │   ├── index.py         # Initial indexing (owner mode)
    │   │   │   ├── refresh.py       # Incremental updates (owner mode)
    │   │   │   ├── search.py        # Hybrid search (both modes)
    │   │   │   └── status.py        # Connection/index status
    │   │   └── ui/
    │   │       ├── progress.py      # Progress bars, status displays
    │   │       └── results.py       # Search results & interactive UI
    │   ├── services/
    │   │   ├── search_service.py    # Hybrid search operations
    │   │   ├── gdrive_service.py    # Google Drive API wrapper
    │   │   ├── document_processor.py # Text chunking & processing
    │   │   └── auth_service.py      # Authentication handling
    │   └── utils/
    │       ├── config_manager.py    # Configuration management
    │       ├── connection_manager.py # Connection state
    │       ├── rate_limiter.py      # API rate limiting
    │       └── exceptions.py        # Custom exceptions
    └── tests/
        ├── test_hybrid_search.py
        └── test_cli.py
```

### Operation Modes

**Owner Mode**: Complete CRUD operations
- Index Google Drive → Pinecone (dense + sparse indexes)
- Refresh/update existing indexes with smart incremental updates
- Search indexed content using hybrid search with reranking
- Requires: Google Drive API access + Pinecone API key

**Connected Mode**: Read-only operations
- Search existing Pinecone indexes using hybrid search
- View comprehensive index statistics
- Requires: Pinecone API key only

## Technical Requirements

### 1. Authentication & Configuration

**Requirement**: Dual authentication modes with secure credential management and environment variable support

**Owner Mode Authentication**:
- Google Drive OAuth2 credentials with scopes: `drive.readonly`
- Pinecone API key for vector database operations
- Secure token storage in `~/.config/gdrive-pinecone-search/`

**Connected Mode Authentication**:
- Pinecone API key only
- No Google Drive access required

**Configuration Schema**:
```json
{
  "mode": "owner|connected",
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

**Environment Variables Support**:
```bash
# Required for Owner Mode
GDRIVE_CREDENTIALS_JSON="path/to/credentials.json"
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_DENSE_INDEX_NAME="company-gdrive-dense-index"
PINECONE_SPARSE_INDEX_NAME="company-gdrive-sparse-index"

# Optional Settings (overrides config file)
CHUNK_SIZE="450"
CHUNK_OVERLAP="75"
RERANKING_MODEL="pinecone-rerank-v0"
```

**Technical Details**:
- Use `google-auth-oauthlib` for OAuth2 flow
- Store configuration in `~/.config/gdrive-pinecone-search/config.json`
- Support environment variable precedence: CLI args > env vars > config file
- Validate API credentials on command execution
- Automatic `.env` file loading from CLI directory

### 2. Google Drive Integration (Owner Mode Only)

**Requirement**: Comprehensive Google Drive file access with intelligent change tracking

**Supported File Types**:
- Google Docs (`application/vnd.google-apps.document`) → exported as `text/plain`
- Google Sheets (`application/vnd.google-apps.spreadsheet`) → exported as `text/csv`
- Google Slides (`application/vnd.google-apps.presentation`) → exported as `text/plain`

**API Integration**:
- Google Drive API v3 with `files.list()` and `files.export()`
- Built-in exponential backoff for rate limiting (1000 requests per 100 seconds)
- Graceful handling of inaccessible files (permission denied, export failures)
- Comprehensive error reporting and recovery strategies

**Smart Change Detection**:
- Track `modifiedTime` for incremental updates using timezone-aware comparisons
- Store `last_refresh_time` in Pinecone index metadata for true incremental updates
- Process new files, modified files, and detect deleted files automatically
- Support for manual date override with `--since YYYY-MM-DD` format
- Use `files.list()` with `q` parameter: `modifiedTime > '2024-01-15T12:00:00Z'`

### 3. Document Processing

**Requirement**: Intelligent text chunking optimized for hybrid search

**Chunking Strategy**:
- Target chunk size: 450 tokens (configurable via `CHUNK_SIZE`)
- Overlap: 75 tokens between chunks (configurable via `CHUNK_OVERLAP`)
- Sentence boundary preservation when possible
- File-type specific processing (Docs/Slides: plain text, Sheets: CSV parsing)

**Text Processing Pipeline**:
1. Extract plain text from Google Drive exports
2. Clean and normalize text (remove excessive whitespace, normalize encoding)
3. Split into chunks with sliding window approach
4. Generate optimized metadata for each chunk

**Optimized Metadata Structure** (reduced by 40-50% for efficiency):
```json
{
  "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "file_name": "Q4 Planning Document",
  "file_type": "docs",
  "chunk_index": 0,
  "modified_time": "2024-01-15T10:30:00Z",
  "web_view_link": "https://docs.google.com/document/d/..."
}
```

**Removed Fields** (for optimization):
- `indexed_at`: Not critical for search functionality
- `chunk_token_count`: Not used in core operations
- `total_chunks`: Not required for search results

**Benefits of Optimization**:
- Reduced Pinecone storage costs
- Faster vector operations with less data
- Less likely to hit Pinecone's 40,960 byte metadata limit
- Focused on essential information only

### 4. Pinecone Integration (Hybrid Search)

**Requirement**: Efficient dual-index vector storage with integrated embedding

**Index Configuration**:
```python
# Dense Index
{
    "dimension": 1024,
    "metric": "cosine",
    "embed": {
        "model": "multilingual-e5-large",
        "field_map": {"text": "chunk_text"}
    }
}

# Sparse Index  
{
    "dimension": 1024,
    "metric": "dotproduct", 
    "embed": {
        "model": "pinecone-sparse-english-v0",
        "field_map": {"text": "chunk_text"}
    }
}
```

**Vector Operations**:
- **Vector ID Format**: `{file_id}#{chunk_index}` (enables efficient updates/deletions)
- **Batch Size**: 96 vectors per upsert (Pinecone integrated embedding limit)
- **Special Metadata Vector**: `__index_metadata__` stores refresh timestamps and indexing info
- **Rate Limiting**: Built-in protection against quota exhaustion using tenacity

**Operations**:
- **Upsert**: Add/update document chunks to both indexes using `upsert_records`
- **Delete**: Remove chunks for deleted files (by file_id prefix)
- **Query**: Hybrid search with result merging and reranking
- **Fetch**: Retrieve specific vectors for validation and metadata

### 5. Hybrid Search Implementation

**Requirement**: Superior search relevance through multi-stage processing

**Advanced Search Algorithm**:
1. **Dual Query**: Generate embeddings for both dense and sparse indexes
2. **Parallel Search**: Query both indexes simultaneously with configurable limits
3. **Smart Merging**: Vector-level deduplication keeping highest scores
4. **Pre-Reranking Deduplication**: File-level deduplication using intelligent chunk selection
5. **Reranking**: Use hosted `pinecone-rerank-v0` model (max 100 documents)
6. **Score Integration**: Transparent scoring with original and reranked scores

**Smart Chunk Selection Strategy** (for file-level deduplication):
- Normalize sparse scores (dot product 0-10 range) to 0-1
- Weighted combined score: `(2 * dense_score + normalized_sparse_score) / 3`
- Position bonus for early chunks (introduction/overview content)
- Fallback to dense score if sparse score is 0

**Performance Optimizations**:
- Fetch 4x limit from both indexes initially for comprehensive results
- Document-level deduplication before reranking (more efficient than after)
- Maximum 100 results enforced (Pinecone reranking API constraint)
- Recommended limit: 50 or less for optimal performance

**Reranking Implementation**:
- **Model**: Configurable via `RERANKING_MODEL` environment variable (default: `pinecone-rerank-v0`)
- **Input**: Original query text + merged document content
- **Output**: Reranked relevance scores with transparency
- **Fallback**: Returns original results if reranking fails
- **Rate Limiting**: 100 reranking requests per minute

### 6. CLI Interface

**Requirement**: Production-ready command-line interface with rich user experience

#### Core Commands

**1. Owner Mode Setup**
```bash
gdrive-pinecone-search owner setup \
  --credentials path/to/credentials.json \
  --api-key your_pinecone_api_key \
  --dense-index-name company-gdrive-dense \
  --sparse-index-name company-gdrive-sparse \
  --validate
```

**2. Connect to Existing Indexes**
```bash
gdrive-pinecone-search connect \
  --dense-index-name existing-dense-index \
  --sparse-index-name existing-sparse-index \
  --api-key your_pinecone_api_key \
  --validate
```

**3. Initial Indexing (Enhanced)**
```bash
gdrive-pinecone-search owner index \
  --limit 100 \
  --file-types docs,sheets,slides \
  --dry-run \
  --credentials path/to/credentials.json
```

**4. Smart Incremental Refresh (Enhanced)**
```bash
# Automatic incremental using last refresh timestamp
gdrive-pinecone-search owner refresh

# Manual date override
gdrive-pinecone-search owner refresh --since 2024-01-15

# Full refresh with options
gdrive-pinecone-search owner refresh \
  --force-full \
  --limit 50 \
  --file-types docs,sheets \
  --dry-run
```

**5. Hybrid Search (Optimized)**
```bash
gdrive-pinecone-search search "quarterly planning" \
  --limit 10 \
  --file-types docs,sheets \
  --interactive
```

**6. Status & Diagnostics**
```bash
gdrive-pinecone-search status \
  --verbose \
  --test-connections
```

#### Enhanced Options

**Refresh Command Options** (matching `owner index` command):
- **`--limit`**: Limit number of files to process
- **`--file-types`**: Filter by specific file types (docs, sheets, slides)
- **`--dry-run`**: Preview what would be processed without making changes
- **`--since`**: Override last refresh time with specific date
- **`--force-full`**: Ignore last refresh time and process all files

**Search Command Options**:
- **`--limit`**: Number of results to return (default: 10, max: 100)
- **`--file-types`**: Filter by file types (docs, sheets, slides)
- **`--interactive`**: Enable interactive result selection with detailed views

#### UI Enhancements

**Search Results Display**:
- Grid format (no borders) with score and content preview
- Interactive mode with detailed result view showing:
  - Reranked Score (primary relevance)
  - Dense Score (semantic similarity)
  - Sparse Score (keyword matching)
  - Full content preview
- Direct browser opening for selected files
- Content preview with 150-character limit in grid view

**Progress Indicators**:
- Real-time progress bars for long operations using Rich library
- Status panels for connection states and operation progress
- Error panels with actionable messages and resolution suggestions
- Success panels with next steps and operation summaries

### 7. Error Handling & Resilience

**Requirement**: Production-grade error handling for team environments

**Error Categories & Recovery Strategies**:
- **Authentication Errors**: Invalid/expired credentials → Clear re-auth instructions
- **API Errors**: Rate limits, quotas → Exponential backoff with jitter using tenacity
- **File Access Errors**: Permission denied → Skip with clear reporting, continue processing
- **Network Errors**: Timeouts, connectivity → Retry with circuit breaker pattern
- **Data Errors**: Metadata size limits → Automatic truncation and graceful fallback

**User Communication**:
- Rich terminal UI with color-coded messages using Rich library
- Progress tracking with ETA for long operations
- Detailed error messages with specific resolution suggestions
- Comprehensive logging for debugging and troubleshooting
- Graceful degradation (skip problematic files, continue processing)

**Recovery Mechanisms**:
- Exponential backoff with jitter for API rate limits
- Retry failed operations up to 3 times with increasing delays
- Resume capability for interrupted long-running operations
- Circuit breakers for failing API endpoints

### 8. Performance & Scalability

**Requirement**: Efficient processing for large organizational Google Drive accounts

**Optimization Strategies**:
- Concurrent API operations within rate limits
- Memory-efficient streaming for large documents
- Smart batching (Google Drive: 1000 files/page, Pinecone: 96 vectors/batch)
- Intelligent caching for frequently accessed metadata

**Resource Management**:
- Built-in rate limiting with configurable limits using custom rate limiter
- Process files by modification time (newest first for refresh operations)
- Circuit breakers for failing endpoints
- Resumable operations with persistent state
- Memory-conscious document processing (stream large files)

**Progress Tracking**:
- Persistent state for resumable operations
- Real-time progress indicators with ETA
- Detailed logging for debugging and monitoring
- Performance metrics and operation summaries

### 9. Current State & Implementation Status

**Project Status**: Fully functional hybrid search implementation with recent monorepo restructuring

**Recent Major Enhancements**:
- ✅ **Monorepo Structure**: Organized with CLI in subdirectory, prepared for web UI
- ✅ **Enhanced Refresh Logic**: True incremental updates using `last_refresh_time` from index metadata
- ✅ **Optimized Metadata**: 40-50% size reduction while maintaining functionality
- ✅ **Smart Deduplication**: File-level deduplication before reranking for efficiency
- ✅ **Grid-Based Results**: Improved search results display with content preview
- ✅ **Timezone Handling**: Fixed timezone issues in date comparisons
- ✅ **Interactive Enhancements**: Detailed result views with score breakdown
- ✅ **Score Normalization**: Proper handling of dense (cosine) and sparse (dot product) scores
- ✅ **Rate Limiting**: Comprehensive API protection with exponential backoff

**Key Improvements Made**:
- **Before**: Only processed new files during refresh (missed modifications)
- **After**: Processes new files + files modified since last refresh timestamp
- **Benefits**: True incremental updates, significantly faster refresh times, better user feedback

**Current Issues**: None critical - system is production-ready

**Files Status**: All major refactoring complete, no files requiring immediate attention

### 10. Dependencies & Environment

**Python Version**: 3.8+ (tested with Python 3.13.7)

**Core Dependencies**:
```txt
click>=8.1.0                    # CLI framework with rich command support
google-auth>=2.23.0             # Google authentication core
google-auth-oauthlib>=1.1.0     # OAuth2 flow for Google Drive
google-auth-httplib2>=0.1.1     # HTTP transport for Google APIs
google-api-python-client>=2.100.0 # Google Drive API client
pinecone>=7.0.0                 # Pinecone vector database with integrated embedding
tiktoken>=0.5.1                 # Token counting for chunk size management
rich>=13.6.0                    # Rich terminal UI with progress bars and panels
python-dotenv>=1.0.0            # Environment variable loading from .env files
pydantic>=2.5.0                 # Data validation and settings management
tenacity>=8.2.3                 # Retry logic with exponential backoff
```

**Installation Process**:
```bash
cd google-drive-pinecone-integration/cli
pip install -r requirements.txt
pip install -e .
```

**Package Configuration**:
- Entry point: `gdrive-pinecone-search=gdrive_pinecone_search.cli.main:main`
- Supports Python 3.8+ with classifiers for modern Python versions
- MIT License with proper package metadata

### 11. Operational Considerations

**Configuration Management**:
- Primary config stored in `~/.config/gdrive-pinecone-search/config.json`
- Environment variable precedence: CLI args > env vars > config file
- Automatic `.env` file loading from CLI directory
- Validation of all configuration before operations

**Security Best Practices**:
- OAuth2 refresh tokens stored securely in user config directory
- API keys never logged or displayed in plain text
- Comprehensive credential validation before operations
- Secure handling of Google Drive credentials with proper scopes

**Monitoring & Maintenance**:
- Built-in index statistics and health checks via `status` command
- Automatic cleanup of deleted files during refresh operations
- Comprehensive logging for troubleshooting and monitoring
- Rate limit monitoring and reporting
- Index metadata tracking for operational insights

**Data Management**:
- Automatic metadata size validation (Pinecone 40,960 byte limit)
- Smart truncation of long file names to stay within limits
- Consistent vector ID format for efficient operations
- Proper cleanup of deleted files from both indexes

### 12. Future Roadmap & Enhancement Opportunities

**Immediate Development Opportunities**:
- **Multi-Architecture Builds**: PyInstaller/Nuitka builds for multiple platforms
- **GitHub Actions CI/CD**: Automated testing and release pipeline
- **Enhanced File Support**: PDFs, Word documents, additional Google Workspace types
- **Performance Metrics**: Search analytics and performance monitoring

**Medium-term Enhancements**:
- **Web UI Implementation**: Complete the web-ui/ directory with modern interface
- **Advanced Search Features**: Boolean operators, date ranges, advanced filters
- **Custom Embedding Models**: Support for user-provided embedding models
- **Multi-language Support**: Enhanced support for non-English content

**Long-term Strategic Vision**:
- **Multi-tenant Architecture**: Support for large organizations with multiple teams
- **Enterprise Integration**: SharePoint, Confluence, and other document sources
- **Advanced Analytics**: Search behavior insights and content recommendations
- **Scalability Improvements**: Distributed processing for very large document collections

**Technical Debt & Optimization**:
- **Batch Processing**: Enhanced batch operations for better performance
- **Memory Optimization**: Further reduce memory footprint for large operations
- **API Efficiency**: Optimize API calls and reduce redundant operations

---

## Development Notes

**Testing Strategy**:
- Comprehensive unit tests in `tests/` directory
- Integration tests for hybrid search functionality
- End-to-end CLI testing with real API interactions
- Performance benchmarking for large document sets

**Code Quality Standards**:
- Type hints throughout codebase using modern Python typing
- Pydantic models for data validation and configuration
- Rich error handling with user-friendly messages
- Comprehensive docstrings and code documentation

**Deployment Considerations**:
- Single binary distribution via PyInstaller for easy deployment
- Docker containerization for consistent environments
- Environment-specific configuration management
- Automated dependency management and security updates
