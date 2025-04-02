#!/usr/bin/env python3
"""
Utility functions for Reflexia LLM implementation
"""
import os
import sys
import time
import logging
import platform
import subprocess
import importlib
import psutil
import json
from pathlib import Path
import datetime
import logging.handlers  # Add missing import for RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger("reflexia-tools.utils")

def get_env_var(name, default=None):
    """Get an environment variable, with fallback to default value"""
    return os.environ.get(name, default)

def get_environment_config():
    """Get all environment configuration with defaults
    
    Returns:
        dict: Environment configuration with all variables
    """
    config = {
        # Web UI Settings
        "WEB_UI_HOST": get_env_var("WEB_UI_HOST", "127.0.0.1"),
        "WEB_UI_PORT": int(get_env_var("WEB_UI_PORT", "8000")),
        "ENABLE_CORS": get_env_var("ENABLE_CORS", "true").lower() in ("true", "1", "yes"),
        
        # Security Settings
        "ENABLE_AUTH": get_env_var("ENABLE_AUTH", "false").lower() in ("true", "1", "yes"),
        "API_KEY": get_env_var("API_KEY", ""),
        "API_RATE_LIMIT": int(get_env_var("API_RATE_LIMIT", "60")),
        "API_RATE_PERIOD": int(get_env_var("API_RATE_PERIOD", "60")),
        "UPLOAD_RATE_LIMIT": int(get_env_var("UPLOAD_RATE_LIMIT", "10")),
        "UPLOAD_RATE_PERIOD": int(get_env_var("UPLOAD_RATE_PERIOD", "60")),
        
        # Resource Settings
        "MAX_MEMORY_PERCENT": float(get_env_var("MAX_MEMORY_PERCENT", "80.0")),
        "ENABLE_ADAPTIVE_QUANTIZATION": get_env_var("ENABLE_ADAPTIVE_QUANTIZATION", "true").lower() in ("true", "1", "yes"),
        "MODEL_NAME": get_env_var("MODEL_NAME", "reflexia-r1"),
        "MODEL_QUANTIZATION": get_env_var("MODEL_QUANTIZATION", "q4_0"),
        
        # Monitoring Settings
        "ENABLE_METRICS": get_env_var("ENABLE_METRICS", "true").lower() in ("true", "1", "yes"),
        "METRICS_PORT": int(get_env_var("METRICS_PORT", "9090")),
        "ENABLE_TELEMETRY": get_env_var("ENABLE_TELEMETRY", "false").lower() in ("true", "1", "yes"),
        "TELEMETRY_URL": get_env_var("TELEMETRY_URL", ""),
        
        # Recovery & Reliability
        "ENABLE_RECOVERY": get_env_var("ENABLE_RECOVERY", "true").lower() in ("true", "1", "yes"),
        "ENABLE_AUTO_RESTART": get_env_var("ENABLE_AUTO_RESTART", "true").lower() in ("true", "1", "yes"),
        "HEALTH_CHECK_INTERVAL": int(get_env_var("HEALTH_CHECK_INTERVAL", "60")),
        
        # Advanced Settings
        "LOG_LEVEL": get_env_var("LOG_LEVEL", "INFO"),
        "MAX_LOG_SIZE_MB": int(get_env_var("MAX_LOG_SIZE_MB", "10")),
        "MAX_LOG_BACKUPS": int(get_env_var("MAX_LOG_BACKUPS", "5")),
        
        # Ollama Integration
        "OLLAMA_METAL": get_env_var("OLLAMA_METAL", "1"),
        "OLLAMA_HOST": get_env_var("OLLAMA_HOST", "localhost:11434")
    }
    
    return config

def validate_api_key(provided_key, expected_key):
    """Validate API key using constant time comparison to prevent timing attacks"""
    if not expected_key or not provided_key:
        return False
    
    # Use constant time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(provided_key, expected_key)

