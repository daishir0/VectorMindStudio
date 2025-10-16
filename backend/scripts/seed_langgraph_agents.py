#!/usr/bin/env python3
"""
LangGraphエージェント初期データ投入スクリプト

7つのエージェント、25のインテント、5つのチェーンインテントを
データベースに登録します。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.infrastructure.repositories.langgraph_agent_repository import LangGraphAgentRepository
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 7つのエージェントデータ
AGENTS_DATA = [
    {
        "name": "outline_agent",
        "display_name": "アウトラインエージェント",
        "description": "論文のアウトライン（セクション構造）を管理します。セクションの作成・更新・削除・再編成を担当します。",
        "class_path": "app.services.agents.outline_agent.OutlineAgent",
        "config": {}
    },
    {
        "name": "writer_agent",
        "display_name": "ライターエージェント",
        "description": "論文のコンテンツを生成します。セクションの執筆、加筆、書き直しを担当します。",
        "class_path": "app.services.agents.writer_agent.WriterAgent",
        "config": {}
    },
    {
        "name": "analysis_agent",
        "display_name": "分析エージェント",
        "description": "論文の批判的分析を行います。構造分析、論理的一貫性チェック、改善提案を担当します。",
        "class_path": "app.services.agents.analysis_agent.AnalysisAgent",
        "config": {}
    },
    {
        "name": "discovery_agent",
        "display_name": "発見エージェント",
        "description": "新しい知識や研究テーマを発見します。ChromaDB検索、ギャップ分析を担当します。",
        "class_path": "app.services.agents.discovery_agent.DiscoveryAgent",
        "config": {}
    },
    {
        "name": "quality_agent",
        "display_name": "品質保証エージェント",
        "description": "論文の品質を評価します。品質チェック、コンプライアンス検証、倫理チェックを担当します。",
        "class_path": "app.services.agents.quality_agent.QualityAgent",
        "config": {}
    },
    {
        "name": "strategy_agent",
        "display_name": "戦略エージェント",
        "description": "研究戦略を立案します。研究方向性の提案、出版戦略、インパクト最大化を担当します。",
        "class_path": "app.services.agents.strategy_agent.StrategyAgent",
        "config": {}
    },
    {
        "name": "reference_agent",
        "display_name": "参考文献エージェント",
        "description": "参考文献を検索・管理します。関連文献の探索、類似コンテンツ検索を担当します。",
        "class_path": "app.services.agents.reference_retrieval_agent.ReferenceRetrievalAgent",
        "config": {}
    }
]


# 25の単一タスクインテントデータ
INTENTS_DATA = [
    # Outline Agent (5)
    {"intent_name": "create_section", "display_name": "セクション作成", "agent_name": "outline_agent",
     "description": "新しいセクションを作成", "example_query": "「Introductionセクションを作成してください」"},
    {"intent_name": "update_section", "display_name": "セクション更新", "agent_name": "outline_agent",
     "description": "既存セクションを更新", "example_query": "「Methodsセクションのタイトルを変更してください」"},
    {"intent_name": "delete_section", "display_name": "セクション削除", "agent_name": "outline_agent",
     "description": "セクションを削除", "example_query": "「Appendixセクションを削除してください」"},
    {"intent_name": "get_outline", "display_name": "アウトライン取得", "agent_name": "outline_agent",
     "description": "論文のアウトラインを取得", "example_query": "「現在の論文構成を教えてください」"},
    {"intent_name": "reorganize_structure", "display_name": "構造再編成", "agent_name": "outline_agent",
     "description": "セクション構造を再編成", "example_query": "「セクションの順序を変更してください」"},

    # Writer Agent (3)
    {"intent_name": "generate_content", "display_name": "コンテンツ生成", "agent_name": "writer_agent",
     "description": "コンテンツを生成", "example_query": "「Methodsセクションの内容を執筆してください」"},
    {"intent_name": "generate_draft", "display_name": "ドラフト生成", "agent_name": "writer_agent",
     "description": "ドラフトを生成", "example_query": "「全体のドラフトを作成してください」"},
    {"intent_name": "rewrite_content", "display_name": "コンテンツ書き直し", "agent_name": "writer_agent",
     "description": "コンテンツを書き直し", "example_query": "「Resultsセクションをよりわかりやすく書き直してください」"},

    # Analysis Agent (3)
    {"intent_name": "critical_analysis", "display_name": "批判的分析", "agent_name": "analysis_agent",
     "description": "批判的な分析を実施", "example_query": "「論文の論理展開を批判的に分析してください」"},
    {"intent_name": "structure_analysis", "display_name": "構造分析", "agent_name": "analysis_agent",
     "description": "論文構造を分析", "example_query": "「論文の構造を分析してください」"},
    {"intent_name": "consistency_check", "display_name": "一貫性チェック", "agent_name": "analysis_agent",
     "description": "論理的一貫性をチェック", "example_query": "「論文全体の一貫性を確認してください」"},
    {"intent_name": "analyze_structure", "display_name": "構造解析", "agent_name": "analysis_agent",
     "description": "構造を解析", "example_query": "「論文の構造的な問題点を洗い出してください」"},

    # Discovery Agent (3)
    {"intent_name": "gap_analysis", "display_name": "ギャップ分析", "agent_name": "discovery_agent",
     "description": "研究ギャップを分析", "example_query": "「既存研究とのギャップを分析してください」"},
    {"intent_name": "search_chromadb", "display_name": "ChromaDB検索", "agent_name": "discovery_agent",
     "description": "ChromaDBで関連資料を検索", "example_query": "「ChromaDBで『深層学習』を検索してください」"},
    {"intent_name": "novel_theme_discovery", "display_name": "新規テーマ発見", "agent_name": "discovery_agent",
     "description": "新しい研究テーマを発見", "example_query": "「新しい研究テーマを提案してください」"},

    # Quality Agent (3)
    {"intent_name": "quality_assessment", "display_name": "品質評価", "agent_name": "quality_agent",
     "description": "論文の品質を評価", "example_query": "「論文全体の品質を評価してください」"},
    {"intent_name": "compliance_check", "display_name": "コンプライアンスチェック", "agent_name": "quality_agent",
     "description": "コンプライアンスをチェック", "example_query": "「論文が学術基準に適合しているか確認してください」"},
    {"intent_name": "ethics_validation", "display_name": "倫理検証", "agent_name": "quality_agent",
     "description": "倫理的妥当性を検証", "example_query": "「倫理的な問題がないか確認してください」"},

    # Strategy Agent (3)
    {"intent_name": "research_strategy_planning", "display_name": "研究戦略立案", "agent_name": "strategy_agent",
     "description": "研究戦略を立案", "example_query": "「今後の研究方向性を提案してください」"},
    {"intent_name": "publication_strategy", "display_name": "出版戦略", "agent_name": "strategy_agent",
     "description": "出版戦略を提案", "example_query": "「最適な投稿先ジャーナルを提案してください」"},
    {"intent_name": "impact_maximization", "display_name": "インパクト最大化", "agent_name": "strategy_agent",
     "description": "研究インパクトを最大化", "example_query": "「研究の影響力を最大化する方法を提案してください」"},

    # Reference Agent (2)
    {"intent_name": "search_references", "display_name": "参考文献検索", "agent_name": "reference_agent",
     "description": "参考文献を検索", "example_query": "「関連する参考文献を探してください」"},
    {"intent_name": "find_similar_content", "display_name": "類似コンテンツ検索", "agent_name": "reference_agent",
     "description": "類似コンテンツを検索", "example_query": "「似たような論文を探してください」"},

    # Special Intents (2)
    {"intent_name": "needs_clarification", "display_name": "明確化要求", "agent_name": "outline_agent",
     "description": "ユーザーへの質問・明確化要求", "example_query": ""},
    {"intent_name": "error", "display_name": "エラー", "agent_name": "outline_agent",
     "description": "エラー応答", "example_query": ""}
]


# 5つのチェーンインテントデータ
CHAIN_INTENTS_DATA = [
    {
        "chain_name": "research_and_write",
        "display_name": "資料検索→執筆→品質チェック",
        "description": "ChromaDBで資料を検索し、それを基にコンテンツを生成し、品質チェックを行います。",
        "task_sequence": ["search_chromadb", "generate_content", "quality_assessment"],
        "example_query": "「ChromaDBで資料を探して、それを基に執筆してください」"
    },
    {
        "chain_name": "deep_analysis",
        "display_name": "構造分析→批判的分析→品質評価",
        "description": "論文の構造を分析し、批判的分析を行い、品質評価を実施します。",
        "task_sequence": ["structure_analysis", "critical_analysis", "quality_assessment"],
        "example_query": "「論文全体を詳しく分析してください」"
    },
    {
        "chain_name": "section_workflow",
        "display_name": "セクション作成→ドラフト生成→品質チェック",
        "description": "新しいセクションを作成し、ドラフトを生成し、品質チェックを行います。",
        "task_sequence": ["create_section", "generate_draft", "quality_assessment"],
        "example_query": "「新しいセクションを作成して、内容も書いてください」"
    },
    {
        "chain_name": "strategic_writing",
        "display_name": "ギャップ分析→戦略立案→コンテンツ生成",
        "description": "研究ギャップを分析し、戦略を立案し、コンテンツを生成します。",
        "task_sequence": ["gap_analysis", "research_strategy_planning", "generate_content"],
        "example_query": "「研究の方向性を検討して、執筆してください」"
    },
    {
        "chain_name": "reference_based_writing",
        "display_name": "参考文献検索→類似コンテンツ探索→コンテンツ生成",
        "description": "参考文献を検索し、類似コンテンツを探索し、それを基にコンテンツを生成します。",
        "task_sequence": ["search_references", "find_similar_content", "generate_content"],
        "example_query": "「参考文献を探して、それを基に執筆してください」"
    }
]


async def seed_data():
    """初期データを投入"""
    # データベース接続
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        repository = LangGraphAgentRepository(session)

        logger.info("🌱 LangGraphエージェント初期データ投入を開始します...")

        # 1. エージェントの登録
        logger.info("\n📦 エージェントを登録中...")
        agent_map = {}  # name -> agent オブジェクト
        for agent_data in AGENTS_DATA:
            # 既存チェック
            existing_agent = await repository.get_agent_by_name(agent_data["name"])
            if existing_agent:
                logger.info(f"   ⏭️  {agent_data['name']} は既に存在します（スキップ）")
                agent_map[agent_data["name"]] = existing_agent
                continue

            agent = await repository.create_agent(**agent_data)
            agent_map[agent_data["name"]] = agent
            logger.info(f"   ✅ {agent_data['name']} を作成しました")

        # 2. インテントの登録
        logger.info("\n📦 インテントを登録中...")
        for intent_data in INTENTS_DATA:
            # 既存チェック
            existing_intent = await repository.get_intent_by_name(intent_data["intent_name"])
            if existing_intent:
                logger.info(f"   ⏭️  {intent_data['intent_name']} は既に存在します（スキップ）")
                continue

            # エージェントIDを取得
            agent_name = intent_data.pop("agent_name")
            agent = agent_map.get(agent_name)
            if not agent:
                logger.warning(f"   ⚠️  {agent_name} が見つかりません（{intent_data['intent_name']}）")
                continue

            intent_data["agent_id"] = agent.id
            await repository.create_intent(**intent_data)
            logger.info(f"   ✅ {intent_data['intent_name']} を作成しました")

        # 3. チェーンインテントの登録
        logger.info("\n📦 チェーンインテントを登録中...")
        for chain_data in CHAIN_INTENTS_DATA:
            # 既存チェック
            existing_chain = await repository.get_chain_intent_by_name(chain_data["chain_name"])
            if existing_chain:
                logger.info(f"   ⏭️  {chain_data['chain_name']} は既に存在します（スキップ）")
                continue

            await repository.create_chain_intent(**chain_data)
            logger.info(f"   ✅ {chain_data['chain_name']} を作成しました")

        logger.info("\n✅ 初期データ投入が完了しました！")

        # サマリー表示
        all_agents = await repository.get_all_agents()
        all_intents = await repository.get_all_intents()
        all_chains = await repository.get_all_chain_intents()

        logger.info(f"\n📊 登録済みデータ:")
        logger.info(f"   - エージェント: {len(all_agents)}件")
        logger.info(f"   - インテント: {len(all_intents)}件")
        logger.info(f"   - チェーンインテント: {len(all_chains)}件")


if __name__ == "__main__":
    asyncio.run(seed_data())
