"""Main CLI entry point for Google Drive to Pinecone integration."""

import click
import sys
from pathlib import Path
from dotenv import load_dotenv

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
    # Load environment variables from .env file if it exists
    load_dotenv()
    pass


@main.command()
@click.option('--index-name', '-i',
              help='Pinecone index name (or set PINECONE_INDEX_NAME env var)')
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
@click.option('--credentials', '-c',
              help='Path to Google Drive credentials JSON file (or set GDRIVE_CREDENTIALS_JSON env var)')
@click.option('--api-key', '-k',
              help='Pinecone API key (or set PINECONE_API_KEY env var)')
@click.option('--index-name', '-i',
              help='Pinecone index name (or set PINECONE_INDEX_NAME env var)')
@click.option('--validate', is_flag=True,
              help='Validate connections after setup')
def setup_owner(credentials, api_key, index_name, validate):
    """Set up owner mode with Google Drive and Pinecone credentials."""
    import os
    from .ui.progress import show_status_panel, show_success_panel, show_error_panel, show_connection_status
    from ..utils.connection_manager import ConnectionManager
    from ..utils.exceptions import AuthenticationError, IndexNotFoundError, IncompatibleIndexError
    
    try:
        
        # Get values from command line or environment variables
        credentials_path = credentials or os.getenv('GDRIVE_CREDENTIALS_JSON')
        pinecone_api_key = api_key or os.getenv('PINECONE_API_KEY')
        pinecone_index_name = index_name or os.getenv('PINECONE_INDEX_NAME')
        
        # Validate that we have all required values
        if not credentials_path:
            show_error_panel("Configuration Error", 
                "Google Drive credentials not provided. Use --credentials option or set GDRIVE_CREDENTIALS_JSON environment variable.")
            return
        
        if not pinecone_api_key:
            show_error_panel("Configuration Error", 
                "Pinecone API key not provided. Use --api-key option or set PINECONE_API_KEY environment variable.")
            return
        
        if not pinecone_index_name:
            show_error_panel("Configuration Error", 
                "Pinecone index name not provided. Use --index-name option or set PINECONE_INDEX_NAME environment variable.")
            return
        
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Store the configuration first
        show_status_panel("Configuration", "Storing credentials...")
        config_manager.set_owner_config(credentials_path, pinecone_api_key, pinecone_index_name)
        
        # Initialize connection manager
        connection_manager = ConnectionManager(config_manager)
        
        # Validate connections if requested
        if validate:
            show_status_panel("Validation", "Validating Google Drive and Pinecone connections...")
            
            # Test Google Drive connection
            try:
                from ..services.auth_service import AuthService
                auth_service = AuthService(credentials_path)
                user_info = auth_service.get_user_info()
                show_success_panel("Google Drive", f"✓ Connected as: {user_info.get('emailAddress', 'Unknown')}")
            except Exception as e:
                show_error_panel("Google Drive", f"✗ Connection failed: {e}")
                return
            
            # Test Pinecone connection
            try:
                connection_manager.validate_pinecone_connection(pinecone_api_key, pinecone_index_name)
                show_success_panel("Pinecone", f"✓ Successfully connected to index '{pinecone_index_name}'")
            except (AuthenticationError, IndexNotFoundError, IncompatibleIndexError) as e:
                show_error_panel("Pinecone", f"✗ Connection failed: {e}")
                return
            
            # Show connection status
            status = connection_manager.get_connection_status()
            show_connection_status(status)
            
            # Additional Pinecone validation
            try:
                from ..services.pinecone_service import PineconeService
                pinecone_service = PineconeService(pinecone_api_key, pinecone_index_name)
                
                # Get index stats
                stats = pinecone_service.get_index_stats()
                total_vectors = stats.get('total_vector_count', 0)
                
                # Get index metadata
                metadata = pinecone_service.get_index_metadata()
                
                validation_info = {
                    "Total Vectors": total_vectors,
                    "Embedding Model": metadata.get('embedding_model', 'Unknown') if metadata else 'Unknown',
                    "Last Updated": metadata.get('last_refresh_time', 'Unknown') if metadata else 'Unknown',
                    "Indexed Files": metadata.get('total_files_indexed', 'Unknown') if metadata else 'Unknown'
                }
                
                show_success_panel("Validation Complete", "All connections validated successfully")
                
                # Display validation details
                from .ui.progress import show_info_table
                show_info_table("Index Information", validation_info)
                
            except Exception as e:
                show_error_panel("Validation Warning", f"Index validation failed: {e}")
        
        show_success_panel(
            "Owner Mode Setup Complete",
            f"Successfully configured owner mode with:\n"
            f"• Google Drive credentials: {credentials_path}\n"
            f"• Pinecone index: {pinecone_index_name}\n\n"
            f"You can now use the index and refresh commands."
        )
        
    except Exception as e:
        show_error_panel("Setup Error", f"Failed to set up owner mode: {e}")





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