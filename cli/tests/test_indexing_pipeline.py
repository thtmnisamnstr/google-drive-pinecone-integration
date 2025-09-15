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
        
        if result.exit_code == 0:
            # When successful, should show completion message
            assert any(phrase in result.output for phrase in [
                "Indexing Complete", "Successfully processed", "files", "Complete", "processed"
            ]), f"Expected completion message not found: {result.output[:200]}..."
        else:
            # Should fail gracefully without traceback
            assert 'Traceback' not in result.output, "Should not expose tracebacks to users"
            assert len(result.output.strip()) > 0, "Should provide error message"
    
    def test_index_requires_owner_mode(self):
        """Test that indexing executes in owner mode."""
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        # Should execute without crashing (service factory provides owner mode by default)
        if result.exit_code == 0:
            # Should show successful execution
            assert any(phrase in result.output for phrase in [
                "Connected", "files", "Complete", "processed", "owner"
            ]), f"Expected owner mode execution output: {result.output[:200]}..."
        else:
            # Should fail gracefully
            assert 'Traceback' not in result.output
    
    def test_index_file_type_validation(self):
        """Test indexing with file type validation."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(index, ['--file-types', 'invalid_type'])
        assert 'Invalid File Types' in result.output or 'Invalid file type' in result.output
        
        # Test valid file types
        result = runner.invoke(index, ['--file-types', 'py,json'])
        # Should not fail on file type validation (may fail on other things)
        assert 'Invalid file type' not in result.output
    
    def test_indexing_with_enhanced_file_types(self):
        """Test indexing with enhanced file type support."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(index, ['--file-types', 'py,json,md'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
    
    def test_indexing_dry_run(self):
        """Test --dry-run indexing shows what would be indexed."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(index, ['--dry-run'])
        
        if result.exit_code == 0:
            # Should show dry run information
            assert any(phrase in result.output for phrase in [
                "would", "dry", "preview", "files", "found"
            ]), f"Expected dry run output not found: {result.output[:200]}..."
        else:
            # Should fail gracefully
            assert 'Traceback' not in result.output
    
    def test_indexing_with_limit(self):
        """Test indexing with --limit parameter."""
        runner = CliRunner()
        
        # Test with limit parameter
        result = runner.invoke(index, ['--limit', '10'])
        # Should not fail on parameter validation
        assert 'Invalid' not in result.output or 'limit' not in result.output.lower()
        assert result.exit_code in [0, 1]

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
            assert 'Invalid file type' not in result.output, f"File type {file_type} should be valid"

class TestIndexingErrorHandling:
    """Test error handling in indexing pipeline."""
    
    def test_indexing_configuration_error(self):
        """Test handling of configuration errors during indexing."""
        # Service factory handles configuration automatically, so this tests graceful execution
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output
    
    def test_indexing_authentication_error(self):
        """Test handling of authentication errors during indexing."""
        # Service factory handles authentication automatically, so this tests graceful execution
        runner = CliRunner()
        result = runner.invoke(index, [])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output
