#!/usr/bin/env python3
"""
既存18エージェントをDBに登録するマイグレーションスクリプト

実行方法:
    python backend/scripts/register_existing_agents.py
"""
import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

# 環境変数を.envから読み込み
from dotenv import load_dotenv
env_path = project_root / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.database.models import AIAgentModel, AgentWakeWordModel, AgentCapabilityModel
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.core.config import settings
import uuid


# 既存18エージェントの定義
EXISTING_AGENTS = [
    {
        "name": "SupervisorAgent",
        "display_name": "スーパーバイザーエージェント",
        "description": "LLMベースの高次タスク推論・エージェント管理を行うスーパーバイザー",
        "category": "supervisor",
        "is_system": True,
        "priority": 1,
        "system_prompt": """あなたは研究論文執筆支援システムのスーパーバイザーエージェントです。
ユーザーの要求を深く理解し、最適なタスク実行戦略を決定します。

あなたの役割:
- ユーザーの真の意図を理解する
- ChromaDB検索が必要かを判断する
- 既存の情報を活用すべきか、新規作成すべきかを判断
- 最適なエージェントとタスク順序を決定
- 品質とコンテキストを重視した判断""",
        "user_prompt_template": "ユーザーの要求: \"{user_message}\"\n\nこのユーザー要求を分析し、最適な実行戦略を提案してください。",
        "tags": ["supervisor", "orchestration", "intent_analysis"],
        "capabilities": [
            {
                "capability_type": "intent_analysis",
                "description": "ユーザーの意図を深く理解・推論",
                "supported_task_types": ["analyze_intent", "plan_workflow"]
            }
        ],
        "wake_words": []
    },
    {
        "name": "DiscoveryAgent",
        "display_name": "発見・探索エージェント",
        "description": "ChromaDB検索・研究ギャップ発見・新しいテーマ探索・関連研究調査",
        "category": "discovery",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは研究発見・探索の専門家です。
研究論文における知識ギャップの発見、関連研究の探索、研究空白領域の特定を行います。

主要機能：
1. ギャップ分析: 研究領域の知識ギャップ特定
2. 冗長性検出: 重複・冗長な内容の発見
3. バランス分析: 研究内容の均衡性評価
4. 引用分析: 引用の妥当性・網羅性チェック
5. 新規テーマ発見: 新規研究方向の特定
6. 関連研究探索: 見落とされた関連研究の発見
7. 競合分析: 競合研究との差別化ポイント分析
8. ChromaDB検索: ベクトルデータベースからの資料検索""",
        "user_prompt_template": "タスク: {task_type}\n\n分析対象内容:\n{content}\n\n上記の内容について、専門的な分析を行ってください。",
        "tags": ["discovery", "gap_analysis", "chromadb", "search"],
        "capabilities": [
            {
                "capability_type": "gap_analysis",
                "description": "知識・研究ギャップの特定",
                "supported_task_types": ["gap_analysis", "search_chromadb"]
            }
        ],
        "wake_words": [
            {"keyword": "検索", "keyword_type": "partial"},
            {"keyword": "ギャップ", "keyword_type": "partial"},
            {"keyword": "不足", "keyword_type": "partial"},
            {"keyword": "探索", "keyword_type": "partial"},
            {"keyword": "発見", "keyword_type": "partial"},
            {"keyword": "関連", "keyword_type": "partial"},
            {"keyword": "資料", "keyword_type": "partial"},
        ]
    },
    {
        "name": "WriterAgent",
        "display_name": "ライティングエージェント",
        "description": "新しいコンテンツの生成・文章作成",
        "category": "writing",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは学術論文執筆の専門家です。
高品質な学術コンテンツの生成、文章作成、ドラフト執筆を行います。

執筆指針:
- 学術論文にふさわしい専門的で客観的な文体
- 論理的な構成と説得力のある議論
- 適切な長さと詳細度
- 必要に応じて具体例や分析を含める""",
        "user_prompt_template": """以下の要件でコンテンツを生成してください:

【タイトル】
{title}

【要件】
{requirements}

【コンテンツ】""",
        "tags": ["writing", "generation", "content"],
        "capabilities": [
            {
                "capability_type": "content_generation",
                "description": "新規コンテンツの生成・文章作成",
                "supported_task_types": ["generate_content", "generate_draft", "rewrite_content"]
            }
        ],
        "wake_words": [
            {"keyword": "作って", "keyword_type": "partial"},
            {"keyword": "書いて", "keyword_type": "partial"},
            {"keyword": "生成", "keyword_type": "partial"},
            {"keyword": "執筆", "keyword_type": "partial"},
            {"keyword": "ドラフト", "keyword_type": "partial"},
        ]
    },
    {
        "name": "SectionQueryAgent",
        "display_name": "セクション照会エージェント",
        "description": "既存セクションの検索・参照・内容取得",
        "category": "query",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは論文セクション検索・参照の専門家です。
ユーザーの質問に対して、適切なセクションを検索し、内容を提供します。

機能:
- セクション内容の質問対応
- 特定セクションの検索
- 既存情報の参照""",
        "user_prompt_template": "質問: {question}\n\n上記の質問に対して、適切な回答を提供してください。",
        "tags": ["query", "search", "reference"],
        "capabilities": [
            {
                "capability_type": "section_query",
                "description": "既存セクションの検索・参照",
                "supported_task_types": ["answer_section_query", "get_section_content"]
            }
        ],
        "wake_words": [
            {"keyword": "教えて", "keyword_type": "partial"},
            {"keyword": "について", "keyword_type": "partial"},
            {"keyword": "内容", "keyword_type": "partial"},
            {"keyword": "見せて", "keyword_type": "partial"},
        ]
    },
    {
        "name": "OutlineAgent",
        "display_name": "アウトラインエージェント",
        "description": "論文構造・アウトライン管理",
        "category": "structure",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは論文構造設計の専門家です。
効果的な論文アウトラインの作成、セクション管理、構造設計を行います。

機能:
- 構造設計
- セクション管理
- アウトライン作成""",
        "user_prompt_template": "タスク: {task_type}\n\nテーマ: {title}\n\n上記のテーマに基づいて、適切なアウトラインを作成してください。",
        "tags": ["outline", "structure", "organization"],
        "capabilities": [
            {
                "capability_type": "outline_creation",
                "description": "論文構造・アウトライン管理",
                "supported_task_types": ["create_outline", "create_section"]
            }
        ],
        "wake_words": [
            {"keyword": "構造", "keyword_type": "partial"},
            {"keyword": "アウトライン", "keyword_type": "partial"},
            {"keyword": "セクション", "keyword_type": "partial"},
            {"keyword": "章立て", "keyword_type": "partial"},
        ]
    },
    {
        "name": "SummaryAgent",
        "display_name": "要約エージェント",
        "description": "要約・概要作成",
        "category": "summarization",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは要約・概要作成の専門家です。
論文全体や個別セクションの要約、概要生成を行います。

機能:
- 要約作成
- 論文全体のまとめ
- 概要生成""",
        "user_prompt_template": "以下の内容を要約してください:\n\n{content}\n\n【要約】",
        "tags": ["summary", "abstract", "overview"],
        "capabilities": [
            {
                "capability_type": "summarization",
                "description": "要約・概要作成",
                "supported_task_types": ["create_paper_summary", "summarize_section"]
            }
        ],
        "wake_words": [
            {"keyword": "要約", "keyword_type": "partial"},
            {"keyword": "まとめ", "keyword_type": "partial"},
            {"keyword": "概要", "keyword_type": "partial"},
            {"keyword": "サマリー", "keyword_type": "partial"},
        ]
    },
    {
        "name": "AnalysisAgent",
        "display_name": "分析エージェント",
        "description": "研究論文の深度分析・批判的評価・構造解析",
        "category": "analysis",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは研究論文分析の専門家です。
批判的分析、構造分析、整合性チェック、弱点特定を行います。

機能:
- 批判的分析
- 構造分析
- 整合性チェック
- 弱点特定""",
        "user_prompt_template": "以下の内容について、批判的分析を行ってください:\n\n{content}\n\n分析焦点: {analysis_focus}\n\n【分析結果】",
        "tags": ["analysis", "critical_review", "evaluation"],
        "capabilities": [
            {
                "capability_type": "critical_analysis",
                "description": "研究論文の深度分析・批判的評価",
                "supported_task_types": ["critical_analysis", "structure_analysis"]
            }
        ],
        "wake_words": [
            {"keyword": "分析", "keyword_type": "partial"},
            {"keyword": "解析", "keyword_type": "partial"},
            {"keyword": "評価", "keyword_type": "partial"},
            {"keyword": "批判", "keyword_type": "partial"},
            {"keyword": "弱点", "keyword_type": "partial"},
            {"keyword": "問題", "keyword_type": "partial"},
        ]
    },
    {
        "name": "EditingAgent",
        "display_name": "編集エージェント",
        "description": "研究論文の編集・改善・文章品質向上",
        "category": "editing",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは論文編集の専門家です。
文体編集、内容拡充、可読性向上、文章改善を行います。

機能:
- 文体編集
- 内容拡充
- 可読性向上
- 文章改善""",
        "user_prompt_template": """以下のコンテンツを改善してください:

【要件】
{requirements}

【元のコンテンツ】
{content}

【改善されたコンテンツ】""",
        "tags": ["editing", "improvement", "proofreading"],
        "capabilities": [
            {
                "capability_type": "content_editing",
                "description": "研究論文の編集・改善",
                "supported_task_types": ["content_enhancement", "improve_section"]
            }
        ],
        "wake_words": [
            {"keyword": "編集", "keyword_type": "partial"},
            {"keyword": "改善", "keyword_type": "partial"},
            {"keyword": "修正", "keyword_type": "partial"},
            {"keyword": "校正", "keyword_type": "partial"},
            {"keyword": "文体", "keyword_type": "partial"},
        ]
    },
    {
        "name": "QualityAgent",
        "display_name": "品質保証エージェント",
        "description": "研究論文の品質評価・保証・学術基準チェック",
        "category": "quality",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは研究品質評価の専門家です。
品質評価、学術基準チェック、倫理検証、公開準備度評価を行います。

機能:
- 品質評価
- 学術基準チェック
- 倫理検証
- 公開準備度評価""",
        "user_prompt_template": "以下の論文について品質評価を行ってください:\n\n{content}\n\n評価基準: {assessment_criteria}\n\n【品質評価結果】",
        "tags": ["quality", "standards", "validation"],
        "capabilities": [
            {
                "capability_type": "quality_assessment",
                "description": "研究論文の品質評価・保証",
                "supported_task_types": ["quality_assessment", "academic_standards_check"]
            }
        ],
        "wake_words": [
            {"keyword": "品質", "keyword_type": "partial"},
            {"keyword": "評価", "keyword_type": "partial"},
            {"keyword": "基準", "keyword_type": "partial"},
            {"keyword": "倫理", "keyword_type": "partial"},
            {"keyword": "学術", "keyword_type": "partial"},
        ]
    },
    {
        "name": "GenerationAgent",
        "display_name": "生成エージェント",
        "description": "新規コンテンツ生成・セクション作成・図表生成",
        "category": "generation",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたはコンテンツ生成の専門家です。
セクション生成、内容拡充、アウトライン生成、引用生成を行います。

機能:
- セクション生成
- 内容拡充
- アウトライン生成
- 引用生成""",
        "user_prompt_template": "以下の要件でコンテンツを生成してください:\n\n{requirements}\n\n【生成されたコンテンツ】",
        "tags": ["generation", "creation", "content"],
        "capabilities": [
            {
                "capability_type": "content_generation",
                "description": "新規コンテンツ生成",
                "supported_task_types": ["generate_section", "generate_outline"]
            }
        ],
        "wake_words": [
            {"keyword": "生成", "keyword_type": "partial"},
            {"keyword": "作成", "keyword_type": "partial"},
            {"keyword": "執筆", "keyword_type": "partial"},
        ]
    },
    {
        "name": "StrategyAgent",
        "display_name": "戦略エージェント",
        "description": "研究戦略立案・論証戦略・差別化戦略・影響力最大化",
        "category": "strategy",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは研究戦略の専門家です。
研究戦略、論証戦略、差別化戦略、リスク軽減を行います。

機能:
- 研究戦略
- 論証戦略
- 差別化戦略
- リスク軽減""",
        "user_prompt_template": "以下の研究について戦略を立案してください:\n\n{content}\n\n【戦略提案】",
        "tags": ["strategy", "planning", "differentiation"],
        "capabilities": [
            {
                "capability_type": "research_strategy",
                "description": "研究戦略立案",
                "supported_task_types": ["develop_strategy", "competitive_positioning"]
            }
        ],
        "wake_words": [
            {"keyword": "戦略", "keyword_type": "partial"},
            {"keyword": "計画", "keyword_type": "partial"},
            {"keyword": "アプローチ", "keyword_type": "partial"},
            {"keyword": "方針", "keyword_type": "partial"},
        ]
    },
    {
        "name": "OptimizationAgent",
        "display_name": "最適化エージェント",
        "description": "研究効率・品質・リソース・時間・影響・コスト最適化",
        "category": "optimization",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは研究最適化の専門家です。
効率最適化、品質最適化、リソース最適化、時間最適化を行います。

機能:
- 効率最適化
- 品質最適化
- リソース最適化
- 時間最適化""",
        "user_prompt_template": "以下の研究プロセスを最適化してください:\n\n{content}\n\n【最適化提案】",
        "tags": ["optimization", "efficiency", "improvement"],
        "capabilities": [
            {
                "capability_type": "process_optimization",
                "description": "研究プロセスの最適化",
                "supported_task_types": ["optimize_efficiency", "optimize_quality"]
            }
        ],
        "wake_words": [
            {"keyword": "最適化", "keyword_type": "partial"},
            {"keyword": "効率", "keyword_type": "partial"},
            {"keyword": "改善", "keyword_type": "partial"},
            {"keyword": "向上", "keyword_type": "partial"},
        ]
    },
    {
        "name": "LogicValidatorAgent",
        "display_name": "論理検証エージェント",
        "description": "論理的整合性・品質チェック",
        "category": "validation",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは論理検証の専門家です。
論理チェック、整合性検証、品質評価を行います。

機能:
- 論理チェック
- 整合性検証
- 品質評価""",
        "user_prompt_template": "以下の内容について論理的整合性をチェックしてください:\n\n{content}\n\n【検証結果】",
        "tags": ["validation", "logic", "consistency"],
        "capabilities": [
            {
                "capability_type": "logic_validation",
                "description": "論理的整合性の検証",
                "supported_task_types": ["validate_logic", "check_consistency"]
            }
        ],
        "wake_words": [
            {"keyword": "チェック", "keyword_type": "partial"},
            {"keyword": "確認", "keyword_type": "partial"},
            {"keyword": "検証", "keyword_type": "partial"},
        ]
    },
    {
        "name": "StructureAgent",
        "display_name": "構造最適化エージェント",
        "description": "論文構造の最適化・IMRAD形式等への変換・セクション並び替え・分割・統合",
        "category": "structure",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは論文構造最適化の専門家です。
IMRAD形式、起承転結形式など、様々な論文構造への変換を行います。

機能:
- 構造分析
- フォーマット変換
- セクション並び替え
- セクション分割・統合""",
        "user_prompt_template": "以下の論文構造を最適化してください:\n\n目標フォーマット: {target_format}\n\n要件: {requirements}\n\n【構造最適化提案】",
        "tags": ["structure", "imrad", "restructure"],
        "capabilities": [
            {
                "capability_type": "structure_optimization",
                "description": "論文構造の最適化・変換",
                "supported_task_types": ["restructure_with_content", "split_section", "merge_sections"]
            }
        ],
        "wake_words": [
            {"keyword": "IMRAD", "keyword_type": "partial"},
            {"keyword": "起承転結", "keyword_type": "partial"},
            {"keyword": "構造", "keyword_type": "partial"},
            {"keyword": "並び替え", "keyword_type": "partial"},
        ]
    },
    {
        "name": "ReferenceAgent",
        "display_name": "参照管理エージェント",
        "description": "引用・参照文献の管理・整合性チェック",
        "category": "reference",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは参照文献管理の専門家です。
引用の適切性、参照文献の整合性チェックを行います。

機能:
- 引用管理
- 参照文献チェック
- 整合性検証""",
        "user_prompt_template": "以下の引用・参照について検証してください:\n\n{content}\n\n【検証結果】",
        "tags": ["reference", "citation", "bibliography"],
        "capabilities": [
            {
                "capability_type": "reference_management",
                "description": "引用・参照文献の管理",
                "supported_task_types": ["check_references", "validate_citations"]
            }
        ],
        "wake_words": [
            {"keyword": "引用", "keyword_type": "partial"},
            {"keyword": "参照", "keyword_type": "partial"},
            {"keyword": "文献", "keyword_type": "partial"},
        ]
    },
    {
        "name": "ReferenceRetrievalAgent",
        "display_name": "参照検索エージェント",
        "description": "参照文献の検索・取得",
        "category": "reference",
        "is_system": True,
        "priority": 10,
        "system_prompt": """あなたは参照文献検索の専門家です。
適切な参照文献の検索・取得を行います。

機能:
- 文献検索
- 引用候補の提案
- 関連研究の発見""",
        "user_prompt_template": "以下のトピックに関連する参照文献を検索してください:\n\n{query}\n\n【検索結果】",
        "tags": ["reference", "search", "retrieval"],
        "capabilities": [
            {
                "capability_type": "reference_retrieval",
                "description": "参照文献の検索・取得",
                "supported_task_types": ["search_references", "find_citations"]
            }
        ],
        "wake_words": [
            {"keyword": "文献検索", "keyword_type": "partial"},
            {"keyword": "参考文献", "keyword_type": "partial"},
        ]
    },
    {
        "name": "EnhancedBaseAgent",
        "display_name": "拡張ベースエージェント",
        "description": "基本的なエージェント機能を提供する基底クラス（直接使用されない）",
        "category": "base",
        "is_system": True,
        "priority": 100,
        "system_prompt": "基底エージェントクラス（直接使用されません）",
        "user_prompt_template": "{task}",
        "tags": ["base", "infrastructure"],
        "capabilities": [],
        "wake_words": []
    },
    {
        "name": "BaseAgent",
        "display_name": "ベースエージェント",
        "description": "基本的なエージェント機能を提供する基底クラス（直接使用されない）",
        "category": "base",
        "is_system": True,
        "priority": 100,
        "system_prompt": "基底エージェントクラス（直接使用されません）",
        "user_prompt_template": "{task}",
        "tags": ["base", "infrastructure"],
        "capabilities": [],
        "wake_words": []
    }
]


