/**
 * LangGraphエージェント管理APIサービス
 */

import api from './api';

// ===== Types =====

export interface LangGraphAgent {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  class_path: string;
  config?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LangGraphIntent {
  id: string;
  intent_name: string;
  display_name: string;
  description?: string;
  agent_id: string;
  agent_name?: string;
  agent_display_name?: string;
  parameters_schema?: Record<string, any>;
  example_query?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LangGraphChainIntent {
  id: string;
  chain_name: string;
  display_name: string;
  description?: string;
  task_sequence: string[];
  example_query?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LangGraphExecutionLog {
  id: string;
  session_id: string;
  user_id: string;
  paper_id: string;
  user_query: string;
  intent?: string;
  agents_used?: string[];
  execution_time_ms?: number;
  validation_result?: string;
  error?: string;
  created_at: string;
}

export interface LangGraphExecutionStats {
  total_executions: number;
  avg_execution_time_ms: number;
  error_count: number;
  success_rate: number;
  intent_distribution: Record<string, number>;
}

export interface AgentCreateRequest {
  name: string;
  display_name: string;
  description?: string;
  class_path: string;
  config?: Record<string, any>;
  is_active?: boolean;
}

export interface AgentUpdateRequest {
  display_name?: string;
  description?: string;
  class_path?: string;
  config?: Record<string, any>;
  is_active?: boolean;
}

export interface IntentCreateRequest {
  intent_name: string;
  display_name: string;
  description?: string;
  agent_id: string;
  parameters_schema?: Record<string, any>;
  example_query?: string;
  is_active?: boolean;
}

export interface ChainIntentCreateRequest {
  chain_name: string;
  display_name: string;
  description?: string;
  task_sequence: string[];
  example_query?: string;
  is_active?: boolean;
}

// API Response Types
interface AgentListResponse {
  agents: LangGraphAgent[];
  total: number;
}

interface IntentListResponse {
  intents: LangGraphIntent[];
  total: number;
}

interface ChainIntentListResponse {
  chain_intents: LangGraphChainIntent[];
  total: number;
}

// ===== Agent Management =====

/**
 * エージェント一覧を取得
 */
export const getAgents = async (onlyActive = true): Promise<LangGraphAgent[]> => {
  const response = await api.get<AgentListResponse>('/api/v1/langgraph-agents/agents', {
    params: { only_active: onlyActive },
  });
  return response.agents;
};

/**
 * エージェント詳細を取得
 */
export const getAgent = async (agentId: string): Promise<LangGraphAgent> => {
  const response = await api.get<LangGraphAgent>(`/api/v1/langgraph-agents/agents/${agentId}`);
  return response;
};

/**
 * エージェントを作成
 */
export const createAgent = async (data: AgentCreateRequest): Promise<LangGraphAgent> => {
  const response = await api.post<LangGraphAgent>('/api/v1/langgraph-agents/agents', data);
  return response;
};

/**
 * エージェントを更新
 */
export const updateAgent = async (
  agentId: string,
  data: AgentUpdateRequest
): Promise<LangGraphAgent> => {
  const response = await api.put<LangGraphAgent>(`/api/v1/langgraph-agents/agents/${agentId}`, data);
  return response;
};

/**
 * エージェントを削除
 */
export const deleteAgent = async (agentId: string): Promise<void> => {
  await api.delete(`/api/v1/langgraph-agents/agents/${agentId}`);
};

// ===== Intent Management =====

/**
 * インテント一覧を取得
 */
export const getIntents = async (
  agentId?: string,
  onlyActive = true
): Promise<LangGraphIntent[]> => {
  const response = await api.get<IntentListResponse>('/api/v1/langgraph-agents/intents', {
    params: { agent_id: agentId, only_active: onlyActive },
  });
  return response.intents;
};

/**
 * インテントを作成
 */
export const createIntent = async (data: IntentCreateRequest): Promise<LangGraphIntent> => {
  const response = await api.post<LangGraphIntent>('/api/v1/langgraph-agents/intents', data);
  return response;
};

// ===== Chain Intent Management =====

/**
 * チェーンインテント一覧を取得
 */
export const getChainIntents = async (onlyActive = true): Promise<LangGraphChainIntent[]> => {
  const response = await api.get<ChainIntentListResponse>('/api/v1/langgraph-agents/chains', {
    params: { only_active: onlyActive },
  });
  return response.chain_intents;
};

/**
 * チェーンインテントを作成
 */
export const createChainIntent = async (
  data: ChainIntentCreateRequest
): Promise<LangGraphChainIntent> => {
  const response = await api.post<LangGraphChainIntent>('/api/v1/langgraph-agents/chains', data);
  return response;
};

// ===== Execution Logs & Stats =====

/**
 * 実行ログを取得
 */
export const getExecutionLogs = async (params?: {
  sessionId?: string;
  userId?: string;
  limit?: number;
}): Promise<LangGraphExecutionLog[]> => {
  const response = await api.get<LangGraphExecutionLog[]>('/api/v1/langgraph-agents/logs', { params });
  return response;
};

/**
 * 実行統計を取得
 */
export const getExecutionStats = async (params?: {
  paperId?: string;
  userId?: string;
}): Promise<LangGraphExecutionStats> => {
  const response = await api.get<LangGraphExecutionStats>('/api/v1/langgraph-agents/stats', {
    params: {
      paper_id: params?.paperId,
      user_id: params?.userId,
    },
  });
  return response;
};
