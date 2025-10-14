"""
AIエージェント管理APIエンドポイント
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.api.deps.auth import get_current_user
from app.domain.entities.user import User
from app.schemas.common import ApiResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# === Request/Response Models ===

class AgentResponse(BaseModel):
    """エージェント情報レスポンス"""
    id: str
    name: str
    display_name: str
    description: str
    category: str
    is_active: bool
    is_system: bool
    priority: int
    executor_type: str
    llm_model: Optional[str]
    system_prompt: str
    user_prompt_template: str
    tags: Optional[List[str]] = []
    usage_count: int = 0

    class Config:
        from_attributes = True


class AgentCreateRequest(BaseModel):
    """エージェント作成リクエスト"""
    name: str = Field(..., description="エージェント名（一意）")
    display_name: str = Field(..., description="表示名")
    description: str = Field(..., description="エージェントの説明")
    system_prompt: str = Field(..., description="システムプロンプト")
    user_prompt_template: str = Field(..., description="ユーザープロンプトテンプレート")
    category: str = Field(default="custom", description="カテゴリ")
    executor_type: str = Field(default="llm_based", description="実行タイプ")
    llm_model: str = Field(default="gpt-4o-mini", description="使用するLLMモデル")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    timeout_seconds: int = Field(default=90, description="タイムアウト秒数")
    priority: int = Field(default=10, description="優先度")
    tags: Optional[List[str]] = Field(default_factory=list, description="タグ")


class AgentUpdateRequest(BaseModel):
    """エージェント更新リクエスト"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    llm_model: Optional[str] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None


class AgentListResponse(BaseModel):
    """エージェント一覧レスポンス"""
    agents: List[AgentResponse]
    total: int


# === API Endpoints ===

@router.get("", response_model=ApiResponse[AgentListResponse])
async def list_agents(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェント一覧を取得

    - **category**: カテゴリでフィルタ（オプション）
    - **is_active**: アクティブ状態でフィルタ（オプション）
    """
    try:
        repository = AgentRepository(session)

        if category:
            agents = await repository.get_agents_by_category(category)
        elif is_active is not None:
            if is_active:
                agents = await repository.get_active_agents(user_id=current_user.id)
            else:
                # 非アクティブエージェントの取得ロジックは必要に応じて実装
                agents = await repository.get_active_agents(user_id=current_user.id)
        else:
            agents = await repository.get_active_agents(user_id=current_user.id)

        # 統計情報を取得してusage_countを設定
        agent_responses = []
        for agent in agents:
            stats = await repository.get_agent_statistics(agent.id)
            agent_response = AgentResponse(
                id=agent.id,
                name=agent.name,
                display_name=agent.display_name,
                description=agent.description,
                category=agent.category,
                is_active=agent.is_active,
                is_system=agent.is_system,
                priority=agent.priority,
                executor_type=agent.executor_type,
                llm_model=agent.llm_model,
                system_prompt=agent.system_prompt,
                user_prompt_template=agent.user_prompt_template,
                tags=agent.tags or [],
                usage_count=stats.get("total_executions", 0)
            )
            agent_responses.append(agent_response)

        return ApiResponse(
            success=True,
            data=AgentListResponse(
                agents=agent_responses,
                total=len(agent_responses)
            ),
            message=f"{len(agent_responses)}個のエージェントを取得しました"
        )

    except Exception as e:
        logger.error(f"エージェント一覧取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/{agent_id}", response_model=ApiResponse[AgentResponse])
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェント詳細を取得

    - **agent_id**: エージェントID
    """
    try:
        repository = AgentRepository(session)
        agent = await repository.get_agent_by_id(agent_id)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"エージェント {agent_id} が見つかりません"
            )

        # 統計情報を取得
        stats = await repository.get_agent_statistics(agent.id)

        agent_response = AgentResponse(
            id=agent.id,
            name=agent.name,
            display_name=agent.display_name,
            description=agent.description,
            category=agent.category,
            is_active=agent.is_active,
            is_system=agent.is_system,
            priority=agent.priority,
            executor_type=agent.executor_type,
            llm_model=agent.llm_model,
            system_prompt=agent.system_prompt,
            user_prompt_template=agent.user_prompt_template,
            tags=agent.tags or [],
            usage_count=stats.get("total_executions", 0)
        )

        return ApiResponse(
            success=True,
            data=agent_response,
            message=f"エージェント {agent.display_name} を取得しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェントの取得に失敗しました: {str(e)}"
        )


