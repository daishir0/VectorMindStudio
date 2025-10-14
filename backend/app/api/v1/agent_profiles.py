"""
エージェントプロファイル管理API

論文タイプ別のエージェント設定プロファイルのCRUD操作を提供
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.schemas.agent import (
    AgentProfileCreate, AgentProfileUpdate, AgentProfileResponse,
    AgentProfileSettingCreate, AgentProfileSettingResponse,
    PaperType
)
from app.schemas.common import ApiResponse
from app.api.deps.auth import get_current_user
from app.infrastructure.database.models import UserModel

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-profiles", tags=["Agent Profiles"])


@router.get("", response_model=ApiResponse[List[AgentProfileResponse]])
async def list_profiles(
    paper_type: Optional[PaperType] = Query(None, description="論文タイプでフィルタ"),
    is_default: Optional[bool] = Query(None, description="デフォルトプロファイルでフィルタ"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントプロファイル一覧を取得

    - システムデフォルトプロファイル + ユーザー作成プロファイルを返す
    - paper_typeでフィルタ可能
    """
    try:
        repo = AgentRepository(session)

        # システムデフォルトプロファイル
        system_profiles = await repo.get_profiles_by_paper_type(
            paper_type=paper_type.value if paper_type else None,
            user_id=None
        )

        # ユーザー作成プロファイル
        user_profiles = await repo.get_profiles_by_paper_type(
            paper_type=paper_type.value if paper_type else None,
            user_id=current_user.id
        )

        all_profiles = system_profiles + user_profiles

        # is_defaultフィルタ
        if is_default is not None:
            all_profiles = [p for p in all_profiles if p.is_default == is_default]

        return ApiResponse(
            success=True,
            data=[AgentProfileResponse.model_validate(p) for p in all_profiles],
            message=f"{len(all_profiles)}件のプロファイルを取得しました"
        )

    except Exception as e:
        logger.error(f"Failed to list profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル一覧取得に失敗: {str(e)}"
        )


@router.get("/{profile_id}", response_model=ApiResponse[AgentProfileResponse])
async def get_profile(
    profile_id: str,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントプロファイル詳細を取得
    """
    try:
        repo = AgentRepository(session)
        profile = await repo.get_profile_by_id(profile_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"プロファイルが見つかりません: {profile_id}"
            )

        # 権限チェック（システムプロファイルは全員アクセス可、ユーザープロファイルは所有者のみ）
        if profile.user_id and profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このプロファイルにアクセスする権限がありません"
            )

        return ApiResponse(
            success=True,
            data=AgentProfileResponse.model_validate(profile),
            message="プロファイルを取得しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル取得に失敗: {str(e)}"
        )


@router.post("", response_model=ApiResponse[AgentProfileResponse], status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: AgentProfileCreate,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    新しいエージェントプロファイルを作成

    - ユーザー固有のプロファイルを作成
    - 初期設定（エージェント有効化状態等）も同時に設定可能
    """
    try:
        repo = AgentRepository(session)

        # 名前重複チェック（同一ユーザー内）
        existing_profiles = await repo.get_profiles_by_paper_type(
            paper_type=profile_data.paper_type.value,
            user_id=current_user.id
        )
        if any(p.name == profile_data.name for p in existing_profiles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"同じ名前のプロファイルが既に存在します: {profile_data.name}"
            )

        # プロファイル作成
        profile = await repo.create_profile(
            name=profile_data.name,
            description=profile_data.description,
            paper_type=profile_data.paper_type.value,
            is_default=profile_data.is_default or False,
            user_id=current_user.id
        )

        # 設定を追加（指定されている場合）
        if profile_data.settings:
            for setting_data in profile_data.settings:
                await repo.create_profile_setting(
                    profile_id=profile.id,
                    agent_id=setting_data.agent_id,
                    is_enabled=setting_data.is_enabled,
                    priority_override=setting_data.priority_override,
                    wake_words_override=setting_data.wake_words_override
                )

        # 作成後のプロファイルを取得（settingsを含む）
        created_profile = await repo.get_profile_by_id(profile.id)

        logger.info(f"Created profile: {profile.id} (name={profile.name}, user_id={current_user.id})")

        return ApiResponse(
            success=True,
            data=AgentProfileResponse.model_validate(created_profile),
            message="プロファイルを作成しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル作成に失敗: {str(e)}"
        )


@router.put("/{profile_id}", response_model=ApiResponse[AgentProfileResponse])
async def update_profile(
    profile_id: str,
    profile_data: AgentProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントプロファイルを更新

    - システムプロファイルは更新不可
    - ユーザープロファイルは所有者のみ更新可能
    """
    try:
        repo = AgentRepository(session)

        # 既存プロファイル取得
        existing_profile = await repo.get_profile_by_id(profile_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"プロファイルが見つかりません: {profile_id}"
            )

        # 権限チェック
        if not existing_profile.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="システムプロファイルは更新できません"
            )

        if existing_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このプロファイルを更新する権限がありません"
            )

        # 更新データ準備
        update_dict = profile_data.model_dump(exclude_unset=True, exclude={'settings'})

        # paper_typeのEnumを文字列に変換
        if 'paper_type' in update_dict and update_dict['paper_type']:
            update_dict['paper_type'] = update_dict['paper_type'].value

        # プロファイル更新
        if update_dict:
            await repo.update_profile(profile_id, update_dict)

        # 設定の更新（指定されている場合）
        if profile_data.settings is not None:
            # 既存の設定を削除
            existing_settings = await repo.get_profile_settings(profile_id)
            for setting in existing_settings:
                await repo.delete_profile_setting(setting.id)

            # 新しい設定を追加
            for setting_data in profile_data.settings:
                await repo.create_profile_setting(
                    profile_id=profile_id,
                    agent_id=setting_data.agent_id,
                    is_enabled=setting_data.is_enabled,
                    priority_override=setting_data.priority_override,
                    wake_words_override=setting_data.wake_words_override
                )

        # 更新後のプロファイルを取得
        updated_profile = await repo.get_profile_by_id(profile_id)

        logger.info(f"Updated profile: {profile_id} (user_id={current_user.id})")

        return ApiResponse(
            success=True,
            data=AgentProfileResponse.model_validate(updated_profile),
            message="プロファイルを更新しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル更新に失敗: {str(e)}"
        )


@router.delete("/{profile_id}", response_model=ApiResponse[dict])
async def delete_profile(
    profile_id: str,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    エージェントプロファイルを削除

    - システムプロファイルは削除不可
    - ユーザープロファイルは所有者のみ削除可能
    """
    try:
        repo = AgentRepository(session)

        # 既存プロファイル取得
        existing_profile = await repo.get_profile_by_id(profile_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"プロファイルが見つかりません: {profile_id}"
            )

        # 権限チェック
        if not existing_profile.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="システムプロファイルは削除できません"
            )

        if existing_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このプロファイルを削除する権限がありません"
            )

        # プロファイル削除
        success = await repo.delete_profile(profile_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="プロファイルの削除に失敗しました"
            )

        logger.info(f"Deleted profile: {profile_id} (user_id={current_user.id})")

        return ApiResponse(
            success=True,
            data={"deleted": True, "profile_id": profile_id},
            message="プロファイルを削除しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロファイル削除に失敗: {str(e)}"
        )


