/**
 * エージェントプロファイル管理サービス
 *
 * 論文タイプ別のエージェント設定プロファイルのCRUD操作を提供
 */
import { api } from './api';
import {
  AgentProfile,
  AgentProfileCreate,
  AgentProfileUpdate,
  AgentProfileSettingCreate,
  PaperType,
} from '../types';

const BASE_URL = '/api/v1/agent-profiles';

export interface ProfileListParams {
  paper_type?: PaperType;
  is_default?: boolean;
}

export const agentProfileService = {
  /**
   * プロファイル一覧を取得
   */
  async list(params?: ProfileListParams): Promise<AgentProfile[]> {
    const queryParams = new URLSearchParams();

    if (params) {
      if (params.paper_type) queryParams.append('paper_type', params.paper_type);
      if (params.is_default !== undefined) queryParams.append('is_default', String(params.is_default));
    }

    const url = queryParams.toString() ? `${BASE_URL}?${queryParams.toString()}` : BASE_URL;
    return api.get<AgentProfile[]>(url);
  },

  /**
   * プロファイル詳細を取得
   */
  async get(profileId: string): Promise<AgentProfile> {
    return api.get<AgentProfile>(`${BASE_URL}/${profileId}`);
  },

  /**
   * 新しいプロファイルを作成
   */
  async create(data: AgentProfileCreate): Promise<AgentProfile> {
    return api.post<AgentProfile>(BASE_URL, data);
  },

  /**
   * プロファイルを更新
   */
  async update(profileId: string, data: AgentProfileUpdate): Promise<AgentProfile> {
    return api.put<AgentProfile>(`${BASE_URL}/${profileId}`, data);
  },

  /**
   * プロファイルを削除
   */
  async delete(profileId: string): Promise<{ deleted: boolean; profile_id: string }> {
    return api.delete<{ deleted: boolean; profile_id: string }>(`${BASE_URL}/${profileId}`);
  },

  /**
   * プロファイル設定を一括更新
   */
  async bulkUpdateSettings(
    profileId: string,
    settings: AgentProfileSettingCreate[]
  ): Promise<AgentProfile> {
    return api.put<AgentProfile>(`${BASE_URL}/${profileId}/settings`, settings);
  },

  /**
   * プロファイルをデフォルトに設定
   */
  async setDefault(profileId: string): Promise<AgentProfile> {
    return api.post<AgentProfile>(`${BASE_URL}/${profileId}/set-default`, {});
  },

  /**
   * 論文タイプ別プロファイル一覧を取得
   */
  async listByPaperType(paperType: PaperType): Promise<AgentProfile[]> {
    return api.get<AgentProfile[]>(`${BASE_URL}?paper_type=${paperType}`);
  },

  /**
   * デフォルトプロファイル一覧を取得
   */
  async listDefaults(): Promise<AgentProfile[]> {
    return api.get<AgentProfile[]>(`${BASE_URL}?is_default=true`);
  },

  /**
   * 論文タイプのデフォルトプロファイルを取得
   */
  async getDefaultByPaperType(paperType: PaperType): Promise<AgentProfile | null> {
    const profiles = await api.get<AgentProfile[]>(
      `${BASE_URL}?paper_type=${paperType}&is_default=true`
    );
    return profiles.length > 0 ? profiles[0] : null;
  },

  /**
   * プロファイルを複製
   */
  async clone(profileId: string, newName: string): Promise<AgentProfile> {
    const original = await this.get(profileId);

    const cloneData: AgentProfileCreate = {
      name: newName,
      description: original.description ? `${original.description} (コピー)` : undefined,
      paper_type: original.paper_type,
      is_default: false,
      settings: original.settings.map(s => ({
        agent_id: s.agent_id,
        is_enabled: s.is_enabled,
        priority_override: s.priority_override,
        wake_words_override: s.wake_words_override,
      })),
    };

    return this.create(cloneData);
  },
};

export default agentProfileService;
