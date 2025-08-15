import React from 'react';
import { Link } from 'react-router-dom';
import { Plus, FileText, TrendingUp, Clock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Home: React.FC = () => {
  const { user } = useAuth();

  const quickActions = [
    {
      name: 'テンプレート作成',
      description: '新しいAIテンプレートを作成',
      href: '/templates/create',
      icon: Plus,
      color: 'bg-blue-600',
    },
    {
      name: 'テンプレート一覧',
      description: '既存のテンプレートを確認',
      href: '/templates',
      icon: FileText,
      color: 'bg-green-600',
    },
    {
      name: 'ダッシュボード',
      description: '利用状況を確認',
      href: '/dashboard',
      icon: TrendingUp,
      color: 'bg-purple-600',
    },
  ];

  const recentTemplates = [
    {
      id: '1',
      name: 'ブログ記事生成テンプレート',
      description: 'SEO最適化されたブログ記事を自動生成',
      usage_count: 25,
      created_at: '2024-01-15',
    },
    {
      id: '2',
      name: 'メール返信テンプレート',
      description: '顧客サポート用の丁寧な返信メールを生成',
      usage_count: 18,
      created_at: '2024-01-14',
    },
    {
      id: '3',
      name: 'プレゼン資料構成テンプレート',
      description: '効果的なプレゼンテーションの構成案を作成',
      usage_count: 12,
      created_at: '2024-01-13',
    },
  ];

  return (
    <div className="space-y-8">
      {/* ウェルカムセクション */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          お帰りなさい、{user?.full_name || user?.username}さん！
        </h1>
        <p className="text-blue-100 text-lg">
          VectorMindStudioでAIを活用した効率的なコンテンツ作成を始めましょう
        </p>
      </div>

      {/* クイックアクション */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">クイックアクション</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow group"
            >
              <div className="flex items-center mb-4">
                <div className={`${action.color} rounded-lg p-3 mr-4`}>
                  <action.icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600">
                    {action.name}
                  </h3>
                  <p className="text-gray-600 text-sm">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* 統計情報 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">今月の統計</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">作成テンプレート</p>
                <p className="text-2xl font-bold text-gray-900">8</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <p className="text-sm text-green-600 mt-2">+2 前月比</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">テンプレート使用</p>
                <p className="text-2xl font-bold text-gray-900">152</p>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <p className="text-sm text-green-600 mt-2">+24% 前月比</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">生成コンテンツ</p>
                <p className="text-2xl font-bold text-gray-900">1,247</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <Plus className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <p className="text-sm text-green-600 mt-2">+18% 前月比</p>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">平均処理時間</p>
                <p className="text-2xl font-bold text-gray-900">2.4s</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-3">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <p className="text-sm text-red-600 mt-2">+0.2s 前月比</p>
          </div>
        </div>
      </div>

      {/* 最近のテンプレート */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">最近のテンプレート</h2>
          <Link
            to="/templates"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            すべて表示 →
          </Link>
        </div>
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="divide-y divide-gray-200">
            {recentTemplates.map((template) => (
              <div key={template.id} className="p-6 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <Link
                      to={`/templates/${template.id}`}
                      className="text-lg font-semibold text-gray-900 hover:text-blue-600"
                    >
                      {template.name}
                    </Link>
                    <p className="text-gray-600 mt-1">{template.description}</p>
                    <div className="flex items-center mt-3 text-sm text-gray-500">
                      <span>使用回数: {template.usage_count}</span>
                      <span className="mx-2">•</span>
                      <span>作成日: {template.created_at}</span>
                    </div>
                  </div>
                  <button className="btn btn-primary btn-sm ml-4">
                    使用する
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ヘルプセクション */}
      <div className="bg-gray-50 rounded-lg p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">始めかた</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">1. テンプレートを作成</h3>
            <p className="text-gray-600 text-sm">
              AIに与えるプロンプトと変数を定義してテンプレートを作成します。
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">2. 変数を設定</h3>
            <p className="text-gray-600 text-sm">
              作成したテンプレートに具体的な値を入力してAIコンテンツを生成します。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;