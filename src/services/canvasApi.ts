import { Course, FileItem, Assignment } from '../store/useCanvasStore';

interface ApiResponse {
  success: boolean;
  error_type?: string;
  error?: string;
  files?: FileItem[];
}

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
      const response = await this.makeBackendRequest(`/api/canvas/courses/${courseId}/files`);
      return response.data;
    } catch (error) {
      if (error instanceof Error && error.message.includes('permission_denied')) {
        throw new Error(
          `Canvas API Permission Error: Your API token lacks the required 'Files' permission scope for course ${courseId}. \n\nTo fix this:\n1. Go to Canvas → Account → Settings → Approved Integrations\n2. Generate a new token with 'Files' scope enabled\n3. Update your token in the application settings\n\nIf you're a student, contact your instructor for file access.`
        );
      }
      if (error instanceof Error && error.message.includes('unauthorized')) {
        throw new Error(
          `Canvas API Authentication Error: Your API token is invalid or expired. Please check your Canvas API token and try again.`
        );
      }
      console.error('Error fetching course files:', error);
      throw new Error(`Failed to load course files: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getCourseAssignments(courseId: number): Promise<Assignment[]> {
    try {
      // For now, return empty array as assignments are not implemented in backend
      return [];
    } catch (error) {
      throw new Error('Failed to fetch assignments: ' + (error as Error).message);
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

  async getCourseModules(courseId: string): Promise<any[]> {
    try {
      console.log(`Fetching modules for course ${courseId}`);
      const response = await this.makeBackendRequest(`/courses/${courseId}/modules?include[]=items`);
      const modules = await response.json();
      console.log(`Successfully fetched ${modules.length} modules`);
      return modules;
    } catch (error) {
      console.error('Error fetching course modules:', error);
      if (error instanceof Error && error.message.includes('permission_denied')) {
        throw new Error('Access forbidden - insufficient permissions. Your Canvas API token may not have the required \'Modules\' permission scope, or you may not have access to modules in this course. Please check your token permissions or contact your Canvas administrator.');
      }
      if (error instanceof Error && error.message.includes('unauthorized')) {
        throw new Error('Authentication failed. Please check your Canvas API token and ensure it is valid and has not expired.');
      }
      throw error;
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