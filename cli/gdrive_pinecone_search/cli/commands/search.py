"""Search command for hybrid search across indexed content."""

import click
from typing import List, Optional

from ...services.search_service import SearchService
from ...utils.config_manager import ConfigManager
from ...utils.exceptions import ConfigurationError
from ..ui.progress import (
    show_status_panel, show_success_panel, show_error_panel
)
from ..ui.results import SearchResultsDisplay


@click.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, 
              help='Number of results to return (default: 10, max: 100)')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types to search (docs,sheets,slides)')
@click.option('--interactive', '-i', is_flag=True, 
              help='Enable interactive result selection')
def search(query: str, limit: int, file_types: Optional[str], interactive: bool):
    """
    Search indexed Google Drive content using hybrid search with reranking.
    
    This command performs hybrid search (combining dense and sparse vectors) across all 
    indexed Google Drive documents, then reranks the results using Pinecone's hosted 
    reranking model for optimal relevance.
    
    Examples:
        gdrive-pinecone-search search "quarterly planning"
        gdrive-pinecone-search search "budget analysis" --file-types docs,sheets --limit 5
        gdrive-pinecone-search search "team meeting notes" --interactive
        gdrive-pinecone-search search "product marketing" --limit 50
    """
    try:
        # Validate limit
        if limit > 100:
            show_error_panel(
                "Invalid Limit",
                f"Limit cannot exceed 100. You requested {limit} results. This limit is enforced due to Pinecone's reranking API constraints."
            )
            return
        
        # Show search status immediately
        show_status_panel("Searching", f"Performing hybrid search for '{query}'...")
        
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Validate configuration
        try:
            config_manager.validate_config()
        except ConfigurationError as e:
            show_error_panel("Configuration Error", str(e))
            return
        
        # Parse file types filter
        file_types_filter = None
        if file_types:
            file_types_list = [ft.strip() for ft in file_types.split(',')]
            # Validate file types
            valid_types = {'docs', 'sheets', 'slides'}
            invalid_types = set(file_types_list) - valid_types
            if invalid_types:
                show_error_panel(
                    "Invalid File Types",
                    f"Invalid file types: {', '.join(invalid_types)}. Valid types are: {', '.join(valid_types)}"
                )
                return
            
            # Create filter for Pinecone
            file_types_filter = {'file_type': {'$in': file_types_list}}
        
        # Initialize hybrid service
        try:
            pinecone_api_key = config_manager.get_pinecone_api_key()
            dense_index_name = config_manager.get_dense_index_name()
            sparse_index_name = config_manager.get_sparse_index_name()
            settings = config_manager.config.settings
            reranking_model = settings.reranking_model
            
            search_service = SearchService(
                pinecone_api_key,
                dense_index_name,
                sparse_index_name,
                reranking_model
            )
            
            # Test connection
            stats = search_service.get_index_stats()
            total_vectors = stats.get('total_vectors', 0)
            
            if total_vectors == 0:
                show_error_panel(
                    "Empty Indexes",
                    "The Pinecone indexes are empty. Please run the index command first to populate them."
                )
                return
            
        except Exception as e:
            show_error_panel("Connection Error", f"Failed to connect to Pinecone: {e}")
            return
        
        # Perform hybrid search with integrated embedding and reranking
        try:
            results = search_service.hybrid_query(
                query_text=query,
                top_k=limit,  # Get exactly the number of results requested
                filter_dict=file_types_filter,
                include_metadata=True
            )
            
            if not results:
                show_error_panel(
                    "No Results",
                    f"No results found for your query. Try refining your search terms."
                )
                return
            
            # Use all results (already limited by top_k)
            final_results = results
            
        except Exception as e:
            show_error_panel("Search Error", f"Failed to perform search: {e}")
            return
        
        # Display results
        try:
            display = SearchResultsDisplay()
            display.show_results(
                query=query,
                results=final_results,
                interactive=interactive
            )
            
        except Exception as e:
            show_error_panel("Display Error", f"Failed to display results: {e}")
            return
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise


@click.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, 
              help='Number of results to return (default: 10, max: 100)')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types to search (docs,sheets,slides)')
def quick_search(query: str, limit: int, file_types: Optional[str]):
    """
    Quick search without interactive mode.
    
    This is a simplified version of the search command that displays results
    without interactive selection.
    """
    # Call the main search function with interactive=False
    search.callback(query, limit, file_types, False) 