"""
API Routes Package

Contains all route blueprints for the GUARDIAN API endpoints.
Each module defines routes for a specific functional area.
"""

from .health import health_bp

# Import other blueprints as they are created
# from .analysis import analysis_bp
# from .upload import upload_bp
# from .search import search_bp
# from .reports import reports_bp

__all__ = [
    'health_bp',
    # 'analysis_bp',
    # 'upload_bp', 
    # 'search_bp',
    # 'reports_bp'
]