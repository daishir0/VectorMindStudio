/**
 * エージェント管理サービス
 *
 * AIエージェントのCRUD操作、統計情報取得を提供
 */
import { api } from './api';
import {
  Agent,
  AgentListItem,
  AgentCreate,
  AgentUpdate,
  AgentStatistics,
  AgentExecutionStats,
  AgentCategory,
  ExecutorType,
} from '../types';

const BASE_URL = '/api/v1/agents';

export interface AgentListParams {
  category?: AgentCategory;
  is_active?: boolean;
  is_system?: boolean;
  executor_type?: ExecutorType;
  search_query?: string;
  page?: number;
  limit?: number;
  order_by?: string;
  order_desc?: boolean;
}

export interface AgentListResponse {
  agents: AgentListItem[];
  total: number;
  page: number;
  limit: number;
}

export const agentService = {
  /**
   * エージェント一覧を取得
   */
  async list(params?: AgentListParams): Promise<AgentListResponse> {
    const queryParams = new URLSearchParams();

    if (params) {
      if (params.category) queryParams.append('category', params.category);
      if (params.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
      if (params.is_system !== undefined) queryParams.append('is_system', String(params.is_system));
      if (params.executor_type) queryParams.append('executor_type', params.executor_type);
      if (params.search_query) queryParams.append('search_query', params.search_query);
      if (params.page) queryParams.append('page', String(params.page));
      if (params.limit) queryParams.append('limit', String(params.limit));
      if (params.order_by) queryParams.append('order_by', params.order_by);
      if (params.order_desc !== undefined) queryParams.append('order_desc', String(params.order_desc));
    }

    const url = queryParams.toString() ? `${BASE_URL}?${queryParams.toString()}` : BASE_URL;
    return api.get<AgentListResponse>(url);
  },

  /**
   * エージェント詳細を取得
   */
  async get(agentId: string): Promise<Agent> {
    return api.get<Agent>(`${BASE_URL}/${agentId}`);
  },

  /**
   * 新しいエージェントを作成
   */
  async create(data: AgentCreate): Promise<Agent> {
    return api.post<Agent>(BASE_URL, data);
  },

  /**
   * エージェントを更新
   */
  async update(agentId: string, data: AgentUpdate): Promise<Agent> {
    return api.put<Agent>(`${BASE_URL}/${agentId}`, data);
  },

  /**
   * エージェントを削除
   */
  async delete(agentId: string): Promise<{ deleted: boolean; agent_id: string }> {
    return api.delete<{ deleted: boolean; agent_id: string }>(`${BASE_URL}/${agentId}`);
  },

  /**
   * エージェントの有効/無効を切り替え
   */
  async toggleActive(agentId: string, isActive: boolean): Promise<Agent> {
    return api.patch<Agent>(`${BASE_URL}/${agentId}`, { is_active: isActive });
  },

  /**
   * エージェント統計情報を取得
   */
  async getStatistics(): Promise<AgentStatistics> {
    return api.get<AgentStatistics>(`${BASE_URL}/statistics/overview`);
  },

  /**
   * エージェント実行統計を取得
   */
  async getExecutionStats(agentId: string): Promise<AgentExecutionStats> {
    return api.get<AgentExecutionStats>(`${BASE_URL}/${agentId}/execution-stats`);
  },

  /**
   * アクティブなエージェント一覧を取得
   */
  async listActive(): Promise<AgentListItem[]> {
    const response = await api.get<AgentListResponse>(`${BASE_URL}?is_active=true`);
    return response.agents;
  },

  /**
   * システムエージェント一覧を取得
   */
  async listSystem(): Promise<AgentListItem[]> {
    const response = await api.get<AgentListResponse>(`${BASE_URL}?is_system=true`);
    return response.agents;
  },

  /**
   * カスタムエージェント一覧を取得
   */
  async listCustom(): Promise<AgentListItem[]> {
    const response = await api.get<AgentListResponse>(`${BASE_URL}?is_system=false`);
    return response.agents;
  },

  /**
   * カテゴリ別エージェント一覧を取得
   */
  async listByCategory(category: AgentCategory): Promise<AgentListItem[]> {
    const response = await api.get<AgentListResponse>(`${BASE_URL}?category=${category}`);
    return response.agents;
  },

  /**
   * エージェントを検索
   */
  async search(query: string, limit: number = 20): Promise<AgentListItem[]> {
    const response = await api.get<AgentListResponse>(
      `${BASE_URL}?search_query=${encodeURIComponent(query)}&limit=${limit}`
    );
    return response.agents;
  },
};

export default agentService;
