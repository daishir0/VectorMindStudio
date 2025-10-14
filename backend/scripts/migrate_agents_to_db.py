"""
既存エージェントをDBに移行するスクリプト

実行方法:
    python scripts/migrate_agents_to_db.py
"""
import asyncio
import sys
import os

# パス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

from app.infrastructure.database.models import Base
from app.infrastructure.repositories.agent_repository import AgentRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 既存エージェント定義（14種類）
AGENT_DEFINITIONS = [
    {
        "name": "OutlineAgent",
        "display_name": "アウトライン管理エージェント",
        "description": "論文の章・節・項構造を管理するエージェント",
        "category": "structure",
        "is_system": True,
        "is_active": True,
        "priority": 1,
        "system_prompt": "あなたは論文のアウトライン構造を管理する専門エージェントです。章・節・項の作成、更新、削除、移動、構造検証を担当します。",
        "user_prompt_template": "タスク: {task_type}\n\nパラメータ:\n{parameters}\n\n上記のタスクを実行してください。",
        "wake_words": [
            {"keyword": "アウトライン", "keyword_type": "partial", "priority": 1},
            {"keyword": "章", "keyword_type": "partial", "priority": 2},
            {"keyword": "節", "keyword_type": "partial", "priority": 2},
            {"keyword": "構造", "keyword_type": "partial", "priority": 3},
        ],
        "supported_task_types": ["create_section", "update_section", "delete_section", "move_section", "get_outline", "validate_structure"],
    },
    {
        "name": "WriterAgent",
        "display_name": "ライティングエージェント",
        "description": "セクションの文章を執筆・生成するエージェント",
        "category": "content_generation",
        "is_system": True,
        "is_active": True,
        "priority": 2,
        "system_prompt": "あなたは学術論文の執筆を専門とするライターエージェントです。指定されたセクションに対して、適切な文章を生成します。",
        "user_prompt_template": "セクション: {section_title}\n\n要件:\n{requirements}\n\n上記の要件に従って、セクションの文章を執筆してください。",
        "wake_words": [
            {"keyword": "執筆", "keyword_type": "partial", "priority": 1},
            {"keyword": "書いて", "keyword_type": "partial", "priority": 1},
            {"keyword": "文章", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["write_section", "rewrite_section", "expand_content"],
    },
    {
        "name": "EditingAgent",
        "display_name": "編集エージェント",
        "description": "文章の編集・改善を行うエージェント",
        "category": "content_refinement",
        "is_system": True,
        "is_active": True,
        "priority": 3,
        "system_prompt": "あなたは学術論文の編集を専門とするエージェントです。文章の改善、修正、調整を行います。",
        "user_prompt_template": "元の文章:\n{original_content}\n\n編集指示:\n{edit_instructions}\n\n上記の指示に従って文章を編集してください。",
        "wake_words": [
            {"keyword": "編集", "keyword_type": "partial", "priority": 1},
            {"keyword": "修正", "keyword_type": "partial", "priority": 1},
            {"keyword": "改善", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["edit_content", "proofread", "improve_clarity"],
    },
    {
        "name": "ReferenceAgent",
        "display_name": "参考文献エージェント",
        "description": "参考文献の管理・引用を担当するエージェント",
        "category": "reference_management",
        "is_system": True,
        "is_active": True,
        "priority": 4,
        "system_prompt": "あなたは学術論文の参考文献管理を専門とするエージェントです。引用文献の検索、管理、フォーマットを行います。",
        "user_prompt_template": "検索クエリ: {query}\n\n関連する参考文献を検索し、適切な引用形式で提示してください。",
        "wake_words": [
            {"keyword": "参考文献", "keyword_type": "partial", "priority": 1},
            {"keyword": "引用", "keyword_type": "partial", "priority": 1},
            {"keyword": "文献", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["search_references", "format_citation", "manage_bibliography"],
    },
    {
        "name": "QualityAgent",
        "display_name": "品質評価エージェント",
        "description": "論文の品質を評価・提案するエージェント",
        "category": "quality_assurance",
        "is_system": True,
        "is_active": True,
        "priority": 5,
        "system_prompt": "あなたは学術論文の品質評価を専門とするエージェントです。論文の構造、内容、表現を評価し、改善提案を行います。",
        "user_prompt_template": "評価対象:\n{content}\n\n上記の内容を評価し、改善点を提案してください。",
        "wake_words": [
            {"keyword": "品質", "keyword_type": "partial", "priority": 1},
            {"keyword": "評価", "keyword_type": "partial", "priority": 1},
            {"keyword": "チェック", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["evaluate_quality", "suggest_improvements", "check_consistency"],
    },
    {
        "name": "AnalysisAgent",
        "display_name": "分析エージェント",
        "description": "データや文章を分析するエージェント",
        "category": "analysis",
        "is_system": True,
        "is_active": True,
        "priority": 6,
        "system_prompt": "あなたはデータや文章を分析するエージェントです。統計的分析、トレンド分析、内容分析を行います。",
        "user_prompt_template": "分析対象:\n{data}\n\n分析タイプ: {analysis_type}\n\n上記のデータを分析し、結果を報告してください。",
        "wake_words": [
            {"keyword": "分析", "keyword_type": "partial", "priority": 1},
            {"keyword": "調査", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["analyze_data", "analyze_content", "identify_trends"],
    },
    {
        "name": "SummaryAgent",
        "display_name": "要約エージェント",
        "description": "文章を要約するエージェント",
        "category": "content_processing",
        "is_system": True,
        "is_active": True,
        "priority": 7,
        "system_prompt": "あなたは文章を要約するエージェントです。長い文章を簡潔にまとめます。",
        "user_prompt_template": "要約対象:\n{content}\n\n上記の文章を{max_words}文字以内で要約してください。",
        "wake_words": [
            {"keyword": "要約", "keyword_type": "partial", "priority": 1},
            {"keyword": "まとめ", "keyword_type": "partial", "priority": 1},
        ],
        "supported_task_types": ["summarize_content", "create_abstract"],
    },
    {
        "name": "DiscoveryAgent",
        "display_name": "発見エージェント",
        "description": "新しい知見や関連情報を発見するエージェント",
        "category": "research",
        "is_system": True,
        "is_active": True,
        "priority": 8,
        "system_prompt": "あなたは研究テーマに関連する新しい知見や情報を発見するエージェントです。",
        "user_prompt_template": "研究テーマ: {topic}\n\n関連する最新の研究や知見を発見してください。",
        "wake_words": [
            {"keyword": "発見", "keyword_type": "partial", "priority": 1},
            {"keyword": "探索", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["discover_insights", "find_related_research"],
    },
    {
        "name": "GenerationAgent",
        "display_name": "生成エージェント",
        "description": "コンテンツを生成するエージェント",
        "category": "content_generation",
        "is_system": True,
        "is_active": True,
        "priority": 9,
        "system_prompt": "あなたは様々なタイプのコンテンツを生成するエージェントです。",
        "user_prompt_template": "生成タイプ: {generation_type}\n\n要件:\n{requirements}\n\n上記の要件に従ってコンテンツを生成してください。",
        "wake_words": [
            {"keyword": "生成", "keyword_type": "partial", "priority": 1},
            {"keyword": "作成", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["generate_content", "create_outline", "generate_ideas"],
    },
    {
        "name": "OptimizationAgent",
        "display_name": "最適化エージェント",
        "description": "内容を最適化するエージェント",
        "category": "optimization",
        "is_system": True,
        "is_active": True,
        "priority": 10,
        "system_prompt": "あなたは論文の内容を最適化するエージェントです。文章の流れ、構造、表現を最適化します。",
        "user_prompt_template": "最適化対象:\n{content}\n\n上記の内容を最適化してください。",
        "wake_words": [
            {"keyword": "最適化", "keyword_type": "partial", "priority": 1},
        ],
        "supported_task_types": ["optimize_content", "improve_structure"],
    },
    {
        "name": "StrategyAgent",
        "display_name": "戦略エージェント",
        "description": "論文執筆の戦略を立案するエージェント",
        "category": "planning",
        "is_system": True,
        "is_active": True,
        "priority": 11,
        "system_prompt": "あなたは論文執筆の戦略を立案するエージェントです。執筆計画、アプローチ、優先順位を決定します。",
        "user_prompt_template": "論文テーマ: {topic}\n\n目標: {goals}\n\n効果的な執筆戦略を提案してください。",
        "wake_words": [
            {"keyword": "戦略", "keyword_type": "partial", "priority": 1},
            {"keyword": "計画", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["plan_strategy", "prioritize_tasks"],
    },
    {
        "name": "LogicValidatorAgent",
        "display_name": "論理検証エージェント",
        "description": "論理的整合性を検証するエージェント",
        "category": "validation",
        "is_system": True,
        "is_active": True,
        "priority": 12,
        "system_prompt": "あなたは論文の論理的整合性を検証するエージェントです。論理の飛躍、矛盾、不整合を検出します。",
        "user_prompt_template": "検証対象:\n{content}\n\n論理的整合性を検証し、問題点を指摘してください。",
        "wake_words": [
            {"keyword": "論理", "keyword_type": "partial", "priority": 1},
            {"keyword": "整合性", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["validate_logic", "check_consistency"],
    },
    {
        "name": "SectionQueryAgent",
        "display_name": "セクション照会エージェント",
        "description": "セクション情報を照会するエージェント",
        "category": "information_retrieval",
        "is_system": True,
        "is_active": True,
        "priority": 13,
        "system_prompt": "あなたはセクション情報を照会するエージェントです。特定のセクションの内容、メタデータを取得します。",
        "user_prompt_template": "照会対象: {query}\n\n上記のクエリに該当するセクション情報を取得してください。",
        "wake_words": [
            {"keyword": "照会", "keyword_type": "partial", "priority": 1},
            {"keyword": "検索", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["query_section", "get_section_info"],
    },
    {
        "name": "ReferenceRetrievalAgent",
        "display_name": "参考資料検索エージェント",
        "description": "アップロード資料から関連情報をベクトル検索で取得するエージェント",
        "category": "knowledge_retrieval",
        "is_system": True,
        "is_active": True,
        "priority": 14,
        "system_prompt": "あなたはアップロードされた資料から関連情報をベクトル検索で取得する専門エージェントです。ユーザーの検索クエリに基づいて、類似性の高い文章やファイルを見つけ出します。",
        "user_prompt_template": "検索クエリ: {query}\n\nユーザーID: {user_id}\n\n上記のクエリに関連する資料を検索し、適切な情報を提供してください。",
        "wake_words": [
            {"keyword": "参考資料", "keyword_type": "partial", "priority": 1},
            {"keyword": "資料検索", "keyword_type": "partial", "priority": 1},
            {"keyword": "資料", "keyword_type": "partial", "priority": 2},
            {"keyword": "アップロード", "keyword_type": "partial", "priority": 3},
            {"keyword": "ファイル検索", "keyword_type": "partial", "priority": 2},
        ],
        "supported_task_types": ["search_references", "find_similar_content", "retrieve_by_tags", "get_file_chunks"],
    },
]


async def migrate_agents():
    """エージェントをDBに移行"""
    # データベース接続
    database_url = "sqlite+aiosqlite:///./vectormind.db"
    engine = create_async_engine(database_url, echo=False)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        repository = AgentRepository(session)

        logger.info(f"Starting migration of {len(AGENT_DEFINITIONS)} agents...")

        for agent_def in AGENT_DEFINITIONS:
            try:
                # エージェントが既に存在するかチェック
                existing_agent = await repository.get_agent_by_name(agent_def["name"])

                if existing_agent:
                    logger.info(f"Agent {agent_def['name']} already exists, skipping...")
                    continue

                # エージェント作成
                wake_words = agent_def.pop("wake_words")
                supported_task_types = agent_def.pop("supported_task_types")

                agent = await repository.create_agent(**agent_def)
                logger.info(f"Created agent: {agent.name} ({agent.id})")

                # ウェイクワード作成
                for ww in wake_words:
                    wake_word = await repository.create_wake_word(
                        agent_id=agent.id,
                        **ww
                    )
                    logger.info(f"  - Created wake word: {wake_word.keyword}")

                # 能力定義作成
                capability = await repository.create_capability(
                    agent_id=agent.id,
                    capability_type="general",
                    description=agent_def["description"],
                    supported_task_types=supported_task_types
                )
                logger.info(f"  - Created capability with {len(supported_task_types)} task types")

            except Exception as e:
                logger.error(f"Failed to migrate agent {agent_def.get('name')}: {e}")
                raise

    await engine.dispose()
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_agents())
