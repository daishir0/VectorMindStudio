"""
Orchestratorノード

ユーザーの問い合わせを解析し、適切なエージェントに
ルーティングするための意図（intent）を決定します。

このノードはLLM（GPT-4o）を使用して、自然言語の依頼から
構造化された意図とパラメータを抽出します。
"""

import json
import logging
from typing import Dict, Any
from app.services.langgraph_agents.state import PaperDiscussionState
from app.services.langgraph_agents.constants import CHAIN_INTENTS
from app.infrastructure.external.openai_client import openai_client

logger = logging.getLogger(__name__)


# 意図解析用のシステムプロンプト
ORCHESTRATOR_SYSTEM_PROMPT = """あなたは論文執筆アシスタントのOrchestratorです。
ユーザーの依頼を分析し、適切なエージェントにタスクを振り分けます。

【利用可能なエージェント】
1. outline_agent: セクションの作成・更新・削除、構造変更
2. writer_agent: コンテンツ生成、加筆、書き直し
3. analysis_agent: 批判的分析、構造分析、一貫性チェック
4. discovery_agent: ChromaDB検索、ギャップ分析、新規テーマ発見
5. quality_agent: 品質評価、コンプライアンスチェック、倫理検証
6. strategy_agent: 研究戦略立案、出版戦略、インパクト最大化
7. reference_agent: 参考文献検索、類似コンテンツ検索

【あなたの役割】
ユーザーの依頼を解析し、以下のJSON形式で意図を返してください：

{
  "intent": "エージェントに対応するタスクタイプ",
  "intent_params": {
    "必要なパラメータ": "値",
    ...
  },
  "reasoning": "なぜこの意図を選択したかの説明"
}

【単一タスクの例】
- create_section: 新しいセクションを作成
- update_section: 既存セクションを更新
- delete_section: セクションを削除
- generate_content: コンテンツを生成
- rewrite_content: コンテンツを書き直し
- analyze_structure: 構造を分析
- search_chromadb: ChromaDBで関連資料を検索
- quality_assessment: 品質を評価
- research_strategy_planning: 研究戦略を立案

【複数エージェント連携タスク（Sequential Chain）】
複雑な依頼の場合、以下のチェーン意図を使用できます：

- research_and_write: 資料検索 → コンテンツ生成 → 品質チェック
  （例：「ChromaDBで資料を探して、それを基に執筆してください」）

- deep_analysis: 構造分析 → 批判的分析 → 品質評価
  （例：「論文全体を詳しく分析してください」）

- section_workflow: セクション作成 → ドラフト生成 → 品質チェック
  （例：「新しいセクションを作成して、内容も書いてください」）

- strategic_writing: ギャップ分析 → 戦略立案 → コンテンツ生成
  （例：「研究の方向性を検討して、執筆してください」）

- reference_based_writing: 参考文献検索 → 類似コンテンツ探索 → コンテンツ生成
  （例：「参考文献を探して、それを基に執筆してください」）

【重要】
- 必ずJSON形式で返してください
- reasoningフィールドで判断根拠を説明してください
- intent_paramsには具体的なパラメータを含めてください
- 複数の処理が必要な場合は、適切なチェーン意図を選択してください
"""


