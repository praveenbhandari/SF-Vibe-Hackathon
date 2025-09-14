#!/usr/bin/env python3
"""
Canvas API Permission Validator

A utility to validate Canvas API token permissions and provide
detailed feedback on what access is available.
"""

import requests
import json
from typing import Dict, List, Any, Optional, Tuple
from canvas_client import CanvasClient, CanvasAPIError, AuthenticationError
import logging

logger = logging.getLogger(__name__)

class CanvasPermissionValidator:
    """Validates Canvas API permissions and provides detailed feedback"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Canvas-Permission-Validator/1.0'
        })
    
    def validate_all_permissions(self, course_id: Optional[int] = None) -> Dict[str, Any]:
        """Validate all available permissions"""
        results = {
            'authentication': self._validate_authentication(),
            'user_access': self._validate_user_access(),
            'courses_access': self._validate_courses_access(),
            'files_access': None,
            'assignments_access': None,
            'modules_access': None,
            'users_access': None,
            'enrollments_access': None,
            'overall_status': 'unknown',
            'recommendations': []
        }
        
        if course_id:
            results['files_access'] = self._validate_files_access(course_id)
            results['assignments_access'] = self._validate_assignments_access(course_id)
            results['modules_access'] = self._validate_modules_access(course_id)
            results['users_access'] = self._validate_users_access(course_id)
            results['enrollments_access'] = self._validate_enrollments_access(course_id)
        
        # Determine overall status
        results['overall_status'] = self._determine_overall_status(results)
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _validate_authentication(self) -> Dict[str, Any]:
        """Validate basic authentication"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/self")
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'status': 'success',
                    'message': 'Authentication successful',
                    'user': {
                        'id': user_data.get('id'),
                        'name': user_data.get('name'),
                        'email': user_data.get('email')
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Authentication failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Authentication error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_user_access(self) -> Dict[str, Any]:
        """Validate user profile access"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/self/profile")
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'message': 'User profile access successful'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'User profile access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'User profile access error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_courses_access(self) -> Dict[str, Any]:
        """Validate courses access"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses", params={'per_page': 5})
            if response.status_code == 200:
                courses = response.json()
                return {
                    'status': 'success',
                    'message': f'Courses access successful: {len(courses)} courses found',
                    'course_count': len(courses)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Courses access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Courses access error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_files_access(self, course_id: int) -> Dict[str, Any]:
        """Validate files access for a specific course"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/files", params={'per_page': 5})
            if response.status_code == 200:
                files = response.json()
                return {
                    'status': 'success',
                    'message': f'Files access successful: {len(files)} files found',
                    'file_count': len(files)
                }
            elif response.status_code == 403:
                return {
                    'status': 'forbidden',
                    'message': 'Files access forbidden - insufficient permissions',
                    'error_code': 403,
                    'troubleshooting': [
                        'Check if your API token has Files scope enabled',
                        'Verify you have access to course files',
                        'Contact your Canvas administrator for permission changes'
                    ]
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Files access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Files access error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_assignments_access(self, course_id: int) -> Dict[str, Any]:
        """Validate assignments access"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/assignments", params={'per_page': 5})
            if response.status_code == 200:
                assignments = response.json()
                return {
                    'status': 'success',
                    'message': f'Assignments access successful: {len(assignments)} assignments found',
                    'assignment_count': len(assignments)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Assignments access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Assignments access error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_modules_access(self, course_id: int) -> Dict[str, Any]:
        """Validate modules access"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/modules", params={'per_page': 5})
            if response.status_code == 200:
                modules = response.json()
                return {
                    'status': 'success',
                    'message': f'Modules access successful: {len(modules)} modules found',
                    'module_count': len(modules)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Modules access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Modules access error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_users_access(self, course_id: int) -> Dict[str, Any]:
        """Validate users access"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/users", params={'per_page': 5})
            if response.status_code == 200:
                users = response.json()
                return {
                    'status': 'success',
                    'message': f'Users access successful: {len(users)} users found',
                    'user_count': len(users)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Users access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Users access error: {str(e)}',
                'error': str(e)
            }
    
    def _validate_enrollments_access(self, course_id: int) -> Dict[str, Any]:
        """Validate enrollments access"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/courses/{course_id}/enrollments", params={'per_page': 5})
            if response.status_code == 200:
                enrollments = response.json()
                return {
                    'status': 'success',
                    'message': f'Enrollments access successful: {len(enrollments)} enrollments found',
                    'enrollment_count': len(enrollments)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Enrollments access failed: {response.status_code}',
                    'error_code': response.status_code
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Enrollments access error: {str(e)}',
                'error': str(e)
            }
    
    def _determine_overall_status(self, results: Dict[str, Any]) -> str:
        """Determine overall permission status"""
        if results['authentication']['status'] != 'success':
            return 'authentication_failed'
        
        if results['files_access'] and results['files_access']['status'] == 'forbidden':
            return 'files_restricted'
        
        if results['files_access'] and results['files_access']['status'] == 'success':
            return 'full_access'
        
        if results['courses_access']['status'] == 'success':
            return 'partial_access'
        
        return 'limited_access'
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if results['authentication']['status'] != 'success':
            recommendations.append({
                'priority': 'critical',
                'title': 'Authentication Failed',
                'description': 'Your Canvas API token is invalid or expired',
                'action': 'Generate a new API token in Canvas',
                'steps': [
                    'Go to Canvas → Account → Settings → Approved Integrations',
                    'Delete the old token and create a new one',
                    'Ensure the token is copied correctly'
                ]
            })
        
        if results['files_access'] and results['files_access']['status'] == 'forbidden':
            recommendations.append({
                'priority': 'high',
                'title': 'Files Access Restricted',
                'description': 'Your API token cannot access course files',
                'action': 'Update token permissions or contact administrator',
                'steps': [
                    'Check if your token has Files scope enabled',
                    'Verify you have access to the specific course',
                    'Contact your Canvas administrator for permission changes',
                    'Consider using Canvas web interface for file downloads'
                ]
            })
        
        if results['courses_access']['status'] != 'success':
            recommendations.append({
                'priority': 'high',
                'title': 'Courses Access Failed',
                'description': 'Cannot access course information',
                'action': 'Verify enrollment and API permissions',
                'steps': [
                    'Ensure you are enrolled in courses',
                    'Check if your institution restricts API access',
                    'Contact your Canvas administrator'
                ]
            })
        
        if results['overall_status'] == 'full_access':
            recommendations.append({
                'priority': 'info',
                'title': 'All Permissions Working',
                'description': 'Your Canvas API token has full access',
                'action': 'No action needed',
                'steps': []
            })
        
        return recommendations
    
    def print_validation_report(self, results: Dict[str, Any]):
        """Print a formatted validation report"""
        print("\n" + "=" * 60)
        print("🔍 CANVAS API PERMISSION VALIDATION REPORT")
        print("=" * 60)
        
        # Authentication status
        auth = results['authentication']
        print(f"\n🔐 Authentication: {'✅' if auth['status'] == 'success' else '❌'}")
        if auth['status'] == 'success':
            user = auth.get('user', {})
            print(f"   User: {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
        else:
            print(f"   Error: {auth['message']}")
        
        # Course access
        courses = results['courses_access']
        print(f"\n📚 Courses Access: {'✅' if courses['status'] == 'success' else '❌'}")
        if courses['status'] == 'success':
            print(f"   Found: {courses.get('course_count', 0)} courses")
        else:
            print(f"   Error: {courses['message']}")
        
        # Files access
        if results['files_access']:
            files = results['files_access']
            status_icon = '✅' if files['status'] == 'success' else '❌' if files['status'] == 'error' else '⚠️'
            print(f"\n📁 Files Access: {status_icon}")
            if files['status'] == 'success':
                print(f"   Found: {files.get('file_count', 0)} files")
            elif files['status'] == 'forbidden':
                print("   Status: Forbidden - insufficient permissions")
                print("   Troubleshooting:")
                for step in files.get('troubleshooting', []):
                    print(f"   • {step}")
            else:
                print(f"   Error: {files['message']}")
        
        # Other permissions
        for perm_name, perm_data in results.items():
            if perm_name in ['assignments_access', 'modules_access', 'users_access', 'enrollments_access'] and perm_data:
                icon = '✅' if perm_data['status'] == 'success' else '❌'
                print(f"\n📋 {perm_name.replace('_', ' ').title()}: {icon}")
                if perm_data['status'] == 'success':
                    count_key = perm_name.replace('_access', '_count')
                    count = perm_data.get(count_key, 0)
                    print(f"   Found: {count} items")
                else:
                    print(f"   Error: {perm_data['message']}")
        
        # Overall status
        print(f"\n📊 Overall Status: {results['overall_status'].replace('_', ' ').title()}")
        
        # Recommendations
        if results['recommendations']:
            print("\n🔧 RECOMMENDATIONS:")
            print("-" * 40)
            for i, rec in enumerate(results['recommendations'], 1):
                priority_icon = "🚨" if rec['priority'] == 'critical' else "⚠️" if rec['priority'] == 'high' else "💡"
                print(f"\n{i}. {priority_icon} {rec['title']}")
                print(f"   {rec['description']}")
                print(f"   Action: {rec['action']}")
                if rec['steps']:
                    print("   Steps:")
                    for step in rec['steps']:
                        print(f"   • {step}")

def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python canvas_permission_validator.py <canvas_url> <api_token> [course_id]")
        print("Example: python canvas_permission_validator.py https://your-school.instructure.com your_token_here 12345")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_token = sys.argv[2]
    course_id = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # Run validation
    validator = CanvasPermissionValidator(base_url, api_token)
    results = validator.validate_all_permissions(course_id)
    
    # Print report
    validator.print_validation_report(results)
    
    # Save report
    with open('canvas_permission_validation.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed report saved to: canvas_permission_validation.json")

if __name__ == "__main__":
    main()
