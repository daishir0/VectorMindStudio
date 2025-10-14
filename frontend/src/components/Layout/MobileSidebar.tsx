import React from 'react';
import { NavLink } from 'react-router-dom';
import { X } from 'lucide-react';
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
  Database,
  MessageSquare,
  PenTool,
  Bot,
  Layers,
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
  {
    name: 'エージェント管理',
    href: '/agents',
    icon: Bot,
  },
  {
    name: 'プロファイル管理',
    href: '/profiles',
    icon: Layers,
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

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const MobileSidebar: React.FC<MobileSidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* オーバーレイ */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* ドロワー */}
      <aside
        className={`
          fixed top-0 left-0 bottom-0 w-80 bg-white z-50
          transform transition-transform duration-300 ease-in-out
          md:hidden overflow-y-auto
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">VM</span>
            </div>
            <h2 className="text-lg font-bold text-gray-900">VectorMindStudio</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mr-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="メニューを閉じる"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <nav className="p-4 space-y-8">
          {/* メインナビゲーション */}
          <div>
            <ul className="space-y-1">
              {navigation.map((item) => (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center px-4 py-3 text-base font-medium rounded-lg transition-colors min-h-[48px] ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                          : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
                      }`
                    }
                  >
                    <item.icon className="w-6 h-6 mr-4" />
                    {item.name}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          {/* セカンダリナビゲーション */}
          <div>
            <h3 className="px-4 text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              その他
            </h3>
            <ul className="space-y-1">
              {secondaryNavigation.map((item) => (
                <li key={item.name}>
                  <NavLink
                    to={item.href}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center px-4 py-3 text-base font-medium rounded-lg transition-colors min-h-[48px] ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                          : 'text-gray-700 hover:bg-gray-100 active:bg-gray-200'
                      }`
                    }
                  >
                    <item.icon className="w-6 h-6 mr-4" />
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
        </nav>
      </aside>
    </>
  );
};

export default MobileSidebar;
