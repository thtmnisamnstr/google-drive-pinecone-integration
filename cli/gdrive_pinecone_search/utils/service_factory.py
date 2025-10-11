"""Service factory for dependency injection and testability."""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from .config_manager import ConfigManager
from ..services.search_service import SearchService
from ..services.gdrive_service import GDriveService
from ..services.document_processor import DocumentProcessor
from ..services.auth_service import AuthService


class ServiceFactoryInterface(ABC):
    """Interface for service factory to enable easy mocking."""
    
    @abstractmethod
    def create_config_manager(self) -> ConfigManager:
        """Create ConfigManager instance."""
        pass
    
    @abstractmethod
    def create_search_service(self, api_key: str, dense_index: str, sparse_index: str, 
                             reranking_model: str = "pinecone-rerank-v0") -> SearchService:
        """Create SearchService instance."""
        pass
    
    @abstractmethod
    def create_gdrive_service(self, auth_service: AuthService) -> GDriveService:
        """Create GDriveService instance."""
        pass
    
    @abstractmethod
    def create_document_processor(self, chunk_size: int = 450, chunk_overlap: int = 75) -> DocumentProcessor:
        """Create DocumentProcessor instance."""
        pass
    
    @abstractmethod
    def create_auth_service(self, credentials_path: str) -> AuthService:
        """Create AuthService instance."""
        pass


class ServiceFactory(ServiceFactoryInterface):
    """Production service factory that creates real service instances."""
    
    def __init__(self):
        """Initialize service factory."""
        pass
    
    def create_config_manager(self) -> ConfigManager:
        """Create ConfigManager instance."""
        return ConfigManager()
    
    def create_search_service(self, api_key: str, dense_index: str, sparse_index: str, 
                             reranking_model: str = "pinecone-rerank-v0") -> SearchService:
        """Create SearchService instance."""
        return SearchService(
            api_key=api_key,
            dense_index_name=dense_index,
            sparse_index_name=sparse_index,
            reranking_model=reranking_model
        )
    
    def create_gdrive_service(self, auth_service: AuthService) -> GDriveService:
        """Create GDriveService instance."""
        return GDriveService(auth_service)
    
    def create_document_processor(self, chunk_size: int = 450, chunk_overlap: int = 75) -> DocumentProcessor:
        """Create DocumentProcessor instance."""
        return DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    def create_auth_service(self, credentials_path: str) -> AuthService:
        """Create AuthService instance."""
        return AuthService(credentials_path)


class MockServiceFactory(ServiceFactoryInterface):
    """Mock service factory for testing that returns mock objects."""
    
    def __init__(self, mock_services: Optional[Dict[str, Any]] = None):
        """Initialize mock service factory.
        
        Args:
            mock_services: Dictionary of service names to mock objects
        """
        self.mock_services = mock_services or {}
    
    def create_config_manager(self) -> ConfigManager:
        """Create mock ConfigManager instance."""
        return self.mock_services.get('config_manager', self._create_default_mock('ConfigManager'))
    
    def create_search_service(self, api_key: str, dense_index: str, sparse_index: str, 
                             reranking_model: str = "pinecone-rerank-v0") -> SearchService:
        """Create mock SearchService instance."""
        return self.mock_services.get('search_service', self._create_default_mock('SearchService'))
    
    def create_gdrive_service(self, auth_service: AuthService) -> GDriveService:
        """Create mock GDriveService instance."""
        return self.mock_services.get('gdrive_service', self._create_default_mock('GDriveService'))
    
    def create_document_processor(self, chunk_size: int = 450, chunk_overlap: int = 75) -> DocumentProcessor:
        """Create mock DocumentProcessor instance."""
        return self.mock_services.get('document_processor', self._create_default_mock('DocumentProcessor'))
    
    def create_auth_service(self, credentials_path: str) -> AuthService:
        """Create mock AuthService instance."""
        return self.mock_services.get('auth_service', self._create_default_mock('AuthService'))
    
    def _create_default_mock(self, service_name: str):
        """Create a default mock object for a service."""
        from unittest.mock import Mock
        return Mock(name=f'Mock{service_name}')


# Global service factory instance - can be replaced for testing
_service_factory: ServiceFactoryInterface = ServiceFactory()


def get_service_factory() -> ServiceFactoryInterface:
    """Get the current service factory instance."""
    return _service_factory


def set_service_factory(factory: ServiceFactoryInterface) -> None:
    """Set the service factory instance (for testing)."""
    global _service_factory
    _service_factory = factory


def reset_service_factory() -> None:
    """Reset to production service factory."""
    global _service_factory
    _service_factory = ServiceFactory()
