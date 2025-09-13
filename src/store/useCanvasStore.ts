import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Course {
  id: number;
  name: string;
  course_code: string;
  workflow_state: string;
  account_id: number;
  start_at?: string;
  end_at?: string;
  enrollment_term_id?: number;
  default_view?: string;
  syllabus_body?: string;
  public_syllabus?: boolean;
  public_syllabus_to_auth?: boolean;
  storage_quota_mb?: number;
  is_public?: boolean;
  is_public_to_auth_users?: boolean;
  public_description?: string;
  calendar?: {
    ics: string;
  };
  time_zone?: string;
  blueprint?: boolean;
  template?: boolean;
  enrollments?: any[];
  hide_final_grades?: boolean;
  apply_assignment_group_weights?: boolean;
  locale?: string;
  created_at?: string;
  course_color?: string;
  friendly_name?: string;
  access_restricted_by_date?: boolean;
  uuid?: string;
}

export interface FileItem {
  id: number;
  uuid: string;
  folder_id: number;
  display_name: string;
  filename: string;
  content_type: string;
  url: string;
  size: number;
  created_at: string;
  updated_at: string;
  unlock_at?: string;
  locked: boolean;
  hidden: boolean;
  lock_at?: string;
  hidden_for_user: boolean;
  thumbnail_url?: string;
  modified_at: string;
  mime_class: string;
  media_entry_id?: string;
  locked_for_user: boolean;
  lock_info?: any;
  lock_explanation?: string;
  preview_url?: string;
}

export interface Assignment {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  due_at?: string;
  lock_at?: string;
  unlock_at?: string;
  has_overrides: boolean;
  all_dates?: any[];
  course_id: number;
  html_url: string;
  submissions_download_url?: string;
  assignment_group_id: number;
  due_date_required: boolean;
  allowed_extensions?: string[];
  max_name_length: number;
  turnitin_enabled: boolean;
  vericite_enabled: boolean;
  turnitin_settings?: any;
  grade_group_students_individually: boolean;
  external_tool_tag_attributes?: any;
  peer_reviews: boolean;
  automatic_peer_reviews: boolean;
  peer_review_count: number;
  peer_reviews_assign_at?: string;
  intra_group_peer_reviews: boolean;
  group_category_id?: number;
  needs_grading_count: number;
  needs_grading_count_by_section?: any[];
  position: number;
  post_to_sis: boolean;
  integration_id?: string;
  integration_data?: any;
  points_possible?: number;
  submission_types: string[];
  has_submitted_submissions: boolean;
  grading_type: string;
  grading_standard_id?: number;
  published: boolean;
  unpublishable: boolean;
  only_visible_to_overrides: boolean;
  locked_for_user: boolean;
  lock_info?: any;
  lock_explanation?: string;
  quiz_id?: number;
  anonymous_submissions: boolean;
  discussion_topic?: any;
  freeze_on_copy: boolean;
  frozen: boolean;
  frozen_attributes?: string[];
  submission?: any;
  use_rubric_for_grading: boolean;
  rubric_settings?: any;
  rubric?: any[];
  assignment_visibility?: number[];
  overrides?: any[];
  omit_from_final_grade: boolean;
  moderated_grading: boolean;
  grader_count?: number;
  final_grader_id?: number;
  grader_comments_visible_to_graders: boolean;
  graders_anonymous_to_graders: boolean;
  grader_names_visible_to_final_grader: boolean;
  anonymous_grading: boolean;
  allowed_attempts: number;
  post_manually: boolean;
  score_statistics?: any;
  can_submit: boolean;
}

export interface ModuleItem {
  id: number;
  module_id: number;
  position: number;
  title: string;
  indent: number;
  type: string;
  content_id?: number;
  html_url?: string;
  url?: string;
  page_url?: string;
  external_url?: string;
  new_tab?: boolean;
  completion_requirement?: {
    type: string;
    min_score?: number;
    completed?: boolean;
  };
  content_details?: {
    points_possible?: number;
    due_at?: string;
    unlock_at?: string;
    lock_at?: string;
  };
  published?: boolean;
}

export interface Module {
  id: number;
  workflow_state: string;
  position: number;
  name: string;
  unlock_at?: string;
  require_sequential_progress: boolean;
  prerequisite_module_ids: number[];
  items_count: number;
  items_url: string;
  items?: ModuleItem[];
  state?: string;
  completed_at?: string;
  publish_final_grade?: boolean;
  published?: boolean;
}

export interface GeneratedNotes {
  id: string;
  fileName: string;
  courseId: number;
  courseName: string;
  content: string;
  summary?: string;
  keyPoints?: string[];
  questions?: string[];
  createdAt: string;
  extractedText?: string;
}

