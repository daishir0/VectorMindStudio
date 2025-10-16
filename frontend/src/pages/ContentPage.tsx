import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  FileText,
  FileOutput,
} from 'lucide-react';
import CategoryPage from '../components/Common/CategoryPage';
import { WorkflowStep } from '../components/Common/WorkflowBar';

// 既存のページコンポーネントをインポート
import Templates from './Templates';
import OutputsPage from './Outputs';

const ContentPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // URLから現在のタブを取得
  const pathParts = location.pathname.split('/');
  const initialTab = pathParts[2] || 'templates';
  const [currentTab, setCurrentTab] = useState(initialTab);

  // タブ変更時にURLも更新
  const handleTabChange = (tabId: string) => {
    setCurrentTab(tabId);
    navigate(`/content/${tabId}`);
  };

  // ワークフローステップの定義（双方向）
  const workflowSteps: WorkflowStep[] = [
    {
      number: 1,
      icon: FileText,
      label: 'テンプレート',
      description: 'テンプレート作成',
      status: currentTab === 'templates' ? 'current' :
              currentTab === 'outputs' ? 'completed' : 'pending',
    },
    {
      number: 2,
      icon: FileOutput,
      label: 'アウトプット',
      description: '生成結果',
      status: currentTab === 'outputs' ? 'current' : 'pending',
    },
  ];

  // タブの定義
  const tabs = [
    {
      id: 'templates',
      label: 'テンプレート',
      icon: FileText,
      description: 'AIプロンプトのテンプレートを管理します',
      component: Templates,
    },
    {
      id: 'outputs',
      label: 'アウトプット',
      icon: FileOutput,
      description: 'AI生成されたコンテンツを確認します',
      component: OutputsPage,
    },
  ];

  return (
    <CategoryPage
      title="コンテンツ生成"
      titleIcon={Sparkles}
      description="テンプレートを作成して、AIで高品質なコンテンツを生成します"
      workflowSteps={workflowSteps}
      bidirectional={true}
      tabs={tabs}
      currentTab={currentTab}
      onTabChange={handleTabChange}
    />
  );
};

export default ContentPage;
