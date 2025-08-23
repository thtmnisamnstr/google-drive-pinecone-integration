"""Authentication service for Google Drive OAuth2."""

import os
import json
from typing import Optional
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..utils.exceptions import AuthenticationError


class AuthService:
    """Handles Google Drive OAuth2 authentication."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, credentials_path: str):
        """
        Initialize authentication service.
        
        Args:
            credentials_path: Path to Google Drive credentials JSON file
        """
        self.credentials_path = credentials_path
        self.token_path = Path(credentials_path).parent / 'token.json'
        self._service = None
    
    def authenticate(self) -> Credentials:
        """
        Authenticate with Google Drive API.
        
        Returns:
            Valid credentials object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            creds = None
            
            # Check if we have a valid token
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
            
            # If no valid credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise AuthenticationError(f"Credentials file not found: {self.credentials_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            return creds
            
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}")
    
    def get_service(self):
        """
        Get authenticated Google Drive service.
        
        Returns:
            Google Drive API service object
        """
        if not self._service:
            creds = self.authenticate()
            self._service = build('drive', 'v3', credentials=creds)
        
        return self._service
    
    def validate_credentials(self) -> bool:
        """
        Validate that credentials are working.
        
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        try:
            service = self.get_service()
            # Make a simple API call to test credentials
            about = service.about().get(fields="user").execute()
            return True
        except Exception as e:
            raise AuthenticationError(f"Invalid credentials: {e}")
    
    def get_user_info(self) -> dict:
        """
        Get information about the authenticated user.
        
        Returns:
            Dictionary with user information
        """
        try:
            service = self.get_service()
            about = service.about().get(fields="user").execute()
            return about.get('user', {})
        except Exception as e:
            raise AuthenticationError(f"Failed to get user info: {e}")
    
    def revoke_credentials(self):
        """Revoke stored credentials."""
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
                creds.revoke(Request())
            except Exception:
                pass
            
            # Remove token file
            self.token_path.unlink(missing_ok=True)
            self._service = None 