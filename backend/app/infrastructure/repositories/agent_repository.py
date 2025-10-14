"""
AIエージェント関連のデータベース操作を担当するリポジトリ
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from app.infrastructure.database.models import (
    AIAgentModel, AgentWakeWordModel, AgentCapabilityModel, AgentExecutionLogModel,
    AgentProfileModel, AgentProfileSettingModel
)


class AgentRepository:
    """AIエージェント関連のリポジトリクラス"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # === AIエージェント関連 ===
    async def create_agent(
        self,
        name: str,
        display_name: str,
        description: str,
        system_prompt: str,
        user_prompt_template: str,
        category: str = "custom",
        user_id: Optional[str] = None,
        **kwargs
    ) -> AIAgentModel:
        """新しいエージェントを作成"""
        agent = AIAgentModel(
            id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            category=category,
            user_id=user_id,
            **kwargs
        )

        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def get_agent_by_id(self, agent_id: str) -> Optional[AIAgentModel]:
        """IDでエージェントを取得（wake_wordsとcapabilitiesを含む）"""
        stmt = (
            select(AIAgentModel)
            .options(
                selectinload(AIAgentModel.wake_words),
                selectinload(AIAgentModel.capabilities)
            )
            .where(AIAgentModel.id == agent_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_agent_by_name(self, name: str) -> Optional[AIAgentModel]:
        """名前でエージェントを取得"""
        stmt = (
            select(AIAgentModel)
            .options(
                selectinload(AIAgentModel.wake_words),
                selectinload(AIAgentModel.capabilities)
            )
            .where(AIAgentModel.name == name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_agents(self, user_id: Optional[str] = None) -> List[AIAgentModel]:
        """アクティブなエージェント一覧を取得"""
        conditions = [AIAgentModel.is_active == True]
        if user_id:
            conditions.append(
                or_(
                    AIAgentModel.user_id == user_id,
                    AIAgentModel.is_system == True
                )
            )

        stmt = (
            select(AIAgentModel)
            .options(
                selectinload(AIAgentModel.wake_words),
                selectinload(AIAgentModel.capabilities)
            )
            .where(and_(*conditions))
            .order_by(AIAgentModel.priority.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_agents_by_category(self, category: str) -> List[AIAgentModel]:
        """カテゴリでエージェント一覧を取得"""
        stmt = (
            select(AIAgentModel)
            .options(
                selectinload(AIAgentModel.wake_words),
                selectinload(AIAgentModel.capabilities)
            )
            .where(
                and_(
                    AIAgentModel.category == category,
                    AIAgentModel.is_active == True
                )
            )
            .order_by(AIAgentModel.priority.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_agent(
        self,
        agent_id: str,
        update_data: Dict[str, Any]
    ) -> AIAgentModel:
        """エージェントを更新"""
        update_data["updated_at"] = datetime.utcnow()

        stmt = (
            update(AIAgentModel)
            .where(AIAgentModel.id == agent_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return await self.get_agent_by_id(agent_id)

    async def delete_agent(self, agent_id: str) -> bool:
        """エージェントを削除（wake_wordsとcapabilitiesも自動削除）"""
        stmt = delete(AIAgentModel).where(AIAgentModel.id == agent_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    # === Wake Word関連 ===
    async def create_wake_word(
        self,
        agent_id: str,
        keyword: str,
        keyword_type: str = "exact",
        priority: int = 10,
        user_id: Optional[str] = None,
        **kwargs
    ) -> AgentWakeWordModel:
        """新しいウェイクワードを作成"""
        wake_word = AgentWakeWordModel(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            keyword=keyword,
            keyword_type=keyword_type,
            priority=priority,
            user_id=user_id,
            **kwargs
        )

        self.session.add(wake_word)
        await self.session.commit()
        await self.session.refresh(wake_word)
        return wake_word

    async def get_active_wake_words(self, user_id: Optional[str] = None) -> List[AgentWakeWordModel]:
        """アクティブなウェイクワード一覧を取得"""
        conditions = [
            AgentWakeWordModel.is_active == True,
            AIAgentModel.is_active == True
        ]
        if user_id:
            conditions.append(
                or_(
                    AgentWakeWordModel.user_id == user_id,
                    AIAgentModel.is_system == True
                )
            )

        stmt = (
            select(AgentWakeWordModel)
            .join(AIAgentModel, AgentWakeWordModel.agent_id == AIAgentModel.id)
            .where(and_(*conditions))
            .order_by(
                AgentWakeWordModel.priority.asc(),
                AgentWakeWordModel.keyword.asc()
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_wake_word_usage(self, wake_word_id: str) -> bool:
        """ウェイクワードの使用回数を更新"""
        stmt = (
            update(AgentWakeWordModel)
            .where(AgentWakeWordModel.id == wake_word_id)
            .values(
                usage_count=AgentWakeWordModel.usage_count + 1,
                last_triggered_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def delete_wake_word(self, wake_word_id: str) -> bool:
        """ウェイクワードを削除"""
        stmt = delete(AgentWakeWordModel).where(AgentWakeWordModel.id == wake_word_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    # === Capability関連 ===
    async def create_capability(
        self,
        agent_id: str,
        capability_type: str,
        description: str,
        supported_task_types: List[str],
        user_id: Optional[str] = None,
        **kwargs
    ) -> AgentCapabilityModel:
        """新しい能力定義を作成"""
        capability = AgentCapabilityModel(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            capability_type=capability_type,
            description=description,
            supported_task_types=supported_task_types,
            user_id=user_id,
            **kwargs
        )

        self.session.add(capability)
        await self.session.commit()
        await self.session.refresh(capability)
        return capability

    async def get_capabilities_by_agent(self, agent_id: str) -> List[AgentCapabilityModel]:
        """エージェントの能力一覧を取得"""
        stmt = (
            select(AgentCapabilityModel)
            .where(AgentCapabilityModel.agent_id == agent_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_capability(self, capability_id: str) -> bool:
        """能力定義を削除"""
        stmt = delete(AgentCapabilityModel).where(AgentCapabilityModel.id == capability_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    # === Execution Log関連 ===
    async def create_execution_log(
        self,
        agent_id: str,
        session_id: str,
        user_id: str,
        user_message: str,
        status: str,
        execution_time_ms: int,
        triggered_by: str = "wake_word",
        **kwargs
    ) -> AgentExecutionLogModel:
        """実行ログを作成"""
        log = AgentExecutionLogModel(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            status=status,
            execution_time_ms=execution_time_ms,
            triggered_by=triggered_by,
            **kwargs
        )

        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_execution_logs_by_agent(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """エージェントの実行ログ一覧を取得"""
        stmt = (
            select(AgentExecutionLogModel)
            .where(AgentExecutionLogModel.agent_id == agent_id)
            .order_by(AgentExecutionLogModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_execution_logs_by_session(
        self,
        session_id: str
    ) -> List[AgentExecutionLogModel]:
        """セッションの実行ログ一覧を取得"""
        stmt = (
            select(AgentExecutionLogModel)
            .where(AgentExecutionLogModel.session_id == session_id)
            .order_by(AgentExecutionLogModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """エージェントの統計情報を取得"""
        # 総実行回数
        count_stmt = select(func.count(AgentExecutionLogModel.id)).where(
            AgentExecutionLogModel.agent_id == agent_id
        )
        count_result = await self.session.execute(count_stmt)
        total_executions = count_result.scalar() or 0

        # 成功回数
        success_stmt = select(func.count(AgentExecutionLogModel.id)).where(
            and_(
                AgentExecutionLogModel.agent_id == agent_id,
                AgentExecutionLogModel.status == "success"
            )
        )
        success_result = await self.session.execute(success_stmt)
        successful_executions = success_result.scalar() or 0

        # 平均実行時間
        avg_stmt = select(func.avg(AgentExecutionLogModel.execution_time_ms)).where(
            AgentExecutionLogModel.agent_id == agent_id
        )
        avg_result = await self.session.execute(avg_stmt)
        average_execution_time = avg_result.scalar() or 0

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "average_execution_time_ms": int(average_execution_time)
        }

    # === エージェント一覧・検索関連（拡張） ===
    async def get_all_agents(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None,
        executor_type: Optional[str] = None,
        search_query: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> tuple[List[AIAgentModel], int]:
        """
        エージェント一覧を取得（フィルタリング・ページネーション対応）

        Returns:
            (agents, total_count)のタプル
        """
        # 基本条件
        conditions = []

        # ユーザーフィルタ: システムエージェント または ユーザーのエージェント
        if user_id:
            conditions.append(
                or_(
                    AIAgentModel.is_system == True,
                    AIAgentModel.user_id == user_id
                )
            )

        # カテゴリフィルタ
        if category:
            conditions.append(AIAgentModel.category == category)

        # アクティブフィルタ
        if is_active is not None:
            conditions.append(AIAgentModel.is_active == is_active)

        # システムエージェントフィルタ
        if is_system is not None:
            conditions.append(AIAgentModel.is_system == is_system)

        # 実行タイプフィルタ
        if executor_type:
            conditions.append(AIAgentModel.executor_type == executor_type)

        # 検索クエリ
        if search_query:
            search_pattern = f"%{search_query}%"
            conditions.append(
                or_(
                    AIAgentModel.name.like(search_pattern),
                    AIAgentModel.display_name.like(search_pattern),
                    AIAgentModel.description.like(search_pattern)
                )
            )

        # 総数取得
        count_stmt = select(func.count(AIAgentModel.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # データ取得
        stmt = select(AIAgentModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # ソート
        order_column = getattr(AIAgentModel, order_by, AIAgentModel.created_at)
        if order_desc:
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())

        # ページネーション
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        agents = list(result.scalars().all())

        return agents, total_count

    async def check_is_deletable(self, agent_id: str) -> bool:
        """エージェントが削除可能かチェック"""
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            return False

        # is_deletable=Falseの場合は削除不可
        if not agent.is_deletable:
            return False

        # システムエージェントは削除不可
        if agent.is_system:
            return False

        return True

    async def get_system_agents(self) -> List[AIAgentModel]:
        """システムエージェント一覧を取得"""
        stmt = (
            select(AIAgentModel)
            .options(
                selectinload(AIAgentModel.wake_words),
                selectinload(AIAgentModel.capabilities)
            )
            .where(AIAgentModel.is_system == True)
            .order_by(AIAgentModel.priority.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_agents_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """エージェント全体の統計情報を取得"""
        conditions = []
        if user_id:
            conditions.append(
                or_(
                    AIAgentModel.is_system == True,
                    AIAgentModel.user_id == user_id
                )
            )

        # 総数
        total_stmt = select(func.count(AIAgentModel.id))
        if conditions:
            total_stmt = total_stmt.where(and_(*conditions))
        total_result = await self.session.execute(total_stmt)
        total_agents = total_result.scalar() or 0

        # アクティブ数
        active_conditions = conditions + [AIAgentModel.is_active == True]
        active_stmt = select(func.count(AIAgentModel.id)).where(and_(*active_conditions))
        active_result = await self.session.execute(active_stmt)
        active_agents = active_result.scalar() or 0

        # システムエージェント数
        system_conditions = conditions + [AIAgentModel.is_system == True]
        system_stmt = select(func.count(AIAgentModel.id)).where(and_(*system_conditions))
        system_result = await self.session.execute(system_stmt)
        system_agents = system_result.scalar() or 0

        # カスタムエージェント数
        custom_agents = total_agents - system_agents

        # カテゴリ別
        category_stmt = select(
            AIAgentModel.category,
            func.count(AIAgentModel.id)
        )
        if conditions:
            category_stmt = category_stmt.where(and_(*conditions))
        category_stmt = category_stmt.group_by(AIAgentModel.category)

        category_result = await self.session.execute(category_stmt)
        agents_by_category = {row[0]: row[1] for row in category_result.all()}

        # 実行タイプ別
        executor_stmt = select(
            AIAgentModel.executor_type,
            func.count(AIAgentModel.id)
        )
        if conditions:
            executor_stmt = executor_stmt.where(and_(*conditions))
        executor_stmt = executor_stmt.group_by(AIAgentModel.executor_type)

        executor_result = await self.session.execute(executor_stmt)
        agents_by_executor_type = {row[0]: row[1] for row in executor_result.all()}

        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "system_agents": system_agents,
            "custom_agents": custom_agents,
            "agents_by_category": agents_by_category,
            "agents_by_executor_type": agents_by_executor_type
        }

    # === Agent Profile関連 ===
    async def create_profile(
        self,
        name: str,
        paper_type: str,
        description: Optional[str] = None,
        is_default: bool = False,
        user_id: Optional[str] = None
    ) -> AgentProfileModel:
        """新しいプロファイルを作成"""
        profile = AgentProfileModel(
            id=str(uuid.uuid4()),
            name=name,
            paper_type=paper_type,
            description=description,
            is_default=is_default,
            user_id=user_id
        )

        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_profile_by_id(self, profile_id: str) -> Optional[AgentProfileModel]:
        """IDでプロファイルを取得"""
        stmt = (
            select(AgentProfileModel)
            .options(selectinload(AgentProfileModel.settings))
            .where(AgentProfileModel.id == profile_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_profiles_by_paper_type(
        self,
        paper_type: str,
        user_id: Optional[str] = None
    ) -> List[AgentProfileModel]:
        """論文タイプでプロファイル一覧を取得"""
        conditions = [AgentProfileModel.paper_type == paper_type]

        if user_id:
            conditions.append(
                or_(
                    AgentProfileModel.user_id == user_id,
                    AgentProfileModel.user_id == None  # グローバルプロファイル
                )
            )

        stmt = (
            select(AgentProfileModel)
            .options(selectinload(AgentProfileModel.settings))
            .where(and_(*conditions))
            .order_by(AgentProfileModel.is_default.desc(), AgentProfileModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_default_profile(
        self,
        paper_type: str,
        user_id: Optional[str] = None
    ) -> Optional[AgentProfileModel]:
        """デフォルトプロファイルを取得"""
        conditions = [
            AgentProfileModel.paper_type == paper_type,
            AgentProfileModel.is_default == True
        ]

        if user_id:
            conditions.append(
                or_(
                    AgentProfileModel.user_id == user_id,
                    AgentProfileModel.user_id == None
                )
            )

        stmt = (
            select(AgentProfileModel)
            .options(selectinload(AgentProfileModel.settings))
            .where(and_(*conditions))
            .order_by(AgentProfileModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_profiles(
        self,
        user_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 20
    ) -> tuple[List[AgentProfileModel], int]:
        """プロファイル一覧を取得"""
        conditions = []

        if user_id:
            conditions.append(
                or_(
                    AgentProfileModel.user_id == user_id,
                    AgentProfileModel.user_id == None
                )
            )

        # 総数取得
        count_stmt = select(func.count(AgentProfileModel.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # データ取得
        stmt = select(AgentProfileModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = (
            stmt
            .options(selectinload(AgentProfileModel.settings))
            .order_by(AgentProfileModel.paper_type.asc(), AgentProfileModel.is_default.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        profiles = list(result.scalars().all())

        return profiles, total_count

    async def update_profile(
        self,
        profile_id: str,
        update_data: Dict[str, Any]
    ) -> AgentProfileModel:
        """プロファイルを更新"""
        update_data["updated_at"] = datetime.utcnow()

        stmt = (
            update(AgentProfileModel)
            .where(AgentProfileModel.id == profile_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        return await self.get_profile_by_id(profile_id)

    async def delete_profile(self, profile_id: str) -> bool:
        """プロファイルを削除"""
        stmt = delete(AgentProfileModel).where(AgentProfileModel.id == profile_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    # === Agent Profile Settings関連 ===
    async def create_profile_setting(
        self,
        profile_id: str,
        agent_id: str,
        is_enabled: bool = True,
        priority_override: Optional[int] = None,
        wake_words_override: Optional[List[Dict[str, Any]]] = None
    ) -> AgentProfileSettingModel:
        """プロファイル設定を作成"""
        setting = AgentProfileSettingModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            agent_id=agent_id,
            is_enabled=is_enabled,
            priority_override=priority_override,
            wake_words_override=wake_words_override
        )

        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def get_settings_by_profile(
        self,
        profile_id: str
    ) -> List[AgentProfileSettingModel]:
        """プロファイルの設定一覧を取得"""
        stmt = (
            select(AgentProfileSettingModel)
            .options(selectinload(AgentProfileSettingModel.agent))
            .where(AgentProfileSettingModel.profile_id == profile_id)
            .order_by(AgentProfileSettingModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_profile_setting(
        self,
        profile_id: str,
        agent_id: str
    ) -> Optional[AgentProfileSettingModel]:
        """特定のプロファイル設定を取得"""
        stmt = (
            select(AgentProfileSettingModel)
            .where(
                and_(
                    AgentProfileSettingModel.profile_id == profile_id,
                    AgentProfileSettingModel.agent_id == agent_id
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_profile_setting(
        self,
        setting_id: str,
        update_data: Dict[str, Any]
    ) -> AgentProfileSettingModel:
        """プロファイル設定を更新"""
        update_data["updated_at"] = datetime.utcnow()

        stmt = (
            update(AgentProfileSettingModel)
            .where(AgentProfileSettingModel.id == setting_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        # 更新後のデータを取得
        get_stmt = select(AgentProfileSettingModel).where(
            AgentProfileSettingModel.id == setting_id
        )
        result = await self.session.execute(get_stmt)
        return result.scalar_one()

    async def delete_profile_setting(self, setting_id: str) -> bool:
        """プロファイル設定を削除"""
        stmt = delete(AgentProfileSettingModel).where(
            AgentProfileSettingModel.id == setting_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def bulk_update_profile_settings(
        self,
        profile_id: str,
        settings_data: List[Dict[str, Any]]
    ) -> List[AgentProfileSettingModel]:
        """プロファイル設定を一括更新"""
        # 既存設定を全削除
        delete_stmt = delete(AgentProfileSettingModel).where(
            AgentProfileSettingModel.profile_id == profile_id
        )
        await self.session.execute(delete_stmt)

        # 新しい設定を一括作成
        new_settings = []
        for setting_data in settings_data:
            setting = AgentProfileSettingModel(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                **setting_data
            )
            new_settings.append(setting)
            self.session.add(setting)

        await self.session.commit()

        # リフレッシュ
        for setting in new_settings:
            await self.session.refresh(setting)

        return new_settings
