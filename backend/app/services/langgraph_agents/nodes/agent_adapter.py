"""
既存エージェントをLangGraphノードに変換するアダプター

既存のBaseAgentを継承したエージェント（OutlineAgent, WriterAgent等）を
LangGraphのノード関数として使用できるようにラップします。
"""

import logging
from typing import Dict, Any, Callable
from app.services.langgraph_agents.state import PaperDiscussionState
from app.services.agents.base_agent import BaseAgent, AgentTask, AgentStatus

logger = logging.getLogger(__name__)


def create_agent_node(
    agent_instance: BaseAgent,
    agent_name: str,
) -> Callable[[PaperDiscussionState], Dict[str, Any]]:
    """
    既存エージェントをLangGraphノード関数に変換

    Args:
        agent_instance: BaseAgentを継承したエージェントインスタンス
        agent_name: エージェント名（ログ用）

    Returns:
        LangGraphノード関数
    """

    async def agent_node(state: PaperDiscussionState) -> Dict[str, Any]:
        """
        エージェントノード関数

        Args:
            state: 現在の状態

        Returns:
            更新すべき状態フィールドの辞書
        """
        logger.info(f"🤖 {agent_name}: タスク実行開始")
        logger.info(f"   Intent: {state.get('intent', 'N/A')}")
        logger.info(f"   Params: {state.get('intent_params', {})}")

        try:
            # intentからtask_typeを取得
            task_type = state.get("intent", "")

            # intent_paramsをエージェントのparams形式に変換
            agent_params = _convert_state_to_agent_params(state)

            # AgentTaskオブジェクトを作成
            task = agent_instance.create_task(
                task_type=task_type,
                parameters=agent_params
            )

            # エージェント実行
            agent_result = await agent_instance.execute_task(task)

            # AgentResultを辞書形式に変換
            if agent_result.status == AgentStatus.COMPLETED:
                result = {
                    "success": True,
                    "message": "タスクが正常に完了しました",
                    "data": agent_result.result
                }
            else:
                result = {
                    "success": False,
                    "message": agent_result.error_message or "タスクが失敗しました",
                    "data": None
                }

            logger.info(f"✅ {agent_name}: タスク実行完了")
            logger.info(f"   Success: {result.get('success', False)}")

            # 状態更新の準備
            state_update = {
                "selected_agent": agent_name,
                "agent_output": result,
                "tool_calls": [agent_name],
            }

            # チェーン処理: task_chainが設定されている場合
            task_chain = state.get("task_chain", [])
            if task_chain and len(task_chain) > 0:
                current_task_index = state.get("current_task_index", 0)

                # 現在のタスク結果を記録
                chain_result = {
                    "task": task_type,
                    "agent": agent_name,
                    "result": result,
                    "success": result.get("success", False),
                }
                state_update["chain_results"] = [chain_result]

                # 次のタスクへインクリメント
                next_index = current_task_index + 1
                state_update["current_task_index"] = next_index

                # 次のタスクがある場合、intentを更新
                if next_index < len(task_chain):
                    next_task = task_chain[next_index]
                    state_update["intent"] = next_task
                    logger.info(f"🔗 チェーン進行: {current_task_index + 1}/{len(task_chain)} → {next_index + 1}/{len(task_chain)}")
                    logger.info(f"   次のタスク: {next_task}")
                else:
                    logger.info(f"🔗 チェーン最終タスク完了: {current_task_index + 1}/{len(task_chain)}")

            return state_update

        except Exception as e:
            logger.error(f"❌ {agent_name}: 実行エラー: {e}", exc_info=True)

            return {
                "selected_agent": agent_name,
                "agent_output": {
                    "success": False,
                    "message": f"エージェント実行エラー: {str(e)}",
                    "data": None,
                },
                "error": f"{agent_name}の実行に失敗しました: {str(e)}",
            }

    return agent_node


