import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Edit, Trash2, Play, Clock, User, Tag, X } from 'lucide-react';
import { api } from '../services/api';
import { Template } from '../types';
import { fileService } from '../services/fileService';

const TemplateDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [template, setTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  
  // タグフィルター関連
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  useEffect(() => {
    if (id) {
      fetchTemplate(id);
    }
    loadAvailableTags();
  }, [id]);

  const fetchTemplate = async (templateId: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/templates/${templateId}`);
      setTemplate(response);
    } catch (error) {
      console.error('Failed to fetch template:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableTags = async () => {
    try {
      const allTags = await fileService.getAllUserTags();
      setAvailableTags(allTags);
    } catch (error) {
      console.error('Failed to load available tags:', error);
    }
  };

  // タグ選択・解除
  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  // タグフィルターをクリア
  const clearTagFilter = () => {
    setSelectedTags([]);
  };

  const handleUseTemplate = async () => {
    if (!template) return;

    try {
      setGenerating(true);
      const response = await api.post(`/api/v1/templates/${template.id}/use`, {
        variables: {},
        tags: selectedTags.length > 0 ? selectedTags : undefined
      });
      
      // 成功時はアウトプット一覧画面に遷移し、成功メッセージを表示
      navigate('/outputs', { 
        state: { 
          successMessage: '生成に成功しました',
          newOutputId: response.output_id 
        } 
      });
    } catch (error) {
      console.error('Failed to generate content:', error);
      alert('AI生成に失敗しました。');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteTemplate = async () => {
    if (!template) return;
    
    if (window.confirm('このテンプレートを削除してもよろしいですか？')) {
      try {
        await api.delete(`/api/v1/templates/${template.id}`);
        navigate('/templates');
      } catch (error) {
        console.error('Failed to delete template:', error);
        alert('テンプレートの削除に失敗しました。');
      }
    }
  };

  if (loading) {
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
        <Link
          to="/templates"
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          テンプレート一覧に戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/templates')}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            テンプレート一覧に戻る
          </button>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to={`/templates/${template.id}/edit`}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
          >
            <Edit className="h-4 w-4 mr-2" />
            編集
          </Link>
          <button
            onClick={handleDeleteTemplate}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            削除
          </button>
        </div>
      </div>

      {/* テンプレート詳細 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">{template.name}</h1>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              template.status === 'active' 
                ? 'bg-green-100 text-green-800'
                : template.status === 'draft'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {template.status === 'active' ? 'アクティブ' : 
               template.status === 'draft' ? '下書き' : 'アーカイブ'}
            </span>
          </div>
          {template.description && (
            <p className="mt-2 text-gray-600">{template.description}</p>
          )}
        </div>

        <div className="px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center">
              <Clock className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <div className="text-sm font-medium text-gray-900">最終更新</div>
                <div className="text-sm text-gray-600">
                  {new Date(template.updated_at).toLocaleDateString('ja-JP')}
                </div>
              </div>
            </div>
            <div className="flex items-center">
              <User className="h-5 w-5 text-gray-400 mr-2" />
              <div>
                <div className="text-sm font-medium text-gray-900">使用回数</div>
                <div className="text-sm text-gray-600">{template.usage_count || 0} 回</div>
              </div>
            </div>
          </div>
        </div>

        {/* コンテンツ */}
        <div className="px-6 py-4 border-t border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-3">テンプレートコンテンツ</h3>
          <div className="bg-gray-50 rounded-md p-4">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
              {template.content}
            </pre>
          </div>
        </div>

      </div>

      {/* テンプレート実行 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-8 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-4">テンプレートを実行</h3>
          <p className="text-sm text-gray-600 mb-6">
            このテンプレートを使用してAIコンテンツを生成します。
          </p>
          
          {/* タグフィルターエリア */}
          {availableTags.length > 0 && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <div className="text-left space-y-3">
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">参照文書のタグフィルター:</span>
                  {selectedTags.length > 0 && (
                    <button
                      onClick={clearTagFilter}
                      className="text-xs text-gray-500 hover:text-gray-700 underline"
                    >
                      クリア
                    </button>
                  )}
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {availableTags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => handleTagToggle(tag)}
                      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                        selectedTags.includes(tag)
                          ? 'bg-indigo-100 text-indigo-800 border-indigo-200'
                          : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>

                {selectedTags.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">選択中:</span>
                    <div className="flex flex-wrap gap-1">
                      {selectedTags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                        >
                          {tag}
                          <button
                            onClick={() => handleTagToggle(tag)}
                            className="ml-1 text-indigo-600 hover:text-indigo-800"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <button
            onClick={handleUseTemplate}
            disabled={generating}
            className="inline-flex items-center justify-center py-4 px-8 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                テンプレート実行中...
              </>
            ) : (
              <>
                <Play className="h-5 w-5 mr-3" />
                テンプレートを実行
              </>
            )}
          </button>
        </div>
      </div>

    </div>
  );
};

export default TemplateDetail;