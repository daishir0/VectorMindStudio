"""
LangGraphエージェント管理APIエンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.infrastructure.database.session import get_session
from app.schemas.langgraph_agent import (
    LangGraphAgentCreate,
    LangGraphAgentUpdate,
    LangGraphAgentDetail,
    LangGraphIntentCreate,
    LangGraphIntentDetail,
    LangGraphIntentWithAgent,
    LangGraphChainIntentCreate,
    LangGraphChainIntentDetail,
    LangGraphExecutionLogSummary,
    LangGraphExecutionStatsResponse,
    AgentListResponse,
    IntentListResponse,
    ChainIntentListResponse
)
from app.schemas.common import ApiResponse
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user
from app.infrastructure.repositories.langgraph_agent_repository import LangGraphAgentRepository

router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Agent Management Endpoints =====

@router.get("/agents", response_model=ApiResponse[AgentListResponse])
async def get_agents(
    only_active: bool = Query(True, description="有効なエージェントのみ取得"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェント一覧を取得

    LangGraphで使用可能なエージェントの一覧を返します。
    """
    try:
        repository = LangGraphAgentRepository(session)
        agents = await repository.get_all_agents(only_active=only_active)

        agent_details = [
            LangGraphAgentDetail.from_orm(agent) for agent in agents
        ]

        return ApiResponse(
            success=True,
            data=AgentListResponse(
                agents=agent_details,
                total=len(agent_details)
            )
        )

    except Exception as e:
        logger.error(f"エージェント一覧取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント一覧取得に失敗しました: {e}"
        )


@router.get("/agents/{agent_id}", response_model=ApiResponse[LangGraphAgentDetail])
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """エージェント詳細を取得"""
    try:
        repository = LangGraphAgentRepository(session)
        agent = await repository.get_agent_by_id(agent_id)

        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="エージェントが見つかりません"
            )

        return ApiResponse(
            success=True,
            data=LangGraphAgentDetail.from_orm(agent)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント取得に失敗しました: {e}"
        )


@router.post("/agents", response_model=ApiResponse[LangGraphAgentDetail], status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: LangGraphAgentCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """新しいエージェントを作成"""
    try:
        repository = LangGraphAgentRepository(session)

        # 重複チェック
        existing_agent = await repository.get_agent_by_name(agent_data.name)
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"エージェント '{agent_data.name}' は既に存在します"
            )

        agent = await repository.create_agent(
            name=agent_data.name,
            display_name=agent_data.display_name,
            class_path=agent_data.class_path,
            description=agent_data.description,
            config=agent_data.config,
            is_active=agent_data.is_active
        )

        return ApiResponse(
            success=True,
            data=LangGraphAgentDetail.from_orm(agent),
            message="エージェントを作成しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント作成エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント作成に失敗しました: {e}"
        )


@router.put("/agents/{agent_id}", response_model=ApiResponse[LangGraphAgentDetail])
async def update_agent(
    agent_id: str,
    agent_data: LangGraphAgentUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """エージェントを更新"""
    try:
        repository = LangGraphAgentRepository(session)

        # 存在確認
        existing_agent = await repository.get_agent_by_id(agent_id)
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="エージェントが見つかりません"
            )

        # 更新データを準備
        update_data = agent_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新するデータが指定されていません"
            )

        updated_agent = await repository.update_agent(agent_id, **update_data)

        return ApiResponse(
            success=True,
            data=LangGraphAgentDetail.from_orm(updated_agent),
            message="エージェントを更新しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント更新エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント更新に失敗しました: {e}"
        )


@router.delete("/agents/{agent_id}", response_model=ApiResponse[dict])
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """エージェントを削除"""
    try:
        repository = LangGraphAgentRepository(session)

        # 存在確認
        existing_agent = await repository.get_agent_by_id(agent_id)
        if not existing_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="エージェントが見つかりません"
            )

        success = await repository.delete_agent(agent_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="エージェント削除に失敗しました"
            )

        return ApiResponse(
            success=True,
            data={"message": "エージェントを削除しました"},
            message="エージェントを削除しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント削除エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント削除に失敗しました: {e}"
        )


# ===== Intent Management Endpoints =====