def _convert_state_to_agent_params(state: PaperDiscussionState) -> Dict[str, Any]:
    """
    LangGraph StateをBaseAgentのparams形式に変換

    Intent別に適切なパラメータマッピングを行います。
    例: sectionsリスト → title/section_title/query などの個別パラメータ

    Args:
        state: PaperDiscussionState

    Returns:
        エージェントに渡すparamsディクショナリ
    """
    # intent_paramsから開始
    intent_params = state.get("intent_params", {})
    params = dict(intent_params)
    intent = state.get("intent", "")

    # 必須パラメータを確実に設定（intent_paramsより優先）
    params["paper_id"] = state.get("paper_id")
    params["user_id"] = state.get("user_id")
    params["session_id"] = state.get("session_id")

    # sectionsを先に設定（パラメータマッピングで使用するため）
    if "sections" not in params:
        params["sections"] = state.get("sections", [])

    # 追加の便利なパラメータも先に設定
    params["user_query"] = state.get("user_query", "")
    params["paper_draft"] = state.get("paper_draft", "")
    params["rag_context"] = state.get("rag_context")

    logger.info(f"🔍 パラメータ変換前: intent={intent}, sections={params.get('sections', [])[:3] if isinstance(params.get('sections'), list) else params.get('sections')}")

    # Intent別のパラメータマッピング
    if intent in ["generate_content", "rewrite_content"]:
        # WriterAgentのgenerate_content用: sectionsリストから最初の要素を取得
        if "sections" in params and isinstance(params["sections"], list) and len(params["sections"]) > 0:
            first_section = params["sections"][0]
            if isinstance(first_section, str):
                params["title"] = first_section
            elif isinstance(first_section, dict):
                params["title"] = first_section.get("title") or first_section.get("name") or str(first_section)
            logger.info(f"📝 WriterAgent用にsectionsから title を抽出: {params.get('title')}")

    elif intent == "generate_draft":
        # WriterAgentのgenerate_draft用
        if "sections" in params and isinstance(params["sections"], list) and len(params["sections"]) > 0:
            first_section = params["sections"][0]
            if isinstance(first_section, str):
                params["section_title"] = first_section
            elif isinstance(first_section, dict):
                params["section_title"] = first_section.get("title") or first_section.get("name") or str(first_section)
            logger.info(f"📝 WriterAgent用にsectionsから section_title を抽出: {params.get('section_title')}")

    elif intent in ["search_references", "find_similar_content"]:
        # ReferenceRetrievalAgent用: sectionsリストをクエリに変換
        if "sections" in params and isinstance(params["sections"], list):
            # セクション名を結合してクエリを作成
            section_names = []
            for s in params["sections"]:
                if isinstance(s, str):
                    section_names.append(s)
                elif isinstance(s, dict):
                    section_names.append(s.get("title") or s.get("name") or "")
            params["query"] = " ".join(section_names)
            logger.info(f"🔍 ReferenceRetrievalAgent用にsectionsから query を生成: {params.get('query')}")

    logger.info(f"✅ パラメータ変換後: title={params.get('title')}, section_title={params.get('section_title')}, query={params.get('query')}")

    return params


def _convert_agent_output_to_state_update(
    agent_output: Dict[str, Any],
    agent_name: str,
) -> Dict[str, Any]:
    """
    エージェントの出力をState更新形式に変換

    Args:
        agent_output: エージェントの出力
        agent_name: エージェント名

    Returns:
        Stateの更新辞書
    """
    state_update = {
        "selected_agent": agent_name,
        "agent_output": agent_output,
    }

    # エージェントの出力に含まれる特定のフィールドをStateに反映
    if agent_output.get("success"):
        data = agent_output.get("data", {})

        # セクション情報の更新
        if "sections" in data:
            state_update["sections"] = data["sections"]

        # 論文ドラフトの更新
        if "paper_draft" in data:
            state_update["paper_draft"] = data["paper_draft"]

        # RAGコンテキストの更新
        if "rag_results" in data:
            state_update["rag_context"] = data["rag_results"]

    return state_update
