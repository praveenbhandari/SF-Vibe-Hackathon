# LMS AI Assistant - Complete Package

This package contains all the essential files for the LMS AI Assistant with the following features:

## 🚀 **Main Features**

### 1. **📝 Generate Notes**
- Extracts text from PDFs, DOCs, and YouTube videos
- Generates structured lecture-style notes using LLM
- Stores notes in separate vector database for retrieval

### 2. **🤖 QA Chatbot**
- Chat interface for asking questions about ingested content
- Uses RAG (Retrieval-Augmented Generation) with FAISS vector store
- Includes short-term and long-term memory

### 3. **🎓 Learning Mode**
- AI tutor chatbot for guided learning
- Uses notes context for relevant responses
- Suggests videos and articles during conversation
- Maintains conversation state and memory

### 4. **📚 Recommended Resources**
- DuckDuckGo search for YouTube videos and articles
- Topic-based recommendations from generated notes
- "Explain connections" feature for AI explanations

## 📁 **File Structure**

```
send_to_friend/
├── streamlit_app.py          # Main UI application
├── main.py                   # Command-line interface
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (API keys)
├── .gitignore               # Git ignore file
├── src/
│   ├── utils/               # Core utility modules
│   │   ├── notes.py         # Notes generation
│   │   ├── rag_llm.py       # RAG with LLM integration
│   │   ├── learning_mode.py # Learning mode functions
│   │   ├── web_search.py    # DuckDuckGo search
│   │   ├── memory.py        # Memory management
│   │   ├── notes_ingest.py  # Notes vector store
│   │   ├── embeddings.py    # Text embeddings
│   │   ├── vector_store.py  # FAISS operations
│   │   ├── retrieval.py     # MMR retrieval
│   │   ├── ingest.py        # Document ingestion
│   │   └── text_processing.py # Text chunking
│   └── pipelines/           # Data extraction pipelines
│       ├── text_extraction_pipeline.py # Unified pipeline
│       ├── pdf_extractor.py # PDF text extraction
│       ├── doc_extractor.py # DOC/DOCX extraction
│       └── youtube_extractor.py # YouTube transcript extraction
└── data/                    # Data directories
    ├── input/              # Upload files here
    ├── output/             # Extracted text results
    ├── vector_store/       # Primary FAISS index
    ├── notes_index/        # Notes FAISS index
    └── memory/             # Long-term memory storage
```

## 🛠️ **Setup Instructions**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   - Copy `.env` and add your API keys:
     - `GROQ_API_KEY` - For Llama models via Groq
     - `OPENAI_API_KEY` - For OpenAI models (optional)

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 🔧 **Key Components**

### **Notes Generation System**
- `src/utils/notes.py` - Core notes generation with chunk processing
- `src/utils/notes_ingest.py` - Ingests notes into separate vector DB
- `src/utils/text_processing.py` - Text chunking utilities

### **QA Chatbot System**
- `src/utils/rag_llm.py` - RAG with LLM integration
- `src/utils/retrieval.py` - MMR retrieval logic
- `src/utils/ingest.py` - Document ingestion
- `src/utils/vector_store.py` - FAISS operations
- `src/utils/embeddings.py` - Text embeddings

### **Learning Mode System**
- `src/utils/learning_mode.py` - Learning functions
- `src/utils/memory.py` - Memory management

### **Recommended Resources**
- `src/utils/web_search.py` - DuckDuckGo search for articles and videos

### **Data Processing**
- `src/pipelines/` - PDF, DOC, YouTube extraction pipelines

## 🎯 **Usage**

1. **Upload files** in the "Generate Notes" tab (PDFs, DOCs, YouTube URLs)
2. **Generate notes** from uploaded content
3. **Ask questions** in the "QA Chatbot" tab
4. **Learn interactively** in the "Learning Mode" tab
5. **Browse resources** in the "Recommended Resources" tab

## 📝 **Notes**

- The app uses two separate FAISS indexes: one for raw content, one for generated notes
- Memory system maintains conversation history and long-term learning facts
- DuckDuckGo is used for both article and YouTube video recommendations
- Rate limiting and error handling are built-in for API stability

## 🔑 **API Keys Required**

- **Groq API Key** (required) - For Llama models
- **OpenAI API Key** (optional) - For GPT models as fallback

Enjoy your LMS AI Assistant! 🚀
