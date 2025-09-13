/**
 * Canvas API routes for handling Canvas LMS integration
 */
import { Router, type Request, type Response } from 'express'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const router = Router()

// Helper function to execute Python Canvas client
const executePythonScript = (scriptName: string, args: string[] = []): Promise<any> => {
  return new Promise((resolve, reject) => {
    const pythonPath = path.join(__dirname, '../../')
    const python = spawn('python3', [scriptName, ...args], {
      cwd: pythonPath,
      stdio: ['pipe', 'pipe', 'pipe']
    })

    let stdout = ''
    let stderr = ''

    python.stdout.on('data', (data) => {
      stdout += data.toString()
    })

    python.stderr.on('data', (data) => {
      stderr += data.toString()
    })

    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout)
          resolve(result)
        } catch (error) {
          resolve({ success: true, data: stdout })
        }
      } else {
        reject(new Error(`Python script failed: ${stderr}`))
      }
    })

    python.on('error', (error) => {
      reject(new Error(`Failed to start Python process: ${error.message}`))
    })
  })
}

/**
 * Validate Canvas credentials
 * POST /api/canvas/validate
 */
router.post('/validate', async (req: Request, res: Response): Promise<void> => {
  try {
    const { baseUrl, apiToken } = req.body

    if (!baseUrl || !apiToken) {
      res.status(400).json({
        success: false,
        error: 'Base URL and API token are required'
      })
      return
    }

    // Create a temporary Python script to validate credentials
    const validationScript = `
import sys
import json
from canvas_client import CanvasClient

try:
    client = CanvasClient(base_url='${baseUrl}', api_token='${apiToken}')
    user_info = client.validate_credentials()
    print(json.dumps({
        'success': True,
        'user': {
            'id': user_info.get('id'),
            'name': user_info.get('name'),
            'email': user_info.get('email')
        }
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e)
    }))
`

    // Write temporary script and execute
    const fs = await import('fs')
    const tempScript = path.join(__dirname, '../../temp_validate.py')
    fs.writeFileSync(tempScript, validationScript)

    try {
      const result = await executePythonScript('temp_validate.py')
      
      // Clean up temp file
      fs.unlinkSync(tempScript)
      
      if (result.success) {
        res.json({
          success: true,
          user: result.user
        })
      } else {
        res.status(401).json({
          success: false,
          error: result.error
        })
      }
    } catch (error) {
      // Clean up temp file on error
      if (fs.existsSync(tempScript)) {
        fs.unlinkSync(tempScript)
      }
      throw error
    }
  } catch (error) {
    console.error('Canvas validation error:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to validate Canvas credentials'
    })
  }
})

/**
 * Get user courses
 * GET /api/canvas/courses
 */
router.get('/courses', async (req: Request, res: Response): Promise<void> => {
  try {
    const { baseUrl, apiToken } = req.query

    if (!baseUrl || !apiToken) {
      res.status(400).json({
        success: false,
        error: 'Base URL and API token are required'
      })
      return
    }

    const coursesScript = `
import sys
import json
from canvas_client import CanvasClient

try:
    client = CanvasClient(base_url='${baseUrl}', api_token='${apiToken}')
    courses = client.get_courses()
    print(json.dumps({
        'success': True,
        'courses': courses
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e)
    }))
`

    const fs = await import('fs')
    const tempScript = path.join(__dirname, '../../temp_courses.py')
    fs.writeFileSync(tempScript, coursesScript)

    try {
      const result = await executePythonScript('temp_courses.py')
      
      // Clean up temp file
      fs.unlinkSync(tempScript)
      
      if (result.success) {
        res.json({
          success: true,
          courses: result.courses
        })
      } else {
        res.status(500).json({
          success: false,
          error: result.error
        })
      }
    } catch (error) {
      // Clean up temp file on error
      if (fs.existsSync(tempScript)) {
        fs.unlinkSync(tempScript)
      }
      throw error
    }
  } catch (error) {
    console.error('Get courses error:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve courses'
    })
  }
})

/**
 * Get course files
 * GET /api/canvas/files
 */
