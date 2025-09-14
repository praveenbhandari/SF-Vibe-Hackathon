#!/usr/bin/env python3
"""
Canvas API Permission Diagnostic Tool

This tool helps diagnose Canvas API permission issues and provides guidance
on resolving them. It tests various API endpoints to identify which permissions
are missing or insufficient.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional
from canvas_client import CanvasClient, CanvasAPIError, AuthenticationError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CanvasPermissionDiagnostic:
    """Diagnostic tool for Canvas API permissions"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Canvas-Permission-Diagnostic/1.0'
        })
        
        # Test results storage
        self.results = {
            'basic_auth': False,
            'user_profile': False,
            'courses_access': False,
            'files_access': False,
            'assignments_access': False,
            'modules_access': False,
            'users_access': False,
            'enrollments_access': False,
            'permissions': {},
            'recommendations': []
        }
    
    def run_full_diagnostic(self, course_id: Optional[int] = None) -> Dict[str, Any]:
        """Run complete permission diagnostic"""
        print("🔍 Starting Canvas API Permission Diagnostic...")
        print("=" * 60)
        
        # Test 1: Basic Authentication
        self._test_basic_auth()
        
        # Test 2: User Profile Access
        self._test_user_profile()
        
        # Test 3: Courses Access
        self._test_courses_access()
        
        # Test 4: Files Access (if course_id provided)
        if course_id:
            self._test_files_access(course_id)
        
        # Test 5: Other endpoints
        if course_id:
            self._test_assignments_access(course_id)
            self._test_modules_access(course_id)
            self._test_users_access(course_id)
            self._test_enrollments_access(course_id)
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.results
    
    def _test_basic_auth(self):
        """Test basic authentication"""
        print("🔐 Testing basic authentication...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/self")
            if response.status_code == 200:
                self.results['basic_auth'] = True
                print("✅ Basic authentication successful")
            else:
                print(f"❌ Basic authentication failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Basic authentication error: {e}")
    
    def _test_user_profile(self):
        """Test user profile access"""
        print("👤 Testing user profile access...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/self")
            if response.status_code == 200:
                self.results['user_profile'] = True
                user_data = response.json()
                print(f"✅ User profile access successful: {user_data.get('name', 'Unknown')}")
            else:
                print(f"❌ User profile access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ User profile access error: {e}")
    
    def _test_courses_access(self):
        """Test courses access"""
        print("📚 Testing courses access...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses", params={'per_page': 1})
            if response.status_code == 200:
                self.results['courses_access'] = True
                courses = response.json()
                print(f"✅ Courses access successful: {len(courses)} courses found")
            else:
                print(f"❌ Courses access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Courses access error: {e}")
    
    def _test_files_access(self, course_id: int):
        """Test files access for a specific course"""
        print(f"📁 Testing files access for course {course_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/files", params={'per_page': 1})
            if response.status_code == 200:
                self.results['files_access'] = True
                files = response.json()
                print(f"✅ Files access successful: {len(files)} files found")
            elif response.status_code == 403:
                print("❌ Files access forbidden - insufficient permissions")
                self.results['permissions']['files'] = 'forbidden'
            else:
                print(f"❌ Files access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Files access error: {e}")
    
    def _test_assignments_access(self, course_id: int):
        """Test assignments access"""
        print(f"📝 Testing assignments access for course {course_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/assignments", params={'per_page': 1})
            if response.status_code == 200:
                self.results['assignments_access'] = True
                assignments = response.json()
                print(f"✅ Assignments access successful: {len(assignments)} assignments found")
            else:
                print(f"❌ Assignments access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Assignments access error: {e}")
    
    def _test_modules_access(self, course_id: int):
        """Test modules access"""
        print(f"📋 Testing modules access for course {course_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/modules", params={'per_page': 1})
            if response.status_code == 200:
                self.results['modules_access'] = True
                modules = response.json()
                print(f"✅ Modules access successful: {len(modules)} modules found")
            else:
                print(f"❌ Modules access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Modules access error: {e}")
    
    def _test_users_access(self, course_id: int):
        """Test users access"""
        print(f"👥 Testing users access for course {course_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/users", params={'per_page': 1})
            if response.status_code == 200:
                self.results['users_access'] = True
                users = response.json()
                print(f"✅ Users access successful: {len(users)} users found")
            else:
                print(f"❌ Users access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Users access error: {e}")
    
    def _test_enrollments_access(self, course_id: int):
        """Test enrollments access"""
        print(f"🎓 Testing enrollments access for course {course_id}...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/enrollments", params={'per_page': 1})
            if response.status_code == 200:
                self.results['enrollments_access'] = True
                enrollments = response.json()
                print(f"✅ Enrollments access successful: {len(enrollments)} enrollments found")
            else:
                print(f"❌ Enrollments access failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Enrollments access error: {e}")
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.results['basic_auth']:
            recommendations.append({
                'priority': 'critical',
                'issue': 'Authentication failed',
                'solution': 'Check your API token and Canvas URL. Ensure the token is valid and not expired.',
                'steps': [
                    'Go to Canvas → Account → Settings → Approved Integrations',
                    'Generate a new API token',
                    'Verify the Canvas URL is correct (e.g., https://your-school.instructure.com)'
                ]
            })
        
        if not self.results['files_access']:
            recommendations.append({
                'priority': 'high',
                'issue': 'Files access forbidden',
                'solution': 'Your API token lacks the necessary permissions to access course files.',
                'steps': [
                    'Go to Canvas → Account → Settings → Approved Integrations',
                    'Click on your existing token or create a new one',
                    'Ensure the token has the following scopes enabled:',
                    '  - /auth/userinfo (User information)',
                    '  - /auth/canvas (Canvas API access)',
                    '  - /auth/canvas/files (File access)',
                    '  - /auth/canvas/courses (Course access)',
                    'If you cannot modify scopes, contact your Canvas administrator'
                ]
            })
        
        if not self.results['courses_access']:
            recommendations.append({
                'priority': 'high',
                'issue': 'Courses access failed',
                'solution': 'Your API token cannot access course information.',
                'steps': [
                    'Verify you are enrolled in courses',
                    'Check if your institution restricts API access',
                    'Contact your Canvas administrator for API permissions'
                ]
            })
        
        if self.results['basic_auth'] and not self.results['files_access']:
            recommendations.append({
                'priority': 'medium',
                'issue': 'Partial access - files restricted',
                'solution': 'You can access basic Canvas data but not files. This is common for student accounts.',
                'steps': [
                    'Check if you have the "Files" permission in your API token',
                    'Verify you have access to the specific course files',
                    'Some institutions restrict file access via API for students',
                    'Consider using the Canvas web interface for file downloads'
                ]
            })
        
        self.results['recommendations'] = recommendations
    
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        # Basic status
        print(f"🔐 Authentication: {'✅' if self.results['basic_auth'] else '❌'}")
        print(f"👤 User Profile: {'✅' if self.results['user_profile'] else '❌'}")
        print(f"📚 Courses: {'✅' if self.results['courses_access'] else '❌'}")
        print(f"📁 Files: {'✅' if self.results['files_access'] else '❌'}")
        print(f"📝 Assignments: {'✅' if self.results['assignments_access'] else '❌'}")
        print(f"📋 Modules: {'✅' if self.results['modules_access'] else '❌'}")
        print(f"👥 Users: {'✅' if self.results['users_access'] else '❌'}")
        print(f"🎓 Enrollments: {'✅' if self.results['enrollments_access'] else '❌'}")
        
        # Recommendations
        if self.results['recommendations']:
            print("\n🔧 RECOMMENDATIONS:")
            print("-" * 40)
            
            for i, rec in enumerate(self.results['recommendations'], 1):
                priority_icon = "🚨" if rec['priority'] == 'critical' else "⚠️" if rec['priority'] == 'high' else "💡"
                print(f"\n{i}. {priority_icon} {rec['issue']}")
                print(f"   Solution: {rec['solution']}")
                print("   Steps:")
                for step in rec['steps']:
                    print(f"   • {step}")
        else:
            print("\n✅ All tests passed! Your Canvas API token has the necessary permissions.")
    
    def save_report(self, filename: str = "canvas_permission_report.json"):
        """Save diagnostic report to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved to: {filename}")

def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 3:
        print("Usage: python canvas_permission_diagnostic.py <canvas_url> <api_token> [course_id]")
        print("Example: python canvas_permission_diagnostic.py https://your-school.instructure.com your_token_here 12345")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_token = sys.argv[2]
    course_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # Run diagnostic
    diagnostic = CanvasPermissionDiagnostic(base_url, api_token)
    results = diagnostic.run_full_diagnostic(course_id)
    
    # Print summary
    diagnostic.print_summary()
    
    # Save report
    diagnostic.save_report()

if __name__ == "__main__":
    main()
