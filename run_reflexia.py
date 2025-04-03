#!/usr/bin/env python3
"""
run_reflexia.py - Part of Reflexia Model Manager

Copyright (c) 2025 Matthew D. Scott
All rights reserved.

This source code is licensed under the Reflexia Model Manager License
found in the LICENSE file in the root directory of this source tree.

Unauthorized use, reproduction, or distribution is prohibited.
"""
Reflexia Model Terminal-Safe Launcher

This script provides a reliable way to run Reflexia Model commands regardless
of terminal environment, automatically detecting and working around PowerShell
rendering issues on macOS.
"""
import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path

def is_powershell():
    """Detect if running in PowerShell terminal on macOS"""
    if platform.system() != 'Darwin':
        return False
    
    term_program = os.environ.get('TERM_PROGRAM', '')
    if 'powershell' in term_program.lower():
        return True
    
    # Additional check for PowerShell
    try:
        # Check parent process - this often reveals the actual terminal
        parent_pid = os.getppid()
        result = subprocess.run(
            ['ps', '-p', str(parent_pid), '-o', 'command='],
            capture_output=True, text=True, timeout=1
        )
        if 'powershell' in result.stdout.lower():
            return True
    except Exception:
        pass
    
    return False

def find_shell():
    """Find available shell on the system (zsh preferred, bash as fallback)"""
    shells = ['/bin/zsh', '/bin/bash', '/bin/sh']
    for shell in shells:
        if os.path.exists(shell):
            return shell
    
    # Fallback to 'zsh' or 'bash' in PATH
    for shell in ['zsh', 'bash', 'sh']:
        try:
            result = subprocess.run(['which', shell], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    
    return None

def run_with_shell(args):
    """Run the command with proper shell to avoid rendering issues"""
    shell_path = find_shell()
    if not shell_path:
        print("❌ No suitable shell found. Please install zsh or bash.")
        return 1
    
    # Get current working directory
    current_dir = os.getcwd()
    
    # Reconstruct command but skip the script name (args[0]) and remove --force-shell if present
    cmd_args = ['python', 'main.py']
    main_args = args[1:]
    
    # Remove --force-shell and --force-direct from arguments passed to main.py
    if '--force-shell' in main_args:
        main_args.remove('--force-shell')
    if '--force-direct' in main_args:
        main_args.remove('--force-direct')
    
    cmd_args.extend(main_args)
    cmd = ' '.join(cmd_args)
    
    # Construct full shell command
    shell_cmd = [shell_path, '-c', f"cd '{current_dir}' && {cmd}"]
    
    print(f"🔄 Running through {os.path.basename(shell_path)} to avoid terminal rendering issues...")
    
    try:
        # Use subprocess.call to inherit stdin/stdout/stderr
        return subprocess.call(shell_cmd)
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Terminal-safe launcher for Reflexia Model",
        epilog="All arguments after -- are passed directly to main.py"
    )
    
    # Add all the same arguments as main.py
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    group.add_argument('--batch', '-b', nargs=2, metavar=('INPUT_FILE', 'OUTPUT_FILE'), 
                      help='Process prompts from input file and save to output file')
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
    
    # Add specific arguments for this wrapper
    parser.add_argument('--force-direct', action='store_true', 
                       help='Force direct execution even in PowerShell')
    parser.add_argument('--force-shell', action='store_true',
                       help='Force execution through bash/zsh shell')
    
    return parser.parse_args()

def main():
    """Main function for the wrapper script"""
    # Check if main.py exists
    if not Path('main.py').exists():
        print("❌ main.py not found. Make sure you're in the Reflexia Model directory.")
        return 1
    
    args = parse_args()
    
    # Determine if we need to use shell execution
    powershell_detected = is_powershell()
    use_shell = args.force_shell or (powershell_detected and not args.force_direct)
    
    if powershell_detected and not args.force_direct:
        print("⚠️  PowerShell terminal detected on macOS, which may cause rendering issues.")
        
    if use_shell:
        # Run through shell
        return run_with_shell(sys.argv)
    else:
        # Direct execution
        try:
            # Filter out wrapper-specific arguments
            main_args = []
            skip_next = False
            for i, arg in enumerate(sys.argv[1:]):
                if skip_next:
                    skip_next = False
                    continue
                
                if arg in ['--force-shell', '--force-direct']:
                    continue
                    
                main_args.append(arg)
            
            cmd = ['python', 'main.py'] + main_args
            return subprocess.call(cmd)
        except Exception as e:
            print(f"❌ Error running command: {e}")
            print("Try running with --force-shell to use bash/zsh instead.")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 
