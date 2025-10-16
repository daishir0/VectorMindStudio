"""
Refineノード

品質検証で不合格となった場合に、改善の指示を
エージェントに伝えて再実行を促します。
"""

import logging
from typing import Dict, Any
from app.services.langgraph_agents.state import PaperDiscussionState

logger = logging.getLogger(__name__)


async def refine_node(state: PaperDiscussionState) -> Dict[str, Any]:
    """
    改善指示ノード

    Args:
        state: 現在の状態

    Returns:
        更新すべき状態フィールドの辞書
    """
    logger.info("🔧 Refine: 改善指示を準備中...")

    validation_feedback = state.get("validation_feedback", "")
    user_query = state.get("user_query", "")

    # チェーン継続フラグをチェック
    if validation_feedback == "__chain_continue__":
        logger.info("🔗 チェーン実行中: user_queryを変更せずにOrchestratorへ戻ります")
        return {
            "tool_calls": ["refine_node_chain_continue"],
        }

    # 通常の改善処理: 元のユーザー依頼に改善フィードバックを追加
    refined_query = f"""
【元の依頼】
{user_query}

【前回の実行結果】
{validation_feedback}

【改善点】
上記のフィードバックを踏まえて、より高品質な結果を生成してください。
"""

    logger.info(f"📝 改善指示:")
    logger.info(f"   {validation_feedback}")

    # user_queryを更新して、再度Orchestratorに戻す
    # （実際のルーティングはグラフ定義で行う）
    return {
        "user_query": refined_query,
        "tool_calls": ["refine_node"],
    }
