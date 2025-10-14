/**
 * エージェント管理用カスタムフック
 *
 * React Queryを使用したエージェントのCRUD操作とキャッシュ管理
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import agentService, { AgentListParams, AgentListResponse } from '../services/agentService';
import {
  Agent,
  AgentListItem,
  AgentCreate,
  AgentUpdate,
  AgentStatistics,
  AgentExecutionStats,
  AgentCategory,
} from '../types';

// Query Keys
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (params?: AgentListParams) => [...agentKeys.lists(), params] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
  statistics: () => [...agentKeys.all, 'statistics'] as const,
  executionStats: (id: string) => [...agentKeys.all, 'execution-stats', id] as const,
  active: () => [...agentKeys.all, 'active'] as const,
  system: () => [...agentKeys.all, 'system'] as const,
  custom: () => [...agentKeys.all, 'custom'] as const,
  category: (category: AgentCategory) => [...agentKeys.all, 'category', category] as const,
};

/**
 * エージェント一覧を取得
 */
export function useAgents(
  params?: AgentListParams,
  options?: Omit<UseQueryOptions<AgentListResponse, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentListResponse, Error>({
    queryKey: agentKeys.list(params),
    queryFn: () => agentService.list(params),
    staleTime: 5 * 60 * 1000, // 5分間はキャッシュを新鮮とみなす
    ...options,
  });
}

/**
 * エージェント詳細を取得
 */
export function useAgent(
  agentId: string,
  options?: Omit<UseQueryOptions<Agent, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Agent, Error>({
    queryKey: agentKeys.detail(agentId),
    queryFn: () => agentService.get(agentId),
    enabled: !!agentId,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * エージェント統計情報を取得
 */
export function useAgentStatistics(
  options?: Omit<UseQueryOptions<AgentStatistics, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentStatistics, Error>({
    queryKey: agentKeys.statistics(),
    queryFn: () => agentService.getStatistics(),
    staleTime: 10 * 60 * 1000, // 10分間キャッシュ
    ...options,
  });
}

/**
 * エージェント実行統計を取得
 */
export function useAgentExecutionStats(
  agentId: string,
  options?: Omit<UseQueryOptions<AgentExecutionStats, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentExecutionStats, Error>({
    queryKey: agentKeys.executionStats(agentId),
    queryFn: () => agentService.getExecutionStats(agentId),
    enabled: !!agentId,
    staleTime: 2 * 60 * 1000, // 2分間キャッシュ
    ...options,
  });
}

/**
 * アクティブなエージェント一覧を取得
 */
export function useActiveAgents(
  options?: Omit<UseQueryOptions<AgentListItem[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentListItem[], Error>({
    queryKey: agentKeys.active(),
    queryFn: () => agentService.listActive(),
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * システムエージェント一覧を取得
 */
export function useSystemAgents(
  options?: Omit<UseQueryOptions<AgentListItem[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentListItem[], Error>({
    queryKey: agentKeys.system(),
    queryFn: () => agentService.listSystem(),
    staleTime: 10 * 60 * 1000, // システムエージェントは変更頻度が低いので長めにキャッシュ
    ...options,
  });
}

/**
 * カスタムエージェント一覧を取得
 */
export function useCustomAgents(
  options?: Omit<UseQueryOptions<AgentListItem[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentListItem[], Error>({
    queryKey: agentKeys.custom(),
    queryFn: () => agentService.listCustom(),
    staleTime: 2 * 60 * 1000,
    ...options,
  });
}

/**
 * カテゴリ別エージェント一覧を取得
 */
export function useAgentsByCategory(
  category: AgentCategory,
  options?: Omit<UseQueryOptions<AgentListItem[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentListItem[], Error>({
    queryKey: agentKeys.category(category),
    queryFn: () => agentService.listByCategory(category),
    enabled: !!category,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * エージェントを作成
 */
export function useCreateAgent(
  options?: UseMutationOptions<Agent, Error, AgentCreate>
) {
  const queryClient = useQueryClient();

  return useMutation<Agent, Error, AgentCreate>({
    mutationFn: (data) => agentService.create(data),
    onSuccess: (newAgent) => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: agentKeys.statistics() });
      queryClient.invalidateQueries({ queryKey: agentKeys.custom() });

      toast.success(`エージェント「${newAgent.display_name}」を作成しました`);
    },
    onError: (error) => {
      toast.error(`エージェントの作成に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * エージェントを更新
 */
export function useUpdateAgent(
  options?: UseMutationOptions<Agent, Error, { id: string; data: AgentUpdate }>
) {
  const queryClient = useQueryClient();

  return useMutation<Agent, Error, { id: string; data: AgentUpdate }>({
    mutationFn: ({ id, data }) => agentService.update(id, data),
    onSuccess: (updatedAgent, variables) => {
      // 詳細キャッシュを更新
      queryClient.setQueryData(agentKeys.detail(variables.id), updatedAgent);

      // 一覧キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: agentKeys.statistics() });

      toast.success(`エージェント「${updatedAgent.display_name}」を更新しました`);
    },
    onError: (error) => {
      toast.error(`エージェントの更新に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * エージェントを削除
 */
export function useDeleteAgent(
  options?: UseMutationOptions<{ deleted: boolean; agent_id: string }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation<{ deleted: boolean; agent_id: string }, Error, string>({
    mutationFn: (id) => agentService.delete(id),
    onSuccess: (_, agentId) => {
      // キャッシュから削除
      queryClient.removeQueries({ queryKey: agentKeys.detail(agentId) });

      // 一覧キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: agentKeys.statistics() });
      queryClient.invalidateQueries({ queryKey: agentKeys.custom() });

      toast.success('エージェントを削除しました');
    },
    onError: (error) => {
      toast.error(`エージェントの削除に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * エージェントの有効/無効を切り替え
 */
export function useToggleAgentActive(
  options?: UseMutationOptions<Agent, Error, { id: string; isActive: boolean }>
) {
  const queryClient = useQueryClient();

  return useMutation<Agent, Error, { id: string; isActive: boolean }>({
    mutationFn: ({ id, isActive }) => agentService.toggleActive(id, isActive),
    onSuccess: (updatedAgent, variables) => {
      // 詳細キャッシュを更新
      queryClient.setQueryData(agentKeys.detail(variables.id), updatedAgent);

      // 一覧キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: agentKeys.active() });

      const status = variables.isActive ? '有効' : '無効';
      toast.success(`エージェント「${updatedAgent.display_name}」を${status}にしました`);
    },
    onError: (error) => {
      toast.error(`エージェントの状態変更に失敗しました: ${error.message}`);
    },
    ...options,
  });
}
