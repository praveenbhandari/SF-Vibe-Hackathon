# MESA Hackathon - Canvas LMS AI Assistant

A comprehensive AI-powered learning management system assistant built with Streamlit, featuring Canvas LMS integration, AI-powered notes generation, and guided learning capabilities.

## Features

### 🎓 Canvas LMS Integration
- **Course Management**: View assignments, modules, and files from Canvas courses
- **File Processing**: Download and process course materials locally
- **User Management**: Access student information and course rosters

### 🤖 AI-Powered Features
- **Smart Notes Generation**: Automatically generate well-formatted notes from course materials
- **Guided Learning**: Step-by-step topic teaching with personalized learning paths
- **RAG Demo**: Retrieval Augmented Generation for intelligent document search

### 🔍 Web Search Integration
- **Resource Recommendations**: Fetch relevant YouTube videos and articles using DuckDuckGo
- **Fallback Resources**: Curated learning materials when web search fails
- **Smart Filtering**: Filter out irrelevant or low-quality content

### 🛠️ Technical Features
- **Groq API Integration**: Fast AI responses using Groq's optimized inference
- **Rate Limiting**: Intelligent retry logic for API rate limits
- **Error Handling**: Robust error handling with graceful degradation
- **Responsive UI**: Clean, modern interface built with Streamlit

## Project Structure

```
MESA-Hackathon/
├── app.py                          # Main Streamlit application
├── canvas_config.py                # Canvas API configuration
├── canvas_client.py                # Canvas API client
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── learning_mode.py            # Guided learning functionality
│   ├── notes.py                    # AI notes generation
│   ├── rag_llm.py                  # RAG LLM utilities
│   ├── text_processing.py          # Text chunking and processing
│   └── web_search.py               # Web search and resource fetching
├── requirements.txt                # Python dependencies
├── vercel.json                     # Vercel deployment configuration
├── Procfile                        # Process file for deployment
├── package.json                    # Node.js configuration
└── README.md                       # This file
```

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/praveenbhandari/MESA-Hackathon.git
   cd MESA-Hackathon
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
LLM_BACKEND=groq

# Canvas API Configuration
CANVAS_BASE_URL=https://your-school.instructure.com
CANVAS_API_TOKEN=your_canvas_api_token_here
```

## Deployment

### Vercel Deployment

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Vercel**
   ```bash
   vercel
   ```

3. **Set environment variables in Vercel dashboard**
   - `GROQ_API_KEY`
   - `CANVAS_BASE_URL`
   - `CANVAS_API_TOKEN`

## Usage

### Getting Started

1. **Configure Canvas API**: Enter your Canvas API credentials in the sidebar
2. **Select Course**: Choose a course from the dropdown menu
3. **Explore Features**: Navigate through different tabs to access various features

### Features Guide

#### 📝 Assignments Tab
- View all assignments for the selected course
- See due dates, descriptions, and submission status
- Access assignment details and requirements

#### 📚 Modules Tab
- Browse course modules and their contents
- Access module descriptions and learning objectives
- Navigate through course structure

#### 📁 Files Tab
- View and download course files
- Process documents for AI analysis
- Organize course materials

#### 🤖 AI Notes Tab
- Generate AI-powered notes from course materials
- Process PDFs, PowerPoints, and other documents
- Create well-formatted, comprehensive notes

#### 🎓 Guided Learning Tab
- Get personalized learning recommendations
- Access step-by-step topic explanations
- Find relevant YouTube videos and articles
- Receive quiz questions and assignments

#### 💬 RAG Demo Tab
- Search through course documents using natural language
- Get intelligent answers based on course content
- Explore document relationships and connections

## API Integration

### Canvas LMS API
- **Authentication**: OAuth2 and API token support
- **Rate Limiting**: Built-in rate limiting and retry logic
- **Error Handling**: Comprehensive error handling for API failures

### Groq API
- **Model**: llama-3.1-8b-instant for fast inference
- **Rate Limiting**: Exponential backoff for rate limit handling
- **Error Recovery**: Automatic retry with intelligent delays

### DuckDuckGo Search
- **Web Search**: Fetch relevant learning resources
- **Video Search**: Find educational YouTube content
- **Article Search**: Discover helpful articles and documentation
- **Fallback System**: Curated resources when search fails

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Canvas LMS** for providing the learning management system API
- **Groq** for fast AI inference capabilities
- **Streamlit** for the web application framework
- **DuckDuckGo** for web search functionality

## Support

For support and questions, please open an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ for the MESA Hackathon**