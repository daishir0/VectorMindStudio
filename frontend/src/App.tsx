import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import Templates from './pages/Templates';
import TemplateDetail from './pages/TemplateDetail';
import CreateTemplate from './pages/CreateTemplate';
import EditTemplate from './pages/EditTemplate';
import UploadPage from './pages/Upload';
import FilesPage from './pages/Files';
import SearchPage from './pages/SearchPage';
import OutputsPage from './pages/Outputs';
import OutputDetailPage from './pages/OutputDetail';
import Dashboard from './pages/Dashboard';
import VectorDBPage from './pages/VectorDB';
import ChatPage from './pages/Chat';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import Help from './pages/Help';
import NotFound from './pages/NotFound';
import Papers from './pages/Papers';
import CreatePaper from './pages/CreatePaper';
import EditPaper from './pages/EditPaper';
import PaperDetail from './pages/PaperDetail';
import CreateChatSession from './pages/CreateChatSession';
import ChatSession from './pages/ChatSession';
import LangGraphAgentsPage from './pages/LangGraphAgentsPage';
import LangGraphAgentDetailPage from './pages/LangGraphAgentDetailPage';

// 新しい統合ページ
import KnowledgePage from './pages/KnowledgePage';
import ContentPage from './pages/ContentPage';
import ResearchPage from './pages/ResearchPage';
import SettingsPageWrapper from './pages/SettingsPageWrapper';

import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';

// React Query クライアント設定
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Routes>
              {/* パブリックルート */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* プロテクトされたルート */}
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  {/* ホーム */}
                  <Route path="/" element={<Home />} />

                  {/* ナレッジベース統合ページ */}
                  <Route path="/knowledge" element={<Navigate to="/knowledge/files" replace />} />
                  <Route path="/knowledge/:tab" element={<KnowledgePage />} />

                  {/* コンテンツ生成統合ページ */}
                  <Route path="/content" element={<Navigate to="/content/templates" replace />} />
                  <Route path="/content/:tab" element={<ContentPage />} />
                  {/* テンプレート詳細ページ（個別ルート） */}
                  <Route path="/templates/:id" element={<TemplateDetail />} />
                  <Route path="/templates/:id/edit" element={<EditTemplate />} />
                  <Route path="/templates/create" element={<CreateTemplate />} />
                  {/* アウトプット詳細ページ（個別ルート） */}
                  <Route path="/outputs/:id" element={<OutputDetailPage />} />

                  {/* 論文・AI統合ページ */}
                  <Route path="/research" element={<Navigate to="/research/agents" replace />} />
                  <Route path="/research/:tab" element={<ResearchPage />} />
                  {/* 論文詳細ページ（個別ルート） */}
                  <Route path="/papers/:id" element={<PaperDetail />} />
                  <Route path="/papers/:id/edit" element={<EditPaper />} />
                  <Route path="/papers/create" element={<CreatePaper />} />
                  <Route path="/papers/:id/chat/create" element={<CreateChatSession />} />
                  <Route path="/papers/:id/chat/:sessionId" element={<ChatSession />} />
                  {/* エージェント詳細ページ（個別ルート） */}
                  <Route path="/langgraph-agents/:agentId" element={<LangGraphAgentDetailPage />} />

                  {/* 設定統合ページ */}
                  <Route path="/settings" element={<Navigate to="/settings/profile" replace />} />
                  <Route path="/settings/:tab" element={<SettingsPageWrapper />} />

                  {/* 旧URLから新URLへのリダイレクト */}
                  <Route path="/dashboard" element={<Navigate to="/" replace />} />
                  <Route path="/files" element={<Navigate to="/knowledge/files" replace />} />
                  <Route path="/vectordb" element={<Navigate to="/knowledge/vectordb" replace />} />
                  <Route path="/search" element={<Navigate to="/knowledge/search" replace />} />
                  <Route path="/chat" element={<Navigate to="/knowledge/chat" replace />} />
                  <Route path="/templates" element={<Navigate to="/content/templates" replace />} />
                  <Route path="/outputs" element={<Navigate to="/content/outputs" replace />} />
                  <Route path="/papers" element={<Navigate to="/research/papers" replace />} />
                  <Route path="/langgraph-agents" element={<Navigate to="/research/agents" replace />} />
                  <Route path="/profile" element={<Navigate to="/settings/profile" replace />} />
                  <Route path="/help" element={<Navigate to="/settings/help" replace />} />

                  {/* 旧アップロードページ */}
                  <Route path="/upload" element={<UploadPage />} />
                </Route>
              </Route>
              
              {/* 404ページ */}
              <Route path="*" element={<NotFound />} />
            </Routes>
            
            {/* トースト通知 */}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10b981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;