import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File as FileIcon, X } from 'lucide-react';
import { fileService } from '../services/fileService';
import toast from 'react-hot-toast';

const UploadPage: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [currentFileIndex, setCurrentFileIndex] = useState<number>(0);
  const [uploadedFiles, setUploadedFiles] = useState<number[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prevFiles => [...prevFiles, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 50 * 1024 * 1024, // 50MB
    onDropRejected: (fileRejections) => {
        fileRejections.forEach(rejection => {
            rejection.errors.forEach(error => {
                if (error.code === 'file-too-large') {
                    toast.error(`ファイルサイズが大きすぎます: ${rejection.file.name} (50MB上限)`);
                } else {
                    toast.error(`ファイルエラー: ${rejection.file.name} - ${error.message}`);
                }
            });
        });
    }
  });

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('アップロードするファイルを選択してください。');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setCurrentFileIndex(0);
    setUploadedFiles([]);

    let successCount = 0;
    let failureCount = 0;

    for (let i = 0; i < files.length; i++) {
      setCurrentFileIndex(i);
      const file = files[i];
      
      try {
        const response = await fileService.uploadFile(file, (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        });
        
        setUploadedFiles(prev => [...prev, i]);
        successCount++;
        toast.success(`'${response.filename}' のアップロードが完了しました。`);
      } catch (error: any) {
        failureCount++;
        toast.error(`'${file.name}' のアップロードに失敗しました: ${error.response?.data?.detail || error.message}`);
      }
      
      // 次のファイルのためにプログレスをリセット
      setUploadProgress(0);
    }

    // 全体の結果を表示
    if (successCount > 0 && failureCount === 0) {
      toast.success(`${successCount}個のファイルのアップロードがすべて完了しました。`);
    } else if (successCount > 0 && failureCount > 0) {
      toast.success(`${successCount}個のファイルが成功、${failureCount}個のファイルが失敗しました。`);
    }

    // アップロードが完了したファイルをリストから削除（後ろから削除して影響を最小化）
    const sortedUploadedIndexes = [...uploadedFiles].sort((a, b) => b - a);
    setFiles(prevFiles => {
      const newFiles = [...prevFiles];
      sortedUploadedIndexes.forEach(index => {
        newFiles.splice(index, 1);
      });
      return newFiles;
    });
    
    setUploading(false);
    setCurrentFileIndex(0);
    setUploadedFiles([]);
  };

  const removeFile = (fileToRemove: File) => {
    setFiles(files.filter(file => file !== fileToRemove));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ファイルアップロード</h1>
        <p className="mt-1 text-sm text-gray-600">
          知識ベースとなるファイルをアップロードします。
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div {...getRootProps()} className={`p-8 border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors ${isDragActive ? 'border-indigo-600 bg-indigo-50' : 'border-gray-300 hover:border-indigo-500'}`}>
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            {isDragActive ? 'ここにファイルをドロップ' : 'ファイルをドラッグ＆ドロップするか、クリックして選択'}
          </p>
          <p className="mt-1 text-xs text-gray-500">最大ファイルサイズ: 50MB</p>
        </div>

        {files.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-medium text-gray-900">選択されたファイル:</h3>
            <ul className="mt-2 border border-gray-200 rounded-md divide-y divide-gray-200">
              {files.map((file, i) => {
                const isCurrentlyUploading = uploading && i === currentFileIndex;
                const isUploaded = uploadedFiles.includes(i);
                return (
                  <li 
                    key={i} 
                    className={`pl-3 pr-4 py-3 flex items-center justify-between text-sm ${
                      isCurrentlyUploading ? 'bg-indigo-50 border-indigo-200' : 
                      isUploaded ? 'bg-green-50' : ''
                    }`}
                  >
                    <div className="w-0 flex-1 flex items-center">
                      <FileIcon className={`flex-shrink-0 h-5 w-5 ${
                        isCurrentlyUploading ? 'text-indigo-600' :
                        isUploaded ? 'text-green-600' : 'text-gray-400'
                      }`} />
                      <span className={`ml-2 flex-1 w-0 truncate ${
                        isCurrentlyUploading ? 'text-indigo-900 font-medium' :
                        isUploaded ? 'text-green-900' : 'text-gray-900'
                      }`}>
                        {file.name}
                      </span>
                      {isCurrentlyUploading && (
                        <span className="ml-2 text-xs text-indigo-600 font-medium">アップロード中</span>
                      )}
                      {isUploaded && (
                        <span className="ml-2 text-xs text-green-600 font-medium">完了</span>
                      )}
                    </div>
                    <div className="ml-4 flex-shrink-0 flex items-center">
                      <span className='text-gray-500 mr-4'>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                      {!uploading && (
                        <button onClick={() => removeFile(file)} className="font-medium text-red-600 hover:text-red-500">
                          <X className='h-5 w-5' />
                        </button>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {uploading && (
            <div className="mt-4">
                <div className="flex justify-between">
                    <span className="text-sm font-medium text-gray-700">
                        アップロード中: {files[currentFileIndex]?.name} ({currentFileIndex + 1}/{files.length})
                    </span>
                    <span className="text-sm font-medium text-gray-700">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1">
                    <div className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                    全体の進行状況: {currentFileIndex}/{files.length} ファイル完了
                </div>
            </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleUpload}
            disabled={uploading || files.length === 0}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? 'アップロード中...' : 'アップロード開始'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
