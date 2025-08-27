import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { ArrowLeft, Save, FileText } from 'lucide-react';
import { paperService } from '../services/paperService';
import toast from 'react-hot-toast';

const CreatePaper: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
  });

  const createMutation = useMutation({
    mutationFn: paperService.createPaper,
    onSuccess: (data) => {
      toast.success('論文が作成されました');
      navigate(`/papers/${data.id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '論文の作成に失敗しました');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      toast.error('タイトルを入力してください');
      return;
    }
    createMutation.mutate(formData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/papers')}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            論文一覧に戻る
          </button>
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">新しい論文を作成</h1>
              <p className="mt-2 text-gray-600">AI支援による学術論文の執筆を開始します</p>
            </div>
          </div>
        </div>

        {/* フォーム */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* タイトル */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                論文タイトル <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="例: 機械学習における説明可能性の向上に関する研究"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                maxLength={500}
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                {formData.title.length}/500文字
              </p>
            </div>

            {/* 説明 */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                論文の概要・説明
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                placeholder="この論文の目的、背景、期待される成果などを簡潔に記述してください..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                maxLength={2000}
              />
              <p className="mt-1 text-sm text-gray-500">
                {formData.description.length}/2000文字
              </p>
            </div>

            {/* 作成後の流れ説明 */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">作成後の流れ</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• AIアシスタントが論文構造の提案を行います</li>
                <li>• セクションごとに内容を執筆・編集できます</li>
                <li>• 研究ディスカッション機能で質問や相談ができます</li>
                <li>• 文献検索・引用管理機能が利用できます</li>
                <li>• 論理構造の検証とフィードバックを受けられます</li>
              </ul>
            </div>

            {/* ボタン */}
            <div className="flex items-center justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate('/papers')}
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
                    論文を作成
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* ヘルプセクション */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">論文執筆システムの特徴</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">AI支援アウトライン</h3>
              <p className="text-sm text-gray-600">
                研究テーマに基づいて、論文の構造を自動提案します
              </p>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">協調執筆</h3>
              <p className="text-sm text-gray-600">
                複数のAIエージェントが連携して、高品質な論文作成をサポートします
              </p>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">品質管理</h3>
              <p className="text-sm text-gray-600">
                論理構造の検証、文献の確認、執筆品質の向上を支援します
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreatePaper;