"""
Google OAuth Service

Handles Google OAuth 2.0 authentication flow for the GUARDIAN system.
Manages user authentication, token refresh, and Google API scopes.
"""

import secrets
import hashlib
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...utils import logger
from ...config.settings import settings

class GoogleOAuthService:
    """
    Google OAuth 2.0 authentication service.
    
    Manages the complete OAuth flow from authorization URL generation
    to token exchange and refresh for Google Drive API access.
    
    Scopes:
        - openid: OpenID Connect for user identification
        - email: User's email address
        - profile: User's basic profile information
        - drive.file: Access to files created by the application
        - drive.appdata: Access to application data folder
    """
    
    SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.appdata'
    ]
    
    def __init__(self):
        """Initialize the OAuth service with configuration."""
        self.client_id = settings.auth.google_client_id
        self.client_secret = settings.auth.google_client_secret
        self.redirect_uri = settings.auth.google_redirect_uri
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError(
                "Google OAuth credentials not configured. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )
        
        logger.info(
            "Google OAuth service initialized",
            client_id=self.client_id[:12] + "...",  # Log partial client ID for debugging
            redirect_uri=self.redirect_uri,
            scopes=len(self.SCOPES)
        )
    
    def _create_flow(self, state: str = None) -> Flow:
        """
        Create a Google OAuth flow instance.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Flow: Configured OAuth flow
        """
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=self.SCOPES,
            state=state
        )
        flow.redirect_uri = self.redirect_uri
        
        return flow
    
    def generate_auth_url(self) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL.
        
        Returns:
            Tuple[str, str]: (authorization_url, state_token)
        """
        try:
            # Generate state token for CSRF protection
            state = secrets.token_urlsafe(32)
            
            # Create OAuth flow
            flow = self._create_flow(state=state)
            
            # Generate authorization URL with additional parameters
            auth_url, _ = flow.authorization_url(
                access_type='offline',  # Request refresh token
                include_granted_scopes='true',  # Incremental authorization
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            logger.info(
                "Generated OAuth authorization URL",
                state_token=state[:8] + "...",  # Log partial state for debugging
                url_length=len(auth_url)
            )
            
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Failed to generate OAuth authorization URL: {str(e)}", exception=e)
            raise
    
    def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Google
            state: State token for verification
            
        Returns:
            Dict containing tokens and user info
            
        Raises:
            ValueError: If code exchange fails
        """
        try:
            # Create flow with state verification
            flow = self._create_flow(state=state)
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            # Get user info from Google
            user_info = self._get_user_info(credentials)
            
            result = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                'user_info': user_info
            }
            
            logger.info(
                "Successfully exchanged OAuth code for tokens",
                user_email=user_info.get('email'),
                has_refresh_token=bool(credentials.refresh_token),
                scopes_granted=len(credentials.scopes or [])
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to exchange authorization code: {str(e)}", exception=e)
            raise ValueError(f"Failed to exchange authorization code: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict containing new tokens
            
        Raises:
            ValueError: If token refresh fails
        """
        try:
            # Create credentials with refresh token
            credentials = Credentials(
                token=None,  # Will be refreshed
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.SCOPES
            )
            
            # Refresh the token
            request = Request()
            credentials.refresh(request)
            
            result = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or refresh_token,  # May not get new refresh token
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                'scopes': credentials.scopes
            }
            
            logger.info(
                "Successfully refreshed access token",
                has_new_refresh_token=bool(credentials.refresh_token and credentials.refresh_token != refresh_token)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}", exception=e)
            raise ValueError(f"Failed to refresh access token: {str(e)}")
    
    def _get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """
        Get user information from Google using the credentials.
        
        Args:
            credentials: Google OAuth credentials
            
        Returns:
            Dict containing user information
        """
        try:
            # Build the OAuth2 service
            service = build('oauth2', 'v2', credentials=credentials)
            
            # Get user info
            user_info = service.userinfo().get().execute()
            
            return {
                'google_id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'locale': user_info.get('locale'),
                'verified_email': user_info.get('verified_email', False)
            }
            
        except HttpError as e:
            logger.error(f"Failed to get user info from Google: {str(e)}", exception=e)
            raise ValueError(f"Failed to get user info: {str(e)}")
    
    def validate_credentials(self, access_token: str) -> bool:
        """
        Validate Google access token by making a test API call.
        
        Args:
            access_token: The access token to validate
            
        Returns:
            bool: True if token is valid
        """
        try:
            # Create credentials with just the access token
            credentials = Credentials(token=access_token)
            
            # Try to get user info (lightweight API call)
            service = build('oauth2', 'v2', credentials=credentials)
            service.userinfo().get().execute()
            
            return True
            
        except Exception as e:
            logger.debug(f"Token validation failed: {str(e)}")
            return False
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a Google OAuth token.
        
        Args:
            token: The token to revoke (access or refresh)
            
        Returns:
            bool: True if revocation successful
        """
        try:
            credentials = Credentials(token=token)
            request = Request()
            
            # Revoke the token
            credentials.revoke(request)
            
            logger.info("Successfully revoked Google OAuth token")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}", exception=e)
            return False
    
    def get_drive_service(self, access_token: str):
        """
        Create a Google Drive service instance.
        
        Args:
            access_token: Valid access token
            
        Returns:
            Google Drive service instance
        """
        credentials = Credentials(token=access_token)
        return build('drive', 'v3', credentials=credentials)