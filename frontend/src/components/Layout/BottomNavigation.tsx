import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, PenTool, Search, Bot, Menu } from 'lucide-react';

interface BottomNavigationProps {
  onMenuClick: () => void;
}

const BottomNavigation: React.FC<BottomNavigationProps> = ({ onMenuClick }) => {
  const navItems = [
    { name: 'ホーム', icon: Home, href: '/' },
    { name: '論文', icon: PenTool, href: '/papers' },
    { name: '検索', icon: Search, href: '/search' },
    { name: 'AI', icon: Bot, href: '/agents' },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40 safe-area-pb">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                isActive ? 'text-blue-600' : 'text-gray-600'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-6 h-6 ${isActive ? 'stroke-2' : 'stroke-1.5'}`} />
                <span className={`text-xs mt-1 ${isActive ? 'font-medium' : 'font-normal'}`}>
                  {item.name}
                </span>
              </>
            )}
          </NavLink>
        ))}

        {/* メニューボタン */}
        <button
          onClick={onMenuClick}
          className="flex flex-col items-center justify-center flex-1 h-full text-gray-600 transition-colors active:text-blue-600"
          aria-label="メニューを開く"
        >
          <Menu className="w-6 h-6" />
          <span className="text-xs mt-1">メニュー</span>
        </button>
      </div>
    </nav>
  );
};

export default BottomNavigation;
