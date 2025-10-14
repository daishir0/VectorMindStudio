/**
 * プロファイル作成・編集フォームページ
 *
 * プロファイルの新規作成と既存プロファイルの編集
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Plus, Trash2, Activity } from 'lucide-react';
import {
  useProfile,
  useCreateProfile,
  useUpdateProfile,
  useBulkUpdateProfileSettings,
} from '../hooks/useAgentProfiles';
import { useAgents } from '../hooks/useAgents';
import {
  PaperType,
  AgentProfileCreate,
  AgentProfileUpdate,
  AgentProfileSettingCreate,
} from '../types';

interface AgentSettingFormData extends Omit<AgentProfileSettingCreate, 'custom_config'> {
  custom_config_json: string;
}

const ProfileFormPage: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const navigate = useNavigate();
  const isEditMode = !!profileId && profileId !== 'new';

  // データ取得
  const { data: profile, isLoading: loadingProfile } = useProfile(profileId!, {
    enabled: isEditMode,
  });
  const { data: agentsData } = useAgents();
  const createProfileMutation = useCreateProfile();
  const updateProfileMutation = useUpdateProfile();
  const bulkUpdateSettingsMutation = useBulkUpdateProfileSettings();

  // フォーム状態
  const [formData, setFormData] = useState<AgentProfileCreate | AgentProfileUpdate>({
    name: '',
    paper_type: PaperType.GENERAL,
    description: '',
    is_active: true,
  });

  const [agentSettings, setAgentSettings] = useState<AgentSettingFormData[]>([]);

  // 論文タイプラベル
  const paperTypeLabels: Record<PaperType, string> = {
    [PaperType.MEDICAL]: '医学',
    [PaperType.ENGINEERING]: '工学',
    [PaperType.HUMANITIES]: '人文科学',
    [PaperType.GENERAL]: '一般',
  };

  // 編集モード時のデータ読み込み
  useEffect(() => {
    if (isEditMode && profile) {
      setFormData({
        name: profile.name,
        paper_type: profile.paper_type,
        description: profile.description || '',
        is_active: profile.is_active,
      });

      if (profile.settings) {
        setAgentSettings(
          profile.settings.map((s) => ({
            agent_id: s.agent_id,
            is_enabled: s.is_enabled,
            priority: s.priority,
            max_retries: s.max_retries,
            timeout_seconds: s.timeout_seconds,
            custom_config_json: s.custom_config ? JSON.stringify(s.custom_config, null, 2) : '',
          }))
        );
      }
    }
  }, [isEditMode, profile]);

  const handleInputChange = (field: keyof typeof formData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const addAgentSetting = () => {
    setAgentSettings([
      ...agentSettings,
      {
        agent_id: '',
        is_enabled: true,
        priority: 10,
        max_retries: undefined,
        timeout_seconds: undefined,
        custom_config_json: '',
      },
    ]);
  };

  const removeAgentSetting = (index: number) => {
    setAgentSettings(agentSettings.filter((_, i) => i !== index));
  };

  const updateAgentSetting = (index: number, field: keyof AgentSettingFormData, value: any) => {
    setAgentSettings(
      agentSettings.map((setting, i) => (i === index ? { ...setting, [field]: value } : setting))
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // カスタム設定をJSONパース
    const parsedSettings: AgentProfileSettingCreate[] = agentSettings
      .filter((s) => s.agent_id) // agent_idが空のものは除外
      .map((s) => {
        let customConfig: any = undefined;
        if (s.custom_config_json?.trim()) {
          try {
            customConfig = JSON.parse(s.custom_config_json);
          } catch (err) {
            console.error('Failed to parse custom config:', err);
          }
        }

        return {
          agent_id: s.agent_id,
          is_enabled: s.is_enabled,
          priority: s.priority,
          max_retries: s.max_retries,
          timeout_seconds: s.timeout_seconds,
          custom_config: customConfig,
        };
      });

    if (isEditMode) {
      // 更新モード
      await updateProfileMutation.mutateAsync(
        { id: profileId!, data: formData },
        {
          onSuccess: async (updatedProfile) => {
            // エージェント設定を一括更新
            if (parsedSettings.length > 0) {
              await bulkUpdateSettingsMutation.mutateAsync({
                profileId: updatedProfile.id,
                settings: parsedSettings,
              });
            }
            navigate(`/profiles/${updatedProfile.id}`);
          },
        }
      );
    } else {
      // 作成モード
      createProfileMutation.mutate(formData as AgentProfileCreate, {
        onSuccess: async (newProfile) => {
          // エージェント設定を一括更新
          if (parsedSettings.length > 0) {
            await bulkUpdateSettingsMutation.mutateAsync({
              profileId: newProfile.id,
              settings: parsedSettings,
            });
          }
          navigate(`/profiles/${newProfile.id}`);
        },
      });
    }
  };

  if (isEditMode && loadingProfile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center py-12">
          <Activity className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  const availableAgents = agentsData?.agents || [];
  const isPending = createProfileMutation.isPending || updateProfileMutation.isPending || bulkUpdateSettingsMutation.isPending;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <button
            onClick={() => navigate(isEditMode ? `/profiles/${profileId}` : '/profiles')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            {isEditMode ? 'プロファイル詳細に戻る' : 'プロファイル一覧に戻る'}
          </button>

          <h1 className="text-3xl font-bold text-gray-900">
            {isEditMode ? 'プロファイルを編集' : '新規プロファイル作成'}
          </h1>
        </div>

        {/* フォーム */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本情報 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">基本情報</h2>

            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  プロファイル名 <span className="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="例: 医学論文用プロファイル"
                />
              </div>

              <div>
                <label htmlFor="paper_type" className="block text-sm font-medium text-gray-700 mb-1">
                  論文タイプ <span className="text-red-500">*</span>
                </label>
                <select
                  id="paper_type"
                  required
                  value={formData.paper_type}
                  onChange={(e) => handleInputChange('paper_type', e.target.value as PaperType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {Object.entries(paperTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  説明
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="プロファイルの説明を入力してください"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  id="is_active"
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => handleInputChange('is_active', e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                  有効化
                </label>
              </div>
            </div>
          </div>

          {/* エージェント設定 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">エージェント設定</h2>
              <button
                type="button"
                onClick={addAgentSetting}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                エージェント追加
              </button>
            </div>

            {agentSettings.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="mb-4">エージェント設定がありません</p>
                <button
                  type="button"
                  onClick={addAgentSetting}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  最初のエージェントを追加
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {agentSettings.map((setting, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="font-medium text-gray-900">エージェント {index + 1}</h3>
                      <button
                        type="button"
                        onClick={() => removeAgentSetting(index)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          エージェント <span className="text-red-500">*</span>
                        </label>
                        <select
                          required
                          value={setting.agent_id}
                          onChange={(e) => updateAgentSetting(index, 'agent_id', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">選択してください</option>
                          {availableAgents.map((agent) => (
                            <option key={agent.id} value={agent.id}>
                              {agent.display_name} ({agent.name})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            優先度
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={setting.priority ?? ''}
                            onChange={(e) =>
                              updateAgentSetting(
                                index,
                                'priority',
                                e.target.value ? parseInt(e.target.value) : undefined
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="10"
                          />
                        </div>

                        <div className="flex items-center gap-2 pt-7">
                          <input
                            type="checkbox"
                            checked={setting.is_enabled}
                            onChange={(e) => updateAgentSetting(index, 'is_enabled', e.target.checked)}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <label className="text-sm font-medium text-gray-700">有効化</label>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            最大リトライ回数
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={setting.max_retries ?? ''}
                            onChange={(e) =>
                              updateAgentSetting(
                                index,
                                'max_retries',
                                e.target.value ? parseInt(e.target.value) : undefined
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="3"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            タイムアウト(秒)
                          </label>
                          <input
                            type="number"
                            min="0"
                            value={setting.timeout_seconds ?? ''}
                            onChange={(e) =>
                              updateAgentSetting(
                                index,
                                'timeout_seconds',
                                e.target.value ? parseInt(e.target.value) : undefined
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="300"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          カスタム設定 (JSON)
                        </label>
                        <textarea
                          rows={3}
                          value={setting.custom_config_json}
                          onChange={(e) => updateAgentSetting(index, 'custom_config_json', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                          placeholder='{"key": "value"}'
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* アクションボタン */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate(isEditMode ? `/profiles/${profileId}` : '/profiles')}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {isPending ? '保存中...' : isEditMode ? '更新' : '作成'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileFormPage;
