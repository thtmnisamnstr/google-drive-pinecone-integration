# Google Drive Pinecone Integration - Technical Requirements

## Description

A sophisticated CLI tool that integrates Google Drive with Pinecone for **hybrid search** across organizational documents. The application leverages Google Drive API to extract content from Google Docs, Sheets, Slides, and plaintext files, processes them intelligently, and stores them in Pinecone vector database using hybrid search for superior relevance.

The tool implements Pinecone's recommended hybrid search approach, combining dense semantic embeddings with sparse keyword embeddings, enhanced by intelligent reranking for optimal search results across diverse document types.

**Core Features:**
- **Hybrid Search**: Dense + sparse vector search with intelligent reranking for superior relevance
- **Comprehensive File Support**: Google Workspace files (Docs, Sheets, Slides) + 39 plaintext file types
- **Dual Operation Modes**: Owner mode (full access) or Connected mode (read-only search)
- **Smart Incremental Updates**: Timestamp-based refresh for optimal performance
- **Interactive Results**: Rich CLI interface with direct browser file opening
- **Production-Ready**: Built-in rate limiting, error handling, and comprehensive testing

**Future Enhancements:**
- **Assistant Mode**: Planned integration with Pinecone Assistant for conversational AI capabilities
- **PDF Support**: Will be available with Assistant Mode integration
- **Web UI**: Planned web interface component

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
│ │(Hybrid)     │ │(Enhanced)   │ │(Enhanced)   │ │             ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │ConfigManager│ │RateLimiter  │ │ConnectionMgr│ │ServiceFactory│
│ │             │ │             │ │             │ │             ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ External APIs                                                   │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│ │  Pinecone   │ │  Pinecone   │ │Google Drive │                │
│ │Dense+Sparse │ │  Reranking  │ │     API     │                │
│ └─────────────┘ └─────────────┘ └─────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### Repository Structure (Monorepo)

```
google-drive-pinecone-integration/
├── README.md                   # Monorepo overview
├── REQUIREMENTS.md             # Technical requirements (this file)
├── LICENSE                     # MIT license
├── .gitignore                  # Git ignore patterns
├── cli/                        # CLI application
│   ├── README.md               # CLI-specific documentation
│   ├── COMPLETION_SUMMARY.md   # Implementation details
│   ├── requirements.txt        # Python dependencies
│   ├── setup.py               # Package configuration
│   ├── gdrive_pinecone_search/ # Main package
│   │   ├── cli/               # CLI command layer
│   │   ├── services/          # Business logic services
│   │   └── utils/             # Utilities and helpers
│   └── tests/                 # Test suite
└── web-ui/                    # Future web interface
    ├── README.md              # Web UI documentation
    └── ...                    # Web UI implementation (future)
```

### Operation Modes

**Owner Mode:**
- Full Google Drive + Pinecone access
- Can index, refresh, and search documents
- Requires: Google Drive OAuth credentials + Pinecone API key
- Target users: System administrators, content managers

**Connected Mode:**
- Read-only access to existing Pinecone indexes
- Can search previously indexed content
- Requires: Pinecone API key only
- Target users: End users, researchers, analysts

## Technical Requirements

### 1. Authentication & Configuration

**Requirement**: Secure, flexible authentication supporting both operation modes with environment variable support

**Owner Mode Authentication:**
- Google Drive OAuth2 credentials with `drive.readonly` scope
- Pinecone API key for vector database operations
- Secure token storage in `~/.config/gdrive-pinecone-search/`

**Connected Mode Authentication:**
- Pinecone API key only
- No Google Drive access required

**Configuration Schema:**
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

**Environment Variables Support:**
```bash
# Required for Owner Mode
GDRIVE_CREDENTIALS_JSON="path/to/credentials.json"
PINECONE_API_KEY="your_pinecone_api_key"
PINECONE_DENSE_INDEX_NAME="company-gdrive-dense-index"
PINECONE_SPARSE_INDEX_NAME="company-gdrive-sparse-index"

# Optional Settings
CHUNK_SIZE="450"
CHUNK_OVERLAP="75"
RERANKING_MODEL="pinecone-rerank-v0"
```

**Technical Implementation:**
- Use `google-auth-oauthlib` for OAuth2 flow
- Store configuration in `~/.config/gdrive-pinecone-search/config.json`
- Support precedence: CLI args > env vars > config file
- Validate API credentials on command execution
- Automatic `.env` file loading from CLI directory

### 2. Google Drive Integration (Owner Mode)

**Requirement**: Comprehensive Google Drive file access with intelligent change tracking

**Google Workspace Files (Primary):**
- Google Docs (`application/vnd.google-apps.document`) → exported as `text/plain`
- Google Sheets (`application/vnd.google-apps.spreadsheet`) → exported as `text/csv`
- Google Slides (`application/vnd.google-apps.presentation`) → exported as `text/plain`

