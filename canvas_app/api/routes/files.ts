import express from 'express';
import fs from 'fs';
import path from 'path';

const router = express.Router();

// Get files from downloads folders - specifically from /Users/praveenbhandari/sf-vibe/downloads
router.get('/downloads', async (req, res) => {
  try {
    const downloadsPaths = [
      '/Users/praveenbhandari/sf-vibe/downloads', // Primary downloads folder
      path.join(process.cwd(), 'downloads'), // Canvas app downloads
      path.join(process.cwd(), '..', 'downloads') // Fallback relative path
    ];
    
    const allFiles: any[] = [];
    
    for (const downloadsPath of downloadsPaths) {
      if (fs.existsSync(downloadsPath)) {
        const items = fs.readdirSync(downloadsPath, { withFileTypes: true });
        
        for (const item of items) {
          if (item.isDirectory()) {
            // This is a course folder
            const coursePath = path.join(downloadsPath, item.name);
            const courseFiles = fs.readdirSync(coursePath, { withFileTypes: true });
            
            for (const file of courseFiles) {
              if (file.isFile()) {
                const filePath = path.join(coursePath, file.name);
                const stats = fs.statSync(filePath);
                
                allFiles.push({
                  name: file.name,
                  path: filePath,
                  size: stats.size,
                  modified: stats.mtime,
                  type: getFileType(file.name),
                  course: item.name
                });
              }
            }
          } else if (item.isFile()) {
            // File in root downloads folder
            const filePath = path.join(downloadsPath, item.name);
            const stats = fs.statSync(filePath);
            
            allFiles.push({
              name: item.name,
              path: filePath,
              size: stats.size,
              modified: stats.mtime,
              type: getFileType(item.name),
              course: 'Uncategorized'
            });
          }
        }
      }
    }
    
    res.json(allFiles);
  } catch (error) {
    console.error('Error reading downloads folder:', error);
    res.status(500).json({ error: 'Failed to read downloads folder' });
  }
});

// Helper function to determine file type
function getFileType(filename: string): string {
  const ext = path.extname(filename).toLowerCase();
  
  const typeMap: Record<string, string> = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.mp4': 'video/mp4',
    '.mp3': 'audio/mpeg',
    '.zip': 'application/zip',
    '.rar': 'application/x-rar-compressed'
  };
  
  return typeMap[ext] || 'application/octet-stream';
}

export default router;