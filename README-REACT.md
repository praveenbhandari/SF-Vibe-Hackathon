# Canvas AI Study Assistant - React Frontend

A React-based frontend for the Canvas LMS integration that provides AI-powered note generation and course content management.

## Architecture

- **Frontend**: React app in `src/` directory
- **Backend**: Express.js API server in `backend/` directory
- **Canvas Integration**: Python backend in `canvas_app/` directory

## Quick Start

### Option 1: Start Everything (Recommended)
```bash
./start-dev.sh
```

### Option 2: Manual Start

#### 1. Start Backend API Server
```bash
cd backend
npm install
npm start
```

#### 2. Start React Frontend
```bash
cd src
npm install
npm start
```

#### 3. Start Canvas Python Backend (Optional)
```bash
cd canvas_app
pip install -r requirements.txt
python canvas_streamlit_app_v2.py
```

## Features

### 🔐 Authentication
- Secure Canvas API token authentication
- Persistent login with token caching
- Automatic logout on token expiration

### 📚 Course Management
- View all enrolled courses
- Course selection and navigation
- Course information and statistics

### 📁 File Management
- Browse Canvas course files
- Download files to local storage
- File type detection and icons
- File size and metadata display

### 🤖 AI Notes Generation
- Select downloaded files for AI processing
- Generate intelligent notes and summaries
- Support for PDF, DOCX, TXT, and PPT files
- Interactive Q&A with generated content

### 📊 Data Export
- Export course data to JSON/CSV
- Batch export all courses
- Download course materials

## Tab Structure

1. **Courses** - Course selection and overview
2. **Canvas Files** - Browse and download Canvas files
3. **AI Notes** - Select downloaded files for AI processing
4. **Generate Notes** - AI note generation interface
5. **Q&A** - Interactive Q&A with generated content

## API Endpoints

### Backend (Express.js - Port 3001)
- `POST /api/canvas/validate` - Validate Canvas credentials
- `GET /api/canvas/courses` - Get user courses
- `POST /api/canvas/files` - Get course files
- `POST /api/canvas/assignments` - Get course assignments
- `POST /api/canvas/modules` - Get course modules
- `GET /api/files/downloaded` - Get downloaded files

### Canvas Backend (Python - Port 8501)
- Canvas API integration
- File processing and text extraction
- AI note generation

## Configuration

### Environment Variables
Create a `.env` file in the root directory:
```
REACT_APP_BACKEND_URL=http://localhost:3001
REACT_APP_CANVAS_BACKEND_URL=http://localhost:8501
```

### Canvas API Token
1. Log into your Canvas account
2. Go to Account → Settings
3. Scroll to "Approved Integrations"
4. Click "+ New Access Token"
5. Enter a purpose and generate the token
6. Copy and paste the token in the app

## File Structure

```
src/
├── components/          # React components
│   ├── CanvasAuth.tsx   # Authentication component
│   ├── CourseSelection.tsx # Course selection
│   ├── FileBrowser.tsx  # File browsing
│   ├── AINotesTab.tsx   # AI Notes tab
│   └── ...
├── services/           # API services
│   └── canvasApi.ts    # Canvas API client
├── store/              # State management
│   └── useCanvasStore.ts # Zustand store
└── App.tsx             # Main app component

backend/
├── server.js           # Express.js server
└── package.json        # Backend dependencies

canvas_app/
├── canvas_streamlit_app_v2.py # Python Canvas app
└── requirements.txt    # Python dependencies
```

## Development

### Adding New Features
1. Create components in `src/components/`
2. Add API methods in `src/services/canvasApi.ts`
3. Update store in `src/store/useCanvasStore.ts`
4. Add backend endpoints in `backend/server.js`

### State Management
The app uses Zustand for state management with persistence:
- Authentication state
- Course and file data
- UI state and navigation
- Generated notes and Q&A sessions

### Styling
- TailwindCSS for styling
- Lucide React for icons
- Responsive design
- Dark/light mode support

## Troubleshooting

### Common Issues

1. **Backend not starting**
   - Check if port 3001 is available
   - Run `npm install` in backend directory

2. **Canvas API errors**
   - Verify API token is valid
   - Check Canvas URL format
   - Ensure token has required permissions

3. **File download issues**
   - Check Canvas permissions
   - Verify file URLs are accessible
   - Check network connectivity

4. **AI Notes not working**
   - Ensure Python backend is running
   - Check file formats are supported
   - Verify AI service configuration

### Debug Mode
Enable debug logging by setting:
```javascript
localStorage.setItem('debug', 'true');
```

## Production Deployment

### Frontend
```bash
cd src
npm run build
# Deploy build/ directory to your hosting service
```

### Backend
```bash
cd backend
npm install --production
npm start
```

### Environment
- Set production environment variables
- Configure CORS for production domains
- Set up SSL certificates
- Configure reverse proxy if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details
