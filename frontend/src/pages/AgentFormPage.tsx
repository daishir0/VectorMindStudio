/**
 * エージェント作成・編集フォームページ
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Plus, X } from 'lucide-react';
import { useAgent, useCreateAgent, useUpdateAgent } from '../hooks/useAgents';
import {
  AgentCategory,
  ExecutorType,
  ResponseFormat,
  WakeWordMatchType,
  AgentCreate,
  AgentUpdate,
  WakeWordCreate,
  CapabilityCreate,
} from '../types';

const AgentFormPage: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const isEditMode = !!agentId;

  const { data: agent } = useAgent(agentId!, { enabled: isEditMode });
  const createMutation = useCreateAgent();
  const updateMutation = useUpdateAgent();

  // フォーム状態
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    description: '',
    category: AgentCategory.CUSTOM,
    priority: 10,
    executor_type: ExecutorType.LLM_BASED,
    class_path: '',
    llm_model: 'gpt-4o-mini',
    max_retries: 3,
    timeout_seconds: 90,
    system_prompt: '',
    user_prompt_template: '',
    response_format: ResponseFormat.TEXT,
    tags: [] as string[],
  });

  const [wakeWords, setWakeWords] = useState<WakeWordCreate[]>([]);
  const [capabilities, setCapabilities] = useState<CapabilityCreate[]>([]);
  const [newTag, setNewTag] = useState('');

  // 編集モード時にデータをロード
  useEffect(() => {
    if (agent) {
      setFormData({
        name: agent.name,
        display_name: agent.display_name,
        description: agent.description,
        category: agent.category,
        priority: agent.priority,
        executor_type: agent.executor_type,
        class_path: agent.class_path || '',
        llm_model: agent.llm_model || 'gpt-4o-mini',
        max_retries: agent.max_retries,
        timeout_seconds: agent.timeout_seconds,
        system_prompt: agent.system_prompt,
        user_prompt_template: agent.user_prompt_template,
        response_format: agent.response_format || ResponseFormat.TEXT,
        tags: agent.tags || [],
      });

      if (agent.wake_words) {
        setWakeWords(
          agent.wake_words.map((ww) => ({
            keyword: ww.keyword,
            match_type: ww.match_type,
            priority: ww.priority,
            is_active: ww.is_active,
          }))
        );
      }

      if (agent.capabilities) {
        setCapabilities(
          agent.capabilities.map((cap) => ({
            task_type: cap.task_type,
            description: cap.description,
          }))
        );
      }
    }
  }, [agent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: AgentCreate | AgentUpdate = {
      ...formData,
      wake_words: wakeWords,
      capabilities: capabilities,
    };

    try {
      if (isEditMode) {
        await updateMutation.mutateAsync({ id: agentId!, data });
        navigate(`/agents/${agentId}`);
      } else {
        const newAgent = await createMutation.mutateAsync(data as AgentCreate);
        navigate(`/agents/${newAgent.id}`);
      }
    } catch (error) {
      console.error('保存エラー:', error);
    }
  };

  const addWakeWord = () => {
    setWakeWords([
      ...wakeWords,
      {
        keyword: '',
        match_type: WakeWordMatchType.EXACT,
        priority: 10,
        is_active: true,
      },
    ]);
  };

  const removeWakeWord = (index: number) => {
    setWakeWords(wakeWords.filter((_, i) => i !== index));
  };

  const updateWakeWord = (index: number, field: keyof WakeWordCreate, value: any) => {
    const updated = [...wakeWords];
    updated[index] = { ...updated[index], [field]: value };
    setWakeWords(updated);
  };

  const addCapability = () => {
    setCapabilities([
      ...capabilities,
      {
        task_type: '',
        description: '',
      },
    ]);
  };

  const removeCapability = (index: number) => {
    setCapabilities(capabilities.filter((_, i) => i !== index));
  };

  const updateCapability = (index: number, field: keyof CapabilityCreate, value: any) => {
    const updated = [...capabilities];
    updated[index] = { ...updated[index], [field]: value };
    setCapabilities(updated);
  };

  const addTag = () => {
    if (newTag && !formData.tags.includes(newTag)) {
      setFormData({ ...formData, tags: [...formData.tags, newTag] });
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={() => navigate('/agents')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        エージェント一覧に戻る
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          {isEditMode ? 'エージェント編集' : '新規エージェント作成'}
        </h1>
        <p className="mt-2 text-gray-600">
          {isEditMode ? 'エージェントの設定を編集します' : 'カスタムエージェントを作成します'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-4xl space-y-8">
        {/* 基本情報 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">基本情報</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  エージェント名 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="agent_name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  表示名 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.display_name}
                  onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="エージェント名"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">説明 *</label>
              <textarea
                required
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="エージェントの説明を入力..."
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリ *</label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value as AgentCategory })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={AgentCategory.WRITING}>執筆</option>
                  <option value={AgentCategory.QUALITY}>品質</option>
                  <option value={AgentCategory.ANALYSIS}>分析</option>
                  <option value={AgentCategory.SEARCH}>検索</option>
                  <option value={AgentCategory.CUSTOM}>カスタム</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">実行タイプ *</label>
                <select
                  required
                  value={formData.executor_type}
                  onChange={(e) => setFormData({ ...formData, executor_type: e.target.value as ExecutorType })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={ExecutorType.LLM_BASED}>LLMベース</option>
                  <option value={ExecutorType.CODE_BASED}>コードベース</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">優先度</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">最大リトライ回数</label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={formData.max_retries}
                  onChange={(e) => setFormData({ ...formData, max_retries: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">タイムアウト（秒）</label>
                <input
                  type="number"
                  min={10}
                  max={300}
                  value={formData.timeout_seconds}
                  onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 実行設定 */}
        {formData.executor_type === ExecutorType.LLM_BASED && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">LLM設定</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">LLMモデル</label>
                  <select
                    value={formData.llm_model}
                    onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4o-mini">GPT-4o-mini</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">レスポンス形式</label>
                  <select
                    value={formData.response_format}
                    onChange={(e) => setFormData({ ...formData, response_format: e.target.value as ResponseFormat })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value={ResponseFormat.TEXT}>テキスト</option>
                    <option value={ResponseFormat.JSON}>JSON</option>
                    <option value={ResponseFormat.MARKDOWN}>Markdown</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">システムプロンプト *</label>
                <textarea
                  required
                  rows={5}
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  placeholder="You are an AI agent that..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ユーザープロンプトテンプレート *</label>
                <textarea
                  required
                  rows={3}
                  value={formData.user_prompt_template}
                  onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  placeholder="Task: {task_description}"
                />
              </div>
            </div>
          </div>
        )}

        {formData.executor_type === ExecutorType.CODE_BASED && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">コード設定</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">クラスパス *</label>
              <input
                type="text"
                required
                value={formData.class_path}
                onChange={(e) => setFormData({ ...formData, class_path: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                placeholder="app.services.agents.my_agent:MyAgent"
              />
              <p className="mt-1 text-sm text-gray-500">形式: module.path:ClassName</p>
            </div>
          </div>
        )}

        {/* ウェイクワード */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">ウェイクワード</h2>
            <button
              type="button"
              onClick={addWakeWord}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              追加
            </button>
          </div>
          <div className="space-y-3">
            {wakeWords.map((ww, index) => (
              <div key={index} className="flex gap-3 items-start p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 grid grid-cols-3 gap-3">
                  <input
                    type="text"
                    placeholder="キーワード"
                    value={ww.keyword}
                    onChange={(e) => updateWakeWord(index, 'keyword', e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <select
                    value={ww.match_type}
                    onChange={(e) => updateWakeWord(index, 'match_type', e.target.value as WakeWordMatchType)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={WakeWordMatchType.EXACT}>完全一致</option>
                    <option value={WakeWordMatchType.SEMANTIC}>意味的一致</option>
                    <option value={WakeWordMatchType.REGEX}>正規表現</option>
                  </select>
                  <input
                    type="number"
                    placeholder="優先度"
                    value={ww.priority}
                    onChange={(e) => updateWakeWord(index, 'priority', parseInt(e.target.value))}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removeWakeWord(index)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* 能力 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">能力</h2>
            <button
              type="button"
              onClick={addCapability}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              追加
            </button>
          </div>
          <div className="space-y-3">
            {capabilities.map((cap, index) => (
              <div key={index} className="flex gap-3 items-start p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 space-y-2">
                  <input
                    type="text"
                    placeholder="タスクタイプ"
                    value={cap.task_type}
                    onChange={(e) => updateCapability(index, 'task_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="説明"
                    value={cap.description}
                    onChange={(e) => updateCapability(index, 'description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => removeCapability(index)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* タグ */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">タグ</h2>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              placeholder="タグを入力..."
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={addTag}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              追加
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.tags.map((tag) => (
              <span
                key={tag}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg flex items-center gap-2"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => removeTag(tag)}
                  className="text-gray-500 hover:text-red-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* 送信ボタン */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={createMutation.isLoading || updateMutation.isLoading}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isEditMode ? '更新' : '作成'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/agents')}
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            キャンセル
          </button>
        </div>
      </form>
    </div>
  );
};

export default AgentFormPage;
