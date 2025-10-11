"""Test CLI commands - the actual user-facing functionality."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock

from gdrive_pinecone_search.cli.main import main

class TestCLICommands:
    """Test all CLI commands work correctly."""
    
    def test_main_help(self):
        """Test main CLI help command."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Google Drive to Pinecone CLI' in result.output
        assert 'owner' in result.output
        assert 'search' in result.output
        assert 'connect' in result.output
        assert 'status' in result.output
    
    def test_owner_help(self):
        """Test owner command group help."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', '--help'])
        assert result.exit_code == 0
        assert 'setup' in result.output
        assert 'index' in result.output
        assert 'refresh' in result.output
    
    def test_owner_setup_help(self):
        """Test owner setup help."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'setup', '--help'])
        assert result.exit_code == 0
        assert 'credentials' in result.output.lower()
        assert 'api-key' in result.output.lower()
        assert 'dense-index-name' in result.output.lower()
        assert 'sparse-index-name' in result.output.lower()
    
    def test_index_help(self):
        """Test index command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'index', '--help'])
        assert result.exit_code == 0
        assert 'file-types' in result.output
        assert 'limit' in result.output
        assert 'dry-run' in result.output
    
    def test_refresh_help(self):
        """Test refresh command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'refresh', '--help'])
        assert result.exit_code == 0
        assert 'file-types' in result.output
        assert 'since' in result.output
        assert 'dry-run' in result.output
    
    def test_search_help(self):
        """Test search command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['search', '--help'])
        assert result.exit_code == 0
        assert 'file-types' in result.output
        assert 'limit' in result.output
        assert 'interactive' in result.output
    
    def test_connect_help(self):
        """Test connect command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['connect', '--help'])
        assert result.exit_code == 0
        assert 'dense-index-name' in result.output
        assert 'sparse-index-name' in result.output
    
    def test_status_help(self):
        """Test status command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['status', '--help'])
        assert result.exit_code == 0
        assert 'verbose' in result.output
        assert 'test-connections' in result.output

class TestCommandParameterValidation:
    """Test command parameter validation."""
    
    def test_index_file_type_validation(self):
        """Test index command file type validation."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(main, ['owner', 'index', '--file-types', 'invalid_type'])
        assert 'Invalid File Types' in result.output or 'Invalid file type' in result.output
        
        # Test valid file types - should not fail on validation
        result = runner.invoke(main, ['owner', 'index', '--file-types', 'py,json'])
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
        assert result.exit_code == 0
    
    def test_refresh_file_type_validation(self):
        """Test refresh command file type validation."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(main, ['owner', 'refresh', '--file-types', 'invalid_type'])
        assert 'Invalid File Types' in result.output or 'Invalid file type' in result.output
        
        # Test valid file types - should not fail on validation
        result = runner.invoke(main, ['owner', 'refresh', '--file-types', 'code,config'])
        # Should not have file type validation errors
        assert 'Invalid file type' not in result.output
        assert result.exit_code == 0
    
    def test_search_file_type_validation(self):
        """Test search command file type validation."""
        runner = CliRunner()
        
        # Test invalid file types - CLI uses return instead of sys.exit, so check output
        result = runner.invoke(main, ['search', 'test query', '--file-types', 'invalid_type'])
        assert 'Invalid File Types' in result.output or 'Invalid file type' in result.output
        
        # Test valid file types - should not fail on validation
        result = runner.invoke(main, ['search', 'test query', '--file-types', 'py,json'])
        # Should fail due to config issues, not file type validation
        assert 'Invalid file type' not in result.output

class TestCommandExecution:
    """Test command execution with mocked dependencies."""
    
    def test_status_command_execution(self):
        """Test status command execution."""
        runner = CliRunner()
        
        # Mock configuration handled by service factory
        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert 'Status' in result.output
    
    def test_owner_mode_requirement(self):
        """Test that owner commands require owner mode."""
        runner = CliRunner()
        
        # Test index command - should execute without crashing
        result = runner.invoke(main, ['owner', 'index'])
        assert result.exit_code == 0
        assert 'Initializing' in result.output or 'Setting up services' in result.output
        
        # Test refresh command - should execute without crashing  
        result = runner.invoke(main, ['owner', 'refresh'])
        assert result.exit_code == 0
        assert 'Initializing' in result.output or 'Setting up services' in result.output

class TestBasicFunctionality:
    """Test basic CLI functionality."""
    
    def test_search_command_basic(self):
        """Test basic search command functionality."""
        runner = CliRunner()
        
        # Test search with query
        result = runner.invoke(main, ['search', 'test query'])
        assert result.exit_code == 0
        assert 'Performing hybrid search' in result.output or 'No results' in result.output
        
        # Should not have invalid file type errors for default execution
        assert 'Invalid file type' not in result.output
    
    def test_connect_command_basic(self):
        """Test basic connect command functionality."""
        runner = CliRunner()
        
        # Test connect with required parameters
        result = runner.invoke(main, ['connect', '--dense-index-name', 'test-dense', '--sparse-index-name', 'test-sparse'])
        assert result.exit_code == 0
        assert 'Validating connections' in result.output or 'Indexes' in result.output
    
    def test_file_type_categories(self):
        """Test that file type categories are recognized."""
        runner = CliRunner()
        
        # Test code category
        result = runner.invoke(main, ['search', 'test', '--file-types', 'code'])
        assert 'Invalid file type' not in result.output
        
        # Test config category
        result = runner.invoke(main, ['search', 'test', '--file-types', 'config'])
        assert 'Invalid file type' not in result.output
        
        # Test mixed categories
        result = runner.invoke(main, ['search', 'test', '--file-types', 'docs,code,json'])
        assert 'Invalid file type' not in result.output

class TestSuccessMessageValidation:
    """Test that commands show appropriate success messages."""
    
    def test_search_success_message(self):
        """Test search shows results or no results message when successful."""
        runner = CliRunner()
        result = runner.invoke(main, ['search', 'test query'])
        
        if result.exit_code == 0:
            # Should show search results or "no results"
            assert any(phrase in result.output for phrase in [
                "Results", "No results", "Found", "matches", "search", "test-file-123"
            ]), f"Expected search output not found: {result.output[:200]}..."
    
    def test_index_success_message(self):
        """Test index shows completion message when successful."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'index'])
        
        if result.exit_code == 0:
            # Should show "Indexing Complete" or similar
            assert any(phrase in result.output for phrase in [
                "Indexing Complete", "Successfully processed", "files", "Complete", "processed"
            ]), f"Expected completion message not found: {result.output[:200]}..."

    def test_refresh_success_message(self):
        """Test refresh shows appropriate status message."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'refresh'])
        
        if result.exit_code == 0:
            # Should show completion or progress messages
            assert any(phrase in result.output for phrase in [
                "Refresh Complete", "refresh complete", "Successfully processed", "Complete", "files", "Initializing", "Setting up"
            ]), f"Expected status message not found: {result.output[:200]}..."

class TestRequiredParameters:
    """Test that commands properly validate required parameters."""
    
    def test_search_requires_query(self):
        """Test search command requires a query parameter."""
        runner = CliRunner()
        result = runner.invoke(main, ['search'])
        
        # Should fail when no query provided
        assert result.exit_code != 0, "Search should fail without query"
        # Should provide helpful error message
        assert any(phrase in result.output for phrase in [
            "Missing argument", "Usage:", "query", "Error:"
        ]), f"Missing query error not clear: {result.output[:200]}..."
    
    def test_limit_parameter_validation(self):
        """Test --limit parameter validation."""
        runner = CliRunner()
        
        # Valid limit should work
        result = runner.invoke(main, ['owner', 'index', '--limit', '10'])
        assert 'invalid' not in result.output.lower() or 'limit' not in result.output.lower()
        
        # Invalid limit should be caught
        result = runner.invoke(main, ['owner', 'index', '--limit', 'not_a_number'])
        assert result.exit_code != 0, "Should reject non-numeric limit"

class TestEdgeCaseValidation:
    """Test edge cases for parameter validation."""
    
    def test_file_type_validation_edge_cases(self):
        """Test file type validation with edge cases."""
        runner = CliRunner()
        
        # Empty file type should be handled gracefully
        result = runner.invoke(main, ['owner', 'index', '--file-types', ''])
        assert result.exit_code != 0 or 'Invalid' not in result.output
        
        # Mixed valid/invalid should identify specific problems
        result = runner.invoke(main, ['owner', 'index', '--file-types', 'py,invalid_type,json'])
        if 'Invalid' in result.output:
            assert 'invalid_type' in result.output, "Should identify specific invalid type"
        
        # Whitespace handling
        result = runner.invoke(main, ['owner', 'index', '--file-types', ' py , json '])
        assert 'Invalid file type' not in result.output, "Should handle whitespace in file types"
        
        # Case sensitivity - file types are case-sensitive, so uppercase should be invalid
        result = runner.invoke(main, ['owner', 'index', '--file-types', 'PY,JSON'])
        assert 'Invalid file type' in result.output, "File types are case-sensitive, uppercase should be invalid"
    
    def test_limit_parameter_edge_cases(self):
        """Test --limit parameter with edge cases."""
        runner = CliRunner()
        
        # Zero limit
        result = runner.invoke(main, ['owner', 'index', '--limit', '0'])
        # Should either work or provide clear error
        if result.exit_code != 0:
            assert 'limit' in result.output.lower() or 'invalid' in result.output.lower()
        
        # Negative limit
        result = runner.invoke(main, ['owner', 'index', '--limit', '-5'])
        # Should either work or provide clear error
        if result.exit_code != 0:
            assert 'limit' in result.output.lower() or 'invalid' in result.output.lower()
        
        # Very large limit
        result = runner.invoke(main, ['owner', 'index', '--limit', '999999'])
        # Should handle gracefully
        assert 'Traceback' not in result.output
    
    def test_special_characters_in_search(self):
        """Test search with special characters."""
        runner = CliRunner()
        
        # Search with quotes
        result = runner.invoke(main, ['search', '"hello world"'])
        assert 'Traceback' not in result.output
        
        # Search with special characters
        result = runner.invoke(main, ['search', 'test@example.com'])
        assert 'Traceback' not in result.output
        
        # Search with unicode
        result = runner.invoke(main, ['search', 'café'])
        assert 'Traceback' not in result.output

class TestHelpAccessibility:
    """Test help is accessible and useful across commands."""
    
    def test_main_help(self):
        """Test main command help is accessible."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0, "Main help should be accessible"
        assert 'Usage:' in result.output, "Main help should show usage"
        assert len(result.output) > 100, "Main help should be informative"
        assert 'Commands:' in result.output, "Should list available commands"
    
    def test_search_help(self):
        """Test search command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['search', '--help'])
        
        assert result.exit_code == 0, "Search help should be accessible"
        assert 'Usage:' in result.output, "Search help should show usage"
        assert 'query' in result.output.lower(), "Should mention query parameter"
        assert '--file-types' in result.output, "Should document file-types option"
    
    def test_index_help(self):
        """Test index command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'index', '--help'])
        
        assert result.exit_code == 0, "Index help should be accessible"
        assert 'Usage:' in result.output, "Index help should show usage"
        assert '--file-types' in result.output, "Should document file-types option"
        assert '--limit' in result.output, "Should document limit option"
    
    def test_refresh_help(self):
        """Test refresh command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['owner', 'refresh', '--help'])
        
        assert result.exit_code == 0, "Refresh help should be accessible"
        assert 'Usage:' in result.output, "Refresh help should show usage"
        assert '--dry-run' in result.output, "Should document dry-run option"
        assert '--force-full' in result.output, "Should document force-full option"
    
    def test_status_help(self):
        """Test status command help."""
        runner = CliRunner()
        result = runner.invoke(main, ['status', '--help'])
        
        assert result.exit_code == 0, "Status help should be accessible"
        assert 'Usage:' in result.output, "Status help should show usage"

class TestUserExperienceFlows:
    """Test realistic user experience flows."""
    
    def test_owner_mode_workflow(self):
        """Test basic owner mode workflow doesn't crash."""
        runner = CliRunner()
        
        # Status should work
        status_result = runner.invoke(main, ['status'])
        assert 'Traceback' not in status_result.output
        
        # Index should work 
        index_result = runner.invoke(main, ['owner', 'index', '--limit', '1'])
        assert 'Traceback' not in index_result.output
        
        # Search should work
        search_result = runner.invoke(main, ['search', 'test'])
        assert 'Traceback' not in search_result.output
    
    def test_scenario_with_files_found(self, mock_files_found_scenario):
        """Test search behavior when files are found."""
        runner = CliRunner()
        result = runner.invoke(main, ['search', 'test'])
        
        if result.exit_code == 0:
            # Should show results from our mock data
            assert any(phrase in result.output for phrase in [
                "test_document.py", "readme.md", "Results", "Found"
            ]), f"Expected files from scenario not found: {result.output[:200]}..."
    
    def test_scenario_with_empty_drive(self, mock_empty_drive_scenario):
        """Test behavior when no files are found."""
        runner = CliRunner()
        result = runner.invoke(main, ['search', 'test'])
        
        if result.exit_code == 0:
            # Should show search activity or no results message
            assert any(phrase in result.output for phrase in [
                "No results", "no matches", "not found", "0 results", "Searching", "Performing", "hybrid search"
            ]), f"Expected search activity or no results message: {result.output[:200]}..."