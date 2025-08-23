"""Refresh command for incremental updates to the index."""

import click
from typing import List, Optional
from datetime import datetime, timezone

from ...services.search_service import SearchService
from ...services.gdrive_service import GDriveService
from ...services.document_processor import DocumentProcessor
from ...utils.config_manager import ConfigManager
from ...utils.connection_manager import ConnectionManager
from ...utils.exceptions import ConfigurationError, AuthenticationError
from ..ui.progress import (
    ProgressManager, show_status_panel, show_success_panel, show_error_panel
)
from ..ui.results import display_file_processing_summary


@click.command()
@click.option('--limit', '-l', type=int, 
              help='Limit the number of files to process')
@click.option('--file-types', '-t', 
              help='Comma-separated list of file types (docs,sheets,slides)')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be indexed without making changes')
@click.option('--since', '-s', 
              help='Process files modified since this date (YYYY-MM-DD)')
@click.option('--force-full', '-f', is_flag=True, 
              help='Force full refresh of all files')
@click.option('--credentials', '-c', 
              help='Path to Google Drive credentials JSON file')
def refresh(limit: Optional[int], file_types: Optional[str], dry_run: bool, since: Optional[str], force_full: bool, credentials: Optional[str]):
    """
    Refresh index with updated Google Drive files using hybrid search (Owner mode only).
    
    This command performs intelligent incremental updates to the index by processing:
    - New files that don't exist in the index
    - Modified files that have changed since the last refresh
    - Files modified since a specified date (if --since is used)
    - All files (if --force-full is used)
    
    The command automatically tracks the last refresh time and uses it for
    future incremental updates, making regular refreshes much faster.
    
    Examples:
        gdrive-pinecone-search owner refresh                    # Incremental refresh using last refresh time
        gdrive-pinecone-search owner refresh --since 2024-01-15 # Process files modified since date
        gdrive-pinecone-search owner refresh --force-full       # Process all files
        gdrive-pinecone-search owner refresh --file-types docs,sheets --limit 50 # Process specific types with limit
        gdrive-pinecone-search owner refresh --dry-run          # Show what would be processed
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
                # Parse the date and make it timezone-aware (UTC)
                modified_since = datetime.strptime(since, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                show_error_panel(
                    "Invalid Date",
                    "Invalid date format. Please use YYYY-MM-DD format."
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
        from ...services.auth_service import AuthService
        auth_service = AuthService(credentials_path)
        
        # Google Drive service
        gdrive_service = GDriveService(auth_service)
        
        # Document processor
        settings = config_manager.config.settings
        doc_processor = DocumentProcessor(
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
            
            search_service = SearchService(
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
        
        # Get existing file IDs from index and last refresh time
        existing_file_ids = set()
        last_refresh_time = None
        
        if not force_full:
            try:
                show_status_panel("Analyzing", "Analyzing existing index...")
                
                # Get existing file IDs
                existing_file_ids = set(search_service.list_file_ids())
                
                # Get last refresh time from index metadata
                index_metadata = search_service.get_index_metadata()
                if index_metadata and 'last_refresh_time' in index_metadata:
                    try:
                        # Parse the timestamp and make it timezone-aware (UTC)
                        last_refresh_time = datetime.fromisoformat(index_metadata['last_refresh_time'])
                        if last_refresh_time.tzinfo is None:
                            last_refresh_time = last_refresh_time.replace(tzinfo=timezone.utc)
                        show_success_panel("Analysis", f"Found {len(existing_file_ids)} existing files, last refresh: {last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    except (ValueError, TypeError):
                        # If we can't parse the timestamp, ignore it
                        last_refresh_time = None
                        show_success_panel("Analysis", f"Found {len(existing_file_ids)} existing files, no valid last refresh time")
                else:
                    show_success_panel("Analysis", f"Found {len(existing_file_ids)} existing files, no previous refresh recorded")
                    
            except Exception as e:
                show_error_panel("Analysis Error", f"Failed to analyze existing index: {e}")
                return
        
        # List files to process
        show_status_panel("Scanning", "Scanning Google Drive for files...")
        
        try:
            all_files = list(gdrive_service.list_files())
            
            if not all_files:
                show_error_panel("No Files Found", "No files found in Google Drive.")
                return
            
            # Filter files based on refresh criteria
            files_to_process = []
            new_files = []
            modified_files = []
            
            for file in all_files:
                file_id = file['id']
                modified_time = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))
                
                # Check if file should be processed
                should_process = False
                process_reason = ""
                
                if force_full:
                    should_process = True
                    process_reason = "force-full"
                elif modified_since and modified_time >= modified_since:
                    should_process = True
                    process_reason = f"modified since {modified_since.strftime('%Y-%m-%d')}"
                elif last_refresh_time and modified_time >= last_refresh_time:
                    should_process = True
                    process_reason = f"modified since last refresh ({last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')})"
                elif file_id not in existing_file_ids:
                    should_process = True
                    process_reason = "new file"
                    new_files.append(file)
                
                if should_process:
                    # Apply file type filtering
                    if file_types_list:
                        file_type = file.get('mimeType', '')
                        if file_type == 'application/vnd.google-apps.document' and 'docs' not in file_types_list:
                            should_process = False
                        elif file_type == 'application/vnd.google-apps.spreadsheet' and 'sheets' not in file_types_list:
                            should_process = False
                        elif file_type == 'application/vnd.google-apps.presentation' and 'slides' not in file_types_list:
                            should_process = False
                    
                    if should_process:
                        files_to_process.append(file)
                        if process_reason != "new file" and file_id in existing_file_ids:
                            modified_files.append(file)
            
            # Apply limit if specified
            if limit and len(files_to_process) > limit:
                files_to_process = files_to_process[:limit]
                show_success_panel("Limit Applied", f"Limited to {limit} files (from {len(all_files)} total files)")
            
            if not files_to_process:
                if last_refresh_time:
                    show_success_panel("No Updates", f"No files have been modified since the last refresh ({last_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}).")
                else:
                    show_success_panel("No Updates", "No files need to be processed.")
                return
            
            # Create detailed summary message
            summary_parts = [f"Found {len(files_to_process)} files to update"]
            if new_files:
                summary_parts.append(f"{len(new_files)} new files")
            if modified_files:
                summary_parts.append(f"{len(modified_files)} modified files")
            
            summary_message = ", ".join(summary_parts)
            show_success_panel("Analysis Complete", summary_message)
            
        except Exception as e:
            show_error_panel("File Listing Error", f"Failed to list files: {e}")
            return
        
        # Check for dry run
        if dry_run:
            show_success_panel("Dry Run Complete", f"Would process {len(files_to_process)} files")
            
            # Display what would be processed
            display_file_processing_summary(len(files_to_process), len(all_files), 0, [], 0)
            
            show_success_panel(
                "Next Steps",
                "Dry run complete! Run without --dry-run to actually process the files."
            )
            return
        
        # Process files
        show_status_panel("Processing", "Starting file processing...")
        
        processed_files = 0
        processed_chunks = 0
        skipped_files = 0
        errors = []
        
        with ProgressManager() as progress:
            # Create main progress task
            main_task = progress.add_task("Processing files", total=len(files_to_process))
            
            for i, file in enumerate(files_to_process):
                try:
                    # Update progress
                    progress.update(main_task, description=f"Processing: {file['name']}")
                    
                    # Delete existing chunks for this file (if any)
                    if file['id'] in existing_file_ids:
                        search_service.delete_by_metadata({'file_id': file['id']})
                    
                    # Process file content
                    # Extract text content with validation
                    text_content = gdrive_service.get_file_content_with_validation(file['id'], file['mimeType'])
                    
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
                    chunks = doc_processor.process_file(text_content, file)
                    
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
                
                # Update progress
                progress.update(main_task, advance=1)
        
        # Clean up deleted files
        if not force_full:
            show_status_panel("Cleanup", "Checking for deleted files...")
            
            try:
                # Get current file IDs from Google Drive
                current_file_ids = [f['id'] for f in gdrive_service.list_files()]
                
                # Clean up deleted files
                cleaned_count = search_service.cleanup_deleted_files(current_file_ids)
                
                if cleaned_count > 0:
                    show_success_panel("Cleanup Complete", f"Removed {cleaned_count} deleted files from index")
                else:
                    show_success_panel("Cleanup Complete", "No deleted files found")
                
            except Exception as e:
                errors.append(f"Failed to cleanup deleted files: {e}")
        
        # Update configuration
        config_manager.update_last_refresh_time(datetime.now(timezone.utc))
        
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
        search_service.update_index_metadata(metadata)
        
        # Show results
        show_success_panel("Refresh Complete", f"Successfully processed {processed_files} files")
        
        # Display summary
        display_file_processing_summary(processed_files, len(files_to_process), processed_chunks, errors, skipped_files)
        
        show_success_panel(
            "Next Steps",
            "Refresh complete! Your hybrid search index has been updated."
        )
        
    except Exception as e:
        show_error_panel("Unexpected Error", f"An unexpected error occurred: {e}")
        raise 