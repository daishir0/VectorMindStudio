"""
エージェント管理サービス

AIエージェントのCRUD操作、検索、統計情報取得などを提供
"""
from typing import List, Optional, Dict, Any
import logging
from fastapi import HTTPException, status

from app.infrastructure.repositories.agent_repository import AgentRepository
from app.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse,
    WakeWordCreate, CapabilityCreate,
    AgentStatistics, AgentExecutionStats,
    ExecutorType
)

logger = logging.getLogger(__name__)


class AgentManagementService:
    """エージェント管理サービス"""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    # === エージェント CRUD ===

    async def create_agent(
        self,
        agent_data: AgentCreate,
        user_id: Optional[str] = None
    ) -> AgentResponse:
        """
        新しいエージェントを作成

        Args:
            agent_data: エージェント作成データ
            user_id: ユーザーID（カスタムエージェントの場合）

        Returns:
            作成されたエージェント

        Raises:
            HTTPException: 名前重複、バリデーションエラー
        """
        try:
            # 名前重複チェック
            existing_agent = await self.agent_repo.get_agent_by_name(agent_data.name)
            if existing_agent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent with name '{agent_data.name}' already exists"
                )

            # エージェント作成
            agent_dict = agent_data.model_dump(exclude={'wake_words', 'capabilities'})
            agent_dict['user_id'] = user_id
            agent_dict['created_by'] = user_id

            # システムエージェントはデフォルトでis_system=False
            agent_dict['is_system'] = False

            agent = await self.agent_repo.create_agent(**agent_dict)

            # ウェイクワード追加
            if agent_data.wake_words:
                for wake_word_data in agent_data.wake_words:
                    await self.agent_repo.create_wake_word(
                        agent_id=agent.id,
                        keyword=wake_word_data.keyword,
                        keyword_type=wake_word_data.match_type.value,
                        priority=wake_word_data.priority,
                        user_id=user_id
                    )

            # 能力追加
            if agent_data.capabilities:
                for capability_data in agent_data.capabilities:
                    await self.agent_repo.create_capability(
                        agent_id=agent.id,
                        capability_type=capability_data.task_type,
                        description=capability_data.description or "",
                        supported_task_types=[capability_data.task_type],
                        user_id=user_id
                    )

            # 作成後のエージェントを取得（wake_wordsとcapabilitiesを含む）
            created_agent = await self.agent_repo.get_agent_by_id(agent.id)

            logger.info(f"Created agent: {agent.id} (name={agent.name}, user_id={user_id})")

            return AgentResponse.model_validate(created_agent)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create agent: {str(e)}"
            )

    async def get_agent(self, agent_id: str) -> AgentResponse:
        """
        エージェントを取得

        Args:
            agent_id: エージェントID

        Returns:
            エージェント情報

        Raises:
            HTTPException: エージェントが存在しない
        """
        agent = await self.agent_repo.get_agent_by_id(agent_id)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )

        return AgentResponse.model_validate(agent)

    async def update_agent(
        self,
        agent_id: str,
        agent_data: AgentUpdate,
        user_id: Optional[str] = None
    ) -> AgentResponse:
        """
        エージェントを更新

        システムエージェントの場合は、プロンプトやexecutor_typeなどの変更は不可

        Args:
            agent_id: エージェントID
            agent_data: 更新データ
            user_id: ユーザーID

        Returns:
            更新されたエージェント

        Raises:
            HTTPException: エージェントが存在しない、権限エラー、バリデーションエラー
        """
        try:
            # 既存エージェント取得
            existing_agent = await self.agent_repo.get_agent_by_id(agent_id)
            if not existing_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent not found: {agent_id}"
                )

            # 権限チェック（カスタムエージェントの場合）
            if not existing_agent.is_system:
                if existing_agent.user_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to update this agent"
                    )

            # システムエージェントの更新制限
            if existing_agent.is_system:
                self._validate_system_agent_update(agent_data)

            # 更新データ準備
            update_dict = agent_data.model_dump(
                exclude_unset=True,
                exclude={'wake_words', 'capabilities'}
            )

            # システムエージェントの場合、変更不可フィールドを除外
            if existing_agent.is_system:
                forbidden_fields = [
                    'executor_type', 'llm_model', 'system_prompt',
                    'user_prompt_template', 'response_format'
                ]
                for field in forbidden_fields:
                    if field in update_dict:
                        del update_dict[field]

            # 更新実行
            if update_dict:
                await self.agent_repo.update_agent(agent_id, update_dict)

            # ウェイクワード更新
            if agent_data.wake_words is not None:
                # 既存のウェイクワードを削除して新しく作成
                existing_wake_words = await self.agent_repo.get_agent_by_id(agent_id)
                for ww in existing_wake_words.wake_words:
                    await self.agent_repo.delete_wake_word(ww.id)

                for wake_word_data in agent_data.wake_words:
                    await self.agent_repo.create_wake_word(
                        agent_id=agent_id,
                        keyword=wake_word_data.keyword,
                        keyword_type=wake_word_data.match_type.value,
                        priority=wake_word_data.priority,
                        user_id=user_id
                    )

            # 能力更新
            if agent_data.capabilities is not None:
                # 既存の能力を削除して新しく作成
                existing_capabilities = await self.agent_repo.get_capabilities_by_agent(agent_id)
                for cap in existing_capabilities:
                    await self.agent_repo.delete_capability(cap.id)

                for capability_data in agent_data.capabilities:
                    await self.agent_repo.create_capability(
                        agent_id=agent_id,
                        capability_type=capability_data.task_type,
                        description=capability_data.description or "",
                        supported_task_types=[capability_data.task_type],
                        user_id=user_id
                    )

            # 更新後のエージェントを取得
            updated_agent = await self.agent_repo.get_agent_by_id(agent_id)

            logger.info(f"Updated agent: {agent_id} (user_id={user_id})")

            return AgentResponse.model_validate(updated_agent)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update agent: {str(e)}"
            )

    async def delete_agent(
        self,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        エージェントを削除

        システムエージェント、またはis_deletable=Falseのエージェントは削除不可

        Args:
            agent_id: エージェントID
            user_id: ユーザーID

        Returns:
            削除成功: True

        Raises:
            HTTPException: エージェントが存在しない、削除不可、権限エラー
        """
        try:
            # 既存エージェント取得
            existing_agent = await self.agent_repo.get_agent_by_id(agent_id)
            if not existing_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent not found: {agent_id}"
                )

            # 削除可能チェック
            if not await self.agent_repo.check_is_deletable(agent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This agent cannot be deleted (system agent or is_deletable=False)"
                )

            # 権限チェック
            if existing_agent.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this agent"
                )

            # 削除実行
            success = await self.agent_repo.delete_agent(agent_id)

            if success:
                logger.info(f"Deleted agent: {agent_id} (user_id={user_id})")
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete agent"
                )

            return success

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete agent: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete agent: {str(e)}"
            )

    async def list_agents(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None,
        executor_type: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> tuple[List[AgentListResponse], int]:
        """
        エージェント一覧を取得

        Args:
            user_id: ユーザーID（フィルタ）
            category: カテゴリ（フィルタ）
            is_active: アクティブ状態（フィルタ）
            is_system: システムエージェント（フィルタ）
            executor_type: 実行タイプ（フィルタ）
            search_query: 検索クエリ
            page: ページ番号
            limit: 1ページあたりの件数
            order_by: ソートカラム
            order_desc: 降順ソート

        Returns:
            (エージェント一覧, 総数)
        """
        try:
            offset = (page - 1) * limit

            agents, total_count = await self.agent_repo.get_all_agents(
                user_id=user_id,
                category=category,
                is_active=is_active,
                is_system=is_system,
                executor_type=executor_type,
                search_query=search_query,
                offset=offset,
                limit=limit,
                order_by=order_by,
                order_desc=order_desc
            )

            agent_list = [AgentListResponse.model_validate(agent) for agent in agents]

            return agent_list, total_count

        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list agents: {str(e)}"
            )

    async def get_statistics(
        self,
        user_id: Optional[str] = None
    ) -> AgentStatistics:
        """
        エージェント統計情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            統計情報
        """
        try:
            stats = await self.agent_repo.get_agents_statistics(user_id=user_id)

            return AgentStatistics(
                total_agents=stats["total_agents"],
                active_agents=stats["active_agents"],
                system_agents=stats["system_agents"],
                custom_agents=stats["custom_agents"],
                agents_by_category=stats["agents_by_category"],
                agents_by_executor_type=stats["agents_by_executor_type"]
            )

        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get statistics: {str(e)}"
            )

    async def get_agent_execution_stats(
        self,
        agent_id: str
    ) -> AgentExecutionStats:
        """
        エージェント実行統計を取得

        Args:
            agent_id: エージェントID

        Returns:
            実行統計
        """
        try:
            agent = await self.agent_repo.get_agent_by_id(agent_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent not found: {agent_id}"
                )

            stats = await self.agent_repo.get_agent_statistics(agent_id)

            # 最後の実行ログを取得
            logs = await self.agent_repo.get_execution_logs_by_agent(agent_id, limit=1)
            last_executed_at = logs[0].created_at if logs else None

            return AgentExecutionStats(
                agent_id=agent_id,
                agent_name=agent.name,
                total_executions=stats["total_executions"],
                success_count=stats["successful_executions"],
                failure_count=stats["total_executions"] - stats["successful_executions"],
                avg_execution_time_ms=float(stats["average_execution_time_ms"]),
                last_executed_at=last_executed_at
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get execution stats: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get execution stats: {str(e)}"
            )

    # === プライベートメソッド ===

    def _validate_system_agent_update(self, agent_data: AgentUpdate):
        """
        システムエージェントの更新データをバリデーション

        システムエージェントは以下のフィールドのみ更新可能：
        - display_name
        - description
        - is_active
        - priority

        Args:
            agent_data: 更新データ

        Raises:
            HTTPException: 禁止されたフィールドが含まれている場合
        """
        forbidden_updates = []

        # 変更不可フィールドをチェック
        if agent_data.executor_type is not None:
            forbidden_updates.append("executor_type")
        if agent_data.llm_model is not None:
            forbidden_updates.append("llm_model")
        if agent_data.system_prompt is not None:
            forbidden_updates.append("system_prompt")
        if agent_data.user_prompt_template is not None:
            forbidden_updates.append("user_prompt_template")
        if agent_data.response_format is not None:
            forbidden_updates.append("response_format")

        if forbidden_updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update these fields for system agents: {', '.join(forbidden_updates)}"
            )