router.get('/files', async (req: Request, res: Response): Promise<void> => {
  try {
    const { baseUrl, apiToken, courseId } = req.query

    if (!baseUrl || !apiToken || !courseId) {
      res.status(400).json({
        success: false,
        error: 'Base URL, API token, and course ID are required'
      })
      return
    }

    console.log(`Fetching files for course ${courseId} from ${baseUrl}`)

    const filesScript = `
import sys
import json
from canvas_client import CanvasClient, CanvasAPIError, AuthenticationError

try:
    client = CanvasClient(base_url='${baseUrl}', api_token='${apiToken}')
    files = client.get_course_files(${courseId})
    print(json.dumps({
        'success': True,
        'files': files
    }))
except AuthenticationError as e:
    print(json.dumps({
        'success': False,
        'error': str(e),
        'error_type': 'authentication',
        'status_code': 401
    }))
except CanvasAPIError as e:
    error_msg = str(e)
    status_code = 500
    error_type = 'api_error'
    
    # Check for specific permission errors
    if 'forbidden' in error_msg.lower() or 'insufficient permissions' in error_msg.lower():
        status_code = 403
        error_type = 'permission_denied'
        error_msg = f"Access forbidden - insufficient permissions. Your Canvas API token may not have the required 'Files' permission scope, or you may not have access to files in course ${courseId}. Please check your token permissions or contact your Canvas administrator."
    elif 'not found' in error_msg.lower():
        status_code = 404
        error_type = 'not_found'
        error_msg = f"Course ${courseId} not found or you don't have access to it."
    
    print(json.dumps({
        'success': False,
        'error': error_msg,
        'error_type': error_type,
        'status_code': status_code
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e),
        'error_type': 'unknown',
        'status_code': 500
    }))
`

    const fs = await import('fs')
    const tempScript = path.join(__dirname, '../../temp_files.py')
    fs.writeFileSync(tempScript, filesScript)

    try {
      const result = await executePythonScript('temp_files.py')
      
      // Clean up temp file
      fs.unlinkSync(tempScript)
      
      if (result.success) {
        console.log(`Successfully retrieved ${result.files?.length || 0} files for course ${courseId}`)
        res.json({
          success: true,
          files: result.files
        })
      } else {
        const statusCode = result.status_code || 500
        console.error(`Files API error for course ${courseId}:`, result.error)
        console.error(`Error type: ${result.error_type}, Status: ${statusCode}`)
        
        res.status(statusCode).json({
          success: false,
          error: result.error,
          error_type: result.error_type
        })
      }
    } catch (error) {
      // Clean up temp file on error
      if (fs.existsSync(tempScript)) {
        fs.unlinkSync(tempScript)
      }
      throw error
    }
  } catch (error) {
    console.error('Get files error:', error)
    console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace')
    console.error('Request details:', {
      courseId,
      baseUrl: req.body.baseUrl ? '[REDACTED]' : 'missing',
      apiToken: req.body.apiToken ? '[REDACTED]' : 'missing'
    })
    
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve files - internal server error',
      details: process.env.NODE_ENV === 'development' ? error instanceof Error ? error.message : String(error) : undefined
    })
  }
})

/**
 * Extract text from file
 * POST /api/canvas/extract-text
 */
router.post('/extract-text', async (req: Request, res: Response): Promise<void> => {
  try {
    const { baseUrl, apiToken, fileId } = req.body

    if (!baseUrl || !apiToken || !fileId) {
      res.status(400).json({
        success: false,
        error: 'Base URL, API token, and file ID are required'
      })
      return
    }

    const extractScript = `
import sys
import json
import tempfile
import os
from canvas_client import CanvasClient
from canvas_file_downloader import CanvasFileDownloader

try:
    client = CanvasClient(base_url='${baseUrl}', api_token='${apiToken}')
    downloader = CanvasFileDownloader(client)
    
    # Download and extract text from file
    content, filename, content_type = client.download_file_content(${fileId})
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Extract text using the downloader's text extraction
        extracted_text = downloader.extract_text_from_file(temp_path, filename)
        
        print(json.dumps({
            'success': True,
            'text': extracted_text,
            'filename': filename,
            'content_type': content_type
        }))
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e)
    }))
`

    const fs = await import('fs')
    const tempScript = path.join(__dirname, '../../temp_extract.py')
    fs.writeFileSync(tempScript, extractScript)

    try {
      const result = await executePythonScript('temp_extract.py')
      
      // Clean up temp file
      fs.unlinkSync(tempScript)
      
      if (result.success) {
        res.json({
          success: true,
          text: result.text,
          filename: result.filename,
          contentType: result.content_type
        })
      } else {
        res.status(500).json({
          success: false,
          error: result.error
        })
      }
    } catch (error) {
      // Clean up temp file on error
      if (fs.existsSync(tempScript)) {
        fs.unlinkSync(tempScript)
      }
      throw error
    }
  } catch (error) {
    console.error('Extract text error:', error)
    console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace')
    console.error('Request details:', {
      fileId: req.body.fileId,
      baseUrl: req.body.baseUrl ? '[REDACTED]' : 'missing',
      apiToken: req.body.apiToken ? '[REDACTED]' : 'missing'
    })
    
    res.status(500).json({
      success: false,
      error: 'Failed to extract text from file',
      details: process.env.NODE_ENV === 'development' ? error instanceof Error ? error.message : String(error) : undefined
    })
  }
})

