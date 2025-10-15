import React, { useState } from 'react';
import {
  HelpCircle,
  Book,
  MessageCircle,
  Mail,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  Video,
  Code,
  Search,
} from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

const Help: React.FC = () => {
  const [expandedFAQ, setExpandedFAQ] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const faqs: FAQItem[] = [
    {
      category: 'basic',
      question: 'VectorMindStudioとは何ですか？',
      answer:
        'VectorMindStudioは、AIを活用した論文執筆・ドキュメント作成支援プラットフォームです。ベクトルデータベースを活用し、効率的な情報検索と文書生成をサポートします。',
    },
    {
      category: 'basic',
      question: '無料で利用できますか？',
      answer:
        '基本機能は無料でご利用いただけます。月間利用量に制限がありますが、プレミアムプランにアップグレードすることで制限を拡大できます。',
    },
    {
      category: 'usage',
      question: '論文を作成するにはどうすればよいですか？',
      answer:
        '左メニューの「論文執筆」をクリックし、「新規作成」ボタンから論文を作成できます。タイトル、概要、セクションを追加して文書を構成してください。',
    },
    {
      category: 'usage',
      question: 'テンプレートはどのように使用しますか？',
      answer:
        '「テンプレート」メニューから既存のテンプレートを選択するか、新規作成できます。テンプレートを使用することで、一貫性のある文書フォーマットを維持できます。',
    },
    {
      category: 'usage',
      question: 'ファイルをアップロードできますか？',
      answer:
        'はい。「ファイル管理」メニューから、PDF、Word、テキストファイルなどをアップロードできます。アップロードしたファイルはVectorDBに自動的にインデックスされます。',
    },
    {
      category: 'vectordb',
      question: 'VectorDBとは何ですか？',
      answer:
        'VectorDBは、文書をベクトル形式で保存し、意味的な類似性に基づいて高速に検索できるデータベースです。キーワード検索よりも高度な文脈理解が可能です。',
    },
    {
      category: 'vectordb',
      question: '検索機能の使い方を教えてください',
      answer:
        '検索バーにキーワードやフレーズを入力すると、VectorDBが意味的に関連するドキュメントやセクションを表示します。完全一致ではなく、文脈を考慮した検索が可能です。',
    },
    {
      category: 'agent',
      question: 'AIエージェントとは何ですか？',
      answer:
        'AIエージェントは、特定のタスクを自動実行する機能です。文章生成、要約、翻訳、データ分析など、様々な目的に応じたエージェントを作成・実行できます。',
    },
    {
      category: 'agent',
      question: 'カスタムエージェントを作成できますか？',
      answer:
        'はい。「エージェント管理」メニューから新規エージェントを作成し、プロンプトや動作パラメータをカスタマイズできます。プロファイル機能で複雑な挙動も定義可能です。',
    },
    {
      category: 'technical',
      question: 'データのセキュリティは保証されますか？',
      answer:
        'はい。すべてのデータは暗号化され、安全に保存されます。アクセス制御とバックアップ機能により、データの安全性と可用性を確保しています。',
    },
    {
      category: 'technical',
      question: 'APIは提供されていますか？',
      answer:
        'REST APIを提供しています。「設定」→「API設定」からAPIキーを取得し、プログラムから各機能にアクセスできます。詳細はAPIドキュメントをご覧ください。',
    },
    {
      category: 'troubleshooting',
      question: 'ログインできません',
      answer:
        'メールアドレスとパスワードが正しいか確認してください。パスワードをお忘れの場合は、ログイン画面の「パスワードを忘れた方」からリセットできます。',
    },
    {
      category: 'troubleshooting',
      question: 'アップロードしたファイルが表示されません',
      answer:
        'ファイルサイズやファイル形式を確認してください。大きなファイルは処理に時間がかかる場合があります。ページを再読み込みして、最新の状態を確認してください。',
    },
    {
      category: 'troubleshooting',
      question: '検索結果が表示されません',
      answer:
        'VectorDBにファイルがインデックスされているか確認してください。新規アップロードしたファイルは、インデックス処理完了後に検索可能になります。',
    },
  ];

  const categories = [
    { id: 'all', name: 'すべて' },
    { id: 'basic', name: '基本' },
    { id: 'usage', name: '使い方' },
    { id: 'vectordb', name: 'VectorDB' },
    { id: 'agent', name: 'AIエージェント' },
    { id: 'technical', name: '技術的な質問' },
    { id: 'troubleshooting', name: 'トラブルシューティング' },
  ];

  const resources = [
    {
      icon: Book,
      title: 'ドキュメント',
      description: '完全な機能ガイドとリファレンス',
      link: '#',
    },
    {
      icon: Video,
      title: 'チュートリアル動画',
      description: '動画で学ぶVectorMindStudio',
      link: '#',
    },
    {
      icon: Code,
      title: 'API リファレンス',
      description: '開発者向けAPIドキュメント',
      link: '#',
    },
    {
      icon: MessageCircle,
      title: 'コミュニティフォーラム',
      description: 'ユーザーと開発者のQ&A',
      link: '#',
    },
  ];

  const filteredFAQs = faqs.filter((faq) => {
    const matchesCategory =
      selectedCategory === 'all' || faq.category === selectedCategory;
    const matchesSearch =
      searchQuery === '' ||
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const toggleFAQ = (index: number) => {
    setExpandedFAQ(expandedFAQ === index ? null : index);
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ヘルプセンター</h1>
        <p className="mt-1 text-sm text-gray-600">
          よくある質問、ガイド、サポート情報
        </p>
      </div>

      {/* 検索バー */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="質問を検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
          />
        </div>
      </div>

      {/* カテゴリフィルター */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category.name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* FAQ セクション */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <HelpCircle className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">
                  よくある質問 (FAQ)
                </h2>
              </div>
            </div>
            <div className="divide-y divide-gray-200">
              {filteredFAQs.length === 0 ? (
                <div className="px-6 py-8 text-center text-gray-500">
                  該当する質問が見つかりませんでした
                </div>
              ) : (
                filteredFAQs.map((faq, index) => (
                  <div key={index} className="px-6 py-4">
                    <button
                      onClick={() => toggleFAQ(index)}
                      className="w-full flex items-start justify-between text-left"
                    >
                      <span className="font-medium text-gray-900 pr-4">
                        {faq.question}
                      </span>
                      {expandedFAQ === index ? (
                        <ChevronUp className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                      ) : (
                        <ChevronDown className="h-5 w-5 text-gray-400 flex-shrink-0 mt-0.5" />
                      )}
                    </button>
                    {expandedFAQ === index && (
                      <div className="mt-3 text-sm text-gray-600 leading-relaxed">
                        {faq.answer}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* リソース & サポート */}
        <div className="space-y-6">
          {/* リソース */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <Book className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">リソース</h2>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {resources.map((resource, index) => (
                <a
                  key={index}
                  href={resource.link}
                  className="flex items-start p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                >
                  <resource.icon className="h-5 w-5 text-blue-600 mr-3 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 group-hover:text-blue-600 flex items-center">
                      {resource.title}
                      <ExternalLink className="h-3 w-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="text-sm text-gray-600">
                      {resource.description}
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>

          {/* サポート連絡先 */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center">
                <MessageCircle className="h-5 w-5 text-gray-400 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">サポート</h2>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <div className="text-sm font-medium text-gray-900 mb-1">
                  メールサポート
                </div>
                <a
                  href="mailto:support@vectormindstudio.com"
                  className="flex items-center text-sm text-blue-600 hover:text-blue-700"
                >
                  <Mail className="h-4 w-4 mr-2" />
                  support@vectormindstudio.com
                </a>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="text-sm font-medium text-gray-900 mb-2">
                  営業時間
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>平日: 9:00 - 18:00 (JST)</div>
                  <div>土日祝日: お休み</div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <div className="text-sm font-medium text-gray-900 mb-2">
                  返信時間
                </div>
                <div className="text-sm text-gray-600">
                  通常1営業日以内に返信いたします
                </div>
              </div>
            </div>
          </div>

          {/* クイックスタートガイド */}
          <div className="bg-blue-50 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <FileText className="h-5 w-5 text-blue-600 mr-2" />
              <h3 className="font-medium text-blue-900">クイックスタート</h3>
            </div>
            <p className="text-sm text-blue-700 mb-4">
              VectorMindStudioを始めるための簡単なガイド
            </p>
            <ol className="space-y-2 text-sm text-blue-800">
              <li className="flex items-start">
                <span className="font-medium mr-2">1.</span>
                <span>ファイルをアップロードする</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium mr-2">2.</span>
                <span>VectorDBで検索を試す</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium mr-2">3.</span>
                <span>論文を新規作成する</span>
              </li>
              <li className="flex items-start">
                <span className="font-medium mr-2">4.</span>
                <span>AIエージェントを活用する</span>
              </li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Help;
