# Canvas LMS Course Explorer

A comprehensive Streamlit web application for accessing and downloading content from Canvas LMS courses.

## Features

- 🔐 **Secure Authentication**: Login with Canvas API token
- 📚 **Course Selection**: Browse and select from your available courses
- 📄 **Page Access**: Direct links to Canvas pages and content
- 📁 **File Download**: Access to downloadable files and resources
- 📊 **Data Export**: Export course data (assignments, modules, users) to JSON/CSV
- 🎨 **Modern UI**: Clean, responsive web interface
- 📈 **Progress Tracking**: Real-time status updates

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the App

```bash
python run_app_v2.py
```

Or directly with Streamlit:

```bash
streamlit run canvas_streamlit_app_v2.py
```

### 3. Open in Browser

The app will automatically open at: http://localhost:8502

## Usage

### 1. Login
- Enter your Canvas URL (e.g., https://your-school.instructure.com)
- Enter your Canvas API token
- Click "Login"

### 2. Select Course
- Click "Refresh Courses" to load your courses
- Select a course from the dropdown

### 3. Access Content
- **View Assignments**: Browse course assignments with details
- **Explore Modules**: Access course modules and their content
- **Check Users**: View enrolled users in the course
- **Export Data**: Download course data as JSON or CSV

### 4. Download Files
- Use the generated HTML files for direct file access:
  - `canvas_files_download.html` - Direct download links for files
  - `canvas_page_links.html` - Direct links to Canvas pages

## Getting Your Canvas API Token

1. Log into your Canvas account
2. Go to **Account** → **Settings**
3. Scroll down to **Approved Integrations**
4. Click **+ New Access Token**
5. Give it a name and generate the token
6. Copy the token and use it in the app

## File Access Methods

### Method 1: Direct File Downloads
- Open `canvas_files_download.html` in your browser
- Click download links for PDFs and other files
- Files download directly to your computer

### Method 2: Canvas Page Access
- Open `canvas_page_links.html` in your browser
- Click "View Page" to access Canvas pages
- Use browser's "Print to PDF" to save content

### Method 3: Streamlit App
- Use the web interface to browse and export data
- Access assignments, modules, and user information
- Export data in various formats

## Project Structure

```
sf-vibe/
├── canvas_streamlit_app_v2.py    # Main Streamlit application
├── canvas_client.py              # Canvas API client
├── canvas_config.py              # Configuration management
├── run_app_v2.py                 # App launcher
├── canvas_files_download.html    # File download links
├── canvas_page_links.html        # Page access links
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Features in Detail

### Authentication
- Secure token-based authentication
- Automatic credential validation
- Session management with keyring storage

### Course Management
- Real-time course loading
- Course selection interface
- Course information display

### Content Access
- **Assignments**: View, filter, and sort assignments
- **Modules**: Browse course modules and content
- **Users**: See enrolled users and their information
- **Files**: Access downloadable files and resources

### Data Export
- Export assignments to JSON/CSV
- Export modules to JSON/CSV
- Export users to JSON/CSV
- Download all course data at once

### File Management
- Direct download links for files
- Page access links for Canvas content
- Organized HTML interfaces
- Progress tracking

## Technical Details

### Built With
- **Streamlit**: Web application framework
- **Canvas API**: Canvas LMS integration
- **Python**: Core programming language
- **Pandas**: Data processing and export
- **BeautifulSoup**: HTML parsing

### Architecture
- Modular design with separate classes
- Session state management
- Error handling and logging
- Responsive UI components
- Rate limiting and retry logic

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your Canvas URL format
   - Verify your API token is correct
   - Ensure you have proper permissions

2. **No Content Found**
   - Check if the course has content
   - Verify you have access to course materials
   - Contact your instructor if needed

3. **Permission Errors**
   - Some content may require special permissions
   - Use the HTML files for direct access
   - Contact your Canvas administrator

### Getting Help

- Check the app's built-in help sections
- Review error messages for specific issues
- Use the generated HTML files for direct access
- Contact your Canvas administrator for permission issues

## Development

### Running in Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
streamlit run canvas_streamlit_app_v2.py --server.runOnSave true
```

### Key Components

- **CanvasClient**: Handles all Canvas API interactions
- **CanvasConfig**: Manages configuration and credentials
- **StreamlitApp**: Main web interface
- **HTML Generators**: Create direct access links

## License

This project is for educational and personal use. Please respect your institution's terms of service and copyright policies when accessing course materials.

## Support

For issues and questions:
1. Check this README
2. Review error messages in the app
3. Use the generated HTML files for direct access
4. Check Canvas API documentation
5. Contact your Canvas administrator