export type TabType = 'courses' | 'files' | 'assignments' | 'modules' | 'ai-notes' | 'notes' | 'qa';

interface CanvasState {
  // Authentication
  isAuthenticated: boolean;
  apiToken: string;
  baseUrl: string;
  currentUser: any;
  
  // Courses
  courses: Course[];
  selectedCourse: Course | null;
  
  // Files
  files: FileItem[];
  selectedFile: FileItem | null;
  
  // Assignments
  assignments: Assignment[];
  
  // Modules
  modules: Module[];
  
  // AI Notes
  generatedNotes: GeneratedNotes[];
  currentNotes: GeneratedNotes | null;
  downloadedFiles: FileItem[];
  
  // UI State
  activeTab: TabType;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setAuth: (token: string, baseUrl: string, user?: any) => void;
  logout: () => void;
  setCourses: (courses: Course[]) => void;
  setSelectedCourse: (course: Course | null) => void;
  setFiles: (files: FileItem[]) => void;
  setSelectedFile: (file: FileItem | null) => void;
  setAssignments: (assignments: Assignment[]) => void;
  setModules: (modules: Module[]) => void;
  addGeneratedNotes: (notes: GeneratedNotes) => void;
  setCurrentNotes: (notes: GeneratedNotes | null) => void;
  setDownloadedFiles: (files: FileItem[]) => void;
  addDownloadedFile: (file: FileItem) => void;
  setActiveTab: (tab: TabType) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useCanvasStore = create<CanvasState>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      apiToken: '',
      baseUrl: '',
      currentUser: null,
      courses: [],
      selectedCourse: null,
      files: [],
      selectedFile: null,
      assignments: [],
      modules: [],
      generatedNotes: [],
      currentNotes: null,
      downloadedFiles: [],
      activeTab: 'courses' as TabType,
      isLoading: false,
      error: null,
      
      // Actions
      setAuth: (token: string, baseUrl: string, user?: any) => {
        set({
          isAuthenticated: true,
          apiToken: token,
          baseUrl: baseUrl,
          currentUser: user,
          error: null
        });
      },
      
      logout: () => {
        set({
          isAuthenticated: false,
          apiToken: '',
          baseUrl: '',
          currentUser: null,
          courses: [],
          selectedCourse: null,
          files: [],
          selectedFile: null,
          assignments: [],
          generatedNotes: [],
          currentNotes: null,
          downloadedFiles: [],
          activeTab: 'courses' as TabType,
          error: null
        });
      },
      
      setCourses: (courses: Course[]) => {
        set({ courses, error: null });
      },
      
      setSelectedCourse: (course: Course | null) => {
        set({ 
          selectedCourse: course,
          files: [],
          selectedFile: null,
          assignments: [],
          modules: []
        });
      },
      
      setFiles: (files: FileItem[]) => {
        set({ files, error: null });
      },
      
      setSelectedFile: (file: FileItem | null) => {
        set({ selectedFile: file });
      },
      
      setAssignments: (assignments: Assignment[]) => {
        set({ assignments, error: null });
      },
      
      setModules: (modules: Module[]) => {
        set({ modules, error: null });
      },
      
      addGeneratedNotes: (notes: GeneratedNotes) => {
        const { generatedNotes } = get();
        set({ 
          generatedNotes: [...generatedNotes, notes],
          currentNotes: notes,
          error: null
        });
      },
      
      setCurrentNotes: (notes: GeneratedNotes | null) => {
        set({ currentNotes: notes });
      },
      
      setDownloadedFiles: (files: FileItem[]) => {
        set({ downloadedFiles: files });
      },
      
      addDownloadedFile: (file: FileItem) => {
        const { downloadedFiles } = get();
        const exists = downloadedFiles.find(f => f.id === file.id);
        if (!exists) {
          set({ downloadedFiles: [...downloadedFiles, file] });
        }
      },
      
      setActiveTab: (tab: TabType) => {
        set({ activeTab: tab });
      },
      
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
      
      setError: (error: string | null) => {
        set({ error, isLoading: false });
      },
      
      clearError: () => {
        set({ error: null });
      }
    }),
    {
      name: 'canvas-storage',
      partialize: (state) => ({
        apiToken: state.apiToken,
        baseUrl: state.baseUrl,
        isAuthenticated: state.isAuthenticated,
        currentUser: state.currentUser,
        generatedNotes: state.generatedNotes,
        downloadedFiles: state.downloadedFiles,
        activeTab: state.activeTab
      })
    }
  )
);