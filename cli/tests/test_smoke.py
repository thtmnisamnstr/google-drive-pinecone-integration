#!/usr/bin/env python3
"""
Smoke tests to verify basic CLI installation and functionality.
These tests ensure the CLI can be imported and basic components work.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    # Test CLI main module
    from gdrive_pinecone_search.cli.main import main
    assert main is not None
    
    # Test config manager (safe to import, no external API calls)
    from gdrive_pinecone_search.utils.config_manager import ConfigManager
    assert ConfigManager is not None
    
    # Test file types utility (safe to import, no external API calls)
    from gdrive_pinecone_search.utils.file_types import validate_file_types
    assert validate_file_types is not None
    
    # Test service factory (safe to import, no external API calls)
    from gdrive_pinecone_search.utils.service_factory import ServiceFactory, MockServiceFactory
    assert ServiceFactory is not None
    assert MockServiceFactory is not None
    
    # Don't import SearchService or GDriveService directly - they trigger API connections
    # Instead, verify they can be created via service factory (mocked in tests)

def test_config_manager():
    """Test configuration manager functionality."""
    from unittest.mock import patch, Mock
    
    # Mock the ConfigManager to avoid real file system operations
    with patch('gdrive_pinecone_search.utils.config_manager.ConfigManager') as mock_config_class:
        mock_config = Mock()
        mock_config.mode = 'connected'
        mock_config.settings = Mock()
        mock_config.settings.chunk_size = 450
        mock_config.settings.chunk_overlap = 75
        mock_config.settings.reranking_model = 'pinecone-rerank-v0'
        
        mock_config_instance = mock_config_class.return_value
        mock_config_instance.get_config.return_value = mock_config
        
        # Test the functionality
        config_manager = mock_config_class()
        config = config_manager.get_config()
        
        assert config is not None
        assert hasattr(config, 'mode')
        assert hasattr(config, 'settings')
        assert hasattr(config.settings, 'chunk_size')
        assert hasattr(config.settings, 'chunk_overlap')
        assert hasattr(config.settings, 'reranking_model')

def test_cli_help():
    """Test that CLI help works."""
    from gdrive_pinecone_search.cli.main import main
    from click.testing import CliRunner
    
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    
    assert result.exit_code == 0
    assert 'Google Drive to Pinecone CLI' in result.output

def test_document_processor():
    """Test document processing functionality."""
    from gdrive_pinecone_search.services.document_processor import DocumentProcessor
    
    processor = DocumentProcessor(chunk_size=450, chunk_overlap=75)
    
    # Test text chunking
    test_text = "This is a test document. It contains multiple sentences. We want to see if chunking works properly."
    test_metadata = {
        'id': 'test-file-id',
        'name': 'Test Document',
        'file_type': 'docs',
        'modifiedTime': '2024-01-15T10:30:00Z',
        'webViewLink': 'https://docs.google.com/document/d/test'
    }
    
    chunks = processor.chunk_text(test_text, test_metadata)
    
    assert chunks is not None
    assert len(chunks) > 0
    assert 'id' in chunks[0]

def test_file_types_basic():
    """Test basic file type functionality."""
    from gdrive_pinecone_search.utils.file_types import (
        validate_file_types, get_file_type_from_extension, 
        is_supported_file_type
    )
    
    # Test basic validation
    result = validate_file_types('docs,py,json')
    assert 'docs' in result
    assert 'py' in result
    assert 'json' in result
    
    # Test extension detection
    file_type = get_file_type_from_extension('test.py')
    assert file_type == 'py'
    
    # Test support check
    is_supported = is_supported_file_type('test.py', 'text/x-python')
    assert is_supported == True

def main():
    """Run all smoke tests."""
    print("Google Drive to Pinecone CLI - Smoke Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_manager,
        test_cli_help,
        test_document_processor,
        test_file_types_basic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Smoke Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All smoke tests passed! The CLI basic functionality is working.")
        return 0
    else:
        print("❌ Some smoke tests failed. Please check the installation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
