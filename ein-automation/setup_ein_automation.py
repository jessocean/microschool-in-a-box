#!/usr/bin/env python3
"""
Setup script for EIN automation
Installs required dependencies and sets up the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("EIN Automation Setup")
    print("=" * 40)
    
    # Check if Python is available
    python_cmd = "python" if sys.platform == "win32" else "python3"
    
    # Install pip requirements
    if not run_command(f"{python_cmd} -m pip install -r requirements.txt", 
                      "Installing Python requirements"):
        print("\\nTrying alternative installation method...")
        run_command(f"{python_cmd} -m pip install playwright asyncio", 
                   "Installing packages individually")
    
    # Install Playwright browsers
    if not run_command(f"{python_cmd} -m playwright install chromium", 
                      "Installing Playwright Chromium browser"):
        print("\\nPlaywright browser installation failed. You may need to:")
        print("1. Run as administrator")
        print("2. Check your internet connection")
        print("3. Try manual installation: python -m playwright install")
    
    # Create directories
    Path("screenshots").mkdir(exist_ok=True)
    print("✓ Created screenshots directory")
    
    print("\\n" + "=" * 40)
    print("Setup completed!")
    print("\\nNext steps:")
    print("1. Edit 'ein_data.json' with your business information")
    print("2. Run 'python ein_automation.py' to start the automation")
    print("\\nMake sure to review all data before submission!")

if __name__ == "__main__":
    main()