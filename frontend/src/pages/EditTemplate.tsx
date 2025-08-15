import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { api } from '../services/api';
import { Template } from '../types';

const EditTemplate: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [template, setTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    content: '',
    requirements: '',
    status: 'draft' as 'draft' | 'active'
  });

  useEffect(() => {
    if (id) {
      fetchTemplate(id);
    }
  }, [id]);

  const fetchTemplate = async (templateId: string) => {
    try {
      setInitialLoading(true);
      const response = await api.get(`/api/v1/templates/${templateId}`);
      setTemplate(response);
      setFormData({
        name: response.name || '',
        description: response.description || '',
        content: response.content || '',
        requirements: response.requirements || '',
        status: response.status || 'draft'
      });
    } catch (error) {
      console.error('Failed to fetch template:', error);
      alert('テンプレートの読み込みに失敗しました。');
      navigate('/templates');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!template) return;

    try {
      setLoading(true);
      
      const templateData = {
        ...formData
      };
      
      await api.put(`/api/v1/templates/${template.id}`, templateData);
      navigate(`/templates/${template.id}`);
    } catch (error) {
      console.error('Failed to update template:', error);
      alert('テンプレートの更新に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">テンプレートを読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">テンプレートが見つかりません</h2>
        <p className="mt-2 text-gray-600">指定されたテンプレートは存在しないか、削除されています。</p>
        <button
          onClick={() => navigate('/templates')}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          テンプレート一覧に戻る
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(`/templates/${template.id}`)}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            テンプレート詳細に戻る
          </button>
        </div>
      </div>

      {/* フォーム */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">テンプレートを編集</h1>
          <p className="mt-1 text-sm text-gray-600">
            テンプレートの情報を更新します。
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
          {/* 基本情報 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                テンプレート名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                required
              />
            </div>

            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                ステータス
              </label>
              <select
                id="status"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as 'draft' | 'active' })}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                <option value="draft">下書き</option>
                <option value="active">アクティブ</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              説明
            </label>
            <textarea
              id="description"
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="テンプレートの説明を入力してください"
            />
          </div>

          <div>
            <label htmlFor="content" className="block text-sm font-medium text-gray-700">
              テンプレートコンテンツ <span className="text-red-500">*</span>
            </label>
            <textarea
              id="content"
              rows={8}
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm font-mono"
              placeholder="テンプレートの内容を入力してください"
              required
            />
          </div>

          <div>
            <label htmlFor="requirements" className="block text-sm font-medium text-gray-700">
              AI生成要件
            </label>
            <textarea
              id="requirements"
              rows={4}
              value={formData.requirements}
              onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="AI生成時の詳細な要件や指示を入力してください"
            />
          </div>

          {/* 保存ボタン */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => navigate(`/templates/${template.id}`)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  更新中...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  テンプレートを更新
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditTemplate;