import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, FileText, Loader, Trash2, Tag, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { chatService, ChatMessage, ChatSession } from '../services/chatService';
import { fileService } from '../services/fileService';
import { formatTimeWithTimezone } from '../utils/dateUtils';


const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // タグフィルター関連
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  // メッセージエリアを最下部にスクロール
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadChatSessions();
    loadAvailableTags();
  }, []);

  const loadChatSessions = async () => {
    try {
      setLoadingSessions(true);
      const sessions = await chatService.getSessions();
      setChatSessions(sessions);
    } catch (error) {
      toast.error('チャット履歴の取得に失敗しました。');
      console.error('Failed to load chat sessions:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadAvailableTags = async () => {
    try {
      const allTags = await fileService.getAllUserTags();
      setAvailableTags(allTags);
    } catch (error) {
      console.error('Failed to load available tags:', error);
    }
  };

  // 新しいチャットセッションを作成
  const createNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
  };

  // チャットセッションを切り替え
  const switchChatSession = async (sessionId: string) => {
    try {
      setCurrentSessionId(sessionId);
      const history = await chatService.getSessionHistory(sessionId);
      setMessages(history);
    } catch (error) {
      toast.error('チャット履歴の読み込みに失敗しました。');
      console.error('Failed to load chat history:', error);
    }
  };

  // タグ選択・解除
  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  // タグフィルターをクリア
  const clearTagFilter = () => {
    setSelectedTags([]);
  };

  // メッセージを送信
  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const messageText = inputText;
    setInputText('');
    setIsLoading(true);

    // ユーザーメッセージを即座に表示
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: messageText,
      role: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatService.sendMessage({
        message: messageText,
        session_id: currentSessionId || undefined,
        max_documents: 5,
        tags: selectedTags.length > 0 ? selectedTags : undefined
      });

      // 新しいセッションの場合、セッションIDを更新
      if (!currentSessionId) {
        setCurrentSessionId(response.session_id);
        // セッション一覧を再読み込み
        await loadChatSessions();
      }

      // AIレスポンスを追加
      setMessages(prev => [...prev, response.message]);
      
    } catch (error) {
      toast.error('メッセージの送信に失敗しました。');
      console.error('Chat error:', error);
      // エラー時はユーザーメッセージを削除
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setIsLoading(false);
    }
  };

  // Enterキーでメッセージ送信
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // セッションを削除
  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('このチャットセッションを削除しますか？')) return;
    
    try {
      await chatService.deleteSession(sessionId);
      setChatSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // 現在のセッションが削除された場合、新しいチャットに切り替え
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      
      toast.success('セッションを削除しました。');
    } catch (error) {
      toast.error('セッションの削除に失敗しました。');
      console.error('Failed to delete session:', error);
    }
  };

  // メッセージのフォーマット
  const formatTimestamp = (timestamp: Date) => {
    return formatTimeWithTimezone(timestamp);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* サイドバー - チャット履歴 */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={createNewChat}
            className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            新しいチャット
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            <h3 className="text-sm font-medium text-gray-500 mb-2 px-2">チャット履歴</h3>
            {loadingSessions ? (
              <div className="text-sm text-gray-400 px-2">
                読み込み中...
              </div>
            ) : chatSessions.length === 0 ? (
              <div className="text-sm text-gray-400 px-2">
                まだチャット履歴がありません
              </div>
            ) : (
              <div className="space-y-1">
                {chatSessions.map((session) => (
                  <div
                    key={session.id}
                    className={`group relative rounded-lg transition-colors ${
                      currentSessionId === session.id ? 'bg-indigo-50 border border-indigo-200' : 'hover:bg-gray-100'
                    }`}
                  >
                    <button
                      onClick={() => switchChatSession(session.id)}
                      className="w-full text-left p-2 rounded-lg"
                    >
                      <div className="text-sm font-medium text-gray-900 truncate pr-6">
                        {session.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {session.updated_at.toLocaleDateString('ja-JP')}
                      </div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(session.id);
                      }}
                      className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* メインチャットエリア */}
      <div className="flex-1 flex flex-col">
        {/* ヘッダー */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center">
            <Bot className="h-6 w-6 text-indigo-600 mr-2" />
            <h1 className="text-lg font-semibold text-gray-900">VectorDB Chat</h1>
            <span className="ml-2 text-sm text-gray-500">
              アップロードしたファイルの内容について質問できます
            </span>
          </div>
        </div>

        {/* メッセージエリア */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot className="h-16 w-16 text-gray-300 mb-4" />
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                VectorDBチャットへようこそ
              </h2>
              <p className="text-gray-500 max-w-md">
                アップロードしたファイルの内容について質問してください。
                AI が関連する情報を検索して回答します。
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl px-4 py-2 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white border border-gray-200'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && (
                      <Bot className="h-5 w-5 text-indigo-600 mt-1 flex-shrink-0" />
                    )}
                    {message.role === 'user' && (
                      <User className="h-5 w-5 text-white mt-1 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="text-sm whitespace-pre-wrap">
                        {message.content}
                      </div>
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-100">
                          <div className="text-xs text-gray-500 mb-1">参照元:</div>
                          <div className="flex flex-wrap gap-1">
                            {message.sources.map((source, index) => (
                              <span
                                key={index}
                                className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md"
                              >
                                <FileText className="h-3 w-3 mr-1" />
                                {source}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      <div className={`text-xs mt-1 ${
                        message.role === 'user' ? 'text-indigo-100' : 'text-gray-400'
                      }`}>
                        {formatTimestamp(message.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-2 max-w-xs">
                <div className="flex items-center space-x-2">
                  <Bot className="h-5 w-5 text-indigo-600" />
                  <div className="flex items-center space-x-1">
                    <Loader className="h-4 w-4 text-gray-400 animate-spin" />
                    <span className="text-sm text-gray-500">AI が回答を生成中...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* タグフィルターエリア */}
        {availableTags.length > 0 && (
          <div className="bg-gray-50 border-t border-gray-200 p-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Tag className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">参照文書のタグフィルター:</span>
                {selectedTags.length > 0 && (
                  <button
                    onClick={clearTagFilter}
                    className="text-xs text-gray-500 hover:text-gray-700 underline"
                  >
                    クリア
                  </button>
                )}
              </div>
              
              <div className="flex flex-wrap gap-2">
                {availableTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => handleTagToggle(tag)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      selectedTags.includes(tag)
                        ? 'bg-indigo-100 text-indigo-800 border-indigo-200'
                        : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>

              {selectedTags.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">選択中:</span>
                  <div className="flex flex-wrap gap-1">
                    {selectedTags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                      >
                        {tag}
                        <button
                          onClick={() => handleTagToggle(tag)}
                          className="ml-1 text-indigo-600 hover:text-indigo-800"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 入力エリア */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="メッセージを入力してください..."
                className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                rows={1}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;