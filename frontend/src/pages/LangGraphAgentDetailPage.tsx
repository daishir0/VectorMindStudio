/**
 * LangGraphエージェント詳細ページ
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  getAgent,
  getIntents,
  updateAgent,
  LangGraphAgent,
  LangGraphIntent,
} from '../services/langGraphAgentService';

const LangGraphAgentDetailPage: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();

  const [agent, setAgent] = useState<LangGraphAgent | null>(null);
  const [intents, setIntents] = useState<LangGraphIntent[]>([]);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({
    description: '',
    config: {} as Record<string, any>,
  });

  // データ取得
  const fetchData = async () => {
    if (!agentId) return;

    setLoading(true);
    try {
      const [agentData, intentsData] = await Promise.all([
        getAgent(agentId),
        getIntents(agentId, false),
      ]);
      setAgent(agentData);
      setIntents(intentsData);
      setEditData({
        description: agentData.description || '',
        config: agentData.config || {},
      });
    } catch (error: any) {
      toast.error(`データ取得に失敗しました: ${error.message}`);
      navigate('/langgraph-agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [agentId]);

  // エージェント更新
  const handleUpdate = async () => {
    if (!agent) return;

    try {
      await updateAgent(agent.id, editData);
      toast.success('エージェントを更新しました');
      setEditMode(false);
      fetchData();
    } catch (error: any) {
      toast.error(`更新に失敗しました: ${error.message}`);
    }
  };

  // 有効/無効切り替え
  const toggleActive = async () => {
    if (!agent) return;

    try {
      await updateAgent(agent.id, { is_active: !agent.is_active });
      toast.success(
        agent.is_active
          ? 'エージェントを無効にしました'
          : 'エージェントを有効にしました'
      );
      fetchData();
    } catch (error: any) {
      toast.error(`更新に失敗しました: ${error.message}`);
    }
  };

  if (loading || !agent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* ヘッダー */}
      <div className="mb-8">
        <div className="flex items-center mb-4">
          <Link
            to="/langgraph-agents"
            className="text-blue-600 hover:text-blue-700 mr-4"
          >
            ← 一覧に戻る
          </Link>
        </div>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {agent.display_name}
            </h1>
            <p className="text-gray-600">{agent.name}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={toggleActive}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                agent.is_active
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              }`}
            >
              {agent.is_active ? '有効' : '無効'}
            </button>
            {!editMode ? (
              <button
                onClick={() => setEditMode(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                編集
              </button>
            ) : (
              <>
                <button
                  onClick={handleUpdate}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  保存
                </button>
                <button
                  onClick={() => {
                    setEditMode(false);
                    setEditData({
                      description: agent.description || '',
                      config: agent.config || {},
                    });
                  }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  キャンセル
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 基本情報 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">基本情報</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              説明
            </label>
            {editMode ? (
              <textarea
                value={editData.description}
                onChange={(e) =>
                  setEditData({ ...editData, description: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            ) : (
              <p className="text-gray-600">{agent.description}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              クラスパス
            </label>
            <p className="text-gray-600 font-mono text-sm">{agent.class_path}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              作成日時
            </label>
            <p className="text-gray-600">
              {new Date(agent.created_at).toLocaleString('ja-JP')}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              更新日時
            </label>
            <p className="text-gray-600">
              {new Date(agent.updated_at).toLocaleString('ja-JP')}
            </p>
          </div>
        </div>
      </div>

      {/* 設定 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">設定</h2>
        {editMode ? (
          <textarea
            value={JSON.stringify(editData.config, null, 2)}
            onChange={(e) => {
              try {
                const config = JSON.parse(e.target.value);
                setEditData({ ...editData, config });
              } catch {
                // JSON パースエラーは無視
              }
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            rows={10}
          />
        ) : (
          <pre className="bg-gray-50 p-4 rounded-md overflow-auto text-sm">
            {JSON.stringify(agent.config, null, 2)}
          </pre>
        )}
      </div>

      {/* インテント一覧 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          インテント ({intents.length})
        </h2>
        {intents.length === 0 ? (
          <p className="text-gray-500">インテントが登録されていません</p>
        ) : (
          <div className="space-y-4">
            {intents.map((intent) => (
              <div key={intent.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-medium text-gray-900">{intent.display_name}</h3>
                    <p className="text-sm text-gray-500">{intent.intent_name}</p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded-md text-xs font-medium ${
                      intent.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {intent.is_active ? '有効' : '無効'}
                  </span>
                </div>
                {intent.description && (
                  <p className="text-sm text-gray-600 mb-2">{intent.description}</p>
                )}
                {intent.example_query && (
                  <div className="text-sm text-gray-500 bg-gray-50 p-2 rounded">
                    <span className="font-medium">例: </span>
                    {intent.example_query}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LangGraphAgentDetailPage;
