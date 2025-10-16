import React from 'react';
import { LucideIcon } from 'lucide-react';
import WorkflowBar, { WorkflowStep } from './WorkflowBar';

export interface TabConfig {
  id: string;
  label: string;
  icon: LucideIcon;
  description: string;
  component: React.ComponentType;
}

interface CategoryPageProps {
  title: string;
  titleIcon?: LucideIcon;
  description: string;
  workflowSteps?: WorkflowStep[];
  bidirectional?: boolean;
  tabs: TabConfig[];
  currentTab: string;
  onTabChange: (tabId: string) => void;
}

const CategoryPage: React.FC<CategoryPageProps> = ({
  title,
  titleIcon: TitleIcon,
  description,
  workflowSteps,
  bidirectional,
  tabs,
  currentTab,
  onTabChange,
}) => {
  const currentTabData = tabs.find(t => t.id === currentTab);

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          {TitleIcon && <TitleIcon className="w-8 h-8 mr-3 text-blue-600" />}
          {title}
        </h1>
        <p className="mt-1 text-sm text-gray-600">{description}</p>
      </div>

      {/* ワークフローバー */}
      {workflowSteps && workflowSteps.length > 0 && (
        <WorkflowBar steps={workflowSteps} bidirectional={bidirectional} />
      )}

      {/* タブナビゲーション */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          {tabs.map(tab => {
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  group inline-flex items-center px-1 py-4 border-b-2 font-medium text-sm
                  transition-colors duration-200
                  ${isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
                aria-current={isActive ? 'page' : undefined}
              >
                <tab.icon className={`
                  w-5 h-5 mr-2 transition-colors duration-200
                  ${isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}
                `} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* タブ説明バー */}
      {currentTabData && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-md">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm text-blue-700">
                💡 {currentTabData.description}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* コンテンツエリア */}
      <div className={`
        bg-white rounded-lg shadow-sm border border-gray-200
        ${currentTab === 'chat' ? 'p-0 h-[calc(100vh-280px)] overflow-hidden' : 'p-6'}
      `}>
        {currentTabData && <currentTabData.component />}
      </div>
    </div>
  );
};

export default CategoryPage;
