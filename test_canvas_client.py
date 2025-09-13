#!/usr/bin/env python3
"""
Canvas API Client Test Script

Simple test script to verify Canvas API client functionality.
Run this after setting up your configuration to test the connection.
"""

import sys
import logging
from canvas_client import CanvasClient, CanvasAPIError, AuthenticationError
from canvas_data_services import CanvasDataServices
from canvas_export import CanvasExporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_authentication():
    """Test Canvas API authentication"""
    print("\n=== Testing Canvas API Authentication ===")
    
    try:
        client = CanvasClient()
        user_info = client.validate_credentials()
        
        print(f"✅ Authentication successful!")
        print(f"   User: {user_info.get('name', 'Unknown')}")
        print(f"   Email: {user_info.get('email', 'Unknown')}")
        print(f"   ID: {user_info.get('id', 'Unknown')}")
        
        return client
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPlease check your Canvas API token and base URL.")
        return None
    except CanvasAPIError as e:
        print(f"❌ Canvas API error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_courses(client):
    """Test course retrieval"""
    print("\n=== Testing Course Retrieval ===")
    
    try:
        data_services = CanvasDataServices(client)
        courses = data_services.get_courses_with_details()
        
        print(f"✅ Retrieved {len(courses)} courses")
        
        if courses:
            print("\nFirst few courses:")
            for i, course in enumerate(courses[:3]):
                print(f"   {i+1}. {course.get('name', 'Unnamed Course')} (ID: {course.get('id')})")
        
        return courses
        
    except Exception as e:
        print(f"❌ Failed to retrieve courses: {e}")
        return []

def test_export(courses):
    """Test export functionality"""
    print("\n=== Testing Export Functionality ===")
    
    if not courses:
        print("⚠️  No courses to export")
        return
    
    try:
        exporter = CanvasExporter()
        
        # Test CSV export
        csv_file = "test_courses.csv"
        exporter.export_to_csv(courses, csv_file)
        print(f"✅ Exported courses to {csv_file}")
        
        # Test JSON export
        json_file = "test_courses.json"
        exporter.export_to_json(courses, json_file)
        print(f"✅ Exported courses to {json_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

def test_client_stats(client):
    """Test client statistics"""
    print("\n=== Client Statistics ===")
    
    try:
        stats = client.get_client_stats()
        print(f"Rate limit remaining: {stats.get('rate_limit_remaining')}")
        print(f"Requests per second: {stats.get('requests_per_second')}")
        print(f"Max retries: {stats.get('max_retries')}")
        print(f"Jitter enabled: {stats.get('jitter_enabled')}")
        
        config_info = client.get_config_info()
        print(f"\nConfiguration:")
        print(f"Base URL: {config_info.get('base_url')}")
        print(f"Rate limit: {config_info.get('rate_limit')}")
        print(f"Debug logging: {config_info.get('debug_logging')}")
        
    except Exception as e:
        print(f"❌ Failed to get client stats: {e}")

def main():
    """Main test function"""
    print("Canvas API Client Test Suite")
    print("=============================")
    
    # Test authentication
    client = test_authentication()
    if not client:
        print("\n❌ Cannot proceed without valid authentication.")
        print("\nTo set up your configuration, run:")
        print("   python canvas_config.py")
        print("or")
        print("   python canvas_cli.py")
        sys.exit(1)
    
    # Test courses
    courses = test_courses(client)
    
    # Test export
    test_export(courses)
    
    # Test client stats
    test_client_stats(client)
    
    print("\n=== Test Summary ===")
    print("✅ All tests completed successfully!")
    print("\nYour Canvas API client is ready to use.")
    print("\nNext steps:")
    print("1. Run 'python canvas_cli.py' for interactive usage")
    print("2. Import modules in your own scripts")
    print("3. Check the README.md for detailed usage instructions")

if __name__ == "__main__":
    main()