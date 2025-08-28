import { api } from './api';
import { parseUTCDateTime } from '../utils/dateUtils';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  max_documents?: number;
  tags?: string[];
}

export interface ChatResponse {
  message: ChatMessage;
  session_id: string;
  sources?: string[];
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: Date;
  updated_at: Date;
  message_count: number;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessage[];
}

export class ChatService {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/api/v1/chat/message', request);
    
    // UTC時間をDateオブジェクトに変換
    return {
      ...response,
      message: {
        ...response.message,
        timestamp: parseUTCDateTime(response.message.timestamp)
      }
    };
  }

  async getSessions(): Promise<ChatSession[]> {
    const response = await api.get<ChatSessionListResponse>('/api/v1/chat/sessions');
    
    // UTC時間をDateオブジェクトに変換
    return response.sessions.map(session => ({
      ...session,
      created_at: parseUTCDateTime(session.created_at),
      updated_at: parseUTCDateTime(session.updated_at)
    }));
  }

  async getSessionHistory(sessionId: string): Promise<ChatMessage[]> {
    const response = await api.get<ChatHistoryResponse>(`/api/v1/chat/sessions/${sessionId}/history`);
    
    // UTC時間をDateオブジェクトに変換
    return response.messages.map(message => ({
      ...message,
      timestamp: parseUTCDateTime(message.timestamp)
    }));
  }

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/api/v1/chat/sessions/${sessionId}`);
    return response;
  }
}

export const chatService = new ChatService();