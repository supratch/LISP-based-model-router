#!/usr/bin/env python3
"""
Simple startup script for the AI Workload Routing System backend
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")

def check_requirements():
    """Check if requirements are installed."""
    try:
        import fastapi
        import uvicorn
        import structlog
        import pydantic
        print("✓ Core dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Installing requirements...")
        return install_requirements()

def install_requirements():
    """Install requirements if missing."""
    try:
        os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"], 
                      check=True)
        print("✓ Requirements installed")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install requirements")
        return False

def start_server():
    """Start the FastAPI server."""
    try:
        os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
        print("\n🚀 Starting AI Workload Routing System...")
        print("📍 Backend URL: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("💡 Health Check: http://localhost:8000/health")
        print("\nPress Ctrl+C to stop the server\n")
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"✗ Error starting server: {e}")

def main():
    """Main startup function."""
    print("🔧 AI Workload Routing System - Backend Startup")
    print("=" * 50)
    
    check_python_version()
    
    if check_requirements():
        start_server()
    else:
        print("✗ Startup failed due to dependency issues")
        sys.exit(1)

if __name__ == "__main__":
    main()