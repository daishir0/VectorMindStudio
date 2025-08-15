import React, { useState, useEffect } from 'react';
import { RefreshCw, Database, FileText, Search, BarChart3, Eye, Tag } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../services/api';

// VectorDBの型定義
interface VectorDocumentInfo {
  id: string;
  filename: string;
  upload_id: string;
  chunk_number: number;
  chunk_size: number;
  document_preview: string;
  distance?: number;
  relevance_score?: number;
  tags?: string[];
}

interface VectorDBStats {
  total_documents: number;
  unique_files: number;
  total_chunks: number;
  average_chunk_size: number;
  collection_name: string;
  user_documents: VectorDocumentInfo[];
}

const VectorDBPage: React.FC = () => {
  const [stats, setStats] = useState<VectorDBStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VectorDocumentInfo[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<VectorDocumentInfo | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const stats = await api.get<VectorDBStats>('/api/v1/vectordb/stats');
      setStats(stats);
    } catch (error: any) {
      console.error('Failed to fetch VectorDB stats:', error);
      
      // エラーの詳細によってメッセージを変える
      if (error.response?.status === 401) {
        toast.error('認証が必要です。再度ログインしてください。');
      } else if (error.response?.status === 404 || error.message.includes('ECONNREFUSED')) {
        toast.error('VectorDBサービスが利用できません。サーバーが起動していることを確認してください。');
      } else {
        // 空の状態として扱う
        setStats({
          total_documents: 0,
          unique_files: 0,
          total_chunks: 0,
          average_chunk_size: 0,
          collection_name: 'vectormind_embeddings',
          user_documents: []
        });
        toast.success('VectorDBは現在空の状態です。ファイルをアップロードしてベクター化を開始してください。');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('検索キーワードを入力してください');
      return;
    }

    try {
      setSearching(true);
      const result = await api.post<VectorDocumentInfo[]>('/api/v1/vectordb/search-preview', {
        query: searchQuery,
        limit: 10,
      });
      
      setSearchResults(result || []);
      toast.success(`${result?.length || 0}件の関連ドキュメントが見つかりました`);
    } catch (error: any) {
      console.error('Search failed:', error);
      if (error.response?.status === 401) {
        toast.error('認証が必要です。再度ログインしてください。');
      } else {
        toast.error('ベクター検索に失敗しました');
      }
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const groupDocumentsByFile = (docs: VectorDocumentInfo[]) => {
    const grouped = docs.reduce((acc, doc) => {
      if (!acc[doc.filename]) {
        acc[doc.filename] = [];
      }
      acc[doc.filename].push(doc);
      return acc;
    }, {} as Record<string, VectorDocumentInfo[]>);

    return Object.entries(grouped).map(([filename, chunks]) => ({
      filename,
      chunks: chunks.sort((a, b) => a.chunk_number - b.chunk_number),
      totalChunks: chunks.length,
      totalSize: chunks.reduce((sum, chunk) => sum + chunk.chunk_size, 0),
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-500">VectorDB情報を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Database className="h-8 w-8 mr-3 text-indigo-600" />
            VectorDB管理
          </h1>
          <p className="mt-1 text-sm text-gray-600">ChromaDBに保存されたベクターデータの詳細情報</p>
        </div>
        <button 
          onClick={fetchStats}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          更新
        </button>
      </div>

      {stats && (
        <>
          {/* 統計カード */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <FileText className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">総ドキュメント数</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.total_documents.toLocaleString()}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Database className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">ユニークファイル数</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.unique_files.toLocaleString()}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BarChart3 className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">総チャンク数</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.total_chunks.toLocaleString()}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BarChart3 className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">平均チャンクサイズ</dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.average_chunk_size} 文字</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 検索セクション */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Search className="h-5 w-5 mr-2" />
              ベクター検索テスト
            </h2>
            <div className="flex space-x-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="検索したいキーワードを入力..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center"
              >
                {searching && <RefreshCw className="h-4 w-4 mr-2 animate-spin" />}
                検索
              </button>
            </div>

            {/* 検索結果 */}
            {searchResults.length > 0 && (
              <div className="mt-6">
                <h3 className="text-md font-medium text-gray-900 mb-3">検索結果</h3>
                <div className="space-y-3">
                  {searchResults.map((result, index) => (
                    <div key={result.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 flex-wrap">
                            <span className="text-sm font-medium text-gray-900">{result.filename}</span>
                            <span className="text-xs text-gray-500">チャンク {result.chunk_number + 1}</span>
                            {result.relevance_score && (
                              <span className={`px-2 py-1 text-xs rounded-full ${getRelevanceColor(result.relevance_score)}`}>
                                関連度: {(result.relevance_score * 100).toFixed(1)}%
                              </span>
                            )}
                            {result.tags && result.tags.length > 0 && (
                              <div className="flex items-center space-x-1">
                                <Tag className="h-3 w-3 text-gray-400" />
                                <div className="flex space-x-1">
                                  {result.tags.map(tag => (
                                    <span
                                      key={tag}
                                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                          <p className="mt-2 text-sm text-gray-600">{result.document_preview}</p>
                        </div>
                        <button
                          onClick={() => setSelectedDoc(result)}
                          className="ml-4 p-1 text-gray-400 hover:text-gray-600"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ファイル別ドキュメント一覧 */}
          {stats.user_documents.length > 0 && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">ファイル別ドキュメント一覧</h2>
                <p className="mt-1 text-sm text-gray-600">コレクション: {stats.collection_name}</p>
              </div>
              <div className="divide-y divide-gray-200">
                {groupDocumentsByFile(stats.user_documents).map(({ filename, chunks, totalChunks, totalSize }) => (
                  <div key={filename} className="p-6">
                    <div className="flex justify-between items-center mb-4">
                      <div>
                        <h3 className="text-md font-medium text-gray-900">{filename}</h3>
                        <p className="text-sm text-gray-500">
                          {totalChunks} チャンク • 総サイズ: {totalSize.toLocaleString()} 文字
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {chunks.map((doc) => (
                        <div key={doc.id} className="border border-gray-200 rounded-md p-3">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-xs font-medium text-gray-600">チャンク {doc.chunk_number + 1}</span>
                            <span className="text-xs text-gray-500">{doc.chunk_size} 文字</span>
                          </div>
                          {doc.tags && doc.tags.length > 0 && (
                            <div className="mb-2">
                              <div className="flex items-center space-x-1">
                                <Tag className="h-3 w-3 text-gray-400" />
                                <div className="flex flex-wrap gap-1">
                                  {doc.tags.map(tag => (
                                    <span
                                      key={tag}
                                      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                          <p className="text-sm text-gray-700 line-clamp-3">{doc.document_preview}</p>
                          <button
                            onClick={() => setSelectedDoc(doc)}
                            className="mt-2 text-xs text-indigo-600 hover:text-indigo-800"
                          >
                            詳細を表示
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stats.user_documents.length === 0 && (
            <div className="bg-white shadow rounded-lg p-6 text-center">
              <Database className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">ベクターデータなし</h3>
              <p className="mt-1 text-sm text-gray-500">まだベクターデータが登録されていません。</p>
              <div className="mt-6">
                <button
                  onClick={() => window.location.href = '/files'}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  ファイルをアップロード
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* ドキュメント詳細モーダル */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
            <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={() => setSelectedDoc(null)}></div>
            <div className="relative w-full max-w-2xl mx-auto bg-white rounded-lg shadow-xl">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">ドキュメント詳細</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {selectedDoc.filename} - チャンク {selectedDoc.chunk_number + 1}
                </p>
              </div>
              <div className="px-6 py-4">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ドキュメントID</label>
                    <p className="mt-1 text-sm text-gray-900 font-mono">{selectedDoc.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ファイルID</label>
                    <p className="mt-1 text-sm text-gray-900 font-mono">{selectedDoc.upload_id}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">チャンク番号</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedDoc.chunk_number + 1}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">サイズ</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedDoc.chunk_size} 文字</p>
                    </div>
                  </div>
                  {(selectedDoc.relevance_score !== undefined) && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">関連度スコア</label>
                        <p className="mt-1 text-sm text-gray-900">{(selectedDoc.relevance_score * 100).toFixed(2)}%</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">距離</label>
                        <p className="mt-1 text-sm text-gray-900">{selectedDoc.distance?.toFixed(4)}</p>
                      </div>
                    </div>
                  )}
                  {selectedDoc.tags && selectedDoc.tags.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700">タグ</label>
                      <div className="mt-1 flex flex-wrap gap-2">
                        {selectedDoc.tags.map(tag => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700">内容プレビュー</label>
                    <div className="mt-1 bg-gray-50 p-4 rounded-md">
                      <pre className="text-sm text-gray-900 whitespace-pre-wrap">{selectedDoc.document_preview}</pre>
                    </div>
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 bg-gray-50 text-right">
                <button
                  onClick={() => setSelectedDoc(null)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  閉じる
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VectorDBPage;