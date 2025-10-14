import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import MobileSidebar from './MobileSidebar';
import BottomNavigation from './BottomNavigation';
import { useAuth } from '../../contexts/AuthContext';
import { useBreakpoint } from '../../hooks/useMediaQuery';

const Layout: React.FC = () => {
  const { isLoading } = useAuth();
  const { isMobile } = useBreakpoint();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー（レスポンシブ対応） */}
      <Header onMenuClick={() => setMobileMenuOpen(true)} />

      <div className="flex h-screen pt-16 pb-0 md:pb-0">
        {/* デスクトップ: 固定サイドバー（完全維持） */}
        {!isMobile && <Sidebar />}

        {/* モバイル: ドロワーサイドバー */}
        {isMobile && (
          <MobileSidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
        )}

        {/* メインコンテンツ */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-20 md:pb-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>

      {/* モバイル: ボトムナビゲーション */}
      {isMobile && <BottomNavigation onMenuClick={() => setMobileMenuOpen(true)} />}
    </div>
  );
};

export default Layout;