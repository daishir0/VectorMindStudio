"""
論文ディスカッショングラフ

LangGraphを使用した論文執筆支援のワークフロー定義
"""

import logging
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.langgraph_agents.state import PaperDiscussionState
from app.services.langgraph_agents.nodes import (
    orchestrator_node,
    create_agent_node,
    validation_node,
    response_node,
    refine_node,
)

# 既存エージェントのインポート
from app.services.agents.outline_agent import OutlineAgent
from app.services.agents.writer_agent import WriterAgent
from app.services.agents.analysis_agent import AnalysisAgent
from app.services.agents.discovery_agent import DiscoveryAgent
from app.services.agents.quality_agent import QualityAgent
from app.services.agents.strategy_agent import StrategyAgent
from app.services.agents.reference_retrieval_agent import ReferenceRetrievalAgent

# Sequential Chain定数のインポート
from app.services.langgraph_agents.constants import CHAIN_INTENTS

logger = logging.getLogger(__name__)


def create_paper_discussion_graph(session: AsyncSession):
    """
    論文ディスカッショングラフを作成

    Args:
        session: データベースセッション

    Returns:
        コンパイル済みのLangGraphアプリケーション
    """
    logger.info("🏗️ LangGraphワークフローを構築中...")

    # 既存エージェントのインスタンス化（各エージェントはsessionのみ受け取る）
    outline_agent = OutlineAgent(session)
    writer_agent = WriterAgent(session)
    analysis_agent = AnalysisAgent(session)
    discovery_agent = DiscoveryAgent(session)
    quality_agent = QualityAgent(session)
    strategy_agent = StrategyAgent(session)
    reference_agent = ReferenceRetrievalAgent(session)

    # エージェントをLangGraphノードに変換
    outline_node = create_agent_node(outline_agent, "outline_agent")
    writer_node = create_agent_node(writer_agent, "writer_agent")
    analysis_node = create_agent_node(analysis_agent, "analysis_agent")
    discovery_node = create_agent_node(discovery_agent, "discovery_agent")
    quality_node = create_agent_node(quality_agent, "quality_agent")
    strategy_node = create_agent_node(strategy_agent, "strategy_agent")
    reference_node = create_agent_node(reference_agent, "reference_agent")

    # グラフビルダー作成
    workflow = StateGraph(PaperDiscussionState)

    # ノード追加
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("outline_agent", outline_node)
    workflow.add_node("writer_agent", writer_node)
    workflow.add_node("analysis_agent", analysis_node)
    workflow.add_node("discovery_agent", discovery_node)
    workflow.add_node("quality_agent", quality_node)
    workflow.add_node("strategy_agent", strategy_node)
    workflow.add_node("reference_agent", reference_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("response", response_node)
    workflow.add_node("refine", refine_node)

    # エントリーポイント
    workflow.set_entry_point("orchestrator")

    # Orchestrator → エージェントへの条件付きエッジ
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "outline_agent": "outline_agent",
            "writer_agent": "writer_agent",
            "analysis_agent": "analysis_agent",
            "discovery_agent": "discovery_agent",
            "quality_agent": "quality_agent",
            "strategy_agent": "strategy_agent",
            "reference_agent": "reference_agent",
            "response": "response",  # 直接応答（エージェント不要）
        }
    )

    # 各エージェント → Validation
    for agent in ["outline_agent", "writer_agent", "analysis_agent",
                  "discovery_agent", "quality_agent", "strategy_agent", "reference_agent"]:
        workflow.add_edge(agent, "validation")

    # Validation → Response/Refineへの条件付きエッジ
    workflow.add_conditional_edges(
        "validation",
        route_validation,
        {
            "response": "response",
            "refine": "refine",
        }
    )

    # Refine → Orchestrator（ループバック）
    workflow.add_edge("refine", "orchestrator")

    # Response → 終了
    workflow.add_edge("response", END)

    # コンパイル
    app = workflow.compile()

    logger.info("✅ LangGraphワークフロー構築完了")

    return app


