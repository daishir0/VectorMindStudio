"""
LangGraphエージェント管理リポジトリ

LangGraphエージェント、インテント、チェーンインテント、実行ログの
データベース操作を提供します。
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc
from datetime import datetime
import uuid

from app.domain.entities.langgraph_agent import (
    LangGraphAgent,
    LangGraphIntent,
    LangGraphChainIntent,
    LangGraphExecutionLog
)

logger = logging.getLogger(__name__)


class LangGraphAgentRepository:
    """
    LangGraphエージェント管理リポジトリ

    エージェント、インテント、チェーン、実行ログの永続化を担当します。
    """

    def __init__(self, session: AsyncSession):
        """
        Args:
            session: データベースセッション
        """
        self.session = session

    # ===== Agent CRUD =====

    async def create_agent(
        self,
        name: str,
        display_name: str,
        class_path: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> LangGraphAgent:
        """
        エージェントを作成

        Args:
            name: エージェント名（例: outline_agent）
            display_name: 表示名
            class_path: Pythonクラスパス
            description: 説明
            config: エージェント設定
            is_active: 有効/無効

        Returns:
            作成されたエージェント
        """
        agent = LangGraphAgent(
            id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            class_path=class_path,
            description=description,
            config=config or {},
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)

        logger.info(f"✅ エージェント作成: {name} (ID: {agent.id})")
        return agent

    async def get_agent_by_id(self, agent_id: str) -> Optional[LangGraphAgent]:
        """IDでエージェントを取得"""
        result = await self.session.execute(
            select(LangGraphAgent).where(LangGraphAgent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_agent_by_name(self, name: str) -> Optional[LangGraphAgent]:
        """名前でエージェントを取得"""
        result = await self.session.execute(
            select(LangGraphAgent).where(LangGraphAgent.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_agents(self, only_active: bool = True) -> List[LangGraphAgent]:
        """
        全エージェントを取得

        Args:
            only_active: 有効なエージェントのみ取得

        Returns:
            エージェントのリスト
        """
        query = select(LangGraphAgent)
        if only_active:
            query = query.where(LangGraphAgent.is_active == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_agent(
        self,
        agent_id: str,
        **kwargs
    ) -> Optional[LangGraphAgent]:
        """
        エージェントを更新

        Args:
            agent_id: エージェントID
            **kwargs: 更新するフィールド

        Returns:
            更新されたエージェント
        """
        kwargs['updated_at'] = datetime.utcnow()

        await self.session.execute(
            update(LangGraphAgent)
            .where(LangGraphAgent.id == agent_id)
            .values(**kwargs)
        )
        await self.session.commit()

        return await self.get_agent_by_id(agent_id)

    async def delete_agent(self, agent_id: str) -> bool:
        """
        エージェントを削除

        Args:
            agent_id: エージェントID

        Returns:
            削除成功したかどうか
        """
        result = await self.session.execute(
            delete(LangGraphAgent).where(LangGraphAgent.id == agent_id)
        )
        await self.session.commit()

        return result.rowcount > 0

    # ===== Intent CRUD =====

    async def create_intent(
        self,
        intent_name: str,
        display_name: str,
        agent_id: str,
        description: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
        example_query: Optional[str] = None,
        is_active: bool = True
    ) -> LangGraphIntent:
        """
        インテントを作成

        Args:
            intent_name: インテント名
            display_name: 表示名
            agent_id: 担当エージェントID
            description: 説明
            parameters_schema: パラメータスキーマ
            example_query: 例文
            is_active: 有効/無効

        Returns:
            作成されたインテント
        """
        intent = LangGraphIntent(
            id=str(uuid.uuid4()),
            intent_name=intent_name,
            display_name=display_name,
            agent_id=agent_id,
            description=description,
            parameters_schema=parameters_schema or {},
            example_query=example_query,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.session.add(intent)
        await self.session.commit()
        await self.session.refresh(intent)

        logger.info(f"✅ インテント作成: {intent_name} (ID: {intent.id})")
        return intent

    async def get_intent_by_name(self, intent_name: str) -> Optional[LangGraphIntent]:
        """名前でインテントを取得"""
        result = await self.session.execute(
            select(LangGraphIntent).where(LangGraphIntent.intent_name == intent_name)
        )
        return result.scalar_one_or_none()

    async def get_intents_by_agent(self, agent_id: str) -> List[LangGraphIntent]:
        """エージェントIDでインテント一覧を取得"""
        result = await self.session.execute(
            select(LangGraphIntent)
            .where(LangGraphIntent.agent_id == agent_id)
            .where(LangGraphIntent.is_active == True)
        )
        return list(result.scalars().all())

    async def get_all_intents(self, only_active: bool = True) -> List[LangGraphIntent]:
        """
        全インテントを取得

        Args:
            only_active: 有効なインテントのみ取得

        Returns:
            インテントのリスト
        """
        query = select(LangGraphIntent)
        if only_active:
            query = query.where(LangGraphIntent.is_active == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_intent(
        self,
        intent_id: str,
        **kwargs
    ) -> Optional[LangGraphIntent]:
        """
        インテントを更新

        Args:
            intent_id: インテントID
            **kwargs: 更新するフィールド

        Returns:
            更新されたインテント
        """
        kwargs['updated_at'] = datetime.utcnow()

        await self.session.execute(
            update(LangGraphIntent)
            .where(LangGraphIntent.id == intent_id)
            .values(**kwargs)
        )
        await self.session.commit()

        result = await self.session.execute(
            select(LangGraphIntent).where(LangGraphIntent.id == intent_id)
        )
        return result.scalar_one_or_none()

    # ===== Chain Intent CRUD =====

    async def create_chain_intent(
        self,
        chain_name: str,
        display_name: str,
        task_sequence: List[str],
        description: Optional[str] = None,
        example_query: Optional[str] = None,
        is_active: bool = True
    ) -> LangGraphChainIntent:
        """
        チェーンインテントを作成

        Args:
            chain_name: チェーン名
            display_name: 表示名
            task_sequence: タスク順序
            description: 説明
            example_query: 例文
            is_active: 有効/無効

        Returns:
            作成されたチェーンインテント
        """
        chain_intent = LangGraphChainIntent(
            id=str(uuid.uuid4()),
            chain_name=chain_name,
            display_name=display_name,
            task_sequence=task_sequence,
            description=description,
            example_query=example_query,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.session.add(chain_intent)
        await self.session.commit()
        await self.session.refresh(chain_intent)

        logger.info(f"✅ チェーンインテント作成: {chain_name} (ID: {chain_intent.id})")
        return chain_intent

    async def get_chain_intent_by_name(self, chain_name: str) -> Optional[LangGraphChainIntent]:
        """名前でチェーンインテントを取得"""
        result = await self.session.execute(
            select(LangGraphChainIntent).where(LangGraphChainIntent.chain_name == chain_name)
        )
        return result.scalar_one_or_none()

    async def get_all_chain_intents(self, only_active: bool = True) -> List[LangGraphChainIntent]:
        """
        全チェーンインテントを取得

        Args:
            only_active: 有効なチェーンインテントのみ取得

        Returns:
            チェーンインテントのリスト
        """
        query = select(LangGraphChainIntent)
        if only_active:
            query = query.where(LangGraphChainIntent.is_active == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ===== Execution Log =====

    async def create_execution_log(
        self,
        session_id: str,
        user_id: str,
        paper_id: str,
        user_query: str,
        intent: Optional[str] = None,
        intent_params: Optional[Dict[str, Any]] = None,
        agents_used: Optional[List[str]] = None,
        execution_time_ms: Optional[int] = None,
        loop_count: int = 0,
        validation_result: Optional[str] = None,
        final_response: Optional[str] = None,
        error: Optional[str] = None,
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> LangGraphExecutionLog:
        """
        実行ログを作成

        Args:
            session_id: セッションID
            user_id: ユーザーID
            paper_id: 論文ID
            user_query: ユーザー依頼
            intent: インテント
            intent_params: インテントパラメータ
            agents_used: 使用されたエージェント
            execution_time_ms: 実行時間（ミリ秒）
            loop_count: ループ回数
            validation_result: 検証結果
            final_response: 最終応答
            error: エラーメッセージ
            execution_metadata: メタデータ

        Returns:
            作成された実行ログ
        """
        log = LangGraphExecutionLog(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            paper_id=paper_id,
            user_query=user_query,
            intent=intent,
            intent_params=intent_params,
            agents_used=agents_used or [],
            execution_time_ms=execution_time_ms,
            loop_count=loop_count,
            validation_result=validation_result,
            final_response=final_response,
            error=error,
            execution_metadata=execution_metadata or {},
            created_at=datetime.utcnow()
        )

        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)

        logger.info(f"✅ 実行ログ作成: session={session_id}, intent={intent}")
        return log

    async def get_execution_logs_by_session(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[LangGraphExecutionLog]:
        """
        セッションIDで実行ログを取得

        Args:
            session_id: セッションID
            limit: 取得件数

        Returns:
            実行ログのリスト
        """
        result = await self.session.execute(
            select(LangGraphExecutionLog)
            .where(LangGraphExecutionLog.session_id == session_id)
            .order_by(desc(LangGraphExecutionLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_execution_logs_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[LangGraphExecutionLog]:
        """
        ユーザーIDで実行ログを取得

        Args:
            user_id: ユーザーID
            limit: 取得件数

        Returns:
            実行ログのリスト
        """
        result = await self.session.execute(
            select(LangGraphExecutionLog)
            .where(LangGraphExecutionLog.user_id == user_id)
            .order_by(desc(LangGraphExecutionLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_execution_stats(
        self,
        paper_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        実行統計を取得

        Args:
            paper_id: 論文ID（オプション）
            user_id: ユーザーID（オプション）

        Returns:
            統計情報の辞書
        """
        # ここでは簡易的な実装
        # 本来はSQLのaggregation関数を使うべき
        query = select(LangGraphExecutionLog)

        if paper_id:
            query = query.where(LangGraphExecutionLog.paper_id == paper_id)
        if user_id:
            query = query.where(LangGraphExecutionLog.user_id == user_id)

        result = await self.session.execute(query)
        logs = list(result.scalars().all())

        # 統計計算
        total_executions = len(logs)
        avg_execution_time = sum([log.execution_time_ms or 0 for log in logs]) / total_executions if total_executions > 0 else 0
        error_count = sum([1 for log in logs if log.error])

        intent_counts = {}
        for log in logs:
            if log.intent:
                intent_counts[log.intent] = intent_counts.get(log.intent, 0) + 1

        return {
            "total_executions": total_executions,
            "avg_execution_time_ms": avg_execution_time,
            "error_count": error_count,
            "success_rate": (total_executions - error_count) / total_executions if total_executions > 0 else 0,
            "intent_distribution": intent_counts
        }
