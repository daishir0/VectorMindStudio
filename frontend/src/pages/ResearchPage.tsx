import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  GraduationCap,
  PenTool,
  Bot,
} from 'lucide-react';
import CategoryPage from '../components/Common/CategoryPage';

// 既存のページコンポーネントをインポート
import Papers from './Papers';
import LangGraphAgentsPage from './LangGraphAgentsPage';

const ResearchPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // URLから現在のタブを取得
  const pathParts = location.pathname.split('/');
  const initialTab = pathParts[2] || 'agents';
  const [currentTab, setCurrentTab] = useState(initialTab);

  // タブ変更時にURLも更新
  const handleTabChange = (tabId: string) => {
    setCurrentTab(tabId);
    navigate(`/research/${tabId}`);
  };

  // タブの定義
  const tabs = [
    {
      id: 'agents',
      label: 'エージェント管理',
      icon: Bot,
      description: '論文執筆を支援するAIエージェントを管理します',
      component: LangGraphAgentsPage,
    },
    {
      id: 'papers',
      label: '論文執筆',
      icon: PenTool,
      description: 'エージェントを使って学術論文を執筆します',
      component: Papers,
    },
  ];

  return (
    <CategoryPage
      title="論文・AI"
      titleIcon={GraduationCap}
      description="AIエージェントを活用して、学術論文を効率的に執筆します"
      tabs={tabs}
      currentTab={currentTab}
      onTabChange={handleTabChange}
    />
  );
};

export default ResearchPage;