/**
 * Test Canvas API permissions
 * POST /api/canvas/test-permissions
 */
router.post('/test-permissions', async (req: Request, res: Response): Promise<void> => {
  try {
    const { baseUrl, apiToken, courseId } = req.body

    if (!baseUrl || !apiToken) {
      res.status(400).json({
        success: false,
        error: 'Base URL and API token are required'
      })
      return
    }

    console.log(`Testing Canvas API permissions for ${baseUrl}`)

    const testScript = `
import sys
import json
from canvas_client import CanvasClient, CanvasAPIError, AuthenticationError

try:
    client = CanvasClient(base_url='${baseUrl}', api_token='${apiToken}')
    
    # Test 1: Validate credentials
    print("Testing credential validation...")
    user = client.validate_credentials()
    
    # Test 2: Get courses
    print("Testing course access...")
    courses = client.get_courses()
    
    # Test 3: Get files for specific course (if courseId provided)
    files_test = None
    if '${courseId}' and '${courseId}' != 'undefined':
        print(f"Testing file access for course ${courseId}...")
        try:
            files_test = client.get_course_files(${courseId})
        except Exception as e:
            files_test = {'error': str(e), 'type': type(e).__name__}
    
    print(json.dumps({
        'success': True,
        'user': user,
        'courses_count': len(courses) if courses else 0,
        'files_test': files_test,
        'permissions': {
            'can_access_profile': True,
            'can_access_courses': True,
            'can_access_files': files_test is not None and not isinstance(files_test, dict)
        }
    }))
except AuthenticationError as e:
    print(json.dumps({
        'success': False,
        'error': str(e),
        'error_type': 'authentication',
        'status_code': 401
    }))
except CanvasAPIError as e:
    error_msg = str(e)
    status_code = 500
    error_type = 'api_error'
    
    if 'forbidden' in error_msg.lower() or 'insufficient permissions' in error_msg.lower():
        status_code = 403
        error_type = 'permission_denied'
    
    print(json.dumps({
        'success': False,
        'error': error_msg,
        'error_type': error_type,
        'status_code': status_code
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e),
        'error_type': 'unknown',
        'status_code': 500
    }))
`

    const fs = await import('fs')
    const tempScript = path.join(__dirname, '../../temp_test_permissions.py')
    fs.writeFileSync(tempScript, testScript)

    try {
      const result = await executePythonScript('temp_test_permissions.py')
      
      // Clean up temp file
      fs.unlinkSync(tempScript)
      
      if (result.success) {
        console.log('Canvas API permissions test completed successfully')
        res.json({
          success: true,
          ...result
        })
      } else {
        const statusCode = result.status_code || 500
        console.error('Canvas API permissions test failed:', result.error)
        
        res.status(statusCode).json({
          success: false,
          error: result.error,
          error_type: result.error_type
        })
      }
    } catch (error) {
      // Clean up temp file on error
      if (fs.existsSync(tempScript)) {
        fs.unlinkSync(tempScript)
      }
      throw error
    }
  } catch (error) {
    console.error('Test permissions error:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to test permissions - internal server error'
    })
  }
})

export default router