import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ArrowLeft, 
  Edit3, 
  Plus, 
  MessageSquare, 
  FileText, 
  Trash2,
  ChevronRight,
  ChevronDown,
  Settings
} from 'lucide-react';
import { paperService, PaperSection, SectionOutline, ChatSession } from '../services/paperService';
import toast from 'react-hot-toast';

const PaperDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'outline' | 'chat'>('outline');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [selectedSection, setSelectedSection] = useState<string | null>(null);

  // 論文データ取得
  const { data: paper, isLoading: paperLoading } = useQuery({
    queryKey: ['paper', id],
    queryFn: () => paperService.getPaper(id!),
    enabled: !!id,
  });

  // セクションデータ取得
  const { data: sections, isLoading: sectionsLoading } = useQuery({
    queryKey: ['paper-sections', id],
    queryFn: () => paperService.getSections(id!),
    enabled: !!id,
  });

  // チャットセッションデータ取得
  const { data: chatSessions, isLoading: chatLoading } = useQuery({
    queryKey: ['chat-sessions', id],
    queryFn: () => paperService.getChatSessions(id!),
    enabled: !!id && activeTab === 'chat',
  });

  // 論文削除ミューテーション
  const deleteMutation = useMutation({
    mutationFn: () => paperService.deletePaper(id!),
    onSuccess: () => {
      toast.success('論文が削除されました');
      navigate('/papers');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '削除に失敗しました');
    },
  });

  const handleDeletePaper = () => {
    if (window.confirm('この論文を削除してもよろしいですか？この操作は取り消せません。')) {
      deleteMutation.mutate();
    }
  };

  const toggleSectionExpansion = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (expandedSections.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { label: '下書き', color: 'bg-gray-100 text-gray-800' },
      in_progress: { label: '執筆中', color: 'bg-yellow-100 text-yellow-800' },
      completed: { label: '完了', color: 'bg-green-100 text-green-800' },
      published: { label: '公開済み', color: 'bg-blue-100 text-blue-800' },
      writing: { label: '執筆中', color: 'bg-blue-100 text-blue-800' },
      review: { label: 'レビュー中', color: 'bg-orange-100 text-orange-800' },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    
    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (paperLoading || sectionsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">論文データを読み込み中...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <p className="text-red-600">論文が見つかりません</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/papers')}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            論文一覧に戻る
          </button>
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{paper.title}</h1>
              {paper.description && (
                <p className="text-gray-600 mb-4">{paper.description}</p>
              )}
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                {getStatusBadge(paper.status)}
                <span>更新: {formatDate(paper.updated_at)}</span>
                <span>作成: {formatDate(paper.created_at)}</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => navigate(`/papers/${id}/edit`)}
                className="inline-flex items-center px-3 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Edit3 className="w-4 h-4 mr-2" />
                編集
              </button>
              <button
                onClick={handleDeletePaper}
                disabled={deleteMutation.isPending}
                className="inline-flex items-center px-3 py-2 text-red-700 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                削除
              </button>
            </div>
          </div>
        </div>

        {/* タブナビゲーション */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('outline')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'outline'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                構成・アウトライン
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'chat'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                研究ディスカッション
              </button>
            </nav>
          </div>
        </div>

        {/* コンテンツエリア */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* メインコンテンツ */}
          <div className="lg:col-span-2">
            {activeTab === 'outline' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">論文構成</h2>
                  <button
                    onClick={() => navigate(`/papers/${id}/sections/create`)}
                    className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    セクション追加
                  </button>
                </div>

                {sections && sections.length > 0 ? (
                  <div className="space-y-2">
                    {sections.map((section: SectionOutline) => (
                      <div
                        key={section.id}
                        className="bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
                      >
                        <div className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center flex-1">
                              <button
                                onClick={() => toggleSectionExpansion(section.id)}
                                className="p-1 hover:bg-gray-100 rounded mr-2"
                              >
                                {expandedSections.has(section.id) ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </button>
                              <div className="flex-1">
                                <h3 className="font-medium text-gray-900">
                                  {section.section_number} {section.title}
                                </h3>
                                <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                                  {getStatusBadge(section.status)}
                                  <span>{section.word_count}語</span>
                                  <span>{formatDate(section.updated_at)}</span>
                                </div>
                              </div>
                            </div>
                            <button
                              onClick={() => navigate(`/papers/${id}/sections/${section.id}/edit`)}
                              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                          </div>
                          
                          {expandedSections.has(section.id) && section.summary && (
                            <div className="mt-3 pl-7">
                              <p className="text-sm text-gray-600">{section.summary}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                    <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">セクションがありません</h3>
                    <p className="text-gray-600 mb-4">最初のセクションを追加して執筆を開始しましょう</p>
                    <button
                      onClick={() => navigate(`/papers/${id}/sections/create`)}
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      セクション追加
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'chat' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900">研究ディスカッション</h2>
                  <button
                    onClick={() => navigate(`/papers/${id}/chat/create`)}
                    className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    新しいセッション
                  </button>
                </div>

                {chatSessions && chatSessions.length > 0 ? (
                  <div className="space-y-3">
                    {chatSessions.map((session: ChatSession) => (
                      <div
                        key={session.id}
                        className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow cursor-pointer"
                        onClick={() => navigate(`/papers/${id}/chat/${session.id}`)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900">{session.title}</h3>
                            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                              <span>{session.message_count} メッセージ</span>
                              <span>更新: {formatDate(session.updated_at)}</span>
                            </div>
                          </div>
                          <MessageSquare className="w-5 h-5 text-gray-400" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
                    <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">ディスカッションがありません</h3>
                    <p className="text-gray-600 mb-4">AIアシスタントとの研究ディスカッションを開始しましょう</p>
                    <button
                      onClick={() => navigate(`/papers/${id}/chat/create`)}
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      新しいセッション
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* サイドバー */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-900 mb-3">論文統計</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">総セクション数</span>
                  <span className="text-sm font-medium">{sections?.length || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">総単語数</span>
                  <span className="text-sm font-medium">
                    {sections?.reduce((total, section) => total + section.word_count, 0).toLocaleString() || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">ディスカッション</span>
                  <span className="text-sm font-medium">{chatSessions?.length || 0}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-900 mb-3">クイックアクション</h3>
              <div className="space-y-2">
                <button
                  onClick={() => navigate(`/papers/${id}/export`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  論文をエクスポート
                </button>
                <button
                  onClick={() => navigate(`/papers/${id}/references`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  文献管理
                </button>
                <button
                  onClick={() => navigate(`/papers/${id}/settings`)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <Settings className="w-4 h-4 inline mr-2" />
                  設定
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaperDetail;