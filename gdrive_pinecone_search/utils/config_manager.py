"""Configuration management for the Google Drive to Pinecone CLI."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .exceptions import ConfigurationError


class ConnectionConfig(BaseModel):
    """Configuration for Pinecone connection."""
    pinecone_api_key: str
    index_name: str
    created_at: datetime = Field(default_factory=datetime.now)


class OwnerConfig(BaseModel):
    """Configuration for owner mode operations."""
    google_drive_credentials_path: str
    pinecone_api_key: str
    index_name: str
    last_refresh_time: Optional[datetime] = None
    total_files_indexed: int = 0


class Settings(BaseModel):
    """Application settings."""
    embedding_model: str = "multilingual-e5-large"
    chunk_size: int = 800
    chunk_overlap: int = 150


class AppConfig(BaseModel):
    """Main application configuration."""
    mode: str = "connected"  # "owner" or "connected"
    connection: Optional[ConnectionConfig] = None
    owner_config: Optional[OwnerConfig] = None
    settings: Settings = Field(default_factory=Settings)


class ConfigManager:
    """Manages application configuration and credentials."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "gdrive-pinecone-search"
        self.config_file = self.config_dir / "config.json"
        self.config: Optional[AppConfig] = None
        self._ensure_config_dir()
        self._load_config()
        self._apply_env_overrides()
    
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.config = AppConfig(**data)
            except (json.JSONDecodeError, ValueError) as e:
                raise ConfigurationError(f"Invalid configuration file: {e}")
        else:
            self.config = AppConfig()
            self._save_config()
    
    def _save_config(self):
        """Save configuration to file."""
        if self.config:
            with open(self.config_file, 'w') as f:
                json.dump(self.config.dict(), f, indent=2, default=str)

    def _apply_env_overrides(self):
        """Apply environment variable overrides to in-memory settings.
        This does not persist to disk; it only affects the current process.
        """
        if not self.config:
            return
        # Settings overrides
        env_embedding_model = os.getenv("EMBEDDING_MODEL")
        if env_embedding_model:
            self.config.settings.embedding_model = env_embedding_model
        env_chunk_size = os.getenv("CHUNK_SIZE")
        if env_chunk_size:
            try:
                self.config.settings.chunk_size = int(env_chunk_size)
            except ValueError:
                # Ignore invalid values; keep existing
                pass
        env_chunk_overlap = os.getenv("CHUNK_OVERLAP")
        if env_chunk_overlap:
            try:
                self.config.settings.chunk_overlap = int(env_chunk_overlap)
            except ValueError:
                pass
    
    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        return self.config
    
    def update_config(self, **kwargs):
        """Update configuration with new values."""
        if not self.config:
            self.config = AppConfig()
        
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._save_config()
    
    def set_connection_config(self, api_key: str, index_name: str):
        """Set Pinecone connection configuration."""
        self.config.connection = ConnectionConfig(
            pinecone_api_key=api_key,
            index_name=index_name
        )
        self._save_config()
    
    def set_owner_config(self, credentials_path: str, api_key: str, index_name: str):
        """Set owner mode configuration with both Google Drive and Pinecone credentials."""
        self.config.mode = "owner"
        self.config.owner_config = OwnerConfig(
            google_drive_credentials_path=credentials_path,
            pinecone_api_key=api_key,
            index_name=index_name
        )
        self._save_config()
    
    def update_last_refresh_time(self, timestamp: datetime):
        """Update the last refresh timestamp."""
        if self.config.owner_config:
            self.config.owner_config.last_refresh_time = timestamp
            self._save_config()
    
    def update_files_indexed_count(self, count: int):
        """Update the total files indexed count."""
        if self.config.owner_config:
            self.config.owner_config.total_files_indexed = count
            self._save_config()
    
    def get_pinecone_api_key(self) -> Optional[str]:
        """Get Pinecone API key from environment or config."""
        # Check environment variable first
        env_key = os.getenv("PINECONE_API_KEY")
        if env_key:
            return env_key
        
        # Check owner config (owner mode)
        if self.config and self.config.owner_config:
            return self.config.owner_config.pinecone_api_key
        
        # Fall back to connection config (connected mode)
        if self.config and self.config.connection:
            return self.config.connection.pinecone_api_key
        
        return None
    
    def get_google_credentials_path(self) -> Optional[str]:
        """Get Google Drive credentials path from environment or config."""
        # Check environment variable first
        env_path = os.getenv("GDRIVE_CREDENTIALS_JSON")
        if env_path:
            return env_path
        
        # Fall back to config
        if self.config and self.config.owner_config:
            return self.config.owner_config.google_drive_credentials_path
        
        return None
    
    def get_pinecone_index_name(self) -> Optional[str]:
        """Get Pinecone index name from environment or config."""
        # Check environment variable first
        env_index = os.getenv("PINECONE_INDEX_NAME")
        if env_index:
            return env_index
        
        # Check owner config (owner mode)
        if self.config and self.config.owner_config:
            return self.config.owner_config.index_name
        
        # Fall back to connection config (connected mode)
        if self.config and self.config.connection:
            return self.config.connection.index_name
        
        return None
    

    
    def is_owner_mode(self) -> bool:
        """Check if the application is in owner mode."""
        return self.config.mode == "owner" if self.config else False
    
    def has_pinecone_config(self) -> bool:
        """Check if Pinecone configuration is available."""
        return bool(self.get_pinecone_api_key())
    
    def has_google_config(self) -> bool:
        """Check if Google Drive configuration is available."""
        return bool(self.get_google_credentials_path())
    
    def validate_config(self) -> bool:
        """Validate the current configuration."""
        if not self.has_pinecone_config():
            raise ConfigurationError("Pinecone API key not configured")
        
        if self.is_owner_mode():
            if not self.has_google_config():
                raise ConfigurationError("Google Drive credentials not configured for owner mode")
            if not self.get_pinecone_index_name():
                raise ConfigurationError("Pinecone index name not configured for owner mode")
        
        return True 