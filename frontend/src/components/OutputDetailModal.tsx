import React, { useState, useEffect } from 'react';
import { X, Eye, Edit3, Trash2, Save, Download } from 'lucide-react';
import { outputService } from '../services/outputService';
import { OutputDetailResponse } from '../types';
import toast from 'react-hot-toast';

interface OutputDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  outputId: string | null;
  onOutputDeleted: () => void;
}

const OutputDetailModal: React.FC<OutputDetailModalProps> = ({
  isOpen,
  onClose,
  outputId,
  onOutputDeleted
}) => {
  const [output, setOutput] = useState<OutputDetailResponse | null>(null);
  const [content, setContent] = useState<string>('');
  const [editedContent, setEditedContent] = useState<string>('');
  const [mode, setMode] = useState<'view' | 'edit'>('view');
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);

  useEffect(() => {
    if (isOpen && outputId) {
      fetchOutputDetails();
    } else {
      // Reset state when modal is closed
      setOutput(null);
      setContent('');
      setEditedContent('');
      setMode('view');
    }
  }, [isOpen, outputId]);

  // 詳細取得後にコンテンツを取得
  useEffect(() => {
    if (output && !content) {
      fetchOutputContent();
    }
  }, [output]);

  const fetchOutputDetails = async () => {
    if (!outputId) return;
    
    try {
      setLoading(true);
      const response = await outputService.getOutputDetails(outputId);
      setOutput(response);
      
      // 詳細取得後、generated_contentをcontentとして設定
      if (response.generated_content) {
        setContent(response.generated_content);
        setEditedContent(response.generated_content);
      }
      
    } catch (error) {
      toast.error('アウトプット情報の取得に失敗しました。');
      console.error('Failed to fetch output details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOutputContent = async () => {
    if (!outputId) return;
    
    try {
      setContentLoading(true);
      
      // まずコンテンツAPIを試行
      const response = await outputService.getOutputContent(outputId);
      setContent(response.content);
      setEditedContent(response.content);
      
    } catch (error: any) {
      // コンテンツAPIが失敗した場合、outputの詳細から取得済みのgenerated_contentを使用
      if (output?.generated_content) {
        setContent(output.generated_content);
        setEditedContent(output.generated_content);
      } else {
        console.error('Failed to fetch output content:', error);
      }
    } finally {
      setContentLoading(false);
    }
  };

  const handleSave = async () => {
    // Note: This would require a new API endpoint to update output content
    // For now, we'll just show a message
    toast.error('アウトプット編集機能は現在実装中です。');
  };

  const handleDelete = async () => {
    if (!outputId || !output) return;
    
    const confirmed = window.confirm(`アウトプット "${output.id}" を削除しますか？この操作は取り消せません。`);
    
    if (!confirmed) return;
    
    try {
      setLoading(true);
      await outputService.deleteOutput(outputId);
      toast.success('アウトプットが削除されました。');
      onOutputDeleted();
      onClose();
    } catch (error) {
      toast.error('アウトプットの削除に失敗しました。');
      console.error('Failed to delete output:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!content || !output) return;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `output_${output.id}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        
        <div className="relative w-full max-w-4xl mx-auto bg-white rounded-lg shadow-xl transform transition-all">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                {output ? `アウトプット詳細 - ${output.name}` : 'アウトプット詳細'}
              </h3>
              {output && (
                <p className="mt-1 text-sm text-gray-500">
                  作成日: {new Date(output.created_at).toLocaleString('ja-JP')}
                </p>
              )}
            </div>
            <div className="flex items-center space-x-2">
              {mode === 'edit' ? (
                <>
                  <button
                    onClick={handleSave}
                    disabled={loading}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                  >
                    <Save className="h-4 w-4 mr-1" />
                    保存
                  </button>
                  <button
                    onClick={() => {
                      setMode('view');
                      setEditedContent(content);
                    }}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    キャンセル
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setMode('view')}
                    className={`inline-flex items-center px-3 py-2 text-sm leading-4 font-medium rounded-md ${
                      mode === 'view'
                        ? 'text-indigo-700 bg-indigo-100'
                        : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                    } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    閲覧
                  </button>
                  <button
                    onClick={() => setMode('edit')}
                    disabled={contentLoading || !content}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    <Edit3 className="h-4 w-4 mr-1" />
                    編集
                  </button>
                  <button
                    onClick={handleDownload}
                    disabled={contentLoading || !content}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    <Download className="h-4 w-4 mr-1" />
                    ダウンロード
                  </button>
                  <button
                    onClick={handleDelete}
                    disabled={loading}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    削除
                  </button>
                </>
              )}
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {contentLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-500">コンテンツを読み込み中...</p>
                </div>
              </div>
            ) : content ? (
              <div className="space-y-4">
                {mode === 'view' ? (
                  <div>
                    <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm text-gray-800 overflow-auto max-h-96 text-left">
                      {content}
                    </pre>
                  </div>
                ) : (
                  <div>
                    <label htmlFor="content-editor" className="block text-sm font-medium text-gray-700 mb-2">
                      アウトプット内容を編集
                    </label>
                    <textarea
                      id="content-editor"
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full h-96 px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                      placeholder="アウトプット内容を入力してください..."
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">アウトプット内容を取得できませんでした。</p>
                <button
                  onClick={fetchOutputContent}
                  className="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  再読み込み
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OutputDetailModal;