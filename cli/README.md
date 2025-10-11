# Google Drive to Pinecone CLI

The CLI indexes Google Drive files into Pinecone hybrid search (dense + sparse) and exposes commands to manage configuration, run indexing pipelines, and query results directly from the terminal.

## Overview

- Hybrid search (integrated embeddings + Pinecone reranking)
- Owner mode for Google Drive indexing; connected mode for search-only access
- Incremental refresh that detects new, modified, and removed files
- Support for 39 text-friendly file types (Google Workspace + 36 plaintext extensions)

## 1. Prerequisites

- Python 3.8+
- Pinecone account & API key
- Google Cloud project with Drive API enabled (owner mode only)

## 2. Installation

```bash
git clone <repository-url>
cd google-drive-pinecone-integration/cli

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
pip install -e .

gdrive-pinecone-search --help
```

The `requirements.txt` file no longer depends on `python-magic`; MIME handling uses filename heuristics and `chardet` for encoding detection.
```

## 3. Configure Credentials

Set environment variables (recommended)

```bash
export PINECONE_API_KEY="..."
export PINECONE_DENSE_INDEX_NAME="corp-dense"
export PINECONE_SPARSE_INDEX_NAME="corp-sparse"
export GDRIVE_CREDENTIALS_JSON="/path/to/credentials.json"  # owner mode

gdrive-pinecone-search owner setup --validate
```

Or pass flags directly to the commands (see `--help`).

## 4. Core Commands

```bash
# Configure owner mode and validate Pinecone + Google Drive
gdrive-pinecone-search owner setup --credentials creds.json --api-key ... --dense-index-name ... --sparse-index-name ...

# Index Google Drive content (owner mode)
gdrive-pinecone-search owner index [--file-types docs,py,json] [--limit 100] [--dry-run]

# Refresh existing index using incremental change detection (owner mode)
gdrive-pinecone-search owner refresh [--since 2024-01-01] [--force-full]

# Connect to existing indexes for search-only usage
gdrive-pinecone-search connect --dense-index-name ... --sparse-index-name ...

# Hybrid search with reranking
gdrive-pinecone-search search "quarterly planning" [--file-types code] [--limit 20] [--interactive]

# Inspect current configuration and index stats
gdrive-pinecone-search status [--verbose] [--test-connections]
```

## 5. File Types & Filters

Supported identifiers include Google Workspace aliases (`docs`, `sheets`, `slides`) plus categories such as `code`, `config`, `txt`, `web`, and `data`. Pass a comma-separated list to `--file-types`; categories expand to their constituent extensions.

## 6. How Hybrid Search Works

1. Text is chunked (~450 tokens with overlap) and stored in Pinecone dense/sparse indexes using integrated embeddings.
2. Queries run against both indexes; results are merged, deduplicated, and reranked by Pinecone’s hosted model (`pinecone-rerank-v0`).
3. CLI output shows reranked score, dense score, and sparse score for transparency.

## 7. Troubleshooting

- Ensure `pip install -e .` completed successfully if the CLI command is missing.
- Verify `GDRIVE_CREDENTIALS_JSON` points to an OAuth credentials file with Drive access.
- If Pinecone calls fail, double-check API key and index names, confirm indexes use integrated embedding models, and rerun with `--verbose` to review automatic retry/backoff diagnostics.

## 8. Testing

```bash
pytest tests/ -q
```

Focused suites are available (e.g., `tests/test_cli_commands.py`, `tests/test_search_service_cleanup.py`). Tests rely on mocked services via the `MockServiceFactory`, automatically retry transient failures, and do not hit external APIs. As of Oct 2025 the suite contains 76 behavioral tests.

---

For detailed requirements and architecture, see `../REQUIREMENTS.md`.