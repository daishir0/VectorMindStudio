import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, FileText, Clock, Edit3 } from 'lucide-react';
import { paperService, PaperSummary } from '../services/paperService';

const Papers: React.FC = () => {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['papers', page, statusFilter],
    queryFn: () => paperService.getPapers(page, 20, statusFilter || undefined),
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { label: '下書き', color: 'bg-gray-100 text-gray-800' },
      in_progress: { label: '執筆中', color: 'bg-yellow-100 text-yellow-800' },
      completed: { label: '完了', color: 'bg-green-100 text-green-800' },
      published: { label: '公開済み', color: 'bg-blue-100 text-blue-800' },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
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

  if (error) {
    console.error('Papers API Error:', error);
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <p className="text-red-600">エラーが発生しました</p>
              <p className="mt-2 text-gray-600">論文データの読み込みに失敗しました</p>
              {process.env.NODE_ENV === 'development' && (
                <p className="mt-2 text-sm text-gray-500">
                  詳細: {error instanceof Error ? error.message : String(error)}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">論文執筆</h1>
              <p className="mt-2 text-gray-600">AI支援による学術論文の執筆・管理システム</p>
            </div>
            <Link
              to="/papers/create"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5 mr-2" />
              新しい論文を作成
            </Link>
          </div>
        </div>

        {/* フィルター */}
        <div className="mb-6">
          <div className="flex items-center space-x-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">すべてのステータス</option>
              <option value="draft">下書き</option>
              <option value="in_progress">執筆中</option>
              <option value="completed">完了</option>
              <option value="published">公開済み</option>
            </select>
          </div>
        </div>

        {/* 論文リスト */}
        {data?.items.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">論文がありません</h3>
            <p className="text-gray-600 mb-6">最初の論文を作成して、AI支援による論文執筆を始めましょう</p>
            <Link
              to="/papers/create"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5 mr-2" />
              新しい論文を作成
            </Link>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((paper: PaperSummary) => (
              <div
                key={paper.id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                        {paper.title}
                      </h3>
                      {paper.description && (
                        <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                          {paper.description}
                        </p>
                      )}
                    </div>
                    <Link
                      to={`/papers/${paper.id}/edit`}
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <Edit3 className="w-4 h-4" />
                    </Link>
                  </div>

                  <div className="flex items-center justify-between mb-4">
                    {getStatusBadge(paper.status)}
                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="w-4 h-4 mr-1" />
                      {formatDate(paper.updated_at)}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{paper.section_count}</div>
                      <div className="text-xs text-gray-500">セクション</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{paper.total_words.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">単語数</div>
                    </div>
                  </div>

                  <Link
                    to={`/papers/${paper.id}`}
                    className="block w-full text-center bg-gray-50 text-gray-700 py-2 rounded-lg hover:bg-gray-100 transition-colors font-medium"
                  >
                    詳細を見る
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ページネーション */}
        {data && data.has_more && (
          <div className="mt-8 flex justify-center">
            <button
              onClick={() => setPage(page + 1)}
              className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              さらに読み込む
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Papers;