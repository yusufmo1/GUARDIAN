"""
Gunicorn WSGI Configuration

Production-ready configuration for GUARDIAN backend deployment.
Optimized for pharmaceutical compliance analysis workloads with
proper resource management and performance tuning.

Usage:
    gunicorn --config gunicorn.conf.py backend.wsgi:app
"""
import multiprocessing
import os
from pathlib import Path

# =============================================================================
# Server socket
# =============================================================================
bind = os.getenv("GUARDIAN_BIND", "0.0.0.0:8000")
backlog = int(os.getenv("GUARDIAN_BACKLOG", "2048"))

# =============================================================================
# Worker processes
# =============================================================================
# Calculate optimal worker count based on CPU cores
# For CPU-intensive tasks (ML processing), use CPU count
# For I/O intensive tasks, use 2 * CPU count + 1
cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv("GUARDIAN_WORKERS", max(2, cpu_count)))

# Worker class - sync for CPU-intensive ML operations
worker_class = os.getenv("GUARDIAN_WORKER_CLASS", "sync")

# Threads per worker for I/O operations
threads = int(os.getenv("GUARDIAN_THREADS", "2"))

# Worker connections for async workers (if using async worker class)
worker_connections = int(os.getenv("GUARDIAN_WORKER_CONNECTIONS", "1000"))

# =============================================================================
# Worker lifecycle
# =============================================================================
# Maximum number of requests a worker will process before restarting
# Helps prevent memory leaks in ML models
max_requests = int(os.getenv("GUARDIAN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUARDIAN_MAX_REQUESTS_JITTER", "100"))

# Worker timeout settings
timeout = int(os.getenv("GUARDIAN_TIMEOUT", "120"))  # Longer for ML processing
keepalive = int(os.getenv("GUARDIAN_KEEPALIVE", "5"))

# Graceful timeout for worker shutdown
graceful_timeout = int(os.getenv("GUARDIAN_GRACEFUL_TIMEOUT", "60"))

# =============================================================================
# Security
# =============================================================================
# Limit request line size to prevent DoS attacks
limit_request_line = int(os.getenv("GUARDIAN_LIMIT_REQUEST_LINE", "8192"))

# Limit request header fields
limit_request_fields = int(os.getenv("GUARDIAN_LIMIT_REQUEST_FIELDS", "200"))

# Limit request header field size
limit_request_field_size = int(os.getenv("GUARDIAN_LIMIT_REQUEST_FIELD_SIZE", "16384"))

# =============================================================================
# Logging
# =============================================================================
# Application log directory
log_dir = Path(os.getenv("GUARDIAN_LOG_DIR", "./backend/logs"))
log_dir.mkdir(parents=True, exist_ok=True)

# Access log configuration
accesslog = str(log_dir / "gunicorn_access.log")
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s'
)

# Error log configuration
errorlog = str(log_dir / "gunicorn_error.log")
loglevel = os.getenv("GUARDIAN_LOG_LEVEL", "info").lower()

# Capture stdout/stderr to error log
capture_output = True

# =============================================================================
# Process naming
# =============================================================================
proc_name = "guardian_backend"

# =============================================================================
# Server mechanics
# =============================================================================
# Daemon mode (set to False for Docker containers)
daemon = os.getenv("GUARDIAN_DAEMON", "false").lower() == "true"

# PID file
pidfile = os.getenv("GUARDIAN_PIDFILE", "/tmp/guardian.pid")

# User/group to run as (for security)
user = os.getenv("GUARDIAN_USER")
group = os.getenv("GUARDIAN_GROUP")

# Working directory
chdir = os.getenv("GUARDIAN_CHDIR", "./")

# =============================================================================
# SSL (if certificates are provided)
# =============================================================================
keyfile = os.getenv("GUARDIAN_SSL_KEYFILE")
certfile = os.getenv("GUARDIAN_SSL_CERTFILE")
ssl_version = int(os.getenv("GUARDIAN_SSL_VERSION", "2"))  # TLS 1.2
ciphers = os.getenv("GUARDIAN_SSL_CIPHERS", "HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA")