**Plaintext Files (Extended Support):**
- **Text files**: `.txt`, `.md`, `.rst`, `.log`
- **Configuration files**: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`
- **Code files**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.go`, `.rs`, `.rb`, `.php`, `.sh`, `.bash`, `.zsh`, `.ps1`, `.bat`, `.cmd`
- **Web files**: `.html`, `.htm`, `.css`, `.xml`
- **Documentation**: `.tex` (LaTeX source)
- **Data files**: `.csv`, `.tsv`, `.sql`

**File Type Categories:**
- `code` - Programming language files
- `config` - Configuration and data files
- `txt` - Plain text and documentation
- `web` - Web development files
- `data` - Data and database files
- `document` - Document files (LaTeX)

**API Integration:**
- Google Drive API v3 with `files.list()` and `files.export()`
- Rate limiting: 100 requests/100 seconds per user
- Exponential backoff with `tenacity` for failed requests
- Automatic character encoding detection for plaintext files
- MIME type fallback for file type detection

### 3. Document Processing

**Requirement**: Intelligent text processing optimized for hybrid search

**Text Chunking:**
- **Chunk Size**: 450 tokens (configurable, optimized for `multilingual-e5-large`)
- **Overlap**: 75 tokens (configurable, ~17% overlap for context preservation)
- **Tokenizer**: `tiktoken` with `cl100k_base` encoding
- **Strategy**: Sentence-boundary aware splitting to maintain semantic coherence

**Content Preprocessing:**
- **JSON files**: Formatted with proper indentation for readability
- **Code files**: Preserve syntax structure, comments, and formatting
- **CSV files**: Intelligent column handling and structure preservation
- **Configuration files**: Maintain structure and comment preservation
- **Google Workspace**: Use native Drive API export for optimal formatting

**Metadata Extraction:**
- File name, type, and Google Drive file ID
- Last modified timestamp for incremental updates
- Web view link for direct browser access
- Chunk index for vector uniqueness and reconstruction

### 4. Pinecone Integration (Hybrid Search)

**Requirement**: Production-ready hybrid search implementation following Pinecone best practices

**Index Architecture:**

**Dense Index:**
- **Model**: `multilingual-e5-large` (integrated embedding)
- **Dimensions**: 1024
- **Metric**: `cosine` similarity
- **Purpose**: Semantic understanding, context, and relationships

**Sparse Index:**
- **Model**: `pinecone-sparse-english-v0` (integrated embedding)
- **Dimensions**: 1024
- **Metric**: `dotproduct` for sparse vectors
- **Purpose**: Exact keyword matching and technical terminology

**Vector Storage Strategy:**
- Consistent vector IDs across both indexes: `{file_id}#{chunk_index}`
- Minimal metadata to optimize storage costs and performance
- Automatic deduplication during result merging
- Batch upsert operations for efficiency

### 5. Hybrid Search Implementation

**Requirement**: Superior search relevance through intelligent combination of dense and sparse results

**Search Algorithm:**
1. **Dual Embedding Generation**: Create both dense and sparse embeddings for user query
2. **Parallel Index Queries**: Query dense and sparse indexes simultaneously
3. **Result Merging**: Deduplicate by vector ID, preserve highest relevance scores
4. **Intelligent Reranking**: Apply Pinecone's hosted reranking model for final relevance

**Reranking Implementation:**
- **Model**: `pinecone-rerank-v0` (hosted, no local computation required)
- **Input**: Original query text + merged document chunks
- **Rate Limiting**: 100 requests/minute with exponential backoff
- **Fallback Strategy**: Return merged results if reranking fails
- **Result Limits**: Maximum 100 results for optimal reranking performance

**Search Features:**
- File type filtering by extension or category
- Configurable result limits (default: 10, maximum: 100)
- Interactive result selection with detailed score breakdown
- Direct file opening in browser via web view links

### 6. Incremental Updates & Refresh

**Requirement**: Efficient change detection and processing for large document collections

**Change Detection Strategy:**
- Track `last_refresh_time` in index metadata
- Query Google Drive API for files modified since last refresh
- Handle timezone differences and daylight saving time
- Compare file modification timestamps with stored values

**Update Processing:**
- **New Files**: Full indexing with chunking and vector generation
- **Modified Files**: Complete re-indexing (remove old chunks, add new ones)
- **Deleted Files**: Remove all associated vectors from both indexes
- **Batch Processing**: Configurable batch sizes for memory management

**Refresh Command Options:**
- `--since YYYY-MM-DD`: Override automatic last refresh time
- `--force-full`: Process all files regardless of modification timestamps
- `--dry-run`: Preview changes without executing operations
- `--file-types`: Limit refresh to specific file types or categories
- `--limit`: Process maximum number of files (useful for testing)

