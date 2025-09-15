"""File type definitions and utilities for enhanced file support."""

from typing import Dict, Set, Optional, List
import os

# Google Workspace file types (existing)
GOOGLE_WORKSPACE_TYPES = {
    'application/vnd.google-apps.document': 'docs',
    'application/vnd.google-apps.spreadsheet': 'sheets', 
    'application/vnd.google-apps.presentation': 'slides'
}

# Plaintext file extensions mapping
PLAINTEXT_EXTENSIONS = {
    # Text files
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.rst': 'text/x-rst', 
    '.log': 'text/plain',
    
    # Configuration files
    '.json': 'application/json',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.toml': 'text/x-toml',
    '.ini': 'text/plain',
    '.cfg': 'text/plain',
    '.conf': 'text/plain',
    
    # Code files
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.java': 'text/x-java-source',
    '.cpp': 'text/x-c++src',
    '.c': 'text/x-csrc',
    '.h': 'text/x-chdr',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.rb': 'text/x-ruby',
    '.php': 'text/x-php',
    '.sh': 'text/x-shellscript',
    '.bash': 'text/x-shellscript',
    '.zsh': 'text/x-shellscript',
    '.ps1': 'text/x-powershell',
    '.bat': 'text/x-msdos-batch',
    '.cmd': 'text/x-msdos-batch',
    
    # Web files
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css', 
    '.xml': 'text/xml',
    
    # Documentation
    '.tex': 'text/x-tex',
    
    # Data files
    '.csv': 'text/csv',
    '.tsv': 'text/tab-separated-values',
    '.sql': 'text/x-sql'
}

# File type categories for CLI
FILE_TYPE_CATEGORIES = {
    'txt': ['txt', 'md', 'rst', 'log'],
    'config': ['json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf'],
    'code': ['py', 'js', 'ts', 'java', 'cpp', 'c', 'h', 'go', 'rs', 'rb', 'php', 'sh', 'bash', 'zsh', 'ps1', 'bat', 'cmd'],
    'web': ['html', 'htm', 'css', 'xml'],
    'data': ['csv', 'tsv', 'sql'],
    'document': ['tex']  # Renamed from 'docs' to avoid confusion with Google Docs
}

def get_file_type_from_extension(filename: str) -> Optional[str]:
    """Get file type from filename extension."""
    ext = os.path.splitext(filename.lower())[1]
    
    # Check plaintext extensions
    if ext in PLAINTEXT_EXTENSIONS:
        # Map extension to our file type - return the extension name without dot
        ext_name = ext[1:]  # Remove the dot
        return ext_name
    
    return None

def is_supported_file_type(filename: str, mime_type: str) -> bool:
    """Check if file type is supported."""
    # Check Google Workspace types
    if mime_type in GOOGLE_WORKSPACE_TYPES:
        return True
    
    # Check plaintext extensions
    ext = os.path.splitext(filename.lower())[1]
    return ext in PLAINTEXT_EXTENSIONS

def get_all_supported_extensions() -> Set[str]:
    """Get all supported file extensions."""
    return set(PLAINTEXT_EXTENSIONS.keys())

def expand_file_type_categories(file_types: List[str]) -> List[str]:
    """Expand file type categories to individual types."""
    expanded = []
    for file_type in file_types:
        if file_type in FILE_TYPE_CATEGORIES:
            expanded.extend(FILE_TYPE_CATEGORIES[file_type])
        else:
            expanded.append(file_type)
    return list(set(expanded))  # Remove duplicates

def get_all_valid_file_types() -> Set[str]:
    """Get all valid file types (individual types + Google Workspace types)."""
    all_types = set(['docs', 'sheets', 'slides'])
    for category_types in FILE_TYPE_CATEGORIES.values():
        all_types.update(category_types)
    return all_types

def validate_file_types(file_types_str: str) -> List[str]:
    """
    Validate and expand file type string.
    
    Args:
        file_types_str: Comma-separated string of file types/categories
        
    Returns:
        List of expanded individual file types
        
    Raises:
        ValueError: If invalid file type is provided
    """
    if not file_types_str:
        return []
    
    requested_types = [ft.strip() for ft in file_types_str.split(',')]
    all_valid_types = get_all_valid_file_types()
    all_valid_categories = set(FILE_TYPE_CATEGORIES.keys())
    
    for requested_type in requested_types:
        if requested_type not in all_valid_types and requested_type not in all_valid_categories:
            raise ValueError(
                f"Invalid file type: '{requested_type}'. "
                f"Valid types: {', '.join(sorted(all_valid_types))} "
                f"or categories: {', '.join(sorted(all_valid_categories))}"
            )
    
    return expand_file_type_categories(requested_types)
