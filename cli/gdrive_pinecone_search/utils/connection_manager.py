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
    
    def validate_pinecone_connection(self, api_key: str, index_name: str, is_sparse: bool = False) -> bool:
        """
        Validate Pinecone connection and index compatibility.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            is_sparse: Whether this is a sparse index
            
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
            self._validate_index_compatibility(stats, index_name, is_sparse)
            
            return True
            
        except Exception as e:
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                raise AuthenticationError(f"Invalid Pinecone API key: {e}")
            elif isinstance(e, (IndexNotFoundError, IncompatibleIndexError)):
                raise
            else:
                raise ConnectionError(f"Failed to connect to Pinecone: {e}")
    
    def validate_hybrid_connection(self, api_key: str, dense_index_name: str, sparse_index_name: str) -> bool:
        """
        Validate hybrid search connection with both dense and sparse indexes.
        
        Args:
            api_key: Pinecone API key
            dense_index_name: Name of the dense Pinecone index
            sparse_index_name: Name of the sparse Pinecone index
            
        Returns:
            True if both connections are valid
            
        Raises:
            AuthenticationError: If API key is invalid
            IndexNotFoundError: If indexes don't exist
            IncompatibleIndexError: If indexes are incompatible
        """
        try:
            # Validate dense index
            self.validate_pinecone_connection(api_key, dense_index_name, is_sparse=False)
            
            # Validate sparse index
            self.validate_pinecone_connection(api_key, sparse_index_name, is_sparse=True)
            
            return True
            
        except Exception as e:
            raise e
    
    def _validate_index_compatibility(self, stats: Dict[str, Any], index_name: str, is_sparse: bool = False):
        """
        Validate that the index is compatible with our requirements.
        
        Args:
            stats: Index statistics from Pinecone
            index_name: Name of the index
            is_sparse: Whether this is a sparse index
            
        Raises:
            IncompatibleIndexError: If index is incompatible
        """
        # Check dimension compatibility
        dimension = stats.get('dimension')
        if is_sparse:
            # Sparse indexes can have different dimensions (often None or 0 for sparse vectors)
            # We don't validate dimension for sparse indexes as they use sparse vector format
            pass
        else:
            # Dense indexes should have dimension 1024 for hybrid search models
            if dimension != 1024:
                raise IncompatibleIndexError(
                    f"Index '{index_name}' has dimension {dimension}, expected 1024 for dense hybrid search models"
                )
        
        # Check metric compatibility
        metric = stats.get('metric')
        if is_sparse:
            # Sparse indexes can use either cosine or dotproduct
            if metric not in ['cosine', 'dotproduct']:
                raise IncompatibleIndexError(
                    f"Index '{index_name}' uses metric '{metric}', expected 'cosine' or 'dotproduct' for sparse indexes"
                )
        else:
            # Dense indexes should use cosine
            if metric != 'cosine':
                raise IncompatibleIndexError(
                    f"Index '{index_name}' uses metric '{metric}', expected 'cosine' for dense indexes"
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
            from ..services.auth_service import AuthService
            from ..services.gdrive_service import GDriveService
            
            # Initialize services
            auth_service = AuthService(credentials_path)
            gdrive_service = GDriveService(auth_service)
            
            # Test connection by getting user info
            user_info = gdrive_service.get_user_info()
            
            if not user_info or 'emailAddress' not in user_info:
                raise AuthenticationError("Failed to get user information from Google Drive")
            
            return True
            
        except Exception as e:
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                raise AuthenticationError(f"Invalid Google Drive credentials: {e}")
            else:
                raise ConnectionError(f"Failed to connect to Google Drive: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status for all services.
        
        Returns:
            Dictionary with connection status information
        """
        status = {
            'pinecone': {
                'connected': False,
                'error': None,
                'indexes': {}
            },
            'google_drive': {
                'connected': False,
                'error': None,
                'user_info': None
            }
        }
        
        # Check Pinecone connection
        try:
            if self.config_manager.get_pinecone_api_key():
                dense_index_name = self.config_manager.get_dense_index_name()
                sparse_index_name = self.config_manager.get_sparse_index_name()
                
                if dense_index_name and sparse_index_name:
                    status['pinecone']['indexes'] = {
                        'dense': dense_index_name,
                        'sparse': sparse_index_name
                    }
                    
                    # Test hybrid connection (but don't fail if it doesn't work)
                    try:
                        self.validate_hybrid_connection(
                            self.config_manager.get_pinecone_api_key(),
                            dense_index_name,
                            sparse_index_name
                        )
                        status['pinecone']['connected'] = True
                    except Exception as validation_error:
                        status['pinecone']['connected'] = False
                        status['pinecone']['error'] = str(validation_error)
                else:
                    status['pinecone']['error'] = "Index names not configured"
            else:
                status['pinecone']['error'] = "API key not configured"
                
        except Exception as e:
            status['pinecone']['error'] = str(e)
        
        # Check Google Drive connection (only in owner mode)
        if self.config_manager.is_owner_mode():
            try:
                credentials_path = self.config_manager.get_google_credentials_path()
                if credentials_path:
                    # Test connection (but don't fail if it doesn't work)
                    try:
                        self.validate_google_drive_connection(credentials_path)
                        
                        # Get user info
                        from ..services.auth_service import AuthService
                        from ..services.gdrive_service import GDriveService
                        
                        auth_service = AuthService(credentials_path)
                        gdrive_service = GDriveService(auth_service)
                        user_info = gdrive_service.get_user_info()
                        
                        status['google_drive']['connected'] = True
                        status['google_drive']['user_info'] = user_info
                    except Exception as validation_error:
                        status['google_drive']['connected'] = False
                        status['google_drive']['error'] = str(validation_error)
                else:
                    status['google_drive']['error'] = "Credentials not configured"
                    
            except Exception as e:
                status['google_drive']['error'] = str(e)
        
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
        
        # Test Pinecone connection
        try:
            if self.config_manager.get_pinecone_api_key():
                dense_index_name = self.config_manager.get_dense_index_name()
                sparse_index_name = self.config_manager.get_sparse_index_name()
                
                if dense_index_name and sparse_index_name:
                    self.validate_hybrid_connection(
                        self.config_manager.get_pinecone_api_key(),
                        dense_index_name,
                        sparse_index_name
                    )
                    results['pinecone'] = True
        except Exception:
            pass
        
        # Test Google Drive connection (only in owner mode)
        if self.config_manager.is_owner_mode():
            try:
                credentials_path = self.config_manager.get_google_credentials_path()
                if credentials_path:
                    self.validate_google_drive_connection(credentials_path)
                    results['google_drive'] = True
            except Exception:
                pass
        
        return results 