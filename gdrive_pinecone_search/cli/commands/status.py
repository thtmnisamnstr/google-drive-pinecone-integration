"""Status command for showing current configuration and connection status."""

import click
from typing import Optional

from ...utils.config_manager import ConfigManager
from ...utils.connection_manager import ConnectionManager
from ...utils.exceptions import ConfigurationError
from ..ui.progress import (
    show_status_panel, show_error_panel, show_connection_status,
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
    connection status, and index statistics.
    
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
        
        # Get connection status
        status_info = connection_manager.get_connection_status()
        
        # Display connection status
        show_connection_status(status_info)
        
        # Show configuration summary
        if verbose:
            show_configuration_summary(config.dict())
        
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
        
        # Show index statistics if connected
        if status_info['pinecone']['connected']:
            try:
                from ...services.pinecone_service import PineconeService
                
                pinecone_api_key = config_manager.get_pinecone_api_key()
                connection_config = config.connection
                pinecone_service = PineconeService(
                    pinecone_api_key,
                    connection_config.index_name
                )
                
                # Get index stats
                stats = pinecone_service.get_index_stats()
                show_index_stats(stats)
                
                # Get index metadata
                metadata = pinecone_service.get_index_metadata()
                if metadata:
                    from ..ui.progress import show_info_table
                    show_info_table("Index Metadata", metadata)
                
            except Exception as e:
                show_error_panel("Index Stats Error", f"Failed to get index statistics: {e}")
        
        # Show mode-specific information
        if config_manager.is_owner_mode():
            show_status_panel(
                "Owner Mode", 
                "You are in owner mode with full access to Google Drive and Pinecone."
            )
            
            if config.owner_config:
                owner_info = {
                    "Last Refresh": str(config.owner_config.last_refresh_time or "Never"),
                    "Files Indexed": str(config.owner_config.total_files_indexed),
                    "Credentials Path": config.owner_config.google_drive_credentials_path
                }
                
                from ..ui.progress import show_info_table
                show_info_table("Owner Information", owner_info)
        else:
            show_status_panel(
                "Connected Mode", 
                "You are in connected mode with read-only access to Pinecone index."
            )
        
        # Show next steps
        if not status_info['pinecone']['connected']:
            show_error_panel(
                "Next Steps",
                "Pinecone not connected. Use 'gdrive-pinecone-search connect <index-name>' to connect."
            )
        elif config_manager.is_owner_mode() and not status_info['google_drive']['connected']:
            show_error_panel(
                "Next Steps",
                "Google Drive not connected. Check your credentials configuration."
            )
        else:
            show_success_panel(
                "Ready",
                "All systems are ready! You can use the search command to find content."
            )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 