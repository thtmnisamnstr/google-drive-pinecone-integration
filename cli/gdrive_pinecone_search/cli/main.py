"""Main CLI entry point for Google Drive to Pinecone integration."""

import click
import sys
from dotenv import load_dotenv

from ..utils.config_manager import ConfigManager
from ..utils.exceptions import GDriveSearchError
from .commands.connect import connect
from .commands.setup_owner import setup_owner
from .commands.index import index
from .commands.refresh import refresh
from .commands.search import search
from .commands.status import status
from .ui.progress import show_error_panel
from .ui.results import display_help_text


@click.group()
@click.option('--config', '-c', 
              help='Path to configuration file')
def main(config):
    """
    Google Drive to Pinecone CLI for hybrid search.
    
    This tool allows you to index Google Drive documents into Pinecone for hybrid search
    (combining dense and sparse vectors). It supports both owner mode (full access) 
    and connected mode (read-only access).
    
    For more information, visit: https://github.com/your-repo/gdrive-pinecone-search
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    pass


@main.group()
def owner():
    """Owner mode commands for full access to Google Drive and Pinecone."""
    pass


@owner.command()
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
@click.option('--api-key', '-k', 
              help='Pinecone API key')
@click.option('--dense-index-name', '-d', 
              help='Pinecone dense index name')
@click.option('--sparse-index-name', '-s', 
              help='Pinecone sparse index name')
@click.option('--validate', is_flag=True, 
              help='Validate all connections after setup')
def setup(credentials, api_key, dense_index_name, sparse_index_name, validate):
    """Set up owner mode with Google Drive and Pinecone credentials for hybrid search."""
    setup_owner.callback(credentials, api_key, dense_index_name, sparse_index_name, validate)


@owner.command()
@click.option('--limit', '-l', type=int, 
              help='Limit the number of files to process')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types (docs,sheets,slides)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be indexed without making changes')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def index_cmd(limit, file_types, dry_run, credentials):
    """Index Google Drive files into Pinecone using hybrid search (Owner mode only)."""
    index.callback(limit, file_types, dry_run, credentials)


@owner.command()
@click.option('--limit', '-l', type=int, 
              help='Limit the number of files to process')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types (docs,sheets,slides)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be indexed without making changes')
@click.option('--since', '-s', 
              help='Process files modified since this date (YYYY-MM-DD)')
@click.option('--force-full', '-f', is_flag=True, 
              help='Force full refresh of all files')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def refresh_cmd(limit, file_types, dry_run, since, force_full, credentials):
    """Refresh index with updated Google Drive files using hybrid search (Owner mode only)."""
    refresh.callback(limit, file_types, dry_run, since, force_full, credentials)


@main.command()
@click.option('--dense-index-name', '-d',
              help='Pinecone dense index name (or set PINECONE_DENSE_INDEX_NAME env var)')
@click.option('--sparse-index-name', '-s',
              help='Pinecone sparse index name (or set PINECONE_SPARSE_INDEX_NAME env var)')
@click.option('--validate', is_flag=True, 
              help='Validate index compatibility')
@click.option('--api-key', '-k', 
              help='Pinecone API key (overrides environment variable)')
def connect_cmd(dense_index_name, sparse_index_name, validate, api_key):
    """Connect to existing Pinecone dense and sparse indexes for hybrid search."""
    connect.callback(dense_index_name, sparse_index_name, validate, api_key)


@main.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, 
              help='Number of results to return (default: 10, max: 100)')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types to search (docs,sheets,slides)')
@click.option('--interactive', '-i', is_flag=True, 
              help='Enable interactive result selection')
def search_cmd(query, limit, file_types, interactive):
    """Search indexed Google Drive content using hybrid search with reranking."""
    search.callback(query, limit, file_types, interactive)


@main.command()
@click.option('--verbose', '-v', is_flag=True, 
              help='Show detailed configuration information')
@click.option('--test-connections', '-t', is_flag=True, 
              help='Test all configured connections')
def status_cmd(verbose, test_connections):
    """Show current configuration and connection status."""
    status.callback(verbose, test_connections)


@main.command()
def help():
    """Show detailed help information."""
    display_help_text()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except GDriveSearchError as e:
        show_error_panel("Error", str(e))
        sys.exit(1)
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        sys.exit(1) 