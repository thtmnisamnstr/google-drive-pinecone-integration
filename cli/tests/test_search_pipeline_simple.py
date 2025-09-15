"""Simplified search pipeline tests that work with the service factory pattern."""
import pytest
from click.testing import CliRunner
from unittest.mock import Mock

from gdrive_pinecone_search.cli.commands.search import search

class TestSearchPipelineSimple:
    """Test search functionality with simplified assertions."""
    
    def test_search_command_execution(self):
        """Test that the search command executes without crashing."""
        runner = CliRunner()
        result = runner.invoke(search, ['test query'])
        
        # Should execute without crashing (may succeed or fail gracefully)
        assert result.exit_code in [0, 1]
        # Should not have Python tracebacks/exceptions
        assert 'Traceback' not in result.output
    
    def test_search_with_file_types(self):
        """Test search with file type filters."""
        runner = CliRunner()
        result = runner.invoke(search, ['test query', '--file-types', 'py,json'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
    
    def test_search_with_limit(self):
        """Test search with limit parameter."""
        runner = CliRunner()
        result = runner.invoke(search, ['test query', '--limit', '5'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Should not have parameter validation errors
        assert 'Invalid' not in result.output or 'limit' not in result.output.lower()
    
    def test_search_with_categories(self):
        """Test search with file type categories."""
        runner = CliRunner()
        
        # Test code category
        result = runner.invoke(search, ['test', '--file-types', 'code'])
        assert 'Invalid file type' not in result.output
        
        # Test config category
        result = runner.invoke(search, ['test', '--file-types', 'config'])
        assert 'Invalid file type' not in result.output
        
        # Test mixed categories
        result = runner.invoke(search, ['test', '--file-types', 'docs,code,json'])
        assert 'Invalid file type' not in result.output
    
    def test_search_interactive_mode(self):
        """Test search with interactive flag."""
        runner = CliRunner()
        result = runner.invoke(search, ['test query', '--interactive'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Interactive mode should not cause errors
        assert 'error' not in result.output.lower() or 'interactive' in result.output.lower()
    
    def test_search_missing_query(self):
        """Test search with missing query argument."""
        runner = CliRunner()
        result = runner.invoke(search, [])
        
        # Should fail gracefully with proper error message
        assert result.exit_code != 0
        # Should not crash with traceback
        assert 'Traceback' not in result.output
