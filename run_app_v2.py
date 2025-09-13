#!/usr/bin/env python3
"""
Canvas LMS Course Explorer Launcher

Launcher script for the improved Canvas Streamlit application.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Launch the improved Streamlit app"""
    app_path = Path(__file__).parent / "canvas_streamlit_app_v2.py"
    
    if not app_path.exists():
        print("❌ Error: canvas_streamlit_app_v2.py not found!")
        sys.exit(1)
    
    print("🚀 Starting Canvas LMS Course Explorer...")
    print("📱 The app will open in your web browser")
    print("🔗 URL: http://localhost:8502")
    print("\nPress Ctrl+C to stop the app")
    print("-" * 50)
    
    try:
        # Run streamlit app on port 8502 to avoid conflicts
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
