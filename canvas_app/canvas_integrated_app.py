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
    st.error("canvasapi not installed. Please