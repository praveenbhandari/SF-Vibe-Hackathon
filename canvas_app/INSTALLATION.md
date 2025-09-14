# Canvas LMS Streamlit App V2 - Installation Guide

## Quick Start

### Option 1: Full Installation (Recommended)
For all features including AI-powered learning, RAG chatbot, and memory management:

```bash
pip install -r requirements.txt
```

### Option 2: Minimal Installation
For basic Canvas functionality without AI features:

```bash
pip install -r requirements-minimal.txt
```

## Detailed Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download
```bash
git clone <repository-url>
cd canvas_app
```

### Step 2: Install Dependencies

#### Full Installation (All Features)
```bash
# Install all dependencies including AI/ML libraries
pip install -r requirements.txt

# Optional: Install additional AI backends
pip install openai groq ollama
```

#### Minimal Installation (Basic Features Only)
```bash
# Install only core dependencies
pip install -r requirements-minimal.txt
```

### Step 3: Run the Application
```bash
streamlit run canvas_streamlit_app_v2.py
```

## Feature-Specific Dependencies

### Core Canvas Features
- `requests` - Canvas API communication
- `streamlit` - Web interface
- `pandas` - Data processing
- `python-dotenv` - Environment configuration
- `keyring` - Secure credential storage

### Document Processing
- `PyPDF2` - PDF text extraction
- `python-docx` - Word document processing
- `python-pptx` - PowerPoint processing

### AI and RAG Features
- `sentence-transformers` - Text embeddings
- `faiss-cpu` - Vector similarity search
- `scikit-learn` - Machine learning utilities
- `nltk` - Natural language processing
- `spacy` - Advanced NLP

### Web Search and Scraping
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML processing

### Optional AI Backends
- `openai` - OpenAI API integration
- `groq` - Groq API integration
- `ollama` - Local Ollama integration

## Troubleshooting

### Common Issues

1. **FAISS Installation Issues**
   ```bash
   # Try CPU-only version
   pip install faiss-cpu
   
   # Or GPU version if you have CUDA
   pip install faiss-gpu
   ```

2. **SpaCy Model Download**
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **NLTK Data Download**
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

4. **Memory Issues with Large Documents**
   - Use the minimal requirements for basic functionality
   - Process documents in smaller chunks
   - Increase system memory or use cloud instances

### Platform-Specific Notes

#### Windows
- Install Visual C++ Build Tools if you encounter compilation errors
- Use Anaconda for easier dependency management

#### macOS
- Install Xcode command line tools: `xcode-select --install`
- Use Homebrew for system dependencies

#### Linux
- Install build essentials: `sudo apt-get install build-essential`
- Install Python development headers: `sudo apt-get install python3-dev`

## Environment Variables

Create a `.env` file in the canvas_app directory:

```env
# Canvas API Configuration
CANVAS_URL=https://your-canvas-instance.com
CANVAS_API_TOKEN=your_api_token_here

# Optional AI Backend Configuration
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
OLLAMA_MODEL=llama3.1:8b

# Optional: Custom model settings
EMBED_MODEL=all-MiniLM-L6-v2
TOP_K=3
```

## Verification

After installation, verify everything works:

```bash
# Test basic functionality
python -c "import streamlit, requests, pandas; print('Core dependencies OK')"

# Test AI features (if full installation)
python -c "import sentence_transformers, faiss; print('AI dependencies OK')"

# Run the app
streamlit run canvas_streamlit_app_v2.py
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the error messages carefully
3. Ensure all dependencies are properly installed
4. Check Python version compatibility (3.8+)
