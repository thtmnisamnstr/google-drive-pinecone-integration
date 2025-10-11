# Google Drive Pinecone Integration

A comprehensive solution for indexing and searching Google Drive content using Pinecone's hybrid search capabilities.

## Overview

This monorepo contains the reference CLI implementation for integrating Google Drive with Pinecone hybrid search. A future web UI may live alongside the CLI, but today the repository focuses on the command-line experience.

## Projects

### [CLI Tool](./cli/)

The CLI lets you index and search Google Drive content using Pinecone’s hosted hybrid search (dense + sparse) and reranking services. Highlights include:

- Owner mode for indexing with Google Drive OAuth credentials
- Connected mode for search-only access using an existing Pinecone project
- Incremental refresh that tracks modified, new, and removed files
- Support for Google Docs/Sheets/Slides plus 36 plaintext extensions (39 total types)
- Integrated embeddings with Pinecone’s `create_index_for_model` workflow
- Behavioral test suite of 76 mocked CLI scenarios with dependency-injected services and automated retries

See the [CLI documentation](./cli/) for installation, configuration, and command help.

### Web UI (future)

A web experience is planned but not yet implemented. The `web-ui/` directory currently contains placeholders only.

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