@router.post("", response_model=ApiResponse[AgentResponse], status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    新規エージェントを作成

    ユーザーが独自のエージェントを作成できます。
    """
    try:
        repository = AgentRepository(session)

        # 同名エージェントの存在チェック
        existing_agent = await repository.get_agent_by_name(request.name)
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"エージェント名 '{request.name}' は既に使用されています"
            )

        # エージェント作成
        agent = await repository.create_agent(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            category=request.category,
            executor_type=request.executor_type,
            llm_model=request.llm_model,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds,
            priority=request.priority,
            user_id=current_user.id,
            tags=request.tags
        )

        agent_response = AgentResponse(
            id=agent.id,
            name=agent.name,
            display_name=agent.display_name,
            description=agent.description,
            category=agent.category,
            is_active=agent.is_active,
            is_system=agent.is_system,
            priority=agent.priority,
            executor_type=agent.executor_type,
            llm_model=agent.llm_model,
            system_prompt=agent.system_prompt,
            user_prompt_template=agent.user_prompt_template,
            tags=agent.tags or [],
            usage_count=0
        )

        return ApiResponse(
            success=True,
            data=agent_response,
            message=f"エージェント {agent.display_name} を作成しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント作成エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェントの作成に失敗しました: {str(e)}"
        )


@router.put("/{agent_id}", response_model=ApiResponse[AgentResponse])
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントを更新

    - **agent_id**: 更新するエージェントのID
    """
    try:
        repository = AgentRepository(session)

        # エージェント存在チェック
        agent = await repository.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"エージェント {agent_id} が見つかりません"
            )

        # システムエージェントの保護
        if agent.is_system and current_user.id != agent.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="システムエージェントは編集できません"
            )

        # 更新データを作成
        update_data = {}
        if request.display_name is not None:
            update_data["display_name"] = request.display_name
        if request.description is not None:
            update_data["description"] = request.description
        if request.system_prompt is not None:
            update_data["system_prompt"] = request.system_prompt
        if request.user_prompt_template is not None:
            update_data["user_prompt_template"] = request.user_prompt_template
        if request.category is not None:
            update_data["category"] = request.category
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.llm_model is not None:
            update_data["llm_model"] = request.llm_model
        if request.max_retries is not None:
            update_data["max_retries"] = request.max_retries
        if request.timeout_seconds is not None:
            update_data["timeout_seconds"] = request.timeout_seconds
        if request.priority is not None:
            update_data["priority"] = request.priority
        if request.tags is not None:
            update_data["tags"] = request.tags

        # エージェント更新
        updated_agent = await repository.update_agent(agent_id, update_data)

        # 統計情報を取得
        stats = await repository.get_agent_statistics(updated_agent.id)

        agent_response = AgentResponse(
            id=updated_agent.id,
            name=updated_agent.name,
            display_name=updated_agent.display_name,
            description=updated_agent.description,
            category=updated_agent.category,
            is_active=updated_agent.is_active,
            is_system=updated_agent.is_system,
            priority=updated_agent.priority,
            executor_type=updated_agent.executor_type,
            llm_model=updated_agent.llm_model,
            system_prompt=updated_agent.system_prompt,
            user_prompt_template=updated_agent.user_prompt_template,
            tags=updated_agent.tags or [],
            usage_count=stats.get("total_executions", 0)
        )

        return ApiResponse(
            success=True,
            data=agent_response,
            message=f"エージェント {updated_agent.display_name} を更新しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント更新エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェントの更新に失敗しました: {str(e)}"
        )


