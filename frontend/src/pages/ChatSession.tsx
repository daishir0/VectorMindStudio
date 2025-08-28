import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ArrowLeft, 
  Send, 
  Bot, 
  User, 
  Clock,
  CheckCircle,
  AlertCircle,
  Loader,
  MessageSquare
} from 'lucide-react';
import { paperService, ChatMessage, ChatResponse } from '../services/paperService';
import toast from 'react-hot-toast';
import { formatDateWithTimezone } from '../utils/dateUtils';

const ChatSession: React.FC = () => {
  const { id: paperId, sessionId } = useParams<{ id: string; sessionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // メッセージ履歴を取得
  const { data: messages, isLoading } = useQuery({
    queryKey: ['chat-messages', paperId, sessionId],
    queryFn: () => paperService.getChatMessages(paperId!, sessionId!),
    enabled: !!paperId && !!sessionId,
  });

  // メッセージ送信ミューテーション
  const sendMutation = useMutation({
    mutationFn: (data: { message: string }) => paperService.sendMessage(paperId!, sessionId!, data),
    onSuccess: (data: ChatResponse) => {
      if (data.success) {
        queryClient.invalidateQueries({ queryKey: ['chat-messages', paperId, sessionId] });
        toast.success('メッセージを送信しました');
      } else {
        toast.error('メッセージの送信に失敗しました');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'メッセージの送信に失敗しました');
    },
    onSettled: () => {
      setIsTyping(false);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sendMutation.isPending) return;
    
    const messageText = message.trim();
    
    // ユーザーメッセージを即座に表示（楽観的更新）
    const tempUserMessage: ChatMessage = {
      id: `temp_user_${Date.now()}`,
      content: messageText,
      role: 'user',
      created_at: new Date().toISOString(),
      agent_name: undefined,
      todo_tasks: [],
      references: []
    };

    queryClient.setQueryData(['chat-messages', paperId, sessionId], (oldMessages: ChatMessage[]) => {
      return oldMessages ? [...oldMessages, tempUserMessage] : [tempUserMessage];
    });

    setMessage('');
    setIsTyping(true);
    sendMutation.mutate({ message: messageText });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatDate = (dateString: string) => {
    return formatDateWithTimezone(dateString);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'in_progress':
        return <Loader className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getAgentColor = (agentName?: string) => {
    if (!agentName) return 'bg-blue-500';
    
    const colors: Record<string, string> = {
      'outline': 'bg-purple-500',
      'summary': 'bg-green-500', 
      'writer': 'bg-blue-500',
      'logic': 'bg-orange-500',
      'reference': 'bg-pink-500',
      'supervisor': 'bg-indigo-500'
    };
    
    const key = agentName.toLowerCase().replace('agent', '');
    return colors[key] || 'bg-gray-500';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">チャット履歴を読み込み中...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ヘッダー */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate(`/papers/${paperId}`)}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            論文詳細に戻る
          </button>
          <div className="flex items-center">
            <MessageSquare className="w-6 h-6 text-blue-600 mr-3" />
            <div>
              <h1 className="text-xl font-semibold text-gray-900">研究ディスカッション</h1>
              <p className="text-sm text-gray-600">AIアシスタントとの研究相談</p>
            </div>
          </div>
        </div>
      </div>

      {/* メッセージ履歴 */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages && messages.length > 0 ? (
            messages.map((msg: ChatMessage) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-900 border border-gray-200'
                  } rounded-lg p-4 shadow-sm`}
                >
                  {/* メッセージヘッダー */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      {msg.role === 'user' ? (
                        <User className="w-4 h-4 mr-2" />
                      ) : (
                        <>
                          <Bot className="w-4 h-4 mr-2" />
                          {msg.agent_name && (
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full text-white ${getAgentColor(msg.agent_name)} mr-2`}>
                              {msg.agent_name}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                    <span className={`text-xs ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                      {formatDate(msg.created_at)}
                    </span>
                  </div>

                  {/* メッセージ内容 */}
                  <div className="whitespace-pre-wrap">{msg.content}</div>

                  {/* TODOタスク */}
                  {msg.todo_tasks && msg.todo_tasks.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <h4 className="text-sm font-medium mb-2">実行中のタスク:</h4>
                      <div className="space-y-2">
                        {msg.todo_tasks.map((task, index) => (
                          <div key={index} className="flex items-center text-sm">
                            {getStatusIcon(task.status)}
                            <span className="ml-2 flex-1">{task.description}</span>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full text-white ${getAgentColor(task.agent_name)}`}>
                              {task.agent_name}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 参考文献 */}
                  {msg.references && msg.references.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <h4 className="text-sm font-medium mb-2">参考文献:</h4>
                      <div className="space-y-1">
                        {msg.references.map((ref, index) => (
                          <div key={index} className="text-sm text-gray-600">
                            {typeof ref === 'string' ? ref : ref.citation}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">メッセージがありません</h3>
              <p className="text-gray-600">最初のメッセージを送信してディスカッションを始めましょう</p>
            </div>
          )}

          {/* タイピングインジケーター */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="max-w-3xl bg-white text-gray-900 border border-gray-200 rounded-lg p-4 shadow-sm">
                <div className="flex items-center">
                  <Bot className="w-4 h-4 mr-2" />
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="ml-2 text-sm text-gray-500">AIが回答を生成中...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* メッセージ入力フォーム */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="研究について質問や相談をしてください..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                rows={3}
                maxLength={2000}
                disabled={sendMutation.isPending}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleSubmit(e);
                  }
                }}
              />
              <div className="flex justify-between items-center mt-2">
                <p className="text-xs text-gray-500">
                  {message.length}/2000文字 • Cmd/Ctrl + Enter で送信
                </p>
              </div>
            </div>
            <button
              type="submit"
              disabled={!message.trim() || sendMutation.isPending}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed self-end"
            >
              {sendMutation.isPending ? (
                <Loader className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatSession;