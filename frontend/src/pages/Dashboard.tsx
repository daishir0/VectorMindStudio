import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  FileText, 
  Play, 
  TrendingUp, 
  Clock, 
  Plus,
  Activity
} from 'lucide-react';
import { api } from '../services/api';
import { Template, DashboardStats } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTemplates, setRecentTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // テンプレート一覧を取得（統計として使用）
      const templatesResponse = await api.get('/api/v1/templates?limit=5');
      setRecentTemplates(templatesResponse.items || []);
      
      // 統計データを計算
      const totalTemplates = templatesResponse.total || 0;
      const activeTemplates = templatesResponse.items?.filter((t: Template) => t.status === 'active').length || 0;
      
      setStats({
        total_templates: totalTemplates,
        active_templates: activeTemplates,
        total_outputs: 0, // TODO: 実際のアウトプット数を取得
        recent_activity: [] // TODO: 実際のアクティビティを取得
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">ダッシュボードを読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
          <p className="mt-1 text-sm text-gray-600">
            VectorMindStudioの概要と最近のアクティビティ
          </p>
        </div>
        <Link
          to="/templates/create"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          新しいテンプレート
        </Link>
      </div>

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
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    総テンプレート数
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats?.total_templates || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    アクティブテンプレート
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats?.active_templates || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Play className="h-6 w-6 text-blue-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    今月の実行回数
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {recentTemplates.reduce((sum, t) => sum + (t.usage_count || 0), 0)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-6 w-6 text-purple-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    生成コンテンツ数
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats?.total_outputs || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最近のテンプレート */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">最近のテンプレート</h2>
              <Link
                to="/templates"
                className="text-sm text-indigo-600 hover:text-indigo-500"
              >
                すべて見る
              </Link>
            </div>
          </div>
          <div className="p-6">
            {recentTemplates.length > 0 ? (
              <div className="space-y-4">
                {recentTemplates.slice(0, 5).map((template) => (
                  <div key={template.id} className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <Link
                        to={`/templates/${template.id}`}
                        className="text-sm font-medium text-gray-900 hover:text-indigo-600 truncate block"
                      >
                        {template.name}
                      </Link>
                      <p className="text-xs text-gray-500 truncate">
                        {template.description || 'No description'}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        template.status === 'active' 
                          ? 'bg-green-100 text-green-800'
                          : template.status === 'draft'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {template.status === 'active' ? 'アクティブ' : 
                         template.status === 'draft' ? '下書き' : 'アーカイブ'}
                      </span>
                      <span>{template.usage_count || 0}回</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">テンプレートがまだありません</p>
                <Link
                  to="/templates/create"
                  className="mt-2 inline-flex items-center text-sm text-indigo-600 hover:text-indigo-500"
                >
                  最初のテンプレートを作成
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* クイックアクション */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">クイックアクション</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <Link
                to="/templates/create"
                className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex-shrink-0 h-10 w-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <Plus className="h-5 w-5 text-indigo-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-900">新しいテンプレート</h3>
                  <p className="text-xs text-gray-500">AI生成用のテンプレートを作成</p>
                </div>
              </Link>

              <Link
                to="/templates"
                className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex-shrink-0 h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <FileText className="h-5 w-5 text-green-600" />
                </div>
                <div className="ml-4">
                  <h3 className="text-sm font-medium text-gray-900">テンプレート一覧</h3>
                  <p className="text-xs text-gray-500">既存のテンプレートを表示・編集</p>
                </div>
              </Link>

              {recentTemplates.length > 0 && (
                <Link
                  to={`/templates/${recentTemplates[0].id}`}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-shrink-0 h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Play className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-sm font-medium text-gray-900">最近のテンプレートを使用</h3>
                    <p className="text-xs text-gray-500">{recentTemplates[0].name}</p>
                  </div>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 最近のアクティビティ */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">最近のアクティビティ</h2>
        </div>
        <div className="p-6">
          <div className="text-center py-8">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">アクティビティログは開発中です</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;