@router.patch("/{agent_id}/toggle", response_model=ApiResponse[AgentResponse])
async def toggle_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントの有効/無効を切り替え

    - **agent_id**: エージェントID
    """
    try:
        repository = AgentRepository(session)

        # エージェント取得
        agent = await repository.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"エージェント {agent_id} が見つかりません"
            )

        # システムエージェントの保護（SupervisorAgentは常に有効）
        if agent.is_system and agent.name == "SupervisorAgent":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SupervisorAgentは無効化できません"
            )

        # 状態を切り替え
        new_is_active = not agent.is_active
        updated_agent = await repository.update_agent(
            agent_id,
            {"is_active": new_is_active}
        )

        # 統計情報を取得
        stats = await repository.get_agent_statistics(updated_agent.id)

        agent_response = AgentResponse(
            id=updated_agent.id,
            name=updated_agent.name,
            display_name=updated_agent.display_name,
            description=updated_agent.description,
            category=updated_agent.category,
            is_active=updated_agent.is_active,
            is_system=updated_agent.is_system,
            priority=updated_agent.priority,
            executor_type=updated_agent.executor_type,
            llm_model=updated_agent.llm_model,
            system_prompt=updated_agent.system_prompt,
            user_prompt_template=updated_agent.user_prompt_template,
            tags=updated_agent.tags or [],
            usage_count=stats.get("total_executions", 0)
        )

        status_text = "有効化" if new_is_active else "無効化"

        return ApiResponse(
            success=True,
            data=agent_response,
            message=f"エージェント {updated_agent.display_name} を{status_text}しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント切り替えエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェントの切り替えに失敗しました: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントを削除

    - **agent_id**: 削除するエージェントのID

    ⚠️ システムエージェントは削除できません
    """
    try:
        repository = AgentRepository(session)

        # エージェント取得
        agent = await repository.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"エージェント {agent_id} が見つかりません"
            )

        # システムエージェントの保護
        if agent.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="システムエージェントは削除できません"
            )

        # ユーザー所有権チェック
        if agent.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="他のユーザーのエージェントは削除できません"
            )

        # エージェント削除
        success = await repository.delete_agent(agent_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="エージェントの削除に失敗しました"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント削除エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェントの削除に失敗しました: {str(e)}"
        )


@router.get("/statistics/overview", response_model=ApiResponse[dict])
async def get_agent_statistics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェント全体の統計情報を取得

    - 総エージェント数
    - アクティブエージェント数
    - システムエージェント数
    - カスタムエージェント数
    - カテゴリ別集計
    - 実行タイプ別集計
    """
    try:
        repository = AgentRepository(session)
        stats = await repository.get_agents_statistics(user_id=current_user.id)

        return ApiResponse(
            success=True,
            data=stats,
            message="統計情報を取得しました"
        )

    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"統計情報の取得に失敗しました: {str(e)}"
        )


@router.get("/{agent_id}/execution-stats", response_model=ApiResponse[dict])
async def get_agent_execution_stats(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントの実行統計を取得

    - **agent_id**: エージェントID

    実行回数、成功率、平均実行時間などを返します
    """
    try:
        repository = AgentRepository(session)

        # エージェント存在チェック
        agent = await repository.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"エージェント {agent_id} が見つかりません"
            )

        # 実行統計を取得
        stats = await repository.get_agent_statistics(agent_id)

        # 最後の実行ログを取得
        logs = await repository.get_execution_logs_by_agent(agent_id, limit=1)
        last_executed_at = logs[0].created_at if logs else None

        execution_stats = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "total_executions": stats["total_executions"],
            "successful_executions": stats["successful_executions"],
            "success_rate": stats["success_rate"],
            "average_execution_time_ms": stats["average_execution_time_ms"],
            "last_executed_at": last_executed_at.isoformat() if last_executed_at else None
        }

        return ApiResponse(
            success=True,
            data=execution_stats,
            message=f"エージェント {agent.display_name} の実行統計を取得しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"実行統計取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"実行統計の取得に失敗しました: {str(e)}"
        )
