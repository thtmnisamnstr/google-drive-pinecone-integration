"""Search command for semantic search across indexed content."""

import click
from typing import List, Optional

from ...utils.config_manager import ConfigManager
from ...utils.exceptions import ConfigurationError, DocumentProcessingError
from ...services.pinecone_service import PineconeService
from ..ui.progress import show_status_panel, show_error_panel, show_success_panel
from ..ui.results import SearchResultsDisplay


@click.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, 
              help='Number of results to return (default: 10)')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types to search (docs,sheets,slides)')
@click.option('--min-score', '-s', type=float, default=0.7, 
              help='Minimum similarity score (0.0-1.0, default: 0.7)')
@click.option('--interactive', '-i', is_flag=True, 
              help='Enable interactive result selection')
def search(query: str, limit: int, file_types: Optional[str], min_score: float, interactive: bool):
    """
    Search indexed Google Drive content.
    
    This command performs semantic search across all indexed Google Drive documents,
    returning the most relevant results based on your query.
    
    Examples:
            gdrive-pinecone-search search "quarterly planning"
    gdrive-pinecone-search search "budget analysis" --file-types docs,sheets --limit 5
    gdrive-pinecone-search search "team meeting notes" --interactive
    """
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Validate configuration
        try:
            config_manager.validate_config()
        except ConfigurationError as e:
            show_error_panel("Configuration Error", str(e))
            return
        
        # Check if we have Pinecone configuration
        if not config_manager.has_pinecone_config():
            show_error_panel(
                "Configuration Error",
                "Pinecone configuration not found. Please use the connect command first."
            )
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
        
        # Initialize Pinecone service
        show_status_panel("Connecting", "Connecting to Pinecone index...")
        
        try:
            pinecone_api_key = config_manager.get_pinecone_api_key()
            connection_config = config_manager.config.connection
            pinecone_service = PineconeService(
                pinecone_api_key,
                connection_config.index_name
            )
            
            # Test connection
            stats = pinecone_service.get_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            if total_vectors == 0:
                show_error_panel(
                    "Empty Index",
                    "The Pinecone index is empty. Please run the index command first to populate it."
                )
                return
            
            show_success_panel("Connected", f"Connected to index with {total_vectors} vectors")
            
        except Exception as e:
            show_error_panel("Connection Error", f"Failed to connect to Pinecone: {e}")
            return
        
        # Generate query embedding
        show_status_panel("Processing", "Generating search query embedding...")
        
        try:
            # For now, use a simple embedding (in production, use a proper embedding model)
            # This is a placeholder - you would integrate with an embedding service here
            query_embedding = [0.0] * 1024  # 1024-dimensional zero vector as placeholder
            
            # In a real implementation, you would do something like:
            # query_embedding = embedding_service.embed_text(query)
            
        except Exception as e:
            show_error_panel("Embedding Error", f"Failed to generate query embedding: {e}")
            return
        
        # Perform search
        show_status_panel("Searching", f"Searching for: '{query}'...")
        
        try:
            results = pinecone_service.query_vectors(
                query_vector=query_embedding,
                top_k=limit * 2,  # Get more results to filter by score
                filter_dict=file_types_filter,
                include_metadata=True
            )
            
            # Filter results by minimum score
            filtered_results = [r for r in results if r.get('score', 0) >= min_score]
            
            # Limit results
            filtered_results = filtered_results[:limit]
            
            show_success_panel("Search Complete", f"Found {len(filtered_results)} results")
            
        except Exception as e:
            show_error_panel("Search Error", f"Failed to perform search: {e}")
            return
        
        # Display results
        if not filtered_results:
            show_error_panel(
                "No Results",
                f"No results found for '{query}' with minimum score {min_score}"
            )
            return
        
        # Create results display
        results_display = SearchResultsDisplay(filtered_results, query)
        
        if interactive:
            # Interactive mode
            results_display.display_results()
            results_display.interactive_selection()
        else:
            # Simple display mode
            results_display.display_results()
        
        show_success_panel(
            "Search Complete",
            f"Search completed successfully. Found {len(filtered_results)} relevant results."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise


@click.command()
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, 
              help='Number of results to return (default: 10)')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types to search (docs,sheets,slides)')
@click.option('--min-score', '-s', type=float, default=0.7, 
              help='Minimum similarity score (0.0-1.0, default: 0.7)')
def quick_search(query: str, limit: int, file_types: Optional[str], min_score: float):
    """
    Quick search without interactive mode.
    
    This is a simplified version of the search command that displays results
    without interactive selection.
    """
    # Call the main search function with interactive=False
    search.callback(query, limit, file_types, min_score, False) 