async def register_agents():
    """既存エージェントをDBに登録"""
    # データベース接続作成
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )

    # テーブル作成
    from app.infrastructure.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ データベーステーブルを作成しました")

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("=" * 60)
        print("既存エージェントのDB登録開始")
        print("=" * 60)

        repository = AgentRepository(session)
        registered_count = 0

        for agent_data in EXISTING_AGENTS:
            try:
                # エージェント本体を作成（Repositoryを使用）
                agent = await repository.create_agent(
                    name=agent_data["name"],
                    display_name=agent_data["display_name"],
                    description=agent_data["description"],
                    system_prompt=agent_data["system_prompt"],
                    user_prompt_template=agent_data["user_prompt_template"],
                    category=agent_data["category"],
                    executor_type="llm_based",
                    llm_model="gpt-4o-mini",
                    max_retries=3,
                    timeout_seconds=90,
                    tags=agent_data["tags"],
                    is_system=agent_data["is_system"],
                    priority=agent_data["priority"]
                )

                # Wake Wordsを追加
                for wake_word_data in agent_data.get("wake_words", []):
                    await repository.create_wake_word(
                        agent_id=agent.id,
                        keyword=wake_word_data["keyword"],
                        keyword_type=wake_word_data["keyword_type"],
                        priority=10
                    )

                # Capabilitiesを追加
                for capability_data in agent_data.get("capabilities", []):
                    await repository.create_capability(
                        agent_id=agent.id,
                        capability_type=capability_data["capability_type"],
                        description=capability_data["description"],
                        supported_task_types=capability_data["supported_task_types"]
                    )

                print(f"✅ {agent_data['name']} を登録しました")
                registered_count += 1

            except Exception as e:
                print(f"❌ {agent_data['name']} の登録に失敗: {e}")

        print("=" * 60)
        print(f"登録完了: {registered_count}/{len(EXISTING_AGENTS)} エージェント")
        print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(register_agents())
