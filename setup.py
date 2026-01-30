#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for TCBF Map App
Automates installation and environment setup
"""

import os
import sys
import subprocess
import platform

def print_header(text):
    """Header display"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_info(text):
    """Info display"""
    print(f"[INFO] {text}")

def print_success(text):
    """Success display"""
    print(f"[OK] {text}")

def print_error(text):
    """Error display"""
    print(f"[ERROR] {text}")
    sys.exit(1)

def check_python_version():
    """Check Python version"""
    print_header("Check Python Version")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print_info(f"Python {version_str}")
    
    if version.major != 3 or version.minor < 10:
        print_error(f"Python 3.10+ required (Current: {version_str})")
    
    print_success(f"Python version OK")

def create_venv():
    """Create virtual environment"""
    print_header("Create Virtual Environment")
    venv_path = ".venv"
    
    if os.path.exists(venv_path):
        print_info(f"Virtual environment already exists: {venv_path}")
        return venv_path
    
    try:
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        print_success(f"Virtual environment created: {venv_path}")
        return venv_path
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")

def get_python_executable(venv_path):
    """Get Python executable path from virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")

def get_pip_executable(venv_path):
    """Get pip executable path from virtual environment"""
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        return os.path.join(venv_path, "bin", "pip")

def upgrade_pip(pip_exe):
    """Upgrade pip to latest version"""
    print_header("Upgrade pip")
    try:
        subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
        print_success("pip upgraded")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to upgrade pip: {e}")

def install_requirements(pip_exe):
    """Install packages from requirements.txt"""
    print_header("Install Required Packages")
    
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print_error(f"{requirements_file} not found")
    
    try:
        subprocess.check_call([pip_exe, "install", "-r", requirements_file])
        print_success("Packages installed")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install packages: {e}")

def main():
    """Main setup process"""
    print_header("TCBF Map App Setup")
    
    # Check Python version
    check_python_version()
    
    # Create virtual environment
    venv_path = create_venv()
    python_exe = get_python_executable(venv_path)
    pip_exe = get_pip_executable(venv_path)
    
    # Upgrade pip
    upgrade_pip(pip_exe)
    
    # Install dependencies
    install_requirements(pip_exe)
    
    # Complete
    print_header("Setup Complete")
    print_success("All setup completed successfully")
    
    print("\n[Run Application]")
    if platform.system() == "Windows":
        print(f"  .venv\\Scripts\\python.exe main.py")
    else:
        print(f"  .venv/bin/python main.py")
    
    print("\n[Activate Virtual Environment]")
    if platform.system() == "Windows":
        print(f"  .venv\\Scripts\\activate")
    else:
        print(f"  source .venv/bin/activate")

if __name__ == "__main__":
    main()
