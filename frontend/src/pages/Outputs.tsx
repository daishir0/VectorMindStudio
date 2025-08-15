import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { outputService } from '../services/outputService';
import { OutputDetailResponse, PaginatedResponse } from '../types';
import toast from 'react-hot-toast';
import OutputDetailModal from '../components/OutputDetailModal';

const OutputsPage: React.FC = () => {
  const location = useLocation();
  const [outputsResponse, setOutputsResponse] = useState<PaginatedResponse<OutputDetailResponse> | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedOutputId, setSelectedOutputId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchOutputs();
    
    // 成功メッセージがある場合は表示
    if (location.state?.successMessage) {
      toast.success(location.state.successMessage);
      
      // 状態をクリアして、ブラウザの戻るボタンで同じメッセージが再表示されるのを防ぐ
      window.history.replaceState(null, '', location.pathname);
    }
  }, [location]);

  const fetchOutputs = async (page = 1) => {
    try {
      setLoading(true);
      const response = await outputService.getOutputs(page);
      setOutputsResponse(response);
    } catch (error) {
      toast.error('生成済みアウトプットの取得に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  const handleOutputClick = (outputId: string) => {
    setSelectedOutputId(outputId);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedOutputId(null);
  };

  const handleOutputDeleted = () => {
    // Refresh the outputs list after deletion
    fetchOutputs(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">生成済みアウトプット</h1>
          <p className="mt-1 text-sm text-gray-600">生成されたアウトプットの一覧です。</p>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={() => fetchOutputs(1)}
            disabled={loading}
            className="inline-flex items-center p-2 border border-transparent rounded-full shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">名前</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">AIモデル</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">生成日時</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={3} className="text-center py-12">読み込み中...</td></tr>
            ) : outputsResponse && outputsResponse.items.length > 0 ? (
              outputsResponse.items.map((output) => (
                <tr 
                  key={output.id} 
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleOutputClick(output.id)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{output.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{output.ai_model}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(output.created_at).toLocaleString('ja-JP')}</td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={3} className="text-center py-12">アウトプットが見つかりません。</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <OutputDetailModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        outputId={selectedOutputId}
        onOutputDeleted={handleOutputDeleted}
      />
    </div>
  );
};

export default OutputsPage;
