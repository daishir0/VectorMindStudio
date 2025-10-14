/**
 * エージェント一覧ページ
 *
 * エージェントの一覧表示、フィルタリング、検索、CRUD操作を提供
 */
import React, { useState } from 'react';
import {
  Bot,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Edit,
  Trash2,
  Eye,
  ToggleLeft,
  ToggleRight,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  useAgents,
  useAgentStatistics,
  useDeleteAgent,
  useToggleAgentActive,
} from '../hooks/useAgents';
import { AgentCategory, ExecutorType, AgentListItem } from '../types';

const AgentsListPage: React.FC = () => {
  const navigate = useNavigate();

  // フィルタ・検索・ページング状態
  const [categoryFilter, setCategoryFilter] = useState<AgentCategory | ''>('');
  const [executorTypeFilter, setExecutorTypeFilter] = useState<ExecutorType | ''>('');
  const [isActiveFilter, setIsActiveFilter] = useState<boolean | undefined>(undefined);
  const [isSystemFilter, setIsSystemFilter] = useState<boolean | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  // データ取得
  const {
    data: agentsData,
    isLoading,
    error,
    refetch,
  } = useAgents({
    category: categoryFilter || undefined,
    executor_type: executorTypeFilter || undefined,
    is_active: isActiveFilter,
    is_system: isSystemFilter,
    search_query: searchQuery || undefined,
    page,
    limit,
  });

  const { data: statistics } = useAgentStatistics();

  // ミューテーション
  const deleteAgentMutation = useDeleteAgent();
  const toggleActiveMutation = useToggleAgentActive();

  const agents = agentsData?.agents || [];
  const total = agentsData?.total || 0;
  const totalPages = Math.ceil(total / limit);

  // ハンドラー
  const handleDelete = (agentId: string) => {
    if (window.confirm('このエージェントを削除してもよろしいですか？')) {
      deleteAgentMutation.mutate(agentId);
    }
  };

  const handleToggleActive = (agentId: string, currentActive: boolean) => {
    toggleActiveMutation.mutate({ id: agentId, isActive: !currentActive });
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1); // 検索時はページをリセット
  };

  const handleFilterChange = () => {
    setPage(1); // フィルタ変更時はページをリセット
  };

  // カテゴリラベルのマッピング
  const categoryLabels: Record<AgentCategory, string> = {
    [AgentCategory.WRITING]: '執筆',
    [AgentCategory.QUALITY]: '品質',
    [AgentCategory.ANALYSIS]: '分析',
    [AgentCategory.SEARCH]: '検索',
    [AgentCategory.CUSTOM]: 'カスタム',
  };

  // 実行タイプラベルのマッピング
  const executorTypeLabels: Record<ExecutorType, string> = {
    [ExecutorType.CODE_BASED]: 'コードベース',
    [ExecutorType.LLM_BASED]: 'LLMベース',
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ヘッダー */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Bot className="w-8 h-8 text-blue-600" />
              エージェント管理
            </h1>
            <p className="mt-2 text-gray-600">AIエージェントの管理・モニタリング</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => refetch()}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              更新
            </button>
            <button
              onClick={() => navigate('/agents/new')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              新規作成
            </button>
          </div>
        </div>
      </div>

      {/* 統計情報 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">総エージェント数</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.total_agents}</p>
              </div>
              <Bot className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">アクティブ</p>
                <p className="text-2xl font-bold text-green-600">{statistics.active_agents}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">システム</p>
                <p className="text-2xl font-bold text-purple-600">{statistics.system_agents}</p>
              </div>
              <Bot className="w-8 h-8 text-purple-600" />
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">カスタム</p>
                <p className="text-2xl font-bold text-orange-600">{statistics.custom_agents}</p>
              </div>
              <Bot className="w-8 h-8 text-orange-600" />
            </div>
          </div>
        </div>
      )}

      {/* 検索・フィルタ */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">検索・フィルタ</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* 検索 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="エージェントを検索..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* カテゴリフィルタ */}
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value as AgentCategory | '');
              handleFilterChange();
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">すべてのカテゴリ</option>
            {Object.entries(categoryLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {/* 実行タイプフィルタ */}
          <select
            value={executorTypeFilter}
            onChange={(e) => {
              setExecutorTypeFilter(e.target.value as ExecutorType | '');
              handleFilterChange();
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">すべての実行タイプ</option>
            {Object.entries(executorTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {/* アクティブフィルタ */}
          <select
            value={isActiveFilter === undefined ? '' : String(isActiveFilter)}
            onChange={(e) => {
              setIsActiveFilter(e.target.value === '' ? undefined : e.target.value === 'true');
              handleFilterChange();
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">すべての状態</option>
            <option value="true">アクティブ</option>
            <option value="false">非アクティブ</option>
          </select>

          {/* システムフィルタ */}
          <select
            value={isSystemFilter === undefined ? '' : String(isSystemFilter)}
            onChange={(e) => {
              setIsSystemFilter(e.target.value === '' ? undefined : e.target.value === 'true');
              handleFilterChange();
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">すべてのタイプ</option>
            <option value="true">システム</option>
            <option value="false">カスタム</option>
          </select>
        </div>
      </div>

      {/* エージェント一覧テーブル */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          エージェントの取得に失敗しました: {(error as Error).message}
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : agents.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">エージェントが見つかりません</p>
          <button
            onClick={() => navigate('/agents/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            最初のエージェントを作成
          </button>
        </div>
      ) : (
        <>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    エージェント名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    カテゴリ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    実行タイプ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状態
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    タイプ
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {agents.map((agent) => (
                  <tr key={agent.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Bot className="w-5 h-5 text-blue-600 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{agent.display_name}</div>
                          <div className="text-sm text-gray-500">{agent.name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        {categoryLabels[agent.category]}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {executorTypeLabels[agent.executor_type]}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleToggleActive(agent.id, agent.is_active)}
                        disabled={toggleActiveMutation.isLoading}
                        className="flex items-center gap-1 text-sm disabled:opacity-50"
                      >
                        {agent.is_active ? (
                          <>
                            <ToggleRight className="w-5 h-5 text-green-600" />
                            <span className="text-green-600">有効</span>
                          </>
                        ) : (
                          <>
                            <ToggleLeft className="w-5 h-5 text-gray-400" />
                            <span className="text-gray-500">無効</span>
                          </>
                        )}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          agent.is_system
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-orange-100 text-orange-800'
                        }`}
                      >
                        {agent.is_system ? 'システム' : 'カスタム'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => navigate(`/agents/${agent.id}`)}
                          className="text-blue-600 hover:text-blue-900"
                          title="詳細表示"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => navigate(`/agents/${agent.id}/edit`)}
                          className="text-gray-600 hover:text-gray-900"
                          title="編集"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        {!agent.is_system && (
                          <button
                            onClick={() => handleDelete(agent.id)}
                            disabled={deleteAgentMutation.isLoading}
                            className="text-red-600 hover:text-red-900 disabled:opacity-50"
                            title="削除"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ページネーション */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                {total}件中 {(page - 1) * limit + 1}～{Math.min(page * limit, total)}件を表示
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-4 py-1 text-sm text-gray-700">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AgentsListPage;
