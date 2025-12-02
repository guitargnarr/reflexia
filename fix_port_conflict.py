#!/usr/bin/env python3
"""
fix_port_conflict.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.

Fix port conflict for Web UI
"""
import os
import subprocess
import sys
import socket
import psutil
from pathlib import Path
import json

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_using_port(port):
    """Find the process using the specified port"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def update_config_port():
    """Update the config to use a different port"""
    config_file = Path("config.json")
    if not config_file.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        
        # Check if web_ui section exists
        if "web_ui" not in config:
            config["web_ui"] = {}
        
        # Get current port
        current_port = config["web_ui"].get("port", 8000)
        
        # Find an available port
        new_port = current_port + 1
        while is_port_in_use(new_port) and new_port < current_port + 100:
            new_port += 1
        
        # Update config
        config["web_ui"]["port"] = new_port
        
        # Write back
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated config to use port {new_port}")
        return True
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def fix_port_conflict():
    """Fix port conflict for Web UI"""
    print("Checking for port conflicts...")
    
    port = 8000
    if is_port_in_use(port):
        print(f"⚠️ Port {port} is in use")
        
        # Find process using port
        proc = find_process_using_port(port)
        if proc:
            print(f"Process using port {port}: {proc.name()} (PID: {proc.pid})")
            
            # Ask user if they want to kill the process
            choice = input(f"Do you want to terminate {proc.name()} (PID: {proc.pid})? (y/n): ")
            if choice.lower() == 'y':
                try:
                    proc.terminate()
                    print(f"✅ Process {proc.pid} terminated")
                    # Wait a moment to ensure the port is freed
                    import time
                    time.sleep(1)
                    return True
                except Exception as e:
                    print(f"❌ Could not terminate process: {e}")
        
        # If we get here, either there was no process found or user declined to kill it
        # Update the config to use a different port
        return update_config_port()
    else:
        print(f"✅ Port {port} is available")
        return True

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Installing required package: psutil")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    fix_port_conflict()