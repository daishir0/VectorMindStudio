"""
Responseノード

最終的なユーザーへの返答を生成します。
"""

import logging
from typing import Dict, Any
from app.services.langgraph_agents.state import PaperDiscussionState
from app.infrastructure.external.openai_client import openai_client

logger = logging.getLogger(__name__)


async def response_node(state: PaperDiscussionState) -> Dict[str, Any]:
    """
    ユーザーへの返答生成ノード

    Args:
        state: 現在の状態

    Returns:
        更新すべき状態フィールドの辞書
    """
    logger.info("💬 Response: ユーザー返答を生成中...")

    try:
        # エージェントの出力を取得
        agent_output = state.get("agent_output", {})
        validation_feedback = state.get("validation_feedback", "")
        selected_agent = state.get("selected_agent", "不明")

        # 簡易的な返答生成（LLMを使用）
        response_prompt = _build_response_prompt(state, agent_output, validation_feedback)

        # system promptとuser promptを組み合わせる
        combined_prompt = f"""あなたは親切な論文執筆アシスタントです。ユーザーに分かりやすく、親しみやすく結果を報告してください。

---

{response_prompt}"""

        llm_response = await openai_client.generate_text(
            prompt=combined_prompt,
            model="gpt-4o-mini"
        )

        final_response = llm_response.get("content", "処理が完了しました。")

        logger.info(f"✅ 返答生成完了: {final_response[:100]}...")

        # メタデータ作成
        metadata = {
            "processing_time_ms": 0,  # TODO: 実際の処理時間を計測
            "agents_used": [selected_agent],
            "loop_iterations": state.get("loop_count", 0),
            "validation_feedback": validation_feedback,
        }

        return {
            "final_response": final_response,
            "response_metadata": metadata,
            "tool_calls": ["response_generator"],
        }

    except Exception as e:
        logger.error(f"❌ 返答生成エラー: {e}", exc_info=True)

        # フォールバック返答
        fallback_response = _build_fallback_response(state)

        return {
            "final_response": fallback_response,
            "response_metadata": {"error": str(e)},
            "error": f"返答生成に失敗しました: {str(e)}",
        }


def _build_response_prompt(
    state: PaperDiscussionState,
    agent_output: Dict[str, Any],
    validation_feedback: str
) -> str:
    """返答生成用のプロンプトを構築"""
    user_query = state.get("user_query", "")
    intent = state.get("intent", "")
    success = agent_output.get("success", False)
    message = agent_output.get("message", "")
    data = agent_output.get("data", {})

    prompt = f"""
【ユーザーの依頼】
{user_query}

【実行したタスク】
{intent}

【実行結果】
成功: {"はい" if success else "いいえ"}
メッセージ: {message}

【詳細データ】
{_format_data_summary(data)}

【検証フィードバック】
{validation_feedback}

上記の実行結果を、ユーザーに分かりやすく、親しみやすく報告してください。
具体的な変更内容や取得した情報を含めてください。
"""

    return prompt


def _format_data_summary(data: Dict[str, Any]) -> str:
    """データを要約（コンテンツプレビュー機能追加）"""
    if not data:
        return "（データなし）"

    summary_parts = []

    if "section" in data:
        section = data["section"]
        summary_parts.append(f"- セクション: {section.get('title', 'N/A')}")

    if "content" in data:
        content = data["content"]
        summary_parts.append(f"- コンテンツ長: {len(content)} 文字")
        # コンテンツのプレビューを追加（最初の500文字）
        if content:
            preview = content[:500]
            if len(content) > 500:
                preview += "..."
            summary_parts.append(f"- コンテンツプレビュー:\n{preview}")

    # WriterAgentが複数セクション処理した場合の対応
    if "results" in data and isinstance(data["results"], list):
        # 検索結果の場合
        if data["results"] and isinstance(data["results"][0], dict):
            first_result = data["results"][0]
            # WriterAgentの複数セクション結果か判定
            if "draft_content" in first_result or "content" in first_result:
                summary_parts.append(f"- 生成セクション数: {len(data['results'])} 個")
                # 各セクションのプレビューを追加
                for i, result in enumerate(data["results"], 1):
                    title = result.get("title", f"セクション{i}")
                    content = result.get("draft_content") or result.get("content", "")
                    word_count = result.get("word_count", 0)
                    summary_parts.append(f"\n【{title}】({word_count}語)")
                    if content:
                        preview = content[:300]
                        if len(content) > 300:
                            preview += "..."
                        summary_parts.append(f"{preview}")
            else:
                # 検索結果の場合
                summary_parts.append(f"- 検索結果: {len(data['results'])} 件")

    if "sections" in data:
        sections = data["sections"]
        summary_parts.append(f"- セクション数: {len(sections)}")

    # word_countとcharacter_countがある場合
    if "word_count" in data:
        summary_parts.append(f"- 語数: {data['word_count']} 語")
    if "character_count" in data:
        summary_parts.append(f"- 文字数: {data['character_count']} 文字")

    # 総合統計（複数セクション処理の場合）
    if "total_word_count" in data:
        summary_parts.append(f"- 総語数: {data['total_word_count']} 語")
    if "total_character_count" in data:
        summary_parts.append(f"- 総文字数: {data['total_character_count']} 文字")

    return "\n".join(summary_parts) if summary_parts else str(data)[:200]


def _build_fallback_response(state: PaperDiscussionState) -> str:
    """LLM失敗時のフォールバック返答"""
    agent_output = state.get("agent_output", {})
    success = agent_output.get("success", False)
    message = agent_output.get("message", "処理が完了しました")

    if success:
        return f"✅ {message}"
    else:
        return f"❌ {message}"
