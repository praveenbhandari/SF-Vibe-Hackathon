#!/usr/bin/env python3
"""
Canvas LMS Course Explorer with Integrated RAG Demo

This application combines:
1. Canvas LMS functionality for course exploration, file downloads, and data export
2. LMS RAG Demo functionality for AI-powered note generation, chatbot, and learning features

Author: Integrated from canvas_streamlit_app_v2.py and send_to_friend/streamlit_app.py
"""

import streamlit as st
import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Canvas LMS imports
try:
    from canvasapi import Canvas
    from canvasapi.exceptions import CanvasException
except ImportError:
    st.error("canvasapi not installed. Please install with: pip install canvasapi")
    st.stop()

# RAG Demo imports
try:
    # Add send_to_friend directory to path for imports
    send_to_friend_path = os.path.join(os.path.dirname(__file__), 'send_to_friend')
    if send_to_friend_path not in sys.path:
        sys.path.insert(0, send_to_friend_path)
    
    # Import from correct paths based on directory structure
    from src.pipelines.text_extraction_pipeline import TextExtractionPipeline
    from src.utils.ingest import ingest_documents, semantic_search
    from src.utils.retrieval import mmr_retrieve
    from src.utils.rag_llm import answer_with_context
    from src.utils.memory import ConversationMemory
    from src.utils.learning_mode import extract_topics_from_notes, recommend_youtube, build_topic_context
    from src.utils.web_search import recommend_articles_ddg, recommend_youtube_ddg
    from src.utils.notes import generate_notes_from_text, iter_generate_notes_from_texts
    from src.utils.notes_ingest import ingest_notes_sections
except ImportError as e:
    st.error(f"RAG Demo dependencies not found: {e}")
    st.error("Please ensure the send_to_friend directory and its dependencies are available.")
    # Continue without RAG features
    RAG_AVAILABLE = False
