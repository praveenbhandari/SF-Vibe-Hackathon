#!/usr/bin/env python3
"""
Test script to check Canvas API token permissions
"""

import sys
import json
from canvas_client import CanvasClient

def test_token_permissions(base_url, api_token, course_id=None):
    """Test various Canvas API endpoints to check permissions"""
    
    try:
        client = CanvasClient(base_url=base_url, api_token=api_token)
        
        print("Testing Canvas API Token Permissions")
        print("=" * 50)
        
        # Test 1: Validate credentials
        print("\n1. Testing credential validation...")
        try:
            user_info = client.validate_credentials()
            print(f"✅ SUCCESS: Authenticated as {user_info.get('name')} (ID: {user_info.get('id')})")
            print(f"   Email: {user_info.get('email', 'N/A')}")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return
        
        # Test 2: Get courses
        print("\n2. Testing course access...")
        try:
            courses = client.get_courses()
            print(f"✅ SUCCESS: Found {len(courses)} courses")
            if courses:
                print("   Sample courses:")
                for course in courses[:3]:
                    print(f"   - {course.get('name')} (ID: {course.get('id')})")
                    if not course_id:
                        course_id = course.get('id')  # Use first course for testing
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return
        
        if not course_id and courses:
            course_id = courses[0].get('id')
        
        if course_id:
            # Test 3: Get course files
            print(f"\n3. Testing file access for course {course_id}...")
            try:
                files = client.get_course_files(course_id)
                print(f"✅ SUCCESS: Found {len(files)} files")
                if files:
                    print("   Sample files:")
                    for file_item in files[:3]:
                        print(f"   - {file_item.get('display_name')} (ID: {file_item.get('id')})")
                        print(f"     Size: {file_item.get('size', 0)} bytes")
                        print(f"     Type: {file_item.get('content-type', 'unknown')}")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                print("   This is likely the source of the permission error!")
                
                # Check if it's a specific permission issue
                error_str = str(e).lower()
                if 'forbidden' in error_str or '403' in error_str:
                    print("\n🔍 DIAGNOSIS: 403 Forbidden Error")
                    print("   Possible causes:")
                    print("   - API token lacks 'Files' permission scope")
                    print("   - Token doesn't have access to this specific course")
                    print("   - Course files are restricted by instructor")
                    print("   - Institution has disabled file access via API")
                elif 'unauthorized' in error_str or '401' in error_str:
                    print("\n🔍 DIAGNOSIS: 401 Unauthorized Error")
                    print("   Possible causes:")
                    print("   - API token has expired")
                    print("   - Token is invalid or revoked")
                else:
                    print(f"\n🔍 DIAGNOSIS: Other error - {e}")
            
            # Test 4: Get course assignments (for comparison)
            print(f"\n4. Testing assignment access for course {course_id}...")
            try:
                assignments = client.get_course_assignments(course_id)
                print(f"✅ SUCCESS: Found {len(assignments)} assignments")
            except Exception as e:
                print(f"❌ FAILED: {e}")
            
            # Test 5: Get course users (for comparison)
            print(f"\n5. Testing user access for course {course_id}...")
            try:
                users = client.get_course_users(course_id)
                print(f"✅ SUCCESS: Found {len(users)} users")
            except Exception as e:
                print(f"❌ FAILED: {e}")
        
        print("\n" + "=" * 50)
        print("Permission test completed!")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        return

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_permissions.py <base_url> <api_token> [course_id]")
        print("Example: python test_permissions.py https://canvas.example.edu your_token_here 12345")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_token = sys.argv[2]
    course_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    test_token_permissions(base_url, api_token, course_id)