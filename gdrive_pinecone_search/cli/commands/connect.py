"""Connect command for connecting to existing Pinecone indexes."""

import click
from typing import Optional

from ...utils.config_manager import ConfigManager
from ...utils.connection_manager import ConnectionManager
from ...utils.exceptions import (
    AuthenticationError, 
    IndexNotFoundError, 
    IncompatibleIndexError,
    ConfigurationError
)
from ..ui.progress import show_status_panel, show_error_panel, show_success_panel, show_connection_status


@click.command()
@click.argument('index_name')
@click.option('--validate', is_flag=True, 
              help='Validate index compatibility')
@click.option('--api-key', '-k', 
              help='Pinecone API key (overrides environment variable)')
def connect(index_name: str, validate: bool, api_key: Optional[str]):
    """
    Connect to an existing Pinecone index.
    
    This command allows you to connect to an existing Pinecone index for search operations.
    You can use this in "connected mode" to search an index that was created by someone else.
    
    Examples:
            gdrive-pinecone-search connect my-company-index
    gdrive-pinecone-search connect my-index --validate
    """
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Get API key from parameter or environment
        pinecone_api_key = api_key or config_manager.get_pinecone_api_key()
        if not pinecone_api_key:
            show_error_panel(
                "Configuration Error",
                "Pinecone API key not found. Please set PINECONE_API_KEY environment variable or use --api-key option."
            )
            return
        
        # Initialize connection manager
        connection_manager = ConnectionManager(config_manager)
        
        # Validate connection
        show_status_panel("Connecting", f"Validating connection to index '{index_name}'...")
        
        try:
            connection_manager.validate_pinecone_connection(pinecone_api_key, index_name)
            show_success_panel("Connection Successful", f"Successfully connected to index '{index_name}'")
        except (AuthenticationError, IndexNotFoundError, IncompatibleIndexError) as e:
            show_error_panel("Connection Failed", str(e))
            return
        
        # Store connection configuration
        config_manager.set_connection_config(pinecone_api_key, index_name)
        
        # Show connection status
        status = connection_manager.get_connection_status()
        show_connection_status(status)
        
        # Additional validation if requested
        if validate:
            show_status_panel("Validation", "Performing additional compatibility checks...")
            
            try:
                # Test a sample query
                from ...services.pinecone_service import PineconeService
                pinecone_service = PineconeService(pinecone_api_key, index_name)
                
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
                
                show_success_panel("Validation Complete", "Index is compatible and ready for search operations")
                
                # Display validation details
                from ..ui.progress import show_info_table
                show_info_table("Index Information", validation_info)
                
            except Exception as e:
                show_error_panel("Validation Warning", f"Index validation failed: {e}")
        
        show_success_panel(
            "Setup Complete", 
            f"Successfully connected to Pinecone index '{index_name}'. You can now use the search command."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 