@router.get("/intents", response_model=ApiResponse[IntentListResponse])
async def get_intents(
    agent_id: Optional[str] = Query(None, description="エージェントIDでフィルタ"),
    only_active: bool = Query(True, description="有効なインテントのみ取得"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """
    インテント一覧を取得

    特定のエージェントのインテント、または全インテントを取得します。
    """
    try:
        repository = LangGraphAgentRepository(session)

        if agent_id:
            intents = await repository.get_intents_by_agent(agent_id)
        else:
            intents = await repository.get_all_intents(only_active=only_active)

        # エージェント情報を付与
        intent_with_agents = []
        for intent in intents:
            agent = await repository.get_agent_by_id(intent.agent_id)
            intent_data = LangGraphIntentWithAgent(
                **LangGraphIntentDetail.from_orm(intent).dict(),
                agent_name=agent.name if agent else "",
                agent_display_name=agent.display_name if agent else ""
            )
            intent_with_agents.append(intent_data)

        return ApiResponse(
            success=True,
            data=IntentListResponse(
                intents=intent_with_agents,
                total=len(intent_with_agents)
            )
        )

    except Exception as e:
        logger.error(f"インテント一覧取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"インテント一覧取得に失敗しました: {e}"
        )


@router.post("/intents", response_model=ApiResponse[LangGraphIntentDetail], status_code=status.HTTP_201_CREATED)
async def create_intent(
    intent_data: LangGraphIntentCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """新しいインテントを作成"""
    try:
        repository = LangGraphAgentRepository(session)

        # エージェント存在確認
        agent = await repository.get_agent_by_id(intent_data.agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたエージェントが見つかりません"
            )

        # 重複チェック
        existing_intent = await repository.get_intent_by_name(intent_data.intent_name)
        if existing_intent:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"インテント '{intent_data.intent_name}' は既に存在します"
            )

        intent = await repository.create_intent(
            intent_name=intent_data.intent_name,
            display_name=intent_data.display_name,
            agent_id=intent_data.agent_id,
            description=intent_data.description,
            parameters_schema=intent_data.parameters_schema,
            example_query=intent_data.example_query,
            is_active=intent_data.is_active
        )

        return ApiResponse(
            success=True,
            data=LangGraphIntentDetail.from_orm(intent),
            message="インテントを作成しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"インテント作成エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"インテント作成に失敗しました: {e}"
        )


# ===== Chain Intent Management Endpoints =====

@router.get("/chains", response_model=ApiResponse[ChainIntentListResponse])
async def get_chain_intents(
    only_active: bool = Query(True, description="有効なチェーンインテントのみ取得"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """チェーンインテント一覧を取得"""
    try:
        repository = LangGraphAgentRepository(session)
        chain_intents = await repository.get_all_chain_intents(only_active=only_active)

        chain_intent_details = [
            LangGraphChainIntentDetail.from_orm(chain) for chain in chain_intents
        ]

        return ApiResponse(
            success=True,
            data=ChainIntentListResponse(
                chain_intents=chain_intent_details,
                total=len(chain_intent_details)
            )
        )

    except Exception as e:
        logger.error(f"チェーンインテント一覧取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チェーンインテント一覧取得に失敗しました: {e}"
        )


@router.post("/chains", response_model=ApiResponse[LangGraphChainIntentDetail], status_code=status.HTTP_201_CREATED)
async def create_chain_intent(
    chain_data: LangGraphChainIntentCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """新しいチェーンインテントを作成"""
    try:
        repository = LangGraphAgentRepository(session)

        # 重複チェック
        existing_chain = await repository.get_chain_intent_by_name(chain_data.chain_name)
        if existing_chain:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"チェーンインテント '{chain_data.chain_name}' は既に存在します"
            )

        chain_intent = await repository.create_chain_intent(
            chain_name=chain_data.chain_name,
            display_name=chain_data.display_name,
            task_sequence=chain_data.task_sequence,
            description=chain_data.description,
            example_query=chain_data.example_query,
            is_active=chain_data.is_active
        )

        return ApiResponse(
            success=True,
            data=LangGraphChainIntentDetail.from_orm(chain_intent),
            message="チェーンインテントを作成しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チェーンインテント作成エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チェーンインテント作成に失敗しました: {e}"
        )


# ===== Execution Log Endpoints =====

@router.get("/logs", response_model=ApiResponse[List[LangGraphExecutionLogSummary]])
async def get_execution_logs(
    session_id: Optional[str] = Query(None, description="セッションIDでフィルタ"),
    user_id: Optional[str] = Query(None, description="ユーザーIDでフィルタ"),
    limit: int = Query(50, ge=1, le=200, description="取得件数"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """実行ログを取得"""
    try:
        repository = LangGraphAgentRepository(session)

        if session_id:
            logs = await repository.get_execution_logs_by_session(session_id, limit=limit)
        elif user_id:
            logs = await repository.get_execution_logs_by_user(user_id, limit=limit)
        else:
            # デフォルトは現在のユーザーのログ
            logs = await repository.get_execution_logs_by_user(current_user.id, limit=limit)

        log_summaries = [
            LangGraphExecutionLogSummary.from_orm(log) for log in logs
        ]

        return ApiResponse(
            success=True,
            data=log_summaries
        )

    except Exception as e:
        logger.error(f"実行ログ取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"実行ログ取得に失敗しました: {e}"
        )


@router.get("/stats", response_model=ApiResponse[LangGraphExecutionStatsResponse])
async def get_execution_stats(
    paper_id: Optional[str] = Query(None, description="論文IDでフィルタ"),
    user_id: Optional[str] = Query(None, description="ユーザーIDでフィルタ"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """実行統計を取得"""
    try:
        repository = LangGraphAgentRepository(session)

        # user_idが指定されていない場合は現在のユーザーを使用
        if not user_id:
            user_id = current_user.id

        stats = await repository.get_execution_stats(
            paper_id=paper_id,
            user_id=user_id
        )

        return ApiResponse(
            success=True,
            data=LangGraphExecutionStatsResponse(**stats)
        )

    except Exception as e:
        logger.error(f"実行統計取得エラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"実行統計取得に失敗しました: {e}"
        )
