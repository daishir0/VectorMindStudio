/**
 * エージェントプロファイル管理用カスタムフック
 *
 * React Queryを使用したプロファイルのCRUD操作とキャッシュ管理
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import agentProfileService, { ProfileListParams } from '../services/agentProfileService';
import {
  AgentProfile,
  AgentProfileCreate,
  AgentProfileUpdate,
  AgentProfileSettingCreate,
  PaperType,
} from '../types';

// Query Keys
export const profileKeys = {
  all: ['agent-profiles'] as const,
  lists: () => [...profileKeys.all, 'list'] as const,
  list: (params?: ProfileListParams) => [...profileKeys.lists(), params] as const,
  details: () => [...profileKeys.all, 'detail'] as const,
  detail: (id: string) => [...profileKeys.details(), id] as const,
  defaults: () => [...profileKeys.all, 'defaults'] as const,
  defaultByPaperType: (paperType: PaperType) => [...profileKeys.defaults(), paperType] as const,
  byPaperType: (paperType: PaperType) => [...profileKeys.all, 'paper-type', paperType] as const,
};

/**
 * プロファイル一覧を取得
 */
export function useProfiles(
  params?: ProfileListParams,
  options?: Omit<UseQueryOptions<AgentProfile[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentProfile[], Error>({
    queryKey: profileKeys.list(params),
    queryFn: () => agentProfileService.list(params),
    staleTime: 5 * 60 * 1000, // 5分間はキャッシュを新鮮とみなす
    ...options,
  });
}

/**
 * プロファイル詳細を取得
 */
export function useProfile(
  profileId: string,
  options?: Omit<UseQueryOptions<AgentProfile, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentProfile, Error>({
    queryKey: profileKeys.detail(profileId),
    queryFn: () => agentProfileService.get(profileId),
    enabled: !!profileId,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * デフォルトプロファイル一覧を取得
 */
export function useDefaultProfiles(
  options?: Omit<UseQueryOptions<AgentProfile[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentProfile[], Error>({
    queryKey: profileKeys.defaults(),
    queryFn: () => agentProfileService.listDefaults(),
    staleTime: 10 * 60 * 1000, // デフォルトは変更頻度が低いので長めにキャッシュ
    ...options,
  });
}

/**
 * 論文タイプのデフォルトプロファイルを取得
 */
export function useDefaultProfileByPaperType(
  paperType: PaperType,
  options?: Omit<UseQueryOptions<AgentProfile | null, Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentProfile | null, Error>({
    queryKey: profileKeys.defaultByPaperType(paperType),
    queryFn: () => agentProfileService.getDefaultByPaperType(paperType),
    enabled: !!paperType,
    staleTime: 10 * 60 * 1000,
    ...options,
  });
}

/**
 * 論文タイプ別プロファイル一覧を取得
 */
export function useProfilesByPaperType(
  paperType: PaperType,
  options?: Omit<UseQueryOptions<AgentProfile[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<AgentProfile[], Error>({
    queryKey: profileKeys.byPaperType(paperType),
    queryFn: () => agentProfileService.listByPaperType(paperType),
    enabled: !!paperType,
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

/**
 * プロファイルを作成
 */
export function useCreateProfile(
  options?: UseMutationOptions<AgentProfile, Error, AgentProfileCreate>
) {
  const queryClient = useQueryClient();

  return useMutation<AgentProfile, Error, AgentProfileCreate>({
    mutationFn: (data) => agentProfileService.create(data),
    onSuccess: (newProfile) => {
      // キャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      queryClient.invalidateQueries({ queryKey: profileKeys.byPaperType(newProfile.paper_type) });

      toast.success(`プロファイル「${newProfile.name}」を作成しました`);
    },
    onError: (error) => {
      toast.error(`プロファイルの作成に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * プロファイルを更新
 */
export function useUpdateProfile(
  options?: UseMutationOptions<AgentProfile, Error, { id: string; data: AgentProfileUpdate }>
) {
  const queryClient = useQueryClient();

  return useMutation<AgentProfile, Error, { id: string; data: AgentProfileUpdate }>({
    mutationFn: ({ id, data }) => agentProfileService.update(id, data),
    onSuccess: (updatedProfile, variables) => {
      // 詳細キャッシュを更新
      queryClient.setQueryData(profileKeys.detail(variables.id), updatedProfile);

      // 一覧キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      queryClient.invalidateQueries({ queryKey: profileKeys.byPaperType(updatedProfile.paper_type) });

      toast.success(`プロファイル「${updatedProfile.name}」を更新しました`);
    },
    onError: (error) => {
      toast.error(`プロファイルの更新に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * プロファイルを削除
 */
export function useDeleteProfile(
  options?: UseMutationOptions<{ deleted: boolean; profile_id: string }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation<{ deleted: boolean; profile_id: string }, Error, string>({
    mutationFn: (id) => agentProfileService.delete(id),
    onSuccess: (_, profileId) => {
      // キャッシュから削除
      queryClient.removeQueries({ queryKey: profileKeys.detail(profileId) });

      // 一覧キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });

      toast.success('プロファイルを削除しました');
    },
    onError: (error) => {
      toast.error(`プロファイルの削除に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * プロファイル設定を一括更新
 */
export function useBulkUpdateProfileSettings(
  options?: UseMutationOptions<
    AgentProfile,
    Error,
    { profileId: string; settings: AgentProfileSettingCreate[] }
  >
) {
  const queryClient = useQueryClient();

  return useMutation<
    AgentProfile,
    Error,
    { profileId: string; settings: AgentProfileSettingCreate[] }
  >({
    mutationFn: ({ profileId, settings }) =>
      agentProfileService.bulkUpdateSettings(profileId, settings),
    onSuccess: (updatedProfile, variables) => {
      // 詳細キャッシュを更新
      queryClient.setQueryData(profileKeys.detail(variables.profileId), updatedProfile);

      // 一覧キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });

      toast.success('プロファイル設定を更新しました');
    },
    onError: (error) => {
      toast.error(`プロファイル設定の更新に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * プロファイルをデフォルトに設定
 */
export function useSetDefaultProfile(
  options?: UseMutationOptions<AgentProfile, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation<AgentProfile, Error, string>({
    mutationFn: (profileId) => agentProfileService.setDefault(profileId),
    onSuccess: (updatedProfile) => {
      // デフォルト関連のキャッシュを無効化
      queryClient.invalidateQueries({ queryKey: profileKeys.defaults() });
      queryClient.invalidateQueries({ queryKey: profileKeys.defaultByPaperType(updatedProfile.paper_type) });
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      queryClient.invalidateQueries({ queryKey: profileKeys.byPaperType(updatedProfile.paper_type) });

      toast.success(`「${updatedProfile.name}」をデフォルトプロファイルに設定しました`);
    },
    onError: (error) => {
      toast.error(`デフォルトプロファイルの設定に失敗しました: ${error.message}`);
    },
    ...options,
  });
}

/**
 * プロファイルを複製
 */
export function useCloneProfile(
  options?: UseMutationOptions<AgentProfile, Error, { profileId: string; newName: string }>
) {
  const queryClient = useQueryClient();

  return useMutation<AgentProfile, Error, { profileId: string; newName: string }>({
    mutationFn: ({ profileId, newName }) => agentProfileService.clone(profileId, newName),
    onSuccess: (newProfile) => {
      // キャッシュを無効化
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      queryClient.invalidateQueries({ queryKey: profileKeys.byPaperType(newProfile.paper_type) });

      toast.success(`プロファイル「${newProfile.name}」を作成しました`);
    },
    onError: (error) => {
      toast.error(`プロファイルの複製に失敗しました: ${error.message}`);
    },
    ...options,
  });
}
