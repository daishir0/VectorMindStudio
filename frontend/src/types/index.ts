// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: any;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// User Types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  roles: UserRole[];
  created_at: string;
  updated_at: string;
  last_login?: string;
  requires_password_change: boolean; // パスワード変更が必要かどうか
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  VIEWER = 'viewer'
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  full_name?: string;
  is_active?: boolean;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

// Template Types
export interface Template {
  id: string;
  name: string;
  description?: string;
  content: string;
  variables: TemplateVariable[];
  requirements: string;
  status: TemplateStatus;
  user_id: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateVariable {
  name: string;
  type: VariableType;
  description?: string;
  required: boolean;
  default_value?: string;
  options?: string[];
}

export enum VariableType {
  STRING = 'string',
  TEXT = 'text',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  DATE = 'date',
  LIST = 'list'
}

export enum TemplateStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived'
}

export interface TemplateCreate {
  name: string;
  description?: string;
  content: string;
  variables?: TemplateVariable[];
  requirements?: string;
  status?: TemplateStatus;
}

export interface TemplateUpdate {
  name?: string;
  description?: string;
  content?: string;
  variables?: TemplateVariable[];
  requirements?: string;
  status?: TemplateStatus;
}

export interface TemplateUse {
  variables: Record<string, any>;
}

export interface TemplateSearch {
  query: string;
  limit?: number;
  filters?: Record<string, any>;
}

// AI Output Types
export interface AIOutput {
  id: string;
  template_id: string;
  user_id: string;
  input_variables: Record<string, any>;
  generated_content: string;
  metadata: Record<string, any>;
  status: OutputStatus;
  created_at: string;
  updated_at: string;
}

export interface OutputDetailResponse {
  id: string;
  template_id: string;
  user_id: string;
  name: string;
  input_variables: Record<string, any>;
  generated_content: string;
  ai_model: string;
  generation_time: number;
  created_at: string;
}

export enum OutputStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// Auth Types
export interface AuthToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// UI Types
export interface FormError {
  field: string;
  message: string;
}

export interface NotificationOptions {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface TableColumn<T = any> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
  width?: string;
}

export interface TableProps<T = any> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    onPageChange: (page: number) => void;
    onLimitChange: (limit: number) => void;
  };
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onSort?: (column: string) => void;
}

// Search & Filter Types
export interface SearchFilters {
  query?: string;
  status?: TemplateStatus;
  dateRange?: {
    from: string;
    to: string;
  };
  author?: string;
}

export interface SortOptions {
  field: string;
  order: 'asc' | 'desc';
}

// Dashboard Types
export interface DashboardStats {
  total_templates: number;
  active_templates: number;
  total_outputs: number;
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'template_created' | 'template_used' | 'output_generated';
  description: string;
  timestamp: string;
  user_id: string;
  user_name: string;
}

// API Key Types
export interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  permissions: ApiPermission[];
  is_active: boolean;
  last_used?: string;
  expires_at?: string;
  created_at: string;
}

export enum ApiPermission {
  READ_TEMPLATES = 'read_templates',
  WRITE_TEMPLATES = 'write_templates',
  USE_TEMPLATES = 'use_templates',
  READ_OUTPUTS = 'read_outputs'
}

// Hook Types
export interface UseApiOptions {
  enabled?: boolean;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  retry?: number;
  staleTime?: number;
}

export interface UseMutationOptions<TData = unknown, TError = unknown, TVariables = void> {
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: TError, variables: TVariables) => void;
  onMutate?: (variables: TVariables) => Promise<any> | any;
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: () => void;
}

