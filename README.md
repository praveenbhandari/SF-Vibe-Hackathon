# Canvas API Python Client

A comprehensive Python application for retrieving and exporting data from Canvas LMS using the Canvas API.

## Features

- **Authentication**: Secure Canvas API token management
- **Data Retrieval**: Fetch courses, assignments, grades, users, and submissions
- **Export Formats**: Export data to CSV, JSON, and Excel formats
- **CLI Interface**: Easy-to-use command-line interface
- **Rate Limiting**: Built-in rate limiting and retry logic
- **Caching**: Intelligent caching for improved performance
- **Analytics**: Course and assignment analytics

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Canvas API Token

1. Log into your Canvas account
2. Go to Account → Settings → Approved Integrations
3. Click "+ New Access Token"
4. Generate a new token and copy it

### Environment Setup

Create a `.env` file in the project directory:

```env
CANVAS_API_TOKEN=your_canvas_api_token_here
CANVAS_BASE_URL=https://your-institution.instructure.com
```

## Usage

### Command Line Interface

Run the CLI application:

```bash
python canvas_cli.py
```

### Available Commands

1. **Authentication Test**
   - Test your Canvas API connection

2. **Retrieve Courses**
   - Fetch all courses you have access to
   - Export to CSV, JSON, or Excel

3. **Retrieve Assignments**
   - Fetch assignments for specific courses
   - Filter by course ID

4. **Retrieve Grades**
   - Get grade information
   - Export grade summaries

5. **Course Analytics**
   - Generate course statistics and analytics

6. **Search Functionality**
   - Search courses and assignments

### Python API Usage

```python
from canvas_client import CanvasClient
from canvas_data_services import CanvasDataServices
from canvas_export import CanvasExporter

# Initialize client
client = CanvasClient(
    base_url="https://your-institution.instructure.com",
    access_token="your_token_here"
)

# Initialize services
data_services = CanvasDataServices(client)
exporter = CanvasExporter()

# Get courses
courses = data_services.get_courses_with_details()

# Export to CSV
exporter.export_to_csv(courses, "courses.csv")

# Get assignments for a course
assignments = data_services.get_assignments_with_details(course_id=12345)

# Export to Excel
exporter.export_to_excel(assignments, "assignments.xlsx")
```

## File Structure

```
canvas-api-client/
├── canvas_client.py          # Main Canvas API client
├── canvas_data_services.py   # Data retrieval services
├── canvas_export.py          # Export functionality
├── canvas_cli.py             # Command-line interface
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .env                      # Environment configuration (create this)
```

## API Rate Limiting

The application includes built-in rate limiting to respect Canvas API limits:
- Default: 10 requests per second
- Automatic retry with exponential backoff
- Configurable rate limits

## Error Handling

- Comprehensive error handling for API failures
- Automatic retry for transient errors
- Detailed logging for debugging

## Security

- API tokens are stored securely in environment variables
- No hardcoded credentials in source code
- Secure token validation

## Troubleshooting

### Common Issues

1. **Invalid Token Error**
   - Verify your Canvas API token is correct
   - Check that the token has appropriate permissions

2. **Connection Errors**
   - Verify your Canvas base URL is correct
   - Check your internet connection

3. **Permission Errors**
   - Ensure your Canvas account has access to the requested data
   - Some data may require instructor or admin privileges

### Logging

The application logs important events and errors. Check the console output for detailed information about API calls and any issues.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is provided as-is for educational and administrative purposes.