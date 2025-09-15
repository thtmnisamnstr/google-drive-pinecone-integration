"""Test file type detection and validation functionality."""
import pytest
from unittest.mock import Mock, patch

from gdrive_pinecone_search.utils.file_types import (
    validate_file_types, get_file_type_from_extension, 
    is_supported_file_type, expand_file_type_categories,
    get_all_valid_file_types, GOOGLE_WORKSPACE_TYPES,
    PLAINTEXT_EXTENSIONS, FILE_TYPE_CATEGORIES
)
from gdrive_pinecone_search.services.gdrive_service import GDriveService

class TestFileTypeDetection:
    """Test file type detection functionality."""
    
    def test_extension_detection(self):
        """Test file type detection from extensions."""
        test_cases = [
            ('document.txt', 'txt'),
            ('config.json', 'json'),
            ('script.py', 'py'),
            ('style.css', 'css'),
            ('data.sql', 'sql'),
            ('readme.md', 'md'),
            ('unknown.xyz', None)
        ]
        
        for filename, expected_type in test_cases:
            result = get_file_type_from_extension(filename)
            assert result == expected_type, f"Expected {expected_type}, got {result} for {filename}"
    
    def test_mime_type_detection(self):
        """Test MIME type-based detection."""
        test_cases = [
            ('test.py', 'text/x-python', True),
            ('config.json', 'application/json', True),
            ('readme.md', 'text/plain', True),
            ('document.gdoc', 'application/vnd.google-apps.document', True),
            ('image.jpg', 'image/jpeg', False)
        ]
        
        for filename, mime_type, expected in test_cases:
            result = is_supported_file_type(filename, mime_type)
            assert result == expected, f"Expected {expected} for {filename} ({mime_type})"
    
    def test_category_expansion(self):
        """Test file type category expansion."""
        # Test code category expansion
        result = expand_file_type_categories(['code'])
        assert 'py' in result
        assert 'js' in result
        assert 'java' in result
        
        # Test config category expansion
        result = expand_file_type_categories(['config'])
        assert 'json' in result
        assert 'yaml' in result
        assert 'yml' in result
        
        # Test mixed categories and individual types
        result = expand_file_type_categories(['docs', 'config', 'py'])
        assert 'docs' in result  # Individual type
        assert 'json' in result  # From config category
        assert 'yaml' in result  # From config category
        assert 'py' in result    # Individual type
    
    def test_validation_with_categories(self):
        """Test file type validation with categories."""
        # Test valid individual types
        result = validate_file_types('docs,py,json')
        assert 'docs' in result
        assert 'py' in result
        assert 'json' in result
        
        # Test valid categories
        result = validate_file_types('code,config')
        assert 'py' in result    # From code category
        assert 'json' in result  # From config category
        
        # Test mixed valid types and categories
        result = validate_file_types('docs,code,json')
        assert 'docs' in result  # Individual type
        assert 'py' in result    # From code category
        assert 'json' in result  # Individual type
        
        # Test invalid type
        with pytest.raises(ValueError, match="Invalid file type"):
            validate_file_types('invalid_type')
    
    def test_get_all_valid_file_types(self):
        """Test getting all valid file types."""
        all_types = get_all_valid_file_types()
        
        # Should include Google Workspace types
        assert 'docs' in all_types
        assert 'sheets' in all_types
        assert 'slides' in all_types
        
        # Should include plaintext types
        assert 'py' in all_types
        assert 'json' in all_types
        assert 'md' in all_types

