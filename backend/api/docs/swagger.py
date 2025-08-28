"""
Swagger UI Integration

Provides Swagger UI interface for interactive API documentation.
Serves the OpenAPI specification with a user-friendly web interface.
"""
import os
import yaml
from flask import Blueprint, render_template_string, jsonify, current_app
from pathlib import Path

# Create docs blueprint
docs_bp = Blueprint('docs', __name__, url_prefix='/docs')

def load_openapi_spec():
    """
    Load OpenAPI specification from YAML file.
    
    Returns:
        dict: OpenAPI specification
    """
    try:
        # Path to OpenAPI spec file
        spec_path = Path(__file__).parent.parent.parent.parent / "openapi.yaml"
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        current_app.logger.error(f"Failed to load OpenAPI spec: {str(e)}")
        return {}

@docs_bp.route('/')
def swagger_ui():
    """
    Serve Swagger UI interface.
    
    Returns:
        str: HTML page with Swagger UI
    """
    swagger_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GUARDIAN API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@4.15.5/favicon-32x32.png" sizes="32x32" />
        <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@4.15.5/favicon-16x16.png" sizes="16x16" />
        <style>
            html {
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }
            *, *:before, *:after {
                box-sizing: inherit;
            }
            body {
                margin:0;
                background: #fafafa;
            }
            .swagger-ui .topbar {
                background-color: #003f5c;
            }
            .swagger-ui .topbar .download-url-wrapper .download-url-button {
                background-color: #d62728;
                border-color: #d62728;
            }
            .swagger-ui .info .title {
                color: #003f5c;
            }
            .swagger-ui .scheme-container {
                background-color: #fff;
                border: 1px solid #d3d3d3;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
            }
            /* Custom header styling */
            .api-header {
                background: linear-gradient(135deg, #003f5c 0%, #2c5a7a 100%);
                color: white;
                padding: 20px;
                text-align: center;
                margin-bottom: 20px;
            }
            .api-header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .api-header p {
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }
            .api-status {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="api-header">
            <h1>GUARDIAN API Documentation 
                <span class="api-status">v1.0.0</span>
            </h1>
            <p>Pharmaceutical Compliance Analysis API</p>
        </div>
        
        <div id="swagger-ui"></div>
        
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                // Initialize Swagger UI
                const ui = SwaggerUIBundle({
                    url: '/docs/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    validatorUrl: "https://online.swagger.io/validator",
                    docExpansion: "list",
                    defaultModelExpandDepth: 3,
                    defaultModelsExpandDepth: 3,
                    displayRequestDuration: true,
                    filter: true,
                    showExtensions: true,
                    showCommonExtensions: true,
                    tryItOutEnabled: true,
                    requestInterceptor: function(request) {
                        // Add any custom headers or authentication here
                        console.log('API Request:', request);
                        return request;
                    },
                    responseInterceptor: function(response) {
                        // Log API responses for debugging
                        console.log('API Response:', response);
                        return response;
                    },
                    onComplete: function() {
                        console.log('Swagger UI loaded successfully');
                    },
                    onFailure: function(error) {
                        console.error('Swagger UI failed to load:', error);
                    }
                });
                
                // Store UI instance globally for debugging
                window.ui = ui;
            };
        </script>
    </body>
    </html>
    """
    return swagger_html

@docs_bp.route('/openapi.json')
def openapi_spec():
    """
    Serve OpenAPI specification as JSON.
    
    Returns:
        dict: OpenAPI specification in JSON format
    """
    spec = load_openapi_spec()
    
    # Update server URLs based on current request
    if spec and 'servers' in spec:
        # Get the current server URL
        from flask import request
        base_url = request.url_root.rstrip('/')
        
        # Update the development server URL
        spec['servers'] = [
            {'url': base_url, 'description': 'Current server'},
            {'url': 'http://localhost:8000', 'description': 'Development server'},
            {'url': 'https://api.guardian.qmul.ac.uk', 'description': 'Production server'}
        ]
    
    return jsonify(spec)

@docs_bp.route('/redoc')
def redoc_ui():
    """
    Serve ReDoc UI interface as an alternative to Swagger UI.
    
    Returns:
        str: HTML page with ReDoc UI
    """
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GUARDIAN API Documentation - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
            .api-header {
                background: linear-gradient(135deg, #003f5c 0%, #2c5a7a 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .api-header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
                font-family: 'Montserrat', sans-serif;
            }
            .api-header p {
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }
            .api-status {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="api-header">
            <h1>GUARDIAN API Documentation 
                <span class="api-status">v1.0.0</span>
            </h1>
            <p>Pharmaceutical Compliance Analysis API - ReDoc Interface</p>
        </div>
        
        <redoc spec-url='/docs/openapi.json'></redoc>
        
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return redoc_html

@docs_bp.route('/postman')
def postman_collection():
    """
    Generate Postman collection from OpenAPI spec.
    
    Returns:
        dict: Postman collection JSON
    """
    spec = load_openapi_spec()
    
    if not spec:
        return jsonify({'error': 'Unable to load OpenAPI specification'}), 500
    
    # Basic Postman collection structure
    collection = {
        "info": {
            "name": "GUARDIAN API",
            "description": spec.get('info', {}).get('description', ''),
            "version": spec.get('info', {}).get('version', '1.0.0'),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:8000",
                "type": "string"
            }
        ]
    }
    
    # Convert OpenAPI paths to Postman requests
    paths = spec.get('paths', {})
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                request_item = {
                    "name": operation.get('summary', f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "url": {
                            "raw": "{{baseUrl}}" + path,
                            "host": ["{{baseUrl}}"],
                            "path": path.strip('/').split('/')
                        }
                    }
                }
                
                # Add request body for POST/PUT requests
                if method.lower() in ['post', 'put', 'patch']:
                    request_body = operation.get('requestBody', {})
                    if request_body:
                        content = request_body.get('content', {})
                        if 'application/json' in content:
                            schema = content['application/json'].get('schema', {})
                            example = content['application/json'].get('example', {})
                            
                            request_item["request"]["body"] = {
                                "mode": "raw",
                                "raw": str(example) if example else "{}",
                                "options": {
                                    "raw": {
                                        "language": "json"
                                    }
                                }
                            }
                
                collection["item"].append(request_item)
    
    return jsonify(collection)

@docs_bp.route('/health')
def docs_health():
    """
    Health check for documentation service.
    
    Returns:
        dict: Health status
    """
    spec = load_openapi_spec()
    
    return jsonify({
        'status': 'healthy' if spec else 'degraded',
        'openapi_spec_loaded': bool(spec),
        'endpoints_documented': len(spec.get('paths', {})) if spec else 0,
        'version': spec.get('info', {}).get('version', 'unknown') if spec else 'unknown'
    })

# Register additional routes for API exploration
@docs_bp.route('/endpoints')
def list_endpoints():
    """
    List all documented API endpoints.
    
    Returns:
        dict: List of endpoints with methods and descriptions
    """
    spec = load_openapi_spec()
    
    if not spec:
        return jsonify({'error': 'Unable to load OpenAPI specification'}), 500
    
    endpoints = []
    paths = spec.get('paths', {})
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                endpoints.append({
                    'path': path,
                    'method': method.upper(),
                    'summary': operation.get('summary', ''),
                    'description': operation.get('description', ''),
                    'tags': operation.get('tags', []),
                    'operationId': operation.get('operationId', '')
                })
    
    return jsonify({
        'endpoints': endpoints,
        'total_count': len(endpoints),
        'by_tag': _group_endpoints_by_tag(endpoints)
    })

def _group_endpoints_by_tag(endpoints):
    """
    Group endpoints by their tags.
    
    Args:
        endpoints: List of endpoint information
        
    Returns:
        dict: Endpoints grouped by tag
    """
    by_tag = {}
    
    for endpoint in endpoints:
        tags = endpoint.get('tags', ['Untagged'])
        for tag in tags:
            if tag not in by_tag:
                by_tag[tag] = []
            by_tag[tag].append(endpoint)
    
    return by_tag