import React, { useEffect } from 'react';
import { useCanvasStore, TabType } from './store/useCanvasStore';
import CanvasAuth from './components/CanvasAuth';
import CourseSelection from './components/CourseSelection';
import FileBrowser from './components/FileBrowser';
import AINotesGenerator from './components/AINotesGenerator';
import QAInterface from './components/QAInterface';
import AINotesTab from './components/AINotesTab';
import {
  GraduationCap, FileText, Brain, MessageCircle,
  LogOut, Settings, User, Download
} from 'lucide-react';

function App() {
  const {
    isAuthenticated,
    selectedCourse,
    selectedFile,
    currentNotes,
    activeTab,
    apiToken,
    baseUrl,
    currentUser,
    logout,
    setSelectedCourse,
    setSelectedFile,
    setCurrentNotes,
    setActiveTab,
    setAuth
  } = useCanvasStore();

  // Auto-login if token exists in cache
  useEffect(() => {
    if (apiToken && baseUrl && !isAuthenticated) {
      setAuth(apiToken, baseUrl, currentUser);
    }
  }, [apiToken, baseUrl, isAuthenticated, currentUser, setAuth]);

  // Determine current view based on active tab and authentication
  const getCurrentView = () => {
    if (!isAuthenticated) return 'auth';
    return activeTab;
  };

  const currentView = getCurrentView();

  const handleLogout = () => {
    logout();
    // Clear localStorage token cache
    localStorage.removeItem('canvas-storage');
  };

  const navigationItems = [
    {
      id: 'courses' as TabType,
      label: 'Courses',
      icon: GraduationCap,
      active: activeTab === 'courses',
      onClick: () => setActiveTab('courses'),
      disabled: !isAuthenticated
    },
    {
      id: 'files' as TabType,
      label: 'Canvas Files',
      icon: FileText,
      active: activeTab === 'files',
      onClick: () => setActiveTab('files'),
      disabled: !selectedCourse
    },
    {
      id: 'ai-notes' as TabType,
      label: 'AI Notes',
      icon: Download,
      active: activeTab === 'ai-notes',
      onClick: () => setActiveTab('ai-notes'),
      disabled: !isAuthenticated
    },
    {
      id: 'notes' as TabType,
      label: 'Generate Notes',
      icon: Brain,
      active: activeTab === 'notes',
      onClick: () => setActiveTab('notes'),
      disabled: !selectedFile
    },
    {
      id: 'qa' as TabType,
      label: 'Q&A',
      icon: MessageCircle,
      active: activeTab === 'qa',
      onClick: () => setActiveTab('qa'),
      disabled: !currentNotes
    }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'auth':
        return <CanvasAuth />;
      case 'courses':
        return <CourseSelection />;
      case 'files':
        return <FileBrowser />;
      case 'ai-notes':
        return <AINotesTab />;
      case 'notes':
        return <AINotesGenerator />;
      case 'qa':
        return <QAInterface />;
      default:
        return <CanvasAuth />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      {isAuthenticated && (
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo and Title */}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <GraduationCap className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Canvas AI Study Assistant</h1>
                  <p className="text-sm text-gray-600">Intelligent note generation and Q&A</p>
                </div>
              </div>

              {/* Navigation Items */}
              <div className="flex items-center space-x-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={item.onClick}
                      disabled={item.disabled}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                        item.active
                          ? 'bg-blue-100 text-blue-700'
                          : item.disabled
                          ? 'text-gray-400 cursor-not-allowed'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="text-sm font-medium">{item.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <User className="w-4 h-4" />
                  <span>Canvas User</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </nav>
      )}

      {/* Breadcrumb */}
      {isAuthenticated && (selectedCourse || selectedFile || currentNotes) && (
        <div className="bg-gray-50 border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <nav className="flex items-center space-x-2 text-sm">
              <button
                onClick={() => {
                  setSelectedCourse(null);
                  setSelectedFile(null);
                  setCurrentNotes(null);
                }}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Courses
              </button>
              
              {selectedCourse && (
                <>
                  <span className="text-gray-400">/</span>
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setCurrentNotes(null);
                    }}
                    className={`font-medium ${
                      selectedFile || currentNotes
                        ? 'text-blue-600 hover:text-blue-700'
                        : 'text-gray-900'
                    }`}
                  >
                    {selectedCourse.name}
                  </button>
                </>
              )}
              
              {selectedFile && (
                <>
                  <span className="text-gray-400">/</span>
                  <button
                    onClick={() => setCurrentNotes(null)}
                    className={`font-medium ${
                      currentNotes
                        ? 'text-blue-600 hover:text-blue-700'
                        : 'text-gray-900'
                    }`}
                  >
                    {selectedFile.display_name}
                  </button>
                </>
              )}
              
              {currentNotes && (
                <>
                  <span className="text-gray-400">/</span>
                  <span className="text-gray-900 font-medium">Q&A Session</span>
                </>
              )}
            </nav>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1">
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-600">
            <p>
              Canvas AI Study Assistant - Powered by AI for enhanced learning
            </p>
            <p className="mt-1">
              Built with React, TypeScript, and TailwindCSS
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
