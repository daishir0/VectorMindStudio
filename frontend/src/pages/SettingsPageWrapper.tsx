import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Settings as SettingsIcon,
  User,
  HelpCircle,
} from 'lucide-react';
import CategoryPage from '../components/Common/CategoryPage';

// 既存のページコンポーネントをインポート
import Profile from './Profile';
import Settings from './Settings';
import Help from './Help';

const SettingsPageWrapper: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // URLから現在のタブを取得
  const pathParts = location.pathname.split('/');
  const initialTab = pathParts[2] || 'profile';
  const [currentTab, setCurrentTab] = useState(initialTab);

  // タブ変更時にURLも更新
  const handleTabChange = (tabId: string) => {
    setCurrentTab(tabId);
    navigate(`/settings/${tabId}`);
  };

  // タブの定義（設定にはワークフローなし）
  const tabs = [
    {
      id: 'profile',
      label: 'プロフィール',
      icon: User,
      description: 'アカウント情報を管理します',
      component: Profile,
    },
    {
      id: 'system',
      label: 'システム設定',
      icon: SettingsIcon,
      description: 'アプリケーションの設定を変更します',
      component: Settings,
    },
    {
      id: 'help',
      label: 'ヘルプ',
      icon: HelpCircle,
      description: '使い方やFAQを確認します',
      component: Help,
    },
  ];

  return (
    <CategoryPage
      title="設定"
      titleIcon={SettingsIcon}
      description="アカウント情報やシステムの設定を管理します"
      tabs={tabs}
      currentTab={currentTab}
      onTabChange={handleTabChange}
    />
  );
};

export default SettingsPageWrapper;
