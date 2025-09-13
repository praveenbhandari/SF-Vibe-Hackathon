import React, { useState } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { canvasApi } from '../services/canvasApi';
import { aiNotesService } from '../services/aiNotesService';
import {
  Brain, FileText, Download, Loader2, AlertCircle,
  CheckCircle, ArrowLeft, Sparkles, Clock, BookOpen
} from 'lucide-react';

const AINotesGenerator: React.FC = () => {
  const {
    selectedFile,
    selectedCourse,
    setSelectedFile,
    addGeneratedNotes,
    generatedNotes,
    currentNotes,
    setCurrentNotes
  } = useCanvasStore();

  const [isGenerating, setIsGenerating] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState<string>('');
  const [progress, setProgress] = useState<string>('');

  const handleGenerateNotes = async () => {
    if (!selectedFile || !selectedCourse) {
      setError('Please select a file and course');
      return;
    }

    setIsExtracting(true);
    setIsGenerating(false);
    setError(null);
    setProgress('Downloading file...');

    try {
      // Download and extract text from file
      const fileBlob = await canvasApi.downloadFile(selectedFile.url);
      setProgress('Extracting text content...');
      
      const text = await aiNotesService.extractTextFromFile(selectedFile, fileBlob);
      setExtractedText(text);
      setIsExtracting(false);
      
      if (!text.trim()) {
        throw new Error('No text content could be extracted from this file');
      }

      setIsGenerating(true);
      setProgress('Generating AI notes...');

      // Generate notes using AI
      const notes = await aiNotesService.generateNotes([selectedFile]);

      addGeneratedNotes(notes);
      setCurrentNotes(notes);
      setProgress('Notes generated successfully!');
      
      // Clear progress after 2 seconds
      setTimeout(() => setProgress(''), 2000);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate notes';
      setError(errorMessage);
    } finally {
      setIsExtracting(false);
      setIsGenerating(false);
    }
  };

  const handleDownloadNotes = (notes: typeof currentNotes) => {
    if (!notes) return;
    
    const content = `# Study Notes: ${notes.fileName}\n\n` +
                   `**Course:** ${notes.courseName}\n` +
                   `**Generated:** ${new Date(notes.createdAt).toLocaleString()}\n\n` +
                   `---\n\n${notes.content}`;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notes-${notes.fileName.replace(/\.[^/.]+$/, '')}.md`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
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

  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return '📄';
    if (contentType.includes('image')) return '🖼️';
    if (contentType.includes('video')) return '🎥';
    if (contentType.includes('text')) return '📝';
    return '📁';
  };

  if (!selectedFile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">AI Notes Generator</h2>
          <p className="text-gray-600 mb-6">
            Select a file from the file browser to generate AI-powered study notes.
          </p>
          <button
            onClick={() => setSelectedFile(null)}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Go to File Browser
          </button>
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
                onClick={() => setSelectedFile(null)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Files</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div className="flex items-center space-x-3">
                <Brain className="w-6 h-6 text-blue-600" />
                <h1 className="text-xl font-semibold text-gray-900">AI Notes Generator</h1>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* File Info and Controls */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Selected File</h2>
              
              <div className="flex items-start space-x-3 mb-4">
                <div className="text-2xl">
                  {getFileIcon(selectedFile.content_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    {selectedFile.display_name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {selectedFile.content_type}
                  </p>
                  <p className="text-sm text-gray-500">
                    {canvasApi.formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>

              {selectedCourse && (
                <div className="mb-6 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-blue-900">Course</p>
                  <p className="text-sm text-blue-700">{selectedCourse.name}</p>
                  <p className="text-xs text-blue-600">{selectedCourse.course_code}</p>
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={handleGenerateNotes}
                disabled={isExtracting || isGenerating}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                {isExtracting || isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>{isExtracting ? 'Extracting...' : 'Generating...'}</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    <span>Generate AI Notes</span>
                  </>
                )}
              </button>

              {/* Progress */}
              {progress && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-blue-600" />
                    <span className="text-sm text-blue-700">{progress}</span>
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm text-red-700">{error}</span>
                  </div>
                </div>
              )}

              {/* Previous Notes */}
              {generatedNotes.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Previous Notes</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {generatedNotes
                      .filter(note => note.fileName === selectedFile.display_name)
                      .map((note) => (
                        <button
                          key={note.id}
                          onClick={() => setCurrentNotes(note)}
                          className={`w-full text-left p-2 rounded border transition-colors ${
                            currentNotes?.id === note.id
                              ? 'bg-blue-50 border-blue-200'
                              : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                          }`}
                        >
                          <p className="text-xs text-gray-600">
                            {formatDate(note.createdAt)}
                          </p>
                        </button>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Generated Notes Display */}
          <div className="lg:col-span-2">
            {currentNotes ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                {/* Notes Header */}
                <div className="border-b border-gray-200 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
                        <BookOpen className="w-5 h-5 text-blue-600" />
                        <span>Generated Notes</span>
                      </h2>
                      <p className="text-sm text-gray-600 mt-1">
                        Created {formatDate(currentNotes.createdAt)}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDownloadNotes(currentNotes)}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download</span>
                    </button>
                  </div>
                </div>

                {/* Notes Content */}
                <div className="p-6">
                  {currentNotes.summary && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Summary</h3>
                      <p className="text-gray-700 leading-relaxed">{currentNotes.summary}</p>
                    </div>
                  )}

                  {currentNotes.keyPoints && currentNotes.keyPoints.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Key Points</h3>
                      <ul className="space-y-2">
                        {currentNotes.keyPoints.map((point, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {currentNotes.questions && currentNotes.questions.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Study Questions</h3>
                      <ul className="space-y-2">
                        {currentNotes.questions.map((question, index) => (
                          <li key={index} className="flex items-start space-x-2">
                            <span className="text-blue-500 font-semibold mt-0.5 flex-shrink-0">
                              {index + 1}.
                            </span>
                            <span className="text-gray-700">{question}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Full Content */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Full Notes</h3>
                    <div className="prose max-w-none">
                      <pre className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                        {currentNotes.content}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Ready to Generate Notes
                </h3>
                <p className="text-gray-600">
                  Click "Generate AI Notes" to create comprehensive study notes from your selected file.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AINotesGenerator;