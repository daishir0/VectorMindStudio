import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Database,
  File,
  Search,
  MessageSquare,
  Settings as SettingsIcon,
} from 'lucide-react';
import CategoryPage from '../components/Common/CategoryPage';
import { WorkflowStep } from '../components/Common/WorkflowBar';

// 既存のページコンポーネントをインポート
import FilesPage from './Files';
import VectorDBPage from './VectorDB';
import SearchPage from './SearchPage';
import ChatPage from './Chat';

const KnowledgePage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // URLから現在のタブを取得
  const pathParts = location.pathname.split('/');
  const initialTab = pathParts[2] || 'files';
  const [currentTab, setCurrentTab] = useState(initialTab);

  // タブ変更時にURLも更新
  const handleTabChange = (tabId: string) => {
    setCurrentTab(tabId);
    navigate(`/knowledge/${tabId}`);
  };

  // ワークフローステップの定義
  const workflowSteps: WorkflowStep[] = [
    {
      number: 1,
      icon: File,
      label: 'ファイル',
      description: 'アップロード',
      status: currentTab === 'files' ? 'current' :
              ['vectordb', 'search', 'chat'].includes(currentTab) ? 'completed' : 'pending',
    },
    {
      number: 2,
      icon: SettingsIcon,
      label: '管理',
      description: '確認',
      status: currentTab === 'vectordb' ? 'current' :
              ['search', 'chat'].includes(currentTab) ? 'completed' : 'pending',
    },
    {
      number: 3,
      icon: Search,
      label: '検索',
      description: '探索',
      status: currentTab === 'search' ? 'current' :
              currentTab === 'chat' ? 'completed' : 'pending',
    },
    {
      number: 4,
      icon: MessageSquare,
      label: 'Chat',
      description: '活用',
      status: currentTab === 'chat' ? 'current' : 'pending',
    },
  ];

  // タブの定義
  const tabs = [
    {
      id: 'files',
      label: 'ファイル管理',
      icon: File,
      description: 'PDFや文書をアップロードして登録します',
      component: FilesPage,
    },
    {
      id: 'vectordb',
      label: 'VectorDB管理',
      icon: Database,
      description: 'ベクター化の状況と品質を確認します',
      component: VectorDBPage,
    },
    {
      id: 'search',
      label: '検索',
      icon: Search,
      description: 'アップロードした内容から情報を探します',
      component: SearchPage,
    },
    {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
      description: '検索結果を使ってAIと対話します',
      component: ChatPage,
    },
  ];

  return (
    <CategoryPage
      title="ナレッジベース"
      titleIcon={Database}
      description="データをアップロードして、AIで活用するまでのワークフロー"
      workflowSteps={workflowSteps}
      tabs={tabs}
      currentTab={currentTab}
      onTabChange={handleTabChange}
    />
  );
};

export default KnowledgePage;
