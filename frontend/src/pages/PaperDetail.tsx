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
  Settings,
  Save,
  X,
  Download,
  ExpandIcon,
  Minimize2
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
  const [editingSections, setEditingSections] = useState<Set<string>>(new Set());
  const [sectionContents, setSectionContents] = useState<Record<string, string>>({});
  const [loadingSections, setLoadingSections] = useState<Set<string>>(new Set());

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


  // セクション更新ミューテーション
  const updateSectionMutation = useMutation({
    mutationFn: ({ sectionId, content }: { sectionId: string; content: string }) => 
      paperService.updateSection(id!, sectionId, { content }),
    onSuccess: () => {
      toast.success('セクションが更新されました');
      queryClient.invalidateQueries({ queryKey: ['paper-sections', id] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'セクションの更新に失敗しました');
    },
  });


  const toggleSectionExpansion = async (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (expandedSections.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
      // セクション内容を取得
      if (!sectionContents[sectionId] && !loadingSections.has(sectionId)) {
        setLoadingSections(prev => new Set(prev).add(sectionId));
        try {
          const sectionDetail = await paperService.getSection(id!, sectionId);
          setSectionContents(prev => ({
            ...prev,
            [sectionId]: sectionDetail.content || ''
          }));
        } catch (error) {
          console.error('セクション内容取得エラー:', error);
          toast.error('セクション内容の取得に失敗しました');
        } finally {
          setLoadingSections(prev => {
            const newSet = new Set(prev);
            newSet.delete(sectionId);
            return newSet;
          });
        }
      }
    }
    setExpandedSections(newExpanded);
  };


  const handleSectionEdit = (sectionId: string) => {
    setEditingSections(prev => new Set(prev).add(sectionId));
  };

  const handleSectionSave = (sectionId: string) => {
    const content = sectionContents[sectionId];
    if (content !== undefined) {
      updateSectionMutation.mutate({ sectionId, content });
      setEditingSections(prev => {
        const newSet = new Set(prev);
        newSet.delete(sectionId);
        return newSet;
      });
    }
  };

  const handleSectionCancel = (sectionId: string) => {
    setEditingSections(prev => {
      const newSet = new Set(prev);
      newSet.delete(sectionId);
      return newSet;
    });
    // 元の内容に戻す
    queryClient.invalidateQueries({ queryKey: ['paper-sections', id] });
  };

  const handleSectionContentChange = (sectionId: string, content: string) => {
    setSectionContents(prev => ({
      ...prev,
      [sectionId]: content
    }));
  };

  const handleExportPaper = async () => {
    try {
      if (!paper || !sections) return;
      
      // 全セクションの内容を取得
      const sectionsWithContent = await Promise.all(
        sections.map(async (section) => {
          if (sectionContents[section.id]) {
            return { ...section, content: sectionContents[section.id] };
          }
          try {
            const sectionDetail = await paperService.getSection(id!, section.id);
            return { ...section, content: sectionDetail.content || '' };
          } catch (error) {
            return { ...section, content: '' };
          }
        })
      );

      // Markdown形式で論文をフォーマット
      let markdownContent = `# ${paper.title}\n\n`;
      if (paper.description) {
        markdownContent += `${paper.description}\n\n`;
      }

      sectionsWithContent.forEach(section => {
        markdownContent += `## ${section.section_number} ${section.title}\n\n`;
        if (section.content) {
          markdownContent += `${section.content}\n\n`;
        }
      });

      // ダウンロード
      const blob = new Blob([markdownContent], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${paper.title.replace(/[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/g, '_')}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success('論文をエクスポートしました');
    } catch (error) {
      console.error('エクスポートエラー:', error);
      toast.error('エクスポートに失敗しました');
    }
  };

  // 全セクション開閉機能
  const handleExpandAll = async () => {
    if (!sections) return;
    
    const allSectionIds = new Set(sections.map(section => section.id));
    setExpandedSections(allSectionIds);

    // まだ内容を取得していないセクションの内容を並列で取得
    const sectionsToLoad = sections.filter(
      section => !sectionContents[section.id] && !loadingSections.has(section.id)
    );

    if (sectionsToLoad.length > 0) {
      const newLoadingSections = new Set(sectionsToLoad.map(s => s.id));
      setLoadingSections(prev => new Set([...prev, ...newLoadingSections]));

      try {
        const sectionDetails = await Promise.allSettled(
          sectionsToLoad.map(section => 
            paperService.getSection(id!, section.id)
          )
        );

        const newSectionContents: Record<string, string> = {};
        sectionDetails.forEach((result, index) => {
          const sectionId = sectionsToLoad[index].id;
          if (result.status === 'fulfilled') {
            newSectionContents[sectionId] = result.value.content || '';
          } else {
            console.error(`セクション ${sectionId} の取得エラー:`, result.reason);
            newSectionContents[sectionId] = '';
          }
        });

        setSectionContents(prev => ({ ...prev, ...newSectionContents }));
      } catch (error) {
        console.error('セクション一括取得エラー:', error);
        toast.error('一部のセクション内容の取得に失敗しました');
      } finally {
        setLoadingSections(prev => {
          const newSet = new Set(prev);
          sectionsToLoad.forEach(section => newSet.delete(section.id));
          return newSet;
        });
      }
    }
  };

  const handleCollapseAll = () => {
    setExpandedSections(new Set());
  };

  const areAllExpanded = sections ? sections.every(section => expandedSections.has(section.id)) : false;
  const areAnyExpanded = expandedSections.size > 0;

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
                  <div className="flex items-center space-x-4">
                    <h2 className="text-xl font-semibold text-gray-900">論文構成</h2>
                    {sections && sections.length > 0 && (
                      <div className="flex items-center space-x-2">
                        {areAllExpanded ? (
                          <button
                            onClick={handleCollapseAll}
                            className="inline-flex items-center px-2 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
                            title="すべて閉じる"
                          >
                            <Minimize2 className="w-4 h-4 mr-1" />
                            すべて閉じる
                          </button>
                        ) : (
                          <button
                            onClick={handleExpandAll}
                            className="inline-flex items-center px-2 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
                            title="すべて開く"
                          >
                            <ExpandIcon className="w-4 h-4 mr-1" />
                            すべて開く
                          </button>
                        )}
                      </div>
                    )}
                  </div>
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
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={() => handleSectionEdit(section.id)}
                                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                                title="編集"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          
                          {expandedSections.has(section.id) && (
                            <div className="mt-3 pl-7 space-y-3">
                              {section.summary && (
                                <div>
                                  <h4 className="text-sm font-medium text-gray-700 mb-1">要約:</h4>
                                  <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">{section.summary}</p>
                                </div>
                              )}
                              
                              <div>
                                <h4 className="text-sm font-medium text-gray-700 mb-2">本文:</h4>
                                {loadingSections.has(section.id) ? (
                                  <div className="flex items-center justify-center py-4">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                                    <span className="ml-2 text-sm text-gray-500">読み込み中...</span>
                                  </div>
                                ) : editingSections.has(section.id) ? (
                                  <div className="space-y-2">
                                    <textarea
                                      value={sectionContents[section.id] || ''}
                                      onChange={(e) => handleSectionContentChange(section.id, e.target.value)}
                                      className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
                                      placeholder="セクションの内容を入力してください..."
                                    />
                                    <div className="flex items-center space-x-2">
                                      <button
                                        onClick={() => handleSectionSave(section.id)}
                                        disabled={updateSectionMutation.isPending}
                                        className="inline-flex items-center px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
                                      >
                                        <Save className="w-3 h-3 mr-1" />
                                        保存
                                      </button>
                                      <button
                                        onClick={() => handleSectionCancel(section.id)}
                                        className="inline-flex items-center px-3 py-1 bg-gray-500 text-white text-sm rounded-lg hover:bg-gray-600"
                                      >
                                        <X className="w-3 h-3 mr-1" />
                                        キャンセル
                                      </button>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="bg-white border border-gray-200 rounded-lg p-3 min-h-[100px]">
                                    {sectionContents[section.id] ? (
                                      <div className="whitespace-pre-wrap text-sm text-gray-700">
                                        {sectionContents[section.id]}
                                      </div>
                                    ) : (
                                      <p className="text-sm text-gray-500 italic">
                                        このセクションにはまだ内容がありません。編集ボタンを押して内容を追加してください。
                                      </p>
                                    )}
                                  </div>
                                )}
                              </div>
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
                  onClick={handleExportPaper}
                  className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
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