/**
 * プロファイル詳細ページ
 *
 * プロファイルの詳細情報とエージェント設定の表示
 */
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Edit,
  Trash2,
  Copy,
  Star,
  ArrowLeft,
  Activity,
  Settings,
  ToggleLeft,
  ToggleRight,
  Info,
} from 'lucide-react';
import {
  useProfile,
  useDeleteProfile,
  useSetDefaultProfile,
  useCloneProfile,
  useUpdateProfile,
} from '../hooks/useAgentProfiles';
import { useAgents } from '../hooks/useAgents';
import { PaperType } from '../types';

const ProfileDetailPage: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const navigate = useNavigate();
  const [cloneName, setCloneName] = useState('');

  const { data: profile, isLoading, error } = useProfile(profileId!);
  const { data: agentsData } = useAgents();
  const deleteProfileMutation = useDeleteProfile();
  const setDefaultMutation = useSetDefaultProfile();
  const cloneMutation = useCloneProfile();
  const updateProfileMutation = useUpdateProfile();

  // 論文タイプラベル
  const paperTypeLabels: Record<PaperType, string> = {
    [PaperType.MEDICAL]: '医学',
    [PaperType.ENGINEERING]: '工学',
    [PaperType.HUMANITIES]: '人文科学',
    [PaperType.GENERAL]: '一般',
  };

  const handleDelete = () => {
    if (window.confirm(`プロファイル「${profile?.name}」を削除してもよろしいですか？`)) {
      deleteProfileMutation.mutate(profileId!, {
        onSuccess: () => {
          navigate('/profiles');
        },
      });
    }
  };

  const handleSetDefault = () => {
    if (window.confirm('このプロファイルをデフォルトに設定しますか？')) {
      setDefaultMutation.mutate(profileId!);
    }
  };

  const handleClone = () => {
    const newName = window.prompt('新しいプロファイル名を入力してください', `${profile?.name}のコピー`);
    if (newName) {
      cloneMutation.mutate({ profileId: profileId!, newName });
    }
  };

  const handleToggleActive = () => {
    if (profile) {
      updateProfileMutation.mutate({
        id: profile.id,
        data: { is_active: !profile.is_active },
      });
    }
  };

  // エージェント名を取得
  const getAgentName = (agentId: string): string => {
    const agent = agentsData?.agents.find((a) => a.id === agentId);
    return agent?.display_name || agentId;
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center py-12">
          <Activity className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          プロファイルの取得に失敗しました
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ヘッダー */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/profiles')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          プロファイル一覧に戻る
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <FileText className="w-12 h-12 text-blue-600" />
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-gray-900">{profile.name}</h1>
                {profile.is_default && (
                  <Star className="w-6 h-6 text-yellow-500 fill-current" />
                )}
              </div>
              <p className="text-gray-600 mt-1">
                {paperTypeLabels[profile.paper_type]}
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleToggleActive}
              disabled={updateProfileMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              {profile.is_active ? (
                <>
                  <ToggleRight className="w-5 h-5 text-green-600" />
                  有効
                </>
              ) : (
                <>
                  <ToggleLeft className="w-5 h-5 text-gray-400" />
                  無効
                </>
              )}
            </button>
            {!profile.is_default && (
              <button
                onClick={handleSetDefault}
                disabled={setDefaultMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <Star className="w-4 h-4" />
                デフォルトに設定
              </button>
            )}
            <button
              onClick={handleClone}
              disabled={cloneMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <Copy className="w-4 h-4" />
              複製
            </button>
            <button
              onClick={() => navigate(`/profiles/${profile.id}/edit`)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Edit className="w-4 h-4" />
              編集
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteProfileMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              削除
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* メイン情報 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本情報 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Info className="w-5 h-5" />
              基本情報
            </h2>
            <dl className="space-y-4">
              {profile.description && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">説明</dt>
                  <dd className="mt-1 text-sm text-gray-900">{profile.description}</dd>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">論文タイプ</dt>
                  <dd className="mt-1">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {paperTypeLabels[profile.paper_type]}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">ステータス</dt>
                  <dd className="mt-1">
                    {profile.is_active ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        有効
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                        無効
                      </span>
                    )}
                  </dd>
                </div>
              </div>
            </dl>
          </div>

          {/* エージェント設定 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              エージェント設定
              <span className="text-sm font-normal text-gray-600">
                ({profile.settings?.length || 0}個)
              </span>
            </h2>

            {!profile.settings || profile.settings.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Settings className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>エージェント設定がありません</p>
              </div>
            ) : (
              <div className="space-y-3">
                {profile.settings.map((setting) => (
                  <div
                    key={setting.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {getAgentName(setting.agent_id)}
                        </h3>
                        <div className="mt-2 space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500">有効:</span>
                            <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                              setting.is_enabled
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {setting.is_enabled ? 'Yes' : 'No'}
                            </span>
                          </div>
                          {setting.priority !== undefined && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">優先度:</span>
                              <span className="text-sm text-gray-900">{setting.priority}</span>
                            </div>
                          )}
                          {setting.max_retries !== undefined && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">最大リトライ:</span>
                              <span className="text-sm text-gray-900">{setting.max_retries}回</span>
                            </div>
                          )}
                          {setting.timeout_seconds !== undefined && (
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">タイムアウト:</span>
                              <span className="text-sm text-gray-900">{setting.timeout_seconds}秒</span>
                            </div>
                          )}
                          {setting.custom_config && Object.keys(setting.custom_config).length > 0 && (
                            <div className="mt-2">
                              <span className="text-sm text-gray-500">カスタム設定:</span>
                              <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                                {JSON.stringify(setting.custom_config, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* サイドバー */}
        <div className="space-y-6">
          {/* メタデータ */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">メタデータ</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">ID</dt>
                <dd className="mt-1 text-gray-900 font-mono text-xs break-all">
                  {profile.id}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">作成日時</dt>
                <dd className="mt-1 text-gray-900">
                  {new Date(profile.created_at).toLocaleString('ja-JP')}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">更新日時</dt>
                <dd className="mt-1 text-gray-900">
                  {new Date(profile.updated_at).toLocaleString('ja-JP')}
                </dd>
              </div>
              {profile.created_by && (
                <div>
                  <dt className="text-gray-500">作成者</dt>
                  <dd className="mt-1 text-gray-900">{profile.created_by}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* ステータス情報 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">ステータス</h2>
            <dl className="space-y-3">
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-500">デフォルト</dt>
                <dd>
                  {profile.is_default ? (
                    <Star className="w-5 h-5 text-yellow-500 fill-current" />
                  ) : (
                    <span className="text-sm text-gray-400">-</span>
                  )}
                </dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-500">有効</dt>
                <dd>
                  {profile.is_active ? (
                    <ToggleRight className="w-5 h-5 text-green-600" />
                  ) : (
                    <ToggleLeft className="w-5 h-5 text-gray-400" />
                  )}
                </dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-500">エージェント数</dt>
                <dd className="text-sm font-semibold text-gray-900">
                  {profile.settings?.length || 0}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileDetailPage;
