import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { ArrowLeft, MessageSquare, Save } from 'lucide-react';
import { paperService } from '../services/paperService';
import toast from 'react-hot-toast';

const CreateChatSession: React.FC = () => {
  const { id: paperId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
  });

  const createMutation = useMutation({
    mutationFn: (data: { title: string }) => paperService.createChatSession(paperId!, data),
    onSuccess: (data) => {
      toast.success('チャットセッションが作成されました');
      navigate(`/papers/${paperId}/chat/${data.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'チャットセッションの作成に失敗しました');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      toast.error('セッションタイトルを入力してください');
      return;
    }
    createMutation.mutate(formData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/papers/${paperId}`)}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            論文詳細に戻る
          </button>
          <div className="flex items-center">
            <MessageSquare className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">新しいディスカッション</h1>
              <p className="mt-2 text-gray-600">AIと論文について研究ディスカッションを始めます</p>
            </div>
          </div>
        </div>

        {/* フォーム */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* セッションタイトル */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                セッションタイトル <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="例: 研究手法について相談"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                maxLength={200}
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                {formData.title.length}/200文字
              </p>
            </div>

            {/* ディスカッション機能説明 */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">研究ディスカッション機能</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• AI研究アシスタントと論文について相談できます</li>
                <li>• 複数のAIエージェントが協調して回答します</li>
                <li>• 文献検索・論理検証・執筆支援などを提供</li>
                <li>• 会話履歴は自動で保存されます</li>
              </ul>
            </div>

            {/* ボタン */}
            <div className="flex items-center justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate(`/papers/${paperId}`)}
                className="px-6 py-2 text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="inline-flex items-center px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    作成中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    セッション作成
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* ヒント */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">ディスカッションのヒント</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">効果的な質問例</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>「この論文の構成を改善したい」</li>
                <li>「関連研究を探してください」</li>
                <li>「論理的な問題点を指摘して」</li>
                <li>「この手法の妥当性を検証して」</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">AIアシスタントの機能</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• 論文構造の提案・改善</li>
                <li>• 関連文献の検索・引用</li>
                <li>• 論理構造の検証</li>
                <li>• 執筆内容の改善提案</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateChatSession;