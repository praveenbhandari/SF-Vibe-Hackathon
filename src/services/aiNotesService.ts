import { FileItem } from '../store/useCanvasStore';
import { canvasApi } from './canvasApi';

interface AIResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class AINotesService {
  private backendUrl = 'http://localhost:3001';

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

  async extractTextFromFile(file: FileItem, fileBlob: Blob): Promise<string> {
    try {
      if (file.content_type.includes('text/plain')) {
        return await fileBlob.text();
      }
      
      if (file.content_type.includes('application/json')) {
        const jsonText = await fileBlob.text();
        return JSON.stringify(JSON.parse(jsonText), null, 2);
      }
      
      if (file.content_type.includes('text/html')) {
        const htmlText = await fileBlob.text();
        // Basic HTML to text conversion
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlText;
        return tempDiv.textContent || tempDiv.innerText || '';
      }
      
      if (file.content_type.includes('text/markdown')) {
        return await fileBlob.text();
      }
      
      // For PDF and other binary formats, we'll need specialized libraries
      // For now, return a placeholder
      if (file.content_type.includes('pdf')) {
        return `PDF file: ${file.display_name}\n\nNote: PDF text extraction requires additional setup. This is a placeholder for the extracted content.\n\nFile size: ${this.formatFileSize(file.size)}\nCreated: ${new Date(file.created_at).toLocaleDateString()}`;
      }
      
      throw new Error(`Unsupported file type: ${file.content_type}`);
    } catch (error) {
      throw new Error(`Failed to extract text: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async generateNotes(files: FileItem[]): Promise<any> {
    try {
      const response = await this.makeBackendRequest<AIResponse>('/api/ai/generate-notes', {
        method: 'POST',
        body: JSON.stringify({
          files: files.map(file => ({
            id: file.id,
            name: file.display_name,
            contentType: file.content_type
          }))
        })
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to generate notes');
      }

      return response.data;
    } catch (error) {
      console.error('Error generating notes:', error);
      throw new Error('Failed to generate notes. Please try again.');
    }
  }

  async answerQuestion(question: string, context: string): Promise<string> {
    try {
      if (!question.trim()) {
        throw new Error('Question cannot be empty');
      }

      const response = await this.makeBackendRequest<AIResponse>('/api/ai/answer-question', {
        method: 'POST',
        body: JSON.stringify({
          question,
          context
        })
      });

      if (!response.success) {
        throw new Error(response.error || 'Failed to answer question');
      }

      return response.data || 'No answer generated';
    } catch (error) {
      throw new Error(`Failed to answer question: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private createNotesPrompt(text: string, fileName: string): string {
    return `Please analyze the following educational content from "${fileName}" and create comprehensive study notes.

Content:
${text}

Please provide:
1. A clear summary of the main concepts
2. Key points and important details (as a bulleted list)
3. Potential study questions that could help with understanding
4. Any important definitions or formulas mentioned

Format your response in a clear, structured way that would be helpful for studying. Use markdown formatting for better readability.`;
  }

  private parseGeneratedNotes(content: string): { summary?: string; keyPoints?: string[]; questions?: string[] } {
    const lines = content.split('\n');
    let summary = '';
    const keyPoints: string[] = [];
    const questions: string[] = [];
    
    let currentSection = '';
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      if (trimmedLine.toLowerCase().includes('summary')) {
        currentSection = 'summary';
        continue;
      }
      
      if (trimmedLine.toLowerCase().includes('key points') || trimmedLine.toLowerCase().includes('important')) {
        currentSection = 'keyPoints';
        continue;
      }
      
      if (trimmedLine.toLowerCase().includes('questions') || trimmedLine.toLowerCase().includes('study questions')) {
        currentSection = 'questions';
        continue;
      }
      
      if (trimmedLine) {
        if (currentSection === 'summary' && !trimmedLine.startsWith('-') && !trimmedLine.startsWith('*')) {
          summary += trimmedLine + ' ';
        } else if (currentSection === 'keyPoints' && (trimmedLine.startsWith('-') || trimmedLine.startsWith('*'))) {
          keyPoints.push(trimmedLine.replace(/^[-*]\s*/, ''));
        } else if (currentSection === 'questions' && (trimmedLine.startsWith('-') || trimmedLine.startsWith('*') || trimmedLine.includes('?'))) {
          questions.push(trimmedLine.replace(/^[-*]\s*/, ''));
        }
      }
    }
    
    return {
      summary: summary.trim() || undefined,
      keyPoints: keyPoints.length > 0 ? keyPoints : undefined,
      questions: questions.length > 0 ? questions : undefined
    };
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  private formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

export const aiNotesService = new AINotesService();