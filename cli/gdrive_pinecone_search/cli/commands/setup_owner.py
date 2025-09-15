"""Setup owner command for configuring full access mode."""

import click
from typing import Optional
from dotenv import load_dotenv

from ...utils.service_factory import get_service_factory
from ...utils.connection_manager import ConnectionManager
from ...utils.exceptions import (
    AuthenticationError, 
    IndexNotFoundError, 
    IncompatibleIndexError,
    ConfigurationError
)
from ..ui.progress import show_status_panel, show_error_panel, show_success_panel


@click.command()
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
def setup_owner(credentials: Optional[str], api_key: Optional[str], 
                dense_index_name: Optional[str], sparse_index_name: Optional[str], 
                validate: bool):
    """
    Set up owner mode with Google Drive and Pinecone credentials for hybrid search.
    
    This command configures the application for full access to both Google Drive
    and Pinecone, allowing you to index documents and perform hybrid search.
    
    Examples:
            gdrive-pinecone-search owner setup --credentials path/to/creds.json --api-key sk-... --dense-index-name my-dense --sparse-index-name my-sparse
    gdrive-pinecone-search owner setup --validate  # uses environment variables
    """
    try:
        # Ensure .env variables are loaded
        load_dotenv()
        
        # Get service factory and initialize configuration
        factory = get_service_factory()
        config_manager = factory.create_config_manager()
        
        # Get credentials from parameters or environment
        import os
        final_credentials = credentials or os.getenv('GDRIVE_CREDENTIALS_JSON')
        if not final_credentials:
            show_error_panel(
                "Configuration Error",
                "Google Drive credentials not found. Please set GDRIVE_CREDENTIALS_JSON environment variable or use --credentials option."
            )
            return
        
        # Get API key from parameters or environment
        final_api_key = api_key or os.getenv('PINECONE_API_KEY')
        if not final_api_key:
            show_error_panel(
                "Configuration Error",
                "Pinecone API key not found. Please set PINECONE_API_KEY environment variable or use --api-key option."
            )
            return
        
        # Get index names from parameters or environment
        final_dense_index_name = dense_index_name or os.getenv('PINECONE_DENSE_INDEX_NAME')
        if not final_dense_index_name:
            show_error_panel(
                "Configuration Error",
                "Pinecone dense index name not found. Please set PINECONE_DENSE_INDEX_NAME environment variable or use --dense-index-name option."
            )
            return
            
        final_sparse_index_name = sparse_index_name or os.getenv('PINECONE_SPARSE_INDEX_NAME')
        if not final_sparse_index_name:
            show_error_panel(
                "Configuration Error",
                "Pinecone sparse index name not found. Please set PINECONE_SPARSE_INDEX_NAME environment variable or use --sparse-index-name option."
            )
            return
        
        # Initialize connection manager
        connection_manager = ConnectionManager(config_manager)
        
        # Validate all connections
        show_status_panel("Validating", "Validating Google Drive and Pinecone connections...")
        
        try:
            # Validate Google Drive connection
            connection_manager.validate_google_drive_connection(final_credentials)
            show_success_panel("Google Drive", "✓ Google Drive connection validated")
            
            # Validate Pinecone hybrid connection
            connection_manager.validate_hybrid_connection(
                final_api_key, 
                final_dense_index_name, 
                final_sparse_index_name
            )
            show_success_panel("Pinecone", "✓ Pinecone hybrid connection validated")
            
        except IndexNotFoundError as e:
            # Indexes don't exist, offer to create them
            show_status_panel("Indexes Not Found", "One or more Pinecone indexes don't exist. Creating them...")
            
            try:
                search_service = factory.create_search_service(
                    final_api_key,
                    final_dense_index_name,
                    final_sparse_index_name
                )
                
                # Create indexes with integrated embedding
                search_service.create_indexes()
                show_success_panel("Indexes Created", "✓ Dense and sparse indexes created successfully")
                
            except Exception as create_error:
                show_error_panel("Index Creation Failed", f"Failed to create indexes: {create_error}")
                return
                
        except (AuthenticationError, IncompatibleIndexError) as e:
            show_error_panel("Validation Failed", str(e))
            return
        
        # Store configuration
        show_status_panel("Configuring", "Storing configuration...")
        
        try:
            config_manager.set_owner_config(
                final_credentials,
                final_api_key,
                final_dense_index_name,
                final_sparse_index_name
            )
            show_success_panel("Configuration", "✓ Configuration stored successfully")
            
        except Exception as e:
            show_error_panel("Configuration Error", f"Failed to store configuration: {e}")
            return
        
        # Additional validation if requested
        if validate:
            show_status_panel("Testing", "Performing additional connection tests...")
            
            try:
                # Test hybrid service
                search_service = factory.create_search_service(
                    final_api_key,
                    final_dense_index_name,
                    final_sparse_index_name
                )
                
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
                
                show_success_panel("Validation Complete", "All connections tested successfully")
                
                # Display validation details
                from ..ui.progress import show_info_table
                show_info_table("Index Information", validation_info)
                
            except Exception as e:
                show_error_panel("Validation Warning", f"Additional validation failed: {e}")
        
        show_success_panel(
            "Setup Complete", 
            "Owner mode configured successfully! You can now use the index and search commands."
        )
        
        # Show next steps
        show_success_panel(
            "Next Steps",
            "1. Run 'gdrive-pinecone-search owner index' to index your Google Drive files\n"
            "2. Run 'gdrive-pinecone-search search \"your query\"' to search your content"
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise
