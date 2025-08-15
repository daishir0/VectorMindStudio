import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, RefreshCw, Search, Tag, X, Trash2, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { fileService } from '../services/fileService';
import { FileListResponse, PaginatedResponse } from '../types';
import toast from 'react-hot-toast';
import FileDetailModal from '../components/FileDetailModal';

const FilesPage: React.FC = () => {
  const [fileResponse, setFileResponse] = useState<PaginatedResponse<FileListResponse> | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  
  // 検索・フィルター関連の状態
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  
  // ソート関連の状態
  const [sortField, setSortField] = useState<'filename' | 'status' | 'created_at' | 'updated_at' | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // 一括選択関連の状態
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkTags, setBulkTags] = useState<string[]>([]);
  const [newBulkTag, setNewBulkTag] = useState('');

  const fetchFiles = async (page = 1) => {
    try {
      setLoading(true);
      console.log('Fetching files with params:', {
        page,
        searchQuery: searchQuery || undefined,
        selectedTags: selectedTags.length > 0 ? selectedTags : undefined,
        sortField: sortField || undefined,
        sortOrder
      });
      
      const response = await fileService.getFiles(
        page, 
        20, 
        searchQuery || undefined, 
        selectedTags.length > 0 ? selectedTags : undefined,
        sortField || undefined,
        sortOrder
      );
      
      console.log('Files API response:', response);
      setFileResponse(response);
      
    } catch (error) {
      toast.error('ファイルの取得に失敗しました。');
      console.error('Failed to fetch files:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllUserTags = async () => {
    try {
      const allTags = await fileService.getAllUserTags();
      setAvailableTags(allTags);
    } catch (error) {
      console.error('Failed to fetch all user tags:', error);
      // エラーが発生した場合は現在表示中のファイルからタグを収集（フォールバック）
      if (fileResponse) {
        const fallbackTags = new Set<string>();
        fileResponse.items.forEach(file => {
          file.tags?.forEach(tag => fallbackTags.add(tag));
        });
        setAvailableTags(Array.from(fallbackTags).sort());
      }
    }
  };

  useEffect(() => {
    fetchAllUserTags(); // 初回読み込み時に全ユーザータグを取得
  }, []);

  useEffect(() => {
    setCurrentPage(1);
    fetchFiles(1);
  }, [searchQuery, selectedTags]);

  useEffect(() => {
    fetchFiles(currentPage);
  }, [currentPage]);

  useEffect(() => {
    fetchFiles(currentPage);
  }, [sortField, sortOrder]);

  const handleFileClick = (fileId: string) => {
    setSelectedFileId(fileId);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedFileId(null);
  };

  const handleFileDeleted = () => {
    // Refresh the files list and tags after deletion
    fetchFiles(currentPage);
    fetchAllUserTags();
  };

  const handleFileUpdated = () => {
    // Refresh the files list and tags after update
    fetchFiles(currentPage);
    fetchAllUserTags();
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedTags([]);
  };

  // 一括選択関連のハンドラー
  const handleBulkModeToggle = () => {
    setBulkMode(!bulkMode);
    setSelectedFiles([]);
  };

  const handleFileSelect = (fileId: string, isSelected: boolean) => {
    if (isSelected) {
      setSelectedFiles(prev => [...prev, fileId]);
    } else {
      setSelectedFiles(prev => prev.filter(id => id !== fileId));
    }
  };

  const handleSelectAll = () => {
    if (fileResponse && fileResponse.items.length > 0) {
      const allFileIds = fileResponse.items.map(file => file.id);
      setSelectedFiles(selectedFiles.length === allFileIds.length ? [] : allFileIds);
    }
  };

  const handleBulkTagAdd = () => {
    if (newBulkTag.trim() && !bulkTags.includes(newBulkTag.trim())) {
      setBulkTags(prev => [...prev, newBulkTag.trim()]);
      setNewBulkTag('');
    }
  };

  const handleBulkTagRemove = (tagToRemove: string) => {
    setBulkTags(prev => prev.filter(tag => tag !== tagToRemove));
  };

  const handleApplyBulkTags = async () => {
    if (selectedFiles.length === 0 || bulkTags.length === 0) {
      toast.error('ファイルとタグを選択してください。');
      return;
    }

    try {
      setLoading(true);
      await fileService.bulkUpdateTags(selectedFiles, bulkTags);
      toast.success(`${selectedFiles.length}件のファイルにタグを適用しました。`);
      setSelectedFiles([]);
      setBulkTags([]);
      setBulkMode(false);
      fetchFiles(currentPage);
      fetchAllUserTags(); // タグリストを更新
    } catch (error) {
      toast.error('一括タグ付けに失敗しました。');
      console.error('Failed to apply bulk tags:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = (fileId: string) => {
    if (!bulkMode) {
      handleFileClick(fileId);
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const getTotalPages = (): number => {
    if (!fileResponse) return 1;
    return Math.ceil(fileResponse.total / 20);
  };

  const getPageNumbers = (): number[] => {
    const totalPages = getTotalPages();
    const pages: number[] = [];
    const maxVisible = 5;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const start = Math.max(1, currentPage - 2);
      const end = Math.min(totalPages, start + maxVisible - 1);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
    }
    
    return pages;
  };

  const handleSort = (field: 'filename' | 'status' | 'created_at' | 'updated_at') => {
    if (sortField === field) {
      // 同じフィールドをクリックした場合は順序を反転
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // 新しいフィールドをクリックした場合は昇順に設定
      setSortField(field);
      setSortOrder('asc');
    }
    setCurrentPage(1); // ソート時はページを1に戻す
  };

  const getSortIcon = (field: 'filename' | 'status' | 'created_at' | 'updated_at') => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 text-gray-400" />;
    }
    return sortOrder === 'asc' 
      ? <ArrowUp className="h-4 w-4 text-indigo-600" />
      : <ArrowDown className="h-4 w-4 text-indigo-600" />;
  };


  const handleDeleteAllFiles = async () => {
    if (!fileResponse?.items.length) {
      toast.error('削除するファイルがありません。');
      return;
    }

    const confirmDelete = window.confirm(
      `すべてのファイル（${fileResponse.items.length}件）を削除しますか？この操作は元に戻せません。`
    );

    if (!confirmDelete) return;

    try {
      setLoading(true);
      const fileIds = fileResponse.items.map(file => file.id);
      
      // Use bulk delete API
      const result = await fileService.bulkDeleteFiles(fileIds);

      if (result.failed_count === 0) {
        toast.success(`すべてのファイル（${result.deleted_count}件）を削除しました。`);
      } else {
        toast.success(`${result.deleted_count}件のファイルを削除しました。${result.failed_count}件の削除に失敗しました。`);
        if (result.errors && result.errors.length > 0) {
          console.error('Delete errors:', result.errors);
        }
      }
      
      // Refresh file list and tags
      fetchFiles(currentPage);
      fetchAllUserTags();
    } catch (error) {
      toast.error('ファイルの一括削除に失敗しました。');
      console.error('Failed to delete all files:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">完了</span>;
      case 'processing':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">処理中</span>;
      case 'failed':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">失敗</span>;
      default:
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ファイル管理</h1>
          <p className="mt-1 text-sm text-gray-600">アップロードしたファイルの一覧です。</p>
        </div>
        <div className="flex items-center space-x-2">
            <button 
                onClick={handleBulkModeToggle}
                className={`inline-flex items-center px-3 py-2 border text-sm font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  bulkMode 
                    ? 'border-transparent text-white bg-purple-600 hover:bg-purple-700 focus:ring-purple-500'
                    : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-indigo-500'
                }`}
            >
                {bulkMode ? '一括モード終了' : '一括タグ付け'}
            </button>
            <button 
                onClick={() => fetchFiles(1)}
                disabled={loading}
                className="inline-flex items-center p-2 border border-transparent rounded-full shadow-sm text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
            >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
                onClick={handleDeleteAllFiles}
                disabled={loading || !fileResponse?.items.length}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <Trash2 className="h-4 w-4 mr-2" />
                すべて削除
            </button>
            <Link
                to="/upload"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
                <Plus className="h-4 w-4 mr-2" />
                ファイルをアップロード
            </Link>
        </div>
      </div>

      {/* 検索・フィルター */}
      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <div className="space-y-4">
          {/* 検索バー */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="ファイル名で検索..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>

          {/* タグフィルター */}
          {availableTags.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Tag className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">タグでフィルター:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {availableTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => handleTagToggle(tag)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      selectedTags.includes(tag)
                        ? 'bg-indigo-100 text-indigo-800 border-indigo-200'
                        : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* アクティブフィルター表示とクリアボタン */}
          {(searchQuery || selectedTags.length > 0) && (
            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">フィルター中:</span>
                {searchQuery && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    検索: {searchQuery}
                  </span>
                )}
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
              <button
                onClick={clearFilters}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                フィルターをクリア
              </button>
            </div>
          )}

          {/* 一括タグ付けセクション */}
          {bulkMode && (
            <div className="pt-4 border-t border-gray-200">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-purple-700">一括タグ付けモード</span>
                    <span className="text-xs text-gray-500">
                      {selectedFiles.length}件選択中
                    </span>
                  </div>
                  <button
                    onClick={handleSelectAll}
                    className="text-xs text-purple-600 hover:text-purple-800 underline"
                  >
                    {selectedFiles.length === fileResponse?.items.length ? '全て解除' : '全て選択'}
                  </button>
                </div>

                {/* タグ入力 */}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700">適用するタグ:</span>
                  <div className="flex flex-wrap items-center gap-2">
                    {bulkTags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 text-xs font-medium text-purple-800 bg-purple-100 rounded-full"
                      >
                        {tag}
                        <button
                          onClick={() => handleBulkTagRemove(tag)}
                          className="ml-1 text-purple-600 hover:text-purple-800"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        value={newBulkTag}
                        onChange={(e) => setNewBulkTag(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleBulkTagAdd();
                          }
                        }}
                        placeholder="新しいタグ"
                        className="px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500"
                      />
                      <button
                        onClick={handleBulkTagAdd}
                        disabled={!newBulkTag.trim()}
                        className="p-1 text-purple-600 hover:text-purple-800 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Plus className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* 実行ボタン */}
                <div className="flex justify-end">
                  <button
                    onClick={handleApplyBulkTags}
                    disabled={selectedFiles.length === 0 || bulkTags.length === 0 || loading}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    タグを適用 ({selectedFiles.length}件)
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {bulkMode && (
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={fileResponse?.items.length > 0 && selectedFiles.length === fileResponse.items.length}
                      onChange={handleSelectAll}
                      className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                    />
                  </th>
                )}
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('filename')}
                    className="flex items-center space-x-1 hover:text-gray-700 focus:outline-none"
                  >
                    <span>ファイル名</span>
                    {getSortIcon('filename')}
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">タグ</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('status')}
                    className="flex items-center space-x-1 hover:text-gray-700 focus:outline-none"
                  >
                    <span>ステータス</span>
                    {getSortIcon('status')}
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('created_at')}
                    className="flex items-center space-x-1 hover:text-gray-700 focus:outline-none"
                  >
                    <span>作成日時</span>
                    {getSortIcon('created_at')}
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('updated_at')}
                    className="flex items-center space-x-1 hover:text-gray-700 focus:outline-none"
                  >
                    <span>最終更新日時</span>
                    {getSortIcon('updated_at')}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={bulkMode ? 6 : 5} className="text-center py-12">読み込み中...</td></tr>
              ) : fileResponse && fileResponse.items.length > 0 ? (
                fileResponse.items.map((file) => (
                  <tr 
                    key={file.id} 
                    className={`hover:bg-gray-50 ${!bulkMode ? 'cursor-pointer' : ''}`}
                    onClick={() => handleRowClick(file.id)}
                  >
                    {bulkMode && (
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedFiles.includes(file.id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleFileSelect(file.id, e.target.checked);
                          }}
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{file.filename}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex flex-wrap gap-1">
                        {file.tags && file.tags.length > 0 ? (
                          file.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-800 bg-indigo-100 rounded-full"
                            >
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{getStatusBadge(file.status)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(file.created_at).toLocaleString('ja-JP')}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(file.updated_at).toLocaleString('ja-JP')}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={bulkMode ? 6 : 5} className="text-center py-12">ファイルが見つかりません。</td></tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* ページング */}
        {fileResponse && fileResponse.total > 20 && (
          <div className="flex items-center justify-between px-6 py-3 bg-white border-t border-gray-200">
            <div className="flex items-center text-sm text-gray-700">
              <span>
                {((currentPage - 1) * 20) + 1}〜{Math.min(currentPage * 20, fileResponse.total)}件を表示 
                （全{fileResponse.total}件中）
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* 前へボタン */}
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-2 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-l-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              
              {/* ページ番号 */}
              {getPageNumbers().map((pageNum) => (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`relative inline-flex items-center px-4 py-2 text-sm font-medium border ${
                    pageNum === currentPage
                      ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              ))}
              
              {/* 次へボタン */}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === getTotalPages()}
                className="relative inline-flex items-center px-2 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-r-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      <FileDetailModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        fileId={selectedFileId}
        onFileDeleted={handleFileDeleted}
        onFileUpdated={handleFileUpdated}
      />
    </div>
  );
};

export default FilesPage;