### 7. CLI Interface & User Experience

**Requirement**: Intuitive, production-ready command-line interface

**Core Commands:**
```bash
# Setup and Configuration
gdrive-pinecone-search owner setup [options]    # Configure owner mode
gdrive-pinecone-search connect [options]        # Configure connected mode

# Document Management (Owner Mode)
gdrive-pinecone-search owner index [options]    # Initial indexing
gdrive-pinecone-search owner refresh [options]  # Incremental updates

# Search (Both Modes)
gdrive-pinecone-search search <query> [options] # Hybrid search

# Status and Information
gdrive-pinecone-search status                   # System status
```

**Global Options:**
- `--help`: Context-sensitive help for all commands
- `--verbose`: Enable detailed logging and debug information
- `--config`: Specify custom configuration file path

**File Processing Options:**
- `--file-types`: Comma-separated file types or categories
- `--limit`: Maximum number of files to process
- `--dry-run`: Preview operations without execution

**Search Options:**
- `--limit`: Number of search results (default: 10, max: 100)
- `--file-types`: Filter results by file type or category
- `--interactive`: Enable interactive result selection

### 8. Error Handling & Reliability

**Requirement**: Robust error handling for production environments

**API Rate Limiting:**
- Google Drive API: 100 requests/100 seconds per user
- Pinecone API: Respect service-specific limits
- Reranking API: 100 requests/minute
- Exponential backoff with jitter for all API calls

**Error Recovery:**
- Graceful handling of network failures and API errors
- Partial result returns when possible
- Clear, actionable error messages for users
- Automatic retry logic with configurable backoff

**Logging and Monitoring:**
- Structured logging with `rich` console output
- Debug mode for troubleshooting
- Progress indicators for long-running operations
- Error reporting without exposing sensitive credentials

### 9. Performance & Scalability

**Requirement**: Efficient processing of large document collections

**Optimization Strategies:**
- Parallel API calls where possible
- Efficient memory management for large files
- Smart deduplication before expensive reranking operations
- Configurable batch sizes for processing and API calls

**Storage Efficiency:**
- Minimal metadata design (40-50% reduction vs. verbose metadata)
- Efficient vector ID scheme for fast lookups
- Automatic cleanup of orphaned vectors during refresh

**Memory Management:**
- Stream processing for large files
- Chunked API requests to prevent memory exhaustion
- Garbage collection optimization for large operations

### 10. Testing & Quality Assurance

**Requirement**: Comprehensive testing framework ensuring reliability

**Test Coverage:**
- **91 comprehensive tests** covering all CLI functionality
- **Sub-second execution** (0.49 seconds) with proper mocking
- **Behavioral validation** testing user-facing functionality
- **Implementation independence** for maintainability

**Test Categories:**
- **Smoke tests**: Basic functionality verification
- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end CLI workflows
- **Edge case testing**: Invalid inputs and boundary conditions
- **User experience testing**: Help messages, error handling, success feedback

**Quality Standards:**
- No external API calls during testing (proper mocking)
- Realistic mock scenarios reflecting real-world usage
- Continuous integration compatibility
- Coverage reporting and quality metrics

## Dependencies & Environment

**Python Requirements:**
- **Python 3.8+** (tested with Python 3.8 through 3.13)
- Cross-platform compatibility (Windows, macOS, Linux)

**Core Dependencies:**
```txt
click>=8.1.0                    # CLI framework
google-auth>=2.23.0             # Google authentication
google-auth-oauthlib>=1.1.0     # OAuth2 flow for Google Drive
google-auth-httplib2>=0.1.1     # HTTP transport for Google APIs
google-api-python-client>=2.100.0 # Google Drive API client
pinecone>=7.0.0                 # Pinecone vector database
tiktoken>=0.5.1                 # Token counting for chunking
rich>=13.6.0                    # Enhanced terminal UI
python-dotenv>=1.0.0            # Environment variable loading
pydantic>=2.5.0                 # Data validation
tenacity>=8.2.3                 # Retry logic with backoff
chardet>=5.2.0                  # Character encoding detection
python-magic>=0.4.27            # MIME type detection
pytest>=7.0.0                   # Testing framework
```

**Platform-Specific Requirements:**
- **macOS**: `brew install libmagic`
- **Ubuntu/Debian**: `sudo apt-get install libmagic1`
- **Windows**: No additional requirements (python-magic-bin included)

**Installation Process:**
```bash
# Clone repository
git clone <repository-url>
cd google-drive-pinecone-integration/cli

# Set up virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies and CLI
pip install -r requirements.txt
pip install -e .

# Verify installation
gdrive-pinecone-search --help
pytest tests/ -v  # Should pass 91 tests
```

