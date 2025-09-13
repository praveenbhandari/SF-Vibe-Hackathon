import React, { useState, useEffect } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import { Calendar, Clock, Target, CheckCircle, AlertCircle, Filter, Search } from 'lucide-react';

interface Assignment {
  id: string;
  name: string;
  description?: string;
  due_at?: string;
  points_possible?: number;
  has_submitted_submissions?: boolean;
  html_url?: string;
  submission_types?: string[];
  created_at?: string;
}

type SortOption = 'Due Date' | 'Name' | 'Points';

export const AssignmentsTab: React.FC = () => {
  const { selectedCourse } = useCanvasStore();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCompleted, setShowCompleted] = useState(true);
  const [sortBy, setSortBy] = useState<SortOption>('Due Date');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (selectedCourse) {
      loadAssignments();
    }
  }, [selectedCourse]);

  const loadAssignments = async () => {
    if (!selectedCourse) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const assignmentsData = await canvasApi.getCourseAssignments(selectedCourse.id);
      setAssignments(assignmentsData);
    } catch (err) {
      console.error('Error loading assignments:', err);
      setError(err instanceof Error ? err.message : 'Failed to load assignments');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'No due date';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString.slice(0, 10);
    }
  };

  const isOverdue = (dueDate?: string) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  const filteredAndSortedAssignments = React.useMemo(() => {
    let filtered = assignments.filter(assignment => {
      // Filter by completion status
      if (!showCompleted && assignment.has_submitted_submissions) {
        return false;
      }
      
      // Filter by search term
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return assignment.name?.toLowerCase().includes(searchLower) ||
               assignment.description?.toLowerCase().includes(searchLower);
      }
      
      return true;
    });

    // Sort assignments
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'Due Date':
          const dateA = a.due_at || '9999-12-31';
          const dateB = b.due_at || '9999-12-31';
          return dateA.localeCompare(dateB);
        case 'Name':
          return (a.name || '').localeCompare(b.name || '');
        case 'Points':
          return (b.points_possible || 0) - (a.points_possible || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [assignments, showCompleted, sortBy, searchTerm]);

  if (!selectedCourse) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Please select a course to view assignments</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Target className="h-6 w-6" />
          Assignments
        </h2>
        <button
          onClick={loadAssignments}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search assignments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Show Completed Filter */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showCompleted"
              checked={showCompleted}
              onChange={(e) => setShowCompleted(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="showCompleted" className="text-sm font-medium text-gray-700">
              Show completed assignments
            </label>
          </div>

          {/* Sort By */}
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="Due Date">Sort by Due Date</option>
              <option value="Name">Sort by Name</option>
              <option value="Points">Sort by Points</option>
            </select>
          </div>
        </div>
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

      {/* Assignments List */}
      {!loading && (
        <div className="space-y-4">
          {filteredAndSortedAssignments.length === 0 ? (
            <div className="text-center py-12">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">
                {assignments.length === 0 ? 'No assignments found' : 'No assignments match your criteria'}
              </p>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-600">
                Found {filteredAndSortedAssignments.length} assignment{filteredAndSortedAssignments.length !== 1 ? 's' : ''}
              </p>
              
              {filteredAndSortedAssignments.map((assignment, index) => {
                const overdue = isOverdue(assignment.due_at);
                const completed = assignment.has_submitted_submissions;
                
                return (
                  <div
                    key={assignment.id}
                    className={`bg-white rounded-lg shadow-sm border-l-4 p-6 hover:shadow-md transition-shadow ${
                      completed ? 'border-l-green-500 bg-green-50' :
                      overdue ? 'border-l-red-500' : 'border-l-blue-500'
                    }`}
                  >
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      {/* Assignment Info */}
                      <div className="lg:col-span-2">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <span className="text-sm text-gray-500">#{index + 1}</span>
                            {assignment.name}
                            {completed && <CheckCircle className="h-5 w-5 text-green-500" />}
                            {overdue && !completed && <AlertCircle className="h-5 w-5 text-red-500" />}
                          </h3>
                        </div>
                        
                        {assignment.description && (
                          <div className="mb-3">
                            {assignment.description.length > 200 ? (
                              <details className="group">
                                <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                                  {assignment.description.slice(0, 200)}...
                                  <span className="text-blue-600 ml-1">Read more</span>
                                </summary>
                                <div className="mt-2 text-gray-600" dangerouslySetInnerHTML={{ __html: assignment.description }} />
                              </details>
                            ) : (
                              <p className="text-gray-600" dangerouslySetInnerHTML={{ __html: assignment.description }} />
                            )}
                          </div>
                        )}
                        
                        {assignment.html_url && (
                          <a
                            href={assignment.html_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm"
                          >
                            View in Canvas →
                          </a>
                        )}
                      </div>

                      {/* Assignment Details */}
                      <div className="space-y-3">
                        {/* Due Date */}
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-4 w-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-700">Due Date</p>
                            <p className={`text-sm ${
                              overdue && !completed ? 'text-red-600 font-medium' : 'text-gray-600'
                            }`}>
                              {assignment.due_at ? (
                                <>
                                  <Clock className="inline h-3 w-3 mr-1" />
                                  {formatDate(assignment.due_at)}
                                </>
                              ) : (
                                'No due date'
                              )}
                            </p>
                          </div>
                        </div>

                        {/* Points */}
                        <div className="flex items-center space-x-2">
                          <Target className="h-4 w-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-700">Points</p>
                            <p className="text-sm text-gray-600">
                              {assignment.points_possible !== null && assignment.points_possible !== undefined
                                ? `${assignment.points_possible} pts`
                                : 'N/A'
                              }
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default AssignmentsTab;