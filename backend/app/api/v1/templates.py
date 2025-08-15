from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
import uuid
from datetime import datetime

from app.infrastructure.database.session import get_session
from app.infrastructure.database.models import TemplateModel, UserModel
from app.infrastructure.external.openai_client import openai_client
from app.services.vector_service import VectorService
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplateUse
)
from app.schemas.common import ApiResponse, MessageResponse, PaginationParams, PaginatedResponse
from app.domain.entities.user import User
from app.domain.entities.template import TemplateStatus, TemplateVariable
from app.api.deps.auth import get_current_active_user, get_optional_current_user

router = APIRouter()

@router.get("", response_model=ApiResponse[PaginatedResponse[TemplateListResponse]])
async def get_templates(
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    search: Optional[str] = Query(None, description="検索クエリ"),
    status: Optional[TemplateStatus] = Query(None, description="ステータスフィルター"),
    user_id: Optional[str] = Query(None, description="作成者フィルター"),
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """テンプレート一覧取得"""
    
    # ベースクエリ
    query = select(TemplateModel)
    
    # 検索フィルター
    if search:
        search_filter = or_(
            TemplateModel.name.contains(search),
            TemplateModel.description.contains(search),
            TemplateModel.content.contains(search)
        )
        query = query.where(search_filter)
    
    # ステータスフィルター
    if status:
        query = query.where(TemplateModel.status == status)
    
    
    # 作成者フィルター
    if user_id:
        query = query.where(TemplateModel.user_id == user_id)
    
    # 総件数取得
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(TemplateModel.created_at.desc())
    
    result = await session.execute(query)
    templates = result.scalars().all()
    
    # レスポンス変換
    template_list = []
    for template in templates:
        template_item = TemplateListResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            status=template.status,
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        template_list.append(template_item)
    
    paginated_data = PaginatedResponse(
        items=template_list,
        total=total,
        page=page,
        limit=limit,
        has_more=total > page * limit
    )
    
    return ApiResponse(
        success=True,
        data=paginated_data
    )

@router.get("/{template_id}", response_model=ApiResponse[TemplateResponse])
async def get_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """テンプレート詳細取得"""
    
    stmt = select(TemplateModel).where(TemplateModel.id == template_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # プライベートテンプレートのアクセス制御
    if template.status != TemplateStatus.ACTIVE:
        if not current_user or template.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    template_response = TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        content=template.content,
        variables=template.variables or [],
        requirements=template.requirements,
        status=template.status,
        user_id=template.user_id,
        usage_count=template.usage_count,
        created_at=template.created_at,
        updated_at=template.updated_at
    )
    
    return ApiResponse(
        success=True,
        data=template_response
    )

@router.post("", response_model=ApiResponse[TemplateResponse])
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """テンプレート作成"""
    
    # 新しいテンプレートを作成
    # TemplateVariable オブジェクトを辞書に変換してからDBに保存
    variables_data = []
    if template_data.variables:
        for var in template_data.variables:
            if isinstance(var, TemplateVariable):
                variables_data.append(var.dict())
            else:
                variables_data.append(var)
    
    new_template = TemplateModel(
        id=str(uuid.uuid4()),
        name=template_data.name,
        description=template_data.description,
        content=template_data.content,
        variables=variables_data,
        requirements=template_data.requirements or "",
        status=template_data.status or TemplateStatus.DRAFT,
        user_id=current_user.id,
        usage_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(new_template)
    await session.commit()
    await session.refresh(new_template)
    
    template_response = TemplateResponse(
        id=new_template.id,
        name=new_template.name,
        description=new_template.description,
        content=new_template.content,
        variables=new_template.variables or [],
        requirements=new_template.requirements,
        tags=new_template.tags or [],
        status=new_template.status,
        user_id=new_template.user_id,
        usage_count=new_template.usage_count,
        created_at=new_template.created_at,
        updated_at=new_template.updated_at
    )
    
    response_data = ApiResponse[
        TemplateResponse
    ](success=True, data=template_response, message="Template created successfully")
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(response_data))

@router.patch("/{template_id}", response_model=ApiResponse[TemplateResponse])
@router.put("/{template_id}", response_model=ApiResponse[TemplateResponse])
async def update_template(
    template_id: str,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """テンプレート更新"""
    
    # テンプレートの存在確認と権限チェック
    stmt = select(TemplateModel).where(TemplateModel.id == template_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this template"
        )
    
    # 更新可能なフィールドのみ更新
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "variables" and value:
            # TemplateVariable オブジェクトを辞書に変換
            variables_data = []
            for var in value:
                if isinstance(var, TemplateVariable):
                    variables_data.append(var.dict())
                else:
                    variables_data.append(var)
            setattr(template, field, variables_data)
        else:
            setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(template)
    
    template_response = TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        content=template.content,
        variables=template.variables or [],
        requirements=template.requirements,
        status=template.status,
        user_id=template.user_id,
        usage_count=template.usage_count,
        created_at=template.created_at,
        updated_at=template.updated_at
    )
    
    return ApiResponse(
        success=True,
        data=template_response,
        message="Template updated successfully"
    )

@router.delete("/{template_id}", response_model=ApiResponse[MessageResponse])
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """テンプレート削除"""
    
    # テンプレートの存在確認と権限チェック
    stmt = select(TemplateModel).where(TemplateModel.id == template_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if template.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this template"
        )
    
    # ソフト削除（ステータスをARCHIVEDに変更）
    template.status = TemplateStatus.ARCHIVED
    template.updated_at = datetime.utcnow()
    
    await session.commit()
    
    return ApiResponse(
        success=True,
        data=MessageResponse(message="Template deleted successfully"),
        message="Template deleted successfully"
    )

from app.services.vector_service import VectorService

async def generate_unique_output_name(session: AsyncSession, user_id: str, base_name: str) -> str:
    """同じ名前のアウトプットがある場合は連番を付けてユニークな名前を生成"""
    from app.infrastructure.database.models import OutputModel
    
    # 基本名をそのまま試す
    stmt = select(OutputModel).where(
        and_(
            OutputModel.user_id == user_id,
            OutputModel.name == base_name
        )
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if not existing:
        return base_name
    
    # 同じ名前が存在する場合は連番を付ける
    counter = 1
    while True:
        new_name = f"{base_name}({counter})"
        stmt = select(OutputModel).where(
            and_(
                OutputModel.user_id == user_id,
                OutputModel.name == new_name
            )
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            return new_name
        counter += 1

@router.post("/{template_id}/use", response_model=ApiResponse[dict])
async def use_template(
    template_id: str,
    usage_data: TemplateUse,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """テンプレート使用（AI生成）"""
    
    from app.infrastructure.database.models import OutputModel
    
    stmt = select(TemplateModel).where(TemplateModel.id == template_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if template.status != TemplateStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template is not active"
        )
    
    try:
        # 1. コンテキスト検索（タグフィルター適用）
        vector_service = VectorService()
        search_query = f"{template.requirements} {template.name}"
        search_results = await vector_service.search_similar(
            query=search_query,
            user_id=current_user.id,
            limit=5,
            tags=usage_data.tags
        )

        # 2. プロンプト構築
        context_str = "\n".join([res['document'] for res in search_results])
        final_prompt = f"""以下のコンテキスト情報を参考に、ユーザーの要求に基づいて出力を作成してください。

[コンテキスト情報]
{context_str}

[ユーザーの要求]
{template.content}
"""

        # 3. AI生成実行
        ai_result = await openai_client.generate_text(
            prompt=final_prompt,
            variables=usage_data.variables
        )
        
        # 4. ユニークなアウトプット名を生成
        output_name = await generate_unique_output_name(session, current_user.id, template.name)
        
        # 5. 生成結果をデータベースに保存
        output = OutputModel(
            id=str(uuid.uuid4()),
            template_id=template_id,
            user_id=current_user.id,
            name=output_name,
            input_variables=usage_data.variables,
            generated_content=ai_result["content"],
            ai_model=ai_result["model"],
            generation_time=ai_result["generation_time_ms"],
            created_at=datetime.utcnow()
        )
        
        session.add(output)
        
        template.usage_count += 1
        await session.commit()
        await session.refresh(output)
        
        return ApiResponse(
            success=True,
            data={
                "output_id": output.id,
                "output_name": output_name,
                "template_id": template_id,
                "template_name": template.name,
                "generated_content": ai_result["content"],
                "input_variables": usage_data.variables,
                "generation_time_ms": ai_result["generation_time_ms"],
                "ai_model": ai_result["model"],
                "usage": ai_result.get("usage", {}),
                "created_at": output.created_at.isoformat()
            },
            message="Template executed successfully"
        )
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}"
        )

@router.get("/mine", response_model=ApiResponse[PaginatedResponse[TemplateListResponse]])
async def get_my_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[TemplateStatus] = Query(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """自分のテンプレート一覧取得"""
    
    query = select(TemplateModel).where(TemplateModel.user_id == current_user.id)
    
    if status:
        query = query.where(TemplateModel.status == status)
    
    # 総件数取得
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # ページネーション
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(TemplateModel.updated_at.desc())
    
    result = await session.execute(query)
    templates = result.scalars().all()
    
    template_list = []
    for template in templates:
        template_item = TemplateListResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            status=template.status,
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        template_list.append(template_item)
    
    paginated_data = PaginatedResponse(
        items=template_list,
        total=total,
        page=page,
        limit=limit,
        has_more=total > page * limit
    )
    
    return ApiResponse(
        success=True,
        data=paginated_data
    )