## Configuration Examples

### Environment Variables (.env file)
```bash
# Pinecone Configuration
PINECONE_API_KEY="pcsk-abc123..."
PINECONE_DENSE_INDEX_NAME="company-docs-dense"
PINECONE_SPARSE_INDEX_NAME="company-docs-sparse"

# Google Drive Configuration (Owner Mode)
GDRIVE_CREDENTIALS_JSON="/path/to/credentials.json"

# Optional Performance Tuning
CHUNK_SIZE="450"
CHUNK_OVERLAP="75"
RERANKING_MODEL="pinecone-rerank-v0"
```

### Configuration File Schema
```json
{
  "mode": "owner",
  "connection": {
    "pinecone_api_key": "pcsk-abc123...",
    "dense_index_name": "company-docs-dense",
    "sparse_index_name": "company-docs-sparse",
    "created_at": "2024-01-15T12:00:00Z"
  },
  "owner_config": {
    "google_drive_credentials_path": "/path/to/credentials.json",
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

## Metadata Structure

**Vector Metadata (Optimized for Performance):**
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

**Field Descriptions:**
- **`file_id`**: Google Drive file identifier (required for refresh operations)
- **`file_name`**: Human-readable name for search result display
- **`file_type`**: File type for filtering (docs, sheets, slides, py, json, etc.)
- **`chunk_index`**: Position within document (ensures vector uniqueness)
- **`modified_time`**: Last modification timestamp (enables incremental updates)
- **`web_view_link`**: Direct link for browser access

## Future Roadmap & Enhancement Opportunities

**Immediate Development Opportunities**:
- **Syntax-Aware Chunking**: Intelligent chunking that respects code structure and syntax boundaries for programming files
- **Advanced File Selection UI**: Web-based interface for folder/file selection with drag-and-drop support
- **Multi-Architecture Builds**: PyInstaller/Nuitka builds for multiple platforms
- **GitHub Actions CI/CD**: Automated testing and release pipeline
- **Performance Metrics**: Search analytics and performance monitoring for both modes

**Assistant Mode Enhancements**:
- **Custom Instructions**: Assistant behavior customization for domain-specific responses
- **Evaluation Integration**: Automated response quality assessment using Assistant evaluation features
- **Context Snippet Retrieval**: Access to underlying context snippets for transparency using [Assistant context retrieval](https://docs.pinecone.io/guides/assistant/retrieve-context-snippets)
- **Advanced Metadata Filtering**: Leverage Assistant's metadata filtering for precise queries
- **Conversation Management**: Persistent conversation history and context management
- **Multimodal Search Enhancement**: Extend search capabilities to handle images and audio when Assistant API supports retrieval

**Medium-term Enhancements**:
- **Web UI Implementation**: Complete the web-ui/ directory with modern interface supporting both Search and Assistant modes
- **Advanced Search Features**: Boolean operators, date ranges, advanced filters for Search mode
- **Custom Embedding Models**: Support for user-provided embedding models in Search mode
- **Multi-language Support**: Enhanced support for non-English content in both modes
- **File Synchronization**: Real-time sync with Google Drive changes using webhooks

**Long-term Strategic Vision**:
- **Multi-tenant Architecture**: Support for large organizations with multiple teams and isolated assistants
- **Enterprise Integration**: SharePoint, Confluence, and other document sources for both processing modes
- **Advanced Analytics**: Search behavior insights and content recommendations across both modes
- **Scalability Improvements**: Distributed processing for very large document collections
- **Hybrid Workflows**: Seamless switching between Search and Assistant modes within single workflows

**Technical Debt & Optimization**:
- **Batch Processing**: Enhanced batch operations for better performance in both modes
- **Memory Optimization**: Further reduce memory footprint for large operations
- **API Efficiency**: Optimize API calls and reduce redundant operations across Google Drive and Pinecone APIs
- **Error Recovery**: Enhanced error recovery and resume capabilities for interrupted operations

## Development Notes

**Testing Strategy**:
- **Fast Test Suite**: 91 tests running in 0.49 seconds (was 20+ minutes)
- **Behavioral Validation**: Tests verify actual functionality, not just execution
- **Comprehensive Coverage**: Unit, integration, and end-to-end CLI testing with realistic scenarios
- **Dependency Injection**: Service factory pattern for easy mocking
- **No Real API Calls**: All external dependencies properly mocked
- **Implementation Independent**: Tests focus on outputs, not internal methods
- **User-Centric**: Validates help messages, error handling, and success feedback
- **Performance Optimized**: Immediate developer feedback with meaningful coverage

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

---

**For implementation details and completion status, see [COMPLETION_SUMMARY.md](cli/COMPLETION_SUMMARY.md)**
