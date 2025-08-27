import { apiClient } from './api';

// 論文関連の型定義
export interface Paper {
  id: string;
  title: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaperSummary extends Paper {
  section_count: number;
  total_words: number;
}

export interface PaperSection {
  id: string;
  paper_id: string;
  hierarchy_path: string;
  section_number: string;
  title: string;
  content: string;
  summary: string;
  word_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SectionOutline {
  id: string;
  hierarchy_path: string;
  section_number: string;
  title: string;
  word_count: number;
  status: string;
  summary: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  agent_name?: string;
  todo_tasks: TodoTask[];
  references: any[];
  created_at: string;
}

export interface TodoTask {
  id: string;
  description: string;
  agent_name: string;
  priority: string;
  status: string;
  result?: any;
}

export interface ChatResponse {
  message: string;
  todo_tasks: TodoTask[];
  task_results: Record<string, any>;
  references: any[];
  suggestions: string[];
  success: boolean;
}

// 論文作成・更新用のデータ型
export interface CreatePaperRequest {
  title: string;
  description?: string;
}

export interface UpdatePaperRequest {
  title?: string;
  description?: string;
  status?: string;
}

export interface CreateSectionRequest {
  title: string;
  content?: string;
  parent_id?: string;
  position?: number;
}

export interface UpdateSectionRequest {
  title?: string;
  content?: string;
  status?: string;
}

export interface CreateChatSessionRequest {
  title: string;
}

export interface SendMessageRequest {
  message: string;
  target_section_id?: string;
}

export const paperService = {
  // 論文管理
  async getPapers(page: number = 1, limit: number = 20, status?: string): Promise<{
    items: PaperSummary[];
    total: number;
    page: number;
    limit: number;
    has_more: boolean;
  }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (status) params.append('status', status);
    
    const response = await apiClient.get(`/papers?${params}`);
    return response.data.data;
  },

  async getPaper(paperId: string): Promise<Paper> {
    const response = await apiClient.get(`/papers/${paperId}`);
    return response.data.data;
  },

  async createPaper(data: CreatePaperRequest): Promise<Paper> {
    const response = await apiClient.post('/papers', data);
    return response.data.data;
  },

  async updatePaper(paperId: string, data: UpdatePaperRequest): Promise<Paper> {
    const response = await apiClient.put(`/papers/${paperId}`, data);
    return response.data.data;
  },

  async deletePaper(paperId: string): Promise<void> {
    await apiClient.delete(`/papers/${paperId}`);
  },

  // セクション管理
  async getSections(paperId: string): Promise<SectionOutline[]> {
    const response = await apiClient.get(`/papers/${paperId}/sections`);
    return response.data.data;
  },

  async getSection(paperId: string, sectionId: string): Promise<PaperSection> {
    const response = await apiClient.get(`/papers/${paperId}/sections/${sectionId}`);
    return response.data.data;
  },

  async createSection(paperId: string, data: CreateSectionRequest): Promise<PaperSection> {
    const response = await apiClient.post(`/papers/${paperId}/sections`, data);
    return response.data.data;
  },

  async updateSection(paperId: string, sectionId: string, data: UpdateSectionRequest): Promise<PaperSection> {
    const response = await apiClient.put(`/papers/${paperId}/sections/${sectionId}`, data);
    return response.data.data;
  },

  async deleteSection(paperId: string, sectionId: string): Promise<void> {
    await apiClient.delete(`/papers/${paperId}/sections/${sectionId}`);
  },

  async getSectionHistory(paperId: string, sectionId: string): Promise<any[]> {
    const response = await apiClient.get(`/papers/${paperId}/sections/${sectionId}/history`);
    return response.data.data;
  },

  // チャット・研究ディスカッション
  async getChatSessions(paperId: string): Promise<ChatSession[]> {
    const response = await apiClient.get(`/papers/${paperId}/chat`);
    return response.data.data;
  },

  async createChatSession(paperId: string, data: CreateChatSessionRequest): Promise<ChatSession> {
    const response = await apiClient.post(`/papers/${paperId}/chat`, data);
    return response.data.data;
  },

  async getChatMessages(paperId: string, sessionId: string): Promise<ChatMessage[]> {
    const response = await apiClient.get(`/papers/${paperId}/chat/${sessionId}/messages`);
    return response.data.data;
  },

  async sendMessage(paperId: string, sessionId: string, data: SendMessageRequest): Promise<ChatResponse> {
    const response = await apiClient.post(`/papers/${paperId}/chat/${sessionId}/messages`, data);
    return response.data.data;
  },

  // エージェント実行
  async executeAgent(paperId: string, agentName: string, task: string, parameters: Record<string, any> = {}): Promise<any> {
    const response = await apiClient.post(`/papers/${paperId}/agents/${agentName}/execute`, {
      task,
      parameters,
    });
    return response.data.data;
  },

  // 文献検索
  async searchReferences(query?: string, keywords: string[] = [], tags: string[] = [], limit: number = 10): Promise<any> {
    const response = await apiClient.post('/papers/search/references', {
      query,
      keywords,
      tags,
      limit,
    });
    return response.data.data;
  },
};