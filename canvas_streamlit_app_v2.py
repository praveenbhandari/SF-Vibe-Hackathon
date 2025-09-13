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
from typing import List, Dict, Any
import logging
import pandas as pd

from canvas_client import CanvasClient
from canvas_config import CanvasConfig

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

class CanvasCourseExplorer:
    """Canvas LMS Course Explorer with focus on accessible data"""
    
    def __init__(self):
        self.client = None
        self.config_manager = CanvasConfig()
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
    
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
        if not st.session_state.course_data:
            return
        
        st.header("📊 Export Data")
        
        course = st.session_state.selected_course
        course_name = course.get('name', 'Unknown') if course else 'Unknown'
        course_data = st.session_state.course_data
        
        # Export options
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("📄 Export All Data to JSON"):
                self.export_to_json(course_data, course_name)
        
        with col2:
            if st.button("📊 Export Assignments to CSV"):
                if course_data.get('assignments'):
                    self.export_assignments_to_csv(course_data['assignments'], course_name)
                else:
                    st.warning("No assignments to export")
    
    def export_to_json(self, data: Dict[str, Any], course_name: str):
        """Export data to JSON file"""
        try:
            safe_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            filename = f"{safe_name}_course_data.json"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
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
                
                tab1, tab2, tab3, tab4 = st.tabs(["📝 Assignments", "📚 Modules", "📁 Files", "📊 Export"])
                
                with tab1:
                    self.render_assignments_section()
                
                with tab2:
                    self.render_modules_section()
                
                with tab3:
                    self.render_files_section()
                
                with tab4:
                    self.render_export_section()
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