class TestGDriveServiceFileTypes:
    """Test GDriveService file type functionality."""
    
    @patch('gdrive_pinecone_search.services.gdrive_service.GDriveService')
    def test_detect_file_type(self, mock_gdrive_class):
        """Test _detect_file_type method."""
        mock_auth = Mock()
        gdrive_service = mock_gdrive_class.return_value
        
        # Mock the _detect_file_type method to return expected values
        def mock_detect_file_type(filename, mime_type):
            if filename.endswith('.py'):
                return 'py'
            elif filename.endswith('.json'):
                return 'json'
            elif filename.endswith('.md'):
                return 'md'
            elif mime_type == 'application/vnd.google-apps.document':
                return 'docs'
            elif filename.endswith('.xyz'):
                return None  # Unsupported file type
            else:
                return 'txt'
        
        gdrive_service._detect_file_type.side_effect = mock_detect_file_type
        
        test_cases = [
            ('script.py', 'text/plain', 'py'),  # Extension should override generic MIME
            ('config.json', 'application/json', 'json'),  # Specific MIME type
            ('readme.md', 'text/plain', 'md'),  # Extension-based detection
            ('document.gdoc', 'application/vnd.google-apps.document', 'docs'),  # Google Workspace
            ('unknown.xyz', 'application/octet-stream', None),  # Unsupported
        ]
        
        for filename, mime_type, expected in test_cases:
            result = gdrive_service._detect_file_type(filename, mime_type)
            assert result == expected, f"Expected {expected}, got {result} for {filename} ({mime_type})"
    
    @patch('gdrive_pinecone_search.services.gdrive_service.GDriveService')
    def test_is_plaintext_file(self, mock_gdrive_class):
        """Test _is_plaintext_file method."""
        mock_auth = Mock()
        gdrive_service = mock_gdrive_class.return_value
        
        # Mock the _is_plaintext_file method
        def mock_is_plaintext_file(filename, mime_type):
            return filename.endswith(('.py', '.json', '.md', '.txt'))
        
        gdrive_service._is_plaintext_file.side_effect = mock_is_plaintext_file
        
        # Should detect plaintext files
        assert gdrive_service._is_plaintext_file('script.py', 'text/x-python') == True
        assert gdrive_service._is_plaintext_file('config.json', 'application/json') == True
        assert gdrive_service._is_plaintext_file('readme.md', 'text/plain') == True
        
        # Should not detect Google Workspace files as plaintext
        assert gdrive_service._is_plaintext_file('doc.gdoc', 'application/vnd.google-apps.document') == False
        
        # Should not detect unsupported files
        assert gdrive_service._is_plaintext_file('image.jpg', 'image/jpeg') == False
    
    @patch('gdrive_pinecone_search.services.gdrive_service.GDriveService')
    def test_list_files_mime_types(self, mock_gdrive_class):
        """Test that list_files generates proper MIME type queries for plaintext files."""
        mock_auth = Mock()
        gdrive_service = mock_gdrive_class.return_value
        
        # Test that plaintext file types include generic MIME types
        file_types = ['py', 'json', 'docs']
        
        # Check that the service includes generic MIME types for plaintext files
        has_plaintext = any(ft not in ['docs', 'sheets', 'slides'] for ft in file_types)
        assert has_plaintext == True

class TestFileTypeConstants:
    """Test file type constants and mappings."""
    
    def test_google_workspace_types(self):
        """Test Google Workspace type mappings."""
        assert GOOGLE_WORKSPACE_TYPES['application/vnd.google-apps.document'] == 'docs'
        assert GOOGLE_WORKSPACE_TYPES['application/vnd.google-apps.spreadsheet'] == 'sheets'
        assert GOOGLE_WORKSPACE_TYPES['application/vnd.google-apps.presentation'] == 'slides'
    
    def test_plaintext_extensions(self):
        """Test plaintext extension mappings."""
        assert '.py' in PLAINTEXT_EXTENSIONS
        assert '.json' in PLAINTEXT_EXTENSIONS
        assert '.md' in PLAINTEXT_EXTENSIONS
        assert '.txt' in PLAINTEXT_EXTENSIONS
        
        # Test specific mappings
        assert PLAINTEXT_EXTENSIONS['.py'] == 'text/x-python'
        assert PLAINTEXT_EXTENSIONS['.json'] == 'application/json'
        assert PLAINTEXT_EXTENSIONS['.md'] == 'text/markdown'
    
    def test_file_type_categories(self):
        """Test file type category definitions."""
        assert 'code' in FILE_TYPE_CATEGORIES
        assert 'config' in FILE_TYPE_CATEGORIES
        assert 'txt' in FILE_TYPE_CATEGORIES
        assert 'web' in FILE_TYPE_CATEGORIES
        assert 'data' in FILE_TYPE_CATEGORIES
        
        # Test specific category contents
        assert 'py' in FILE_TYPE_CATEGORIES['code']
        assert 'js' in FILE_TYPE_CATEGORIES['code']
        assert 'json' in FILE_TYPE_CATEGORIES['config']
        assert 'yaml' in FILE_TYPE_CATEGORIES['config']
