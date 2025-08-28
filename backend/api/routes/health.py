"""
Health Check Routes

Provides system health monitoring endpoints for the GUARDIAN API.
These endpoints help monitor system status, database connectivity,
and service dependencies.
"""

import logging
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import text

from ...models.base import db_config
from ...integrations.llm.client import LLMClient
from ...config.settings import settings

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/health')


@health_bp.route('/', methods=['GET'])
def basic_health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON response with basic system status
    """
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'GUARDIAN API',
            'version': '1.0.0',
            'environment': getattr(settings.api, 'debug', False) and 'development' or 'production'
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check including database and external service status.
    
    Returns:
        JSON response with comprehensive system health information
    """
    start_time = time.time()
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'GUARDIAN API',
        'version': '1.0.0',
        'checks': {},
        'response_time_ms': 0
    }
    
    # Check database connectivity
    try:
        with db_config.get_session() as session:
            result = session.execute(text('SELECT 1')).fetchone()
            if result and result[0] == 1:
                health_status['checks']['database'] = {
                    'status': 'healthy',
                    'message': 'Database connection successful',
                    'checked_at': datetime.utcnow().isoformat()
                }
            else:
                raise Exception("Database query returned unexpected result")
                
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}',
            'checked_at': datetime.utcnow().isoformat()
        }
    
    # Check LLM service (if configured)
    try:
        if hasattr(settings, 'llm') and settings.llm.api_url:
            llm_client = LLMClient()
            # Simple connectivity test - we don't need to make an actual inference
            health_status['checks']['llm_service'] = {
                'status': 'configured',
                'endpoint': settings.llm.api_url,
                'model': getattr(settings.llm, 'model_name', 'unknown'),
                'message': 'LLM service endpoint configured',
                'checked_at': datetime.utcnow().isoformat()
            }
        else:
            health_status['checks']['llm_service'] = {
                'status': 'not_configured',
                'message': 'LLM service not configured',
                'checked_at': datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['llm_service'] = {
            'status': 'unhealthy',
            'message': f'LLM service check failed: {str(e)}',
            'checked_at': datetime.utcnow().isoformat()
        }
    
    # Check embedding model availability
    try:
        from ...core.ml.embedding_model import EmbeddingModel
        embedding_model = EmbeddingModel()
        device = embedding_model.get_device()
        
        health_status['checks']['embedding_model'] = {
            'status': 'healthy',
            'model_name': embedding_model.model_name,
            'device': str(device),
            'message': 'Embedding model loaded successfully',
            'checked_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['embedding_model'] = {
            'status': 'unhealthy',
            'message': f'Embedding model check failed: {str(e)}',
            'checked_at': datetime.utcnow().isoformat()
        }
    
    # Check file system access
    try:
        import os
        from ...config.settings import settings
        
        # Check if storage directories exist and are writable
        storage_path = getattr(settings, 'storage_path', './storage')
        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            health_status['checks']['file_system'] = {
                'status': 'healthy',
                'storage_path': storage_path,
                'message': 'File system access healthy',
                'checked_at': datetime.utcnow().isoformat()
            }
        else:
            health_status['checks']['file_system'] = {
                'status': 'unhealthy',
                'storage_path': storage_path,
                'message': 'Storage directory not accessible',
                'checked_at': datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['file_system'] = {
            'status': 'unhealthy',
            'message': f'File system check failed: {str(e)}',
            'checked_at': datetime.utcnow().isoformat()
        }
    
    # Calculate response time
    end_time = time.time()
    health_status['response_time_ms'] = round((end_time - start_time) * 1000, 2)
    
    # Determine overall status
    unhealthy_checks = [
        check for check in health_status['checks'].values() 
        if check['status'] == 'unhealthy'
    ]
    
    if unhealthy_checks:
        health_status['status'] = 'unhealthy'
        status_code = 503
    elif health_status['status'] == 'degraded':
        status_code = 200  # Degraded but still functional
    else:
        status_code = 200
    
    return jsonify(health_status), status_code


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Kubernetes-style readiness probe.
    
    Returns:
        200 if service is ready to receive traffic, 503 otherwise
    """
    try:
        # Check critical dependencies for readiness
        with db_config.get_session() as session:
            session.execute(text('SELECT 1')).fetchone()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503


@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes-style liveness probe.
    
    Returns:
        200 if service is alive, 503 if it should be restarted
    """
    try:
        # Basic liveness check - just ensure the service can respond
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - getattr(health_bp, '_start_time', time.time())
        }), 200
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            'status': 'dead',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503


@health_bp.route('/metrics', methods=['GET'])
def metrics_endpoint():
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        JSON response with basic application metrics
    """
    try:
        import psutil
        import os
        
        # Get process info
        process = psutil.Process()
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'process': {
                'pid': os.getpid(),
                'memory_usage_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
            },
            'system': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                'memory_available_gb': round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2),
                'disk_usage_percent': psutil.disk_usage('/').percent
            }
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return jsonify({
            'error': 'Metrics collection failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Initialize start time for uptime calculation
health_bp._start_time = time.time()


@health_bp.errorhandler(Exception)
def handle_health_error(error):
    """Handle errors in health check endpoints."""
    logger.error(f"Health endpoint error: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Health check failed',
        'timestamp': datetime.utcnow().isoformat()
    }), 500