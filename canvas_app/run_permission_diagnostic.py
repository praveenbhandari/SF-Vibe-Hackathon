#!/usr/bin/env python3
"""
Quick Canvas Permission Diagnostic Runner

This script provides an easy way to run the Canvas permission diagnostic
without needing to remember command-line arguments.
"""

import sys
import os
from canvas_permission_diagnostic import CanvasPermissionDiagnostic

def main():
    print("🔍 Canvas API Permission Diagnostic Tool")
    print("=" * 50)
    
    # Get Canvas URL
    canvas_url = input("Enter your Canvas URL (e.g., https://your-school.instructure.com): ").strip()
    if not canvas_url:
        print("❌ Canvas URL is required!")
        return
    
    if not canvas_url.startswith(('http://', 'https://')):
        canvas_url = 'https://' + canvas_url
    
    # Get API token
    import getpass
    api_token = getpass.getpass("Enter your Canvas API token (hidden): ").strip()
    if not api_token:
        print("❌ API token is required!")
        return
    
    # Get course ID (optional)
    course_id_input = input("Enter course ID to test (optional, press Enter to skip): ").strip()
    course_id = None
    if course_id_input:
        try:
            course_id = int(course_id_input)
        except ValueError:
            print("⚠️ Invalid course ID, skipping course-specific tests")
    
    print("\n" + "=" * 50)
    print("Running diagnostic...")
    print("=" * 50)
    
    try:
        # Run diagnostic
        diagnostic = CanvasPermissionDiagnostic(canvas_url, api_token)
        results = diagnostic.run_full_diagnostic(course_id)
        
        # Print summary
        diagnostic.print_summary()
        
        # Save report
        diagnostic.save_report()
        
        print("\n✅ Diagnostic completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
