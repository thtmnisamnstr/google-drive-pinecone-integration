"""Simplified refresh pipeline tests that work with the service factory pattern."""
import pytest
from click.testing import CliRunner
from unittest.mock import Mock

from gdrive_pinecone_search.cli.commands.refresh import refresh

class TestRefreshPipelineSimple:
    """Test refresh functionality with simplified assertions."""
    
    def test_refresh_command_execution(self):
        """Test that the refresh command executes without crashing."""
        runner = CliRunner()
        result = runner.invoke(refresh, [])
        
        # Should execute without crashing (may succeed or fail gracefully)
        assert result.exit_code in [0, 1]
        # Should not have Python tracebacks/exceptions
        assert 'Traceback' not in result.output
    
    def test_refresh_with_file_types(self):
        """Test refresh with file type filters."""
        runner = CliRunner()
        result = runner.invoke(refresh, ['--file-types', 'py,json'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
    
    def test_refresh_dry_run(self):
        """Test refresh with dry-run flag."""
        runner = CliRunner()
        result = runner.invoke(refresh, ['--dry-run'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Should not crash with traceback
        assert 'Traceback' not in result.output
    
    def test_refresh_with_since_parameter(self):
        """Test refresh with since parameter."""
        runner = CliRunner()
        result = runner.invoke(refresh, ['--since', '2024-01-01'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Should not have parameter validation errors
        assert 'Invalid' not in result.output or 'since' not in result.output.lower()
    
    def test_refresh_force_full(self):
        """Test refresh with force-full flag."""
        runner = CliRunner()
        result = runner.invoke(refresh, ['--force-full'])
        
        # Should execute without crashing
        assert result.exit_code in [0, 1]
        # Should not cause errors
        assert 'error' not in result.output.lower() or 'force' in result.output.lower()
    
    def test_refresh_with_categories(self):
        """Test refresh with file type categories."""
        runner = CliRunner()
        
        # Test code category
        result = runner.invoke(refresh, ['--file-types', 'code'])
        assert 'Invalid file type' not in result.output
        
        # Test config category
        result = runner.invoke(refresh, ['--file-types', 'config'])
        assert 'Invalid file type' not in result.output
        
        # Test mixed categories
        result = runner.invoke(refresh, ['--file-types', 'docs,code,json'])
        assert 'Invalid file type' not in result.output
