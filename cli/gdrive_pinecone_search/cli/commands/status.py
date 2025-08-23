"""Status command for showing current configuration and connection status."""

import click
from typing import Optional

from ...utils.config_manager import ConfigManager
from ...utils.connection_manager import ConnectionManager
from ...utils.exceptions import ConfigurationError
from ..ui.progress import (
    show_status_panel, show_error_panel, show_success_panel, show_connection_status,
    show_configuration_summary, show_index_stats
)


@click.command()
@click.option('--verbose', '-v', is_flag=True, 
              help='Show detailed configuration information')
@click.option('--test-connections', '-t', is_flag=True, 
              help='Test all configured connections')
def status(verbose: bool, test_connections: bool):
    """
    Show current configuration and connection status.
    
    This command displays information about your current configuration,
    connection status, and hybrid search index statistics.
    
    Examples:
            gdrive-pinecone-search status
    gdrive-pinecone-search status --verbose
    gdrive-pinecone-search status --test-connections
    """
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Get configuration
        config = config_manager.get_config()
        
        # Show basic status
        show_status_panel("Status", "Retrieving configuration and connection status...")
        
        # Initialize connection manager
        connection_manager = ConnectionManager(config_manager)
        
        # Get connection status (skip validation for now to avoid recursion)
        try:
            status_info = connection_manager.get_connection_status()
            # Display connection status
            show_connection_status(status_info)
        except Exception as e:
            show_error_panel("Connection Status Error", f"Could not retrieve connection status: {e}")
            status_info = {'pinecone': {'connected': False, 'error': str(e)}, 'google_drive': {'connected': False, 'error': str(e)}}
        
        # Show configuration summary
        if verbose:
            show_configuration_summary(config.model_dump())
        
        # Test connections if requested
        if test_connections:
            show_status_panel("Testing", "Testing all configured connections...")
            
            test_results = connection_manager.test_all_connections()
            
            # Display test results
            from ..ui.progress import show_info_table
            show_info_table("Connection Test Results", test_results)
            
            # Show detailed results
            if test_results['pinecone']:
                show_success_panel("Pinecone", "✓ Pinecone connection successful")
            else:
                show_error_panel("Pinecone", "✗ Pinecone connection failed")
            
            if config_manager.is_owner_mode():
                if test_results['google_drive']:
                    show_success_panel("Google Drive", "✓ Google Drive connection successful")
                else:
                    show_error_panel("Google Drive", "✗ Google Drive connection failed")
        
        # Show hybrid search index statistics if connected
        if status_info['pinecone']['connected']:
            try:
                from ...services.search_service import SearchService
                
                pinecone_api_key = config_manager.get_pinecone_api_key()
                dense_index_name = config_manager.get_dense_index_name()
                sparse_index_name = config_manager.get_sparse_index_name()
                reranking_model = config.settings.reranking_model
                
                search_service = SearchService(
                    pinecone_api_key,
                    dense_index_name,
                    sparse_index_name,
                    reranking_model
                )
                
                # Get hybrid index stats
                stats = search_service.get_index_stats()
                show_index_stats(stats)
                
                # Get index metadata
                metadata = search_service.get_index_metadata()
                if metadata:
                    from ..ui.progress import show_info_table
                    
                    # Format metadata for display
                    display_metadata = {
                        "Dense Index Model": "multilingual-e5-large (integrated)",
                        "Sparse Index Model": "pinecone-sparse-english-v0 (integrated)",
                        "Reranking Model": metadata.get('reranking_model', 'Unknown'),
                        "Chunk Size": metadata.get('chunk_size', 'Unknown'),
                        "Chunk Overlap": metadata.get('chunk_overlap', 'Unknown'),
                        "Last Updated": metadata.get('last_refresh_time', 'Unknown'),
                        "Indexed Files": metadata.get('total_files_indexed', 'Unknown'),
                        "Total Chunks": metadata.get('total_chunks_indexed', 'Unknown'),
                        "Indexed By": metadata.get('indexed_by', 'Unknown')
                    }
                    
                    show_info_table("Hybrid Search Configuration", display_metadata)
                
            except Exception as e:
                show_error_panel("Index Stats Error", f"Failed to get hybrid search index statistics: {e}")
        else:
            # Show basic index information even if not connected
            try:
                from ..ui.progress import show_info_table
                
                display_metadata = {
                    "Dense Index": config_manager.get_dense_index_name(),
                    "Sparse Index": config_manager.get_sparse_index_name(),
                    "Dense Index Model": "multilingual-e5-large (integrated)",
                    "Sparse Index Model": "pinecone-sparse-english-v0 (integrated)",
                    "Reranking Model": config.settings.reranking_model,
                    "Connection Status": "Not connected - check API key and index names"
                }
                
                show_info_table("Hybrid Search Configuration", display_metadata)
                
            except Exception as e:
                show_error_panel("Configuration Error", f"Failed to display configuration: {e}")
        

        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 