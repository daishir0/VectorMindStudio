"""
論文執筆ディスカッションの状態定義

LangGraphで使用する状態（State）を定義します。
この状態は全ノード（エージェント）間で共有され、
ワークフローの現在のコンテキストを保持します。
"""

from typing import TypedDict, List, Dict, Any, Annotated, Optional
from operator import add


class PaperDiscussionState(TypedDict):
    """
    論文執筆ディスカッションの状態

    この状態は全エージェント間で共有され、ユーザーの依頼から
    最終的な返答までの全コンテキストを保持します。
    """

    # ===== 論文データ =====
    paper_id: str
    """論文ID"""

    user_id: str
    """ユーザーID"""

    session_id: str
    """チャットセッションID"""

    paper_title: str
    """論文タイトル"""

    paper_draft: str
    """現在の論文全体テキスト（最新版）"""

    sections: List[Dict[str, Any]]
    """
    セクション構造のリスト
    各セクションは {id, hierarchy_path, title, content, summary} を含む
    """

    # ===== ユーザーインタラクション =====
    user_query: str
    """ユーザーの最新依頼（生のテキスト）"""

    intent: str
    """
    Orchestratorが解析した意図
    例: create_section, update_section, generate_content,
        search_chromadb, analyze_structure, etc.
    """

    intent_params: Dict[str, Any]
    """
    意図に関連するパラメータ
    例: section_id, section_title, query_text, etc.
    """

    # ===== エージェント実行 =====
    selected_agent: str
    """選択されたエージェント名（outline_agent, writer_agent, etc.）"""

    agent_output: Dict[str, Any]
    """
    エージェントの出力結果
    エージェントが返すデータ構造は自由だが、
    最低限 {success: bool, message: str, data: Any} を含むべき
    """

    tool_calls: Annotated[List[str], add]
    """
    使用されたツールのリスト（追加専用、Reducerでマージ）
    例: ["chromadb_search", "openai_api", "vector_service"]
    """

    # ===== コンテキスト =====
    conversation_history: Annotated[List[Dict[str, str]], add]
    """
    会話履歴（追加専用、Reducerでマージ）
    各要素: {role: "user"|"assistant"|"system", content: str, timestamp: str}
    """

    rag_context: Optional[Dict[str, Any]]
    """
    ChromaDB検索結果やRAGコンテキスト
    {query: str, results: List[Dict], similarity_scores: List[float]}
    """

    # ===== タスクチェーン（複数エージェント連携） =====
    task_chain: List[str]
    """
    実行予定タスクリスト（Sequential Chain用）
    例: ["search_chromadb", "generate_content", "quality_assessment"]
    """

    current_task_index: int
    """
    現在のタスク位置（Sequential Chain用）
    デフォルト: 0、task_chainの何番目のタスクを実行中か
    """

    chain_results: Annotated[List[Dict[str, Any]], add]
    """
    各タスクの結果リスト（Sequential Chain用、追加専用）
    例: [{"task": "search_chromadb", "result": {...}}, ...]
    """

    # ===== フロー制御 =====
    validation_result: str
    """
    品質検証結果
    - "ok": 品質問題なし、ユーザーに返答可能
    - "needs_refinement": 品質不足、修正が必要
    - "needs_more_info": 情報不足、追加質問が必要
    """

    validation_feedback: Optional[str]
    """品質検証の詳細フィードバック（改善提案など）"""

    loop_count: int
    """
    反復実行のカウンター（無限ループ防止）
    デフォルト: 0、最大: 3
    """

    max_loops: int
    """許可される最大ループ回数（デフォルト: 3）"""

    # ===== 最終出力 =====
    final_response: str
    """ユーザーに返す最終的な応答テキスト"""

    response_metadata: Optional[Dict[str, Any]]
    """
    応答に関するメタデータ
    例: {processing_time_ms: 1234, agents_used: ["outline", "writer"],
         loop_iterations: 2}
    """

    # ===== エラーハンドリング =====
    error: Optional[str]
    """エラーメッセージ（エラー発生時のみ）"""

    error_details: Optional[Dict[str, Any]]
    """エラーの詳細情報"""


def create_initial_state(
    paper_id: str,
    user_id: str,
    session_id: str,
    user_query: str,
    paper_title: str = "",
    paper_draft: str = "",
    sections: Optional[List[Dict[str, Any]]] = None,
) -> PaperDiscussionState:
    """
    初期状態を作成するヘルパー関数

    Args:
        paper_id: 論文ID
        user_id: ユーザーID
        session_id: セッションID
        user_query: ユーザーの依頼
        paper_title: 論文タイトル（オプション）
        paper_draft: 論文の現在のドラフト（オプション）
        sections: セクション構造（オプション）

    Returns:
        初期化されたPaperDiscussionState
    """
    return PaperDiscussionState(
        # 論文データ
        paper_id=paper_id,
        user_id=user_id,
        session_id=session_id,
        paper_title=paper_title,
        paper_draft=paper_draft,
        sections=sections or [],

        # ユーザーインタラクション
        user_query=user_query,
        intent="",
        intent_params={},

        # エージェント実行
        selected_agent="",
        agent_output={},
        tool_calls=[],

        # コンテキスト
        conversation_history=[{
            "role": "user",
            "content": user_query,
            "timestamp": "",
        }],
        rag_context=None,

        # タスクチェーン（複数エージェント連携）
        task_chain=[],
        current_task_index=0,
        chain_results=[],

        # フロー制御
        validation_result="",
        validation_feedback=None,
        loop_count=0,
        max_loops=3,

        # 最終出力
        final_response="",
        response_metadata=None,

        # エラーハンドリング
        error=None,
        error_details=None,
    )
