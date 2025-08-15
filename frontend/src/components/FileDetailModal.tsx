import React, { useState, useEffect } from 'react';
import { X, Eye, Edit3, Trash2, Save, Download, Tag, Plus } from 'lucide-react';
import { fileService } from '../services/fileService';
import { FileListResponse } from '../types';
import toast from 'react-hot-toast';

interface FileDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileId: string | null;
  onFileDeleted: () => void;
  onFileUpdated?: () => void;
}

const FileDetailModal: React.FC<FileDetailModalProps> = ({
  isOpen,
  onClose,
  fileId,
  onFileDeleted,
  onFileUpdated
}) => {
  const [file, setFile] = useState<FileListResponse | null>(null);
  const [content, setContent] = useState<string>('');
  const [editedContent, setEditedContent] = useState<string>('');
  const [mode, setMode] = useState<'view' | 'edit'>('view');
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  
  // タグ関連の状態
  const [tags, setTags] = useState<string[]>([]);
  const [editingTags, setEditingTags] = useState(false);
  const [newTag, setNewTag] = useState('');

  useEffect(() => {
    if (isOpen && fileId) {
      fetchFileDetails();
      fetchFileContent();
    } else {
      // Reset state when modal is closed
      setFile(null);
      setContent('');
      setEditedContent('');
      setMode('view');
      setTags([]);
      setEditingTags(false);
      setNewTag('');
    }
  }, [isOpen, fileId]);

  const fetchFileDetails = async () => {
    if (!fileId) return;
    
    try {
      setLoading(true);
      const response = await fileService.getFileDetails(fileId);
      setFile(response);
      setTags(response.tags || []);
    } catch (error) {
      toast.error('ファイル情報の取得に失敗しました。');
      console.error('Failed to fetch file details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFileContent = async () => {
    if (!fileId) return;
    
    try {
      setContentLoading(true);
      const response = await fileService.getFileContent(fileId);
      setContent(response.content);
      setEditedContent(response.content);
    } catch (error: any) {
      if (error.response?.status === 404) {
        toast.error('ファイルの内容が見つかりません。処理が完了していない可能性があります。');
      } else {
        toast.error('ファイル内容の取得に失敗しました。');
      }
      console.error('Failed to fetch file content:', error);
    } finally {
      setContentLoading(false);
    }
  };

  const handleSave = async () => {
    // Note: This would require a new API endpoint to update file content
    // For now, we'll just show a message
    toast.error('ファイル編集機能は現在実装中です。');
  };

  const handleDelete = async () => {
    if (!fileId || !file) return;
    
    const confirmed = window.confirm(`ファイル "${file.filename}" を削除しますか？この操作は取り消せません。`);
    
    if (!confirmed) return;
    
    try {
      setLoading(true);
      await fileService.deleteFile(fileId);
      toast.success('ファイルが削除されました。');
      onFileDeleted();
      onClose();
    } catch (error) {
      toast.error('ファイルの削除に失敗しました。');
      console.error('Failed to delete file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!content || !file) return;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.filename.replace(/\.[^/.]+$/, '') + '.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // タグ関連のハンドラー
  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      const updatedTags = [...tags, newTag.trim()];
      setTags(updatedTags);
      setNewTag('');
      updateFileTags(updatedTags);
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const updatedTags = tags.filter(tag => tag !== tagToRemove);
    setTags(updatedTags);
    updateFileTags(updatedTags);
  };

  const updateFileTags = async (updatedTags: string[]) => {
    if (!fileId) return;
    
    try {
      await fileService.updateFileTags(fileId, updatedTags);
      toast.success('タグが更新されました。');
      if (onFileUpdated) {
        onFileUpdated();
      }
    } catch (error) {
      toast.error('タグの更新に失敗しました。');
      console.error('Failed to update tags:', error);
      // タグをロールバック
      if (file) {
        setTags(file.tags || []);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTag();
    }
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
                {file?.filename || 'ファイル詳細'}
              </h3>
              {file && (
                <div className="mt-1 space-y-1">
                  <p className="text-sm text-gray-500">
                    作成日: {new Date(file.created_at).toLocaleString('ja-JP')}
                  </p>
                  {/* タグ表示 */}
                  <div className="flex items-center flex-wrap gap-2">
                    {tags.length > 0 && (
                      <>
                        <Tag className="h-4 w-4 text-gray-400" />
                        {tags.map((tag, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-800 bg-indigo-100 rounded-full"
                          >
                            {tag}
                            <button
                              onClick={() => handleRemoveTag(tag)}
                              className="ml-1 text-indigo-600 hover:text-indigo-800"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </>
                    )}
                    {/* タグ追加フィールド */}
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={newTag}
                        onChange={(e) => setNewTag(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="新しいタグ"
                        className="px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                      <button
                        onClick={handleAddTag}
                        disabled={!newTag.trim()}
                        className="p-1 text-indigo-600 hover:text-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Plus className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>
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
                      ファイル内容を編集
                    </label>
                    <textarea
                      id="content-editor"
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="w-full h-96 px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                      placeholder="ファイル内容を入力してください..."
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">ファイル内容を取得できませんでした。</p>
                <button
                  onClick={fetchFileContent}
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

export default FileDetailModal;