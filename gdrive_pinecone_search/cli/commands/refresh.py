"""Refresh command for incremental updates to the index."""

import click
from typing import Optional
from datetime import datetime, timedelta

from ...utils.config_manager import ConfigManager
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
    ProgressManager, show_status_panel, show_error_panel, show_success_panel
)
from ..ui.results import display_file_processing_summary


@click.command()
@click.option('--since', '-s', 
              help='Process files modified since this date (YYYY-MM-DD)')
@click.option('--force-full', '-f', is_flag=True, 
              help='Force full refresh of all files')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def refresh(since: Optional[str], force_full: bool, credentials: Optional[str]):
    """
    Refresh index with updated Google Drive files (Owner mode only).
    
    This command performs incremental updates to the index by processing only
    files that have been modified since the last refresh or a specified date.
    
    Examples:
            gdrive-pinecone-search refresh
    gdrive-pinecone-search refresh --since 2024-01-15
    gdrive-pinecone-search refresh --force-full
    """
    try:
        # Initialize configuration
        config_manager = ConfigManager()
        
        # Check if we're in owner mode
        if not config_manager.is_owner_mode():
            show_error_panel(
                "Mode Error",
                "Refresh command requires owner mode. Please configure Google Drive credentials first."
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
        
        # Parse since date
        modified_since = None
        if since:
            try:
                modified_since = datetime.strptime(since, '%Y-%m-%d')
            except ValueError:
                show_error_panel(
                    "Invalid Date",
                    "Invalid date format. Please use YYYY-MM-DD format."
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
        
        # Determine what files to process
        if force_full:
            show_status_panel("Full Refresh", "Performing full refresh of all files...")
            modified_since = None
        elif modified_since:
            show_status_panel("Incremental Refresh", f"Processing files modified since {since}...")
        else:
            # Use last refresh time from config
            last_refresh = config_manager.config.owner_config.last_refresh_time
            if last_refresh:
                modified_since = last_refresh
                show_status_panel("Incremental Refresh", f"Processing files modified since last refresh ({last_refresh.strftime('%Y-%m-%d %H:%M:%S')})...")
            else:
                show_status_panel("Initial Refresh", "No previous refresh found. Processing all files...")
        
        # List files to process
        try:
            files = list(gdrive_service.list_files(modified_since=modified_since))
            
            if not files:
                show_success_panel("No Updates", "No files have been modified since the last refresh.")
                return
            
            show_success_panel("Files Found", f"Found {len(files)} files to process")
            
        except Exception as e:
            show_error_panel("File Listing Error", f"Failed to list files: {e}")
            return
        
        # Get list of existing file IDs in the index
        show_status_panel("Analyzing", "Analyzing existing index...")
        
        try:
            existing_file_ids = set(pinecone_service.list_file_ids())
            files_to_process = [f for f in files if f['id'] in existing_file_ids]
            new_files = [f for f in files if f['id'] not in existing_file_ids]
            
            show_success_panel("Analysis Complete", f"Found {len(files_to_process)} files to update, {len(new_files)} new files")
            
        except Exception as e:
            show_error_panel("Analysis Error", f"Failed to analyze existing index: {e}")
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
                    
                    # Delete existing chunks for this file (if any)
                    if file['id'] in existing_file_ids:
                        pinecone_service.delete_by_metadata({'file_id': file['id']})
                    
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
        
        # Clean up deleted files
        if not force_full and not modified_since:
            show_status_panel("Cleanup", "Checking for deleted files...")
            
            try:
                # Get current file IDs from Google Drive
                current_file_ids = [f['id'] for f in gdrive_service.list_files()]
                
                # Clean up deleted files
                cleaned_count = pinecone_service.cleanup_deleted_files(current_file_ids)
                
                if cleaned_count > 0:
                    show_success_panel("Cleanup Complete", f"Removed {cleaned_count} deleted files from index")
                
            except Exception as e:
                errors.append(f"Failed to cleanup deleted files: {e}")
        
        # Update configuration
        config_manager.update_last_refresh_time(datetime.now())
        
        # Update index metadata
        try:
            metadata = {
                'last_refresh_time': datetime.now().isoformat(),
                'total_files_indexed': processed_files,
                'total_chunks_indexed': processed_chunks,
                'embedding_model': settings.embedding_model,
                'chunk_size': settings.chunk_size,
                'chunk_overlap': settings.chunk_overlap,
                'indexed_by': user_info.get('emailAddress', 'Unknown'),
                'refresh_type': 'full' if force_full else 'incremental'
            }
            pinecone_service.update_index_metadata(metadata)
        except Exception as e:
            errors.append(f"Failed to update index metadata: {e}")
        
        # Show results
        show_success_panel("Refresh Complete", f"Successfully processed {processed_files} files")
        
        # Display summary
        display_file_processing_summary(processed_files, len(files), processed_chunks, errors)
        
        show_success_panel(
            "Next Steps",
            "Refresh complete! Your index is now up to date with the latest changes."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 