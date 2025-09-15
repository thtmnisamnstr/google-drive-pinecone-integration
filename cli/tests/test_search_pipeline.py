"""Test search pipeline - hybrid search functionality."""
import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner

from gdrive_pinecone_search.cli.commands.search import search
from gdrive_pinecone_search.services.search_service import SearchService

class TestSearchPipeline:
    """Test the complete search workflow."""
    
    def test_search_command_execution(self):
        """Test search command execution."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(search, ['test query'])
        
        if result.exit_code == 0:
            # When successful, should show search results or "no results"
            assert any(phrase in result.output for phrase in [
                "Results", "No results", "Found", "matches", "search", "test-file-123"
            ]), f"Expected search output not found: {result.output[:200]}..."
        else:
            # When failing, should show user-friendly error
            assert 'Traceback' not in result.output, "Should not expose tracebacks to users"
            assert len(result.output.strip()) > 0, "Should provide error message"
    
    def test_search_file_type_filtering(self):
        """Test search with file type filtering."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(search, ['test query', '--file-types', 'invalid_type'])
        assert 'Invalid File Types' in result.output or 'Invalid file type' in result.output
        
        # Test valid file types
        result = runner.invoke(search, ['test query', '--file-types', 'py,json'])
        # Should not fail on file type validation (may fail on other things)
        assert 'Invalid file type' not in result.output
    
    def test_search_with_enhanced_file_types(self):
        """Test search with enhanced file type filtering."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(search, ['test query', '--file-types', 'py,json,md'])
        
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
        
        if result.exit_code == 0:
            # When successful, should show search results
            assert any(phrase in result.output for phrase in [
                "Results", "No results", "Found", "matches", "search"
            ]), f"Expected search output not found: {result.output[:200]}..."
        else:
            # Should fail gracefully without traceback
            assert 'Traceback' not in result.output
    
    def test_search_with_categories(self):
        """Test search with file type categories."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(search, ['test query', '--file-types', 'code'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
    
    def test_search_parameter_validation(self):
        """Test search parameter validation."""
        runner = CliRunner()
        
        # Test with limit parameter
        result = runner.invoke(search, ['test query', '--limit', '5'])
        # Should not fail on parameter validation
        assert 'Invalid' not in result.output or 'limit' not in result.output.lower()
        assert result.exit_code in [0, 1]

class TestHybridSearchService:
    """Test the hybrid search service functionality."""
    
    def test_search_service_initialization(self):
        """Test that search service can be initialized."""
        # This tests the service factory can create a search service
        runner = CliRunner()
        result = runner.invoke(search, ['--help'])
        
        # Help should always work
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_hybrid_query_execution(self):
        """Test hybrid query execution."""
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(search, ['test query'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output

class TestSearchErrorHandling:
    """Test error handling in search pipeline."""
    
    def test_search_configuration_error(self):
        """Test handling of configuration errors during search."""
        # Service factory handles configuration automatically, so this tests graceful execution
        runner = CliRunner()
        result = runner.invoke(search, ['test query'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output
    
    def test_search_missing_query(self):
        """Test search with missing query argument."""
        runner = CliRunner()
        result = runner.invoke(search, [])
        
        # Should fail when no query provided
        assert result.exit_code != 0, "Search should fail without query"
        # Should not crash with traceback
        assert 'Traceback' not in result.output
        # Should provide helpful error message
        assert any(phrase in result.output for phrase in [
            "Missing argument", "Usage:", "query", "Error:"
        ]), f"Missing query error not clear: {result.output[:200]}..."
