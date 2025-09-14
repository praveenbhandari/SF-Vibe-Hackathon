import os
import re
import json
import subprocess
from typing import List, Dict, Any

from .rag_llm import answer_with_context


def extract_topics_from_notes(notes_sections: List[str]) -> List[str]:
    """Extract topic headings (## or ###) from markdown sections."""
    topics: List[str] = []
    pattern = re.compile(r"^#{2,3}\s+(.+)$")
    for sec in notes_sections:
        for line in sec.splitlines():
            m = pattern.match(line.strip())
            if m:
                t = m.group(1).strip()
                if t and t not in topics:
                    topics.append(t)
    return topics


def _yt_search(query: str, limit: int = 3) -> List[Dict[str, str]]:
    """Search YouTube without API key using yt-dlp ytsearch.
    Returns list of dicts with title and url.
    """
    cmd = [
        "yt-dlp",
        f"ytsearch{limit}:{query}",
        "--dump-json",
        "--no-warnings",
        "--skip-download",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        results: List[Dict[str, str]] = []
        for line in proc.stdout.strip().splitlines():
            try:
                data = json.loads(line)
                title = data.get("title", "")
                url = data.get("webpage_url") or (f"https://www.youtube.com/watch?v={data.get('id')}" if data.get('id') else None)
                if title and url:
                    results.append({"title": title, "url": url})
            except json.JSONDecodeError:
                continue
        return results[:limit]
    except subprocess.CalledProcessError:
        return []


def build_topic_context(notes_sections: List[str], topic: str) -> List[Dict[str, Any]]:
    """Build minimal context for LLM from notes related to a topic."""
    context_texts: List[str] = []
    for sec in notes_sections:
        if topic.lower() in sec.lower():
            context_texts.append(sec)
    if not context_texts:
        context_texts = notes_sections[:2]
    contexts = []
    for idx, t in enumerate(context_texts):
        contexts.append({"source": "notes", "chunk_index": idx, "text": t})
    return contexts


def generate_explainer(topic: str, notes_sections: List[str]) -> str:
    context = build_topic_context(notes_sections, topic)
    prompt = f"Explain the topic '{topic}' concisely for a student using the context. Emphasize definitions, key steps, and one short example."
    return answer_with_context(prompt, context)


def generate_quiz(topic: str, notes_sections: List[str]) -> str:
    context = build_topic_context(notes_sections, topic)
    prompt = f"Create 2 short quiz questions (bullet list) to test understanding of '{topic}'."
    return answer_with_context(prompt, context)


def generate_assignment(topic: str, notes_sections: List[str]) -> str:
    context = build_topic_context(notes_sections, topic)
    prompt = f"Give one small assignment (3-5 steps) for practicing '{topic}'."
    return answer_with_context(prompt, context)


def recommend_youtube(topic: str) -> List[Dict[str, str]]:
    """Recommend YouTube videos using DuckDuckGo search"""
    try:
        from .web_search import recommend_youtube_ddg
        return recommend_youtube_ddg(topic, limit=3)
    except Exception as e:
        print(f"Error with DuckDuckGo YouTube search: {e}")
        # Fallback to yt-dlp if available
        try:
            q = f"{topic} tutorial"
            return _yt_search(q, limit=3)
        except Exception as e2:
            print(f"Error with yt-dlp fallback: {e2}")
            return []


def detect_learning_preference(user_input: str) -> Dict[str, str]:
    """
    Hardcoded learning preference detection for demo purposes.
    Analyzes user input for learning preference keywords.
    """
    user_lower = user_input.lower()
    
    # Initialize preferences
    prefs = {
        "preferred_content_type": None,
        "preferred_learning_style": None,
        "project_preference": None,
        "preferred_pace": None
    }
    
    # Detect content type preferences
    if any(word in user_lower for word in ["video", "watch", "visual", "see", "youtube"]):
        prefs["preferred_content_type"] = "videos"
    elif any(word in user_lower for word in ["article", "read", "text", "documentation", "written"]):
        prefs["preferred_content_type"] = "articles"
    
    # Detect learning style preferences
    if any(word in user_lower for word in ["visual", "diagram", "chart", "see", "watch"]):
        prefs["preferred_learning_style"] = "visual"
    elif any(word in user_lower for word in ["hands-on", "practice", "coding", "build", "create"]):
        prefs["preferred_learning_style"] = "kinesthetic"
    elif any(word in user_lower for word in ["listen", "audio", "podcast", "hear"]):
        prefs["preferred_learning_style"] = "auditory"
    
    # Detect project preferences
    if any(word in user_lower for word in ["small", "quick", "assignment", "exercise", "challenge"]):
        prefs["project_preference"] = "small_assignments"
    elif any(word in user_lower for word in ["big", "large", "project", "comprehensive", "build"]):
        prefs["project_preference"] = "big_projects"
    
    # Detect pace preferences
    if any(word in user_lower for word in ["quick", "fast", "brief", "summary"]):
        prefs["preferred_pace"] = "fast"
    elif any(word in user_lower for word in ["detailed", "comprehensive", "thorough", "step-by-step"]):
        prefs["preferred_pace"] = "slow"
    
    return prefs


def adaptive_learning_response(
    user_input: str, 
    notes_sections: List[str], 
    conversation_history: List[Dict[str, str]], 
    profile_id: str = "default"
) -> Dict[str, Any]:
    """
    Generate adaptive learning response based on hardcoded preference detection.
    Returns a dict with response, resources, and suggested actions.
    """
    # Detect learning preferences from user input
    prefs = detect_learning_preference(user_input)
    
    # Build context from notes
    note_ctx = []
    for idx, section in enumerate(notes_sections[:5]):
        note_ctx.append({"source": "notes", "chunk_index": idx, "text": section})
    
    # Create adaptive prompt based on detected preferences
    adaptive_prompt = ""
    if prefs.get("preferred_content_type") == "videos":
        adaptive_prompt += "The student prefers video content - prioritize suggesting YouTube videos and visual explanations. "
    elif prefs.get("preferred_content_type") == "articles":
        adaptive_prompt += "The student prefers textual content - prioritize suggesting articles and written explanations. "
    
    if prefs.get("preferred_learning_style") == "visual":
        adaptive_prompt += "The student is a visual learner - use diagrams, charts, and visual examples when explaining concepts. "
    elif prefs.get("preferred_learning_style") == "kinesthetic":
        adaptive_prompt += "The student learns best through hands-on practice - suggest practical exercises and coding projects. "
    
    if prefs.get("project_preference") == "small_assignments":
        adaptive_prompt += "The student prefers small, manageable assignments - break down complex topics into bite-sized tasks. "
    elif prefs.get("project_preference") == "big_projects":
        adaptive_prompt += "The student enjoys comprehensive projects - suggest larger, multi-step projects that build upon each other. "
    
    if prefs.get("preferred_pace") == "fast":
        adaptive_prompt += "The student prefers quick, concise explanations - keep responses brief and to the point. "
    elif prefs.get("preferred_pace") == "slow":
        adaptive_prompt += "The student prefers detailed explanations - provide comprehensive, step-by-step guidance. "
    
    # Generate base response
    base_prompt = f"""You are an AI learning tutor. {adaptive_prompt}
    
    Student said: {user_input}
    
    Provide a helpful, educational response that adapts to the student's learning preferences.
    Be encouraging and guide them through their learning journey."""
    
    try:
        response = answer_with_context(base_prompt, note_ctx)
    except Exception as e:
        response = f"I'd be happy to help you learn! Could you tell me more about what you'd like to explore? (Error: {str(e)})"
    
    # Generate resources based on preferences
    resources = {"videos": [], "articles": [], "assignments": [], "projects": []}
    
    # Extract topic for resource recommendations
    topic = user_input
    
    # Try to find a more specific topic from notes sections
    for section in notes_sections:
        if any(word in user_input.lower() for word in section.lower().split()[:5]):
            for line in section.splitlines():
                if line.strip().startswith('#'):
                    topic = line.strip().lstrip('#').strip()
                    break
            break
    
    # If no specific topic found, use the user input as topic
    if not topic or topic == user_input:
        # Clean up the topic for better search results
        topic = user_input.strip()
        # Remove common question words to get better search results
        question_words = ['what', 'how', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did', 'will', 'tell', 'me', 'about', 'explain', 'show']
        words = topic.lower().split()
        topic_words = [word for word in words if word not in question_words]
        if topic_words:
            topic = ' '.join(topic_words)
    
    # Always recommend resources for any topic
    try:
        resources["videos"] = recommend_youtube(topic)
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        resources["videos"] = []
    
    try:
        from .web_search import recommend_articles_ddg
        resources["articles"] = recommend_articles_ddg(topic)
    except Exception as e:
        print(f"Error fetching articles: {e}")
        resources["articles"] = []
    
    # Generate assignments/projects based on preferences
    if prefs.get("project_preference") in ["small_assignments", None]:
        try:
            assignment = generate_assignment(topic, notes_sections)
            resources["assignments"] = [{"title": f"Assignment: {topic}", "content": assignment}]
        except:
            pass
    
    if prefs.get("project_preference") == "big_projects":
        try:
            project_prompt = f"Suggest a comprehensive project idea for learning '{topic}' that includes multiple smaller components."
            project_ctx = build_topic_context(notes_sections, topic)
            project_suggestion = answer_with_context(project_prompt, project_ctx)
            resources["projects"] = [{"title": f"Project: {topic}", "content": project_suggestion}]
        except:
            pass
    
    # Generate quiz if student prefers interactive learning
    quiz_content = ""
    if any(word in user_input.lower() for word in ["quiz", "test", "question", "interactive"]):
        try:
            quiz_content = generate_quiz(topic, notes_sections)
        except:
            pass
    
    return {
        "response": response,
        "resources": resources,
        "quiz": quiz_content,
        "learning_preferences": prefs,
        "memory_updated": True
    }


def get_learning_suggestions(profile_id: str = "default") -> Dict[str, Any]:
    """Get hardcoded learning suggestions for demo purposes."""
    return {
        "content_recommendations": [
            "Focus on video tutorials for visual learners",
            "Use written guides for text-based learners",
            "Try hands-on projects for kinesthetic learners"
        ],
        "learning_approach": "adaptive",
        "next_steps": [
            "Complete small coding challenges",
            "Watch tutorial videos",
            "Read documentation",
            "Build a comprehensive project"
        ]
    }
