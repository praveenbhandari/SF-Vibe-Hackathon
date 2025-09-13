#!/usr/bin/env python3
"""
Canvas API Data Retrieval Client

A Python application for retrieving data from Canvas LMS through API integration.
Supports authentication, data retrieval, error handling, and export functionality.
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path
import random
from functools import wraps
from canvas_config import CanvasConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Retry decorator function
def retry_on_failure(max_retries: int = 3):
    """Decorator for retrying failed requests with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = max_retries or getattr(self, 'max_retries', 3)
            last_exception = None
            
            for attempt in range(retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except (RateLimitError, NetworkError, RetryableError) as e:
                    last_exception = e
                    
                    if attempt == retries:
                        logger.error(f"Max retries ({retries}) exceeded for {func.__name__}")
                        raise e
                    
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
                except (AuthenticationError, CanvasAPIError) as e:
                    # Don't retry authentication or other non-retryable errors
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise e
            
            raise last_exception
        return wrapper
    return decorator

class CanvasAPIError(Exception):
    """Custom exception for Canvas API errors"""
    pass

class RateLimitError(CanvasAPIError):
    """Exception for rate limit errors"""
    pass

class AuthenticationError(CanvasAPIError):
    """Exception for authentication errors"""
    pass

class NetworkError(CanvasAPIError):
    """Exception for network-related errors"""
    pass

class RetryableError(CanvasAPIError):
    """Exception for errors that can be retried"""
    pass

class CanvasClient:
    """
    Main Canvas API client for authentication and data retrieval
    """
    
    def __init__(self, base_url: str = None, api_token: str = None, config_file: str = None):
        """
        Initialize Canvas client with enhanced configuration management
        
        Args:
            base_url: Canvas instance URL (e.g., 'https://your-school.instructure.com')
            api_token: Canvas API access token
            config_file: Path to configuration file
        """
        # Initialize configuration manager
        self.config_manager = CanvasConfig(config_file)
        
        # Use provided values or fall back to configuration
        self.base_url = base_url or self.config_manager.get('base_url')
        self.api_token = api_token or self.config_manager.get('api_token')
        
        # Load other settings from configuration
        self.requests_per_second = self.config_manager.get('rate_limit', 10)
        self.max_retries = self.config_manager.get('max_retries', 3)
        timeout = self.config_manager.get('timeout', 30)
        
        self.session = requests.Session()
        self.rate_limit_remaining = 3000
        self.rate_limit_reset = None
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.backoff_factor = 2.0
        self.jitter = True
        
        # Configure logging level based on config
        if self.config_manager.get('debug_logging', False):
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Set up session headers
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Canvas-API-Client/1.0'
            })
        
        # Set session timeout
        self.session.timeout = timeout
        
        # Initialize rate limiting
        self.last_request_time = 0
        
        # Validate configuration
        self._validate_config()
    

    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
        

    
    def _validate_config(self):
        """Validate current configuration"""
        is_valid, errors = self.config_manager.validate_config()
        
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise CanvasAPIError(error_msg)
        
        logger.info("Configuration validated successfully")
    
    def setup_config(self) -> bool:
        """Interactive configuration setup"""
        return self.config_manager.setup_interactive()
    
    def save_config(self, base_url: str = None, api_token: str = None, **kwargs) -> bool:
        """Save configuration using the configuration manager"""
        return self.config_manager.save_config(
            base_url=base_url or self.base_url,
            api_token=api_token or self.api_token,
            **kwargs
        )
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information (excluding sensitive data)"""
        return self.config_manager.export_config(include_token=False)
    
    def validate_credentials(self) -> Dict[str, Any]:
        """Validate API credentials by fetching user profile"""
        if not self.base_url or not self.api_token:
            raise AuthenticationError("Base URL and API token are required")
        
        try:
            response = self._make_request('GET', '/api/v1/users/self')
            logger.info(f"Authentication successful for user: {response.get('name')}")
            return response
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Invalid credentials: {e}")
    
    @retry_on_failure()
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Any:
        """Make HTTP request to Canvas API with enhanced error handling and retry logic"""
        if not self.base_url:
            raise CanvasAPIError("Base URL not configured")
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        try:
            # Check rate limits
            self._check_rate_limit()
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            
            # Update rate limit info from headers
            self._update_rate_limit_info(response)
            
            # Handle different response codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise AuthenticationError("Invalid or expired API token")
            elif response.status_code == 403:
                raise CanvasAPIError("Access forbidden - insufficient permissions")
            elif response.status_code == 404:
                raise CanvasAPIError("Resource not found")
            elif response.status_code == 429:
                # Rate limit exceeded - this is retryable
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limit exceeded. Retry after {wait_time} seconds")
                    time.sleep(wait_time)
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 500:
                # Server errors are retryable
                raise RetryableError(f"Server error: {response.status_code}")
            else:
                response.raise_for_status()
                return response.json() if response.content else {}
                
        except requests.exceptions.Timeout:
            raise NetworkError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Connection error - check your internet connection")
        except requests.exceptions.RequestException as e:
            if "timeout" in str(e).lower():
                raise NetworkError(f"Network timeout: {e}")
            elif "connection" in str(e).lower():
                raise NetworkError(f"Connection error: {e}")
            else:
                raise RetryableError(f"Request failed: {e}")
    
    def _check_rate_limit(self):
        """Enhanced rate limit checking with adaptive waiting"""
        current_time = time.time()
        
        # Enforce requests per second limit
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        # Check Canvas API rate limits
        if self.rate_limit_remaining <= 10:
            if self.rate_limit_reset:
                wait_time = max(0, self.rate_limit_reset - time.time())
                if wait_time > 0:
                    logger.warning(f"Canvas rate limit low ({self.rate_limit_remaining} remaining), waiting {wait_time:.1f} seconds")
                    time.sleep(wait_time)
                    # Reset our tracking after waiting
                    self.rate_limit_remaining = 1000
    
    def _update_rate_limit_info(self, response):
        """Update rate limit information from response headers"""
        # Canvas uses different header names, check for common variations
        rate_limit_headers = [
            'X-Rate-Limit-Remaining',
            'X-RateLimit-Remaining', 
            'RateLimit-Remaining'
        ]
        
        reset_headers = [
            'X-Rate-Limit-Reset',
            'X-RateLimit-Reset',
            'RateLimit-Reset'
        ]
        
        for header in rate_limit_headers:
            if header in response.headers:
                try:
                    self.rate_limit_remaining = int(response.headers[header])
                    logger.debug(f"Rate limit remaining: {self.rate_limit_remaining}")
                    break
                except ValueError:
                    continue
        
        for header in reset_headers:
            if header in response.headers:
                try:
                    self.rate_limit_reset = int(response.headers[header])
                    break
                except ValueError:
                    continue
    
    def configure_retry_settings(self, max_retries: int = 3, base_delay: float = 1.0, 
                                max_delay: float = 60.0, backoff_factor: float = 2.0, 
                                jitter: bool = True):
        """Configure retry and backoff settings"""
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        logger.info(f"Retry settings updated: max_retries={max_retries}, base_delay={base_delay}s")
    
    def configure_rate_limiting(self, requests_per_second: int = 10):
        """Configure rate limiting settings"""
        self.requests_per_second = requests_per_second
        logger.info(f"Rate limiting updated: {requests_per_second} requests/second")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get current client statistics and configuration"""
        return {
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': self.rate_limit_reset,
            'requests_per_second': self.requests_per_second,
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
            'backoff_factor': self.backoff_factor,
            'jitter_enabled': self.jitter
        }
    
    def get_courses(self, enrollment_state: str = 'active', per_page: int = 100) -> List[Dict]:
        """Retrieve courses for the authenticated user"""
        params = {
            'enrollment_state': enrollment_state,
            'per_page': per_page,
            'include[]': ['term', 'course_progress']
        }
        
        courses = []
        page = 1
        
        while True:
            params['page'] = page
            response = self._make_request('GET', '/api/v1/courses', params=params)
            
            if not response:
                break
            
            courses.extend(response)
            
            # Check if there are more pages
            if len(response) < per_page:
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(courses)} courses")
        return courses
    
    def get_course_assignments(self, course_id: int, include_submissions: bool = False) -> List[Dict]:
        """Retrieve assignments for a specific course"""
        params = {
            'per_page': 100
        }
        
        if include_submissions:
            params['include[]'] = ['submission']
        
        assignments = []
        page = 1
        
        while True:
            params['page'] = page
            response = self._make_request('GET', f'/api/v1/courses/{course_id}/assignments', params=params)
            
            if not response:
                break
            
            assignments.extend(response)
            
            if len(response) < 100:
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(assignments)} assignments for course {course_id}")
        return assignments
    
    def get_course_users(self, course_id: int, enrollment_type: str = None) -> List[Dict]:
        """Retrieve users enrolled in a specific course"""
        params = {
            'per_page': 100,
            'include[]': ['enrollments', 'email']
        }
        
        if enrollment_type:
            params['enrollment_type[]'] = enrollment_type
        
        users = []
        page = 1
        
        while True:
            params['page'] = page
            response = self._make_request('GET', f'/api/v1/courses/{course_id}/users', params=params)
            
            if not response:
                break
            
            users.extend(response)
            
            if len(response) < 100:
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(users)} users for course {course_id}")
        return users
    
    def get_course_grades(self, course_id: int) -> List[Dict]:
        """Retrieve grades for a specific course"""
        try:
            # Get enrollments with grades
            params = {
                'per_page': 100,
                'include[]': ['current_grading_period_scores', 'total_scores']
            }
            
            enrollments = []
            page = 1
            
            while True:
                params['page'] = page
                response = self._make_request('GET', f'/api/v1/courses/{course_id}/enrollments', params=params)
                
                if not response:
                    break
                
                enrollments.extend(response)
                
                if len(response) < 100:
                    break
                
                page += 1
            
            logger.info(f"Retrieved {len(enrollments)} grade records for course {course_id}")
            return enrollments
            
        except Exception as e:
            logger.error(f"Error retrieving grades for course {course_id}: {e}")
            raise CanvasAPIError(f"Failed to retrieve grades: {e}")
    
    def get_course_modules(self, course_id: int, include_items: bool = True) -> List[Dict]:
        """Retrieve modules for a specific course"""
        params = {
            'per_page': 100
        }
        
        if include_items:
            params['include[]'] = ['items']
        
        modules = []
        page = 1
        
        while True:
            params['page'] = page
            response = self._make_request('GET', f'/api/v1/courses/{course_id}/modules', params=params)
            
            if not response:
                break
            
            modules.extend(response)
            
            if len(response) < 100:
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(modules)} modules for course {course_id}")
        return modules
    
    def get_module_items(self, course_id: int, module_id: int) -> List[Dict]:
        """Retrieve items for a specific module"""
        params = {
            'per_page': 100,
            'include[]': ['content_details']
        }
        
        items = []
        page = 1
        
        while True:
            params['page'] = page
            response = self._make_request('GET', f'/api/v1/courses/{course_id}/modules/{module_id}/items', params=params)
            
            if not response:
                break
            
            items.extend(response)
            
            if len(response) < 100:
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(items)} items for module {module_id}")
        return items
    
    def get_course_files(self, course_id: int) -> List[Dict]:
        """Retrieve files for a specific course"""
        params = {
            'per_page': 100,
            'include[]': ['user']
        }
        
        files = []
        page = 1
        
        while True:
            params['page'] = page
            response = self._make_request('GET', f'/api/v1/courses/{course_id}/files', params=params)
            
            if not response:
                break
            
            files.extend(response)
            
            if len(response) < 100:
                break
            
            page += 1
        
        logger.info(f"Retrieved {len(files)} files for course {course_id}")
        return files
    
    def get_file_download_url(self, file_id: int) -> str:
        """Get download URL for a specific file"""
        response = self._make_request('GET', f'/api/v1/files/{file_id}')
        return response.get('url', '') if response else ''
    
    def download_file_content(self, file_id: int) -> tuple[bytes, str, str]:
        """Download file content directly from Canvas
        
        Returns:
            tuple: (file_content, filename, content_type)
        """
        import requests
        
        # First get file info
        file_info = self._make_request('GET', f'/api/v1/files/{file_id}')
        if not file_info:
            raise CanvasAPIError(f"File {file_id} not found")
        
        download_url = file_info.get('url')
        filename = file_info.get('display_name', f'file_{file_id}')
        content_type = file_info.get('content-type', 'application/octet-stream')
        
        if not download_url:
            raise CanvasAPIError(f"No download URL available for file {file_id}")
        
        # Download the file content
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'User-Agent': 'Canvas-API-Client/1.0'
            }
            
            response = requests.get(download_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Downloaded file {filename} ({len(response.content)} bytes)")
            return response.content, filename, content_type
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise CanvasAPIError(f"Failed to download file: {e}")
    
    def export_course_data(self, course_id: int, include_files: bool = True) -> Dict[str, Any]:
        """Export comprehensive course data to JSON format
        
        Args:
            course_id: Canvas course ID
            include_files: Whether to include file information
            
        Returns:
            Dictionary containing all course data
        """
        logger.info(f"Starting comprehensive export for course {course_id}")
        
        course_data = {
            'course_id': course_id,
            'export_timestamp': datetime.now().isoformat(),
            'assignments': [],
            'modules': [],
            'users': [],
            'files': [],
            'course_info': None
        }
        
        try:
            # Get course information
            logger.info("Fetching course information...")
            course_info = self._make_request('GET', f'/api/v1/courses/{course_id}')
            course_data['course_info'] = course_info
            
            # Get assignments
            logger.info("Fetching assignments...")
            assignments = self.get_course_assignments(course_id, include_submissions=True)
            course_data['assignments'] = assignments
            
            # Get modules with items
            logger.info("Fetching modules...")
            modules = self.get_course_modules(course_id, include_items=True)
            course_data['modules'] = modules
            
            # Get users
            logger.info("Fetching users...")
            users = self.get_course_users(course_id)
            course_data['users'] = users
            
            # Get files if requested
            if include_files:
                logger.info("Fetching files...")
                try:
                    files = self.get_course_files(course_id)
                    course_data['files'] = files
                except CanvasAPIError as e:
                    logger.warning(f"Could not fetch files: {e}")
                    course_data['files'] = []
            
            logger.info(f"Export completed for course {course_id}")
            return course_data
            
        except Exception as e:
            logger.error(f"Error exporting course {course_id}: {e}")
            raise CanvasAPIError(f"Failed to export course data: {e}")
    
    def export_all_courses_data(self, include_files: bool = True, output_dir: str = None) -> Dict[str, str]:
        """Export data for all accessible courses
        
        Args:
            include_files: Whether to include file information
            output_dir: Directory to save JSON files (optional)
            
        Returns:
            Dictionary mapping course_id to export data or file path
        """
        logger.info("Starting export for all courses")
        
        # Get all courses
        courses = self.get_courses()
        exported_courses = {}
        
        for course in courses:
            course_id = course['id']
            course_name = course.get('name', f'Course_{course_id}')
            
            try:
                logger.info(f"Exporting course: {course_name} (ID: {course_id})")
                course_data = self.export_course_data(course_id, include_files)
                
                if output_dir:
                    # Save to file
                    os.makedirs(output_dir, exist_ok=True)
                    safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"course_{course_id}_{safe_name}.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(course_data, f, indent=2, ensure_ascii=False)
                    
                    exported_courses[str(course_id)] = filepath
                    logger.info(f"Saved course data to: {filepath}")
                else:
                    # Return data directly
                    exported_courses[str(course_id)] = course_data
                
            except Exception as e:
                logger.error(f"Failed to export course {course_id} ({course_name}): {e}")
                exported_courses[str(course_id)] = f"Error: {e}"
        
        logger.info(f"Completed export for {len(courses)} courses")
        return exported_courses

if __name__ == "__main__":
    # Example usage
    client = CanvasClient()
    
    # Check if configuration exists
    if not (client.base_url and client.api_token):
        print("Canvas API client requires configuration.")
        print("Please run: python canvas_client.py auth --setup")
    else:
        try:
            user_info = client.validate_credentials()
            print(f"Successfully authenticated as: {user_info.get('name')}")
        except Exception as e:
            print(f"Authentication failed: {e}")