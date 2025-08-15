import React, { useState, useEffect } from 'react';
import { Search, Loader, Tag, X } from 'lucide-react';
import { api } from '../services/api';
import { SearchResult, SearchQuery, FileListResponse, PaginatedResponse } from '../types';
import toast from 'react-hot-toast';

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingTags, setLoadingTags] = useState(false);

  // 利用可能なタグを取得
  const loadAvailableTags = async () => {
    setLoadingTags(true);
    try {
      const response = await api.get<PaginatedResponse<FileListResponse>>('/api/v1/files?limit=1000');
      const allTags = response.items.flatMap(file => file.tags || []);
      const uniqueTags = Array.from(new Set(allTags)).sort();
      setAvailableTags(uniqueTags);
    } catch (error: any) {
      console.error('タグ取得エラー:', error);
    } finally {
      setLoadingTags(false);
    }
  };

  useEffect(() => {
    loadAvailableTags();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error('検索クエリを入力してください。');
      return;
    }

    setLoading(true);
    setResults([]);
    try {
      const searchQuery: SearchQuery = {
        query,
        limit: 10,
        tags: selectedTags.length > 0 ? selectedTags : undefined
      };
      const response = await api.post<SearchResult[]>('/api/v1/search', searchQuery);
      setResults(response);
    } catch (error: any) {
      toast.error(`検索に失敗しました: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const clearSelectedTags = () => {
    setSelectedTags([]);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">セマンティック検索</h1>
        <p className="mt-1 text-sm text-gray-600">
          アップロードしたドキュメント全体から、意味的に関連する情報を検索します。
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex-grow">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="検索キーワードを入力..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? <Loader className="animate-spin h-5 w-5" /> : <Search className="h-5 w-5" />}
              <span className="ml-2">検索</span>
            </button>
          </div>

          {/* タグフィルタセクション */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 flex items-center">
                <Tag className="h-4 w-4 mr-1" />
                タグフィルタ
              </label>
              {selectedTags.length > 0 && (
                <button
                  type="button"
                  onClick={clearSelectedTags}
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
                >
                  <X className="h-3 w-3 mr-1" />
                  すべてクリア
                </button>
              )}
            </div>
            
            {/* 選択されたタグ */}
            {selectedTags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedTags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleTagToggle(tag)}
                      className="ml-1 text-indigo-600 hover:text-indigo-800"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* 利用可能なタグ */}
            {loadingTags ? (
              <div className="text-sm text-gray-500">タグを読み込み中...</div>
            ) : (
              <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                {availableTags
                  .filter(tag => !selectedTags.includes(tag))
                  .map(tag => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => handleTagToggle(tag)}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                    >
                      {tag}
                    </button>
                  ))}
                {availableTags.length === 0 && (
                  <div className="text-sm text-gray-500">利用可能なタグがありません</div>
                )}
              </div>
            )}
          </div>
        </form>
      </div>

      <div className="space-y-4">
        {loading && (
            <div className="text-center py-12">
                <Loader className="mx-auto h-12 w-12 text-indigo-600 animate-spin" />
                <p className="mt-2 text-gray-600">検索中...</p>
            </div>
        )}
        {!loading && results.length > 0 && (
          results.map((result) => (
            <div key={result.id} className="bg-white shadow rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{result.document}</p>
                  {/* タグ表示 */}
                  {result.tags && result.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {result.tags.map(tag => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-xs font-semibold text-indigo-600 bg-indigo-100 px-2 py-1 rounded-full ml-2">
                  関連度: {result.relevance_score.toFixed(2)}
                </span>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                <span>ソース: {result.filename || result.metadata.filename} (Chunk #{result.metadata.chunk_number})</span>
              </div>
            </div>
          ))
        )}
        {!loading && results.length === 0 && (
            <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500">検索結果はありません。</p>
            </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
