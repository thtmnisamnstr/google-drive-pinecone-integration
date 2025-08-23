"""Connect command for connecting to existing Pinecone indexes."""

import click
from typing import Optional
from dotenv import load_dotenv

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
@click.option('--dense-index-name', '-d',
              help='Pinecone dense index name (or set PINECONE_DENSE_INDEX_NAME env var)')
@click.option('--sparse-index-name', '-s',
              help='Pinecone sparse index name (or set PINECONE_SPARSE_INDEX_NAME env var)')
@click.option('--validate', is_flag=True, 
              help='Validate index compatibility')
@click.option('--api-key', '-k', 
              help='Pinecone API key (overrides environment variable)')
def connect(dense_index_name: Optional[str], sparse_index_name: Optional[str], validate: bool, api_key: Optional[str]):
    """
    Connect to existing Pinecone dense and sparse indexes for hybrid search.
    
    This command allows you to connect to existing Pinecone indexes for hybrid search operations.
    You can use this in "connected mode" to search indexes that were created by someone else.
    
    Examples:
            gdrive-pinecone-search connect --dense-index-name my-dense-index --sparse-index-name my-sparse-index
    gdrive-pinecone-search connect --dense-index-name my-dense --sparse-index-name my-sparse --validate
    gdrive-pinecone-search connect --validate  # uses PINECONE_DENSE_INDEX_NAME and PINECONE_SPARSE_INDEX_NAME from environment
    """
    try:
        # Ensure .env variables are loaded for this command as well
        # This is safe to call multiple times and helps when this command is invoked directly.
        load_dotenv()
        
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Get API key from parameter or environment
        import os
        pinecone_api_key = api_key or os.getenv('PINECONE_API_KEY')
        if not pinecone_api_key:
            show_error_panel(
                "Configuration Error",
                "Pinecone API key not found. Please set PINECONE_API_KEY environment variable or use --api-key option."
            )
            return
        
        # Get index names from options or environment
        final_dense_index_name = dense_index_name or os.getenv('PINECONE_DENSE_INDEX_NAME')
        final_sparse_index_name = sparse_index_name or os.getenv('PINECONE_SPARSE_INDEX_NAME')
        
        if not final_dense_index_name:
            show_error_panel(
                "Configuration Error",
                "Pinecone dense index name not found. Use --dense-index-name option or set PINECONE_DENSE_INDEX_NAME environment variable."
            )
            return
            
        if not final_sparse_index_name:
            show_error_panel(
                "Configuration Error",
                "Pinecone sparse index name not found. Use --sparse-index-name option or set PINECONE_SPARSE_INDEX_NAME environment variable."
            )
            return
        
        # Initialize connection manager
        connection_manager = ConnectionManager(config_manager)
        
        # Validate connections
        show_status_panel("Connecting", f"Validating connections to indexes...")
        
        try:
            # Validate dense index
            connection_manager.validate_pinecone_connection(pinecone_api_key, final_dense_index_name, is_sparse=False)
            show_success_panel("Dense Index Connected", f"Successfully connected to dense index '{final_dense_index_name}'")
            
            # Validate sparse index
            connection_manager.validate_pinecone_connection(pinecone_api_key, final_sparse_index_name, is_sparse=True)
            show_success_panel("Sparse Index Connected", f"Successfully connected to sparse index '{final_sparse_index_name}'")
            
        except (AuthenticationError, IndexNotFoundError, IncompatibleIndexError) as e:
            show_error_panel("Connection Failed", str(e))
            return
        
        # Store connection configuration
        config_manager.set_connection_config(pinecone_api_key, final_dense_index_name, final_sparse_index_name)
        
        # Show connection status (but avoid recursion by not calling get_connection_status)
        show_success_panel("Configuration Stored", "Connection configuration has been saved successfully")
        
        # Additional validation if requested
        if validate:
            show_status_panel("Validation", "Performing additional compatibility checks...")
            
            try:
                # Test hybrid service
                from ...services.search_service import SearchService
                search_service = SearchService(pinecone_api_key, final_dense_index_name, final_sparse_index_name)
                
                # Get index stats
                stats = search_service.get_index_stats()
                total_vectors = stats.get('total_vectors', 0)
                
                # Get index metadata and models
                metadata = search_service.get_index_metadata()
                models = search_service.get_index_models()
                
                validation_info = {
                    "Total Vectors": total_vectors,
                    "Dense Index": final_dense_index_name,
                    "Sparse Index": final_sparse_index_name,
                    "Dense Model": models['dense_model'],
                    "Sparse Model": models['sparse_model'],
                    "Last Updated": metadata.get('last_refresh_time', 'Unknown') if metadata else 'Unknown',
                    "Indexed Files": metadata.get('total_files_indexed', 'Unknown') if metadata else 'Unknown'
                }
                
                show_success_panel("Validation Complete", "Indexes are compatible and ready for hybrid search operations")
                
                # Display validation details
                from ..ui.progress import show_info_table
                show_info_table("Index Information", validation_info)
                
            except Exception as e:
                show_error_panel("Validation Warning", f"Index validation failed: {e}")
        
        show_success_panel(
            "Setup Complete", 
            f"Successfully connected to Pinecone indexes for hybrid search. You can now use the search command."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 