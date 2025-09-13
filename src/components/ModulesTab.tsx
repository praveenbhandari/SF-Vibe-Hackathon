import React, { useState, useEffect } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import { 
  BookOpen, 
  ChevronDown, 
  ChevronRight, 
  FileText, 
  MessageSquare, 
  HelpCircle, 
  Link, 
  Settings, 
  Download,
  ExternalLink,
  AlertCircle,
  BarChart3
} from 'lucide-react';

interface ModuleItem {
  id: string;
  title: string;
  type: string;
  html_url?: string;
  content_id?: string;
  url?: string;
}

interface Module {
  id: string;
  name: string;
  description?: string;
  items?: ModuleItem[];
  items_count?: number;
  position?: number;
}

export const ModulesTab: React.FC = () => {
  const { selectedCourse } = useCanvasStore();
  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [downloadingFiles, setDownloadingFiles] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (selectedCourse) {
      loadModules();
    }
  }, [selectedCourse]);

  const loadModules = async () => {
    if (!selectedCourse) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const modulesData = await canvasApi.getCourseModules(selectedCourse.id);
      setModules(modulesData);
    } catch (err) {
      console.error('Error loading modules:', err);
      setError(err instanceof Error ? err.message : 'Failed to load modules');
    } finally {
      setLoading(false);
    }
  };

  const toggleModule = (moduleId: string) => {
    const newExpanded = new Set(expandedModules);
    if (newExpanded.has(moduleId)) {
      newExpanded.delete(moduleId);
    } else {
      newExpanded.add(moduleId);
    }
    setExpandedModules(newExpanded);
  };

  const getItemIcon = (type: string) => {
    const iconProps = { className: "h-4 w-4" };
    switch (type) {
      case 'File':
        return <FileText {...iconProps} />;
      case 'Page':
        return <FileText {...iconProps} />;
      case 'Assignment':
        return <FileText {...iconProps} />;
      case 'Discussion':
        return <MessageSquare {...iconProps} />;
      case 'Quiz':
        return <HelpCircle {...iconProps} />;
      case 'ExternalUrl':
        return <Link {...iconProps} />;
      case 'ExternalTool':
        return <Settings {...iconProps} />;
      default:
        return <FileText {...iconProps} />;
    }
  };

  const getItemTypeColor = (type: string) => {
    switch (type) {
      case 'File':
        return 'text-blue-600 bg-blue-50';
      case 'Page':
        return 'text-green-600 bg-green-50';
      case 'Assignment':
        return 'text-purple-600 bg-purple-50';
      case 'Discussion':
        return 'text-orange-600 bg-orange-50';
      case 'Quiz':
        return 'text-red-600 bg-red-50';
      case 'ExternalUrl':
        return 'text-indigo-600 bg-indigo-50';
      case 'ExternalTool':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const handleDownloadFile = async (item: ModuleItem) => {
    if (!item.content_id) return;
    
    const fileId = item.content_id;
    setDownloadingFiles(prev => new Set([...prev, fileId]));
    
    try {
      const blob = await canvasApi.downloadFile(fileId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = item.title || `file_${fileId}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading file:', err);
      // Could add toast notification here
    } finally {
      setDownloadingFiles(prev => {
        const newSet = new Set(prev);
        newSet.delete(fileId);
        return newSet;
      });
    }
  };

  const groupItemsByType = (items: ModuleItem[]) => {
    const grouped: { [key: string]: ModuleItem[] } = {};
    items.forEach(item => {
      const type = item.type || 'Unknown';
      if (!grouped[type]) {
        grouped[type] = [];
      }
      grouped[type].push(item);
    });
    return grouped;
  };

  if (!selectedCourse) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Please select a course to view modules</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BookOpen className="h-6 w-6" />
          Course Modules
        </h2>
        <button
          onClick={loadModules}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Modules List */}
      {!loading && (
        <div className="space-y-4">
          {modules.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No modules found</p>
            </div>
          ) : (
            modules.map((module, index) => {
              const isExpanded = expandedModules.has(module.id);
              const itemsCount = module.items?.length || module.items_count || 0;
              
              return (
                <div key={module.id} className="bg-white rounded-lg shadow-sm border">
                  {/* Module Header */}
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => toggleModule(module.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {isExpanded ? (
                          <ChevronDown className="h-5 w-5 text-gray-400" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-400" />
                        )}
                        <BookOpen className="h-5 w-5 text-blue-600" />
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {index + 1}. {module.name}
                          </h3>
                          {module.description && (
                            <p className="text-sm text-gray-600 mt-1">
                              {module.description.length > 100
                                ? `${module.description.slice(0, 100)}...`
                                : module.description
                              }
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-1 text-sm text-gray-500">
                          <BarChart3 className="h-4 w-4" />
                          <span>{itemsCount} items</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Module Content */}
                  {isExpanded && (
                    <div className="border-t border-gray-200 p-4">
                      {module.description && module.description.length > 100 && (
                        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                          <p className="text-sm text-gray-700">
                            <strong>Description:</strong> {module.description}
                          </p>
                        </div>
                      )}

                      {module.items && module.items.length > 0 ? (
                        <div className="space-y-4">
                          <h4 className="font-medium text-gray-900 flex items-center gap-2">
                            <BarChart3 className="h-4 w-4" />
                            Module Contents
                          </h4>
                          
                          {Object.entries(groupItemsByType(module.items)).map(([type, items]) => (
                            <div key={type} className="space-y-2">
                              <h5 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                {getItemIcon(type)}
                                {type}s ({items.length})
                              </h5>
                              
                              <div className="space-y-2 ml-6">
                                {items.map((item, itemIndex) => (
                                  <div
                                    key={item.id}
                                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                                  >
                                    <div className="flex items-center space-x-3 flex-1">
                                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getItemTypeColor(item.type)}`}>
                                        {getItemIcon(item.type)}
                                        <span className="ml-1">{item.type}</span>
                                      </span>
                                      <span className="text-sm text-gray-600">{itemIndex + 1}.</span>
                                      <span className="text-sm font-medium text-gray-900 flex-1">
                                        {item.title}
                                      </span>
                                    </div>
                                    
                                    <div className="flex items-center space-x-2">
                                      {/* View Link */}
                                      {item.html_url && (
                                        <a
                                          href={item.html_url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="inline-flex items-center px-2 py-1 text-xs text-blue-600 hover:text-blue-800 border border-blue-200 rounded hover:bg-blue-50 transition-colors"
                                        >
                                          <ExternalLink className="h-3 w-3 mr-1" />
                                          View
                                        </a>
                                      )}
                                      
                                      {/* Download Button for Files */}
                                      {item.type === 'File' && item.content_id && (
                                        <button
                                          onClick={() => handleDownloadFile(item)}
                                          disabled={downloadingFiles.has(item.content_id)}
                                          className="inline-flex items-center px-2 py-1 text-xs text-green-600 hover:text-green-800 border border-green-200 rounded hover:bg-green-50 transition-colors disabled:opacity-50"
                                        >
                                          <Download className="h-3 w-3 mr-1" />
                                          {downloadingFiles.has(item.content_id) ? 'Downloading...' : 'Download'}
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8">
                          <BookOpen className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                          <p className="text-gray-500 text-sm">No items in this module</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

export default ModulesTab;