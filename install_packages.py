#!/usr/bin/env python3
"""
Installation script for Gemini project dependencies
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {package}")

def main():
    """Install all required packages"""
    packages = [
        "google-generativeai",
        "Pillow", 
        "opencv-python",
        "openai",
        "python-metar",
        "python-opensky",
        "pandas",
        "requests-oauthlib"
        

    ]
    
    print("Installing required packages for Gemini project...")
    print("=" * 50)
    
    for package in packages:
        install_package(package)
    
    print("=" * 50)
    print("Installation complete!")

