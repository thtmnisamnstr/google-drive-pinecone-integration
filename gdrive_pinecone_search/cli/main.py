"""Main CLI entry point for Google Drive to Pinecone integration."""

import click
import sys
from pathlib import Path

from ..utils.config_manager import ConfigManager
from ..utils.exceptions import GDriveSearchError
from .commands.connect import connect
from .commands.index import index
from .commands.refresh import refresh
from .commands.search import search
from .commands.status import status
from .ui.progress import show_error_panel
from .ui.results import display_help_text


@click.group()
@click.version_option(version="1.0.0", prog_name="gdrive-pinecone-search")
@click.option('--config', '-c', 
              help='Path to configuration file')
def main(config):
    """
    Google Drive to Pinecone CLI for semantic search.
    
    This tool allows you to index Google Drive documents into Pinecone for semantic search.
    It supports both owner mode (full access) and connected mode (read-only access).
    
    For more information, visit: https://github.com/your-repo/gdrive-pinecone-search
    """
    pass


@main.command()
@click.argument('index_name')
@click.option('--validate', is_flag=True, 
              help='Validate index compatibility')
@click.option('--api-key', '-k', 
              help='Pinecone API key (overrides environment variable)')
def connect_cmd(index_name, validate, api_key):
    """Connect to an existing Pinecone index."""
    connect.callback(index_name, validate, api_key)


@main.command()
@click.option('--limit', '-l', type=int, 
              help='Limit the number of files to process')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types (docs,sheets,slides)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be indexed without making changes')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def index_cmd(limit, file_types, dry_run, credentials):
    """Index Google Drive files into Pinecone (Owner mode only)."""
    index.callback(limit, file_types, dry_run, credentials)


@main.command()
@click.option('--since', '-s', 
              help='Process files modified since this date (YYYY-MM-DD)')
@click.option('--force-full', '-f', is_flag=True, 
              help='Force full refresh of all files')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def refresh_cmd(since, force_full, credentials):
    """Refresh index with updated Google Drive files (Owner mode only)."""
    refresh.callback(since, force_full, credentials)


@main.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, 
              help='Number of results to return (default: 10)')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types to search (docs,sheets,slides)')
@click.option('--min-score', '-s', type=float, default=0.7, 
              help='Minimum similarity score (0.0-1.0, default: 0.7)')
@click.option('--interactive', '-i', is_flag=True, 
              help='Enable interactive result selection')
def search_cmd(query, limit, file_types, min_score, interactive):
    """Search indexed Google Drive content."""
    search.callback(query, limit, file_types, min_score, interactive)


@main.command()
@click.option('--verbose', '-v', is_flag=True, 
              help='Show detailed configuration information')
@click.option('--test-connections', '-t', is_flag=True, 
              help='Test all configured connections')
def status_cmd(verbose, test_connections):
    """Show current configuration and connection status."""
    status.callback(verbose, test_connections)


@main.command()
def help_cmd():
    """Show detailed help information."""
    display_help_text()


@main.command()
@click.option('--credentials', '-c', required=True,
              help='Path to Google Drive credentials JSON file')
@click.option('--api-key', '-k', required=True,
              help='Pinecone API key')
@click.option('--index-name', '-i', required=True,
              help='Pinecone index name')
def setup_owner(credentials, api_key, index_name):
    """Set up owner mode with Google Drive and Pinecone credentials."""
    try:
        config_manager = ConfigManager()
        config_manager.set_owner_config(credentials, api_key, index_name)
        
        from ..ui.progress import show_success_panel
        show_success_panel(
            "Owner Mode Setup",
            f"Successfully configured owner mode with:\n"
            f"• Google Drive credentials: {credentials}\n"
            f"• Pinecone index: {index_name}"
        )
        
    except Exception as e:
        show_error_panel("Setup Error", f"Failed to set up owner mode: {e}")


@main.command()
@click.option('--api-key', '-k', required=True,
              help='Pinecone API key')
@click.option('--index-name', '-i', required=True,
              help='Pinecone index name')
def setup_connected(api_key, index_name):
    """Set up connected mode with Pinecone credentials."""
    try:
        config_manager = ConfigManager()
        config_manager.set_connection_config(api_key, index_name)
        
        from ..ui.progress import show_success_panel
        show_success_panel(
            "Connected Mode Setup",
            f"Successfully configured connected mode with index: {index_name}"
        )
        
    except Exception as e:
        show_error_panel("Setup Error", f"Failed to set up connected mode: {e}")


def main_wrapper():
    """Wrapper for the main function to handle exceptions gracefully."""
    try:
        main()
    except GDriveSearchError as e:
        show_error_panel("Error", str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        show_error_panel("Interrupted", "Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main_wrapper() 