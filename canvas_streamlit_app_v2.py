#!/usr/bin/env python3
"""
Canvas LMS Streamlit App V2

A web interface for Canvas LMS that focuses on accessible data:
- Assignments and due dates
- Course modules and content
- Course information
- User data
- Assignment submissions (if available)
"""

import streamlit as st
import os
import json
import requests
from pathlib import Path
from datetime import datetime
import zipfile
import io
from typing import List, Dict, Any, Optional
import logging
import pandas as pd
import re
import time
from urllib.parse import urlparse, unquote, parse_qs
import glob
import tempfile
import sys

from canvas_client import CanvasClient
from canvas_config import CanvasConfig

# Add MESA-Hackathon modules to path
sys.path.append(str(Path(__file__).parent / "MESA-Hackathon-main" / "src"))

# Import MESA-Hackathon components
try:
    from pipelines.text_extraction_pipeline import TextExtractionPipeline
    from utils.ingest import ingest_documents
    from utils.retrieval import mmr_retrieve
    from utils.rag_llm import answer_with_context
    from utils.notes import generate_notes_from_text, iter_generate_notes_from_texts
    MESA_AVAILABLE = True
except ImportError as e:
    MESA_AVAILABLE = False
    st.warning(f"MESA-Hackathon components not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Canvas LMS Course Explorer",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .course-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .assignment-card {
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .module-card {
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .due-date {
        color: #ff6b35;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class CanvasFileDownloader:
    """Download files from Canvas course JSON exports"""
    
    def __init__(self, api_token: str = None, base_url: str = None, output_dir: str = "downloads", dry_run: bool = False):
        """
        Initialize the downloader
        
        Args:
            api_token: Canvas API token (optional, for authenticated requests)
            base_url: Canvas base URL (optional)
            output_dir: Directory to save downloaded files
            dry_run: If True, only show what would be downloaded without downloading
        """
        self.api_token = api_token
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.session = requests.Session()
        
        # Set up session headers if token provided
        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_token}',
                'User-Agent': 'Canvas-File-Downloader/1.0'
            })
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0,
            'external_urls': 0
        }
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename or 'unnamed_file'
    
    def get_filename_from_url(self, url: str, default_name: str = None) -> str:
        """Extract filename from URL"""
        try:
            parsed = urlparse(url)
            filename = os.path.basename(unquote(parsed.path))
            if filename and '.' in filename:
                return self.sanitize_filename(filename)
        except Exception:
            pass
        
        return self.sanitize_filename(default_name or 'downloaded_file')
    
    def download_file(self, url: str, filename: str, course_dir: Path, progress_callback=None) -> bool:
        """Download a single file with improved error handling
        
        Args:
            url: URL to download from
            filename: Suggested filename
            course_dir: Directory to save the file
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create course directory if it doesn't exist
            course_dir.mkdir(parents=True, exist_ok=True)
            
            # Get filename from URL if not provided
            if not filename or filename == 'unknown_file':
                filename = self.get_filename_from_url(url)
            
            # Sanitize filename
            safe_filename = self.sanitize_filename(filename)
            filepath = course_dir / safe_filename
            
            # Skip if file already exists
            if filepath.exists():
                if progress_callback:
                    progress_callback(f"File already exists, skipping: {safe_filename}")
                self.stats['skipped'] += 1
                return True
            
            if progress_callback:
                progress_callback(f"{'[DRY RUN] Would download' if self.dry_run else 'Downloading'}: {safe_filename}")
            
            # In dry-run mode, just simulate the download
            if self.dry_run:
                self.stats['downloaded'] += 1
                return True
            
            # Download with timeout and streaming
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check content type for potential issues
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type and not filename.endswith('.html'):
                if progress_callback:
                    progress_callback(f"Warning: Received HTML content for {filename}, might be an error page")
            
            # Write file in chunks with verification
            temp_filepath = filepath.with_suffix(filepath.suffix + '.tmp')
            total_size = 0
            
            with open(temp_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            # Verify download completed successfully
            if total_size == 0:
                if progress_callback:
                    progress_callback(f"Error: Downloaded file is empty: {safe_filename}")
                temp_filepath.unlink()
                self.stats['errors'] += 1
                return False
            
            # Move temp file to final location
            temp_filepath.rename(filepath)
            
            if progress_callback:
                progress_callback(f"Downloaded: {safe_filename} ({total_size} bytes)")
            self.stats['downloaded'] += 1
            return True
            
        except requests.exceptions.RequestException as e:
            if progress_callback:
                progress_callback(f"Network error downloading {filename}: {e}")
            self.stats['errors'] += 1
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error downloading {filename}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_module_items(self, items: List[Dict], course_dir: Path, progress_callback=None) -> None:
        """Process module items and download content"""
        for item in items:
            self.stats['total_files'] += 1
            
            title = item.get('title', 'Untitled')
            item_type = item.get('type', 'Unknown')
            
            # Process different types of URLs
            if 'url' in item and item['url']:
                url = item['url']
                
                if item_type == 'File' or 'files' in url:
                    # Canvas file
                    filename = item.get('display_name', title)
                    self.download_file(url, filename, course_dir, progress_callback)
            
            elif 'external_url' in item and item['external_url']:
                url = item['external_url']
                
                if 'drive.google.com' in url:
                    # Google Drive file
                    self.process_google_drive_url(url, title, course_dir, progress_callback)
    
    def process_google_drive_url(self, url: str, title: str, course_dir: Path, progress_callback=None) -> bool:
        """Process Google Drive URL and attempt direct download"""
        try:
            # Convert Google Drive view URL to download URL
            if '/file/d/' in url and '/view' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                
                if progress_callback:
                    progress_callback(f"Converting Google Drive URL for: {title}")
                return self.download_file(download_url, f"{title}.pdf", course_dir, progress_callback)
            else:
                # Save as link if can't convert
                return self.process_external_url(url, title, course_dir, progress_callback)
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error processing Google Drive URL {title}: {e}")
            return self.process_external_url(url, title, course_dir, progress_callback)
    
    def process_external_url(self, url: str, title: str, course_dir: Path, progress_callback=None) -> bool:
        """Process external URL (save link info)"""
        try:
            # For external URLs, save a link file
            safe_filename = self.sanitize_filename(f"{title}_link.txt")
            filepath = course_dir / safe_filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Saved: {datetime.now().isoformat()}\n")
            
            if progress_callback:
                progress_callback(f"Saved external link: {safe_filename}")
            self.stats['external_urls'] += 1
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error saving external URL {title}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_course_files(self, files: List[Dict], course_dir: Path, progress_callback=None) -> None:
        """Process course files list"""
        files_dir = course_dir / "course_files"
        
        for file_info in files:
            self.stats['total_files'] += 1
            
            filename = file_info.get('display_name', file_info.get('filename', 'unknown_file'))
            file_url = file_info.get('url')
            
            if file_url:
                self.download_file(file_url, filename, files_dir, progress_callback)
    
    def process_json_export(self, json_file: str, progress_callback=None) -> None:
        """Process a single JSON export file"""
        try:
            if progress_callback:
                progress_callback(f"Processing JSON export: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            # Handle both old and new export formats
            if 'course_data' in course_data:
                # New format with metadata
                actual_data = course_data['course_data']
                course_info = actual_data.get('course_info', {})
            else:
                # Old format
                actual_data = course_data
                course_info = actual_data.get('course_info', {})
            
            course_name = course_info.get('name', f"Course_{actual_data.get('course_id', 'Unknown')}")
            course_id = actual_data.get('course_id', 'unknown')
            
            # Create course directory
            safe_course_name = self.sanitize_filename(course_name)
            course_dir = self.output_dir / f"course_{course_id}_{safe_course_name}"
            
            if progress_callback:
                progress_callback(f"Processing course: {course_name} (ID: {course_id})")
            
            # Process modules and their items
            modules = actual_data.get('modules', [])
            for module in modules:
                module_name = module.get('name', 'Unnamed Module')
                if progress_callback:
                    progress_callback(f"Processing module: {module_name}")
                
                items = module.get('items', [])
                if items:
                    module_dir = course_dir / self.sanitize_filename(module_name)
                    self.process_module_items(items, module_dir, progress_callback)
            
            # Process course files
            files = actual_data.get('files', [])
            if files:
                if progress_callback:
                    progress_callback(f"Processing {len(files)} course files")
                self.process_course_files(files, course_dir, progress_callback)
            
            if progress_callback:
                progress_callback(f"Completed processing: {course_name}")
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error processing JSON file {json_file}: {e}")
            self.stats['errors'] += 1


class CanvasCourseExplorer:
    """Canvas LMS Course Explorer with focus on accessible data"""
    
    def __init__(self):
        self.client = None
        self.config_manager = CanvasConfig()
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'courses' not in st.session_state:
            st.session_state.courses = []
        if 'selected_course' not in st.session_state:
            st.session_state.selected_course = None
        if 'course_data' not in st.session_state:
            st.session_state.course_data = {}
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">📚 Canvas LMS Course Explorer</h1>', unsafe_allow_html=True)
        st.markdown("---")
    
    def render_login_section(self):
        """Render the login section"""
        st.sidebar.header("🔐 Authentication")
        
        # Check if already authenticated
        if st.session_state.authenticated:
            st.sidebar.success("✅ Authenticated")
            if st.session_state.user_info:
                st.sidebar.write(f"**User:** {st.session_state.user_info.get('name', 'Unknown')}")
                st.sidebar.write(f"**ID:** {st.session_state.user_info.get('id', 'Unknown')}")
            
            if st.sidebar.button("🚪 Logout", type="secondary"):
                self.logout()
            return True
        
        # Login form
        with st.sidebar.form("login_form"):
            st.write("Enter your Canvas credentials:")
            
            canvas_url = st.text_input(
                "Canvas URL",
                value=self.config_manager.get('base_url', ''),
                placeholder="https://your-school.instructure.com",
                help="Your Canvas instance URL"
            )
            
            api_token = st.text_input(
                "API Token",
                type="password",
                placeholder="Enter your Canvas API token",
                help="Get this from Account → Settings → Approved Integrations"
            )
            
            submitted = st.form_submit_button("🔑 Login", type="primary")
            
            if submitted:
                if canvas_url and api_token:
                    self.login(canvas_url, api_token)
                else:
                    st.error("Please enter both Canvas URL and API token")
        
        # Instructions
        with st.sidebar.expander("ℹ️ How to get API token"):
            st.markdown("""
            1. Log into your Canvas account
            2. Go to **Account** → **Settings**
            3. Scroll down to **Approved Integrations**
            4. Click **+ New Access Token**
            5. Give it a name and generate
            6. Copy the token and paste it here
            """)
        
        return False
    
    def login(self, canvas_url: str, api_token: str):
        """Handle login process"""
        try:
            with st.spinner("Authenticating..."):
                # Create client with provided credentials
                self.client = CanvasClient(base_url=canvas_url, api_token=api_token)
                
                # Validate credentials
                user_info = self.client.validate_credentials()
                
                # Save configuration
                self.config_manager.save_config(
                    base_url=canvas_url,
                    api_token=api_token
                )
                
                # Update session state
                st.session_state.authenticated = True
                st.session_state.user_info = user_info
                st.session_state.client = self.client
                
                st.success(f"✅ Successfully authenticated as {user_info.get('name')}")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Authentication failed: {str(e)}")
            logger.error(f"Login error: {e}")
    
    def logout(self):
        """Handle logout process"""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.courses = []
        st.session_state.selected_course = None
        st.session_state.course_data = {}
        st.session_state.client = None
        st.rerun()
    
    def load_courses(self):
        """Load courses from Canvas"""
        if not st.session_state.authenticated or not st.session_state.client:
            return
        
        try:
            with st.spinner("Loading courses..."):
                courses = st.session_state.client.get_courses()
                st.session_state.courses = courses
                st.success(f"✅ Loaded {len(courses)} courses")
        except Exception as e:
            st.error(f"❌ Failed to load courses: {str(e)}")
            logger.error(f"Load courses error: {e}")
    
    def load_course_data(self, course_id: int):
        """Load comprehensive course data"""
        if not st.session_state.client:
            return {}
        
        try:
            with st.spinner("Loading course data..."):
                course_data = {
                    'assignments': [],
                    'modules': [],
                    'users': [],
                    'announcements': []
                }
                
                # Load assignments
                try:
                    assignments = st.session_state.client.get_course_assignments(course_id)
                    course_data['assignments'] = assignments
                except Exception as e:
                    logger.warning(f"Could not load assignments: {e}")
                
                # Load modules
                try:
                    modules = st.session_state.client.get_course_modules(course_id, include_items=True)
                    course_data['modules'] = modules
                except Exception as e:
                    logger.warning(f"Could not load modules: {e}")
                
                # Load course files
                try:
                    files = st.session_state.client.get_course_files(course_id)
                    course_data['files'] = files
                except Exception as e:
                    logger.warning(f"Could not load files: {e}")
                
                # Load users
                try:
                    users = st.session_state.client.get_course_users(course_id)
                    course_data['users'] = users
                except Exception as e:
                    logger.warning(f"Could not load users: {e}")
                
                # Load announcements
                try:
                    announcements = []
                    page = 1
                    per_page = 50
                    
                    while True:
                        params = {
                            'per_page': per_page,
                            'page': page,
                            'context_codes[]': f'course_{course_id}'
                        }
                        
                        response = st.session_state.client._make_request(
                            'GET', 
                            '/api/v1/announcements', 
                            params=params
                        )
                        
                        if not response:
                            break
                        
                        announcements.extend(response)
                        
                        if len(response) < per_page:
                            break
                        
                        page += 1
                    
                    course_data['announcements'] = announcements
                except Exception as e:
                    logger.warning(f"Could not load announcements: {e}")
                
                return course_data
                
        except Exception as e:
            st.error(f"❌ Failed to load course data: {str(e)}")
            logger.error(f"Load course data error: {e}")
            return {}
    
    def render_course_selection(self):
        """Render course selection interface"""
        if not st.session_state.authenticated:
            return
        
        st.header("📚 Course Selection")
        
        # Load courses button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Refresh Courses", type="primary"):
                self.load_courses()
        
        with col2:
            if st.session_state.courses:
                st.success(f"Found {len(st.session_state.courses)} courses")
        
        # Course selection
        if st.session_state.courses:
            course_options = {
                f"{course.get('name', 'Unknown')} (ID: {course.get('id')})": course
                for course in st.session_state.courses
            }
            
            selected_course_name = st.selectbox(
                "Select a course:",
                options=list(course_options.keys()),
                index=0
            )
            
            if selected_course_name:
                st.session_state.selected_course = course_options[selected_course_name]
                # Load course data when course is selected
                if st.session_state.selected_course:
                    course_id = st.session_state.selected_course.get('id')
                    st.session_state.course_data = self.load_course_data(course_id)
        else:
            st.info("Click 'Refresh Courses' to load your courses")
    
    def render_course_overview(self):
        """Render course overview and statistics"""
        if not st.session_state.selected_course:
            return
        
        course = st.session_state.selected_course
        course_data = st.session_state.course_data
        
        st.header(f"📖 {course.get('name', 'Unknown Course')}")
        
        # Course information
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Assignments", len(course_data.get('assignments', [])))
        with col2:
            st.metric("Modules", len(course_data.get('modules', [])))
        with col3:
            st.metric("Files", len(course_data.get('files', [])))
        with col4:
            st.metric("Users", len(course_data.get('users', [])))
        with col5:
            st.metric("Announcements", len(course_data.get('announcements', [])))
        
        # Course details
        with st.expander("📋 Course Details"):
            st.write(f"**Course ID:** {course.get('id')}")
            st.write(f"**Course Code:** {course.get('course_code', 'N/A')}")
            st.write(f"**Term:** {course.get('term', {}).get('name', 'N/A')}")
            st.write(f"**Start Date:** {course.get('start_at', 'N/A')}")
            st.write(f"**End Date:** {course.get('end_at', 'N/A')}")
    
    def render_assignments_section(self):
        """Render assignments section"""
        if not st.session_state.course_data.get('assignments'):
            return
        
        st.header("📝 Assignments")
        
        assignments = st.session_state.course_data['assignments']
        
        # Assignment filters
        col1, col2 = st.columns([1, 1])
        
        with col1:
            show_completed = st.checkbox("Show completed assignments", value=True)
        
        with col2:
            sort_by = st.selectbox("Sort by", ["Due Date", "Name", "Points"])
        
        # Filter and sort assignments
        filtered_assignments = assignments.copy()
        
        if not show_completed:
            filtered_assignments = [a for a in filtered_assignments if not a.get('has_submitted_submissions', False)]
        
        if sort_by == "Due Date":
            filtered_assignments.sort(key=lambda x: x.get('due_at') or '9999-12-31')
        elif sort_by == "Name":
            filtered_assignments.sort(key=lambda x: x.get('name', ''))
        elif sort_by == "Points":
            filtered_assignments.sort(key=lambda x: x.get('points_possible') or 0, reverse=True)
        
        # Display assignments
        for assignment in filtered_assignments:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{assignment.get('name', 'No name')}**")
                    if assignment.get('description'):
                        st.write(assignment.get('description')[:200] + "..." if len(assignment.get('description', '')) > 200 else assignment.get('description'))
                
                with col2:
                    due_date = assignment.get('due_at')
                    if due_date:
                        try:
                            # Format the date nicely
                            from datetime import datetime
                            dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d')
                            st.write(f"**Due:** {formatted_date}")
                        except:
                            st.write(f"**Due:** {due_date[:10]}")
                    else:
                        st.write("**Due:** No due date")
                
                with col3:
                    points = assignment.get('points_possible')
                    if points is not None:
                        st.write(f"**Points:** {points}")
                    else:
                        st.write("**Points:** N/A")
                
                st.markdown("---")
    
    def render_modules_section(self):
        """Render modules section with file download functionality"""
        if not st.session_state.course_data.get('modules'):
            return
        
        st.header("📚 Course Modules")
        
        modules = st.session_state.course_data['modules']
        
        for module in modules:
            with st.expander(f"📁 {module.get('name', 'Unnamed Module')}"):
                st.write(f"**Description:** {module.get('description', 'No description')}")
                st.write(f"**Items:** {len(module.get('items', []))}")
                
                # Show module items
                items = module.get('items', [])
                if items:
                    st.write("**Module Items:**")
                    for item in items:
                        item_type = item.get('type', 'Unknown')
                        item_title = item.get('title', 'Untitled')
                        item_url = item.get('html_url', '')
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if item_url:
                                st.markdown(f"- **{item_type}**: [{item_title}]({item_url})")
                            else:
                                st.write(f"- **{item_type}**: {item_title}")
                        
                        with col2:
                            # Add download button for file items
                            if item_type == 'File' and item.get('content_id'):
                                try:
                                    file_id = item.get('content_id')
                                    if st.button("📥 Download", key=f"download_module_{file_id}"):
                                        with st.spinner("Downloading file..."):
                                            file_content, filename, content_type = st.session_state.client.download_file_content(file_id)
                                            st.download_button(
                                                label="📥 Click to save file",
                                                data=file_content,
                                                file_name=filename,
                                                mime=content_type,
                                                key=f"save_module_{file_id}"
                                            )
                                except Exception as e:
                                     st.write("❌ Download unavailable")
    
    def render_files_section(self):
        """Render course files section with download functionality"""
        if not st.session_state.course_data.get('files'):
            return
        
        st.header("📁 Course Files")
        
        files = st.session_state.course_data['files']
        
        # File filters
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Filter by file type
            file_types = list(set([f.get('content-type', 'Unknown').split('/')[0] for f in files]))
            selected_type = st.selectbox("Filter by type:", ['All'] + file_types)
        
        with col2:
            # Search files
            search_term = st.text_input("Search files:", placeholder="Enter filename...")
        
        # Filter files
        filtered_files = files.copy()
        
        if selected_type != 'All':
            filtered_files = [f for f in filtered_files if f.get('content-type', '').startswith(selected_type)]
        
        if search_term:
            filtered_files = [f for f in filtered_files if search_term.lower() in f.get('display_name', '').lower()]
        
        # Display files
        if filtered_files:
            st.write(f"**Found {len(filtered_files)} files:**")
            
            for file_info in filtered_files:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        file_name = file_info.get('display_name', 'Unknown')
                        file_size = file_info.get('size', 0)
                        file_type = file_info.get('content-type', 'Unknown')
                        
                        # Format file size
                        if file_size > 1024 * 1024:
                            size_str = f"{file_size / (1024 * 1024):.1f} MB"
                        elif file_size > 1024:
                            size_str = f"{file_size / 1024:.1f} KB"
                        else:
                            size_str = f"{file_size} B"
                        
                        st.write(f"**{file_name}**")
                        st.caption(f"Type: {file_type} | Size: {size_str}")
                    
                    with col2:
                        # View button
                        if file_info.get('url'):
                            st.markdown(f"[👁️ View]({file_info.get('url')})")
                    
                    with col3:
                        # Download button
                        try:
                            file_id = file_info.get('id')
                            if file_id:
                                if st.button("📥 Download", key=f"download_file_{file_id}"):
                                    with st.spinner("Downloading file..."):
                                        file_content, filename, content_type = st.session_state.client.download_file_content(file_id)
                                        st.download_button(
                                            label="📥 Click to save file",
                                            data=file_content,
                                            file_name=filename,
                                            mime=content_type,
                                            key=f"save_file_{file_id}"
                                        )
                            else:
                                st.write("❌ Unavailable")
                        except Exception as e:
                            st.write("❌ Error")
                    
                    st.divider()
        else:
            st.info("No files found matching your criteria.")
    
    def render_export_section(self):
        """Render data export section"""
        st.header("📊 Export Data")
        
        # Batch export section
        st.subheader("🚀 Batch Export All Courses")
        st.write("Export comprehensive JSON data for all your courses at once.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📦 Export All Courses", type="primary"):
                self.batch_export_all_courses()
        
        with col2:
            export_format = st.selectbox(
                "Export Format",
                ["Individual JSON files", "Single ZIP file"],
                help="Choose how to package the exported data"
            )
        
        with col3:
            include_files = st.checkbox(
                "Include file metadata",
                value=True,
                help="Include course files information in exports"
            )
        
        st.divider()
        
        # Single course export section
        if st.session_state.course_data:
            st.subheader("📄 Current Course Export")
            
            course = st.session_state.selected_course
            course_name = course.get('name', 'Unknown') if course else 'Unknown'
            course_data = st.session_state.course_data
            
            # Export options
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("📄 Export Current Course to JSON"):
                    self.export_to_json(course_data, course_name, course.get('id') if course else None)
            
            with col2:
                if st.button("📊 Export Assignments to CSV"):
                    if course_data.get('assignments'):
                        self.export_assignments_to_csv(course_data['assignments'], course_name)
                    else:
                        st.warning("No assignments to export")
        else:
            st.info("Select a course to enable single course export options.")
    
    def render_download_section(self):
        """Render the download section for downloading files from JSON exports"""
        st.header("⬇️ Download Files from JSON Exports")
        st.write("Upload JSON export files and download course materials")
        
        # Initialize session state for downloads
        if 'download_progress' not in st.session_state:
            st.session_state.download_progress = []
        if 'download_stats' not in st.session_state:
            st.session_state.download_stats = {}
        
        # File upload section
        st.subheader("📁 Select JSON Files")
        
        # Option 1: Upload files
        uploaded_files = st.file_uploader(
            "Upload JSON export files",
            type=['json'],
            accept_multiple_files=True,
            help="Upload one or more JSON export files from the Export tab"
        )
        
        # Option 2: Select from exports directory
        export_files = []
        if self.export_dir.exists():
            export_files = list(self.export_dir.glob("*.json"))
        
        if export_files:
            st.subheader("📂 Or Select from Exports Directory")
            selected_export_files = st.multiselect(
                "Select from existing exports:",
                options=export_files,
                format_func=lambda x: x.name
            )
        else:
            selected_export_files = []
        
        # Download options
        st.subheader("⚙️ Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            dry_run = st.checkbox(
                "Dry Run Mode",
                value=False,
                help="Preview what would be downloaded without actually downloading"
            )
            
            use_api_token = st.checkbox(
                "Use API Token for Downloads",
                value=True,
                help="Use your Canvas API token for authenticated downloads"
            )
        
        with col2:
            download_dir = st.text_input(
                "Download Directory",
                value="downloads",
                help="Directory where files will be saved"
            )
            
            max_concurrent = st.slider(
                "Max Concurrent Downloads",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of files to download simultaneously"
            )
        
        # Process files
        files_to_process = []
        
        # Add uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Save uploaded file temporarily
                temp_path = self.export_dir / uploaded_file.name
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                files_to_process.append(temp_path)
        
        # Add selected export files
        files_to_process.extend(selected_export_files)
        
        if files_to_process:
            st.subheader("📋 Files to Process")
            for file_path in files_to_process:
                st.write(f"• {file_path.name}")
            
            # Download button
            if st.button("🚀 Start Download", type="primary", use_container_width=True):
                self.start_download_process(files_to_process, download_dir, dry_run, use_api_token)
        
        # Display progress and results
        if st.session_state.download_progress:
            st.subheader("📊 Download Progress")
            
            # Create progress container
            progress_container = st.container()
            
            with progress_container:
                # Show recent progress messages
                for message in st.session_state.download_progress[-10:]:
                    st.text(message)
                
                # Show statistics if available
                if st.session_state.download_stats:
                    stats = st.session_state.download_stats
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Files", stats.get('total_files', 0))
                    
                    with col2:
                        st.metric("Downloaded", stats.get('downloaded', 0))
                    
                    with col3:
                        st.metric("Skipped", stats.get('skipped', 0))
                    
                    with col4:
                        st.metric("Errors", stats.get('errors', 0))
        
        # Clear progress button
        if st.session_state.download_progress:
            if st.button("🗑️ Clear Progress"):
                st.session_state.download_progress = []
                st.session_state.download_stats = {}
                st.rerun()
    
    def start_download_process(self, files_to_process: List[Path], download_dir: str, dry_run: bool, use_api_token: bool):
        """Start the download process for selected files"""
        try:
            # Clear previous progress
            st.session_state.download_progress = []
            st.session_state.download_stats = {}
            
            # Get API token if requested
            api_token = None
            base_url = None
            
            if use_api_token and self.client:
                api_token = self.client.api_token
                base_url = self.client.base_url
            
            # Initialize downloader
            downloader = CanvasFileDownloader(
                api_token=api_token,
                base_url=base_url,
                output_dir=download_dir,
                dry_run=dry_run
            )
            
            # Progress callback function
            def progress_callback(message: str):
                st.session_state.download_progress.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
                # Keep only last 100 messages to prevent memory issues
                if len(st.session_state.download_progress) > 100:
                    st.session_state.download_progress = st.session_state.download_progress[-100:]
            
            progress_callback(f"Starting download process for {len(files_to_process)} files...")
            progress_callback(f"Mode: {'Dry Run' if dry_run else 'Download'}")
            progress_callback(f"Output Directory: {download_dir}")
            
            # Process each JSON file
            for json_file in files_to_process:
                progress_callback(f"Processing: {json_file.name}")
                downloader.process_json_export(str(json_file), progress_callback)
            
            # Update statistics
            st.session_state.download_stats = downloader.stats.copy()
            
            progress_callback("Download process completed!")
            progress_callback(f"Summary: {downloader.stats['downloaded']} downloaded, {downloader.stats['skipped']} skipped, {downloader.stats['errors']} errors")
            
            # Show completion message
            if dry_run:
                st.success(f"✅ Dry run completed! Would have processed {downloader.stats['total_files']} files.")
            else:
                st.success(f"✅ Download completed! {downloader.stats['downloaded']} files downloaded.")
            
            # Rerun to update the display
            st.rerun()
            
        except Exception as e:
            error_msg = f"Error during download process: {str(e)}"
            st.session_state.download_progress.append(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {error_msg}")
            st.error(error_msg)
            logging.error(f"Download process error: {e}", exc_info=True)
    
    def batch_export_all_courses(self):
        """Export all courses data to JSON files"""
        if not st.session_state.authenticated or not st.session_state.client:
            st.error("Please authenticate first")
            return
        
        try:
            with st.spinner("Exporting all courses data..."):
                # Get all courses if not already loaded
                if not st.session_state.courses:
                    st.session_state.courses = st.session_state.client.get_courses()
                
                export_files = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_courses = len(st.session_state.courses)
                
                for i, course in enumerate(st.session_state.courses):
                    course_id = course.get('id')
                    course_name = course.get('name', f'Course_{course_id}')
                    
                    status_text.text(f"Exporting: {course_name}")
                    
                    try:
                        # Use the enhanced export method from canvas_client
                        course_data = st.session_state.client.export_course_data(course_id)
                        
                        # Save to file
                        safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_name = safe_name.replace(' ', '_')
                        filename = f"course_{course_id}_{safe_name}.json"
                        filepath = self.export_dir / filename
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(course_data, f, indent=2, ensure_ascii=False)
                        
                        export_files.append(filepath)
                        logger.info(f"Exported course: {course_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to export course {course_name}: {e}")
                        st.warning(f"⚠️ Failed to export: {course_name}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / total_courses)
                
                status_text.text("Export completed!")
                
                if export_files:
                    st.success(f"✅ Successfully exported {len(export_files)} courses")
                    
                    # Create ZIP file for download
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for filepath in export_files:
                            zip_file.write(filepath, filepath.name)
                    
                    zip_buffer.seek(0)
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download All Exports (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"canvas_courses_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
                    
                    # Show individual files
                    with st.expander("📁 Individual Export Files"):
                        for filepath in export_files:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"📄 {filepath.name}")
                            with col2:
                                with open(filepath, 'rb') as f:
                                    st.download_button(
                                        label="📥",
                                        data=f.read(),
                                        file_name=filepath.name,
                                        mime="application/json",
                                        key=f"download_{filepath.stem}"
                                    )
                else:
                    st.error("❌ No courses were successfully exported")
                    
        except Exception as e:
            st.error(f"❌ Batch export failed: {str(e)}")
            logger.error(f"Batch export error: {e}")
    
    def export_to_json(self, data: Dict[str, Any], course_name: str, course_id: int = None):
        """Export data to JSON file"""
        try:
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            if course_id:
                filename = f"course_{course_id}_{safe_name}.json"
            else:
                filename = f"{safe_name}_course_data.json"
            
            filepath = self.export_dir / filename
            
            # Add metadata to the export
            export_data = {
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'course_name': course_name,
                    'course_id': course_id,
                    'export_version': '2.0'
                },
                'course_data': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Data exported to {filepath}")
            
            # Provide download link
            with open(filepath, 'rb') as f:
                st.download_button(
                    label="📥 Download JSON File",
                    data=f.read(),
                    file_name=filename,
                    mime="application/json"
                )
                
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
    def export_assignments_to_csv(self, assignments: List[Dict], course_name: str):
        """Export assignments to CSV"""
        try:
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            filename = f"{safe_name}_assignments.csv"
            filepath = self.export_dir / filename
            
            # Convert to DataFrame
            df = pd.DataFrame(assignments)
            
            # Select relevant columns
            columns_to_keep = ['name', 'due_at', 'points_possible', 'description', 'created_at']
            available_columns = [col for col in columns_to_keep if col in df.columns]
            
            if available_columns:
                df_export = df[available_columns]
                df_export.to_csv(filepath, index=False)
                
                st.success(f"✅ Assignments exported to {filepath}")
                
                # Provide download link
                with open(filepath, 'rb') as f:
                    st.download_button(
                        label="📥 Download CSV File",
                        data=f.read(),
                        file_name=filename,
                        mime="text/csv"
                    )
            else:
                st.warning("No suitable columns found for export")
                
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
    def render_ai_notes_section(self):
        """Render AI Notes section with MESA-Hackathon integration"""
        st.header("🤖 AI-Powered Note Generation")
        
        if not MESA_AVAILABLE:
            st.error("❌ MESA-Hackathon components are not available. Please ensure the MESA-Hackathon-main folder is properly integrated.")
            return
        
        # Check for downloaded course files
        course_id = st.session_state.selected_course['id']
        course_name = st.session_state.selected_course['name']
        
        # Look for course files in downloads directory
        course_pattern = f"course_{course_id}_*"
        course_dirs = list(self.download_dir.glob(course_pattern))
        
        if not course_dirs:
            st.warning("⚠️ No downloaded course files found. Please download course files first using the Download tab.")
            
            # Provide quick download option
            if st.button("📥 Quick Download Course Files"):
                st.info("Redirecting to Download tab...")
                st.rerun()
            return
        
        # Course file selection
        st.subheader("📁 Select Course Files for Note Generation")
        
        selected_course_dir = st.selectbox(
            "Choose course directory:",
            course_dirs,
            format_func=lambda x: x.name
        )
        
        if selected_course_dir:
            # Find all text-based files
            supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
            all_files = []
            
            for ext in supported_extensions:
                all_files.extend(selected_course_dir.rglob(f'*{ext}'))
            
            if not all_files:
                st.warning("No supported files found in the selected course directory.")
                return
            
            # File selection
            selected_files = st.multiselect(
                "Select files to process:",
                all_files,
                format_func=lambda x: f"{x.parent.name}/{x.name}"
            )
            
            if selected_files:
                # AI Settings
                st.subheader("⚙️ AI Settings")
                
                col1, col2 = st.columns(2)
                with col1:
                    embed_model = st.text_input("Embedding model", value="all-MiniLM-L6-v2")
                    top_k = st.number_input("Top K", min_value=1, max_value=20, value=5)
                
                with col2:
                    backend = st.selectbox("LLM Backend", options=["groq (OpenAI-compatible)", "openai", "ollama"], index=0)
                    notes_title = st.text_input("Notes Title (optional)", value=f"{course_name} - AI Generated Notes")
                
                # Backend-specific settings
                if backend.startswith("groq"):
                    st.caption("Uses GROQ_API_KEY from environment")
                    groq_key = st.text_input("GROQ_API_KEY (optional)", type="password")
                    groq_model = st.text_input("GROQ_MODEL (optional)", value=os.getenv("GROQ_MODEL", ""))
                    
                    if groq_key:
                        os.environ["GROQ_API_KEY"] = groq_key
                    if groq_model:
                        os.environ["GROQ_MODEL"] = groq_model
                    os.environ["LLM_BACKEND"] = "groq"
                    
                elif backend == "openai":
                    st.caption("Uses OPENAI_API_KEY from environment")
                    openai_key = st.text_input("OPENAI_API_KEY (optional)", type="password")
                    openai_model = st.text_input("OPENAI_MODEL", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
                    
                    if openai_key:
                        os.environ["OPENAI_API_KEY"] = openai_key
                    if openai_model:
                        os.environ["OPENAI_MODEL"] = openai_model
                    os.environ["LLM_BACKEND"] = "openai"
                    
                else:
                    st.caption("Requires local ollama service")
                    os.environ["LLM_BACKEND"] = "ollama"
                
                # Processing options
                st.subheader("📝 Processing Options")
                col1, col2 = st.columns(2)
                with col1:
                    chunk_size = st.number_input("Chunk size", min_value=400, max_value=4000, value=1200, step=100)
                with col2:
                    group_size = st.number_input("Chunks per group", min_value=1, max_value=10, value=3)
                
                # Process files
                if st.button("🚀 Generate AI Notes", type="primary"):
                    self.process_files_for_notes(selected_files, notes_title, embed_model, top_k, chunk_size, group_size)
    
    def process_files_for_notes(self, files: List[Path], title: str, embed_model: str, top_k: int, chunk_size: int, group_size: int):
        """Process selected files and generate AI notes"""
        try:
            with st.spinner("Processing files and generating notes..."):
                # Initialize text extraction pipeline
                pipe = TextExtractionPipeline()
                
                # Extract text from files
                extraction_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file_path in enumerate(files):
                    status_text.text(f"Extracting text from: {file_path.name}")
                    
                    try:
                        result = pipe.extract_from_file(str(file_path))
                        if result.get('success'):
                            extraction_results.append(result)
                    except Exception as e:
                        st.warning(f"Failed to extract from {file_path.name}: {e}")
                    
                    progress_bar.progress((i + 1) / len(files))
                
                if not extraction_results:
                    st.error("❌ No files were successfully processed")
                    return
                
                status_text.text("Ingesting documents into vector store...")
                
                # Ingest documents
                vector_store = ingest_documents(extraction_results, model_name=embed_model)
                
                status_text.text("Generating AI notes...")
                
                # Generate notes
                # Get all text chunks from the extraction results
                all_texts = []
                for result in extraction_results:
                    if 'text' in result:
                        all_texts.append(result['text'])
                
                if all_texts:
                    # Generate notes section by section
                    st.subheader("📝 Generated Notes")
                    
                    notes_container = st.container()
                    sections = []
                    
                    with notes_container:
                        placeholder = st.empty()
                        
                        for idx, section in enumerate(iter_generate_notes_from_texts(all_texts, title=title, group_size=group_size), 1):
                            sections.append(section)
                            
                            with placeholder.container():
                                for i, s in enumerate(sections, 1):
                                    with st.expander(f"Section {i}", expanded=(i == idx)):
                                        st.markdown(s)
                    
                    # Save notes to file
                    if sections:
                        combined_notes = "\n\n---\n\n".join(sections)
                        
                        # Create notes directory
                        notes_dir = self.download_dir / "ai_notes"
                        notes_dir.mkdir(exist_ok=True)
                        
                        # Save notes
                        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_title = safe_title.replace(' ', '_')
                        notes_filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                        notes_filepath = notes_dir / notes_filename
                        
                        with open(notes_filepath, 'w', encoding='utf-8') as f:
                            f.write(f"# {title}\n\n")
                            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            f.write(f"Source files: {', '.join([f.name for f in files])}\n\n")
                            f.write("---\n\n")
                            f.write(combined_notes)
                        
                        st.success(f"✅ Notes saved to: {notes_filepath}")
                        
                        # Provide download button
                        with open(notes_filepath, 'rb') as f:
                            st.download_button(
                                label="📥 Download Notes (Markdown)",
                                data=f.read(),
                                file_name=notes_filename,
                                mime="text/markdown"
                            )
                
                status_text.text("Notes generation completed!")
                
        except Exception as e:
            st.error(f"❌ Error generating notes: {str(e)}")
            logger.error(f"Notes generation error: {e}")
    
    def check_course_files_availability(self, course_id: int) -> Dict[str, Any]:
        """Check if course files are available in downloads directory"""
        course_pattern = f"course_{course_id}_*"
        course_dirs = list(self.download_dir.glob(course_pattern))
        
        if not course_dirs:
            return {
                'available': False,
                'directories': [],
                'file_count': 0
            }
        
        total_files = 0
        for course_dir in course_dirs:
            # Count supported files
            supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
            for ext in supported_extensions:
                total_files += len(list(course_dir.rglob(f'*{ext}')))
        
        return {
            'available': True,
            'directories': course_dirs,
            'file_count': total_files
        }
    
    def render_enhanced_download_section(self):
        """Enhanced download section with file availability checking"""
        st.header("📥 Course File Downloads")
        
        course_id = st.session_state.selected_course['id']
        course_name = st.session_state.selected_course['name']
        
        # Check file availability
        file_status = self.check_course_files_availability(course_id)
        
        # Status display
        col1, col2, col3 = st.columns(3)
        with col1:
            if file_status['available']:
                st.success(f"✅ Files Available")
            else:
                st.warning("⚠️ No Files Downloaded")
        
        with col2:
            st.metric("Downloaded Directories", len(file_status['directories']))
        
        with col3:
            st.metric("Total Files", file_status['file_count'])
        
        # Show existing downloads if available
        if file_status['available']:
            st.subheader("📁 Existing Downloads")
            
            for course_dir in file_status['directories']:
                with st.expander(f"📂 {course_dir.name}", expanded=False):
                    # Show directory contents
                    supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
                    files_found = []
                    
                    for ext in supported_extensions:
                        files_found.extend(course_dir.rglob(f'*{ext}'))
                    
                    if files_found:
                        st.write(f"**Found {len(files_found)} supported files:**")
                        for file_path in files_found[:10]:  # Show first 10 files
                            relative_path = file_path.relative_to(course_dir)
                            st.write(f"• {relative_path}")
                        
                        if len(files_found) > 10:
                            st.write(f"... and {len(files_found) - 10} more files")
                        
                        # Quick action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"🤖 Generate AI Notes", key=f"ai_notes_{course_dir.name}"):
                                st.info("Switching to AI Notes tab...")
                                st.rerun()
                        
                        with col2:
                            if st.button(f"📂 Open Folder", key=f"open_{course_dir.name}"):
                                st.info(f"Folder location: {course_dir}")
                    else:
                        st.write("No supported files found in this directory.")
            
            st.divider()
        
        # Download new files section
        st.subheader("📥 Download Course Files")
        
        if not file_status['available']:
            st.info("💡 **Recommended**: Download course files to enable AI note generation and offline access.")
        
        # Initialize downloader
        if 'downloader' not in st.session_state:
            st.session_state.downloader = CanvasFileDownloader(
                canvas_client=st.session_state.canvas_client,
                download_dir=self.download_dir
            )
        
        downloader = st.session_state.downloader
        
        # Download options
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Download Options:**")
            download_files = st.checkbox("📄 Course Files", value=True)
            download_modules = st.checkbox("📚 Module Content", value=True)
            download_assignments = st.checkbox("📝 Assignment Files", value=False)
        
        with col2:
            st.write("**Settings:**")
            dry_run = st.checkbox("🔍 Dry Run (Preview Only)", value=False)
            organize_by_type = st.checkbox("📁 Organize by File Type", value=True)
            max_file_size = st.number_input("Max File Size (MB)", min_value=1, max_value=500, value=100)
        
        # Custom download directory
        custom_dir = st.text_input(
            "Custom Download Directory (optional):",
            placeholder=str(self.download_dir)
        )
        
        if custom_dir:
            download_dir = Path(custom_dir)
        else:
            download_dir = self.download_dir
        
        # Download button
        if st.button("🚀 Start Download", type="primary"):
            if not any([download_files, download_modules, download_assignments]):
                st.error("❌ Please select at least one download option.")
                return
            
            # Update downloader settings
            downloader.download_dir = download_dir
            downloader.max_file_size_mb = max_file_size
            
            # Start download process
            with st.spinner("Preparing download..."):
                try:
                    # Create progress containers
                    progress_container = st.container()
                    log_container = st.container()
                    
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        stats_container = st.empty()
                    
                    # Download course content
                    course = st.session_state.selected_course
                    
                    if dry_run:
                        status_text.text("🔍 Running dry run - no files will be downloaded")
                        st.info("Dry run mode: This will show what would be downloaded without actually downloading files.")
                    
                    # Process downloads
                    total_downloaded = 0
                    total_failed = 0
                    downloaded_files = []
                    failed_downloads = []
                    
                    if download_files:
                        status_text.text("📄 Processing course files...")
                        try:
                            result = downloader.download_course_files(
                                course_id=course['id'],
                                course_name=course['name'],
                                dry_run=dry_run,
                                organize_by_type=organize_by_type
                            )
                            total_downloaded += result.get('downloaded', 0)
                            total_failed += result.get('failed', 0)
                            downloaded_files.extend(result.get('files', []))
                            failed_downloads.extend(result.get('failed_files', []))
                        except Exception as e:
                            st.error(f"Error downloading course files: {e}")
                        
                        progress_bar.progress(0.33)
                    
                    if download_modules:
                        status_text.text("📚 Processing module content...")
                        try:
                            # Get modules
                            modules = list(st.session_state.canvas_client.get_course(course['id']).get_modules())
                            
                            for i, module in enumerate(modules):
                                module_items = list(module.get_module_items())
                                for item in module_items:
                                    if hasattr(item, 'url') and item.url:
                                        # Process module item
                                        try:
                                            downloader.process_module_item(
                                                item,
                                                course['id'],
                                                course['name'],
                                                module.name,
                                                dry_run=dry_run
                                            )
                                            total_downloaded += 1
                                        except Exception as e:
                                            total_failed += 1
                                            failed_downloads.append(f"Module item: {item.title} - {str(e)}")
                                
                                # Update progress
                                progress = 0.33 + (0.33 * (i + 1) / len(modules))
                                progress_bar.progress(min(progress, 0.66))
                        except Exception as e:
                            st.error(f"Error downloading module content: {e}")
                        
                        progress_bar.progress(0.66)
                    
                    if download_assignments:
                        status_text.text("📝 Processing assignment files...")
                        try:
                            # This would require additional implementation
                            # for assignment-specific file downloads
                            st.info("Assignment file downloads not yet implemented")
                        except Exception as e:
                            st.error(f"Error downloading assignment files: {e}")
                        
                        progress_bar.progress(1.0)
                    
                    # Final status
                    status_text.text("✅ Download process completed!")
                    
                    # Show results
                    with stats_container:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ Downloaded", total_downloaded)
                        with col2:
                            st.metric("❌ Failed", total_failed)
                        with col3:
                            success_rate = (total_downloaded / (total_downloaded + total_failed) * 100) if (total_downloaded + total_failed) > 0 else 0
                            st.metric("Success Rate", f"{success_rate:.1f}%")
                    
                    # Show failed downloads if any
                    if failed_downloads:
                        with st.expander(f"❌ Failed Downloads ({len(failed_downloads)})", expanded=False):
                            for failure in failed_downloads[:20]:  # Show first 20 failures
                                st.write(f"• {failure}")
                            if len(failed_downloads) > 20:
                                st.write(f"... and {len(failed_downloads) - 20} more failures")
                    
                    # Next steps
                    if total_downloaded > 0 and not dry_run:
                        st.success("🎉 Files downloaded successfully!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🤖 Generate AI Notes Now"):
                                st.info("Switching to AI Notes tab...")
                                st.rerun()
                        
                        with col2:
                            if st.button("📂 View Downloads Folder"):
                                st.info(f"Downloads saved to: {download_dir}")
                                # Show updated file status
                                updated_status = self.check_course_files_availability(course_id)
                                st.write(f"Total files now available: {updated_status['file_count']}")
                    
                except Exception as e:
                    st.error(f"❌ Download failed: {str(e)}")
                    logger.error(f"Download error: {e}")
        
        # Help section
        with st.expander("ℹ️ Help & Tips", expanded=False):
            st.markdown("""
            ### Download Tips:
            
            **File Types Supported for AI Notes:**
            - 📄 PDF documents
            - 📝 Word documents (.docx, .doc)
            - 📄 Text files (.txt)
            
            **Workflow Recommendations:**
            1. **First Time**: Download course files using this tab
            2. **Generate Notes**: Use the AI Notes tab to process downloaded files
            3. **Organize**: Files are automatically organized by course and type
            
            **Troubleshooting:**
            - Use "Dry Run" to preview what will be downloaded
            - Check Canvas permissions if downloads fail
            - Large files may take longer to process
            
            **File Organization:**
            - Files are saved to: `downloads/course_{id}_{name}/`
            - AI notes are saved to: `downloads/ai_notes/`
            """)
    
    def run(self):
        """Main app runner"""
        self.initialize_session_state()
        self.render_header()
        
        # Sidebar authentication
        is_authenticated = self.render_login_section()
        
        if is_authenticated:
            # Main content
            self.render_course_selection()
            
            if st.session_state.selected_course:
                self.render_course_overview()
                self.render_workflow_status()
                
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Assignments", "📚 Modules", "📁 Files", "📊 Export", "⬇️ Download", "🤖 AI Notes"])
                
                with tab1:
                    self.render_assignments_section()
                
                with tab2:
                    self.render_modules_section()
                
                with tab3:
                    self.render_files_section()
                
                with tab4:
                    self.render_export_section()
                
                with tab5:
                    self.render_enhanced_download_section()
                
                with tab6:
                    self.render_ai_notes_section()
        else:
            # Show instructions when not authenticated
            st.markdown("""
            ## Welcome to Canvas LMS Course Explorer! 🎉
            
            This application allows you to:
            - 🔐 Securely connect to your Canvas LMS account
            - 📚 Browse and explore your courses
            - 📝 View assignments and due dates
            - 📚 Explore course modules and content
            - 📊 Export course data for analysis
            
            ### Getting Started:
            1. **Login**: Use the sidebar to enter your Canvas URL and API token
            2. **Select Course**: Choose from your available courses
            3. **Explore Data**: View assignments, modules, and other course information
            4. **Export**: Download course data in various formats
            
            ### Note:
            This app focuses on data you have access to as a student. Some features like file downloads may not be available due to Canvas permissions.
            """)

def main():
    """Main function"""
    app = CanvasCourseExplorer()
    app.run()

if __name__ == "__main__":
    main()
