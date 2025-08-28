import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, X, AlertTriangle, Trash2 } from 'lucide-react';
import { paperService } from '../services/paperService';
import toast from 'react-hot-toast';

const EditPaper: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('draft');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  // 論文データ取得
  const { data: paper, isLoading } = useQuery({
    queryKey: ['paper', id],
    queryFn: () => paperService.getPaper(id!),
    enabled: !!id,
  });

  // データが読み込まれたらフォームに反映
  useEffect(() => {
    if (paper) {
      setTitle(paper.title);
      setDescription(paper.description || '');
      setStatus(paper.status);
    }
  }, [paper]);

  // 論文更新ミューテーション
  const updateMutation = useMutation({
    mutationFn: (data: { title: string; description?: string; status: string }) =>
      paperService.updatePaper(id!, data),
    onSuccess: () => {
      toast.success('論文が更新されました');
      queryClient.invalidateQueries({ queryKey: ['paper', id] });
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      navigate(`/papers/${id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '更新に失敗しました');
    },
  });

  // 論文削除ミューテーション
  const deleteMutation = useMutation({
    mutationFn: () => paperService.deletePaper(id!),
    onSuccess: () => {
      toast.success('論文が削除されました');
      queryClient.invalidateQueries({ queryKey: ['papers'] });
      navigate('/papers');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '削除に失敗しました');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      toast.error('タイトルを入力してください');
      return;
    }

    updateMutation.mutate({
      title: title.trim(),
      description: description.trim() || undefined,
      status,
    });
  };

  const handleCancel = () => {
    navigate(`/papers/${id}`);
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
    setDeleteConfirmText('');
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirmText !== paper?.title) {
      toast.error('論文タイトルが正しく入力されていません');
      return;
    }
    deleteMutation.mutate();
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
    setDeleteConfirmText('');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">論文データを読み込み中...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <p className="text-red-600">論文が見つかりません</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <button
            onClick={handleCancel}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            論文詳細に戻る
          </button>
          <h1 className="text-3xl font-bold text-gray-900">論文を編集</h1>
          <p className="text-gray-600 mt-2">論文のタイトル、説明、ステータスを編集できます。</p>
        </div>

        {/* メインコンテンツ */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* タイトル */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                論文タイトル <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                placeholder="論文のタイトルを入力してください"
                required
              />
            </div>

            {/* 説明 */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                論文の説明・概要
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={6}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                placeholder="論文の概要や説明を入力してください（任意）"
              />
              <p className="mt-2 text-sm text-gray-500">
                論文の研究目的、背景、主要な成果などの概要を記述してください。
              </p>
            </div>

            {/* ステータス */}
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
                ステータス
              </label>
              <select
                id="status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="draft">下書き</option>
                <option value="in_progress">執筆中</option>
                <option value="writing">執筆中</option>
                <option value="review">レビュー中</option>
                <option value="completed">完了</option>
                <option value="published">公開済み</option>
              </select>
            </div>

            {/* アクションボタン */}
            <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={handleCancel}
                className="inline-flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <X className="w-4 h-4 mr-2" />
                キャンセル
              </button>
              <button
                type="submit"
                disabled={updateMutation.isPending || !title.trim()}
                className="inline-flex items-center px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="w-4 h-4 mr-2" />
                {updateMutation.isPending ? '更新中...' : '更新'}
              </button>
            </div>
          </form>
        </div>

        {/* 注意事項 */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <div className="w-5 h-5 text-blue-400">ℹ️</div>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">編集に関する注意事項</h3>
              <div className="mt-2 text-sm text-blue-700">
                <ul className="list-disc list-inside space-y-1">
                  <li>タイトルの変更は論文全体に反映されます</li>
                  <li>セクションの内容を編集するには、論文詳細ページで各セクションを開いて編集してください</li>
                  <li>ステータスの変更は論文の進捗管理に使用されます</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="mt-8 bg-red-50 border border-red-200 rounded-lg">
          <div className="px-6 py-4 border-b border-red-200">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
              <h3 className="text-lg font-medium text-red-800">Danger Zone</h3>
            </div>
            <p className="mt-1 text-sm text-red-600">
              一度削除すると、論文とその全セクションが完全に削除され、復元することはできません。
            </p>
          </div>
          
          <div className="px-6 py-4">
            {!showDeleteConfirm ? (
              <button
                onClick={handleDeleteClick}
                className="inline-flex items-center px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                論文を削除
              </button>
            ) : (
              <div className="space-y-4">
                <div className="bg-red-100 border border-red-300 rounded-lg p-4">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-red-800">本当に削除しますか？</h4>
                      <p className="text-sm text-red-700 mt-1">
                        この操作は取り消すことができません。論文「<strong>{paper?.title}</strong>」とその全セクション、チャット履歴が完全に削除されます。
                      </p>
                    </div>
                  </div>
                </div>
                
                <div>
                  <label htmlFor="deleteConfirm" className="block text-sm font-medium text-red-800 mb-2">
                    削除を確認するために、論文タイトルを正確に入力してください：
                  </label>
                  <input
                    type="text"
                    id="deleteConfirm"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    className="w-full px-3 py-2 border border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder={paper?.title}
                  />
                </div>
                
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleDeleteConfirm}
                    disabled={deleteConfirmText !== paper?.title || deleteMutation.isPending}
                    className="inline-flex items-center px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {deleteMutation.isPending ? '削除中...' : '完全に削除する'}
                  </button>
                  <button
                    onClick={handleDeleteCancel}
                    className="inline-flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <X className="w-4 h-4 mr-2" />
                    キャンセル
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditPaper;