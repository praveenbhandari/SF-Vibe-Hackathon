import React, { useState, useEffect } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import PermissionTester from './PermissionTester';
import { Key, Globe, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const CanvasAuth: React.FC = () => {
  const [baseUrl, setBaseUrl] = useState('');
  const [apiToken, setApiToken] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const { 
    setAuth, 
    setLoading, 
    setError, 
    clearError,
    apiToken: storedApiToken,
    baseUrl: storedBaseUrl,
    setActiveTab
  } = useCanvasStore();

  // Load cached credentials on component mount
  useEffect(() => {
    if (storedBaseUrl) {
      setBaseUrl(storedBaseUrl);
    }
    if (storedApiToken) {
      setApiToken(storedApiToken);
    }
  }, [storedBaseUrl, storedApiToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!baseUrl.trim() || !apiToken.trim()) {
      setValidationError('Please fill in both Canvas URL and API token');
      return;
    }

    setIsValidating(true);
    setValidationError(null);
    clearError();
    setLoading(true);

    try {
      // Clean up the base URL
      const cleanBaseUrl = baseUrl.trim().replace(/\/$/, '');
      
      // Validate URL format
      if (!cleanBaseUrl.startsWith('http')) {
        throw new Error('Canvas URL must start with http:// or https://');
      }

      // Set credentials and validate
      canvasApi.setCredentials(cleanBaseUrl, apiToken.trim());
      const user = await canvasApi.validateCredentials();

      // Success - store credentials and navigate to courses
      setAuth(apiToken.trim(), cleanBaseUrl, user);
      setShowSuccess(true);
      
      // Navigate to courses tab after successful authentication
      setTimeout(() => {
        setShowSuccess(false);
        setActiveTab('courses');
      }, 2000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      setValidationError(errorMessage);
      setError(errorMessage);
    } finally {
      setIsValidating(false);
      setLoading(false);
    }
  };

  const handleInputChange = () => {
    if (validationError) {
      setValidationError(null);
      clearError();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="bg-blue-100 rounded-full p-3 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
            <Key className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Connect to Canvas</h1>
          <p className="text-gray-600">Enter your Canvas credentials to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="baseUrl" className="block text-sm font-medium text-gray-700 mb-2">
              Canvas URL
            </label>
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="url"
                id="baseUrl"
                value={baseUrl}
                onChange={(e) => {
                  setBaseUrl(e.target.value);
                  handleInputChange();
                }}
                placeholder="https://your-school.instructure.com"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                disabled={isValidating}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Your Canvas institution URL (e.g., https://canvas.university.edu)
            </p>
          </div>

          <div>
            <label htmlFor="apiToken" className="block text-sm font-medium text-gray-700 mb-2">
              API Token
            </label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="password"
                id="apiToken"
                value={apiToken}
                onChange={(e) => {
                  setApiToken(e.target.value);
                  handleInputChange();
                }}
                placeholder="Enter your Canvas API token"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                disabled={isValidating}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Generate this in Canvas: Account → Settings → Approved Integrations → New Access Token
            </p>
          </div>

          {validationError && (
            <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700">{validationError}</span>
            </div>
          )}

          {showSuccess && (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-sm text-green-700">Successfully connected to Canvas!</span>
              </div>
              
              {/* Permission Tester */}
              <PermissionTester />
            </div>
          )}

          <button
            type="submit"
            disabled={isValidating || !baseUrl.trim() || !apiToken.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            {isValidating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Connecting...</span>
              </>
            ) : (
              <span>Connect to Canvas</span>
            )}
          </button>
        </form>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 mb-2">How to get your API token:</h3>
          <ol className="text-xs text-blue-800 space-y-1">
            <li>1. Log into your Canvas account</li>
            <li>2. Go to Account → Settings</li>
            <li>3. Scroll to "Approved Integrations"</li>
            <li>4. Click "+ New Access Token"</li>
            <li>5. Enter a purpose and generate the token</li>
            <li>6. Copy and paste the token here</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default CanvasAuth;