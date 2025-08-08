#!/usr/bin/env python3
"""
Simple test script to verify the CLI installation and basic functionality.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from gdrive_pinecone_search.cli.main import main
        print("✓ CLI main module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import CLI main module: {e}")
        return False
    
    try:
        from gdrive_pinecone_search.utils.config_manager import ConfigManager
        print("✓ Config manager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config manager: {e}")
        return False
    
    try:
        from gdrive_pinecone_search.services.pinecone_service import PineconeService
        print("✓ Pinecone service imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Pinecone service: {e}")
        return False
    
    try:
        from gdrive_pinecone_search.services.gdrive_service import GDriveService
        print("✓ Google Drive service imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Google Drive service: {e}")
        return False
    
    return True

def test_config_manager():
    """Test configuration manager functionality."""
    print("\nTesting configuration manager...")
    
    try:
        from gdrive_pinecone_search.utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        print(f"✓ Configuration loaded: mode = {config.mode}")
        print(f"✓ Settings: chunk_size = {config.settings.chunk_size}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration manager test failed: {e}")
        return False

def test_cli_help():
    """Test that CLI help works."""
    print("\nTesting CLI help...")
    
    try:
        from gdrive_pinecone_search.cli.main import main
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        if result.exit_code == 0 and 'Google Drive to Pinecone CLI' in result.output:
            print("✓ CLI help command works")
            return True
        else:
            print(f"✗ CLI help command failed: {result.output}")
            return False
    except Exception as e:
        print(f"✗ CLI help test failed: {e}")
        return False

def test_document_processor():
    """Test document processing functionality."""
    print("\nTesting document processor...")
    
    try:
        from gdrive_pinecone_search.services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor(chunk_size=800, chunk_overlap=150)
        
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
        
        if chunks:
            print(f"✓ Document processor created {len(chunks)} chunks")
            print(f"✓ First chunk ID: {chunks[0]['id']}")
            return True
        else:
            print("✗ Document processor failed to create chunks")
            return False
    except Exception as e:
        print(f"✗ Document processor test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Google Drive to Pinecone CLI - Installation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config_manager,
        test_cli_help,
        test_document_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The CLI is ready to use.")
        print("\nNext steps:")
        print("1. Set up your Pinecone API key: export PINECONE_API_KEY='your-key'")
        print("2. For owner mode, set up Google Drive credentials")
        print("3. Run: gdrive-pinecone-search help")
        return 0
    else:
        print("❌ Some tests failed. Please check the installation.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 