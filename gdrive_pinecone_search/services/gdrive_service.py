"""Google Drive service for file operations and content extraction."""

import io
import csv
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
from urllib.parse import urlparse

from ..utils.rate_limiter import rate_limited, GOOGLE_DRIVE_RATE_LIMITER
from ..utils.exceptions import DocumentProcessingError, APIRateLimitError
from .auth_service import AuthService


class GDriveService:
    """Service for Google Drive operations."""
    
    # Supported Google Workspace file types
    SUPPORTED_MIME_TYPES = {
        'application/vnd.google-apps.document': 'docs',
        'application/vnd.google-apps.spreadsheet': 'sheets',
        'application/vnd.google-apps.presentation': 'slides'
    }
    
    # Export formats for each file type
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
    
    @rate_limited(100, 100)  # 100 requests per 100 seconds
    def list_files(self, 
                   file_types: Optional[List[str]] = None,
                   modified_since: Optional[datetime] = None,
                   page_size: int = 100) -> Generator[Dict[str, Any], None, None]:
        """
        List Google Drive files with optional filtering.
        
        Args:
            file_types: List of file types to include (docs, sheets, slides)
            modified_since: Only include files modified since this time
            page_size: Number of files per page
            
        Yields:
            File metadata dictionaries
        """
        try:
            # Build query
            query_parts = []
            
            # Filter by file types
            if file_types:
                mime_types = [
                    mime_type for mime_type, file_type in self.SUPPORTED_MIME_TYPES.items()
                    if file_type in file_types
                ]
                if mime_types:
                    mime_query = " or ".join([f"mimeType='{mime_type}'" for mime_type in mime_types])
                    query_parts.append(f"({mime_query})")
            
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
                        # Add file type information
                        file['file_type'] = self.SUPPORTED_MIME_TYPES.get(file['mimeType'])
                        if file['file_type']:
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
    def get_file_content(self, file_id: str, mime_type: str) -> str:
        """
        Get the text content of a Google Drive file.
        
        Args:
            file_id: Google Drive file ID
            mime_type: MIME type of the file
            
        Returns:
            Extracted text content
            
        Raises:
            DocumentProcessingError: If content extraction fails
        """
        try:
            if mime_type not in self.SUPPORTED_MIME_TYPES:
                raise DocumentProcessingError(f"Unsupported file type: {mime_type}")
            
            export_format = self.EXPORT_FORMATS[mime_type]
            file_type = self.SUPPORTED_MIME_TYPES[mime_type]
            
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
            
            # Add file type information
            file['file_type'] = self.SUPPORTED_MIME_TYPES.get(file['mimeType'])
            
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