async def orchestrator_node(state: PaperDiscussionState) -> Dict[str, Any]:
    """
    Orchestratorノード関数

    ユーザーの問い合わせを解析し、意図（intent）と
    パラメータ（intent_params）を決定します。

    Args:
        state: 現在の状態

    Returns:
        更新すべき状態フィールドの辞書
    """
    logger.info(f"🎯 Orchestrator: ユーザー依頼を解析中...")
    logger.info(f"   User Query: {state['user_query'][:100]}...")

    # チェーン実行中の場合：LLM呼び出しをスキップ
    task_chain = state.get("task_chain", [])
    current_task_index = state.get("current_task_index", 0)

    if task_chain and len(task_chain) > 0 and current_task_index < len(task_chain):
        # チェーン実行中は現在のintentとパラメータをそのまま返す
        current_intent = state.get("intent", "")
        logger.info(f"🔗 チェーン実行中: LLM呼び出しをスキップ")
        logger.info(f"   現在のIntent: {current_intent}")
        logger.info(f"   タスク進捗: {current_task_index}/{len(task_chain)}")

        return {
            "tool_calls": ["orchestrator_chain_passthrough"],
        }

    try:
        # ユーザープロンプト構築
        user_prompt = f"""
【ユーザーの依頼】
{state['user_query']}

【現在の論文情報】
- タイトル: {state.get('paper_title', '未設定')}
- セクション数: {len(state.get('sections', []))}
- 論文の長さ: {len(state.get('paper_draft', ''))} 文字

【会話履歴】
{_format_conversation_history(state.get('conversation_history', []))}

上記の依頼を解析し、適切な意図（intent）とパラメータを決定してください。
"""

        # LLM呼び出し（system promptとuser promptを組み合わせる）
        combined_prompt = f"""{ORCHESTRATOR_SYSTEM_PROMPT}

---

{user_prompt}"""

        response = await openai_client.generate_text(
            prompt=combined_prompt,
            model="gpt-4o"
        )

        # レスポンスをパース
        content = response.get("content", "{}")

        # JSONを抽出（マークダウンコードブロックを考慮）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        intent_data = json.loads(content)

        intent = intent_data.get("intent", "")
        intent_params = intent_data.get("intent_params", {})
        reasoning = intent_data.get("reasoning", "")

        logger.info(f"✅ Intent解析完了:")
        logger.info(f"   Intent: {intent}")
        logger.info(f"   Params: {intent_params}")
        logger.info(f"   Reasoning: {reasoning}")

        # 状態更新の準備
        state_update = {
            "intent": intent,
            "intent_params": intent_params,
            "tool_calls": ["orchestrator_llm"],
        }

        # チェーン意図の場合、task_chainを設定
        if intent in CHAIN_INTENTS:
            task_chain = CHAIN_INTENTS[intent]
            state_update["task_chain"] = task_chain
            state_update["current_task_index"] = 0
            # 最初のタスクをintentに設定
            state_update["intent"] = task_chain[0]
            logger.info(f"🔗 チェーン意図を検出: {len(task_chain)}タスク")
            logger.info(f"   タスクリスト: {', '.join(task_chain)}")
            logger.info(f"   最初のタスク: {task_chain[0]}")

        return state_update

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析エラー: {e}")
        logger.error(f"   Response content: {content}")

        # フォールバック: 簡易的な意図推定
        fallback_intent = _fallback_intent_detection(state['user_query'])

        return {
            "intent": fallback_intent["intent"],
            "intent_params": fallback_intent["params"],
            "tool_calls": ["orchestrator_fallback"],
        }

    except Exception as e:
        logger.error(f"❌ Orchestrator実行エラー: {e}", exc_info=True)

        return {
            "intent": "error",
            "intent_params": {"error_message": str(e)},
            "error": f"意図解析に失敗しました: {str(e)}",
        }


def _format_conversation_history(history: list) -> str:
    """会話履歴をフォーマット"""
    if not history:
        return "（会話履歴なし）"

    formatted = []
    for msg in history[-3:]:  # 直近3件のみ
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:100]  # 最初の100文字
        formatted.append(f"- {role}: {content}...")

    return "\n".join(formatted)


def _fallback_intent_detection(query: str) -> Dict[str, Any]:
    """
    LLM失敗時のフォールバック意図検出（簡易的なキーワードマッチ）

    キーワードマッチに成功した場合は該当intentを返す。
    マッチ失敗時はユーザーガイダンス付きの needs_clarification を返す。
    """
    query_lower = query.lower()

    # キーワードベースの簡易マッチング
    if any(word in query_lower for word in ["セクション作成", "新しいセクション", "セクション追加"]):
        return {"intent": "create_section", "params": {}}

    elif any(word in query_lower for word in ["加筆", "追加", "書いて", "執筆"]):
        return {"intent": "generate_content", "params": {}}

    elif any(word in query_lower for word in ["検索", "探して", "資料", "参考文献"]):
        return {"intent": "search_chromadb", "params": {"query": query}}

    elif any(word in query_lower for word in ["分析", "評価", "チェック"]):
        return {"intent": "analyze_structure", "params": {}}

    elif any(word in query_lower for word in ["構成", "構造", "並び替え", "整理"]):
        return {"intent": "update_section", "params": {}}

    else:
        # マッチ失敗: ユーザーガイダンスを返す
        return {
            "intent": "needs_clarification",
            "params": {
                "original_query": query,
                "suggestions": [
                    {
                        "example": "「Introductionセクションを作成してください」",
                        "intent": "create_section",
                        "description": "新しいセクションを追加したい場合"
                    },
                    {
                        "example": "「ChromaDBで『AI倫理』を検索してください」",
                        "intent": "search_chromadb",
                        "description": "資料を検索したい場合"
                    },
                    {
                        "example": "「Methodsセクションに詳しい説明を追加してください」",
                        "intent": "generate_content",
                        "description": "コンテンツを生成したい場合"
                    },
                    {
                        "example": "「論文全体の品質を評価してください」",
                        "intent": "quality_assessment",
                        "description": "品質チェックをしたい場合"
                    },
                    {
                        "example": "「論文の構造を分析してください」",
                        "intent": "structure_analysis",
                        "description": "論文構造を確認したい場合"
                    }
                ],
                "help_message": "依頼内容がよくわかりませんでした。以下のように指示してみてください："
            }
        }