# =============================================================================
# Application configuration
# =============================================================================
# Raw environment variables to pass to workers
raw_env = [
    f"FLASK_ENV={os.getenv('FLASK_ENV', 'production')}",
    f"GUARDIAN_CONFIG={os.getenv('GUARDIAN_CONFIG', 'production')}",
]

# =============================================================================
# Performance tuning
# =============================================================================
# Enable sendfile for static files (if serving static files directly)
sendfile = os.getenv("GUARDIAN_SENDFILE", "true").lower() == "true"

# Enable reuse_port for better load distribution (Linux 3.9+)
reuse_port = os.getenv("GUARDIAN_REUSE_PORT", "true").lower() == "true"

# Preload application to save memory
preload_app = os.getenv("GUARDIAN_PRELOAD", "true").lower() == "true"

# =============================================================================
# Hooks for custom behavior
# =============================================================================

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("GUARDIAN backend starting up...")
    server.log.info(f"Configuration: {workers} workers, {threads} threads per worker")
    server.log.info(f"Binding to: {bind}")
    server.log.info(f"Worker timeout: {timeout}s")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("GUARDIAN backend reloading...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("GUARDIAN backend ready to serve requests")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker {worker.pid} received interrupt signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.debug(f"Forking worker {worker.age}")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.debug(f"Worker {worker.pid} spawned")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info(f"Worker {worker.pid} initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.warning(f"Worker {worker.pid} aborted")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked new master process")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    # Log ML-intensive requests for monitoring
    if any(path in req.path for path in ['/api/analyze', '/api/reports/generate']):
        worker.log.debug(f"Processing ML request: {req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Log completion of ML-intensive requests
    if any(path in req.path for path in ['/api/analyze', '/api/reports/generate']):
        worker.log.debug(f"Completed ML request: {req.method} {req.path} -> {resp.status}")

def child_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info(f"Worker {worker.pid} exited")

def worker_exit(server, worker):
    """Called just after a worker has been reaped."""
    server.log.info(f"Worker {worker.pid} shutdown")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    server.log.info(f"Worker count changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("GUARDIAN backend shutting down...")

# =============================================================================
# Development vs Production overrides
# =============================================================================
if os.getenv("FLASK_ENV") == "development":
    # Development-specific settings
    reload = True
    reload_extra_files = ["backend/config/settings.py"]
    timeout = 60  # Shorter timeout for development
    loglevel = "debug"
    workers = 1  # Single worker for easier debugging
    preload_app = False  # Disable preload for faster reloads
    
    # Override production security settings for development
    user = None
    group = None
    
    # Development logging
    accesslog = "-"  # Log to stdout
    errorlog = "-"   # Log to stderr

# =============================================================================
# Environment-specific configurations
# =============================================================================

# Docker-specific settings
if os.getenv("GUARDIAN_DOCKER", "false").lower() == "true":
    daemon = False  # Never run as daemon in Docker
    pidfile = None  # Don't create PID file in Docker
    
# Kubernetes-specific settings  
if os.getenv("GUARDIAN_K8S", "false").lower() == "true":
    bind = "0.0.0.0:8000"  # Always bind to all interfaces in K8s
    graceful_timeout = 30   # Shorter graceful timeout for K8s rolling updates
    preload_app = True      # Enable preload for faster startup

# High-performance settings for large-scale deployment
if os.getenv("GUARDIAN_SCALE", "standard") == "high":
    workers = cpu_count * 2  # More workers for high-scale
    max_requests = 2000      # Higher request limit
    worker_connections = 2000 # More connections
    backlog = 4096           # Larger backlog

print(f"Gunicorn configuration loaded:")
print(f"  Workers: {workers}")
print(f"  Threads per worker: {threads}")
print(f"  Timeout: {timeout}s")
print(f"  Bind: {bind}")
print(f"  Log level: {loglevel}")
print(f"  Environment: {os.getenv('FLASK_ENV', 'production')}")