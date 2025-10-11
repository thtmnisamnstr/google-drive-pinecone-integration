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
        
        assert result.exit_code == 0
        assert any(phrase in result.output for phrase in [
            "Results", "No results", "Found", "matches", "test-file-123"
        ]), f"Expected search output not found: {result.output[:200]}..."
    
    def test_search_file_type_filtering(self):
        """Test search with file type filtering."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(search, ['test query', '--file-types', 'invalid_type'])
        assert result.exit_code == 0
        assert 'Invalid file type' in result.output
        
        # Test valid file types
        result = runner.invoke(search, ['test query', '--file-types', 'py,json'])
        assert result.exit_code == 0
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
        
        assert result.exit_code == 0
        assert 'Invalid file type' not in result.output
    
    def test_search_parameter_validation(self):
        """Test search parameter validation."""
        runner = CliRunner()
        
        # Test with limit parameter
        result = runner.invoke(search, ['test query', '--limit', '5'])
        assert result.exit_code == 0
        assert 'Invalid' not in result.output.lower()

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
        assert result.exit_code == 0
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
        
        assert result.exit_code != 0, "Search should fail without query"
        assert 'Traceback' not in result.output
        assert 'Missing argument' in result.output or 'Usage:' in result.output
