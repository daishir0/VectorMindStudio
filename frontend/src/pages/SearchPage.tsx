import React, { useState } from 'react';
import { Search, Loader } from 'lucide-react';
import { api } from '../services/api';
import { SearchResult } from '../types';
import toast from 'react-hot-toast';

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error('検索クエリを入力してください。');
      return;
    }

    setLoading(true);
    setResults([]);
    try {
      const response = await api.post<SearchResult[]>('/api/v1/search', { query });
      setResults(response);
    } catch (error: any) {
      toast.error(`検索に失敗しました: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
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
        <form onSubmit={handleSearch} className="flex items-center space-x-2">
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
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{result.document}</p>
                <span className="text-xs font-semibold text-indigo-600 bg-indigo-100 px-2 py-1 rounded-full">
                  関連度: {result.relevance_score.toFixed(2)}
                </span>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                <span>ソース: {result.metadata.filename} (Chunk #{result.metadata.chunk_number})</span>
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
