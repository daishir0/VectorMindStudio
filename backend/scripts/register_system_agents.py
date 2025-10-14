"""
既存14エージェントをDBに登録するスクリプト

システムエージェントとして登録し、class_pathを設定してcode_basedで動作させる
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.database.session import engine, AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 既存14エージェントの定義
SYSTEM_AGENTS = [
    {
        "name": "outline",
        "display_name": "OutlineAgent",
        "description": "論文のセクション構造を管理。セクション作成、再構成、階層更新を担当",
        "category": "writing",
        "class_path": "app.services.agents.outline_agent:OutlineAgent",
        "priority": 1,
        "system_prompt": "You are an outline agent responsible for managing paper section structures.",
        "user_prompt_template": "Task: {task_description}\\nContext: {context}",
    },
    {
        "name": "writer",
        "display_name": "WriterAgent",
        "description": "論文コンテンツの生成と編集。ドラフト作成、コンテンツ更新、拡張、文体改善を担当",
        "category": "writing",
        "class_path": "app.services.agents.writer_agent:WriterAgent",
        "priority": 2,
        "system_prompt": "You are a writer agent responsible for generating and editing academic content.",
        "user_prompt_template": "Task: {task_description}\\nSection: {section_info}\\nRequirements: {requirements}",
    },
    {
        "name": "logic_validator",
        "display_name": "LogicValidatorAgent",
        "description": "論理構造と論証の妥当性を検証。構造検証、論証検証、一貫性チェックを担当",
        "category": "quality",
        "class_path": "app.services.agents.logic_validator_agent:LogicValidatorAgent",
        "priority": 5,
        "system_prompt": "You are a logic validation agent responsible for checking argument validity.",
        "user_prompt_template": "Task: {task_description}\\nContent: {content}\\nCriteria: {criteria}",
    },
    {
        "name": "summary",
        "display_name": "SummaryAgent",
        "description": "要約と抄録の作成。セクション要約、論文抄録、セクション分析を担当",
        "category": "analysis",
        "class_path": "app.services.agents.summary_agent:SummaryAgent",
        "priority": 6,
        "system_prompt": "You are a summary agent responsible for creating concise summaries.",
        "user_prompt_template": "Task: {task_description}\\nContent: {content}\\nLength: {length}",
    },
    {
        "name": "reference",
        "display_name": "ReferenceAgent",
        "description": "文献管理と引用。文献検索、引用検証、引用追加を担当",
        "category": "search",
        "class_path": "app.services.agents.reference_agent:ReferenceAgent",
        "priority": 4,
        "system_prompt": "You are a reference agent responsible for managing citations.",
        "user_prompt_template": "Task: {task_description}\\nContext: {context}\\nCitation Style: {style}",
    },
    {
        "name": "discovery",
        "display_name": "DiscoveryAgent",
        "description": "論文の発見と分析。関連論文の発見、トピック探索、文献レビューを担当",
        "category": "search",
        "class_path": "app.services.agents.discovery_agent:DiscoveryAgent",
        "priority": 3,
        "system_prompt": "You are a discovery agent responsible for finding relevant research papers.",
        "user_prompt_template": "Task: {task_description}\\nKeywords: {keywords}\\nFilters: {filters}",
    },
    {
        "name": "analysis",
        "display_name": "AnalysisAgent",
        "description": "論文内容の深い分析。データ分析、トレンド分析、比較分析を担当",
        "category": "analysis",
        "class_path": "app.services.agents.analysis_agent:AnalysisAgent",
        "priority": 7,
        "system_prompt": "You are an analysis agent responsible for deep content analysis.",
        "user_prompt_template": "Task: {task_description}\\nData: {data}\\nAnalysis Type: {analysis_type}",
    },
    {
        "name": "quality",
        "display_name": "QualityAgent",
        "description": "品質管理と改善提案。品質チェック、改善提案、スコアリングを担当",
        "category": "quality",
        "class_path": "app.services.agents.quality_agent:QualityAgent",
        "priority": 8,
        "system_prompt": "You are a quality agent responsible for ensuring content quality.",
        "user_prompt_template": "Task: {task_description}\\nContent: {content}\\nQuality Criteria: {criteria}",
    },
    {
        "name": "editing",
        "display_name": "EditingAgent",
        "description": "文章の編集と校正。文法チェック、スタイル改善、校正を担当",
        "category": "quality",
        "class_path": "app.services.agents.editing_agent:EditingAgent",
        "priority": 9,
        "system_prompt": "You are an editing agent responsible for proofreading and style improvement.",
        "user_prompt_template": "Task: {task_description}\\nContent: {content}\\nEditing Focus: {focus}",
    },
    {
        "name": "structure",
        "display_name": "StructureAgent",
        "description": "論文構造の最適化。構造分析、構造改善、セクション関係の管理を担当",
        "category": "writing",
        "class_path": "app.services.agents.structure_agent:StructureAgent",
        "priority": 10,
        "system_prompt": "You are a structure agent responsible for optimizing paper structure.",
        "user_prompt_template": "Task: {task_description}\\nCurrent Structure: {structure}\\nGoal: {goal}",
    },
    {
        "name": "strategy",
        "display_name": "StrategyAgent",
        "description": "執筆戦略の立案。執筆計画、戦略提案、進捗管理を担当",
        "category": "analysis",
        "class_path": "app.services.agents.strategy_agent:StrategyAgent",
        "priority": 11,
        "system_prompt": "You are a strategy agent responsible for planning writing strategies.",
        "user_prompt_template": "Task: {task_description}\\nGoal: {goal}\\nConstraints: {constraints}",
    },
    {
        "name": "optimization",
        "display_name": "OptimizationAgent",
        "description": "コンテンツの最適化。文章最適化、構造最適化、全体最適化を担当",
        "category": "quality",
        "class_path": "app.services.agents.optimization_agent:OptimizationAgent",
        "priority": 12,
        "system_prompt": "You are an optimization agent responsible for optimizing content.",
        "user_prompt_template": "Task: {task_description}\\nContent: {content}\\nOptimization Goals: {goals}",
    },
    {
        "name": "generation",
        "display_name": "GenerationAgent",
        "description": "コンテンツの自動生成。テンプレートベース生成、AIアシスト生成を担当",
        "category": "writing",
        "class_path": "app.services.agents.generation_agent:GenerationAgent",
        "priority": 13,
        "system_prompt": "You are a generation agent responsible for automated content generation.",
        "user_prompt_template": "Task: {task_description}\\nTemplate: {template}\\nParameters: {parameters}",
    },
    {
        "name": "reference_retrieval",
        "display_name": "ReferenceRetrievalAgent",
        "description": "文献情報の詳細取得。文献詳細取得、メタデータ抽出、アクセス情報を担当",
        "category": "search",
        "class_path": "app.services.agents.reference_retrieval_agent:ReferenceRetrievalAgent",
        "priority": 14,
        "system_prompt": "You are a reference retrieval agent responsible for fetching detailed reference information.",
        "user_prompt_template": "Task: {task_description}\\nReference ID: {reference_id}\\nFields: {fields}",
    },
]


async def register_agents():
    """システムエージェントをDBに登録"""
    async with AsyncSessionLocal() as session:
        repo = AgentRepository(session)

        logger.info(f"Registering {len(SYSTEM_AGENTS)} system agents...")

        registered_count = 0
        updated_count = 0
        skipped_count = 0

        for agent_data in SYSTEM_AGENTS:
            try:
                # 既存チェック
                existing_agent = await repo.get_agent_by_name(agent_data["name"])

                if existing_agent:
                    # 既に登録済みの場合は更新
                    logger.info(f"Agent '{agent_data['name']}' already exists, updating...")

                    update_data = {
                        "display_name": agent_data["display_name"],
                        "description": agent_data["description"],
                        "category": agent_data["category"],
                        "priority": agent_data["priority"],
                        "class_path": agent_data["class_path"],
                        "is_system": True,
                        "is_deletable": False,
                        "executor_type": "code_based",
                        "system_prompt": agent_data["system_prompt"],
                        "user_prompt_template": agent_data["user_prompt_template"],
                    }

                    await repo.update_agent(existing_agent.id, update_data)
                    updated_count += 1
                    logger.info(f"✓ Updated: {agent_data['display_name']}")
                else:
                    # 新規登録
                    agent = await repo.create_agent(
                        name=agent_data["name"],
                        display_name=agent_data["display_name"],
                        description=agent_data["description"],
                        system_prompt=agent_data["system_prompt"],
                        user_prompt_template=agent_data["user_prompt_template"],
                        category=agent_data["category"],
                        priority=agent_data["priority"],
                        class_path=agent_data["class_path"],
                        is_system=True,
                        is_deletable=False,
                        is_active=True,
                        executor_type="code_based",
                        llm_model=None,
                        max_retries=3,
                        timeout_seconds=90,
                        user_id=None
                    )
                    registered_count += 1
                    logger.info(f"✓ Registered: {agent_data['display_name']} (ID: {agent.id})")

            except Exception as e:
                logger.error(f"✗ Failed to register {agent_data['name']}: {e}")
                skipped_count += 1

        logger.info("=" * 60)
        logger.info(f"Registration completed:")
        logger.info(f"  - Newly registered: {registered_count}")
        logger.info(f"  - Updated: {updated_count}")
        logger.info(f"  - Skipped (errors): {skipped_count}")
        logger.info(f"  - Total processed: {len(SYSTEM_AGENTS)}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(register_agents())
