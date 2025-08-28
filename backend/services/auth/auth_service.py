"""
Authentication Service

High-level authentication service that integrates Google OAuth with 
user management and session handling for the GUARDIAN system.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ...models import User, UserSession
from ...integrations.google import GoogleOAuthService, GoogleDriveService
from ...utils import logger
from ...config.settings import settings
from ..session_vector_service import SessionVectorService

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class AuthService:
    """
    High-level authentication service.
    
    Orchestrates the complete authentication flow from OAuth initiation
    through user creation and session management.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the authentication service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.oauth_service = GoogleOAuthService()
        
        logger.info("Authentication service initialized")
    
    def initiate_oauth_flow(self) -> Dict[str, str]:
        """
        Initiate Google OAuth flow.
        
        Returns:
            Dict containing authorization URL and state token
        """
        try:
            auth_url, state = self.oauth_service.generate_auth_url()
            
            logger.info("OAuth flow initiated", state_token=state[:8] + "...")
            
            return {
                'authorization_url': auth_url,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate OAuth flow: {str(e)}", exception=e)
            raise AuthenticationError(f"Failed to initiate OAuth flow: {str(e)}")
    
    def handle_oauth_callback(self, code: str, state: str, 
                             ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Handle OAuth callback and create user session.
        
        Args:
            code: Authorization code from Google
            state: State token for verification
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dict containing session token and user info
        """
        try:
            # Exchange code for tokens
            token_data = self.oauth_service.exchange_code_for_tokens(code, state)
            user_info = token_data['user_info']
            
            # Create or update user
            user = self._create_or_update_user(user_info, token_data)
            
            # Create session
            session, session_token = self._create_user_session(
                user.id, ip_address, user_agent
            )
            
            # Update user's last login
            user.update_last_login()
            self.db.commit()
            
            logger.info(
                "OAuth callback handled successfully",
                user_id=str(user.id),
                user_email=user.email,
                session_id=str(session.id)
            )
            
            return {
                'session_token': session_token,
                'user': user.to_dict(),
                'session': session.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to handle OAuth callback: {str(e)}", exception=e)
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return user information.
        
        Args:
            session_token: The session token to validate
            
        Returns:
            Dict containing user and session info, or None if invalid
        """
        try:
            # Hash the token to find in database
            token_hash = UserSession.hash_session_token(session_token)
            
            # Find session in database
            session = self.db.query(UserSession).filter(
                UserSession.session_token_hash == token_hash
            ).first()
            
            if not session:
                logger.debug("Session not found")
                return None
            
            # Check if session is valid
            if not session.is_valid():
                logger.debug("Session expired", session_id=str(session.id))
                return None
            
            # Update last accessed time
            session.update_last_accessed()
            self.db.commit()
            
            # Get user
            user = session.user
            
            logger.debug(
                "Session validated successfully",
                user_id=str(user.id),
                session_id=str(session.id)
            )
            
            return {
                'user': user.to_dict(),
                'session': session.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate session: {str(e)}", exception=e)
            return None
    
    def logout_user(self, session_token: str) -> bool:
        """
        Logout a user by invalidating their session and cleaning up vector databases.
        
        Args:
            session_token: The session token to invalidate
            
        Returns:
            bool: True if logout successful
        """
        try:
            # Hash the token to find in database
            token_hash = UserSession.hash_session_token(session_token)
            
            # Find session
            session = self.db.query(UserSession).filter(
                UserSession.session_token_hash == token_hash
            ).first()
            
            if session:
                user_id = session.user_id
                session_id = str(session.id)
                
                # Clean up vector database sessions before deleting auth session
                try:
                    vector_service = SessionVectorService()
                    
                    # Get list of active VDB sessions for this user
                    active_sessions = vector_service.list_active_sessions()
                    user_sessions = [s for s in active_sessions if s['user_id'] == str(user_id)]
                    
                    # Clean up each VDB session
                    for vdb_session in user_sessions:
                        logger.info(f"Cleaning up VDB session {vdb_session['session_id']} for user {user_id} on logout")
                        vector_service.cleanup_session(str(user_id), vdb_session['session_id'])
                    
                except Exception as vdb_error:
                    logger.error(f"Failed to cleanup VDB sessions during logout: {str(vdb_error)}", exception=vdb_error)
                    # Continue with logout even if VDB cleanup fails
                
                # Delete the auth session
                self.db.delete(session)
                self.db.commit()
                
                logger.info(f"User logged out successfully with VDB cleanup", user_id=str(user_id))
                return True
            else:
                logger.debug("Session not found for logout")
                return False
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to logout user: {str(e)}", exception=e)
            return False
    
    def refresh_drive_token(self, user_id: str) -> bool:
        """
        Refresh Google Drive access token for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if refresh successful
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            refresh_token = user.get_drive_refresh_token()
            if not refresh_token:
                logger.warning(f"No refresh token for user {user_id}")
                return False
            
            # Refresh token
            token_data = self.oauth_service.refresh_access_token(refresh_token)
            
            # Update user tokens
            user.set_drive_access_token(token_data['access_token'])
            if token_data.get('refresh_token'):
                user.set_drive_refresh_token(token_data['refresh_token'])
            
            if token_data.get('expiry'):
                user.drive_token_expiry = datetime.fromisoformat(token_data['expiry'])
            
            self.db.commit()
            
            logger.info(f"Drive token refreshed for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to refresh Drive token: {str(e)}", exception=e)
            return False
    
    def get_drive_service(self, user_id: str) -> Optional[GoogleDriveService]:
        """
        Get Google Drive service for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            GoogleDriveService instance or None
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            access_token = user.get_drive_access_token()
            if not access_token:
                return None
            
            # Check if token needs refresh
            if not user.is_drive_token_valid():
                if not self.refresh_drive_token(user_id):
                    return None
                # Reload user to get updated token
                user = self.db.query(User).filter(User.id == user_id).first()
                access_token = user.get_drive_access_token()
            
            # Create credentials and Drive service
            from google.oauth2.credentials import Credentials
            credentials = Credentials(token=access_token)
            
            return GoogleDriveService(credentials)
            
        except Exception as e:
            logger.error(f"Failed to get Drive service: {str(e)}", exception=e)
            return None
    
    def _create_or_update_user(self, user_info: Dict[str, Any], 
                              token_data: Dict[str, Any]) -> User:
        """
        Create a new user or update existing user with OAuth data.
        
        Args:
            user_info: User information from Google
            token_data: Token data from OAuth exchange
            
        Returns:
            User: Created or updated user instance
        """
        try:
            # Check if user already exists
            user = self.db.query(User).filter(
                User.google_id == user_info['google_id']
            ).first()
            
            if user:
                # Update existing user
                user.email = user_info['email']
                user.name = user_info['name']
                user.picture_url = user_info.get('picture')
                
                # Update tokens
                if token_data.get('access_token'):
                    user.set_drive_access_token(token_data['access_token'])
                if token_data.get('refresh_token'):
                    user.set_drive_refresh_token(token_data['refresh_token'])
                if token_data.get('expiry'):
                    user.drive_token_expiry = datetime.fromisoformat(token_data['expiry'])
                
                logger.info(f"Updated existing user: {user.email}")
                
            else:
                # Create new user
                user = User(
                    google_id=user_info['google_id'],
                    email=user_info['email'],
                    name=user_info['name'],
                    picture_url=user_info.get('picture')
                )
                
                # Set tokens
                if token_data.get('access_token'):
                    user.set_drive_access_token(token_data['access_token'])
                if token_data.get('refresh_token'):
                    user.set_drive_refresh_token(token_data['refresh_token'])
                if token_data.get('expiry'):
                    user.drive_token_expiry = datetime.fromisoformat(token_data['expiry'])
                
                self.db.add(user)
                logger.info(f"Created new user: {user.email}")
            
            self.db.flush()  # Get the user ID
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            # Handle case where user might have been created in another request
            user = self.db.query(User).filter(
                User.google_id == user_info['google_id']
            ).first()
            if user:
                return user
            raise e
    
    def _create_user_session(self, user_id: str, ip_address: str = None, 
                           user_agent: str = None) -> Tuple[UserSession, str]:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Tuple of (UserSession, raw_session_token)
        """
        session, raw_token = UserSession.create_session(
            user_id=user_id,
            duration_hours=settings.auth.session_duration_hours,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(session)
        self.db.flush()
        
        return session, raw_token
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from the database.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            count = UserSession.cleanup_expired_sessions(self.db)
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}", exception=e)
            return 0
    
    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.expires_at > datetime.utcnow()
        ).all()
        
        return [session.to_dict() for session in sessions]