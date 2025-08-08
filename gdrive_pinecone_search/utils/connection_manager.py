"""Connection management for external services."""

import os
from typing import Optional, Dict, Any
from datetime import datetime

from .exceptions import (
    AuthenticationError, 
    ConnectionError, 
    IndexNotFoundError, 
    IncompatibleIndexError
)
from .config_manager import ConfigManager


class ConnectionManager:
    """Manages connections to external services."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._pinecone_client = None
        self._gdrive_service = None
    
    def validate_pinecone_connection(self, api_key: str, index_name: str) -> bool:
        """
        Validate Pinecone connection and index compatibility.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            
        Returns:
            True if connection is valid
            
        Raises:
            AuthenticationError: If API key is invalid
            IndexNotFoundError: If index doesn't exist
            IncompatibleIndexError: If index is incompatible
        """
        try:
            from pinecone import Pinecone
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=api_key)
            
            # Check if index exists
            if not pc.has_index(index_name):
                raise IndexNotFoundError(f"Index '{index_name}' not found")
            
            # Get index stats to validate access
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            
            # Validate index configuration
            self._validate_index_compatibility(stats, index_name)
            
            return True
            
        except Exception as e:
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                raise AuthenticationError(f"Invalid Pinecone API key: {e}")
            elif isinstance(e, (IndexNotFoundError, IncompatibleIndexError)):
                raise
            else:
                raise ConnectionError(f"Failed to connect to Pinecone: {e}")
    
    def _validate_index_compatibility(self, stats: Dict[str, Any], index_name: str):
        """
        Validate that the index is compatible with our requirements.
        
        Args:
            stats: Index statistics from Pinecone
            index_name: Name of the index
            
        Raises:
            IncompatibleIndexError: If index is incompatible
        """
        # Check dimension compatibility (should be 1024 for multilingual-e5-large)
        dimension = stats.get('dimension')
        if dimension != 1024:
            raise IncompatibleIndexError(
                f"Index '{index_name}' has dimension {dimension}, expected 1024 for multilingual-e5-large model"
            )
        
        # Check metric compatibility (should be cosine)
        metric = stats.get('metric')
        if metric != 'cosine':
            raise IncompatibleIndexError(
                f"Index '{index_name}' uses metric '{metric}', expected 'cosine'"
            )
    
    def validate_google_drive_connection(self, credentials_path: str) -> bool:
        """
        Validate Google Drive connection.
        
        Args:
            credentials_path: Path to Google Drive credentials JSON file
            
        Returns:
            True if connection is valid
            
        Raises:
            AuthenticationError: If credentials are invalid
            ConnectionError: If connection fails
        """
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            # Check if credentials file exists
            if not os.path.exists(credentials_path):
                raise AuthenticationError(f"Credentials file not found: {credentials_path}")
            
            # Load credentials
            creds = None
            token_path = os.path.join(os.path.dirname(credentials_path), 'token.json')
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/drive.readonly'])
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, ['https://www.googleapis.com/auth/drive.readonly']
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Test the connection by making a simple API call
            service = build('drive', 'v3', credentials=creds)
            about = service.about().get(fields="user").execute()
            
            return True
            
        except Exception as e:
            if "invalid" in str(e).lower() or "unauthorized" in str(e).lower():
                raise AuthenticationError(f"Invalid Google Drive credentials: {e}")
            else:
                raise ConnectionError(f"Failed to connect to Google Drive: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status for all services.
        
        Returns:
            Dictionary with connection status information
        """
        status = {
            'mode': self.config_manager.config.mode if self.config_manager.config else 'unknown',
            'pinecone': {
                'configured': False,
                'connected': False,
                'index_name': None,
    
            },
            'google_drive': {
                'configured': False,
                'connected': False,
                'credentials_path': None
            }
        }
        
        # Check Pinecone configuration
        pinecone_api_key = self.config_manager.get_pinecone_api_key()
        if pinecone_api_key and self.config_manager.config and self.config_manager.config.connection:
            status['pinecone']['configured'] = True
            status['pinecone']['index_name'] = self.config_manager.config.connection.index_name

            
            # Test connection
            try:
                self.validate_pinecone_connection(
                    pinecone_api_key,
                    status['pinecone']['index_name'],
        
                )
                status['pinecone']['connected'] = True
            except Exception:
                pass
        
        # Check Google Drive configuration (only for owner mode)
        if self.config_manager.is_owner_mode():
            credentials_path = self.config_manager.get_google_credentials_path()
            if credentials_path:
                status['google_drive']['configured'] = True
                status['google_drive']['credentials_path'] = credentials_path
                
                # Test connection
                try:
                    self.validate_google_drive_connection(credentials_path)
                    status['google_drive']['connected'] = True
                except Exception:
                    pass
        
        return status
    
    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test all configured connections.
        
        Returns:
            Dictionary with test results for each service
        """
        results = {
            'pinecone': False,
            'google_drive': False
        }
        
        # Test Pinecone
        pinecone_api_key = self.config_manager.get_pinecone_api_key()
        if pinecone_api_key and self.config_manager.config and self.config_manager.config.connection:
            try:
                self.validate_pinecone_connection(
                    pinecone_api_key,
                    self.config_manager.config.connection.index_name,
    
                )
                results['pinecone'] = True
            except Exception:
                pass
        
        # Test Google Drive (only for owner mode)
        if self.config_manager.is_owner_mode():
            credentials_path = self.config_manager.get_google_credentials_path()
            if credentials_path:
                try:
                    self.validate_google_drive_connection(credentials_path)
                    results['google_drive'] = True
                except Exception:
                    pass
        
        return results 