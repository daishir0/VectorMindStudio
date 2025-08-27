import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  FileText,
  BarChart3,
  User,
  Settings,
  HelpCircle,
  File,
  Search,
  FileOutput,
  Database, // VectorDB用のアイコン
  MessageSquare, // Chat用のアイコン
  PenTool, // Papers用のアイコン
} from 'lucide-react';

const navigation = [
  {
    name: 'ホーム',
    href: '/',
    icon: Home,
  },
  {
    name: 'ダッシュボード',
    href: '/dashboard',
    icon: BarChart3,
  },
  {
    name: '検索',
    href: '/search',
    icon: Search,
  },
  {
    name: 'ファイル管理',
    href: '/files',
    icon: File,
  },
  {
    name: 'VectorDB',
    href: '/vectordb',
    icon: Database,
  },
  {
    name: 'Chat',
    href: '/chat',
    icon: MessageSquare,
  },
  {
    name: 'テンプレート',
    href: '/templates',
    icon: FileText,
  },
  {
    name: 'アウトプット',
    href: '/outputs',
    icon: FileOutput,
  },
  {
    name: '論文執筆',
    href: '/papers',
    icon: PenTool,
  },
];

const secondaryNavigation = [
  {
    name: 'プロフィール',
    href: '/profile',
    icon: User,
  },
  {
    name: '設定',
    href: '/settings',
    icon: Settings,
  },
  {
    name: 'ヘルプ',
    href: '/help',
    icon: HelpCircle,
  },
];

const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
      <nav className="p-4 space-y-8">
        {/* メインナビゲーション */}
        <div>
          <ul className="space-y-2">
            {navigation.map((item) => (
              <li key={item.name}>
                <NavLink
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>

        {/* セカンダリナビゲーション */}
        <div>
          <h3 className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
            その他
          </h3>
          <ul className="space-y-2">
            {secondaryNavigation.map((item) => (
              <li key={item.name}>
                <NavLink
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>

        {/* 使用状況表示 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">月間使用量</h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">テンプレート使用</span>
              <span className="font-medium">48/100</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: '48%' }}
              ></div>
            </div>
          </div>
        </div>

        {/* フィードバックセクション */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">フィードバック</h4>
          <p className="text-xs text-blue-700 mb-3">
            VectorMindStudioの改善にご協力ください
          </p>
          <button className="w-full bg-blue-600 text-white text-xs py-2 px-3 rounded-md hover:bg-blue-700 transition-colors">
            フィードバックを送信
          </button>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;