else:
    RAG_AVAILABLE = True

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Canvas LMS Explorer + RAG Demo",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-completed { background-color: #d4edda; color: #155724; }
    .status-pending { background-color: #fff3cd; color: #856404; }
    .status-in-progress { background-color: #cce5ff; color: #004085; }
    .workflow-step {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background-color: #f8f9fa;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

# RAG Demo Configuration (from send_to_friend)
if RAG_AVAILABLE:
    TOP_K = 5
    EMBED_MODEL = "all-MiniLM-L6-v2"
    
    def _store_dir():
        return os.path.join("data", "vector_store")
    
    def _meta_path():
        return os.path.join("data", "notes_index", "metadata.json")
    
    # Initialize memory
    mem = ConversationMemory()

class CanvasClient:
    """Canvas API client wrapper"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.canvas = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Canvas"""
        try:
            self.canvas = Canvas(self.base_url, self.api_token)
            # Test connection
            self.canvas.get_current_user()
            logger.info("Successfully connected to Canvas")
        except Exception as e:
            logger.error(f"Failed to connect to Canvas: {e}")
            raise
    
    def get_courses(self) -> List[Dict]:
        """Get user's courses"""
        try:
            courses = list(self.canvas.get_courses())
            course_list = []
            for course in courses:
                try:
                    # Try different possible attribute names for course name
                    course_name = None
                    for attr in ['name', 'course_name', 'title', 'course_code']:
                        if hasattr(course, attr):
                            course_name = getattr(course, attr)
                            break
                    
                    if not course_name:
                        course_name = f'Course {course.id}'
                    
                    course_list.append({
                        'id': course.id,
                        'name': course_name,
                        'course_code': getattr(course, 'course_code', 'N/A'),
                        'enrollment_term_id': getattr(course, 'enrollment_term_id', None),
                        'start_at': getattr(course, 'start_at', None),
                        'end_at': getattr(course, 'end_at', None)
                    })
                except Exception as course_error:
                    logger.warning(f"Error processing course {course.id}: {course_error}")
                    continue
            
            return course_list
        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []
    
    def get_course(self, course_id: int):
        """Get specific course"""
        return self.canvas.get_course(course_id)

class CanvasFileDownloader:
    """Enhanced file downloader for Canvas courses"""
    
    def __init__(self, canvas_client: CanvasClient, base_download_dir: str = "downloads"):
        self.canvas_client = canvas_client
        self.base_download_dir = Path(base_download_dir)
        self.base_download_dir.mkdir(exist_ok=True)
    
    def download_course_files(self, course_id: int, course_name: str, 
                            dry_run: bool = False, organize_by_type: bool = True) -> Dict:
        """Download all accessible files from a course"""
        try:
            course = self.canvas_client.get_course(course_id)
            
            # Create course directory
            safe_course_name = "".join(c for c in course_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            course_dir = self.base_download_dir / f"course_{course_id}_{safe_course_name}"
            
            if not dry_run:
                course_dir.mkdir(exist_ok=True)
            
            downloaded = 0
            failed = 0
            files_info = []
            failed_files = []
            
            # Get course files
            try:
                files = list(course.get_files())
                
                for file in files:
                    try:
                        # Determine file path
                        if organize_by_type:
                            file_ext = Path(file.filename).suffix.lower()
                            if file_ext in ['.pdf', '.doc', '.docx']:
                                type_dir = course_dir / "documents"
                            elif file_ext in ['.mp4', '.avi', '.mov']:
                                type_dir = course_dir / "videos"
                            elif file_ext in ['.jpg', '.png', '.gif']:
                                type_dir = course_dir / "images"
                            else:
                                type_dir = course_dir / "other"
                        else:
                            type_dir = course_dir
                        
                        file_path = type_dir / file.filename
                        
                        if dry_run:
                            files_info.append({
                                'name': file.filename,
                                'size': getattr(file, 'size', 0),
                                'path': str(file_path),
                                'url': getattr(file, 'url', None)
                            })
                            downloaded += 1
                        else:
                            # Create directory
                            type_dir.mkdir(exist_ok=True)
                            
                            # Download file (simplified - actual implementation would need proper Canvas file download)
                            files_info.append({
                                'name': file.filename,
                                'size': getattr(file, 'size', 0),
                                'path': str(file_path),
                                'downloaded': True
                            })
                            downloaded += 1
                            
                    except Exception as e:
                        failed += 1
                        failed_files.append(f"{file.filename}: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error accessing course files: {e}")
                failed_files.append(f"Course files access error: {str(e)}")
            
            return {
                'downloaded': downloaded,
                'failed': failed,
                'files': files_info,
                'failed_files': failed_files,
                'course_dir': str(course_dir)
            }
            
        except Exception as e:
            logger.error(f"Error in download_course_files: {e}")
            return {
                'downloaded': 0,
                'failed': 1,
                'files': [],
                'failed_files': [f"General error: {str(e)}"],
                'course_dir': None
            }

class CanvasIntegratedApp:
    """Main integrated application class"""
    
    def __init__(self):
        self.canvas_client = None
        self.downloader = None
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        # Canvas LMS session state
        if 'canvas_authenticated' not in st.session_state:
            st.session_state.canvas_authenticated = False
        if 'canvas_client' not in st.session_state:
            st.session_state.canvas_client = None
        if 'courses' not in st.session_state:
            st.session_state.courses = []
        if 'selected_course' not in st.session_state:
            st.session_state.selected_course = None
        if 'course_data' not in st.session_state:
            st.session_state.course_data = {}
        
        # RAG Demo session state
        if RAG_AVAILABLE:
            if 'rag_profile_id' not in st.session_state:
                st.session_state.rag_profile_id = "default"
            if 'memory_short_window' not in st.session_state:
                st.session_state.memory_short_window = 5
            if 'chat_messages' not in st.session_state:
                st.session_state.chat_messages = []
            if 'chat_cooldown' not in st.session_state:
                st.session_state.chat_cooldown = 0.0
            if 'learning_messages' not in st.session_state:
                st.session_state.learning_messages = []
            if 'learning_cooldown' not in st.session_state:
                st.session_state.learning_cooldown = 0.0
            if 'learning_initialized' not in st.session_state:
                st.session_state.learning_initialized = False
    
    def render_header(self):
        """Render application header"""
        st.markdown("""
        <div class="main-header">
            <h1>🎓 Canvas LMS Explorer + RAG Demo</h1>
            <p>Comprehensive Canvas course exploration with AI-powered learning features</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_login_section(self) -> bool:
        """Render Canvas login section in sidebar"""
        with st.sidebar:
            st.header("🔐 Canvas Authentication")
            
            if st.session_state.canvas_authenticated:
                st.success("✅ Connected to Canvas")
                if st.button("🚪 Logout"):
                    st.session_state.canvas_authenticated = False
                    st.session_state.canvas_client = None
                    st.session_state.courses = []
                    st.session_state.selected_course = None
                    st.rerun()
                return True
            else:
                st.info("Please enter your Canvas credentials to continue.")
                
                canvas_url = st.text_input(
                    "Canvas URL",
                    placeholder="https://your-institution.instructure.com",
                    help="Your institution's Canvas URL"
                )
                
                api_token = st.text_input(
                    "API Token",
                    type="password",
                    help="Generate this from Canvas Account > Settings > Approved Integrations"
                )
                
                if st.button("🔑 Connect to Canvas"):
                    if canvas_url and api_token:
                        try:
                            with st.spinner("Connecting to Canvas..."):
                                client = CanvasClient(canvas_url, api_token)
                                st.session_state.canvas_client = client
                                st.session_state.canvas_authenticated = True
                                
                                # Load courses
                                courses = client.get_courses()
                                st.session_state.courses = courses
                                
                                st.success(f"✅ Connected! Found {len(courses)} courses.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Connection failed: {str(e)}")
                    else:
                        st.error("Please provide both Canvas URL and API token.")
                
                return False
    
    def render_course_selection(self):
        """Render course selection interface"""
        if not st.session_state.courses:
            st.info("No courses found. Please check your Canvas connection.")
            return
        
        st.subheader("📚 Select Course")
        
        # Course selection
        course_options = {f"{course['name']} ({course['course_code']})": course 
                         for course in st.session_state.courses}
        
        selected_course_name = st.selectbox(
            "Choose a course to explore:",
            options=list(course_options.keys()),
            index=0 if course_options else None
        )
        
        if selected_course_name:
            selected_course = course_options[selected_course_name]
            if st.session_state.selected_course != selected_course:
                st.session_state.selected_course = selected_course
                st.session_state.course_data = {}
                st.rerun()
    
    def render_course_overview(self):
        """Render course overview section"""
        if not st.session_state.selected_course:
            return
        
        course = st.session_state.selected_course
        
        st.subheader(f"📖 {course['name']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>📋 Course Code</h4>
                <p>{}</p>
            </div>
            """.format(course.get('course_code', 'N/A')), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>🆔 Course ID</h4>
                <p>{}</p>
            </div>
            """.format(course['id']), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>📅 Term</h4>
                <p>{}</p>
            </div>
            """.format(course.get('enrollment_term_id', 'N/A')), unsafe_allow_html=True)
    
    def render_rag_content_ingestion(self):
        """Render RAG content ingestion section"""
        if not RAG_AVAILABLE:
            st.error("RAG functionality not available. Please check dependencies.")
            return
        
        st.subheader("📥 Content Ingestion")
        
        # Memory profile selection
        profile_id = st.selectbox(
            "Memory Profile",
            ["default", "study_session_1", "study_session_2"],
            help="Different profiles maintain separate conversation histories"
        )
        st.session_state.rag_profile_id = profile_id
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload PDF/DOCX files",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True
        )
        
        # YouTube URL input
        youtube_url = st.text_input(
            "YouTube URL or Playlist",
            placeholder="https://www.youtube.com/watch?v=..."
        )
        
        # Process uploads
        if st.button("🔄 Process Content"):
            if uploaded_files or youtube_url:
                with st.spinner("Processing content..."):
                    try:
                        pipeline = TextExtractionPipeline()
                        all_results = []
                        
                        # Process uploaded files
                        for uploaded_file in uploaded_files:
                            # Save uploaded file temporarily
                            temp_path = f"temp_{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            result = pipeline.extract_from_file(temp_path)
                            all_results.append(result)
                            
                            # Clean up temp file
                            os.remove(temp_path)
                        
                        # Process YouTube URL
                        if youtube_url:
                            result = pipeline.extract_from_youtube(youtube_url)
                            all_results.append(result)
                        
                        # Ingest into vector store
                        successful_results = [r for r in all_results if r.get('success')]
                        if successful_results:
                            store_dir = ingest_documents(successful_results, model_name=EMBED_MODEL)
                            st.success(f"✅ Processed {len(successful_results)} items successfully!")
                            st.info(f"Vector store saved to: {store_dir}")
                        else:
                            st.error("No content was successfully processed.")
                            
                    except Exception as e:
                        st.error(f"Error processing content: {e}")
            else:
                st.warning("Please upload files or provide a YouTube URL.")
    
    def render_rag_notes_tab(self):
        """Render RAG notes generation tab"""
        if not RAG_AVAILABLE:
            st.error("RAG functionality not available.")
            return
        
        st.subheader("📝 Generate Notes")
        
        # Check if content is available
        store_meta = _meta_path()
        if not os.path.exists(store_meta):
            st.warning("No content found. Please ingest content first using the Content Ingestion section.")
            return
        
        # Notes generation options
        col1, col2 = st.columns(2)
        
        with col1:
            note_style = st.selectbox(
                "Note Style",
                ["Detailed", "Summary", "Bullet Points", "Q&A Format"]
            )
        
        with col2:
            max_sections = st.slider("Max Sections", 5, 50, 20)
        
        if st.button("📝 Generate Notes"):
            with st.spinner("Generating notes..."):
                try:
                    # Load metadata
                    with open(store_meta, "r", encoding="utf-8") as f:
                        metas = json.load(f)
                    
                    # Extract text sections
                    texts = [m.get("text", "") for m in metas if m.get("text")]
                    sections = texts[:max_sections]
                    
                    if sections:
                        # Generate notes using LLM
                        prompt = f"Generate {note_style.lower()} notes from the following content:"
                        context = [{"source": "content", "chunk_index": i, "text": text} 
                                 for i, text in enumerate(sections)]
                        
                        notes = answer_with_context(prompt, context)
                        
                        st.markdown("### 📋 Generated Notes")
                        st.markdown(notes)
                        
                        # Save notes
                        notes_dir = Path("data/ai_notes")
                        notes_dir.mkdir(parents=True, exist_ok=True)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        notes_file = notes_dir / f"notes_{timestamp}.md"
                        
                        with open(notes_file, "w", encoding="utf-8") as f:
                            f.write(f"# Generated Notes - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            f.write(notes)
                        
                        st.success(f"Notes saved to: {notes_file}")
                    else:
                        st.error("No content sections found.")
                        
                except Exception as e:
                    st.error(f"Error generating notes: {e}")
    
    def render_rag_chat_tab(self):
        """Render RAG chatbot tab"""
        if not RAG_AVAILABLE:
            st.error("RAG functionality not available.")
            return
        
        st.subheader("💬 QA Chatbot")
        
        # Check if content is available
        store_meta = _meta_path()
        if not os.path.exists(store_meta):
            st.warning("No content found. Please ingest content first.")
            return
        
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            for msg in st.session_state.chat_messages:
                if msg.get("role") == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {msg.get("content", "")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {msg.get("content", "")}</div>', unsafe_allow_html=True)
        
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_question = st.text_input(
                "Ask a question about your content...",
                key="chat_input",
                placeholder="Type your question here..."
            )
        
        with col2:
            send_button = st.button("Send", key="chat_send", type="primary")
        
        if send_button and user_question:
            # Cooldown check
            now = time.time()
            if now - st.session_state.chat_cooldown < 3.0:
                st.warning("Please wait a moment before sending another message.")
                st.stop()
            
            with st.spinner("Retrieving and answering..."):
                try:
                    # Retrieve contexts
                    contexts = mmr_retrieve(user_question, top_k=TOP_K, store_dir=_store_dir(), model_name=EMBED_MODEL)
                    
                    # Memory contexts
                    mem_ctx = mem.memory_contexts(
                        st.session_state.chat_messages, 
                        profile_id=st.session_state.rag_profile_id, 
                        short_window=st.session_state.memory_short_window
                    )
                    
                    all_ctx = contexts + mem_ctx
                    
                    if not all_ctx:
                        answer = "No results found. Please ingest content first."
                    else:
                        answer = answer_with_context(user_question, all_ctx)
                    
                    # Update chat history
                    st.session_state.chat_messages.append({"role": "user", "content": user_question})
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                    
                    # Update long-term memory
                    mem.summarize_and_store_long_term(
                        st.session_state.chat_messages, 
                        profile_id=st.session_state.rag_profile_id
                    )
                    
                    st.session_state.chat_cooldown = time.time()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    
    def render_rag_learning_tab(self):
        """Render RAG learning mode tab"""
        if not RAG_AVAILABLE:
            st.error("RAG functionality not available.")
            return
        
        st.subheader("🎓 Learning Mode - AI Tutor Chat")
        
        # Check if notes are available
        store_meta = _meta_path()
        if not os.path.exists(store_meta):
            st.warning("No notes context found. Generate notes first.")
            return
        
        # Initialize learning chat
        if not st.session_state.learning_initialized:
            try:
                with open(store_meta, "r", encoding="utf-8") as f:
                    metas = json.load(f)
                
                texts = [m.get("text", "") for m in metas if m.get("text")]
                notes_sections = texts[:50]
                topics = extract_topics_from_notes(notes_sections)
                
                if not topics:
                    topics = [f"Topic {i+1}" for i in range(min(5, len(notes_sections)))]
                
                st.session_state.learning_topics = topics[:10]
                st.session_state.learning_initialized = True
                
                # Welcome message
                welcome_msg = f"Hello! I'm your AI learning tutor. I can help you learn about these topics: {', '.join(topics[:5])}. What would you like to explore first?"
                st.session_state.learning_messages.append({"role": "assistant", "content": welcome_msg})
                
            except Exception as e:
                st.error(f"Error initializing learning mode: {e}")
                return
        
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            for msg in st.session_state.learning_messages:
                if msg.get("role") == "user":
                    st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {msg.get("content", "")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message assistant-message"><strong>Tutor:</strong> {msg.get("content", "")}</div>', unsafe_allow_html=True)
        
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask your tutor anything...",
                key="learning_input",
                placeholder="What would you like to learn about?"
            )
        
        with col2:
            send_button = st.button("Send", key="learning_send", type="primary")
        
        if send_button and user_input:
            # Cooldown check
            now = time.time()
            if now - st.session_state.learning_cooldown < 3.0:
                st.warning("Please wait a moment before sending another message.")
                st.stop()
            
            with st.spinner("Tutor is thinking..."):
                try:
                    # Build context from Notes Index
                    note_ctx = semantic_search(
                        user_input, 
                        store_dir=os.path.join("data", "notes_index"), 
                        top_k=TOP_K, 
                        model_name=EMBED_MODEL
                    )
                    
                    # Memory context
                    mem_ctx = mem.memory_contexts(
                        st.session_state.learning_messages, 
                        profile_id=st.session_state.rag_profile_id, 
                        short_window=st.session_state.memory_short_window
                    )
                    
                    # Get recommended resources
                    relevant_topic = user_input
                    for topic in st.session_state.learning_topics:
                        if topic.lower() in user_input.lower() or user_input.lower() in topic.lower():
                            relevant_topic = topic
                            break
                    
                    vlinks = recommend_youtube(relevant_topic)
                    alinks = recommend_articles_ddg(relevant_topic)
                    
                    res_text = f"Recommended Videos for '{relevant_topic}':\n" + "\n".join([f"- {l['title']}: {l['url']}" for l in vlinks[:2]]) + \
                              f"\nRecommended Articles for '{relevant_topic}':\n" + "\n".join([f"- {a['title']}: {a['url']}" for a in alinks[:2]])
                    
                    res_ctx = [{"source": "resources", "chunk_index": 0, "text": res_text}]
                    
                    all_ctx = note_ctx + mem_ctx + res_ctx
                    
                    # Tutor prompt
                    prompt = f"You are an AI learning tutor. Help the student learn by explaining concepts, asking questions, suggesting resources, and giving small assignments. Be encouraging and educational. Student said: {user_input}"
                    
                    reply = answer_with_context(prompt, all_ctx)
                    
                    # Update chat history
                    st.session_state.learning_messages.append({"role": "user", "content": user_input})
                    st.session_state.learning_messages.append({"role": "assistant", "content": reply})
                    
                    # Update long-term memory
                    mem.summarize_and_store_long_term(
                        st.session_state.learning_messages, 
                        profile_id=st.session_state.rag_profile_id
                    )
                    
                    st.session_state.learning_cooldown = time.time()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    
    def render_rag_resources_tab(self):
        """Render RAG resources tab"""
        if not RAG_AVAILABLE:
            st.error("RAG functionality not available.")
            return
        
        st.subheader("🔗 Recommended Resources")
        
        # Check if notes are available
        store_meta = _meta_path()
        if not os.path.exists(store_meta):
            st.warning("No notes context found. Generate notes first.")
            return
        
        try:
            with open(store_meta, "r", encoding="utf-8") as f:
                metas = json.load(f)
            
            texts = [m.get("text", "") for m in metas if m.get("text")]
            notes_sections = texts[:50]
            topics = extract_topics_from_notes(notes_sections)
            
            if not topics:
                st.info("Could not detect headings; using first few sections as topics.")
                topics = [f"Topic {i+1}" for i in range(min(5, len(notes_sections)))]
            
            for topic in topics[:10]:
                with st.expander(topic, expanded=False):
                    st.markdown("**Related Videos (via DuckDuckGo)**")
                    vlinks = recommend_youtube_ddg(topic)
                    if vlinks:
                        for l in vlinks:
                            st.write(f"- [{l['title']}]({l['url']})")
                    else:
                        st.write("No videos found for this topic.")
                    
                    st.markdown("**Related Articles (via DuckDuckGo)**")
                    alinks = recommend_articles_ddg(topic)
                    if alinks:
                        for a in alinks:
                            st.write(f"- [{a['title']}]({a['url']})")
                    else:
                        st.write("No articles found for this topic.")
                    
                    if st.button("Explain connections", key=f"explain_{topic}"):
                        try:
                            topic_ctx = build_topic_context(notes_sections, topic)
                            res_text = "Videos:\n" + "\n".join([l['title'] for l in vlinks]) + "\nArticles:\n" + "\n".join([a['title'] for a in alinks])
                            aug_ctx = topic_ctx + [{"source": "resources", "chunk_index": 0, "text": res_text}]
                            
                            prompt = f"For the topic '{topic}', explain in 2-3 sentences how the above videos and articles help learning the topic (what each adds)."
                            msg = answer_with_context(prompt, aug_ctx)
                            st.write(msg)
                        except Exception as e:
                            st.info(f"Could not generate explanation: {e}")
                            
        except Exception as e:
            st.error(f"Error loading resources: {e}")
    
    def run(self):
        """Main application runner"""
        self.initialize_session_state()
        self.render_header()
        
        # Sidebar authentication
        is_authenticated = self.render_login_section()
        
        if is_authenticated:
            # Main content
            self.render_course_selection()
            
            if st.session_state.selected_course:
                self.render_course_overview()
                
                # Main tabs - Canvas LMS + RAG Demo
                if RAG_AVAILABLE:
                    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                        "📥 Content Ingestion", "📝 Generate Notes", "💬 QA Chatbot", 
                        "🎓 Learning Mode", "🔗 Resources", "📁 Canvas Files", "📊 Canvas Export"
                    ])
                    
                    with tab1:
                        self.render_rag_content_ingestion()
                    
                    with tab2:
                        self.render_rag_notes_tab()
                    
                    with tab3:
                        self.render_rag_chat_tab()
                    
                    with tab4:
                        self.render_rag_learning_tab()
                    
                    with tab5:
                        self.render_rag_resources_tab()
                    
                    with tab6:
                        st.subheader("📁 Canvas Files")
                        st.info("Canvas file management functionality - to be implemented")
                    
                    with tab7:
                        st.subheader("📊 Canvas Export")
                        st.info("Canvas data export functionality - to be implemented")
                else:
                    # Only Canvas functionality if RAG not available
                    tab1, tab2 = st.tabs(["📁 Canvas Files", "📊 Canvas Export"])
                    
                    with tab1:
                        st.subheader("📁 Canvas Files")
                        st.info("Canvas file management functionality - to be implemented")
                    
                    with tab2:
                        st.subheader("📊 Canvas Export")
                        st.info("Canvas data export functionality - to be implemented")
        else:
            # Show instructions when not authenticated
            st.markdown("""
            ## Welcome to Canvas LMS Explorer + RAG Demo! 🎉
            
            This integrated application combines:
            
            ### 🎓 Canvas LMS Features:
            - 🔐 Securely connect to your Canvas LMS account
            - 📚 Browse and explore your courses
            - 📝 View assignments and due dates
            - 📚 Explore course modules and content
            - 📊 Export course data for analysis
            
            ### 🤖 AI-Powered RAG Demo Features:
            - 📥 Ingest PDF/DOCX files and YouTube content
            - 📝 Generate AI-powered notes from your content
            - 💬 Interactive QA chatbot for your materials
            - 🎓 AI tutor for personalized learning
            - 🔗 Recommended resources based on your content
            
            ### Getting Started:
            1. **Login**: Use the sidebar to enter your Canvas URL and API token
            2. **Select Course**: Choose from your available courses
            3. **Ingest Content**: Upload files or YouTube URLs for AI processing
            4. **Explore**: Use the various tabs to interact with your content
            
            ### Note:
            Canvas features focus on data you have access to as a student. Some features may be limited by Canvas permissions.
            """)

def main():
    """Main function"""
    app = CanvasIntegratedApp()
    app.run()

if __name__ == "__main__":
    main()