def route_to_agent(state: PaperDiscussionState) -> str:
    """
    Orchestratorが決定したintentに基づいて次のノードを選択

    Sequential Chain（複数エージェント連携）にも対応しており、
    task_chainが設定されている場合は順次実行します。

    Args:
        state: 現在の状態

    Returns:
        次のノード名
    """
    intent = state.get("intent", "")
    task_chain = state.get("task_chain", [])
    current_task_index = state.get("current_task_index", 0)

    # インテントからエージェントへのマッピング
    intent_to_agent = {
        # Outline Agent
        "create_section": "outline_agent",
        "update_section": "outline_agent",
        "delete_section": "outline_agent",
        "get_outline": "outline_agent",
        "reorganize_structure": "outline_agent",

        # Writer Agent
        "generate_content": "writer_agent",
        "generate_draft": "writer_agent",
        "rewrite_content": "writer_agent",

        # Analysis Agent
        "critical_analysis": "analysis_agent",
        "structure_analysis": "analysis_agent",
        "consistency_check": "analysis_agent",
        "analyze_structure": "analysis_agent",

        # Discovery Agent
        "gap_analysis": "discovery_agent",
        "search_chromadb": "discovery_agent",
        "novel_theme_discovery": "discovery_agent",

        # Quality Agent
        "quality_assessment": "quality_agent",
        "compliance_check": "quality_agent",
        "ethics_validation": "quality_agent",

        # Strategy Agent
        "research_strategy_planning": "strategy_agent",
        "publication_strategy": "strategy_agent",
        "impact_maximization": "strategy_agent",

        # Reference Agent
        "search_references": "reference_agent",
        "find_similar_content": "reference_agent",

        # Special Intents
        "needs_clarification": "response",  # ユーザーガイダンスを直接返す
        "error": "response",  # エラーは直接応答
    }

    # ===== チェーン処理：既にチェーン実行中の場合 =====
    if task_chain and len(task_chain) > 0:
        # 次のタスクがあるかチェック
        if current_task_index < len(task_chain):
            next_task = task_chain[current_task_index]
            selected_agent = intent_to_agent.get(next_task, "response")

            logger.info(
                f"🔗 チェーン実行中: "
                f"タスク {current_task_index + 1}/{len(task_chain)} - "
                f"{next_task} → {selected_agent}"
            )

            return selected_agent
        else:
            # チェーン完了 → 応答へ
            logger.info(f"✅ チェーン完了: {len(task_chain)}タスク実行済み")
            return "response"

    # ===== チェーン開始：intentがCHAIN_INTENTSに含まれる場合 =====
    if intent in CHAIN_INTENTS:
        task_chain = CHAIN_INTENTS[intent]
        first_task = task_chain[0]
        selected_agent = intent_to_agent.get(first_task, "response")

        logger.info(
            f"🔗 チェーン開始: {intent} → "
            f"{len(task_chain)}タスク [{', '.join(task_chain)}]"
        )
        logger.info(
            f"🎯 最初のタスク: {first_task} → {selected_agent}"
        )

        return selected_agent

    # ===== 通常の単一インテント処理 =====
    selected_agent = intent_to_agent.get(intent, "response")

    logger.info(f"🎯 ルーティング: {intent} → {selected_agent}")

    return selected_agent


def route_validation(state: PaperDiscussionState) -> str:
    """
    品質チェック結果に基づいてループバックか終了かを判定

    Args:
        state: 現在の状態

    Returns:
        次のノード名
    """
    validation_result = state.get("validation_result", "ok")
    loop_count = state.get("loop_count", 0)
    max_loops = state.get("max_loops", 3)

    logger.info(f"🔍 Validation結果: {validation_result} (ループ回数: {loop_count}/{max_loops})")

    # 品質OK、または最大ループ回数到達 → 終了
    if validation_result == "ok" or loop_count >= max_loops:
        return "response"

    # 改善が必要 → Refineノードへ
    elif validation_result == "needs_refinement":
        return "refine"

    # 情報不足（現在は未実装） → とりあえず終了
    else:
        return "response"
