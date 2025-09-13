import { Course, FileItem, Assignment } from '../store/useCanvasStore';

class CanvasApiService {
  private baseUrl: string = '';
  private apiToken: string = '';
  private backendUrl: string = 'http://localhost:3001';

  setCredentials(baseUrl: string, apiToken: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiToken = apiToken;
  }

  private async makeBackendRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.backendUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `Backend error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  async validateCredentials(): Promise<any> {
    try {
      const response = await this.makeBackendRequest<any>('/api/canvas/validate', {
        method: 'POST',
        body: JSON.stringify({
          baseUrl: this.baseUrl,
          apiToken: this.apiToken
        })
      });
      return response.user;
    } catch (error) {
      throw new Error('Failed to validate credentials: ' + (error as Error).message);
    }
  }

  async getCourses(): Promise<Course[]> {
    try {
      const params = new URLSearchParams({
        baseUrl: this.baseUrl,
        apiToken: this.apiToken
      });
      const response = await this.makeBackendRequest<any>(`/api/canvas/courses?${params}`, {
        method: 'GET'
      });
      return response.courses || [];
    } catch (error) {
      throw new Error('Failed to fetch courses: ' + (error as Error).message);
    }
  }

  async getCourseFiles(courseId: number): Promise<FileItem[]> {
    try {
      const response = await this.makeBackendRequest(
        `/api/canvas/files?baseUrl=${encodeURIComponent(this.baseUrl)}&apiToken=${encodeURIComponent(this.apiToken)}&courseId=${courseId}`
      );
      
      if (!response.success) {
        // Handle specific error types
        if (response.error_type === 'permission_denied') {
          throw new Error(`Access forbidden - Your Canvas API token doesn't have permission to access files in this course. Please check that your token has the 'Files' permission scope enabled, or contact your Canvas administrator for assistance.`);
        } else if (response.error_type === 'authentication') {
          throw new Error(`Authentication failed - Your Canvas API token may have expired or is invalid. Please try generating a new token.`);
        } else if (response.error_type === 'not_found') {
          throw new Error(`Course not found - Course ${courseId} doesn't exist or you don't have access to it.`);
        }
        
        throw new Error(response.error || 'Failed to fetch course files');
      }
      
      return response.files || [];
    } catch (error) {
      console.error('Error fetching course files:', error);
      
      // If it's already a formatted error, re-throw it
      if (error instanceof Error && (error.message.includes('Access forbidden') || error.message.includes('Authentication failed'))) {
        throw error;
      }
      
      throw new Error(`Failed to fetch course files: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getCourseAssignments(courseId: number): Promise<Assignment[]> {
    try {
      const response = await this.makeBackendRequest<any>('/api/canvas/assignments', {
        method: 'POST',
        body: JSON.stringify({
          baseUrl: this.baseUrl,
          apiToken: this.apiToken,
          courseId: courseId
        })
      });
      return response.data || [];
    } catch (error) {
      throw new Error('Failed to fetch assignments: ' + (error as Error).message);
    }
  }

  async getCourseModules(courseId: number): Promise<any[]> {
    try {
      const response = await this.makeBackendRequest<any>('/api/canvas/modules', {
        method: 'POST',
        body: JSON.stringify({
          baseUrl: this.baseUrl,
          apiToken: this.apiToken,
          courseId: courseId
        })
      });
      return response.data || [];
    } catch (error) {
      throw new Error('Failed to fetch modules: ' + (error as Error).message);
    }
  }

  async getDownloadedFiles(): Promise<any[]> {
    try {
      const response = await this.makeBackendRequest<any>('/api/files/downloaded', {
        method: 'GET'
      });
      return response.files || [];
    } catch (error) {
      throw new Error('Failed to fetch downloaded files: ' + (error as Error).message);
    }
  }

  async downloadFile(fileUrl: string): Promise<Blob> {
    try {
      const response = await fetch(fileUrl, {
        headers: {
          'Authorization': `Bearer ${this.apiToken}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to download file: ${response.status} ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      throw new Error('Failed to download file: ' + (error as Error).message);
    }
  }

  async getFileContent(file: FileItem): Promise<string> {
    try {
      const response = await this.makeBackendRequest<any>('/api/canvas/extract-text', {
        method: 'POST',
        body: JSON.stringify({
          baseUrl: this.baseUrl,
          apiToken: this.apiToken,
          fileId: file.id,
          fileName: file.display_name,
          contentType: file.content_type
        })
      });
      return response.data || 'No content extracted';
    } catch (error) {
      throw new Error('Failed to extract file content: ' + (error as Error).message);
    }
  }

  // Helper method to get file icon based on content type
  getFileIcon(contentType: string): string {
    if (contentType.includes('pdf')) return '📄';
    if (contentType.includes('image')) return '🖼️';
    if (contentType.includes('video')) return '🎥';
    if (contentType.includes('audio')) return '🎵';
    if (contentType.includes('text')) return '📝';
    if (contentType.includes('spreadsheet') || contentType.includes('excel')) return '📊';
    if (contentType.includes('presentation') || contentType.includes('powerpoint')) return '📈';
    if (contentType.includes('word') || contentType.includes('document')) return '📄';
    if (contentType.includes('zip') || contentType.includes('archive')) return '📦';
    return '📁';
  }

  // Helper method to format file size
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

export const canvasApi = new CanvasApiService();