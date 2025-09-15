"""Index command for initial indexing of Google Drive files."""

import click
from typing import List, Optional
from datetime import datetime, timezone

from ...utils.service_factory import get_service_factory
from ...utils.exceptions import ConfigurationError, AuthenticationError
from ...utils.file_types import validate_file_types, get_all_valid_file_types
from ..ui.progress import (
    ProgressManager, show_status_panel, show_success_panel, show_error_panel
)
from ..ui.results import display_file_processing_summary


@click.command()
@click.option('--limit', '-l', type=int, 
              help='Limit the number of files to process')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types (docs,sheets,slides,py,json,md,etc) or categories (code,config,txt,web,data)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be indexed without making changes')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def index(limit: Optional[int], file_types: Optional[str], dry_run: bool, credentials: Optional[str]):
    """
    Index Google Drive files into Pinecone using hybrid search (Owner mode only).
    
    This command will:
    1. Authenticate with Google Drive
    2. List and process Google Drive files
    3. Extract text content and chunk it
    4. Generate dense and sparse embeddings
    5. Store vectors in both dense and sparse Pinecone indexes
    
    Examples:
            gdrive-pinecone-search owner index
    gdrive-pinecone-search owner index --file-types docs,sheets --limit 100
    gdrive-pinecone-search owner index --dry-run
    """
    try:
        # Get service factory and initialize configuration
        factory = get_service_factory()
        config_manager = factory.create_config_manager()
        
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
        
        # Parse and validate file types
        file_types_list = None
        if file_types:
            try:
                file_types_list = validate_file_types(file_types)
            except ValueError as e:
                show_error_panel("Invalid File Types", str(e))
                return
        
        # Initialize services
        show_status_panel("Initializing", "Setting up services...")
        
        # Authentication service
        auth_service = factory.create_auth_service(credentials_path)
        
        # Google Drive service
        gdrive_service = factory.create_gdrive_service(auth_service)
        
        # Document processor
        settings = config_manager.config.settings
        document_processor = factory.create_document_processor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        # Initialize hybrid service
        show_status_panel("Connecting", "Connecting to Pinecone indexes...")
        
        try:
            pinecone_api_key = config_manager.get_pinecone_api_key()
            dense_index_name = config_manager.get_dense_index_name()
            sparse_index_name = config_manager.get_sparse_index_name()
            reranking_model = settings.reranking_model
            
            search_service = factory.create_search_service(
                pinecone_api_key,
                dense_index_name,
                sparse_index_name,
                reranking_model
            )
            
            # Test connection
            stats = search_service.get_index_stats()
            show_success_panel("Connected", "Connected to Pinecone indexes successfully")
            
        except Exception as e:
            show_error_panel("Connection Error", f"Failed to connect to Pinecone: {e}")
            return
        
        # Test connections
        show_status_panel("Testing Connections", "Validating Google Drive and Pinecone access...")
        
        try:
            # Test Google Drive connection
            gdrive_service.validate_file_access("test")
            
            # Test Pinecone connection
            search_service.get_index_stats()
            
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
            # Show progress during scanning
            print("  Scanning Google Drive files...")
            files = []
            file_count = 0
            for file in gdrive_service.list_files(file_types=file_types_list):
                files.append(file)
                file_count += 1
                if file_count % 50 == 0:  # Show progress every 50 files
                    print(f"  Found {file_count} files so far...")
            
            print(f"  Scanning complete. Found {len(files)} total files.")
            
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
            show_success_panel("Dry Run", f"Would process {len(files)} files")
            for file in files:
                print(f"  - {file['name']} ({file['mimeType']})")
            return
        
        # Process files
        show_status_panel("Processing", "Starting file processing...")
        
        processed_files = 0
        processed_chunks = 0
        skipped_files = 0
        errors = []
        
        with ProgressManager() as progress:
            # Create main progress task
            main_task = progress.add_task("Processing files", total=len(files))
            
            for i, file in enumerate(files):
                try:
                    # Update progress
                    progress.update(main_task, description=f"Processing: {file['name']}")
                    
                    # Process file content
                    # Extract text content with validation
                    text_content = gdrive_service.get_file_content_with_validation(file['id'], file['mimeType'], file['name'])
                    
                    if text_content is None:
                        # File is not accessible, skip it
                        skipped_files += 1
                        errors.append(f"Skipped {file.get('name', 'Unknown file')}: File is not accessible (permission denied)")
                        continue
                    
                    if not text_content.strip():
                        skipped_files += 1
                        errors.append(f"Skipped {file.get('name', 'Unknown file')}: File has no content")
                        continue
                    
                    # Chunk the text
                    chunks = document_processor.process_file(text_content, file)
                    
                    if not chunks:
                        skipped_files += 1
                        errors.append(f"Skipped {file.get('name', 'Unknown file')}: No chunks generated")
                        continue
                    
                    # Prepare vectors for upserting (using integrated embedding)
                    vectors = []
                    for chunk in chunks:
                        metadata = {
                            'file_id': chunk['file_id'],
                            'file_name': chunk['file_name'],
                            'file_type': chunk['file_type'],
                            'chunk_index': chunk['chunk_index'],
                            'modified_time': chunk['modified_time'],
                            'web_view_link': chunk['web_view_link']
                        }
                        
                        # Check metadata size (Pinecone limit is 40,960 bytes)
                        import json
                        metadata_size = len(json.dumps(metadata).encode('utf-8'))
                        if metadata_size > 40000:  # Leave some buffer
                            # Truncate file_name if it's too long
                            if len(metadata['file_name']) > 100:
                                metadata['file_name'] = metadata['file_name'][:97] + "..."
                            
                            # Re-check size after truncation
                            metadata_size = len(json.dumps(metadata).encode('utf-8'))
                            if metadata_size > 40000:
                                # Skip this chunk if still too large
                                errors.append(f"Skipped chunk {chunk['chunk_index']} from {file.get('name', 'Unknown file')}: Metadata too large ({metadata_size} bytes)")
                                continue
                        
                        vectors.append({
                            'id': chunk['id'],  # Will be converted to _id in search_service
                            'chunk_text': chunk['content'],
                            'metadata': metadata
                        })
                    
                    # Upsert vectors to both indexes (integrated embedding handles vector generation)
                    if vectors:
                        search_service.upsert_hybrid_vectors(vectors)
                        processed_chunks += len(vectors)
                    
                    processed_files += 1
                    
                except Exception as e:
                    error_str = str(e).lower()
                    if any(keyword in error_str for keyword in ['cannotexportfile', 'forbidden', '403', 'permission']):
                        error_msg = f"Skipped {file.get('name', 'Unknown file')}: File is not accessible (permission denied)"
                        skipped_files += 1
                    elif 'metadata size' in error_str or '40960 bytes' in error_str:
                        error_msg = f"Failed to process {file.get('name', 'Unknown file')}: Metadata too large for Pinecone (limit: 40,960 bytes)"
                        skipped_files += 1
                    else:
                        error_msg = f"Failed to process {file.get('name', 'Unknown file')}: {e}"
                        skipped_files += 1
                    errors.append(error_msg)
                    continue
        
        # Update configuration
        config_manager.update_last_refresh_time(datetime.now(timezone.utc))
        config_manager.update_files_indexed_count(processed_files)
        
        # Update index metadata
        metadata = {
            'reranking_model': settings.reranking_model,
            'chunk_size': settings.chunk_size,
            'chunk_overlap': settings.chunk_overlap,
            'last_refresh_time': datetime.now(timezone.utc).isoformat(),
            'total_files_indexed': processed_files,
            'total_chunks_indexed': processed_chunks,
            'indexed_by': user_info.get('emailAddress', 'Unknown')
        }
        try:
            search_service.update_index_metadata(metadata)
        except Exception as e:
            errors.append(f"Failed to update index metadata: {e}")
        
        # Show results
        show_success_panel("Indexing Complete", f"Successfully processed {processed_files} files")
        
        # Display summary
        display_file_processing_summary(processed_files, len(files), processed_chunks, errors, skipped_files)
        
        show_success_panel(
            "Next Steps",
            "Indexing complete! You can now use the search command to find content in your indexed files using hybrid search."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 