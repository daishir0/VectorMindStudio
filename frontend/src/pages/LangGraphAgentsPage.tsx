/**
 * LangGraphエージェント一覧ページ
 *
 * 研究ディスカッション用の7つのエージェントを管理します。
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  getAgents,
  getIntents,
  getChainIntents,
  updateAgent,
  LangGraphAgent,
  LangGraphIntent,
  LangGraphChainIntent,
} from '../services/langGraphAgentService';

const LangGraphAgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<LangGraphAgent[]>([]);
  const [intents, setIntents] = useState<LangGraphIntent[]>([]);
  const [chainIntents, setChainIntents] = useState<LangGraphChainIntent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'agents' | 'intents' | 'chains'>('agents');

  // データ取得
  const fetchData = async () => {
    setLoading(true);
    try {
      const [agentsData, intentsData, chainsData] = await Promise.all([
        getAgents(false), // 全エージェント取得
        getIntents(undefined, false), // 全インテント取得
        getChainIntents(false), // 全チェーンインテント取得
      ]);
      setAgents(agentsData);
      setIntents(intentsData);
      setChainIntents(chainsData);
    } catch (error: any) {
      toast.error(`データ取得に失敗しました: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // エージェント有効/無効切り替え
  const toggleAgentActive = async (agent: LangGraphAgent) => {
    try {
      await updateAgent(agent.id, { is_active: !agent.is_active });
      toast.success(
        agent.is_active
          ? `${agent.display_name}を無効にしました`
          : `${agent.display_name}を有効にしました`
      );
      fetchData();
    } catch (error: any) {
      toast.error(`更新に失敗しました: ${error.message}`);
    }
  };

  // エージェント名からカテゴリーを判定
  function getCategoryFromName(name: string): string {
    if (name.includes('outline')) return '構造管理';
    if (name.includes('writer')) return 'コンテンツ生成';
    if (name.includes('analysis')) return '分析';
    if (name.includes('discovery')) return '研究発見';
    if (name.includes('quality')) return '品質保証';
    if (name.includes('strategy')) return '戦略立案';
    if (name.includes('reference')) return '参考文献';
    return 'その他';
  }

  // カテゴリー色を取得
  function getCategoryColor(category: string): string {
    const colors: Record<string, string> = {
      '構造管理': 'bg-blue-100 text-blue-800',
      'コンテンツ生成': 'bg-green-100 text-green-800',
      '分析': 'bg-purple-100 text-purple-800',
      '研究発見': 'bg-yellow-100 text-yellow-800',
      '品質保証': 'bg-red-100 text-red-800',
      '戦略立案': 'bg-indigo-100 text-indigo-800',
      '参考文献': 'bg-pink-100 text-pink-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          LangGraphエージェント管理
        </h1>
        <p className="text-gray-600">
          研究ディスカッション用の7つの専門エージェントを管理します
        </p>
      </div>

      {/* 統計情報 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">エージェント総数</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {agents.length}
              </p>
            </div>
            <div className="ml-4">
              <div className="bg-blue-100 rounded-full p-3">
                <svg
                  className="h-6 w-6 text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">インテント数</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {intents.length}
              </p>
            </div>
            <div className="ml-4">
              <div className="bg-green-100 rounded-full p-3">
                <svg
                  className="h-6 w-6 text-green-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">チェーン数</p>
              <p className="text-2xl font-semibold text-gray-900 mt-1">
                {chainIntents.length}
              </p>
            </div>
            <div className="ml-4">
              <div className="bg-purple-100 rounded-full p-3">
                <svg
                  className="h-6 w-6 text-purple-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* タブ */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('agents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'agents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              エージェント ({agents.length})
            </button>
            <button
              onClick={() => setActiveTab('intents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'intents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              インテント ({intents.length})
            </button>
            <button
              onClick={() => setActiveTab('chains')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chains'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              チェーン ({chainIntents.length})
            </button>
          </nav>
        </div>
      </div>

      {/* エージェント一覧 */}
      {activeTab === 'agents' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => {
            const category = getCategoryFromName(agent.name);
            return (
              <div
                key={agent.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {agent.display_name}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      <span
                        className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(
                          category
                        )}`}
                      >
                        {category}
                      </span>
                      <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        {agent.name}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => toggleAgentActive(agent)}
                    className={`ml-2 px-3 py-1 rounded-md text-sm font-medium flex-shrink-0 ${
                      agent.is_active
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    {agent.is_active ? '有効' : '無効'}
                  </button>
                </div>
                <p className="text-gray-600 text-sm mb-4">{agent.description}</p>
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-500">
                    インテント: {intents.filter((i) => i.agent_id === agent.id).length}件
                  </div>
                  <Link
                    to={`/langgraph-agents/${agent.id}`}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    詳細 →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* インテント一覧 */}
      {activeTab === 'intents' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  インテント名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  エージェント
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  説明
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ステータス
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {intents.map((intent) => (
                <tr key={intent.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {intent.display_name}
                    </div>
                    <div className="text-xs text-gray-500">{intent.intent_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{intent.agent_display_name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-600">{intent.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        intent.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {intent.is_active ? '有効' : '無効'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* チェーンインテント一覧 */}
      {activeTab === 'chains' && (
        <div className="grid grid-cols-1 gap-6">
          {chainIntents.map((chain) => (
            <div key={chain.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {chain.display_name}
                  </h3>
                  <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    {chain.chain_name}
                  </span>
                </div>
                <span
                  className={`px-3 py-1 rounded-md text-sm font-medium ${
                    chain.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {chain.is_active ? '有効' : '無効'}
                </span>
              </div>
              <p className="text-gray-600 text-sm mb-4">{chain.description}</p>
              <div className="mb-3">
                <div className="text-sm font-medium text-gray-700 mb-2">タスク順序:</div>
                <div className="flex flex-wrap gap-2">
                  {chain.task_sequence.map((task, index) => (
                    <React.Fragment key={index}>
                      <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-md text-sm">
                        {task}
                      </span>
                      {index < chain.task_sequence.length - 1 && (
                        <span className="text-gray-400">→</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
              {chain.example_query && (
                <div className="text-sm text-gray-500">
                  <span className="font-medium">例: </span>
                  {chain.example_query}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LangGraphAgentsPage;
