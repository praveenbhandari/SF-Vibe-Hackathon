import React, { useState, useEffect } from 'react';
import { useCanvasStore, DownloadedFile } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import { FileText, Download, Brain, RefreshCw, FolderOpen, AlertCircle } from 'lucide-react';

const AINotesTab: React.FC = () => {
  const { downloadedFiles, setDownloadedFiles, setSelectedFile, setActiveTab } = useCanvasStore();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFileLocal] = useState<DownloadedFile | null>(null);

  // Load downloaded files from the downloads folder
  const loadDownloadedFiles = async () => {
    setIsLoading(true);
    try {
      const files = await canvasApi.getDownloadedFiles();
      setDownloadedFiles(files);
    } catch (error) {
      console.error('Error loading downloaded files:', error);
      // Fallback to mock data if backend is not available
      const mockFiles: DownloadedFile[] = [
        {
          id: '1',
          name: 'lecture-1.pdf',
          path: '/downloads/course_123/lecture-1.pdf',
          course: 'Advanced Algorithms',
          size: 2048576,
          type: 'application/pdf',
          lastModified: '2024-01-15T10:30:00Z'
        },
        {
          id: '2',
          name: 'assignment-1.docx',
          path: '/downloads/course_123/assignment-1.docx',
          course: 'Advanced Algorithms',
          size: 1024000,
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          lastModified: '2024-01-14T15:45:00Z'
        },
        {
          id: '3',
          name: 'notes.txt',
          path: '/downloads/course_123/notes.txt',
          course: 'Advanced Algorithms',
          size: 512000,
          type: 'text/plain',
          lastModified: '2024-01-13T09:20:00Z'
        }
      ];
      setDownloadedFiles(mockFiles);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDownloadedFiles();
  }, []);

  const handleFileSelect = (file: DownloadedFile) => {
    setSelectedFileLocal(file);
    // Convert DownloadedFile to FileItem format for compatibility
    const fileItem = {
      id: parseInt(file.id),
      uuid: file.id,
      folder_id: 0,
      display_name: file.name,
      filename: file.name,
      content_type: file.type,
      url: file.path,
      size: file.size,
      created_at: file.lastModified,
      updated_at: file.lastModified,
      locked: false,
      hidden: false,
      hidden_for_user: false,
      modified_at: file.lastModified,
      mime_class: file.type.split('/')[0],
      locked_for_user: false
    };
    setSelectedFile(fileItem);
    setActiveTab('notes');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string): string => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('image')) return '🖼️';
    if (type.includes('video')) return '🎥';
    if (type.includes('audio')) return '🎵';
    if (type.includes('text')) return '📝';
    if (type.includes('spreadsheet') || type.includes('excel')) return '📊';
    if (type.includes('presentation') || type.includes('powerpoint')) return '📈';
    if (type.includes('word') || type.includes('document')) return '📄';
    if (type.includes('zip') || type.includes('archive')) return '📦';
    return '📁';
  };

  const groupFilesByCourse = (files: DownloadedFile[]) => {
    const grouped: { [key: string]: DownloadedFile[] } = {};
    files.forEach(file => {
      if (!grouped[file.course]) {
        grouped[file.course] = [];
      }
      grouped[file.course].push(file);
    });
    return grouped;
  };

  const groupedFiles = groupFilesByCourse(downloadedFiles);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI Notes</h1>
            <p className="mt-2 text-gray-600">
              Select downloaded files to generate AI-powered notes and summaries
            </p>
          </div>
          <button
            onClick={loadDownloadedFiles}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Files</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center space-x-3">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
            <span className="text-gray-600">Loading downloaded files...</span>
          </div>
        </div>
      ) : downloadedFiles.length === 0 ? (
        <div className="text-center py-12">
          <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Downloaded Files</h3>
          <p className="text-gray-600 mb-6">
            Download some course files first to generate AI notes
          </p>
          <button
            onClick={() => setActiveTab('files')}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Go to Files Tab</span>
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(groupedFiles).map(([courseName, files]) => (
            <div key={courseName} className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">{courseName}</h2>
                <p className="text-sm text-gray-600">{files.length} files available</p>
              </div>
              
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {files.map((file) => (
                    <div
                      key={file.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md ${
                        selectedFile?.id === file.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleFileSelect(file)}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="text-2xl">{getFileIcon(file.type)}</div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {file.name}
                          </h3>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatFileSize(file.size)}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(file.lastModified).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex-shrink-0">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFileSelect(file);
                            }}
                            className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                            title="Generate AI Notes"
                          >
                            <Brain className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedFile && (
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-3">
            <Brain className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-900">
                Selected: {selectedFile.name}
              </p>
              <p className="text-xs text-blue-700">
                Click "Generate Notes" tab to create AI notes for this file
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AINotesTab;