@router.put("/{profile_id}/settings", response_model=ApiResponse[AgentProfileResponse])
async def bulk_update_profile_settings(
    profile_id: str,
    settings: List[AgentProfileSettingCreate],
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    プロファイル設定を一括更新

    - 既存の設定をすべて削除して、新しい設定に置き換える
    - エージェントの有効/無効、優先度、ウェイクワードを一括設定
    """
    try:
        repo = AgentRepository(session)

        # 既存プロファイル取得
        existing_profile = await repo.get_profile_by_id(profile_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"プロファイルが見つかりません: {profile_id}"
            )

        # 権限チェック
        if existing_profile.user_id and existing_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このプロファイルの設定を更新する権限がありません"
            )

        # 設定を一括更新
        await repo.bulk_update_profile_settings(
            profile_id=profile_id,
            settings=[
                {
                    "agent_id": s.agent_id,
                    "is_enabled": s.is_enabled,
                    "priority_override": s.priority_override,
                    "wake_words_override": s.wake_words_override
                }
                for s in settings
            ]
        )

        # 更新後のプロファイルを取得
        updated_profile = await repo.get_profile_by_id(profile_id)

        logger.info(f"Bulk updated settings for profile: {profile_id} ({len(settings)}件)")

        return ApiResponse(
            success=True,
            data=AgentProfileResponse.model_validate(updated_profile),
            message=f"{len(settings)}件の設定を更新しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk update settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"設定の一括更新に失敗: {str(e)}"
        )


@router.post("/{profile_id}/set-default", response_model=ApiResponse[AgentProfileResponse])
async def set_default_profile(
    profile_id: str,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    プロファイルをデフォルトに設定

    - 同一paper_type内で1つのみデフォルト設定可能
    - ユーザープロファイルのみ設定可能（システムプロファイルは不可）
    """
    try:
        repo = AgentRepository(session)

        # 既存プロファイル取得
        existing_profile = await repo.get_profile_by_id(profile_id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"プロファイルが見つかりません: {profile_id}"
            )

        # 権限チェック
        if not existing_profile.user_id or existing_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このプロファイルをデフォルトに設定する権限がありません"
            )

        # 同一paper_typeの他のプロファイルのデフォルトを解除
        user_profiles = await repo.get_profiles_by_paper_type(
            paper_type=existing_profile.paper_type,
            user_id=current_user.id
        )

        for profile in user_profiles:
            if profile.id != profile_id and profile.is_default:
                await repo.update_profile(profile.id, {"is_default": False})

        # このプロファイルをデフォルトに設定
        await repo.update_profile(profile_id, {"is_default": True})

        # 更新後のプロファイルを取得
        updated_profile = await repo.get_profile_by_id(profile_id)

        logger.info(f"Set default profile: {profile_id} (paper_type={existing_profile.paper_type})")

        return ApiResponse(
            success=True,
            data=AgentProfileResponse.model_validate(updated_profile),
            message="デフォルトプロファイルを設定しました"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set default profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"デフォルトプロファイル設定に失敗: {str(e)}"
        )
