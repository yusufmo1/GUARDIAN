"""
WSGI Entry Point

Production entry point for GUARDIAN backend application.
Used by WSGI servers like Gunicorn for deployment.

Usage:
    gunicorn --config gunicorn.conf.py backend.wsgi:app
"""
from .main import create_app

# Create application instance for WSGI server
app = create_app()

if __name__ == "__main__":
    app.run()