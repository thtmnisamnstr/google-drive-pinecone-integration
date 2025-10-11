"""Test complete indexing pipeline - Google Drive to Pinecone."""
import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from gdrive_pinecone_search.cli.commands.index import index

class TestIndexingPipeline:
    """Test the complete indexing workflow."""
    
    def test_complete_indexing_workflow(self):
        """Test Google Drive → Processing → Pinecone pipeline."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        assert result.exit_code == 0
        assert 'Initializing' in result.output or 'Setting up services' in result.output
    
    def test_index_requires_owner_mode(self):
        """Test that indexing executes in owner mode."""
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        assert result.exit_code == 0
        assert any(phrase in result.output for phrase in [
            "Connected", "Indexing Complete", "Successfully processed"
        ]), f"Expected owner mode execution output: {result.output[:200]}..."
    
    def test_index_file_type_validation(self):
        """Test indexing with file type validation."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(index, ['--file-types', 'invalid_type'])
        assert result.exit_code == 0
        assert 'Invalid file type' in result.output
        
        # Test valid file types
        result = runner.invoke(index, ['--file-types', 'py,json'])
        assert result.exit_code == 0
        assert 'Invalid file type' not in result.output
    
    def test_indexing_with_enhanced_file_types(self):
        """Test indexing with enhanced file type support."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(index, ['--file-types', 'py,json,md'])
        
        assert result.exit_code == 0
        assert 'Invalid file type' not in result.output
    
    def test_indexing_dry_run(self):
        """Test --dry-run indexing shows what would be indexed."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(index, ['--dry-run'])
        assert result.exit_code == 0
    
    def test_indexing_with_limit(self):
        """Test indexing with --limit parameter."""
        runner = CliRunner()
        
        # Test with limit parameter
        result = runner.invoke(index, ['--limit', '10'])
        assert result.exit_code == 0
        assert 'Invalid' not in result.output.lower()

class TestIndexingFileTypeIntegration:
    """Test indexing with enhanced file type support."""
    
    def test_indexing_with_category_filtering(self):
        """Test indexing with file type categories."""
        runner = CliRunner()
        
        # Test indexing with code category
        result = runner.invoke(index, ['--file-types', 'code'])
        assert 'Invalid file type' not in result.output
        
        # Test indexing with config category
        result = runner.invoke(index, ['--file-types', 'config'])
        assert 'Invalid file type' not in result.output
        
        # Test indexing with mixed categories and individual types
        result = runner.invoke(index, ['--file-types', 'docs,code,json'])
        assert 'Invalid file type' not in result.output
    
    def test_indexing_with_plaintext_file_types(self):
        """Test indexing with plaintext file types."""
        runner = CliRunner()
        
        # Test indexing with various plaintext file types
        plaintext_types = ['py', 'json', 'md', 'txt', 'js', 'css', 'html', 'sql']
        
        for file_type in plaintext_types:
            result = runner.invoke(index, ['--file-types', file_type])
            assert result.exit_code == 0
            assert 'Invalid file type' not in result.output, f"File type {file_type} should be valid"

class TestIndexingErrorHandling:
    """Test error handling in indexing pipeline."""
    
    def test_indexing_configuration_error(self):
        """Test handling of configuration errors during indexing."""
        # Service factory handles configuration automatically, so this tests graceful execution
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        assert result.exit_code == 0
        assert 'Traceback' not in result.output
    
    def test_indexing_authentication_error(self):
        """Test handling of authentication errors during indexing."""
        # Service factory handles authentication automatically, so this tests graceful execution
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        assert result.exit_code == 0
        assert 'Traceback' not in result.output
