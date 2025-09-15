"""Google Drive service for file operations and content extraction."""

import io
import csv
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
from urllib.parse import urlparse

import chardet
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

from ..utils.rate_limiter import rate_limited, GOOGLE_DRIVE_RATE_LIMITER
from ..utils.exceptions import DocumentProcessingError, APIRateLimitError
from .auth_service import AuthService
from ..utils.file_types import (
    GOOGLE_WORKSPACE_TYPES, PLAINTEXT_EXTENSIONS, 
    get_file_type_from_extension, is_supported_file_type
)


class GDriveService:
    """Service for Google Drive operations."""
    
    # Merge Google Workspace and plaintext types
    SUPPORTED_MIME_TYPES = {
        **GOOGLE_WORKSPACE_TYPES,
        # Add common plaintext MIME types that Google Drive might report
        'text/plain': 'txt',
        'text/markdown': 'md',
        'application/json': 'json',
        'text/html': 'html',
        'text/css': 'css',
        'text/javascript': 'js',
        'text/x-python': 'py'
    }
    
    # Export formats - Google Workspace files only
    EXPORT_FORMATS = {
        'application/vnd.google-apps.document': 'text/plain',
        'application/vnd.google-apps.spreadsheet': 'text/csv',
        'application/vnd.google-apps.presentation': 'text/plain'
    }
    
    def __init__(self, auth_service: AuthService):
        """
        Initialize Google Drive service.
        
        Args:
            auth_service: Authenticated auth service instance
        """
        self.auth_service = auth_service
        self.service = auth_service.get_service()
    
    def _is_file_accessible(self, file_id: str, mime_type: str, filename: str = "") -> bool:
        """
        Check if a file is accessible for export/download.
        
        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file
            filename: Name of the file (for plaintext file detection)
            
        Returns:
            True if file is accessible, False otherwise
        """
        try:
            # Check if file type is supported
            if mime_type not in GOOGLE_WORKSPACE_TYPES and not self._is_plaintext_file(filename, mime_type):
                return False
            
            # Use a faster validation approach - just check file permissions
            # This is much faster than trying to export
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,capabilities"
            ).execute()
            
            capabilities = file_info.get('capabilities', {})
            
            # Check if we can export/download the file
            if not capabilities.get('canDownload', False):
                return False
            
            return True
            
        except Exception as e:
            # Check for specific permission errors
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['forbidden', '403', 'permission', 'notfound']):
                return False
            # For other errors (like network issues), we'll assume it's accessible
            # and let the actual processing handle it
            return True
    
    def _detect_file_type(self, filename: str, mime_type: str) -> Optional[str]:
        """
        Detect file type from filename and MIME type.
        
        Args:
            filename: Name of the file
            mime_type: MIME type reported by Google Drive
            
        Returns:
            File type string or None if unsupported
        """
        # First check if it's a Google Workspace file
        if mime_type in GOOGLE_WORKSPACE_TYPES:
            return GOOGLE_WORKSPACE_TYPES[mime_type]
        
        # For plaintext files, prefer extension-based detection over generic MIME types
        ext_type = get_file_type_from_extension(filename)
        if ext_type:
            return ext_type
        
        # Fallback to MIME type for plaintext files
        if mime_type in self.SUPPORTED_MIME_TYPES:
            return self.SUPPORTED_MIME_TYPES[mime_type]
        
        return None
    
    def _is_plaintext_file(self, filename: str, mime_type: str) -> bool:
        """Check if file is a plaintext file (not Google Workspace)."""
        return (mime_type not in GOOGLE_WORKSPACE_TYPES and 
                is_supported_file_type(filename, mime_type))
    
    @rate_limited(100, 100)
    def get_plaintext_file_content(self, file_id: str, filename: str) -> str:
        """
        Get content of a plaintext file.
        
        Args:
            file_id: Google Drive file ID
            filename: Name of the file
            
        Returns:
            File content as string
            
        Raises:
            DocumentProcessingError: If content extraction fails
        """
        try:
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = request.execute()
            file_content.write(downloader)
            file_content.seek(0)
            
            # Detect encoding
            raw_content = file_content.read()
            detected_encoding = chardet.detect(raw_content)
            encoding = detected_encoding.get('encoding', 'utf-8')
            
            # Decode content
            try:
                content = raw_content.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to utf-8 with error handling
                content = raw_content.decode('utf-8', errors='replace')
            
            return content
            
        except Exception as e:
            if "quota" in str(e).lower():
                raise APIRateLimitError(f"Google Drive API quota exceeded: {e}")
            else:
                raise DocumentProcessingError(f"Failed to get plaintext file content: {e}")
    
    def get_file_content_with_validation(self, file_id: str, mime_type: str, filename: str = "") -> Optional[str]:
        """
        Get file content with built-in accessibility validation.
        Returns None if file is not accessible.
        
        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file
            filename: Name of the file (required for plaintext files)
            
        Returns:
            File content or None if not accessible
        """
        try:
            return self.get_file_content(file_id, mime_type, filename)
        except Exception as e:
            # Check for specific permission errors
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['cannotexportfile', 'forbidden', '403', 'permission']):
                return None
            # Re-raise other errors
            raise
    
    @rate_limited(1000, 100)  # 1000 requests per 100 seconds (increased rate limit)
    def list_files(self, 
                   file_types: Optional[List[str]] = None,
                   modified_since: Optional[datetime] = None,
                   page_size: int = 1000,  # Increased page size
                   validate_access: bool = False) -> Generator[Dict[str, Any], None, None]:
        """
        List Google Drive files with optional filtering.
        
        Args:
            file_types: List of file types to include (docs, sheets, slides, py, json, md, etc.)
            modified_since: Only include files modified since this time
            page_size: Number of files per page
            validate_access: Whether to validate file accessibility during listing
            
        Yields:
            File metadata dictionaries with enhanced file_type detection
        """
        try:
            # Build query
            query_parts = []
            
            # For plaintext files, we need to get all files and filter by extension
            # since Google Drive may not report accurate MIME types for plaintext files
            if file_types:
                # If specific file types requested, include known MIME types
                known_mime_types = [
                    mime_type for mime_type, file_type in self.SUPPORTED_MIME_TYPES.items()
                    if file_type in file_types
                ]
                
                # For plaintext files, also include generic types that might contain them
                has_plaintext_types = any(ft not in ['docs', 'sheets', 'slides'] for ft in file_types)
                if has_plaintext_types:
                    # Add common generic MIME types that plaintext files might have
                    generic_types = [
                        "text/plain", "application/octet-stream", "text/x-python", 
                        "application/json", "text/markdown", "text/html", "text/css",
                        "text/javascript", "application/x-sh"
                    ]
                    known_mime_types.extend(generic_types)
                
                if known_mime_types:
                    # Remove duplicates
                    known_mime_types = list(set(known_mime_types))
                    mime_query = " or ".join([f"mimeType='{mime_type}'" for mime_type in known_mime_types])
                    query_parts.append(f"({mime_query})")
            # If no file types specified, don't filter by MIME type to get all files
            
            # Filter by modification time
            if modified_since:
                # Format datetime for Google Drive API
                modified_str = modified_since.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                query_parts.append(f"modifiedTime > '{modified_str}'")
            
            # Combine query parts
            query = " and ".join(query_parts) if query_parts else None
            
            # List files
            page_token = None
            while True:
                try:
                    results = self.service.files().list(
                        q=query,
                        pageSize=page_size,
                        fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, size)",
                        pageToken=page_token
                    ).execute()
                    
                    files = results.get('files', [])
                    for file in files:
                        # Enhanced file type detection
                        file_type = self._detect_file_type(file['name'], file['mimeType'])
                        file['file_type'] = file_type
                        
                        if file_type:
                            # Validate accessibility if requested
                            if validate_access and not self._is_file_accessible(file['id'], file['mimeType'], file['name']):
                                # Skip inaccessible files
                                continue
                            yield file
                    
                    page_token = results.get('nextPageToken', None)
                    if not page_token:
                        break
                        
                except Exception as e:
                    if "quota" in str(e).lower():
                        raise APIRateLimitError(f"Google Drive API quota exceeded: {e}")
                    else:
                        raise DocumentProcessingError(f"Failed to list files: {e}")
                        
        except Exception as e:
            raise DocumentProcessingError(f"Error listing files: {e}")
    
    @rate_limited(100, 100)
    def get_file_content(self, file_id: str, mime_type: str, filename: str = "") -> str:
        """
        Get the text content of a Google Drive file.
        
        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file
            filename: Name of the file (required for plaintext files)
            
        Returns:
            Extracted text content
        """
        try:
            # Handle Google Workspace files (existing logic)
            if mime_type in GOOGLE_WORKSPACE_TYPES:
                if mime_type not in self.EXPORT_FORMATS:
                    raise DocumentProcessingError(f"Unsupported Google Workspace file type: {mime_type}")
                
                export_format = self.EXPORT_FORMATS[mime_type]
                file_type = GOOGLE_WORKSPACE_TYPES[mime_type]
                
                # Export file content
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType=export_format
                )
                
                file_content = io.BytesIO()
                downloader = request.execute()
                file_content.write(downloader)
                file_content.seek(0)
                
                # Process content based on file type
                if file_type == 'sheets':
                    return self._process_sheets_content(file_content)
                else:
                    return file_content.read().decode('utf-8')
            
            # Handle plaintext files (new logic)
            elif self._is_plaintext_file(filename, mime_type):
                return self.get_plaintext_file_content(file_id, filename)
            
            else:
                raise DocumentProcessingError(f"Unsupported file type: {mime_type}")
                
        except Exception as e:
            if "quota" in str(e).lower():
                raise APIRateLimitError(f"Google Drive API quota exceeded: {e}")
            else:
                raise DocumentProcessingError(f"Failed to get file content: {e}")
    
    def _process_sheets_content(self, file_content: io.BytesIO) -> str:
        """
        Process Google Sheets content to extract meaningful text.
        
        Args:
            file_content: Raw CSV content from Google Sheets
            
        Returns:
            Processed text content
        """
        try:
            content = file_content.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(content))
            
            processed_lines = []
            for row_num, row in enumerate(csv_reader, 1):
                if row:  # Skip empty rows
                    # Join non-empty cells with spaces
                    row_text = ' '.join([cell.strip() for cell in row if cell.strip()])
                    if row_text:
                        processed_lines.append(f"Row {row_num}: {row_text}")
            
            return '\n'.join(processed_lines)
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to process sheets content: {e}")
    
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File metadata dictionary
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, webViewLink, size, createdTime, owners"
            ).execute()
            
            # Add enhanced file type information
            file['file_type'] = self._detect_file_type(file['name'], file['mimeType'])
            
            return file
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get file metadata: {e}")
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            User information dictionary
        """
        return self.auth_service.get_user_info()
    
    def get_storage_quota(self) -> Dict[str, Any]:
        """
        Get Google Drive storage quota information.
        
        Returns:
            Storage quota information
        """
        try:
            about = self.service.about().get(
                fields="storageQuota"
            ).execute()
            
            return about.get('storageQuota', {})
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to get storage quota: {e}")
    
    def validate_file_access(self, file_id: str) -> bool:
        """
        Validate that we have access to a specific file.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            True if file is accessible
        """
        try:
            self.service.files().get(fileId=file_id, fields="id").execute()
            return True
        except Exception:
            return False 