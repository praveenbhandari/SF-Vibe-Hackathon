const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs').promises;

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Canvas API base URL and token (these would come from the frontend)
let canvasConfig = {
  baseUrl: '',
  apiToken: ''
};

// Set Canvas credentials
app.post('/api/canvas/credentials', (req, res) => {
  const { baseUrl, apiToken } = req.body;
  canvasConfig = { baseUrl, apiToken };
  res.json({ success: true });
});

// Validate Canvas credentials
app.post('/api/canvas/validate', async (req, res) => {
  try {
    const { baseUrl, apiToken } = req.body;
    canvasConfig = { baseUrl, apiToken };
    
    // Make a test request to Canvas API
    const response = await fetch(`${baseUrl}/api/v1/users/self`, {
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Canvas API error: ${response.status} ${response.statusText}`);
    }
    
    const user = await response.json();
    res.json({ success: true, user });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// Get courses
app.get('/api/canvas/courses', async (req, res) => {
  try {
    const { baseUrl, apiToken } = req.query;
    canvasConfig = { baseUrl, apiToken };
    
    const response = await fetch(`${baseUrl}/api/v1/courses?enrollment_state=active&per_page=100`, {
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Canvas API error: ${response.status} ${response.statusText}`);
    }
    
    const courses = await response.json();
    res.json({ success: true, courses });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// Get course files
app.post('/api/canvas/files', async (req, res) => {
  try {
    const { baseUrl, apiToken, courseId } = req.body;
    
    const response = await fetch(`${baseUrl}/api/v1/courses/${courseId}/files?per_page=100`, {
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Canvas API error: ${response.status} ${response.statusText}`);
    }
    
    const files = await response.json();
    res.json({ success: true, data: files });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// Get course assignments
app.post('/api/canvas/assignments', async (req, res) => {
  try {
    const { baseUrl, apiToken, courseId } = req.body;
    
    const response = await fetch(`${baseUrl}/api/v1/courses/${courseId}/assignments?per_page=100`, {
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Canvas API error: ${response.status} ${response.statusText}`);
    }
    
    const assignments = await response.json();
    res.json({ success: true, data: assignments });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// Get course modules
app.post('/api/canvas/modules', async (req, res) => {
  try {
    const { baseUrl, apiToken, courseId } = req.body;
    
    const response = await fetch(`${baseUrl}/api/v1/courses/${courseId}/modules?include[]=items&per_page=100`, {
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Canvas API error: ${response.status} ${response.statusText}`);
    }
    
    const modules = await response.json();
    res.json({ success: true, data: modules });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// Get downloaded files from downloads folder
app.get('/api/files/downloaded', async (req, res) => {
  try {
    const downloadsPath = path.join(__dirname, '..', 'downloads');
    
    // Check if downloads directory exists
    try {
      await fs.access(downloadsPath);
    } catch {
      return res.json({ success: true, files: [] });
    }
    
    const files = await scanDirectory(downloadsPath);
    res.json({ success: true, files });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Helper function to scan directory recursively
async function scanDirectory(dirPath, basePath = '') {
  const files = [];
  const entries = await fs.readdir(dirPath, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    const relativePath = path.join(basePath, entry.name);
    
    if (entry.isDirectory()) {
      const subFiles = await scanDirectory(fullPath, relativePath);
      files.push(...subFiles);
    } else {
      const stats = await fs.stat(fullPath);
      files.push({
        id: Math.random().toString(36).substr(2, 9),
        name: entry.name,
        path: fullPath,
        course: basePath.split('/')[0] || 'Unknown Course',
        size: stats.size,
        type: getMimeType(entry.name),
        lastModified: stats.mtime.toISOString()
      });
    }
  }
  
  return files;
}

// Helper function to get MIME type based on file extension
function getMimeType(filename) {
  const ext = path.extname(filename).toLowerCase();
  const mimeTypes = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.mp4': 'video/mp4',
    '.mp3': 'audio/mpeg',
    '.zip': 'application/zip'
  };
  return mimeTypes[ext] || 'application/octet-stream';
}

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Catch all handler for undefined routes
app.use('*', (req, res) => {
  res.status(404).json({ 
    success: false, 
    error: 'Route not found', 
    path: req.originalUrl 
  });
});

app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
});
