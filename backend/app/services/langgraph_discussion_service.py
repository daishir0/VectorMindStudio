"""
LangGraphベースの研究ディスカッションサービス

このサービスは、LangGraphワークフローを使用して
論文執筆の研究ディスカッションを処理します。
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.langgraph_agents.graphs.paper_discussion_graph import create_paper_discussion_graph
from app.services.langgraph_agents.state import create_initial_state
from app.infrastructure.repositories.paper_repository import PaperRepository

logger = logging.getLogger(__name__)


class LangGraphDiscussionService:
    """
    LangGraphベースの研究ディスカッションサービス

    旧ResearchDiscussionServiceV3の代替として、
    LangGraphワークフローを使用した実装を提供します。
    """

    def __init__(self, session: AsyncSession):
        """
        Args:
            session: データベースセッション
        """
        self.session = session
        self.repository = PaperRepository(session)

    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str,
        paper_id: str
    ) -> Dict[str, Any]:
        """
        ユーザーメッセージを処理して応答を生成

        LangGraphワークフローを実行し、適切なエージェントに
        ルーティングして結果を返します。

        Args:
            session_id: チャットセッションID
            user_message: ユーザーの入力メッセージ
            user_id: ユーザーID
            paper_id: 論文ID

        Returns:
            処理結果の辞書
            {
                "message": "応答メッセージ",
                "todo_tasks": [],
                "task_results": {},
                "references": [],
                "suggestions": [],
                "success": True
            }
        """
        logger.info(f"🎯 LangGraph処理開始: session={session_id}, paper={paper_id}")
        logger.info(f"   User message: {user_message[:100]}...")

        try:
            # 論文情報の取得
            paper = await self.repository.get_paper_by_id(paper_id)
            if not paper:
                return {
                    "message": "論文が見つかりませんでした。",
                    "todo_tasks": [],
                    "task_results": {},
                    "references": [],
                    "suggestions": [],
                    "success": False
                }

            # セクション情報の取得
            sections = await self.repository.get_sections_by_paper(paper_id)
            sections_data = [
                {
                    "id": section.id,
                    "hierarchy_path": section.section_number,
                    "title": section.title,
                    "content": section.content or "",
                    "summary": section.summary or "",
                }
                for section in sections
            ]

            # 論文の全体テキスト構築（簡易版）
            paper_draft = "\n\n".join([
                f"## {section.title}\n{section.content or ''}"
                for section in sections
            ])

            # 初期状態の作成
            initial_state = create_initial_state(
                paper_id=paper_id,
                user_id=user_id,
                session_id=session_id,
                user_query=user_message,
                paper_title=paper.title,
                paper_draft=paper_draft,
                sections=sections_data
            )

            # LangGraphワークフローの作成と実行
            logger.info("🏗️ LangGraphワークフローを構築中...")
            graph_app = create_paper_discussion_graph(self.session)

            logger.info("▶️ ワークフロー実行中...")
            # 同期的に実行（ainvoke は async）
            # recursion_limitを増やして無限ループを防ぐ
            config = {"recursion_limit": 50}
            final_state = await graph_app.ainvoke(initial_state, config=config)

            logger.info("✅ ワークフロー実行完了")

            # 結果の取得
            final_response = final_state.get("final_response", "")
            response_metadata = final_state.get("response_metadata", {})
            error = final_state.get("error")
            agent_output = final_state.get("agent_output", {})

            # エラーチェック
            if error:
                logger.error(f"❌ ワークフローエラー: {error}")
                return {
                    "message": f"処理中にエラーが発生しました: {error}",
                    "todo_tasks": [],
                    "task_results": {},
                    "references": [],
                    "suggestions": [],
                    "success": False
                }

            # チャットメッセージの保存
            await self._save_chat_messages(
                session_id=session_id,
                user_message=user_message,
                assistant_message=final_response,
                agent_name=response_metadata.get("agent_used", "LangGraph"),
                references=agent_output.get("references", [])
            )

            # レスポンスの構築
            return {
                "message": final_response,
                "todo_tasks": self._extract_todo_tasks(agent_output),
                "task_results": agent_output.get("task_results", {}),
                "references": agent_output.get("references", []),
                "suggestions": agent_output.get("suggestions", []),
                "success": True,
                "metadata": response_metadata
            }

        except Exception as e:
            logger.error(f"❌ メッセージ処理エラー: {e}", exc_info=True)
            return {
                "message": f"申し訳ございません。処理中にエラーが発生しました: {str(e)}",
                "todo_tasks": [],
                "task_results": {},
                "references": [],
                "suggestions": [],
                "success": False
            }

    async def _save_chat_messages(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        agent_name: str,
        references: List[Dict[str, Any]]
    ) -> None:
        """
        チャットメッセージをデータベースに保存

        Args:
            session_id: チャットセッションID
            user_message: ユーザーメッセージ
            assistant_message: アシスタントメッセージ
            agent_name: 使用されたエージェント名
            references: 参考文献リスト
        """
        try:
            # ユーザーメッセージを保存
            await self.repository.create_chat_message(
                session_id=session_id,
                role="user",
                content=user_message,
                agent_name=None,
                todo_tasks=[],
                references=[]
            )

            # アシスタントメッセージを保存
            await self.repository.create_chat_message(
                session_id=session_id,
                role="assistant",
                content=assistant_message,
                agent_name=agent_name,
                todo_tasks=[],
                references=references
            )

            logger.info(f"💾 チャットメッセージを保存しました: session={session_id}")

        except Exception as e:
            logger.error(f"❌ メッセージ保存エラー: {e}", exc_info=True)
            # メッセージ保存失敗は致命的ではないので、処理を続行

    def _extract_todo_tasks(self, agent_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        エージェント出力からTODOタスクを抽出

        Args:
            agent_output: エージェントの出力

        Returns:
            TODOタスクのリスト
        """
        # agent_outputから直接取得を試みる
        if "todo_tasks" in agent_output:
            return agent_output["todo_tasks"]

        # データ内にネストされている場合
        if "data" in agent_output and isinstance(agent_output["data"], dict):
            if "todo_tasks" in agent_output["data"]:
                return agent_output["data"]["todo_tasks"]

        # デフォルトは空リスト
        return []
