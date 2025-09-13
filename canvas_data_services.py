#!/usr/bin/env python3
"""
Canvas Data Services

Specialized services for retrieving and processing Canvas LMS data.
Provides enhanced functionality for courses, assignments, grades, and user data.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from canvas_client import CanvasClient, CanvasAPIError

logger = logging.getLogger(__name__)

class CanvasDataServices:
    """
    Enhanced data services for Canvas API operations
    """
    
    def __init__(self, client: CanvasClient):
        """
        Initialize data services with Canvas client
        
        Args:
            client: Configured CanvasClient instance
        """
        self.client = client
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_timeout:
                return data
        return None
    
    def _set_cached_data(self, cache_key: str, data: Any):
        """Store data in cache with timestamp"""
        self.cache[cache_key] = (data, datetime.now().timestamp())
    
    def get_all_courses(self, include_concluded: bool = False) -> List[Dict]:
        """
        Get all courses with enhanced filtering and information
        
        Args:
            include_concluded: Whether to include concluded courses
        
        Returns:
            List of course dictionaries with enhanced information
        """
        cache_key = f"courses_{include_concluded}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get active courses
            active_courses = self.client.get_courses(enrollment_state='active')
            
            courses = active_courses
            
            if include_concluded:
                concluded_courses = self.client.get_courses(enrollment_state='completed')
                courses.extend(concluded_courses)
            
            # Enhance course data
            enhanced_courses = []
            for course in courses:
                enhanced_course = self._enhance_course_data(course)
                enhanced_courses.append(enhanced_course)
            
            self._set_cached_data(cache_key, enhanced_courses)
            return enhanced_courses
            
        except Exception as e:
            logger.error(f"Error retrieving courses: {e}")
            raise CanvasAPIError(f"Failed to retrieve courses: {e}")
    
    def _enhance_course_data(self, course: Dict) -> Dict:
        """Enhance course data with additional computed fields"""
        enhanced = course.copy()
        
        # Add enrollment status
        enhanced['is_active'] = course.get('workflow_state') == 'available'
        
        # Parse dates
        if course.get('start_at'):
            enhanced['start_date'] = datetime.fromisoformat(course['start_at'].replace('Z', '+00:00'))
        if course.get('end_at'):
            enhanced['end_date'] = datetime.fromisoformat(course['end_at'].replace('Z', '+00:00'))
        
        # Add term information if available
        if 'term' in course:
            enhanced['term_name'] = course['term'].get('name', 'Unknown')
        
        return enhanced
    
    def get_course_details(self, course_id: int) -> Dict:
        """
        Get detailed information about a specific course
        
        Args:
            course_id: Canvas course ID
        
        Returns:
            Detailed course information
        """
        cache_key = f"course_details_{course_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get course info
            course_info = self.client._make_request('GET', f'/api/v1/courses/{course_id}', 
                                                  params={'include[]': ['term', 'course_progress', 'sections']})
            
            # Get additional statistics
            course_stats = self._get_course_statistics(course_id)
            course_info.update(course_stats)
            
            self._set_cached_data(cache_key, course_info)
            return course_info
            
        except Exception as e:
            logger.error(f"Error retrieving course details for {course_id}: {e}")
            raise CanvasAPIError(f"Failed to retrieve course details: {e}")
    
    def _get_course_statistics(self, course_id: int) -> Dict:
        """Get statistical information about a course"""
        try:
            # Get assignment count
            assignments = self.client.get_course_assignments(course_id)
            assignment_count = len(assignments)
            
            # Get user count
            users = self.client.get_course_users(course_id)
            user_count = len(users)
            
            # Calculate assignment statistics
            total_points = sum(a.get('points_possible', 0) for a in assignments if a.get('points_possible'))
            
            return {
                'assignment_count': assignment_count,
                'user_count': user_count,
                'total_points_possible': total_points,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Could not retrieve course statistics: {e}")
            return {}
    
    def get_assignments_with_details(self, course_id: int, include_submissions: bool = False) -> List[Dict]:
        """
        Get assignments with enhanced details and statistics
        
        Args:
            course_id: Canvas course ID
            include_submissions: Whether to include submission data
        
        Returns:
            List of enhanced assignment dictionaries
        """
        cache_key = f"assignments_{course_id}_{include_submissions}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            assignments = self.client.get_course_assignments(course_id, include_submissions)
            
            # Enhance assignment data
            enhanced_assignments = []
            for assignment in assignments:
                enhanced = self._enhance_assignment_data(assignment)
                enhanced_assignments.append(enhanced)
            
            self._set_cached_data(cache_key, enhanced_assignments)
            return enhanced_assignments
            
        except Exception as e:
            logger.error(f"Error retrieving assignments for course {course_id}: {e}")
            raise CanvasAPIError(f"Failed to retrieve assignments: {e}")
    
    def _enhance_assignment_data(self, assignment: Dict) -> Dict:
        """Enhance assignment data with additional computed fields"""
        enhanced = assignment.copy()
        
        # Parse due date
        if assignment.get('due_at'):
            due_date = datetime.fromisoformat(assignment['due_at'].replace('Z', '+00:00'))
            enhanced['due_date'] = due_date
            enhanced['is_overdue'] = due_date < datetime.now(due_date.tzinfo)
            enhanced['days_until_due'] = (due_date - datetime.now(due_date.tzinfo)).days
        
        # Add submission type information
        submission_types = assignment.get('submission_types', [])
        enhanced['accepts_online_upload'] = 'online_upload' in submission_types
        enhanced['accepts_text_entry'] = 'online_text_entry' in submission_types
        enhanced['accepts_url'] = 'online_url' in submission_types
        
        # Add grading information
        enhanced['is_graded'] = assignment.get('points_possible', 0) > 0
        enhanced['grading_type'] = assignment.get('grading_type', 'points')
        
        return enhanced
    
    def get_user_grades_summary(self, course_id: int) -> List[Dict]:
        """
        Get comprehensive grade summary for all users in a course
        
        Args:
            course_id: Canvas course ID
        
        Returns:
            List of user grade summaries
        """
        cache_key = f"grades_summary_{course_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get enrollments with grades
            enrollments = self.client.get_course_grades(course_id)
            
            # Get users for additional information
            users = self.client.get_course_users(course_id)
            user_lookup = {user['id']: user for user in users}
            
            # Process grade data
            grade_summaries = []
            for enrollment in enrollments:
                if enrollment.get('type') == 'StudentEnrollment':
                    user_id = enrollment.get('user_id')
                    user_info = user_lookup.get(user_id, {})
                    
                    grade_summary = {
                        'user_id': user_id,
                        'user_name': user_info.get('name', 'Unknown'),
                        'user_email': user_info.get('email', ''),
                        'enrollment_state': enrollment.get('enrollment_state'),
                        'current_score': enrollment.get('grades', {}).get('current_score'),
                        'final_score': enrollment.get('grades', {}).get('final_score'),
                        'current_grade': enrollment.get('grades', {}).get('current_grade'),
                        'final_grade': enrollment.get('grades', {}).get('final_grade'),
                        'last_activity_at': enrollment.get('last_activity_at')
                    }
                    
                    grade_summaries.append(grade_summary)
            
            self._set_cached_data(cache_key, grade_summaries)
            return grade_summaries
            
        except Exception as e:
            logger.error(f"Error retrieving grade summary for course {course_id}: {e}")
            raise CanvasAPIError(f"Failed to retrieve grade summary: {e}")
    
    def get_assignment_submissions(self, course_id: int, assignment_id: int) -> List[Dict]:
        """
        Get all submissions for a specific assignment
        
        Args:
            course_id: Canvas course ID
            assignment_id: Canvas assignment ID
        
        Returns:
            List of submission dictionaries
        """
        try:
            params = {
                'per_page': 100,
                'include[]': ['submission_comments', 'rubric_assessment', 'user']
            }
            
            submissions = []
            page = 1
            
            while True:
                params['page'] = page
                response = self.client._make_request(
                    'GET', 
                    f'/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions',
                    params=params
                )
                
                if not response:
                    break
                
                submissions.extend(response)
                
                if len(response) < 100:
                    break
                
                page += 1
            
            logger.info(f"Retrieved {len(submissions)} submissions for assignment {assignment_id}")
            return submissions
            
        except Exception as e:
            logger.error(f"Error retrieving submissions for assignment {assignment_id}: {e}")
            raise CanvasAPIError(f"Failed to retrieve submissions: {e}")
    
    def get_course_analytics(self, course_id: int) -> Dict:
        """
        Get comprehensive analytics for a course
        
        Args:
            course_id: Canvas course ID
        
        Returns:
            Dictionary containing course analytics
        """
        try:
            # Get basic course info
            course_details = self.get_course_details(course_id)
            
            # Get assignments
            assignments = self.get_assignments_with_details(course_id)
            
            # Get grade summary
            grade_summary = self.get_user_grades_summary(course_id)
            
            # Calculate analytics
            analytics = {
                'course_info': {
                    'id': course_id,
                    'name': course_details.get('name'),
                    'course_code': course_details.get('course_code'),
                    'enrollment_count': course_details.get('user_count', 0)
                },
                'assignment_analytics': self._calculate_assignment_analytics(assignments),
                'grade_analytics': self._calculate_grade_analytics(grade_summary),
                'generated_at': datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating analytics for course {course_id}: {e}")
            raise CanvasAPIError(f"Failed to generate course analytics: {e}")
    
    def _calculate_assignment_analytics(self, assignments: List[Dict]) -> Dict:
        """Calculate assignment-related analytics"""
        if not assignments:
            return {}
        
        total_assignments = len(assignments)
        graded_assignments = len([a for a in assignments if a.get('is_graded')])
        total_points = sum(a.get('points_possible', 0) for a in assignments)
        
        # Due date analysis
        now = datetime.now()
        overdue_count = len([a for a in assignments if a.get('is_overdue')])
        upcoming_count = len([a for a in assignments 
                            if a.get('due_date') and a['due_date'] > now 
                            and (a['due_date'] - now).days <= 7])
        
        return {
            'total_assignments': total_assignments,
            'graded_assignments': graded_assignments,
            'total_points_possible': total_points,
            'overdue_assignments': overdue_count,
            'upcoming_assignments': upcoming_count,
            'average_points_per_assignment': total_points / total_assignments if total_assignments > 0 else 0
        }
    
    def _calculate_grade_analytics(self, grade_summary: List[Dict]) -> Dict:
        """Calculate grade-related analytics"""
        if not grade_summary:
            return {}
        
        # Filter out None scores
        current_scores = [g['current_score'] for g in grade_summary 
                         if g.get('current_score') is not None]
        final_scores = [g['final_score'] for g in grade_summary 
                       if g.get('final_score') is not None]
        
        analytics = {
            'total_students': len(grade_summary),
            'students_with_grades': len(current_scores)
        }
        
        if current_scores:
            analytics.update({
                'average_current_score': sum(current_scores) / len(current_scores),
                'highest_current_score': max(current_scores),
                'lowest_current_score': min(current_scores)
            })
        
        if final_scores:
            analytics.update({
                'average_final_score': sum(final_scores) / len(final_scores),
                'highest_final_score': max(final_scores),
                'lowest_final_score': min(final_scores)
            })
        
        return analytics
    
    def search_courses(self, search_term: str) -> List[Dict]:
        """Search courses by name or course code"""
        try:
            all_courses = self.get_all_courses(include_concluded=True)
            
            search_term = search_term.lower()
            matching_courses = []
            
            for course in all_courses:
                course_name = course.get('name', '').lower()
                course_code = course.get('course_code', '').lower()
                
                if search_term in course_name or search_term in course_code:
                    matching_courses.append(course)
            
            logger.info(f"Found {len(matching_courses)} courses matching '{search_term}'")
            return matching_courses
            
        except Exception as e:
            logger.error(f"Error searching courses: {e}")
            raise CanvasAPIError(f"Failed to search courses: {e}")