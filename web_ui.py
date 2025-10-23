#!/usr/bin/env python3
"""
web_ui.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""

Web UI for Reflexia LLM implementation
"""
import os
import logging
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_swagger_ui import get_swaggerui_blueprint
import requests

logger = logging.getLogger("reflexia-tools.web_ui")

class WebUI:
    """Web UI for Reflexia LLM implementation"""
    
    def __init__(self, config, model_manager, memory_manager, prompt_manager, rag_manager=None):
        """Initialize the Web UI
        
        Args:
            config: Configuration object
            model_manager: ModelManager instance
            memory_manager: MemoryManager instance
            prompt_manager: PromptManager instance
            rag_manager: RAGManager instance (optional)
        """
        self.config = config
        self.model_manager = model_manager
        self.memory_manager = memory_manager
        self.prompt_manager = prompt_manager
        self.rag_manager = rag_manager
        
        # Initialize metrics
        try:
            from utils import get_env_var
            enable_metrics = get_env_var("ENABLE_METRICS", "true").lower() in ("true", "1", "yes")
            self.metrics_enabled = enable_metrics
            
            if enable_metrics:
                metrics_port = int(get_env_var("METRICS_PORT", "9090"))
                import monitoring
                self.metrics = None  # Will be set after app is created
                monitoring.start_metrics_server(metrics_port)
                if self.memory_manager:
                    monitoring.track_memory_usage(self.memory_manager)
                if self.rag_manager:
                    monitoring.track_rag_document_count(self.rag_manager)
                logger.info(f"Metrics server started on port {metrics_port}")
        except ImportError:
            logger.warning("Monitoring module not available, metrics disabled")
            self.metrics_enabled = False
        
        # Import utility for environment variables
        from utils import get_env_var
        
        # Set host and port, prioritizing environment variables
        self.host = get_env_var("WEB_UI_HOST", 
                               self.config.get("web_ui", "host", default="127.0.0.1"))
        self.port = int(get_env_var("WEB_UI_PORT", 
                                    self.config.get("web_ui", "port", default=8000)))
        
        # Get security settings from environment
        from utils import get_env_var
        enable_auth = get_env_var("ENABLE_AUTH", "false").lower() in ("true", "1", "yes")
        api_key = get_env_var("API_KEY", "")
        
        # Create Flask app
        self.app = Flask(__name__, 
                     template_folder="web_ui/templates",
                     static_folder="web_ui/static")
                     
        # Setup prometheus metrics for Flask
        if self.metrics_enabled:
            import monitoring
            self.metrics = monitoring.instrument_flask_app(self.app)
        
        # Performance optimizations
        from flask_compress import Compress
        Compress(self.app)  # Enable gzip compression for responses
        
        # Add cache control headers for static files
        @self.app.after_request
        def add_cache_headers(response):
            # Cache static files for 7 days
            if request.path.startswith('/static/'):
                response.headers['Cache-Control'] = 'public, max-age=604800'
            # Set no-cache for API endpoints
            elif request.path.startswith('/api/'):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return response
        
        # Configure CORS
        enable_cors = get_env_var("ENABLE_CORS", "true").lower() in ("true", "1", "yes")
        cors_origins = "*" if enable_cors else []
        
        # Create SocketIO instance
        self.socketio = SocketIO(self.app, cors_allowed_origins=cors_origins)
        
        # Setup security if enabled
        self.enable_auth = enable_auth
        self.api_key = api_key
        
        # Setup routes
        self._setup_routes()
        
        # Setup Swagger UI for API documentation
        self._setup_swagger_ui()
        
        # Ensure Socket.IO JS is available
        self._ensure_socket_io_js()
        
        logger.info("Web UI initialized")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        # Setup API key authentication if enabled
        if self.enable_auth:
            from functools import wraps
            from flask import request, jsonify
            from utils import validate_api_key, rate_limit
            
            def require_api_key(f):
                @wraps(f)
                def decorated_function(*args, **kwargs):
                    # Get API key from header
                    api_key = request.headers.get('X-API-Key', '')
                    
                    # Validate API key
                    if not validate_api_key(api_key, self.api_key):
                        return jsonify({"error": "Unauthorized: Invalid API key"}), 401
                    
                    # Apply rate limiting based on API key
                    if not rate_limit(api_key, limit=60, period=60):
                        return jsonify({"error": "Too many requests"}), 429
                    
                    return f(*args, **kwargs)
                return decorated_function
            
            # Apply auth wrapper to API routes
            self._require_api_key = require_api_key
        
        @self.app.route("/")
        def index():
            return render_template("index.html")
            
        @self.app.route("/healthz")
        def health_check():
            """Health check endpoint for monitoring"""
            health = {
                "status": "ok",
                "timestamp": time.time(),
                "version": "1.0.0",
                "services": {
                    "model": self.model_manager is not None,
                    "memory": self.memory_manager is not None,
                    "rag": self.rag_manager is not None and getattr(self.rag_manager, "is_available", lambda: False)()
                }
            }
            return jsonify(health)
        
        # Apply authentication wrapper to API endpoints if enabled
        if self.enable_auth:
            get_documents = self._require_api_key(get_documents)
            delete_document = self._require_api_key(delete_document)
            upload_file = self._require_api_key(upload_file)
            
        # Define the API endpoints with optional authentication
        @self.app.route("/api/documents", methods=["GET"])
        def get_documents():
            # Apply rate limiting based on IP address regardless of auth setting
            if not rate_limit(request.remote_addr, limit=120, period=60):
                return jsonify({"error": "Too many requests"}), 429
                
            if self.rag_manager:
                docs = self.rag_manager.list_documents()
                return jsonify({"documents": docs})
            return jsonify({"documents": []})
        
        @self.app.route("/api/documents/<doc_id>", methods=["DELETE"])
        def delete_document(doc_id):
            if self.rag_manager:
                success = self.rag_manager.delete_document(doc_id)
                if success:
                    return jsonify({"success": True})
                return jsonify({"success": False, "error": "Document not found"})
            return jsonify({"success": False, "error": "RAG not available"})
        
        @self.app.route("/api/upload", methods=["POST"])
        def upload_file():
            # Apply rate limiting for file uploads (more strict)
            if not rate_limit(request.remote_addr, limit=10, period=60):
                return jsonify({"error": "Too many requests. File uploads are limited."}), 429
                
            if not self.rag_manager:
                return jsonify({"success": False, "error": "RAG not available"})
            
            if "file" not in request.files:
                return jsonify({"success": False, "error": "No file part"})
            
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"success": False, "error": "No selected file"})
            
            try:
                # Validate file type
                from utils import validate_file_type, sanitize_filename
                
                if not validate_file_type(file):
                    return jsonify({
                        "success": False, 
                        "error": "Invalid file type. Allowed types: .txt, .md, .pdf, .csv, .json, .docx, .xlsx"
                    }), 400
                
                # Sanitize filename
                safe_filename = sanitize_filename(file.filename)
                
                # Check file size (limit to 10MB)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)  # Reset file pointer
                
                if file_size > 10 * 1024 * 1024:  # 10MB
                    return jsonify({
                        "success": False, 
                        "error": "File too large. Maximum size is 10MB"
                    }), 400
                
                # Save file temporarily with sanitized name
                temp_dir = Path("temp")
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / safe_filename
                
                # Ensure we have a secure path
                if not str(temp_path).startswith(str(temp_dir.absolute())):
                    return jsonify({
                        "success": False, 
                        "error": "Invalid file path"
                    }), 400
                
                file.save(temp_path)
                
                # Load into RAG
                success = self.rag_manager.load_file(temp_path)
                
                # Clean up
                os.remove(temp_path)
                
                if success:
                    return jsonify({
                        "success": True, 
                        "filename": safe_filename
                    })
                else:
                    return jsonify({
                        "success": False, 
                        "error": "Failed to process file"
                    })
            except Exception as e:
                logger.error(f"Error uploading file: {e}")
                # Make sure we don't expose internal details in error messages
                return jsonify({
                    "success": False, 
                    "error": "An error occurred while processing the file"
                }), 500
        
        @self.socketio.on("connect")
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            # Track connection in metrics
            if self.metrics_enabled:
                import monitoring
                monitoring.track_connection(connected=True)
        
        @self.socketio.on("disconnect")
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")
            # Track disconnection in metrics
            if self.metrics_enabled:
                import monitoring
                monitoring.track_connection(connected=False)
        
        @self.socketio.on("get_initial_data")
        def handle_get_initial_data():
            # Send templates
            templates = self.prompt_manager.list_templates()
            emit("templates", {"templates": templates})
            
            # Send system prompt
            emit("system_prompt", {"prompt": self.prompt_manager.get_system_prompt()})
            
            # Send memory usage
            memory_stats = self.memory_manager.get_memory_stats()
            emit("memory_update", {
                "percent": memory_stats["percent"],
                "used_gb": memory_stats["used"] / (1024 * 1024 * 1024),
                "critical": memory_stats["critical"]
            })
            
            # Send documents if RAG is available
            if self.rag_manager:
                docs = self.rag_manager.list_documents()
                emit("documents", {"documents": docs})
        
        @self.socketio.on("user_message")
        def handle_message(data):
            # Process message in a background thread to not block
            import threading
            thread = threading.Thread(
                target=self._process_message,
                args=(data["message"], data.get("use_rag", False), 
                     data.get("template", "default"), 
                     data.get("temperature", 0.7), 
                     data.get("top_p", 0.9),
                     request.sid)
            )
            thread.daemon = True
            thread.start()
        
        @self.socketio.on("clear_chat")
        def handle_clear_chat():
            logger.info("Clearing chat history")
        
        @self.socketio.on("update_system_prompt")
        def handle_update_system_prompt(data):
            prompt = data.get("prompt", "")
            if prompt:
                self.prompt_manager.set_system_prompt(prompt)
                logger.info("System prompt updated")
                emit("system_prompt", {"prompt": prompt})
    
    def _process_message(self, message, use_rag, template, temperature, top_p, sid):
        """Process a user message in a background thread"""
        try:
            # Send typing indicator
            self.socketio.emit("status", {
                "status": "thinking",
                "message": "Generating response..."
            }, to=sid)
            
            # Format the prompt using the specified template
            formatted_prompt = self.prompt_manager.format_prompt(message, template_name=template)
            
            # Start time measurement
            start_time = time.time()
            
            # Memory stats before generation
            before_memory = self.memory_manager.get_memory_stats()
            
            # Generate response
            if use_rag and self.rag_manager:
                # Generate RAG response
                result = self.rag_manager.generate_rag_response(
                    message,
                    system_prompt=self.prompt_manager.get_system_prompt()
                )
                response = result["response"]
                sources = result.get("sources", [])
                
                # Send the response with sources
                self.socketio.emit("message", {
                    "message": response,
                    "sources": sources,
                    "processing_time": time.time() - start_time
                }, to=sid)
            else:
                # Generate standard response
                response = self.model_manager.generate_response(
                    formatted_prompt,
                    system_prompt=self.prompt_manager.get_system_prompt(),
                    temperature=temperature,
                    top_p=top_p
                )
                
                # Send the response
                self.socketio.emit("message", {
                    "message": response,
                    "processing_time": time.time() - start_time
                }, to=sid)
            
            # Memory stats after generation
            after_memory = self.memory_manager.get_memory_stats()
            memory_impact = after_memory["percent"] - before_memory["percent"]
            
            # Send detailed memory stats
            self.socketio.emit("memory_update", {
                "percent": after_memory["percent"],
                "used_gb": after_memory["used"] / (1024 * 1024 * 1024),
                "impact": memory_impact,
                "critical": after_memory["critical"]
            }, to=sid)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.socketio.emit("message", {
                "message": f"Error generating response: {str(e)}",
                "error": True
            }, to=sid)
    
    def _setup_swagger_ui(self):
        """Setup Swagger UI for API documentation"""
        try:
            # Define Swagger UI blueprint
            SWAGGER_URL = '/api/docs'
            API_URL = '/static/api/api_spec.yaml'
            
            # Create blueprint
            swagger_blueprint = get_swaggerui_blueprint(
                SWAGGER_URL,
                API_URL,
                config={
                    'app_name': "Reflexia API Documentation",
                    'deepLinking': True,
                    'displayOperationId': True,
                    'defaultModelsExpandDepth': 2,
                }
            )
            
            # Register blueprint with Flask app
            self.app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)
            
            # Add redirect from /docs to Swagger UI
            @self.app.route('/docs')
            def api_docs_redirect():
                return self.app.redirect(SWAGGER_URL)
                
            logger.info(f"Swagger UI initialized at {SWAGGER_URL}")
        except Exception as e:
            logger.error(f"Error setting up Swagger UI: {e}")
    
    def _ensure_socket_io_js(self):
        """Ensure Socket.IO JavaScript file is available"""
        socket_io_js_path = Path("web_ui/static/socket.io.js")
        if not socket_io_js_path.exists():
            os.makedirs(socket_io_js_path.parent, exist_ok=True)
            try:
                response = requests.get("https://cdn.socket.io/4.5.4/socket.io.min.js")
                with open(socket_io_js_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Downloaded socket.io.js to {socket_io_js_path}")
            except Exception as e:
                logger.error(f"Error downloading socket.io.js: {e}")
    
    def start(self, debug=False, threaded=False):
        """Start the web UI server
        
        Args:
            debug: Enable debug mode
            threaded: Run in a separate thread
            
        Returns:
            bool: Success status
        """
        # Set host and port
        self.host = self.config.get('web_ui', 'host', default='127.0.0.1')
        self.port = self.config.get('web_ui', 'port', default=8000)
        
        logger.info(f"Starting Web UI on {self.host}:{self.port}")
        print(f"Web UI started at http://{self.host}:{self.port}")
        print("Press Ctrl+C to stop")
        
        if threaded:
            import threading
            server_thread = threading.Thread(
                target=self.socketio.run,
                args=(self.app,),
                kwargs={'host': self.host, 'port': self.port, 'debug': debug, 'allow_unsafe_werkzeug': True}
            )
            server_thread.daemon = True
            server_thread.start()
            return True
        else:
            try:
                self.socketio.run(self.app, host=self.host, port=self.port, debug=debug, allow_unsafe_werkzeug=True)
                return True
            except Exception as e:
                logger.error(f"Error starting Web UI: {e}")
                return False
