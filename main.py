#!/usr/bin/env python3
"""
main.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Reflexia Local LLM Implementation
Main Entry Point Script

Designed for MacOS Sequoia with M3 Max (36GB RAM)
"""

import os
import sys
import argparse
import logging
import logging.handlers
from pathlib import Path
import json
import time
import threading

# Set up Metal acceleration for Apple Silicon if enabled
from utils import get_env_var
metal_enabled = get_env_var("METAL_ENABLED", "true").lower() in ("true", "1", "yes")
if metal_enabled:
    os.environ["OLLAMA_METAL"] = "1"

# Import utils first to set up logging
from utils import setup_rotating_logs, check_dependencies

# Get log level from environment variable if set
log_level_name = get_env_var("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    
# Configure logger with rotation
log_file = setup_rotating_logs(app_name="reflexia-tools", log_dir="logs", log_level=log_level)
logger = logging.getLogger("reflexia-tools")

# Import modules
try:
    from config import Config
    from model_manager import ModelManager
    from memory_manager import MemoryManager
    from prompt_manager import PromptManager
    from fine_tuning import FineTuningManager
    from utils import benchmark_model, monitor_resources, generate_requirements_file
except ImportError as e:
    logger.error(f"Failed to import core module: {e}")
    print(f"Error: Missing core module - {e}")
    print("Please ensure all dependencies are installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

# Import optional modules
rag_available = False
try:
    from self.rag_manager import RAGManager
    rag_available = True
except ImportError as e:
    logger.warning(f"RAG Manager not available: {e}")
    print(f"Note: RAG functionality not available - {e}")
    print("For RAG support: pip install chromadb sentence-transformers")

web_ui_available = False
try:
    from web_ui import WebUI
    web_ui_available = True
except ImportError as e:
    logger.warning(f"Web UI not available: {e}")
    print(f"Note: Web UI not available - {e}")
    print("For Web UI support: pip install flask flask-socketio")

class ReflexiaTools:
    """Main application class for Reflexia Tools"""
    
    def __init__(self, config_path=None):
        """Initialize the Reflexia Tools framework"""
        logger.info("Initializing Reflexia Tools")
        
        # Load configuration
        self.config = Config(config_path)
        logger.info(f"Loaded configuration from {config_path or 'default'}")
        
        # Check dependencies
        check_dependencies()
        
        # Initialize core components
        self.model_manager = ModelManager(self.config)
        self.memory_manager = MemoryManager(self.config, self.model_manager)
        self.prompt_manager = PromptManager(self.config)
        self.fine_tuning = FineTuningManager(self.config)
        
        # Apply recovery mechanisms and health monitoring
        try:
            from utils import get_env_var
            enable_recovery = get_env_var("ENABLE_RECOVERY", "true").lower() in ("true", "1", "yes")
            
            if enable_recovery:
                import recovery
                
                # Apply circuit breakers to critical components
                self.model_manager = recovery.protect_model_manager(self.model_manager)
                
                # Initialize health monitor
                self.health_monitor = recovery.HealthMonitor(
                    model_manager=self.model_manager,
                    memory_manager=self.memory_manager
                )
                
                # Start health monitoring
                self.health_monitor.start_monitoring(interval=60)
                logger.info("Recovery mechanisms enabled")
        except ImportError:
            logger.warning("Recovery module not available, recovery disabled")
            self.health_monitor = None
        
        # Initialize optional components
        self.rag_manager = None
        if rag_available:
            try:
                self.rag_manager = RAGManager(self.config, self.model_manager)
                
                # Apply recovery to RAG manager if enabled
                if hasattr(self, 'health_monitor') and self.health_monitor:
                    import recovery
                    self.rag_manager = recovery.protect_rag_manager(self.rag_manager)
                    # Update health monitor with RAG manager
                    self.health_monitor.rag_manager = self.rag_manager
                
                logger.info("RAG manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize RAG manager: {e}")
                print(f"Error initializing RAG manager: {e}")
        
        self.web_ui = None
        if web_ui_available:
            try:
                self.web_ui = WebUI(
                    self.config,
                    self.model_manager,
                    self.memory_manager,
                    self.prompt_manager,
                    self.rag_manager
                )
                logger.info("Web UI initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Web UI: {e}")
                print(f"Error initializing Web UI: {e}")
        
        # Resource monitoring
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start resource monitoring in a separate thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
        
    def _monitor_loop(self):
        """Background thread for resource monitoring"""
        while self.monitoring:
            stats = monitor_resources()
            logger.debug(f"Resources: {stats}")
            
            # Check memory pressure
            if stats["memory_percent"] > self.config.get("memory", "max_memory_percent", default=80):
                logger.warning(f"High memory usage detected: {stats['memory_percent']}%")
                self.memory_manager.reduce_memory_pressure()
                
                # Adaptively change quantization if enabled
                if self.config.get("memory", "adaptive_quantization", default=True):
                    logger.info("Attempting adaptive quantization due to memory pressure")
                    self.model_manager.adaptive_quantization(self.memory_manager)
            
            time.sleep(10)  # Check every 10 seconds
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("Resource monitoring stopped")
    
    def interactive_mode(self, use_rag=False):
        """Run an interactive session with the model"""
        logger.info(f"Starting interactive mode (RAG: {use_rag})")
        print("\n=== Reflexia Interactive Mode ===")
        if use_rag and self.rag_manager:
            print("RAG enabled: Responses will incorporate document knowledge")
        elif use_rag and not self.rag_manager:
            print("Warning: RAG requested but not available")
            use_rag = False
        print("Type 'exit' to quit, 'help' for commands\n")
        
        # Load the model
        self.model_manager.load_model()
        
        while True:
            try:
                # Get user input
                user_input = input("> ")
                # Strip whitespace
                user_input = user_input.strip()

                # Command handling
                if user_input.lower() == "exit" or user_input.lower() == "quit":
                    print("Exiting application...")
                    break

                elif user_input.lower() == "help":
                    print("Available commands:")
                    commands = {
                        "exit/quit": "Exit the application",
                        "help": "Show this help message",
                        "benchmark": "Run a benchmarking test",
                        "system:X": "Set system prompt to X",
                        "load:X": "Load document X into the knowledge base",
                        "clear": "Clear the screen",
                        "status": "Show current system status",
                        "memory": "Show memory usage details",
                        "list": "List available documents in the knowledge base",
                        "info": "Show information about the current model"
                    }
                    max_len = max(len(c) for c in commands.keys())
                    for command, description in commands.items():
                        print(f"  {command.ljust(max_len+2)}- {description}")
                    
                    if use_rag and self.rag_manager and self.rag_manager.is_available():
                        print("\nRAG is enabled. Responses will incorporate knowledge from loaded documents.")
                        print("Type 'list' to see available documents.")
                    continue

                elif user_input.lower() == "clear":
                    # Clear the screen
                    os.system("cls" if os.name == "nt" else "clear")
                    print("=== Reflexia Interactive Mode ===\nType 'help' for available commands")
                    if use_rag and self.rag_manager and self.rag_manager.is_available():
                        print("RAG enabled: Responses will incorporate document knowledge")
                    continue

                elif user_input.lower() == "status":
                    # Show system status
                    print("=== System Status ===")
                    print(f"Model: {self.model_manager.model_name}")
                    print(f"Memory usage: {self.memory_manager.get_memory_usage():.1f}%")
                    print(f"RAG enabled: {use_rag and self.rag_manager is not None and self.rag_manager.is_available()}")
                    if use_rag and self.rag_manager and self.rag_manager.is_available():
                        try:
                            if hasattr(self.rag_manager, "list_documents"):
                                docs = self.rag_manager.list_documents()
                                print(f"Documents loaded: {len(docs)}")
                        except Exception:
                            print("Documents loaded: Unknown")
                    continue

                elif user_input.lower() == "memory":
                    # Show detailed memory info
                    mem_stats = self.memory_manager.get_memory_stats()
                    print("=== Memory Usage ===")
                    print(f"Current usage: {mem_stats['percent']:.1f}%")
                    print(f"Used: {mem_stats['used'] / (1024**3):.2f} GB")
                    print(f"Available: {mem_stats['available'] / (1024**3):.2f} GB")
                    print(f"Total: {mem_stats['total'] / (1024**3):.2f} GB")
                    print(f"Critical threshold: {mem_stats.get('critical', 90)}%")
                    continue

                elif user_input.lower() == "list":
                    # List available documents
                    if not use_rag or not self.rag_manager or not self.rag_manager.is_available():
                        print("RAG is not available")
                        continue
                    
                    try:
                        # Try to use the list_documents method if available
                        if hasattr(self.rag_manager, "list_documents"):
                            docs = self.rag_manager.list_documents()
                            if docs:
                                print("Available documents:")
                                for i, doc in enumerate(docs, 1):
                                    doc_name = doc.get("filename", doc.get("id", f"Document {i}"))
                                    print(f"  {i}. {doc_name}")
                            else:
                                print("No documents loaded. Use 'load:filename' to add documents.")
                        else:
                            # Fallback to showing collections
                            if hasattr(self.rag_manager, "chroma_client") and self.rag_manager.chroma_client:
                                collections = self.rag_manager.chroma_client.list_collections()
                                if collections:
                                    print("Available collections:")
                                    for i, coll in enumerate(collections, 1):
                                        print(f"  {i}. {coll.name}")
                                else:
                                    print("No collections found. Use 'load:filename' to add documents.")
                            else:
                                print("Unable to list documents. RAG system is available but document listing is not supported.")
                    except Exception as e:
                        print(f"Error listing documents: {e}")
                    continue

                elif user_input.lower() == "info":
                    # Show model information
                    print(f"=== Model: {self.model_manager.model_name} ===")
                    try:
                        ctx_len = self.model_manager.context_length
                        print(f"Context length: {ctx_len}")
                    except:
                        print(f"Context length: Unknown")
                    try:
                        quant = self.model_manager.quantization
                        print(f"Quantization: {quant}")
                    except:
                        print(f"Quantization: Unknown")
                    try:
                        metal = self.model_manager.metal_enabled
                        print(f"Metal acceleration: {'Enabled' if metal else 'Disabled'}")
                    except:
                        print(f"Metal acceleration: Unknown")
                    continue

                elif user_input.lower() == "benchmark":
                    print("Running benchmark...")
                    try:
                        if hasattr(self.model_manager, "benchmark_model"):
                            self.model_manager.benchmark_model()
                        else:
                            print("Benchmark function not available")
                    except Exception as e:
                        print(f"Error running benchmark: {e}")
                    continue

                elif user_input.lower().startswith("system:"):
                    # Set system prompt
                    new_prompt = user_input[7:].strip()
                    if new_prompt:
                        self.prompt_manager.set_system_prompt(new_prompt)
                        print(f"System prompt updated: {new_prompt}")
                    else:
                        current = self.prompt_manager.get_system_prompt()
                        print(f"Current system prompt: {current}")
                    continue

                elif user_input.lower().startswith("load:"):
                    # Load document to RAG
                    if not use_rag or not self.rag_manager or not self.rag_manager.is_available():
                        print("RAG is not available")
                        continue
                    
                    filepath = user_input[5:].strip()
                    if not filepath:
                        print("Please specify a file to load: load:path/to/file")
                        continue
                    
                    try:
                        success = self.rag_manager.load_file(filepath)
                        if success:
                            print(f"✅ Successfully loaded: {filepath}")
                        else:
                            print(f"❌ Failed to load document: {filepath}")
                    except Exception as e:
                        print(f"Error loading document: {e}")
                    continue

                # Check for command-like typos
                command_prefixes = ['help', 'exit', 'quit', 'clear', 'list', 'memory', 'status', 'info']
                user_prefix = user_input.split()[0].lower() if user_input.split() else ''
                
                # Check for close matches to commands
                if user_prefix and any(cmd.startswith(user_prefix) for cmd in command_prefixes) and user_prefix not in command_prefixes:
                    matches = [cmd for cmd in command_prefixes if cmd.startswith(user_prefix)]
                    if matches:
                        print(f"Command '{user_prefix}' not found. Did you mean '{matches[0]}'?")
                        print("Type 'help' for a list of available commands.")
                        continue

                # Process the input and get response
                start_time = time.time()
                
                if use_rag and self.rag_manager:
                    # Generate response with RAG
                    result = self.rag_manager.generate_rag_response(
                        user_input,
                        system_prompt=self.prompt_manager.get_system_prompt()
                    )
                    response = result["response"]
                    
                    # Display response
                    print(f"\n{response}")
                    
                    # Display sources if available
                    if result["sources"]:
                        print("\nSources:")
                        for source in result["sources"]:
                            print(f"- {source}")
                else:
                    # Standard generation
                    formatted_prompt = self.prompt_manager.format_prompt(user_input)
                    
                    # Before generating responses
                    content_complexity = self.model_manager.estimate_content_complexity(formatted_prompt)
                    self.model_manager.adaptive_quantization(self.memory_manager, content_complexity)
                    
                    response = self.model_manager.generate_response(
                        formatted_prompt,
                        system_prompt=self.prompt_manager.get_system_prompt()
                    )
                    
                    # Display response
                    print(f"\n{response}")
                
                elapsed = time.time() - start_time
                print(f"\n[Generated in {elapsed:.2f}s]")
                
                # Update memory usage stats
                memory_stats = self.memory_manager.get_memory_stats()
                if memory_stats["percent"] > 70:
                    print(f"[Memory usage: {memory_stats['percent']}%]")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"Error: {e}")
        
        logger.info("Interactive mode ended")
    
    def _show_help(self, rag_enabled=False):
        """Show help information"""
        print("\nAvailable commands:")
        print("  exit       - Exit the application")
        print("  help       - Show this help message")
        print("  benchmark  - Run a benchmarking test")
        print("  system:X   - Set system prompt to X")
        
        if rag_enabled:
            print("  load:X     - Load document X into the knowledge base")
            print("\nRAG is enabled. Responses will incorporate knowledge from loaded documents.")
        
        print("")
    
    def _run_benchmark(self):
        """Run benchmark tests"""
        print("\nRunning benchmark tests...")
        results = benchmark_model(self.model_manager, self.config)
        
        # Calculate and display average time across all prompts
        total_time = 0
        total_prompts = 0
        
        for result in results:
            if result["avg_time"] != float('inf'):
                total_time += result["avg_time"]
                total_prompts += 1
        
        if total_prompts > 0:
            average_time = total_time / total_prompts
            print(f"\nOverall average response time: {average_time:.2f}s")
    
    def batch_process(self, input_file, output_file, use_rag=False):
        """Process inputs from a file in batch mode"""
        logger.info(f"Starting batch processing: {input_file} -> {output_file}")
        
        try:
            # Load inputs
            with open(input_file, 'r') as f:
                inputs = [line.strip() for line in f if line.strip()]
            
            # Process each input
            results = []
            self.model_manager.load_model()
            
            for i, prompt in enumerate(inputs):
                print(f"Processing prompt {i+1}/{len(inputs)}...")
                
                try:
                    start_time = time.time()
                    
                    if use_rag and self.rag_manager:
                        # Generate RAG response
                        response_data = self.rag_manager.generate_rag_response(prompt)
                        response = response_data["response"]
                        sources = response_data.get("sources", [])
                        
                        results.append({
                            "prompt": prompt,
                            "response": response,
                            "sources": sources,
                            "time": time.time() - start_time
                        })
                    else:
                        # Standard generation
                        formatted_prompt = self.prompt_manager.format_prompt(prompt)
                        
                        # Before generating responses
                        content_complexity = self.model_manager.estimate_content_complexity(formatted_prompt)
                        self.model_manager.adaptive_quantization(self.memory_manager, content_complexity)
                        
                        response = self.model_manager.generate_response(
                            formatted_prompt,
                            system_prompt=self.prompt_manager.get_system_prompt()
                        )
                        
                        results.append({
                            "prompt": prompt,
                            "response": response,
                            "time": time.time() - start_time
                        })
                    
                    # Monitor memory to prevent OOM
                    memory_stats = self.memory_manager.get_memory_stats()
                    if memory_stats["percent"] > 85:
                        logger.warning(f"High memory usage: {memory_stats['percent']}%. Reducing pressure...")
                        self.memory_manager.reduce_memory_pressure()
                    
                    # Brief pause between requests to let resources stabilize
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing prompt {i+1}: {e}")
                    results.append({
                        "prompt": prompt,
                        "error": str(e)
                    })
            
            # Save results
            with open(output_file, 'w') as f:
                json.dump({
                    "model": self.config.get("model", "name"),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_prompts": len(inputs),
                    "successful": sum(1 for r in results if "error" not in r),
                    "results": results
                }, f, indent=2)
            
            print(f"Batch processing complete. Results saved to {output_file}")
            logger.info(f"Batch processing completed: {len(inputs)} prompts")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            print(f"Error during batch processing: {e}")
    
    def fine_tune(self, dataset_path):
        """Run fine-tuning with the specified dataset"""
        logger.info(f"Starting fine-tuning with dataset: {dataset_path}")
        print(f"Starting fine-tuning process with {dataset_path}...")
        
        try:
            # Run fine-tuning
            result = self.fine_tuning.fine_tune_model(dataset_path)
            
            if result["success"]:
                print(f"Fine-tuning completed successfully!")
                print(f"New model: {result['model_name']}")
                print(f"Performance: {result['metrics']}")
            else:
                print(f"Fine-tuning failed: {result['error']}")
            
            logger.info(f"Fine-tuning completed: {result}")
            
        except Exception as e:
            logger.error(f"Error during fine-tuning: {e}")
            print(f"Error during fine-tuning: {e}")
    
    def start_web_ui(self):
        """Start the web UI"""
        if not self.web_ui:
            logger.error("Web UI not available")
            print("Error: Web UI not available. Install dependencies with: pip install flask flask-socketio")
            return False
        
        try:
            # Start the UI in a separate thread
            self.web_ui.start(threaded=True)
            
            host = self.config.get("web_ui", "host", default="127.0.0.1")
            port = self.config.get("web_ui", "port", default=8000)
            
            print(f"Web UI started at http://{host}:{port}")
            print("Press Ctrl+C to stop")
            
            # Keep the main thread alive
            try:
                # Simple keep-alive that allows keyboard interrupts
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping Web UI...")
                return True
            
        except Exception as e:
            logger.error(f"Error starting Web UI: {e}")
            print(f"Error starting Web UI: {e}")
            return False

def main():
    """Main function for Reflexia Tools"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Reflexia Local LLM Tools")
    
    # Mode selection arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    group.add_argument('--batch', '-b', nargs=2, metavar=('INPUT_FILE', 'OUTPUT_FILE'), help='Process prompts from input file and save to output file')
    group.add_argument('--benchmark', action='store_true', help='Run benchmark tests')
    group.add_argument('--finetune', metavar='DATASET_PATH', help='Fine-tune model with dataset')
    group.add_argument('--web', '-w', action='store_true', help='Start web UI')
    group.add_argument('--initialize', action='store_true', help='Initialize system (run all necessary fixes)')
    group.add_argument('--diagnose', action='store_true', help='Run system diagnostics')
    group.add_argument('--test-rag', action='store_true', help='Test RAG functionality')
    
    # Optional arguments
    parser.add_argument('--config', metavar='CONFIG_PATH', help='Path to config file')
    parser.add_argument('--rag', action='store_true', help='Enable RAG in interactive or batch mode')
    parser.add_argument('--monitor', action='store_true', help='Enable resource monitoring')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--force-bash', action='store_true', help='Force using bash/zsh instead of current shell')
    
    try:
        args = parser.parse_args()
    except Exception as e:
        logger.error(f"Error parsing arguments: {e}")
        print(f"Error parsing command line arguments: {e}")
        print("Use --help to see available options.")
        return 1
    
    # Check for terminal rendering issues
    terminal_issue_detected = False
    if sys.platform == 'darwin' and os.environ.get('TERM_PROGRAM') == 'PowerShell':
        terminal_issue_detected = True
        if not args.force_bash:
            logger.warning("PowerShell terminal detected on macOS, which may cause rendering issues.")
            print("\n⚠️ PowerShell terminal detected, which may cause rendering issues.")
            print("To avoid these issues, you can:")
            print("  1. Use --force-bash to automatically execute via bash/zsh")
            print("  2. Run commands directly in bash/zsh")
            print("  3. Continue with possible rendering glitches\n")
            
            if not args.diagnose and not args.initialize and not args.test_rag:
                cont = input("Do you want to continue anyway? (y/N): ").lower().strip()
                if cont != 'y' and cont != 'yes':
                    print("Exiting. Please run using bash/zsh directly.")
                    return 1
    
    # For certain commands, automatically use bash/zsh if detected issues
    if terminal_issue_detected and args.force_bash:
        import subprocess
        
        # Check for available shells
        shell_cmd = None
        for shell in ['/bin/zsh', '/bin/bash', '/bin/sh']:
            if os.path.exists(shell):
                shell_cmd = shell
                break
        
        if shell_cmd:
            print(f"Restarting command using {shell_cmd}...")
            try:
                # Reconstruct command with all arguments
                cmd = [shell_cmd, '-c', f"cd '{os.getcwd()}' && python {' '.join(sys.argv)}"]
                # Remove the --force-bash flag to avoid infinite loop
                cmd[2] = cmd[2].replace(' --force-bash', '')
                
                # Execute the command
                result = subprocess.run(cmd)
                return result.returncode
            except Exception as e:
                logger.error(f"Error running command with alternative shell: {e}")
                print(f"Error: {e}")
                print("Continuing with current shell...")
    
    # Handle some commands that don't need the full initialization
    if args.initialize:
        # Run initialization scripts in the right order
        print("\n=== Initializing Reflexia System ===\n")
        
        # Use the scripts we have in the repo
        try:
            # Fix port conflicts
            print("1. Checking for port conflicts...")
            try:
                from fix_port_conflict import fix_port_conflict
                fix_port_conflict()
            except Exception as e:
                logger.error(f"Error fixing port conflicts: {e}")
                print(f"⚠️ Error fixing port conflicts: {e}")
            
            # Fix web UI
            print("\n2. Fixing Web UI...")
            try:
                from fix_web_ui_thorough import fix_web_ui_thorough
                fix_web_ui_thorough()
            except Exception as e:
                logger.error(f"Error fixing Web UI: {e}")
                print(f"⚠️ Error fixing Web UI: {e}")
            
            # Fix RAG consistency
            print("\n3. Fixing RAG consistency...")
            try:
                from fix_rag_consistency import fix_rag_consistency
                fix_rag_consistency()
            except Exception as e:
                logger.error(f"Error fixing RAG consistency: {e}")
                print(f"⚠️ Error fixing RAG consistency: {e}")
            
            # Fix RAG helper
            print("\n4. Fixing RAG helper...")
            try:
                from fix_rag_helper import fix_list_documents
                fix_list_documents()
            except Exception as e:
                logger.error(f"Error fixing RAG helper: {e}")
                print(f"⚠️ Error fixing RAG helper: {e}")
            
            # Add interactive mode
            print("\n5. Adding interactive mode...")
            try:
                from add_interactive_mode import add_interactive_mode
                add_interactive_mode()
            except Exception as e:
                logger.error(f"Error adding interactive mode: {e}")
                print(f"⚠️ Error adding interactive mode: {e}")
            
            # Add command handler
            print("\n6. Adding command handler...")
            try:
                from add_command_handler import add_command_handler
                add_command_handler()
            except Exception as e:
                logger.error(f"Error adding command handler: {e}")
                print(f"⚠️ Error adding command handler: {e}")
            
            # Apply final RAG fix
            print("\n7. Applying final RAG fix...")
            try:
                from fix_rag_final import fix_rag_final
                fix_rag_final()
            except Exception as e:
                logger.error(f"Error applying final RAG fix: {e}")
                print(f"⚠️ Error applying final RAG fix: {e}")
            
            print("\n✅ Initialization complete!")
            print("\nYou can now run the system with:")
            print("  python main.py --interactive --rag     # For interactive mode with RAG")
            print("  python main.py --web                  # For web UI")
            
            return 0
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            print(f"\n❌ Error during initialization: {e}")
            return 1
    
    if args.diagnose:
        # Run diagnostics without full initialization
        try:
            from utils import debug_environment
            debug_environment()
            return 0
        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            print(f"❌ Error running diagnostics: {e}")
            return 1
    
    if args.test_rag:
        # Test RAG functionality
        try:
            from utils import test_rag_functionality
            test_rag_functionality()
            return 0
        except Exception as e:
            logger.error(f"Error testing RAG functionality: {e}")
            print(f"❌ Error testing RAG functionality: {e}")
            print("Make sure the required modules are installed:")
            print("  - chromadb")
            print("  - sentence-transformers")
            return 1
    
    # Continue with normal initialization for other commands
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        print(f"Verbose logging enabled. Log file: {log_file}")
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        print(f"Debug mode enabled. Log file: {log_file}")
        
    # Initialize application
    try:
        app = ReflexiaTools(args.config)
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        print(f"❌ Error initializing Reflexia Tools: {e}")
        return 1
    
    # Enable resource monitoring if requested
    if args.monitor:
        try:
            app.start_monitoring()
        except Exception as e:
            logger.error(f"Error starting resource monitoring: {e}")
            print(f"⚠️ Error starting resource monitoring: {e}")
            print("Continuing without resource monitoring...")
        
    # Execute requested mode
    try:
        if args.interactive:
            return 0 if app.interactive_mode(use_rag=args.rag) else 1
        elif args.batch:
            return 0 if app.batch_process(args.batch[0], args.batch[1], use_rag=args.rag) else 1
        elif args.benchmark:
            return 0 if app._run_benchmark() else 1
        elif args.finetune:
            return 0 if app.fine_tune(args.finetune) else 1
        elif args.web:
            return 0 if app.start_web_ui() else 1
        else:
            # Default to interactive mode if no mode specified
            print("No mode specified, defaulting to interactive mode")
            return 0 if app.interactive_mode() else 1
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Error executing requested mode: {e}")
        print(f"❌ Error: {e}")
        return 1
    finally:
        # Always stop monitoring on exit if it was started
        if args.monitor:
            try:
                app.stop_monitoring()
            except Exception:
                pass  # Don't let cleanup errors affect exit code
    
    return 0

if __name__ == "__main__":
    main()
