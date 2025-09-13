import React, { useState, useRef, useEffect } from 'react';
import { useCanvasStore } from '../store/useCanvasStore';
import { aiNotesService } from '../services/aiNotesService';
import {
  MessageCircle, Send, Loader2, Brain, ArrowLeft,
  User, Bot, Copy, CheckCircle, AlertCircle
} from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const QAInterface: React.FC = () => {
  const { currentNotes, setCurrentNotes } = useCanvasStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (currentNotes && messages.length === 0) {
      // Add welcome message when notes are loaded
      const welcomeMessage: Message = {
        id: `welcome-${Date.now()}`,
        type: 'assistant',
        content: `Hi! I'm ready to answer questions about "${currentNotes.fileName}". You can ask me about:

• Key concepts and topics covered
• Explanations of specific points
• Connections between different ideas
• Study tips and exam preparation
• Clarification of complex topics

What would you like to know?`,
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
  }, [currentNotes, messages.length]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !currentNotes || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const answer = await aiNotesService.answerQuestion(
        userMessage.content,
        currentNotes.content,
        currentNotes.fileName
      );

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: answer,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get answer';
      setError(errorMessage);
      
      const errorResponse: Message = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: `I apologize, but I encountered an error while processing your question: ${errorMessage}. Please try rephrasing your question or try again.`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const copyToClipboard = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const suggestedQuestions = [
    "What are the main topics covered in this document?",
    "Can you explain the key concepts in simple terms?",
    "What are the most important points to remember?",
    "How can I best study this material for an exam?",
    "Are there any connections between different sections?"
  ];

  if (!currentNotes) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Q&A Interface</h2>
          <p className="text-gray-600 mb-6">
            Generate AI notes first to start asking questions about your study material.
          </p>
          <button
            onClick={() => setCurrentNotes(null)}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Go to Notes Generator
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentNotes(null)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Notes</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div className="flex items-center space-x-3">
                <MessageCircle className="w-6 h-6 text-blue-600" />
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">Q&A Assistant</h1>
                  <p className="text-sm text-gray-600">{currentNotes.fileName}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start space-x-3 ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.type === 'assistant' && (
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Bot className="w-4 h-4 text-blue-600" />
                      </div>
                    </div>
                  )}
                  
                  <div
                    className={`max-w-3xl rounded-lg px-4 py-3 ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-200 text-gray-900'
                    }`}
                  >
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {message.content}
                    </div>
                    
                    <div className="flex items-center justify-between mt-2">
                      <span
                        className={`text-xs ${
                          message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                        }`}
                      >
                        {formatTimestamp(message.timestamp)}
                      </span>
                      
                      {message.type === 'assistant' && (
                        <button
                          onClick={() => copyToClipboard(message.content, message.id)}
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                          title="Copy to clipboard"
                        >
                          {copiedMessageId === message.id ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {message.type === 'user' && (
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-gray-600" />
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              {isLoading && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <Bot className="w-4 h-4 text-blue-600" />
                    </div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                      <span className="text-gray-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Suggested Questions (only show when no messages except welcome) */}
          {messages.length <= 1 && (
            <div className="px-4 pb-4">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Suggested Questions:</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {suggestedQuestions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => setInputValue(question)}
                      className="text-left p-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded border border-gray-200 transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Input Form */}
          <div className="flex-shrink-0 border-t border-gray-200 bg-white">
            <div className="px-4 py-4">
              {error && (
                <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm text-red-700">{error}</span>
                  </div>
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="flex space-x-3">
                <div className="flex-1">
                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask a question about your notes..."
                    rows={1}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    style={{ minHeight: '48px', maxHeight: '120px' }}
                    disabled={isLoading}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading}
                  className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </form>
              
              <p className="text-xs text-gray-500 mt-2">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QAInterface;