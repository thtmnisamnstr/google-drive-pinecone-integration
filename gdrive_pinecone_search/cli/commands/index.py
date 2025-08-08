"""Index command for initial indexing of Google Drive files."""

import click
from typing import List, Optional
from datetime import datetime

from ...utils.config_manager import ConfigManager
from ...utils.connection_manager import ConnectionManager
from ...utils.exceptions import (
    AuthenticationError, 
    ConfigurationError,
    DocumentProcessingError
)
from ...services.auth_service import AuthService
from ...services.gdrive_service import GDriveService
from ...services.document_processor import DocumentProcessor
from ...services.pinecone_service import PineconeService
from ..ui.progress import (
    ProgressManager, show_status_panel, show_error_panel, show_success_panel,
    show_file_processing_progress
)
from ..ui.results import display_file_processing_summary


@click.command()
@click.option('--limit', '-l', type=int, 
              help='Limit the number of files to process')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types (docs,sheets,slides)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be indexed without making changes')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def index(limit: Optional[int], file_types: Optional[str], dry_run: bool, credentials: Optional[str]):
    """
    Index Google Drive files into Pinecone (Owner mode only).
    
    This command will:
    1. Authenticate with Google Drive
    2. List and process Google Drive files
    3. Extract text content and chunk it
    4. Generate embeddings and store in Pinecone
    
    Examples:
            gdrive-pinecone-search index
    gdrive-pinecone-search index --file-types docs,sheets --limit 100
    gdrive-pinecone-search index --dry-run
    """
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Check if we're in owner mode
        if not config_manager.is_owner_mode():
            show_error_panel(
                "Mode Error",
                "Index command requires owner mode. Please configure Google Drive credentials first."
            )
            return
        
        # Validate configuration
        try:
            config_manager.validate_config()
        except ConfigurationError as e:
            show_error_panel("Configuration Error", str(e))
            return
        
        # Get credentials path
        credentials_path = credentials or config_manager.get_google_credentials_path()
        if not credentials_path:
            show_error_panel(
                "Configuration Error",
                "Google Drive credentials not found. Please set GDRIVE_CREDENTIALS_JSON environment variable or use --credentials option."
            )
            return
        
        # Parse file types
        file_types_list = None
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
        
        # Initialize services
        show_status_panel("Initializing", "Setting up services...")
        
        # Authentication service
        auth_service = AuthService(credentials_path)
        
        # Google Drive service
        gdrive_service = GDriveService(auth_service)
        
        # Document processor
        settings = config_manager.config.settings
        doc_processor = DocumentProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Pinecone service
        pinecone_api_key = config_manager.get_pinecone_api_key()
        connection_config = config_manager.config.connection
        pinecone_service = PineconeService(
            pinecone_api_key,
            connection_config.index_name
        )
        
        # Test connections
        show_status_panel("Testing Connections", "Validating Google Drive and Pinecone access...")
        
        try:
            # Test Google Drive connection
            gdrive_service.validate_file_access("test")
            
            # Test Pinecone connection
            pinecone_service.get_index_stats()
            
        except Exception as e:
            show_error_panel("Connection Error", f"Failed to connect to services: {e}")
            return
        
        # Get user info
        try:
            user_info = gdrive_service.get_user_info()
            show_success_panel("Authentication", f"Connected as: {user_info.get('emailAddress', 'Unknown')}")
        except Exception as e:
            show_error_panel("Authentication Error", f"Failed to get user info: {e}")
            return
        
        # List files
        show_status_panel("Scanning", "Scanning Google Drive for files...")
        
        try:
            files = list(gdrive_service.list_files(file_types=file_types_list))
            
            if not files:
                show_error_panel("No Files Found", "No files found matching the specified criteria.")
                return
            
            # Apply limit if specified
            if limit:
                files = files[:limit]
            
            show_success_panel("Files Found", f"Found {len(files)} files to process")
            
        except Exception as e:
            show_error_panel("File Listing Error", f"Failed to list files: {e}")
            return
        
        if dry_run:
            # Show what would be processed
            show_status_panel("Dry Run", "Showing files that would be processed:")
            
            for i, file in enumerate(files, 1):
                file_type = file.get('file_type', 'unknown')
                modified_time = file.get('modifiedTime', 'Unknown')
                estimated_chunks = doc_processor.estimate_chunks("Sample text for estimation")
                
                click.echo(f"{i:3d}. {file['name']} ({file_type}) - {modified_time} (~{estimated_chunks} chunks)")
            
            show_success_panel("Dry Run Complete", f"Would process {len(files)} files")
            return
        
        # Process files
        show_status_panel("Processing", "Starting file processing...")
        
        processed_files = 0
        processed_chunks = 0
        errors = []
        
        with ProgressManager() as progress:
            # Create main progress task
            main_task = progress.add_task("Processing files", total=len(files))
            
            for i, file in enumerate(files):
                try:
                    # Update progress
                    progress.update(main_task, description=f"Processing: {file['name']}")
                    
                    # Get file content
                    content = gdrive_service.get_file_content(file['id'], file['mimeType'])
                    
                    if not content.strip():
                        continue  # Skip empty files
                    
                    # Process file into chunks
                    chunks = doc_processor.process_file(content, file)
                    
                    if not chunks:
                        continue  # Skip files that produce no chunks
                    
                    # Generate embeddings and prepare vectors
                    vectors = []
                    for chunk in chunks:
                        # For now, use a simple embedding (in production, use a proper embedding model)
                        # This is a placeholder - you would integrate with an embedding service here
                        embedding = [0.0] * 1024  # 1024-dimensional zero vector as placeholder
                        
                        vectors.append({
                            'id': chunk['id'],
                            'values': embedding,
                            'metadata': {
                                'file_id': chunk['file_id'],
                                'file_name': chunk['file_name'],
                                'file_type': chunk['file_type'],
                                'chunk_index': chunk['chunk_index'],
                                'content': chunk['content'],
                                'modified_time': chunk['modified_time'],
                                'web_view_link': chunk['web_view_link'],
                                'indexed_at': chunk['indexed_at'],
                                'chunk_token_count': chunk['chunk_token_count'],
                                'total_chunks': chunk['total_chunks']
                            }
                        })
                    
                    # Upsert vectors to Pinecone
                    if vectors:
                        pinecone_service.upsert_vectors(vectors)
                        processed_chunks += len(vectors)
                    
                    processed_files += 1
                    
                except Exception as e:
                    error_msg = f"Failed to process {file.get('name', 'Unknown file')}: {e}"
                    errors.append(error_msg)
                    continue
                
                # Update progress
                progress.update(main_task, advance=1)
        
        # Update configuration
        config_manager.update_last_refresh_time(datetime.now())
        config_manager.update_files_indexed_count(processed_files)
        
        # Update index metadata
        try:
            metadata = {
                'last_refresh_time': datetime.now().isoformat(),
                'total_files_indexed': processed_files,
                'total_chunks_indexed': processed_chunks,
                'embedding_model': settings.embedding_model,
                'chunk_size': settings.chunk_size,
                'chunk_overlap': settings.chunk_overlap,
                'indexed_by': user_info.get('emailAddress', 'Unknown')
            }
            pinecone_service.update_index_metadata(metadata)
        except Exception as e:
            errors.append(f"Failed to update index metadata: {e}")
        
        # Show results
        show_success_panel("Indexing Complete", f"Successfully processed {processed_files} files")
        
        # Display summary
        display_file_processing_summary(processed_files, len(files), processed_chunks, errors)
        
        show_success_panel(
            "Next Steps",
            "Indexing complete! You can now use the search command to find content in your indexed files."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 