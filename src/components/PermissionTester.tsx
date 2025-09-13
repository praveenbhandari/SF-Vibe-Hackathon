import React, { useState } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { AlertTriangle, CheckCircle, XCircle, Loader2, Info } from 'lucide-react';

interface PermissionTestResult {
  success: boolean;
  user?: any;
  courses_count?: number;
  files_test?: any;
  permissions?: {
    can_access_profile: boolean;
    can_access_courses: boolean;
    can_access_files: boolean;
  };
  error?: string;
  error_type?: string;
}

const PermissionTester: React.FC = () => {
  const { apiToken, baseUrl, selectedCourse } = useCanvasStore();
  const [isTestingPermissions, setIsTestingPermissions] = useState(false);
  const [testResult, setTestResult] = useState<PermissionTestResult | null>(null);

  const testPermissions = async () => {
    if (!apiToken || !baseUrl) {
      setTestResult({
        success: false,
        error: 'Canvas credentials not found. Please authenticate first.',
        error_type: 'missing_credentials'
      });
      return;
    }

    setIsTestingPermissions(true);
    setTestResult(null);

    try {
      const response = await fetch('http://localhost:3001/api/canvas/test-permissions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          baseUrl,
          apiToken,
          courseId: selectedCourse?.id
        })
      });

      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        error: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error_type: 'network_error'
      });
    } finally {
      setIsTestingPermissions(false);
    }
  };

  const getStatusIcon = (status: boolean | undefined) => {
    if (status === true) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (status === false) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
    return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
  };

  const getRecommendations = (result: PermissionTestResult) => {
    const recommendations: string[] = [];

    if (result.error_type === 'authentication') {
      recommendations.push('Your API token may have expired. Try generating a new token.');
      recommendations.push('Verify that your Canvas URL is correct.');
    } else if (result.error_type === 'permission_denied') {
      recommendations.push('Your API token lacks the required permissions.');
      recommendations.push('Contact your Canvas administrator to enable "Files" permission scope.');
      recommendations.push('Ensure you have access to the selected course.');
    } else if (result.permissions) {
      if (!result.permissions.can_access_files) {
        recommendations.push('File access is restricted. Check your token permissions.');
        recommendations.push('Verify you have access to files in the selected course.');
      }
    }

    if (recommendations.length === 0) {
      recommendations.push('Try refreshing your browser and re-authenticating.');
      recommendations.push('Contact your Canvas administrator if the issue persists.');
    }

    return recommendations;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Canvas API Permission Test</h3>
        <button
          onClick={testPermissions}
          disabled={isTestingPermissions || !apiToken || !baseUrl}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isTestingPermissions ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Testing...</span>
            </>
          ) : (
            <span>Test Permissions</span>
          )}
        </button>
      </div>

      {!apiToken || !baseUrl ? (
        <div className="flex items-center space-x-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <Info className="w-5 h-5 text-yellow-600" />
          <span className="text-sm text-yellow-800">
            Please authenticate with Canvas first to test permissions.
          </span>
        </div>
      ) : null}

      {testResult && (
        <div className="mt-4 space-y-4">
          {testResult.success ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm text-green-800">
                  Permission test completed successfully!
                </span>
              </div>

              {testResult.user && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">User Information</h4>
                  <p className="text-sm text-gray-600">
                    Logged in as: <strong>{testResult.user.name}</strong> ({testResult.user.login_id})
                  </p>
                </div>
              )}

              <div className="p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">Permission Status</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Profile Access</span>
                    {getStatusIcon(testResult.permissions?.can_access_profile)}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Course Access</span>
                    {getStatusIcon(testResult.permissions?.can_access_courses)}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">File Access</span>
                    {getStatusIcon(testResult.permissions?.can_access_files)}
                  </div>
                </div>
                {typeof testResult.courses_count === 'number' && (
                  <p className="text-sm text-gray-600 mt-2">
                    Found {testResult.courses_count} accessible courses
                  </p>
                )}
              </div>

              {testResult.files_test && typeof testResult.files_test === 'object' && testResult.files_test.error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-medium text-red-900 mb-2">File Access Issue</h4>
                  <p className="text-sm text-red-700">{testResult.files_test.error}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <XCircle className="w-5 h-5 text-red-500" />
                <span className="text-sm text-red-800">
                  Permission test failed: {testResult.error}
                </span>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Recommendations</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  {getRecommendations(testResult).map((recommendation, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PermissionTester;