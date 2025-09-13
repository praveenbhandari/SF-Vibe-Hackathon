import React, { useEffect, useState } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import { BookOpen, Users, Calendar, ChevronRight, RefreshCw, AlertCircle, LogOut } from 'lucide-react';
import type { Course } from '../store/useCanvasStore';

const CourseSelection: React.FC = () => {
  const {
    courses,
    setCourses,
    setSelectedCourse,
    isLoading,
    setLoading,
    error,
    setError,
    clearError,
    logout,
    currentUser
  } = useCanvasStore();

  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    setLoading(true);
    clearError();
    
    try {
      const fetchedCourses = await canvasApi.getCourses();
      setCourses(fetchedCourses);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load courses';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCourseSelect = (course: Course) => {
    setSelectedCourse(course);
  };

  const handleLogout = () => {
    logout();
  };

  const filteredCourses = courses.filter(course =>
    course.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.course_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'No date';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCourseColor = (course: Course) => {
    if (course.course_color) {
      return course.course_color;
    }
    // Generate a color based on course ID for consistency
    const colors = [
      'bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-red-500',
      'bg-yellow-500', 'bg-indigo-500', 'bg-pink-500', 'bg-teal-500'
    ];
    return colors[course.id % colors.length];
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-100 rounded-full p-2">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Canvas Courses</h1>
                {currentUser && (
                  <p className="text-sm text-gray-600">Welcome back, {currentUser.name}</p>
                )}
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Refresh */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div className="flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search courses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={loadCourses}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Loading State */}
        {isLoading && courses.length === 0 && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading your courses...</p>
            </div>
          </div>
        )}

        {/* Courses Grid */}
        {!isLoading && filteredCourses.length === 0 && courses.length > 0 && (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No courses found matching your search.</p>
          </div>
        )}

        {!isLoading && courses.length === 0 && !error && (
          <div className="text-center py-12">
            <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No courses available.</p>
          </div>
        )}

        {filteredCourses.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course) => (
              <div
                key={course.id}
                onClick={() => handleCourseSelect(course)}
                className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer border border-gray-200 overflow-hidden group"
              >
                {/* Course Header */}
                <div className={`h-24 ${getCourseColor(course)} relative`}>
                  <div className="absolute inset-0 bg-black bg-opacity-20"></div>
                  <div className="absolute bottom-3 left-4 right-4">
                    <h3 className="text-white font-semibold text-lg truncate">
                      {course.course_code}
                    </h3>
                  </div>
                  <ChevronRight className="absolute top-3 right-3 w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                {/* Course Content */}
                <div className="p-4">
                  <h4 className="font-medium text-gray-900 mb-2 line-clamp-2">
                    {course.name}
                  </h4>
                  
                  <div className="space-y-2 text-sm text-gray-600">
                    {course.enrollments && course.enrollments.length > 0 && (
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4" />
                        <span>{course.enrollments[0].type || 'Student'}</span>
                      </div>
                    )}
                    
                    {(course.start_at || course.end_at) && (
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-4 h-4" />
                        <span>
                          {course.start_at ? formatDate(course.start_at) : 'Started'}
                          {course.end_at && ` - ${formatDate(course.end_at)}`}
                        </span>
                      </div>
                    )}
                  </div>

                  {course.public_description && (
                    <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                      {course.public_description}
                    </p>
                  )}
                </div>

                {/* Course Footer */}
                <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      Course ID: {course.id}
                    </span>
                    <div className="flex items-center space-x-1 text-blue-600 group-hover:text-blue-700">
                      <span className="text-sm font-medium">View Course</span>
                      <ChevronRight className="w-4 h-4" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Course Count */}
        {filteredCourses.length > 0 && (
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-600">
              Showing {filteredCourses.length} of {courses.length} courses
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseSelection;