"""pytest configuration and shared fixtures."""
import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone

@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_credentials_file():
    """Mock Google Drive credentials file."""
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "private_key_id": "test-key-id",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }

@pytest.fixture
def sample_file_metadata():
    """Sample Google Drive file metadata."""
    return {
        'id': 'test-file-123',
        'name': 'test_document.py',
        'mimeType': 'text/x-python',
        'file_type': 'py',
        'modifiedTime': '2024-01-15T10:30:00Z',
        'webViewLink': 'https://drive.google.com/file/d/test-file-123',
        'size': '1024'
    }

@pytest.fixture
def sample_google_workspace_file():
    """Sample Google Workspace file metadata."""
    return {
        'id': 'gdoc-file-456',
        'name': 'Test Document',
        'mimeType': 'application/vnd.google-apps.document',
        'file_type': 'docs',
        'modifiedTime': '2024-01-15T11:00:00Z',
        'webViewLink': 'https://docs.google.com/document/d/gdoc-file-456',
        'size': '2048'
    }

@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    env_vars = {
        'PINECONE_API_KEY': 'test-api-key-12345',
        'PINECONE_DENSE_INDEX_NAME': 'test-dense-index',
        'PINECONE_SPARSE_INDEX_NAME': 'test-sparse-index',
        'GDRIVE_CREDENTIALS_JSON': '/path/to/test/creds.json'
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for testing."""
    with patch('gdrive_pinecone_search.utils.config_manager.ConfigManager') as mock:
        config_instance = mock.return_value
        config_instance.is_owner_mode.return_value = True
        config_instance.get_pinecone_api_key.return_value = 'test-api-key'
        config_instance.get_dense_index_name.return_value = 'test-dense-index'
        config_instance.get_sparse_index_name.return_value = 'test-sparse-index'
        
        # Mock config object
        mock_config = Mock()
        mock_config.mode = 'owner'
        mock_config.settings.chunk_size = 450
        mock_config.settings.chunk_overlap = 75
        mock_config.settings.reranking_model = 'pinecone-rerank-v0'
        config_instance.get_config.return_value = mock_config
        
        yield config_instance

@pytest.fixture
def mock_auth_service():
    """Mock AuthService for testing."""
    mock_auth = Mock()
    mock_service = Mock()
    mock_auth.get_service.return_value = mock_service
    return mock_auth

@pytest.fixture
def sample_document_content():
    """Sample document content for testing."""
    return '''def hello_world():
    """Print hello world message."""
    print("Hello, World!")
    return "success"

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    result = a + b
    return result
'''

@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing."""
    return '''{
    "name": "test-config",
    "version": "1.0.0",
    "settings": {
        "debug": true,
        "timeout": 30
    }
}'''

@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing."""
    return [
        {
            'id': 'test-file-123#0',
            'chunk_text': 'def hello_world():\n    """Print hello world message."""\n    print("Hello, World!")',
            'file_id': 'test-file-123',
            'file_name': 'test_document.py',
            'file_type': 'py',
            'chunk_index': 0,
            'modified_time': '2024-01-15T10:30:00Z',
            'web_view_link': 'https://drive.google.com/file/d/test-file-123'
        },
        {
            'id': 'test-file-123#1',
            'chunk_text': 'def calculate_sum(a, b):\n    """Calculate sum of two numbers."""\n    result = a + b\n    return result',
            'file_id': 'test-file-123',
            'file_name': 'test_document.py',
            'file_type': 'py',
            'chunk_index': 1,
            'modified_time': '2024-01-15T10:30:00Z',
            'web_view_link': 'https://drive.google.com/file/d/test-file-123'
        }
    ]

@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return [
        {
            'id': 'test-file-123#0',
            'score': 0.85,
            'reranked_score': 0.92,
            'original_score': 0.78,
            'file_id': 'test-file-123',
            'file_name': 'test_document.py',
            'file_type': 'py',
            'chunk_index': 0,
            'chunk_text': 'def hello_world():\n    print("Hello, World!")',
            'web_view_link': 'https://drive.google.com/file/d/test-file-123'
        }
    ]

@pytest.fixture(autouse=True)
def setup_mock_service_factory():
    """Automatically set up mock service factory for all tests."""
    from unittest.mock import Mock
    from gdrive_pinecone_search.utils.service_factory import MockServiceFactory, set_service_factory, reset_service_factory
    
    # Create mock services
    mock_config_manager = Mock()
    mock_config_manager.validate_config.return_value = None
    mock_config_manager.get_pinecone_api_key.return_value = 'test-api-key'
    mock_config_manager.get_dense_index_name.return_value = 'test-dense-index'
    mock_config_manager.get_sparse_index_name.return_value = 'test-sparse-index'
    mock_config_manager.get_google_credentials_path.return_value = '/path/to/creds.json'
    mock_config_manager.is_owner_mode.return_value = True
    
    # Mock config object
    mock_config = Mock()
    mock_config.mode = 'owner'
    mock_config.settings = Mock()
    mock_config.settings.chunk_size = 450
    mock_config.settings.chunk_overlap = 75
    mock_config.settings.reranking_model = 'pinecone-rerank-v0'
    mock_config_manager.get_config.return_value = mock_config
    mock_config_manager.config = mock_config
    
    # Mock search service
    mock_search_service = Mock()
    mock_search_service.get_index_stats.return_value = {'total_vectors': 100}
    mock_search_service.hybrid_query.return_value = [
        {
            'id': 'test-file-123#0',
            'score': 0.85,
            'reranked_score': 0.92,
            'original_score': 0.78,
            'file_id': 'test-file-123',
            'file_name': 'test_document.py',
            'file_type': 'py',
            'chunk_index': 0,
            'chunk_text': 'def hello_world():\n    print("Hello, World!")',
            'web_view_link': 'https://drive.google.com/file/d/test-file-123'
        }
    ]
    mock_search_service.list_file_ids.return_value = []
    mock_search_service.get_index_metadata.return_value = {}
    
    # Mock other services
    mock_auth_service = Mock()
    mock_gdrive_service = Mock()
    mock_gdrive_service.get_user_info.return_value = {'emailAddress': 'test@example.com'}
    mock_gdrive_service.list_files.return_value = []
    
    mock_document_processor = Mock()
    mock_document_processor.chunk_text.return_value = []
    
    # Create mock service factory with all services
    mock_services = {
        'config_manager': mock_config_manager,
        'search_service': mock_search_service,
        'auth_service': mock_auth_service,
        'gdrive_service': mock_gdrive_service,
        'document_processor': mock_document_processor
    }
    
    mock_factory = MockServiceFactory(mock_services)
    
    # Set the mock factory globally for all tests
    set_service_factory(mock_factory)
    
    yield mock_factory
    
    # Clean up: reset to production factory after test
    reset_service_factory()

@pytest.fixture
def mock_empty_drive_scenario(setup_mock_service_factory):
    """Mock scenario with no files in Google Drive."""
    factory = setup_mock_service_factory
    factory.mock_services['gdrive_service'].list_files.return_value = []
    factory.mock_services['search_service'].hybrid_query.return_value = []
    factory.mock_services['search_service'].get_index_stats.return_value = {'total_vectors': 0}
    return factory

@pytest.fixture  
def mock_files_found_scenario(setup_mock_service_factory):
    """Mock scenario with files found in Google Drive."""
    factory = setup_mock_service_factory
    factory.mock_services['gdrive_service'].list_files.return_value = [
        {
            'id': 'file1',
            'name': 'test_document.py',
            'file_type': 'py',
            'modifiedTime': '2024-01-15T10:30:00Z',
            'webViewLink': 'https://drive.google.com/file/d/file1'
        },
        {
            'id': 'file2',
            'name': 'readme.md',
            'file_type': 'md',
            'modifiedTime': '2024-01-16T14:20:00Z',
            'webViewLink': 'https://drive.google.com/file/d/file2'
        }
    ]
    
    # Update search results to match
    factory.mock_services['search_service'].hybrid_query.return_value = [
        {
            'id': 'file1#0',
            'score': 0.89,
            'reranked_score': 0.94,
            'original_score': 0.82,
            'file_id': 'file1',
            'file_name': 'test_document.py',
            'file_type': 'py',
            'chunk_index': 0,
            'chunk_text': 'def process_documents():\n    """Process uploaded documents."""\n    return results',
            'web_view_link': 'https://drive.google.com/file/d/file1'
        },
        {
            'id': 'file2#0',
            'score': 0.76,
            'reranked_score': 0.81,
            'original_score': 0.71,
            'file_id': 'file2',
            'file_name': 'readme.md',
            'file_type': 'md',
            'chunk_index': 0,
            'chunk_text': '# Project Documentation\n\nThis project provides Google Drive integration.',
            'web_view_link': 'https://drive.google.com/file/d/file2'
        }
    ]
    
    factory.mock_services['search_service'].get_index_stats.return_value = {'total_vectors': 150}
    return factory

@pytest.fixture
def mock_large_drive_scenario(setup_mock_service_factory):
    """Mock scenario with many files in Google Drive."""
    factory = setup_mock_service_factory
    
    # Generate multiple files
    files = []
    search_results = []
    for i in range(25):
        file_id = f'file{i+1:03d}'
        files.append({
            'id': file_id,
            'name': f'document_{i+1:03d}.py',
            'file_type': 'py',
            'modifiedTime': f'2024-01-{(i%30)+1:02d}T10:30:00Z',
            'webViewLink': f'https://drive.google.com/file/d/{file_id}'
        })
        
        search_results.append({
            'id': f'{file_id}#0',
            'score': 0.85 - (i * 0.01),
            'reranked_score': 0.90 - (i * 0.01),
            'original_score': 0.80 - (i * 0.01),
            'file_id': file_id,
            'file_name': f'document_{i+1:03d}.py',
            'file_type': 'py',
            'chunk_index': 0,
            'chunk_text': f'def function_{i+1}():\n    """Function {i+1} implementation."""\n    pass',
            'web_view_link': f'https://drive.google.com/file/d/{file_id}'
        })
    
    factory.mock_services['gdrive_service'].list_files.return_value = files
    factory.mock_services['search_service'].hybrid_query.return_value = search_results[:10]  # Return top 10
    factory.mock_services['search_service'].get_index_stats.return_value = {'total_vectors': 500}
    return factory

@pytest.fixture
def mock_service_factory(setup_mock_service_factory):
    """Get the mock service factory (for tests that need direct access)."""
    return setup_mock_service_factory