// File Types
export interface FileListResponse {
  id: string;
  filename: string;
  status: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface FileUploadResponse {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: string;
  created_at: string;
}

// Search Types
export interface SearchQuery {
  query: string;
  limit?: number;
  tags?: string[];
}

export interface SearchResult {
  id: string;
  document: string;
  metadata: Record<string, any>;
  distance: number;
  relevance_score: number;
  tags?: string[];
  filename?: string;
  upload_id?: string;
}

// Agent Management Types
export enum AgentCategory {
  WRITING = 'writing',
  QUALITY = 'quality',
  ANALYSIS = 'analysis',
  SEARCH = 'search',
  CUSTOM = 'custom'
}

export enum ExecutorType {
  CODE_BASED = 'code_based',
  LLM_BASED = 'llm_based'
}

export enum ResponseFormat {
  TEXT = 'text',
  JSON = 'json',
  MARKDOWN = 'markdown'
}

export enum WakeWordMatchType {
  EXACT = 'exact',
  SEMANTIC = 'semantic',
  REGEX = 'regex'
}

export enum PaperType {
  MEDICAL = 'medical',
  ENGINEERING = 'engineering',
  HUMANITIES = 'humanities',
  GENERAL = 'general'
}

export enum ExecutionStatus {
  SUCCESS = 'success',
  FAILURE = 'failure',
  TIMEOUT = 'timeout',
  ERROR = 'error'
}

export interface WakeWord {
  id: string;
  agent_id: string;
  keyword: string;
  match_type: WakeWordMatchType;
  priority: number;
  is_active: boolean;
  semantic_weight?: number;
  min_similarity_score?: number;
  usage_count: number;
  last_triggered_at?: string;
  created_at: string;
  updated_at: string;
}

export interface WakeWordCreate {
  keyword: string;
  match_type: WakeWordMatchType;
  priority?: number;
  is_active?: boolean;
  semantic_weight?: number;
  min_similarity_score?: number;
}

export interface Capability {
  id: string;
  agent_id: string;
  task_type: string;
  description: string;
  best_for?: string[];
  supported_task_types: string[];
  task_examples?: string[];
  average_execution_time?: number;
  success_rate?: number;
  created_at: string;
  updated_at: string;
}

export interface CapabilityCreate {
  task_type: string;
  description?: string;
  best_for?: string[];
  task_examples?: string[];
}

export interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: AgentCategory;
  is_active: boolean;
  is_system: boolean;
  is_deletable: boolean;
  priority: number;
  executor_type: ExecutorType;
  class_path?: string;
  llm_model?: string;
  max_retries: number;
  timeout_seconds: number;
  system_prompt: string;
  user_prompt_template: string;
  response_format?: ResponseFormat;
  tags?: string[];
  agent_metadata?: Record<string, any>;
  created_by?: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  wake_words?: WakeWord[];
  capabilities?: Capability[];
}

export interface AgentListItem {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: AgentCategory;
  is_active: boolean;
  is_system: boolean;
  executor_type: ExecutorType;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  display_name: string;
  description: string;
  category: AgentCategory;
  priority?: number;
  executor_type: ExecutorType;
  class_path?: string;
  llm_model?: string;
  max_retries?: number;
  timeout_seconds?: number;
  system_prompt: string;
  user_prompt_template: string;
  response_format?: ResponseFormat;
  tags?: string[];
  agent_metadata?: Record<string, any>;
  wake_words?: WakeWordCreate[];
  capabilities?: CapabilityCreate[];
}

export interface AgentUpdate {
  display_name?: string;
  description?: string;
  category?: AgentCategory;
  is_active?: boolean;
  priority?: number;
  executor_type?: ExecutorType;
  llm_model?: string;
  max_retries?: number;
  timeout_seconds?: number;
  system_prompt?: string;
  user_prompt_template?: string;
  response_format?: ResponseFormat;
  tags?: string[];
  agent_metadata?: Record<string, any>;
  wake_words?: WakeWordCreate[];
  capabilities?: CapabilityCreate[];
}

export interface AgentStatistics {
  total_agents: number;
  active_agents: number;
  system_agents: number;
  custom_agents: number;
  agents_by_category: Record<string, number>;
  agents_by_executor_type: Record<string, number>;
}

export interface AgentExecutionStats {
  agent_id: string;
  agent_name: string;
  total_executions: number;
  success_count: number;
  failure_count: number;
  avg_execution_time_ms: number;
  last_executed_at?: string;
}

// Agent Profile Types
export interface AgentProfile {
  id: string;
  name: string;
  description?: string;
  paper_type: PaperType;
  is_default: boolean;
  user_id?: string;
  created_at: string;
  updated_at: string;
  settings: AgentProfileSetting[];
}

export interface AgentProfileSetting {
  id: string;
  profile_id: string;
  agent_id: string;
  is_enabled: boolean;
  priority_override?: number;
  wake_words_override?: string[];
  created_at: string;
  updated_at: string;
}

export interface AgentProfileCreate {
  name: string;
  description?: string;
  paper_type: PaperType;
  is_default?: boolean;
  settings?: AgentProfileSettingCreate[];
}

export interface AgentProfileUpdate {
  name?: string;
  description?: string;
  paper_type?: PaperType;
  is_default?: boolean;
  settings?: AgentProfileSettingCreate[];
}

export interface AgentProfileSettingCreate {
  agent_id: string;
  is_enabled: boolean;
  priority_override?: number;
  wake_words_override?: string[];
}