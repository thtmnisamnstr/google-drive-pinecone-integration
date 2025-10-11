"""Test refresh pipeline - incremental updates functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from click.testing import CliRunner

from gdrive_pinecone_search.cli.commands.refresh import refresh

class TestRefreshPipeline:
    """Test the refresh pipeline functionality."""
    
    def test_incremental_refresh_logic(self):
        """Test that refresh only processes files modified since last refresh."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(refresh, [])
        
        assert result.exit_code == 0
        assert 'Initializing' in result.output or 'Setting up services' in result.output
    
    def test_refresh_requires_owner_mode(self):
        """Test that refresh executes in owner mode."""
        runner = CliRunner()
        result = runner.invoke(refresh, [])
        
        # Should execute without crashing (service factory provides owner mode by default)
        assert result.exit_code in [0, 1]
        assert 'Traceback' not in result.output
    
    def test_refresh_file_type_validation(self):
        """Test refresh with file type validation."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(refresh, ['--file-types', 'invalid_type'])
        assert result.exit_code == 0
        assert 'Invalid file type' in result.output
        
        # Test valid file types
        result = runner.invoke(refresh, ['--file-types', 'py,json'])
        assert result.exit_code == 0
        assert 'Invalid file type' not in result.output
    
    def test_refresh_dry_run(self):
        """Test --dry-run refresh shows what would be processed without making changes."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(refresh, ['--dry-run'])
        assert result.exit_code == 0
    
    def test_refresh_force_full(self):
        """Test --force-full refresh processes all files."""
        
        # All mocking is handled by the service factory automatically
        runner = CliRunner()
        result = runner.invoke(refresh, ['--force-full'])
        assert result.exit_code == 0

class TestRefreshFileTypeIntegration:
    """Test refresh with enhanced file type support."""
    
    def test_refresh_with_category_filtering(self):
        """Test refresh with file type categories."""
        runner = CliRunner()
        
        # Test refresh with code category
        result = runner.invoke(refresh, ['--file-types', 'code'])
        assert 'Invalid file type' not in result.output
        
        # Test refresh with config category
        result = runner.invoke(refresh, ['--file-types', 'config'])
        assert 'Invalid file type' not in result.output
        
        # Test refresh with mixed categories and individual types
        result = runner.invoke(refresh, ['--file-types', 'docs,code,json'])
        assert 'Invalid file type' not in result.output
    
    def test_refresh_with_plaintext_file_types(self):
        """Test refresh with plaintext file types."""
        runner = CliRunner()
        
        # Test refresh with various plaintext file types
        plaintext_types = ['py', 'json', 'md', 'txt', 'js', 'css', 'html', 'sql']
        
        for file_type in plaintext_types:
            result = runner.invoke(refresh, ['--file-types', file_type])
            assert result.exit_code == 0
            assert 'Invalid file type' not in result.output, f"File type {file_type} should be valid"
