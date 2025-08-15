import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Search } from 'lucide-react';

const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          {/* 404アイコン */}
          <div className="flex justify-center">
            <div className="h-24 w-24 bg-indigo-100 rounded-full flex items-center justify-center">
              <Search className="h-12 w-12 text-indigo-600" />
            </div>
          </div>
          
          {/* エラーメッセージ */}
          <h1 className="mt-6 text-6xl font-extrabold text-gray-900">404</h1>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-gray-900">
            ページが見つかりません
          </h2>
          <p className="mt-4 text-base text-gray-600">
            お探しのページは存在しないか、移動または削除された可能性があります。
          </p>

          {/* アクションボタン */}
          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <Home className="h-4 w-4 mr-2" />
              ホームに戻る
            </Link>
            
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              前のページに戻る
            </button>
          </div>

          {/* 人気のページへのリンク */}
          <div className="mt-8">
            <h3 className="text-sm font-medium text-gray-900 mb-4">
              こちらのページもお試しください
            </h3>
            <div className="space-y-2">
              <div>
                <Link
                  to="/templates"
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  テンプレート一覧
                </Link>
              </div>
              <div>
                <Link
                  to="/templates/create"
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  新しいテンプレートを作成
                </Link>
              </div>
              <div>
                <Link
                  to="/dashboard"
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  ダッシュボード
                </Link>
              </div>
            </div>
          </div>

          {/* お問い合わせ */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              問題が解決しない場合は、
              <a 
                href="mailto:support@vectormindstudio.com" 
                className="text-indigo-600 hover:text-indigo-500"
              >
                サポートチーム
              </a>
              までお問い合わせください。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFound;