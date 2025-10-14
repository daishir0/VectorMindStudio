/**
 * エージェント詳細ページ
 *
 * エージェントの詳細情報表示と操作
 */
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Bot,
  Edit,
  Trash2,
  ArrowLeft,
  ToggleLeft,
  ToggleRight,
  Clock,
  TrendingUp,
  Activity,
  Tag,
  Code,
  Zap,
} from 'lucide-react';
import { useAgent, useAgentExecutionStats, useDeleteAgent, useToggleAgentActive } from '../hooks/useAgents';
import { AgentCategory, ExecutorType, ResponseFormat } from '../types';

const AgentDetailPage: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();

  const { data: agent, isLoading, error } = useAgent(agentId!);
  const { data: stats } = useAgentExecutionStats(agentId!);
  const deleteAgentMutation = useDeleteAgent();
  const toggleActiveMutation = useToggleAgentActive();

  const handleDelete = () => {
    if (window.confirm('このエージェントを削除してもよろしいですか？')) {
      deleteAgentMutation.mutate(agentId!, {
        onSuccess: () => {
          navigate('/agents');
        },
      });
    }
  };

  const handleToggleActive = () => {
    if (agent) {
      toggleActiveMutation.mutate({ id: agent.id, isActive: !agent.is_active });
    }
  };

  // カテゴリラベル
  const categoryLabels: Record<AgentCategory, string> = {
    [AgentCategory.WRITING]: '執筆',
    [AgentCategory.QUALITY]: '品質',
    [AgentCategory.ANALYSIS]: '分析',
    [AgentCategory.SEARCH]: '検索',
    [AgentCategory.CUSTOM]: 'カスタム',
  };

  // 実行タイプラベル
  const executorTypeLabels: Record<ExecutorType, string> = {
    [ExecutorType.CODE_BASED]: 'コードベース',
    [ExecutorType.LLM_BASED]: 'LLMベース',
  };

  // レスポンス形式ラベル
  const responseFormatLabels: Record<ResponseFormat, string> = {
    [ResponseFormat.TEXT]: 'テキスト',
    [ResponseFormat.JSON]: 'JSON',
    [ResponseFormat.MARKDOWN]: 'Markdown',
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

  if (error || !agent) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          エージェントの取得に失敗しました
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ヘッダー */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/agents')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          エージェント一覧に戻る
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Bot className="w-12 h-12 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{agent.display_name}</h1>
              <p className="text-gray-600">{agent.name}</p>
            </div>
            {agent.is_system && (
              <span className="px-3 py-1 text-sm font-medium rounded-full bg-purple-100 text-purple-800">
                システムエージェント
              </span>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleToggleActive}
              disabled={toggleActiveMutation.isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              {agent.is_active ? (
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
            <button
              onClick={() => navigate(`/agents/${agent.id}/edit`)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Edit className="w-4 h-4" />
              編集
            </button>
            {!agent.is_system && (
              <button
                onClick={handleDelete}
                disabled={deleteAgentMutation.isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                削除
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* メイン情報 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本情報 */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">基本情報</h2>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">説明</dt>
                <dd className="mt-1 text-sm text-gray-900">{agent.description}</dd>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">カテゴリ</dt>
                  <dd className="mt-1">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {categoryLabels[agent.category]}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">実行タイプ</dt>
                  <dd className="mt-1">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800">
                      {executorTypeLabels[agent.executor_type]}
                    </span>
                  </dd>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">優先度</dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent.priority}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">レスポンス形式</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {agent.response_format ? responseFormatLabels[agent.response_format] : 'テキスト'}
                  </dd>
                </div>
              </div>
              {agent.executor_type === ExecutorType.CODE_BASED && agent.class_path && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 flex items-center gap-2">
                    <Code className="w-4 h-4" />
                    クラスパス
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded">
                    {agent.class_path}
                  </dd>
                </div>
              )}
              {agent.executor_type === ExecutorType.LLM_BASED && agent.llm_model && (
                <div>
                  <dt className="text-sm font-medium text-gray-500 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    LLMモデル
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent.llm_model}</dd>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">最大リトライ回数</dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent.max_retries}回</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">タイムアウト</dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent.timeout_seconds}秒</dd>
                </div>
              </div>
            </dl>
          </div>

          {/* システムプロンプト */}
          {agent.executor_type === ExecutorType.LLM_BASED && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">プロンプト設定</h2>
              <div className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-2">システムプロンプト</dt>
                  <dd className="text-sm text-gray-900 bg-gray-50 px-4 py-3 rounded-lg whitespace-pre-wrap">
                    {agent.system_prompt}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 mb-2">ユーザープロンプトテンプレート</dt>
                  <dd className="text-sm text-gray-900 bg-gray-50 px-4 py-3 rounded-lg whitespace-pre-wrap">
                    {agent.user_prompt_template}
                  </dd>
                </div>
              </div>
            </div>
          )}

          {/* ウェイクワード */}
          {agent.wake_words && agent.wake_words.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">ウェイクワード</h2>
              <div className="flex flex-wrap gap-2">
                {agent.wake_words.map((ww) => (
                  <span
                    key={ww.id}
                    className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-lg flex items-center gap-2"
                  >
                    {ww.keyword}
                    <span className="text-xs text-blue-500">({ww.match_type})</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 能力 */}
          {agent.capabilities && agent.capabilities.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">能力</h2>
              <div className="space-y-3">
                {agent.capabilities.map((cap) => (
                  <div key={cap.id} className="border-l-4 border-blue-500 pl-4">
                    <h3 className="text-sm font-medium text-gray-900">{cap.task_type}</h3>
                    <p className="text-sm text-gray-600 mt-1">{cap.description}</p>
                    {cap.success_rate !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        成功率: {(cap.success_rate * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* タグ */}
          {agent.tags && agent.tags.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Tag className="w-5 h-5" />
                タグ
              </h2>
              <div className="flex flex-wrap gap-2">
                {agent.tags.map((tag, idx) => (
                  <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* サイドバー */}
        <div className="space-y-6">
          {/* 実行統計 */}
          {stats && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                実行統計
              </h2>
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm text-gray-500">総実行回数</dt>
                  <dd className="mt-1 text-2xl font-bold text-gray-900">{stats.total_executions}</dd>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-sm text-gray-500">成功</dt>
                    <dd className="mt-1 text-lg font-semibold text-green-600">{stats.success_count}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-gray-500">失敗</dt>
                    <dd className="mt-1 text-lg font-semibold text-red-600">{stats.failure_count}</dd>
                  </div>
                </div>
                <div>
                  <dt className="text-sm text-gray-500 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    平均実行時間
                  </dt>
                  <dd className="mt-1 text-lg font-semibold text-gray-900">{stats.avg_execution_time_ms}ms</dd>
                </div>
                {stats.last_executed_at && (
                  <div>
                    <dt className="text-sm text-gray-500">最終実行日時</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {new Date(stats.last_executed_at).toLocaleString('ja-JP')}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* メタデータ */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">メタデータ</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">作成日時</dt>
                <dd className="mt-1 text-gray-900">
                  {new Date(agent.created_at).toLocaleString('ja-JP')}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">更新日時</dt>
                <dd className="mt-1 text-gray-900">
                  {new Date(agent.updated_at).toLocaleString('ja-JP')}
                </dd>
              </div>
              {agent.created_by && (
                <div>
                  <dt className="text-gray-500">作成者</dt>
                  <dd className="mt-1 text-gray-900">{agent.created_by}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentDetailPage;