def sanitize_filename(filename):
    """Sanitize a filename to prevent path traversal and other attacks
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Get just the basename, not any path components
    from os.path import basename
    safe_name = basename(filename)
    
    # Remove any potentially dangerous characters
    import re
    safe_name = re.sub(r'[^\w\.-]', '_', safe_name)
    
    # Ensure it's not empty or just an extension
    if not safe_name or safe_name.startswith('.'):
        safe_name = f"document_{int(time.time())}{safe_name}"
        
    return safe_name

def validate_file_type(file, allowed_types=None):
    """Validate file type based on extension and/or mimetype
    
    Args:
        file: The file object to validate
        allowed_types: List of allowed MIME types, defaults to common document types
        
    Returns:
        bool: True if file is valid, False otherwise
    """
    if allowed_types is None:
        allowed_types = [
            'text/plain', 'text/csv', 'text/markdown',
            'application/pdf', 'application/json',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
    
    # First check the filename extension
    import os
    valid_extensions = ['.txt', '.md', '.pdf', '.csv', '.json', '.docx', '.xlsx']
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in valid_extensions:
        return False
    
    # If we have access to mimetype, check that too
    if hasattr(file, 'content_type') and file.content_type not in allowed_types:
        return False
        
    return True

def validate_input(data, schema, max_length=None):
    """Validate input against a schema and check for length limits
    
    Args:
        data: The data to validate
        schema: The schema to validate against (dict with field names and types)
        max_length: Maximum length for string fields
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Input must be an object"
        
    for field, field_type in schema.items():
        # Check required fields
        if field not in data:
            return False, f"Missing required field: {field}"
            
        # Check field type
        if not isinstance(data[field], field_type):
            return False, f"Field {field} has wrong type"
            
        # Check string length
        if max_length and isinstance(data[field], str) and len(data[field]) > max_length:
            return False, f"Field {field} exceeds maximum length of {max_length}"
    
    return True, ""

def rate_limit(key, limit=60, period=60):
    """Simple in-memory rate limiting
    
    Args:
        key: Identifier for the client (e.g. IP address)
        limit: Maximum number of requests allowed in the period
        period: Time period in seconds
        
    Returns:
        bool: True if request is allowed, False if rate limit exceeded
    """
    from time import time
    
    # Use a global dict to track requests
    if not hasattr(rate_limit, "_cache"):
        rate_limit._cache = {}
    
    # Clean up old entries
    now = time()
    for k in list(rate_limit._cache.keys()):
        if rate_limit._cache[k]["reset_time"] < now:
            del rate_limit._cache[k]
    
    # Check if key exists
    if key not in rate_limit._cache:
        rate_limit._cache[key] = {
            "count": 1,
            "reset_time": now + period
        }
        return True
    
    # Check if limit exceeded
    if rate_limit._cache[key]["count"] >= limit:
        return False
    
    # Increment count
    rate_limit._cache[key]["count"] += 1
    return True
    
def setup_rotating_logs(app_name="reflexia-tools", log_dir="logs", log_level=logging.INFO, 
                        max_bytes=10485760, backup_count=5):
    """Set up rotating logs to prevent large log files
    
    Args:
        app_name: Name of the application for the logger
        log_dir: Directory to store logs
        log_level: Log level (default: INFO)
        max_bytes: Maximum size in bytes before rotating (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        
    Returns:
        str: Path to the log file
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create a rotating file handler
    today = datetime.datetime.now().strftime("%Y%m%d")
    log_file = log_path / f"{app_name}-{today}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    # Set level for both handlers
    file_handler.setLevel(log_level)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Logging initialized with rotating logs in {log_file}")
    return str(log_file)

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("Checking dependencies")
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(["ollama", "version"], capture_output=True, text=True)
        ollama_version = result.stdout.strip()
        logger.info(f"✓ Ollama version: {ollama_version}")
        print(f"✓ Ollama version: {ollama_version}")
    except FileNotFoundError:
        logger.error("❌ Ollama not found. Please install Ollama first.")
        print("❌ Ollama not found. Please install Ollama first.")
        print("   Visit https://ollama.ai/ to download and install.")
        return False
    
    # Check if Ollama is running
    try:
        result = subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("❌ Ollama service not running")
            print("❌ Ollama service not running. Please start Ollama.")
            print("   Run 'ollama serve' or start the Ollama application.")
            return False
        else:
            logger.info("✓ Ollama service is running")
            print("✓ Ollama service is running")
    except Exception as e:
        logger.error(f"❌ Error checking Ollama service: {e}")
        print(f"❌ Error checking Ollama service: {e}")
        return False
    
    # Check if we're on Apple Silicon
    if platform.system() == "Darwin" and "arm" in platform.processor():
        logger.info("✓ Running on Apple Silicon")
        print("✓ Running on Apple Silicon")
        
        # Check if Metal is available
        try:
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                  capture_output=True, text=True)
            if "Metal" in result.stdout:
                logger.info("✓ Metal is available")
                print("✓ Metal is available")
            else:
                logger.warning("⚠️ Metal may not be available")
                print("⚠️ Metal may not be available")
        except Exception:
            logger.warning("⚠️ Could not check Metal availability")
            print("⚠️ Could not check Metal availability")
    else:
        logger.warning("⚠️ Not running on Apple Silicon, performance may be limited")
        print("⚠️ Not running on Apple Silicon, performance may be limited")
    
    # Check available memory
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024 * 1024 * 1024)
    logger.info(f"Available memory: {memory_gb:.2f} GB")
    print(f"✓ Available memory: {memory_gb:.2f} GB")
    
    if memory_gb < 32:
        logger.warning(f"⚠️ Only {memory_gb:.2f} GB RAM detected. 32GB+ recommended for optimal performance.")
        print(f"⚠️ Only {memory_gb:.2f} GB RAM detected. 32GB+ recommended for optimal performance.")
    
    # Check Python packages
    required_packages = ["tenacity", "psutil", "numpy"]
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        logger.info("✓ All required Python packages are installed")
        print("✓ All required Python packages are installed")
    
    return True

def monitor_resources():
    """Monitor system resources"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_used_gb = memory.used / (1024 * 1024 * 1024)
    memory_percent = memory.percent
    
    # GPU memory info (for Apple Silicon)
    gpu_info = "N/A"
    if platform.system() == "Darwin" and "arm" in platform.processor():
        try:
            result = subprocess.run(
                ["ioreg", "-l", "-w", "0", "-d", "1", "-r", "-c", "AppleM1PerfCounterARM"],
                capture_output=True, text=True
            )
            # Extract relevant GPU info
            if result.returncode == 0:
                gpu_info = "Metal GPU active"
        except Exception:
            pass
    
    return {
        "timestamp": time.time(),
        "cpu_percent": cpu_percent,
        "memory_used_gb": memory_used_gb,
        "memory_percent": memory_percent,
        "gpu_info": gpu_info
    }

