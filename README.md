# Google Drive Pinecone Integration

A comprehensive solution for indexing and searching Google Drive content using Pinecone's hybrid search capabilities.

## Overview

This monorepo contains multiple components for integrating Google Drive with Pinecone vector search:

- **CLI Tool**: Command-line interface for indexing and searching Google Drive files
- **Web UI**: Web-based interface (coming eventually)

## Projects

### [CLI Tool](./cli/)

A powerful command-line interface that provides:

- **Hybrid Search**: Combines dense semantic embeddings and sparse keyword embeddings for superior search results
- **Smart Indexing**: Incremental updates that only process changed files
- **Multiple File Types**: Support for Google Docs, Sheets, and Slides
- **Dual Modes**: Owner mode (full access) and Connected mode (read-only search)
- **Reranking**: Uses Pinecone's hosted reranking model for improved relevance

**Key Features:**
- Automatic document chunking with overlap
- Integrated embedding models (no API calls needed)
- Rate limiting and error handling
- Comprehensive logging and progress tracking

[View CLI Documentation →](./cli/)

### [Web UI](./web-ui/)

A web-based interface for the Google Drive Pinecone Integration (coming eventually).

[View Web UI →](./web-ui/)

## Getting Started

1. **CLI Tool**: Start with the [CLI documentation](./cli/) for setup and usage instructions
2. **Web UI**: Coming eventually

## Architecture

The project uses Pinecone's hybrid search approach:
- **Dense Vectors**: Semantic understanding using multilingual embeddings
- **Sparse Vectors**: Keyword matching for precise term retrieval
- **Reranking**: Final relevance scoring using Pinecone's hosted model

## License

MIT License - see [LICENSE](LICENSE) for details.
