"""
Validationノード

エージェントの出力結果を検証し、品質が十分か、
追加の処理が必要かを判定します。
"""

import logging
from typing import Dict, Any
from app.services.langgraph_agents.state import PaperDiscussionState

logger = logging.getLogger(__name__)


async def validation_node(state: PaperDiscussionState) -> Dict[str, Any]:
    """
    エージェント出力の品質検証ノード

    Args:
        state: 現在の状態

    Returns:
        更新すべき状態フィールドの辞書
    """
    logger.info("🔍 Validation: エージェント出力を検証中...")

    agent_output = state.get("agent_output", {})
    success = agent_output.get("success", False)
    loop_count = state.get("loop_count", 0)
    max_loops = state.get("max_loops", 3)

    # チェーン実行中の場合：中間タスクは品質チェックをスキップ
    task_chain = state.get("task_chain", [])
    current_task_index = state.get("current_task_index", 0)

    if task_chain and len(task_chain) > 0:
        # 最後のタスクでない場合は、品質チェックをスキップして次のタスクへ
        if current_task_index < len(task_chain):
            logger.info(
                f"🔗 チェーン実行中: 中間タスク ({current_task_index}/{len(task_chain)}) "
                f"のため品質チェックをスキップして次のタスクへ進みます"
            )
            # needs_refinementを返してRefine → Orchestratorへ
            # （実際には品質問題ではなく、チェーン継続のため）
            return {
                "validation_result": "needs_refinement",
                "validation_feedback": "__chain_continue__",  # チェーン継続フラグ
            }
        else:
            logger.info(f"🔗 チェーン最終タスク: 品質チェックを実行します")

    # エージェント実行が失敗した場合
    if not success:
        error_msg = agent_output.get("message", "不明なエラー")
        logger.warning(f"⚠️ エージェント実行失敗: {error_msg}")

        # エージェント失敗時は即座にループを抜けてエラー応答を返す
        # （無限ループを防ぐため、リトライせずに終了）
        logger.info(f"❌ エージェント失敗により処理を終了します")
        return {
            "validation_result": "ok",  # ループを抜ける
            "validation_feedback": f"エラーが発生しました: {error_msg}",
        }

    # エージェント実行が成功した場合
    logger.info("✅ エージェント実行成功")

    # データの内容を検証
    data = agent_output.get("data", {})

    # 簡易的な品質チェック
    validation_result, feedback = _simple_quality_check(state, data)

    logger.info(f"📊 品質チェック結果: {validation_result}")
    if feedback:
        logger.info(f"   フィードバック: {feedback}")

    return {
        "validation_result": validation_result,
        "validation_feedback": feedback,
        "loop_count": loop_count + 1 if validation_result == "needs_refinement" else loop_count,
    }


def _simple_quality_check(
    state: PaperDiscussionState,
    data: Dict[str, Any]
) -> tuple[str, str]:
    """
    簡易的な品質チェック

    Args:
        state: 現在の状態
        data: エージェントが返したデータ

    Returns:
        (validation_result, feedback) のタプル
    """
    intent = state.get("intent", "")

    # セクション作成/更新の場合
    if intent in ["create_section", "update_section"]:
        # 複数セクション作成の場合
        created_sections = data.get("created_sections")
        if created_sections:
            return "ok", f"{len(created_sections)}個のセクションが作成されました"

        # 単一セクション作成の場合
        section = data.get("section")
        if section and section.get("title"):
            return "ok", "セクション作成/更新が完了しました"

        # セクションが見つからない場合はエラー
        return "needs_refinement", "セクションが作成されませんでした"

    # コンテンツ生成の場合
    elif intent in ["generate_content", "rewrite_content"]:
        content = data.get("content", "")
        if not content or len(content) < 50:
            return "needs_refinement", "生成されたコンテンツが短すぎます"

        return "ok", "コンテンツ生成が完了しました"

    # 検索の場合
    elif intent == "search_chromadb":
        results = data.get("results", [])
        if not results:
            return "needs_more_info", "検索結果が見つかりませんでした"

        return "ok", f"{len(results)}件の検索結果を取得しました"

    # その他のタスク
    else:
        # デフォルトは成功とみなす
        return "ok", "タスクが完了しました"
