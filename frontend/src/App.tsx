import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
import NotFound from './pages/NotFound';

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
                  <Route path="/" element={<Home />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/templates" element={<Templates />} />
                  <Route path="/templates/:id" element={<TemplateDetail />} />
                  <Route path="/templates/:id/edit" element={<EditTemplate />} />
                  <Route path="/templates/create" element={<CreateTemplate />} />
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="/files" element={<FilesPage />} />
                  <Route path="/vectordb" element={<VectorDBPage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/outputs" element={<OutputsPage />} />
                  <Route path="/outputs/:id" element={<OutputDetailPage />} />
                  <Route path="/profile" element={<Profile />} />
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