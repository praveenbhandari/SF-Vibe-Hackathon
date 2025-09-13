import React, { useState, useEffect } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import {
  FileText, Download, Brain, Clock, Search,
  FolderOpen, File, AlertCircle
} from 'lucide-react';

interface DownloadedFile {
  name: string;
  path: string;
  size: number;
  modified: Date;
  type: string;
  course?: string;
}

const AINotesTab: React.FC = () => {
  const { 
    downloadedFiles, 
    addDownloadedFile, 
    setSelectedFile, 
    setActiveTab,
    selectedFile 
  } = useCanvasStore();
  const [localFiles, setLocalFiles] = useState<DownloadedFile[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load files from downloads folder and subfolders
  useEffect(() => {
    loadDownloadedFiles();
  }, []);

  const loadDownloadedFiles = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch files from backend API - specifically from /Users/praveenbhandari/sf-vibe/downloads
      const response = await fetch('/api/files/downloads');
      if (response.ok) {
        const files = await response.json();
        // Filter and organize files from the downloads folder
        const processedFiles = files.map((file: any) => ({
          ...file,
          modified: new Date(file.modified),
          // Ensure course name is properly formatted
          course: file.course || 'Uncategorized'
        }));
        setLocalFiles(processedFiles);
      } else {
        setError('Failed to load files from downloads folder');
      }
    } catch (err) {
      setError('Failed to connect to file service');
      console.error('Error loading files:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />;
    if (type.includes('word') || type.includes('document')) return <FileText className="w-5 h-5 text-blue-500" />;
    if (type.includes('text')) return <File className="w-5 h-5 text-gray-500" />;
    return <File className="w-5 h-5 text-gray-400" />;
  };

  const filteredFiles = localFiles.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (file.course && file.course.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Group files by course
  const filesByCourse = filteredFiles.reduce((acc, file) => {
    const course = file.course || 'Uncategorized';
    if (!acc[course]) {
      acc[course] = [];
    }
    acc[course].push(file);
    return acc;
  }, {} as Record<string, DownloadedFile[]>);

  const courses = Object.keys(filesByCourse).sort();

  const handleGenerateNotes = (file: DownloadedFile) => {
    try {
      console.log('Generating notes for file:', file);
      
      // Check if setSelectedFile is available
      if (!setSelectedFile) {
        console.error('setSelectedFile is not available from store');
        setError('Store function not available. Please refresh the page.');
        return;
      }
      
      // Convert local file to FileItem format for compatibility
      const fileItem = {
        id: Date.now(), // Generate a temporary ID
        uuid: `local-${Date.now()}`,
        folder_id: 0,
        display_name: file.name,
        filename: file.name,
        content_type: file.type,
        url: file.path,
        size: file.size,
        created_at: file.modified.toISOString(),
        updated_at: file.modified.toISOString(),
        locked: false,
        hidden: false,
        hidden_for_user: false,
        modified_at: file.modified.toISOString(),
        mime_class: file.type.split('/')[0],
        locked_for_user: false
      };
      
      console.log('Setting selected file:', fileItem);
      console.log('setSelectedFile function:', setSelectedFile);
      
      // Call setSelectedFile with proper error handling
      try {
        setSelectedFile(fileItem);
        console.log('Successfully set selected file');
      } catch (storeError) {
        console.error('Error calling setSelectedFile:', storeError);
        setError('Failed to set selected file. Please try again.');
        return;
      }
      
      setActiveTab('notes');
    } catch (error) {
      console.error('Error in handleGenerateNotes:', error);
      setError('Failed to generate notes. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading downloaded files...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AI Notes</h1>
        </div>
        <p className="text-gray-600">
          Generate AI-powered notes from files in your downloads folder. Each subfolder appears as a separate course for easy organization.
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search files in downloads folder..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
          <button
            onClick={loadDownloadedFiles}
            className="ml-auto text-red-600 hover:text-red-700 font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Files by Course */}
      {filteredFiles.length === 0 ? (
        <div className="text-center py-12">
          <FolderOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchTerm ? 'No files found' : 'No files in downloads folder'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm 
              ? 'Try adjusting your search terms'
              : 'Add files to your downloads folder to get started with AI note generation. Each subfolder will appear as a separate course.'
            }
          </p>
          {!searchTerm && (
            <button
              onClick={() => setActiveTab('files')}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Browse Canvas Files</span>
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-8">
          {courses.map((course) => (
            <div key={course} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FolderOpen className="w-5 h-5 text-blue-600" />
                </div>
                <h2 className="text-lg font-semibold text-gray-900">{course}</h2>
                <span className="text-sm text-gray-500">({filesByCourse[course].length} files)</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filesByCourse[course].map((file, index) => (
                  <div
                    key={`${course}-${index}`}
                    className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        {getFileIcon(file.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                          {file.name}
                        </h3>
                        <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                          <span>{formatFileSize(file.size)}</span>
                          <div className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{file.modified.toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4">
                      <button
                        onClick={() => handleGenerateNotes(file)}
                        className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        <Brain className="w-4 h-4" />
                        <span>Generate AI Notes</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      {filteredFiles.length > 0 && (
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              {filteredFiles.length} file{filteredFiles.length !== 1 ? 's' : ''} available
            </span>
            <span>
              Total size: {formatFileSize(filteredFiles.reduce((sum, file) => sum + file.size, 0))}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AINotesTab;