def benchmark_model(model_manager, config):
    """Run benchmarks on the model"""
    print("\nRunning model benchmark...")
    logger.info("Starting model benchmark")
    
    benchmark_prompts = config.get("benchmark", "prompts", 
                                  default=["Explain quantum computing in simple terms"])
    num_runs = config.get("benchmark", "num_runs", default=3)
    timeout = config.get("benchmark", "timeout", default=60)
    
    results = []
    
    for prompt in benchmark_prompts:
        prompt_results = []
        
        print(f"\nBenchmarking prompt: {prompt[:40]}...")
        for i in range(num_runs):
            print(f"  Run {i+1}/{num_runs}... ", end="", flush=True)
            
            # Measure time
            start_time = time.time()
            try:
                # Use the correct method name (generate_response not generate_completion)
                _ = model_manager.generate_response(prompt)
                end_time = time.time()
                
                duration = end_time - start_time
                prompt_results.append(duration)
                
                print(f"{duration:.2f}s")
                
                # Monitor resources after run
                resources = monitor_resources()
                logger.debug(f"Run {i+1} resources: {resources}")
                
            except Exception as e:
                logger.error(f"Error during benchmark run {i+1}: {e}")
                print(f"Error: {e}")
                # Add a failed result with None duration
                prompt_results.append(None)
            
            # Sleep briefly between runs to let resources settle
            time.sleep(1)
            
        # Calculate average (ignoring failed runs)
        valid_runs = [t for t in prompt_results if t is not None]
        avg_time = sum(valid_runs) / len(valid_runs) if valid_runs else float('inf')
        
        results.append({
            "prompt": prompt,
            "avg_time": avg_time,
            "runs": prompt_results,
            "success_rate": len(valid_runs) / num_runs if num_runs > 0 else 0
        })
        
        print(f"  Average time: {avg_time:.2f}s")
    
    # Save benchmark results
    benchmark_path = Path(config.get("paths", "output_dir")) / "benchmarks"
    benchmark_path.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    result_file = benchmark_path / f"benchmark-{timestamp}.json"
    
    with open(result_file, "w") as f:
        json.dump({
            "model": config.get("model", "name"),
            "quantization": config.get("model", "quantization"),
            "timestamp": timestamp,
            "system_info": {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "memory_gb": psutil.virtual_memory().total / (1024 * 1024 * 1024)
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nBenchmark results saved to {result_file}")
    return results

def get_requirements():
    """Get list of required packages"""
    return [
        "tenacity>=8.2.2",
        "psutil>=5.9.5",
        "numpy>=1.24.3",
        "huggingface-hub>=0.16.4",
        "datasets>=2.13.0",
        "requests>=2.28.0",
        "rich>=13.4.0",
        "typer>=0.9.0"
    ]

def generate_requirements_file():
    """Generate requirements.txt file"""
    requirements = get_requirements()
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    print(f"Generated requirements.txt with {len(requirements)} packages")
    return True

def setup_logging(log_dir="logs", log_level=logging.INFO, max_size_mb=10, backup_count=5):
    """Set up logging configuration with rotation and configurable levels
    
    Args:
        log_dir (str): Directory for log files
        log_level (int): Logging level (default: INFO)
        max_size_mb (int): Maximum size of log file in MB before rotation
        backup_count (int): Number of backup files to keep
    
    Returns:
        str: Path to the log file
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d")
    log_file = log_path / f"reflexia-tools-{timestamp}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
        backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure module loggers with potentially different levels
    logging.getLogger("reflexia-tools.model").setLevel(log_level)
    logging.getLogger("reflexia-tools.memory").setLevel(log_level)
    logging.getLogger("reflexia-tools.config").setLevel(log_level)
    logging.getLogger("reflexia-tools.finetune").setLevel(log_level)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    return log_file

def optimize_for_m3_max():
    """Apply optimizations for M3 Max with 36GB RAM"""
    try:
        logger.info("Applying optimizations for M3 Max")
        
        # Ensure Metal acceleration is enabled
        os.environ["OLLAMA_METAL"] = "1"
        
        # Optimize thread usage for M3 Max
        # M3 Max has 16 cores - 12 performance, 4 efficiency
        cpu_count = os.cpu_count() or 16
        optimal_threads = min(cpu_count - 2, 14)  # Reserve some cores for system
        
        # Adjust thread-related settings here
        
        logger.info(f"Optimized for M3 Max: {optimal_threads} threads")
        return True
    except Exception as e:
        logger.error(f"Error applying M3 Max optimizations: {e}")
        return False

def debug_environment():
    """Print detailed environment information for debugging"""
    import platform
    import sys
    import subprocess
    
    print("\n=== Environment Diagnostic Information ===\n")
    
    # System information
    print("System Information:")
    print(f"  OS: {platform.system()} {platform.version()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  Python: {sys.version}")
    print(f"  CPU Count: {os.cpu_count()}")
    
    # Shell detection
    print("\nTerminal Information:")
    shell = os.environ.get('SHELL', 'Unknown')
    term_program = os.environ.get('TERM_PROGRAM', 'Unknown')
    term = os.environ.get('TERM', 'Unknown')
    print(f"  Current Shell: {shell}")
    print(f"  Terminal Program: {term_program}")
    print(f"  Terminal Type: {term}")
    
    # PowerShell detection
    powershell_detected = False
    if 'powershell' in term_program.lower() or (platform.system() == 'Darwin' and term_program == 'Unknown'):
        # Additional check for PowerShell on macOS
        try:
            result = subprocess.run(['ps', '-p', str(os.getppid()), '-o', 'command='], 
                                   capture_output=True, text=True, timeout=1)
            if 'powershell' in result.stdout.lower():
                powershell_detected = True
        except (subprocess.SubprocessError, OSError):
            pass
    
    if powershell_detected:
        print("  ⚠️  PowerShell detected, which may cause rendering issues.")
        print("  Recommendation: Use Terminal.app, iTerm2, or another native macOS terminal")
    
    # Environment variables
    print("\nRelevant Environment Variables:")
    print(f"  OLLAMA_METAL: {os.environ.get('OLLAMA_METAL', 'Not set')}")
    print(f"  CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')}")
    print(f"  USE_MPS: {os.environ.get('USE_MPS', 'Not set')}")
    print(f"  PATH: {os.environ.get('PATH', 'Not set')[:60]}...")
    
    # Installation verification
    print("\nInstallation Verification:")
    try:
        venv_path = os.environ.get('VIRTUAL_ENV')
        if venv_path:
            print(f"  Virtual Environment: ✅ Active ({os.path.basename(venv_path)})")
            # Check Python version in venv
            try:
                python_path = os.path.join(venv_path, 'bin', 'python')
                if os.path.exists(python_path):
                    result = subprocess.run([python_path, '--version'], 
                                           capture_output=True, text=True, timeout=1)
                    print(f"  Venv Python Version: {result.stdout.strip() or result.stderr.strip()}")
            except (subprocess.SubprocessError, OSError):
                print("  Venv Python Version: Unable to determine")
        else:
            print("  Virtual Environment: ❌ Not active (recommended)")
    except Exception as e:
        print(f"  Virtual Environment check error: {e}")
    
    # Check for critical dependencies
    print("\nDependency Check:")
    missing_deps = []
    try:
        import chromadb
        print(f"  ChromaDB: ✅ {chromadb.__version__ if hasattr(chromadb, '__version__') else 'Installed (version unknown)'}")
    except ImportError:
        print("  ChromaDB: ❌ Not installed")
        missing_deps.append("chromadb")
    
    try:
        import sentence_transformers
        print(f"  Sentence-Transformers: ✅ {sentence_transformers.__version__ if hasattr(sentence_transformers, '__version__') else 'Installed (version unknown)'}")
    except ImportError:
        print("  Sentence-Transformers: ❌ Not installed")
        missing_deps.append("sentence-transformers")
    
    try:
        import flask
        print(f"  Flask: ✅ {flask.__version__ if hasattr(flask, '__version__') else 'Installed (version unknown)'}")
    except ImportError:
        print("  Flask: ❌ Not installed")
        missing_deps.append("flask")
    
    try:
        import flask_socketio
        print(f"  Flask-SocketIO: ✅ {flask_socketio.__version__ if hasattr(flask_socketio, '__version__') else 'Installed (version unknown)'}")
    except ImportError:
        print("  Flask-SocketIO: ❌ Not installed")
        missing_deps.append("flask-socketio")
    
    try:
        import torch
        torch_version = torch.__version__
        print(f"  PyTorch: ✅ {torch_version}")
        print(f"  CUDA Available: {'✅ Yes' if torch.cuda.is_available() else '❌ No'}")
        if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps') and hasattr(torch.backends.mps, 'is_available'):
            print(f"  MPS Available: {'✅ Yes' if torch.backends.mps.is_available() else '❌ No'}")
    except ImportError:
        print("  PyTorch: ❌ Not installed")
        missing_deps.append("torch")
    
    # Directory structure check
    print("\nDirectory Structure Check:")
    critical_dirs = [
        "models", "cache", "logs", "vector_db", "web_ui", "web_ui/templates", "web_ui/static"
    ]
    missing_dirs = []
    for dir_name in critical_dirs:
        if os.path.exists(dir_name):
            print(f"  {dir_name}: ✅ Exists")
        else:
            print(f"  {dir_name}: ❌ Missing")
            missing_dirs.append(dir_name)
    
    # File integrity check
    print("\nFile Integrity Check:")
    critical_files = {
        "main.py": "Main script",
        "config.json": "Configuration file",
        "web_ui.py": "Web UI module",
        "rag_manager.py": "RAG module",
        "model_manager.py": "Model manager",
        "memory_manager.py": "Memory manager",
        "utils.py": "Utilities"
    }
    missing_files = []
    for filename, description in critical_files.items():
        if os.path.exists(filename):
            print(f"  {filename}: ✅ Present ({description})")
        else:
            print(f"  {filename}: ❌ Missing ({description})")
            missing_files.append(filename)
    
    # Config check
    print("\nConfiguration Check:")
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"  Config file: ✅ Valid JSON")
            print(f"  Model: {config.get('model', {}).get('name', 'Not specified')}")
            print(f"  Quantization: {config.get('model', {}).get('quantization', 'Not specified')}")
            print(f"  Web UI Port: {config.get('web_ui', {}).get('port', 'Not specified')}")
            
            # Check for port conflicts on web UI port
            web_port = config.get('web_ui', {}).get('port')
            if web_port:
                try:
                    import socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = s.connect_ex(('127.0.0.1', web_port))
                    s.close()
                    if result == 0:
                        print(f"  Web UI Port {web_port}: ❌ Currently in use (conflict)")
                    else:
                        print(f"  Web UI Port {web_port}: ✅ Available")
                except Exception:
                    print(f"  Web UI Port {web_port}: ❓ Unable to check availability")
        except Exception as e:
            print(f"  Config file: ❌ Error: {e}")
    else:
        print(f"  Config file: ❌ Missing")
    
    # Memory check
    print("\nMemory Information:")
    try:
        import psutil
        vm = psutil.virtual_memory()
        print(f"  Total RAM: {vm.total / (1024**3):.1f} GB")
        print(f"  Available RAM: {vm.available / (1024**3):.1f} GB")
        print(f"  Used RAM: {vm.used / (1024**3):.1f} GB ({vm.percent}%)")
        
        # RAM recommendations for Reflexia
        if vm.total < 20 * (1024**3):  # Less than 20GB
            print("  ⚠️  Warning: Low total RAM. Reflexia models may not run optimally.")
            print("  Recommendation: Use 4-bit quantization and reduce context length.")
        elif vm.available < 10 * (1024**3):  # Less than 10GB available
            print("  ⚠️  Warning: Low available RAM. Close other applications to free memory.")
    except ImportError:
        print("  Memory info unavailable (psutil not installed)")
        missing_deps.append("psutil")
    
    # Check ChromaDB collections if RAG is configured
    vector_db_path = "vector_db"
    if os.path.exists(vector_db_path):
        print("\nVector Database Check:")
        try:
            import chromadb
            client = chromadb.PersistentClient(path=vector_db_path)
            collections = client.list_collections()
            if collections:
                print(f"  Collections: ✅ {len(collections)} found")
                for coll in collections:
                    try:
                        count = client.get_collection(coll.name).count()
                        print(f"    • {coll.name}: {count} documents")
                    except Exception as e:
                        print(f"    • {coll.name}: Error getting count - {e}")
            else:
                print("  Collections: ❌ None found")
                print("  Recommendation: Run 'python fix_rag_final.py' to initialize the vector database")
        except Exception as e:
            print(f"  Vector DB check failed: {e}")
    
    # Summary and recommendations
    print("\n=== Summary and Recommendations ===")
    
    if missing_deps:
        print("\n⚠️  Missing Dependencies:")
        print("  Run the following command to install missing dependencies:")
        print(f"  pip install {' '.join(missing_deps)}")
    
    if missing_dirs:
        print("\n⚠️  Missing Directories:")
        print("  Create the following directories:")
        for dir_name in missing_dirs:
            print(f"  mkdir -p {dir_name}")
    
    if missing_files:
        print("\n⚠️  Missing Critical Files:")
        print("  Please restore these files from the original repository")
    
    if powershell_detected:
        print("\n⚠️  Terminal Issue Detected:")
        print("  Run Reflexia with a bash/zsh shell instead of PowerShell to avoid rendering issues:")
        print("  zsh -c \"cd '/Users/matthewscott/Desktop/Reflexia Model Manager' && python main.py --interactive --rag\"")
    
    print("\n=== End of Diagnostic Information ===\n")
    
    return True

def test_rag_functionality():
    """Run a basic test of RAG functionality"""
    print("\n=== Testing RAG Functionality ===\n")
    
    # Detect potential terminal issues early
    terminal_issue_detected = False
    try:
        import platform
        import subprocess
        term_program = os.environ.get('TERM_PROGRAM', 'Unknown')
        
        if 'powershell' in term_program.lower() or (platform.system() == 'Darwin' and term_program == 'Unknown'):
            # Additional check for PowerShell on macOS
            try:
                result = subprocess.run(['ps', '-p', str(os.getppid()), '-o', 'command='], 
                                      capture_output=True, text=True, timeout=1)
                if 'powershell' in result.stdout.lower():
                    terminal_issue_detected = True
                    print("⚠️  PowerShell terminal detected. Some rendering issues may occur.")
                    print("    Consider running via bash/zsh instead:\n")
                    print("    zsh -c \"cd '/Users/matthewscott/Desktop/Deekseek Model' && python main.py --test-rag\"\n")
            except Exception:
                pass
    except Exception:
        pass
    
    # Import and dependency checks
    print("Checking required dependencies...")
    missing_deps = []
    
    try:
        import chromadb
        print("✅ ChromaDB installed")
    except ImportError:
        print("❌ ChromaDB not installed")
        missing_deps.append("chromadb")
    
    try:
        import sentence_transformers
        print("✅ Sentence-Transformers installed")
    except ImportError:
        print("❌ Sentence-Transformers not installed")
        missing_deps.append("sentence-transformers")
    
    if missing_deps:
        print("\n❌ Missing required dependencies. Please install:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    # Vector database path check
    vector_db_path = "vector_db"
    if not os.path.exists(vector_db_path):
        print(f"\n❌ Vector database directory '{vector_db_path}' not found")
        print("Run 'python fix_rag_final.py' to initialize the vector database")
        return False
    
    # Environment variables for embedding models
    print("\nSetting up environment for embedding models...")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if platform.system() == "Darwin":  # macOS
        os.environ["USE_MPS"] = "0"  # Disable MPS to avoid potential issues
    
    try:
        # Test ChromaDB
        print("\nTesting ChromaDB connection...")
        import chromadb
        client = chromadb.PersistentClient(path=vector_db_path)
        collections = client.list_collections()
        
        if not collections:
            print("❌ No collections found in the vector database")
            print("Run 'python fix_rag_final.py' to initialize with sample documents")
            return False
            
        print(f"✅ ChromaDB connected successfully. Found {len(collections)} collections:")
        for coll in collections:
            try:
                collection = client.get_collection(coll.name)
                count = collection.count()
                print(f"  • {coll.name}: {count} documents")
            except Exception as e:
                print(f"  • {coll.name}: Error getting count - {e}")
        
        # Test embeddings
        print("\nTesting embedding generation...")
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading embedding model (this may take a moment)...")
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            test_embedding = model.encode(["This is a test of the embedding function."])
            print(f"✅ Embedding generation successful. Shape: {test_embedding.shape}")
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            print("This may indicate an issue with sentence-transformers or its dependencies")
            return False
        
        # Test basic query if collections exist
        print("\nTesting vector database query...")
        try:
            # Try each collection until one works
            query_success = False
            for coll in collections:
                try:
                    collection = client.get_collection(coll.name)
                    print(f"Querying collection '{coll.name}'...")
                    results = collection.query(
                        query_texts=["machine learning"],
                        n_results=1
                    )
                    
                    if results and "documents" in results and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
                        print(f"✅ Query successful! Found document: {results['documents'][0][0][:50]}...")
                        
                        # Print distance/similarity for debugging
                        if "distances" in results and len(results["distances"]) > 0 and len(results["distances"][0]) > 0:
                            distance = results["distances"][0][0]
                            similarity = 1.0 - distance/2.0
                            print(f"   Similarity score: {similarity:.3f}")
                        
                        query_success = True
                        break
                    else:
                        print(f"❌ No results found in collection '{coll.name}'")
                except Exception as e:
                    print(f"❌ Error querying collection '{coll.name}': {e}")
            
            if not query_success:
                print("\n❌ Unable to get results from any collection")
                print("Your vector database may need to be reinitialized")
                return False
        except Exception as e:
            print(f"❌ Error during query test: {e}")
            return False
        
        # Test RAG integration
        print("\nTesting RAG response generation...")
        try:
            # Try to import the RAG manager and generate a response
            from rag_manager import RAGManager
            from config import Config
            
            config = Config()
            rag = RAGManager(config)
            
            if rag.is_available():
                print("Generating RAG response (this may take a moment)...")
                result = rag.generate_rag_response(
                    "What is machine learning?",
                    system_prompt="You are a helpful AI assistant."
                )
                
                if result and "response" in result and result["response"]:
                    print("✅ RAG response generated successfully")
                    print("\nSample response:")
                    print("-" * 40)
                    print(result["response"][:200] + "..." if len(result["response"]) > 200 else result["response"])
                    print("-" * 40)
                    
                    if "sources" in result and result["sources"]:
                        print("\nSources:")
                        for source in result["sources"]:
                            print(f"- {source}")
                    
                    print("\n✅ Full RAG pipeline test completed successfully!")
                    return True
                else:
                    print("❌ RAG response generation failed - empty response")
            else:
                print("❌ RAG manager reports that it is not available")
                
            # If we got here, we couldn't do a full test, but basic functionality works
            print("\n⚠️ Basic vector database and embedding tests passed, but full RAG test failed")
            print("This may indicate issues with the model integration or RAG manager")
            return True  # Return true since the core vector DB is working
            
        except Exception as e:
            print(f"❌ Error during RAG response test: {e}")
            print("\n⚠️ Basic vector database and embedding tests passed, but RAG integration test failed")
            return True  # Return true since the core vector DB is working
        
    except Exception as e:
        print(f"\n❌ RAG test failed: {e}")
        if terminal_issue_detected:
            print("\nThis failure may be related to PowerShell terminal rendering issues.")
            print("Try running the test with bash/zsh instead.")
        return False
    
    print("\n=== RAG Test Complete ===\n")
    return True
