/**
 * エージェントプロファイル一覧ページ
 *
 * プロファイル一覧表示と管理操作
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Plus,
  Search,
  Filter,
  Star,
  Copy,
  Edit,
  Trash2,
  Activity,
} from 'lucide-react';
import {
  useProfiles,
  useDeleteProfile,
  useSetDefaultProfile,
  useCloneProfile,
} from '../hooks/useAgentProfiles';
import { PaperType } from '../types';

const ProfilesListPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [paperTypeFilter, setPaperTypeFilter] = useState<PaperType | 'all'>('all');

  // データ取得
  const { data: profiles, isLoading, error } = useProfiles({
    paper_type: paperTypeFilter !== 'all' ? paperTypeFilter : undefined,
    search: searchQuery || undefined,
  });

  const deleteProfileMutation = useDeleteProfile();
  const setDefaultMutation = useSetDefaultProfile();
  const cloneMutation = useCloneProfile();

  // 論文タイプラベル
  const paperTypeLabels: Record<PaperType, string> = {
    [PaperType.MEDICAL]: '医学',
    [PaperType.ENGINEERING]: '工学',
    [PaperType.HUMANITIES]: '人文科学',
    [PaperType.GENERAL]: '一般',
  };

  const handleDelete = (profileId: string, profileName: string) => {
    if (window.confirm(`プロファイル「${profileName}」を削除してもよろしいですか？`)) {
      deleteProfileMutation.mutate(profileId);
    }
  };

  const handleSetDefault = (profileId: string) => {
    if (window.confirm('このプロファイルをデフォルトに設定しますか？')) {
      setDefaultMutation.mutate(profileId);
    }
  };

  const handleClone = (profileId: string, originalName: string) => {
    const newName = window.prompt('新しいプロファイル名を入力してください', `${originalName}のコピー`);
    if (newName) {
      cloneMutation.mutate({ profileId, newName });
    }
  };

  // フィルタリング
  const filteredProfiles = profiles || [];

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center py-12">
          <Activity className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
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
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">エージェントプロファイル</h1>
            <p className="text-gray-600 mt-2">論文タイプごとのエージェント設定を管理</p>
          </div>
          <button
            onClick={() => navigate('/profiles/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            新規作成
          </button>
        </div>

        {/* 統計情報 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">総プロファイル数</p>
                <p className="text-2xl font-bold text-gray-900">{filteredProfiles.length}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          {Object.entries(paperTypeLabels).map(([type, label]) => {
            const count = (profiles || []).filter((p) => p.paper_type === type).length;
            return (
              <div key={type} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{label}</p>
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                  </div>
                  <FileText className="w-8 h-8 text-gray-600" />
                </div>
              </div>
            );
          })}
        </div>

        {/* 検索とフィルター */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="プロファイル名で検索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex gap-2">
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={paperTypeFilter}
                onChange={(e) => setPaperTypeFilter(e.target.value as PaperType | 'all')}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
              >
                <option value="all">すべての論文タイプ</option>
                {Object.entries(paperTypeLabels).map(([type, label]) => (
                  <option key={type} value={type}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* プロファイル一覧 */}
      {filteredProfiles.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">プロファイルがありません</h3>
          <p className="text-gray-600 mb-4">新しいプロファイルを作成してください</p>
          <button
            onClick={() => navigate('/profiles/new')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            プロファイルを作成
          </button>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  プロファイル名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  論文タイプ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  エージェント数
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ステータス
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  更新日時
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredProfiles.map((profile) => (
                <tr
                  key={profile.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/profiles/${profile.id}`)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <FileText className="w-5 h-5 text-blue-600" />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{profile.name}</span>
                          {profile.is_default && (
                            <Star className="w-4 h-4 text-yellow-500 fill-current" />
                          )}
                        </div>
                        {profile.description && (
                          <p className="text-sm text-gray-600 mt-1">{profile.description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {paperTypeLabels[profile.paper_type]}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {profile.settings?.length || 0} 個
                  </td>
                  <td className="px-6 py-4">
                    {profile.is_active ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        有効
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                        無効
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(profile.updated_at).toLocaleDateString('ja-JP')}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                      {!profile.is_default && (
                        <button
                          onClick={() => handleSetDefault(profile.id)}
                          disabled={setDefaultMutation.isPending}
                          className="p-2 text-gray-600 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors disabled:opacity-50"
                          title="デフォルトに設定"
                        >
                          <Star className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleClone(profile.id, profile.name)}
                        disabled={cloneMutation.isPending}
                        className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                        title="複製"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/profiles/${profile.id}/edit`);
                        }}
                        className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="編集"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(profile.id, profile.name)}
                        disabled={deleteProfileMutation.isPending}
                        className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="削除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ProfilesListPage;
