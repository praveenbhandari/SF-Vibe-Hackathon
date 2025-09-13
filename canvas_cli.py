#!/usr/bin/env python3
"""
Canvas CLI - Command Line Interface for Canvas API Data Retrieval

Provides a comprehensive command-line interface for interacting with Canvas LMS API.
Supports authentication, data retrieval, analytics, and export functionality.
"""

import argparse
import sys
import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Import our modules
from canvas_client import CanvasClient, CanvasAPIError, AuthenticationError, RateLimitError
from canvas_data_services import CanvasDataServices
from canvas_export import CanvasExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('canvas_cli.log')
    ]
)
logger = logging.getLogger(__name__)

class CanvasCLI:
    """
    Main CLI application class
    """
    
    def __init__(self):
        self.client = None
        self.data_services = None
        self.exporter = CanvasExporter()
        self.config_file = 'canvas_config.json'
    
    def setup_client(self, base_url: str = None, api_token: str = None) -> bool:
        """
        Setup Canvas client with authentication
        
        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.client = CanvasClient(base_url=base_url, api_token=api_token, config_file=self.config_file)
            
            # Validate credentials
            user_info = self.client.validate_credentials()
            self.data_services = CanvasDataServices(self.client)
            
            print(f"✅ Successfully authenticated as: {user_info.get('name')} ({user_info.get('email')})")
            return True
            
        except AuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def configure_auth(self, args):
        """Configure Canvas authentication"""
        print("🔧 Canvas API Configuration")
        print("=" * 40)
        
        if args.interactive or not (args.url and args.token):
            # Interactive configuration
            base_url = input("Enter your Canvas instance URL (e.g., https://your-school.instructure.com): ").strip()
            api_token = input("Enter your Canvas API token: ").strip()
        else:
            # Command line arguments
            base_url = args.url
            api_token = args.token
        
        if not base_url or not api_token:
            print("❌ Both URL and API token are required")
            return False
        
        # Ensure URL format
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"
        
        try:
            # Test configuration
            test_client = CanvasClient(base_url=base_url, api_token=api_token)
            user_info = test_client.validate_credentials()
            
            # Save configuration
            test_client.save_config(base_url, api_token)
            
            print(f"✅ Configuration saved successfully!")
            print(f"   Authenticated as: {user_info.get('name')} ({user_info.get('email')})")
            print(f"   Institution: {base_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Configuration failed: {e}")
            return False
    
    def list_courses(self, args):
        """List all accessible courses"""
        if not self._ensure_authenticated():
            return
        
        try:
            print("📚 Retrieving courses...")
            courses = self.data_services.get_all_courses(include_concluded=args.include_concluded)
            
            if not courses:
                print("No courses found.")
                return
            
            print(f"\n📋 Found {len(courses)} courses:")
            print("=" * 80)
            
            for course in courses:
                status = "✅" if course.get('is_active') else "⏸️"
                print(f"{status} [{course['id']}] {course['name']}")
                if course.get('course_code'):
                    print(f"    Code: {course['course_code']}")
                if course.get('term_name'):
                    print(f"    Term: {course['term_name']}")
                if course.get('user_count'):
                    print(f"    Students: {course['user_count']}")
                print()
            
            # Export if requested
            if args.export:
                self._export_data(courses, 'courses', args.format)
                
        except Exception as e:
            print(f"❌ Error retrieving courses: {e}")
            logger.error(f"Error in list_courses: {e}")
    
    def get_course_info(self, args):
        """Get detailed information about a specific course"""
        if not self._ensure_authenticated():
            return
        
        try:
            print(f"📖 Retrieving course information for ID: {args.course_id}")
            course_details = self.data_services.get_course_details(args.course_id)
            
            print(f"\n📋 Course Details:")
            print("=" * 50)
            print(f"Name: {course_details.get('name')}")
            print(f"Code: {course_details.get('course_code')}")
            print(f"Status: {course_details.get('workflow_state')}")
            print(f"Students: {course_details.get('user_count', 'N/A')}")
            print(f"Assignments: {course_details.get('assignment_count', 'N/A')}")
            
            if course_details.get('start_at'):
                print(f"Start Date: {course_details['start_at']}")
            if course_details.get('end_at'):
                print(f"End Date: {course_details['end_at']}")
            
            # Export if requested
            if args.export:
                self._export_data([course_details], 'course_details', args.format)
                
        except Exception as e:
            print(f"❌ Error retrieving course information: {e}")
            logger.error(f"Error in get_course_info: {e}")
    
    def list_assignments(self, args):
        """List assignments for a course"""
        if not self._ensure_authenticated():
            return
        
        try:
            print(f"📝 Retrieving assignments for course ID: {args.course_id}")
            assignments = self.data_services.get_assignments_with_details(
                args.course_id, 
                include_submissions=args.include_submissions
            )
            
            if not assignments:
                print("No assignments found.")
                return
            
            print(f"\n📋 Found {len(assignments)} assignments:")
            print("=" * 80)
            
            for assignment in assignments:
                status = "⚠️" if assignment.get('is_overdue') else "📝"
                print(f"{status} [{assignment['id']}] {assignment['name']}")
                
                if assignment.get('due_at'):
                    print(f"    Due: {assignment['due_at']}")
                if assignment.get('points_possible'):
                    print(f"    Points: {assignment['points_possible']}")
                if assignment.get('submission_types'):
                    types = ', '.join(assignment['submission_types'])
                    print(f"    Submission Types: {types}")
                print()
            
            # Export if requested
            if args.export:
                self._export_data(assignments, 'assignments', args.format)
                
        except Exception as e:
            print(f"❌ Error retrieving assignments: {e}")
            logger.error(f"Error in list_assignments: {e}")
    
    def get_grades(self, args):
        """Get grade summary for a course"""
        if not self._ensure_authenticated():
            return
        
        try:
            print(f"📊 Retrieving grades for course ID: {args.course_id}")
            grade_summary = self.data_services.get_user_grades_summary(args.course_id)
            
            if not grade_summary:
                print("No grade data found.")
                return
            
            print(f"\n📋 Grade Summary ({len(grade_summary)} students):")
            print("=" * 80)
            
            # Calculate statistics
            current_scores = [g['current_score'] for g in grade_summary if g.get('current_score') is not None]
            
            if current_scores:
                avg_score = sum(current_scores) / len(current_scores)
                print(f"Average Score: {avg_score:.2f}%")
                print(f"Highest Score: {max(current_scores):.2f}%")
                print(f"Lowest Score: {min(current_scores):.2f}%")
                print()
            
            # Show individual grades if requested
            if args.detailed:
                for grade in grade_summary:
                    print(f"👤 {grade['user_name']}")
                    print(f"    Email: {grade.get('user_email', 'N/A')}")
                    print(f"    Current Score: {grade.get('current_score', 'N/A')}%")
                    print(f"    Final Score: {grade.get('final_score', 'N/A')}%")
                    print(f"    Current Grade: {grade.get('current_grade', 'N/A')}")
                    print()
            
            # Export if requested
            if args.export:
                self._export_data(grade_summary, 'grades', args.format)
                
        except Exception as e:
            print(f"❌ Error retrieving grades: {e}")
            logger.error(f"Error in get_grades: {e}")
    
    def get_course_analytics(self, args):
        """Generate comprehensive course analytics"""
        if not self._ensure_authenticated():
            return
        
        try:
            print(f"📈 Generating analytics for course ID: {args.course_id}")
            analytics = self.data_services.get_course_analytics(args.course_id)
            
            print(f"\n📊 Course Analytics Report")
            print("=" * 50)
            
            # Course info
            course_info = analytics.get('course_info', {})
            print(f"Course: {course_info.get('name')}")
            print(f"Code: {course_info.get('course_code')}")
            print(f"Enrolled Students: {course_info.get('enrollment_count')}")
            print()
            
            # Assignment analytics
            assignment_analytics = analytics.get('assignment_analytics', {})
            if assignment_analytics:
                print("📝 Assignment Statistics:")
                print(f"  Total Assignments: {assignment_analytics.get('total_assignments', 0)}")
                print(f"  Graded Assignments: {assignment_analytics.get('graded_assignments', 0)}")
                print(f"  Total Points: {assignment_analytics.get('total_points_possible', 0)}")
                print(f"  Overdue Assignments: {assignment_analytics.get('overdue_assignments', 0)}")
                print(f"  Upcoming Assignments: {assignment_analytics.get('upcoming_assignments', 0)}")
                print()
            
            # Grade analytics
            grade_analytics = analytics.get('grade_analytics', {})
            if grade_analytics:
                print("📊 Grade Statistics:")
                print(f"  Total Students: {grade_analytics.get('total_students', 0)}")
                print(f"  Students with Grades: {grade_analytics.get('students_with_grades', 0)}")
                if grade_analytics.get('average_current_score'):
                    print(f"  Average Score: {grade_analytics['average_current_score']:.2f}%")
                    print(f"  Highest Score: {grade_analytics.get('highest_current_score', 0):.2f}%")
                    print(f"  Lowest Score: {grade_analytics.get('lowest_current_score', 0):.2f}%")
            
            # Export analytics
            if args.export:
                course_name = course_info.get('name', f"course_{args.course_id}")
                exported_files = self.exporter.export_course_analytics(analytics, course_name)
                print(f"\n📁 Analytics exported to:")
                for format_type, file_path in exported_files.items():
                    print(f"  {format_type.upper()}: {file_path}")
                
        except Exception as e:
            print(f"❌ Error generating analytics: {e}")
            logger.error(f"Error in get_course_analytics: {e}")
    
    def search_courses(self, args):
        """Search courses by name or code"""
        if not self._ensure_authenticated():
            return
        
        try:
            print(f"🔍 Searching courses for: '{args.query}'")
            matching_courses = self.data_services.search_courses(args.query)
            
            if not matching_courses:
                print("No matching courses found.")
                return
            
            print(f"\n📋 Found {len(matching_courses)} matching courses:")
            print("=" * 80)
            
            for course in matching_courses:
                status = "✅" if course.get('is_active') else "⏸️"
                print(f"{status} [{course['id']}] {course['name']}")
                if course.get('course_code'):
                    print(f"    Code: {course['course_code']}")
                print()
            
            # Export if requested
            if args.export:
                self._export_data(matching_courses, 'search_results', args.format)
                
        except Exception as e:
            print(f"❌ Error searching courses: {e}")
            logger.error(f"Error in search_courses: {e}")
    
    def show_export_summary(self, args):
        """Show summary of exported files"""
        try:
            summary = self.exporter.get_export_summary()
            
            print("📁 Export Summary")
            print("=" * 40)
            print(f"Export Directory: {summary['export_directory']}")
            print(f"Total Files: {summary['total_files']}")
            print()
            
            if summary['files_by_type']:
                print("Files by Type:")
                for file_type, count in summary['files_by_type'].items():
                    print(f"  {file_type}: {count} files")
                print()
            
            if summary['recent_exports']:
                print("Recent Exports:")
                for export in summary['recent_exports'][:5]:
                    size_mb = export['size_bytes'] / (1024 * 1024)
                    print(f"  📄 {export['filename']} ({size_mb:.2f} MB)")
                    print(f"      Modified: {export['modified']}")
                    print()
                    
        except Exception as e:
            print(f"❌ Error getting export summary: {e}")
            logger.error(f"Error in show_export_summary: {e}")
    
    def _ensure_authenticated(self) -> bool:
        """Ensure client is authenticated"""
        if not self.client:
            if not self.setup_client():
                print("❌ Authentication required. Run: python canvas_cli.py auth --setup")
                return False
        return True
    
    def _export_data(self, data: List[Dict], data_type: str, format_type: str = 'csv'):
        """Export data in specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{data_type}_{timestamp}"
            
            if format_type.lower() == 'csv':
                file_path = self.exporter.export_to_csv(data, filename, data_type)
            elif format_type.lower() == 'json':
                file_path = self.exporter.export_to_json(data, filename)
            elif format_type.lower() in ['excel', 'xlsx']:
                file_path = self.exporter.export_to_excel(data, filename, data_type)
            else:
                print(f"❌ Unsupported export format: {format_type}")
                return
            
            print(f"✅ Data exported to: {file_path}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            logger.error(f"Export error: {e}")

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Canvas API Data Retrieval Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python canvas_cli.py auth --setup
  python canvas_cli.py courses --list
  python canvas_cli.py assignments --course-id 12345
  python canvas_cli.py grades --course-id 12345 --export --format excel
  python canvas_cli.py analytics --course-id 12345 --export
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Configure authentication')
    auth_parser.add_argument('--setup', action='store_true', help='Setup Canvas API credentials')
    auth_parser.add_argument('--url', help='Canvas instance URL')
    auth_parser.add_argument('--token', help='Canvas API token')
    auth_parser.add_argument('--interactive', action='store_true', help='Interactive configuration')
    
    # Courses command
    courses_parser = subparsers.add_parser('courses', help='Course operations')
    courses_parser.add_argument('--list', action='store_true', help='List all courses')
    courses_parser.add_argument('--info', action='store_true', help='Get course details')
    courses_parser.add_argument('--course-id', type=int, help='Course ID')
    courses_parser.add_argument('--include-concluded', action='store_true', help='Include concluded courses')
    courses_parser.add_argument('--export', action='store_true', help='Export data')
    courses_parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='Export format')
    
    # Assignments command
    assignments_parser = subparsers.add_parser('assignments', help='Assignment operations')
    assignments_parser.add_argument('--course-id', type=int, required=True, help='Course ID')
    assignments_parser.add_argument('--include-submissions', action='store_true', help='Include submission data')
    assignments_parser.add_argument('--export', action='store_true', help='Export data')
    assignments_parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='Export format')
    
    # Grades command
    grades_parser = subparsers.add_parser('grades', help='Grade operations')
    grades_parser.add_argument('--course-id', type=int, required=True, help='Course ID')
    grades_parser.add_argument('--detailed', action='store_true', help='Show detailed grade information')
    grades_parser.add_argument('--export', action='store_true', help='Export data')
    grades_parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='Export format')
    
    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Course analytics')
    analytics_parser.add_argument('--course-id', type=int, required=True, help='Course ID')
    analytics_parser.add_argument('--export', action='store_true', help='Export analytics')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search courses')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--export', action='store_true', help='Export results')
    search_parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='Export format')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export operations')
    export_parser.add_argument('--summary', action='store_true', help='Show export summary')
    
    return parser

def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = CanvasCLI()
    
    try:
        if args.command == 'auth':
            if args.setup or args.url or args.token or args.interactive:
                cli.configure_auth(args)
            else:
                print("Use --setup for interactive configuration or provide --url and --token")
        
        elif args.command == 'courses':
            if args.list:
                cli.list_courses(args)
            elif args.info and args.course_id:
                cli.get_course_info(args)
            else:
                print("Use --list to list courses or --info --course-id <id> for course details")
        
        elif args.command == 'assignments':
            cli.list_assignments(args)
        
        elif args.command == 'grades':
            cli.get_grades(args)
        
        elif args.command == 'analytics':
            cli.get_course_analytics(args)
        
        elif args.command == 'search':
            cli.search_courses(args)
        
        elif args.command == 'export':
            if args.summary:
                cli.show_export_summary(args)
            else:
                print("Use --summary to show export summary")
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()