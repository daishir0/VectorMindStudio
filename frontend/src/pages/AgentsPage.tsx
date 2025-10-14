import React, { useState, useEffect } from 'react';
import { Bot, CheckCircle, XCircle, RefreshCw, Settings, AlertTriangle } from 'lucide-react';

interface Agent {
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  capabilities: string[];
  keywords: string[];
  lastUsed?: string;
  usageCount?: number;
}

const AgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all');

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      // バックエンドAPIからエージェント情報を取得
      const response = await fetch('/api/v1/agents', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // APIレスポンスからエージェント一覧を取得
        const agentsData = data.data?.agents || data.agents || [];

        // APIレスポンスをUI用の形式に変換
        const formattedAgents = agentsData.map((agent: any) => ({
          name: agent.display_name || agent.name,
          description: agent.description,
          status: agent.is_active ? 'active' : 'inactive',
          capabilities: agent.capabilities || [],
          keywords: agent.tags || [],
          usageCount: agent.usage_count || 0,
        }));

        setAgents(formattedAgents);
      } else {
        console.error('エージェント取得エラー:', response.status);
        // エラー時は空配列を設定
        setAgents([]);
      }
    } catch (error) {
      console.error('エージェント情報の取得に失敗:', error);
      // エラー時は空配列を設定
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  const getDefaultAgents = (): Agent[] => [
    {
      name: 'SupervisorAgent',
      description: 'LLMベースの高次タスク推論・エージェント管理を行うスーパーバイザー',
      status: 'active',
      capabilities: ['意図解析', 'ワークフロープランニング', 'タスク委譲', '品質管理'],
      keywords: [],
      usageCount: 0,
    },
    {
      name: 'DiscoveryAgent',
      description: 'ChromaDB検索・研究ギャップ発見・新しいテーマ探索・関連研究調査',
      status: 'active',
      capabilities: ['ChromaDB検索', 'ギャップ分析', '冗長性検出', '新規テーマ発見'],
      keywords: ['検索', 'ギャップ', '不足', '探索', '発見', '関連', '資料'],
      usageCount: 0,
    },
    {
      name: 'WriterAgent',
      description: '新しいコンテンツの生成・文章作成',
      status: 'active',
      capabilities: ['新規セクション作成', '文章生成', 'コンテンツ執筆'],
      keywords: ['作って', '書いて', '生成', '執筆', 'ドラフト'],
      usageCount: 0,
    },
    {
      name: 'SectionQueryAgent',
      description: '既存セクションの検索・参照・内容取得',
      status: 'active',
      capabilities: ['セクション内容の質問', '特定セクションの検索', '既存情報の参照'],
      keywords: ['教えて', 'について', '内容', '見せて'],
      usageCount: 0,
    },
    {
      name: 'OutlineAgent',
      description: '論文構造・アウトライン管理',
      status: 'active',
      capabilities: ['構造設計', 'セクション管理', 'アウトライン作成'],
      keywords: ['構造', 'アウトライン', 'セクション', '章立て'],
      usageCount: 0,
    },
    {
      name: 'SummaryAgent',
      description: '要約・概要作成',
      status: 'active',
      capabilities: ['要約作成', '論文全体のまとめ', '概要生成'],
      keywords: ['要約', 'まとめ', '概要', 'サマリー'],
      usageCount: 0,
    },
    {
      name: 'AnalysisAgent',
      description: '研究論文の深度分析・批判的評価・構造解析',
      status: 'active',
      capabilities: ['批判的分析', '構造分析', '整合性チェック', '弱点特定'],
      keywords: ['分析', '解析', '評価', '批判', '弱点', '問題'],
      usageCount: 0,
    },
    {
      name: 'EditingAgent',
      description: '研究論文の編集・改善・文章品質向上',
      status: 'active',
      capabilities: ['文体編集', '内容拡充', '可読性向上', '文章改善'],
      keywords: ['編集', '改善', '修正', '校正', '文体'],
      usageCount: 0,
    },
    {
      name: 'QualityAgent',
      description: '研究論文の品質評価・保証・学術基準チェック',
      status: 'active',
      capabilities: ['品質評価', '学術基準チェック', '倫理検証', '公開準備度評価'],
      keywords: ['品質', '評価', '基準', '倫理', '学術'],
      usageCount: 0,
    },
    {
      name: 'GenerationAgent',
      description: '新規コンテンツ生成・セクション作成・図表生成',
      status: 'active',
      capabilities: ['セクション生成', '内容拡充', 'アウトライン生成', '引用生成'],
      keywords: ['生成', '作成', '執筆', '図', '表', '引用'],
      usageCount: 0,
    },
    {
      name: 'StrategyAgent',
      description: '研究戦略立案・論証戦略・差別化戦略・影響力最大化',
      status: 'active',
      capabilities: ['研究戦略', '論証戦略', '差別化戦略', 'リスク軽減'],
      keywords: ['戦略', '計画', 'アプローチ', '方針', '差別化'],
      usageCount: 0,
    },
    {
      name: 'OptimizationAgent',
      description: '研究効率・品質・リソース・時間・影響・コスト最適化',
      status: 'active',
      capabilities: ['効率最適化', '品質最適化', 'リソース最適化', '時間最適化'],
      keywords: ['最適化', '効率', '改善', '向上', '短縮'],
      usageCount: 0,
    },
    {
      name: 'LogicValidatorAgent',
      description: '論理的整合性・品質チェック',
      status: 'active',
      capabilities: ['論理チェック', '整合性検証', '品質評価'],
      keywords: ['チェック', '確認', '検証', '品質'],
      usageCount: 0,
    },
  ];

  const filteredAgents = agents.filter(agent => {
    if (filter === 'all') return true;
    return agent.status === filter;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'inactive':
        return <XCircle className="w-5 h-5 text-gray-400" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      error: 'bg-red-100 text-red-800',
    };
    const labels = {
      active: '稼働中',
      inactive: '停止中',
      error: 'エラー',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${badges[status as keyof typeof badges]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Bot className="w-8 h-8 text-blue-600" />
              エージェント管理
            </h1>
            <p className="mt-2 text-gray-600">
              VectorMindStudioのAIエージェントを管理・モニタリングします
            </p>
          </div>
          <button
            onClick={fetchAgents}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            更新
          </button>
        </div>
      </div>

      {/* フィルター */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          すべて ({agents.length})
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'active'
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          稼働中 ({agents.filter(a => a.status === 'active').length})
        </button>
        <button
          onClick={() => setFilter('inactive')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'inactive'
              ? 'bg-gray-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          停止中 ({agents.filter(a => a.status === 'inactive').length})
        </button>
      </div>

      {/* エージェント一覧 */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <div
              key={agent.name}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setSelectedAgent(agent)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(agent.status)}
                  <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                </div>
                {getStatusBadge(agent.status)}
              </div>

              <p className="text-sm text-gray-600 mb-4">{agent.description}</p>

              <div className="space-y-3">
                <div>
                  <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">機能</h4>
                  <div className="flex flex-wrap gap-2">
                    {agent.capabilities.slice(0, 3).map((cap, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                        {cap}
                      </span>
                    ))}
                    {agent.capabilities.length > 3 && (
                      <span className="px-2 py-1 bg-gray-50 text-gray-600 text-xs rounded">
                        +{agent.capabilities.length - 3}
                      </span>
                    )}
                  </div>
                </div>

                {agent.keywords.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">キーワード</h4>
                    <div className="flex flex-wrap gap-1">
                      {agent.keywords.slice(0, 4).map((keyword, idx) => (
                        <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {agent.usageCount !== undefined && (
                  <div className="pt-3 border-t border-gray-100">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>利用回数</span>
                      <span className="font-medium">{agent.usageCount}回</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* エージェント詳細モーダル */}
      {selectedAgent && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedAgent(null)}
        >
          <div
            className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Bot className="w-8 h-8 text-blue-600" />
                <h2 className="text-2xl font-bold text-gray-900">{selectedAgent.name}</h2>
              </div>
              {getStatusBadge(selectedAgent.status)}
            </div>

            <p className="text-gray-600 mb-6">{selectedAgent.description}</p>

            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">機能一覧</h3>
                <ul className="space-y-2">
                  {selectedAgent.capabilities.map((cap, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      {cap}
                    </li>
                  ))}
                </ul>
              </div>

              {selectedAgent.keywords.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-3">トリガーキーワード</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.keywords.map((keyword, idx) => (
                      <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-lg">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-6 border-t border-gray-200 flex gap-3">
                <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
                  <Settings className="w-4 h-4" />
                  設定
                </button>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  閉じる
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentsPage;
