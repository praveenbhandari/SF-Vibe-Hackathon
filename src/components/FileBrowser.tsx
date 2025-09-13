import React, { useEffect, useState } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import {
  FileText, Image, Video, Music, Archive, Download,
  ArrowLeft, Search, Filter, Grid, List, Calendar,
  Eye, RefreshCw, AlertCircle, Folder
} from 'lucide-react';
import type { FileItem } from '../store/useCanvasStore';

type ViewMode = 'grid' | 'list';
type SortBy = 'name' | 'date' | 'size' | 'type';

const FileBrowser: React.FC = () => {
  const {
    selectedCourse,
    files,
    setFiles,
    selectedFile,
    setSelectedFile,
    setSelectedCourse,
    isLoading,
    setLoading,
    error,
    setError,
    clearError
  } = useCanvasStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [sortBy, setSortBy] = useState<SortBy>('date');
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    if (selectedCourse) {
      loadFiles();
    }
  }, [selectedCourse]);

  const loadFiles = async () => {
    if (!selectedCourse) return;
    
    setLoading(true);
    clearError();
    
    try {
      const fetchedFiles = await canvasApi.getCourseFiles(selectedCourse.id);
      setFiles(fetchedFiles);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load files';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (file: FileItem) => {
    setSelectedFile(file);
  };

  const handleDownload = async (file: FileItem, e: React.MouseEvent) => {
    e.stopPropagation();
    
    try {
      const blob = await canvasApi.downloadFile(file.url);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setError('Failed to download file');
    }
  };

  const getFileIcon = (contentType: string, size: number = 24) => {
    const iconProps = { size, className: 'text-gray-600' };
    
    if (contentType.includes('pdf') || contentType.includes('document')) {
      return <FileText {...iconProps} className="text-red-500" />;
    }
    if (contentType.includes('image')) {
      return <Image {...iconProps} className="text-green-500" />;
    }
    if (contentType.includes('video')) {
      return <Video {...iconProps} className="text-purple-500" />;
    }
    if (contentType.includes('audio')) {
      return <Music {...iconProps} className="text-blue-500" />;
    }
    if (contentType.includes('zip') || contentType.includes('archive')) {
      return <Archive {...iconProps} className="text-yellow-500" />;
    }
    return <FileText {...iconProps} />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFileTypeFilter = (contentType: string): string => {
    if (contentType.includes('image')) return 'images';
    if (contentType.includes('video')) return 'videos';
    if (contentType.includes('audio')) return 'audio';
    if (contentType.includes('pdf') || contentType.includes('document')) return 'documents';
    if (contentType.includes('zip') || contentType.includes('archive')) return 'archives';
    return 'other';
  };

  const filteredAndSortedFiles = files
    .filter(file => {
      const matchesSearch = file.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           file.filename.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterType === 'all' || getFileTypeFilter(file.content_type) === filterType;
      return matchesSearch && matchesFilter;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.display_name.localeCompare(b.display_name);
        case 'date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'size':
          return b.size - a.size;
        case 'type':
          return a.content_type.localeCompare(b.content_type);
        default:
          return 0;
      }
    });

  const fileTypeOptions = [
    { value: 'all', label: 'All Files' },
    { value: 'documents', label: 'Documents' },
    { value: 'images', label: 'Images' },
    { value: 'videos', label: 'Videos' },
    { value: 'audio', label: 'Audio' },
    { value: 'archives', label: 'Archives' },
    { value: 'other', label: 'Other' }
  ];

  if (!selectedCourse) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Folder className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Please select a course to view files</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSelectedCourse(null)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Courses</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{selectedCourse.name}</h1>
                <p className="text-sm text-gray-600">{selectedCourse.course_code}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Controls */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters and Controls */}
          <div className="flex items-center space-x-4">
            {/* File Type Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {fileTypeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Sort By */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortBy)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="date">Sort by Date</option>
              <option value="name">Sort by Name</option>
              <option value="size">Sort by Size</option>
              <option value="type">Sort by Type</option>
            </select>

            {/* View Mode */}
            <div className="flex border border-gray-300 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>

            {/* Refresh */}
            <button
              onClick={loadFiles}
              disabled={isLoading}
              className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Loading State */}
        {isLoading && files.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading files...</p>
            </div>
          </div>
        )}

        {/* No Files */}
        {!isLoading && filteredAndSortedFiles.length === 0 && files.length > 0 && (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No files found matching your criteria.</p>
          </div>
        )}

        {!isLoading && files.length === 0 && !error && (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No files available in this course.</p>
          </div>
        )}

        {/* Files Display */}
        {filteredAndSortedFiles.length > 0 && (
          <>
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredAndSortedFiles.map((file) => (
                  <div
                    key={file.id}
                    onClick={() => handleFileSelect(file)}
                    className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer border-2 ${
                      selectedFile?.id === file.id ? 'border-blue-500' : 'border-gray-200'
                    } overflow-hidden group`}
                  >
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-shrink-0">
                          {getFileIcon(file.content_type, 32)}
                        </div>
                        <button
                          onClick={(e) => handleDownload(file, e)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-blue-600 transition-all"
                          title="Download file"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                      
                      <h3 className="font-medium text-gray-900 text-sm mb-2 line-clamp-2">
                        {file.display_name}
                      </h3>
                      
                      <div className="space-y-1 text-xs text-gray-500">
                        <p>{formatFileSize(file.size)}</p>
                        <p>{formatDate(file.created_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Size
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Modified
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredAndSortedFiles.map((file) => (
                        <tr
                          key={file.id}
                          onClick={() => handleFileSelect(file)}
                          className={`cursor-pointer hover:bg-gray-50 ${
                            selectedFile?.id === file.id ? 'bg-blue-50' : ''
                          }`}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 mr-3">
                                {getFileIcon(file.content_type, 20)}
                              </div>
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {file.display_name}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {file.content_type}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatFileSize(file.size)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(file.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={(e) => handleDownload(file, e)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Download"
                              >
                                <Download className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* File Count */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Showing {filteredAndSortedFiles.length} of {files.length} files
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FileBrowser;