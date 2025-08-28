"""
External Integrations Package

Contains integrations with external services like Google OAuth and Google Drive
for the GUARDIAN authentication and data persistence system.
"""

from .google import GoogleOAuthService, GoogleDriveService

__all__ = [
    'GoogleOAuthService',
    'GoogleDriveService'
]