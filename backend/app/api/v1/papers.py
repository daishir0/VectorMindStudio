"""
論文執筆機能のAPIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union
import yaml
import logging

from app.infrastructure.database.session import get_session
from app.schemas.paper import (
    PaperCreate, PaperUpdate, PaperDetail, PaperSummary,
    SectionCreate, SectionUpdate, SectionDetail, SectionOutline, SectionHistory,
    ChatSessionCreate, ChatSessionSummary, ChatMessageCreate, ChatMessage, ChatResponse,
    ReferenceSearchRequest, ReferenceSearchResponse,
    AgentExecuteRequest, AgentExecuteResponse,
    SectionMoveRequest, SectionMoveResponse,
    YamlResponse, TodoTaskInfo
)
from app.schemas.common import ApiResponse, PaginatedResponse
from app.domain.entities.user import User
from app.api.deps.auth import get_current_active_user
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.services.research_discussion_service_v2 import ResearchDiscussionServiceV2

router = APIRouter()
logger = logging.getLogger(__name__)


def create_yaml_response(data: dict, status_code: int = 200) -> FastAPIResponse:
    """YAML形式のレスポンスを作成"""
    try:
        yaml_content = yaml.dump(data, allow_unicode=True, default_flow_style=False)
        return FastAPIResponse(
            content=yaml_content,
            media_type="application/x-yaml",
            status_code=status_code
        )
    except Exception as e:
        logger.error(f"YAML変換エラー: {e}")
        # フォールバック: JSON形式で返す
        return FastAPIResponse(
            content=str(data),
            media_type="application/json",
            status_code=status_code
        )


# === 論文管理エンドポイント ===

@router.get("", response_model=ApiResponse[PaginatedResponse[PaperSummary]])
async def get_papers(
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(20, ge=1, le=100, description="取得件数"),
    status: Optional[str] = Query(None, description="ステータスフィルター"),
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """論文一覧取得"""
    try:
        repository = PaperRepository(session)
        offset = (page - 1) * limit
        
        papers, total = await repository.get_papers_by_user(
            user_id=current_user.id,
            offset=offset,
            limit=limit
        )
        
        # セクション数・単語数の計算（簡易実装）
        paper_summaries = []
        for paper in papers:
            sections = await repository.get_sections_by_paper(paper.id)
            total_words = sum(section.word_count for section in sections)
            
            paper_summaries.append(PaperSummary(
                id=paper.id,
                title=paper.title,
                status=paper.status,
                section_count=len(sections),
                total_words=total_words,
                created_at=paper.created_at,
                updated_at=paper.updated_at
            ))
        
        response_data = {
            "success": True,
            "data": {
                "items": [summary.dict() for summary in paper_summaries],
                "total": total,
                "page": page,
                "limit": limit,
                "has_more": total > offset + len(papers)
            }
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=PaginatedResponse(
            items=paper_summaries,
            total=total,
            page=page,
            limit=limit,
            has_more=total > offset + len(papers)
        ))
        
    except Exception as e:
        logger.error(f"論文一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文一覧の取得に失敗しました: {e}"
        )


@router.post("", response_model=ApiResponse[PaperDetail], status_code=status.HTTP_201_CREATED)
async def create_paper(
    paper_data: PaperCreate,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """新しい論文を作成"""
    try:
        repository = PaperRepository(session)
        
        paper = await repository.create_paper(
            user_id=current_user.id,
            title=paper_data.title,
            description=paper_data.description
        )
        
        paper_detail = PaperDetail(
            id=paper.id,
            title=paper.title,
            description=paper.description,
            status=paper.status,
            created_at=paper.created_at,
            updated_at=paper.updated_at
        )
        
        response_data = {
            "success": True,
            "data": paper_detail.dict(),
            "message": "論文が正常に作成されました"
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data, 201)
        
        return ApiResponse(
            success=True,
            data=paper_detail,
            message="論文が正常に作成されました"
        )
        
    except Exception as e:
        logger.error(f"論文作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文作成に失敗しました: {e}"
        )


@router.get("/{paper_id}", response_model=ApiResponse[PaperDetail])
async def get_paper(
    paper_id: str,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """論文詳細取得"""
    try:
        repository = PaperRepository(session)
        paper = await repository.get_paper_by_id(paper_id)
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        if paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この論文にアクセスする権限がありません"
            )
        
        paper_detail = PaperDetail(
            id=paper.id,
            title=paper.title,
            description=paper.description,
            status=paper.status,
            created_at=paper.created_at,
            updated_at=paper.updated_at
        )
        
        response_data = {
            "success": True,
            "data": paper_detail.dict()
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=paper_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"論文取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文取得に失敗しました: {e}"
        )


@router.put("/{paper_id}", response_model=ApiResponse[PaperDetail])
async def update_paper(
    paper_id: str,
    paper_data: PaperUpdate,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """論文更新"""
    try:
        repository = PaperRepository(session)
        paper = await repository.get_paper_by_id(paper_id)
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        if paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この論文を更新する権限がありません"
            )
        
        # 更新データを準備
        update_data = paper_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新するデータが指定されていません"
            )
        
        updated_paper = await repository.update_paper(paper_id, update_data)
        
        paper_detail = PaperDetail(
            id=updated_paper.id,
            title=updated_paper.title,
            description=updated_paper.description,
            status=updated_paper.status,
            created_at=updated_paper.created_at,
            updated_at=updated_paper.updated_at
        )
        
        response_data = {
            "success": True,
            "data": paper_detail.dict(),
            "message": "論文が正常に更新されました"
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(
            success=True,
            data=paper_detail,
            message="論文が正常に更新されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"論文更新エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文更新に失敗しました: {e}"
        )


@router.delete("/{paper_id}", response_model=ApiResponse[dict])
async def delete_paper(
    paper_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """論文削除"""
    try:
        repository = PaperRepository(session)
        paper = await repository.get_paper_by_id(paper_id)
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        if paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この論文を削除する権限がありません"
            )
        
        success = await repository.delete_paper(paper_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="論文削除に失敗しました"
            )
        
        return ApiResponse(
            success=True,
            data={"message": "論文が正常に削除されました"},
            message="論文が正常に削除されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"論文削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"論文削除に失敗しました: {e}"
        )


# === セクション管理エンドポイント ===

@router.get("/{paper_id}/sections", response_model=ApiResponse[List[SectionOutline]])
async def get_sections(
    paper_id: str,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """論文のセクション一覧取得"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        sections = await repository.get_sections_by_paper(paper_id)
        
        section_outlines = [
            SectionOutline(
                id=section.id,
                position=section.position,
                section_number=section.section_number,
                title=section.title,
                word_count=section.word_count,
                status=section.status,
                summary=section.summary,
                updated_at=section.updated_at
            )
            for section in sections
        ]
        
        response_data = {
            "success": True,
            "data": [outline.dict() for outline in section_outlines]
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=section_outlines)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション一覧取得に失敗しました: {e}"
        )


@router.post("/{paper_id}/sections", response_model=ApiResponse[SectionDetail], status_code=status.HTTP_201_CREATED)
async def create_section(
    paper_id: str,
    section_data: SectionCreate,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """新しいセクションを作成"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        # アウトライン管理エージェントを使用してセクション作成
        from app.services.agents import OutlineAgent
        outline_agent = OutlineAgent(session)
        
        task = outline_agent.create_task(
            task_type="create_section",
            parameters={
                "paper_id": paper_id,
                "parent_id": section_data.parent_id,
                "title": section_data.title,
                "position": section_data.position
            }
        )
        
        result = await outline_agent.execute_task(task)
        
        if result.status != AgentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"セクション作成に失敗しました: {result.error_message}"
            )
        
        # 作成されたセクションの詳細を取得
        section_info = result.result.get("section", {})
        section = await repository.get_section_by_id(section_info.get("id"))
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="作成されたセクションの取得に失敗しました"
            )
        
        section_detail = SectionDetail(
            id=section.id,
            paper_id=section.paper_id,
            position=section.position,
            section_number=section.section_number,
            title=section.title,
            content=section.content,
            summary=section.summary,
            word_count=section.word_count,
            status=section.status,
            created_at=section.created_at,
            updated_at=section.updated_at
        )
        
        response_data = {
            "success": True,
            "data": section_detail.dict(),
            "message": "セクションが正常に作成されました"
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data, 201)
        
        return ApiResponse(
            success=True,
            data=section_detail,
            message="セクションが正常に作成されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション作成に失敗しました: {e}"
        )


# === 研究ディスカッションエンドポイント ===

@router.post("/{paper_id}/chat", response_model=ApiResponse[ChatSessionSummary], status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    paper_id: str,
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """新しいチャットセッションを作成"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        chat_session = await repository.create_chat_session(
            paper_id=paper_id,
            user_id=current_user.id,
            title=session_data.title
        )
        
        session_summary = ChatSessionSummary(
            id=chat_session.id,
            title=chat_session.title,
            message_count=0,
            created_at=chat_session.created_at,
            updated_at=chat_session.updated_at
        )
        
        return ApiResponse(
            success=True,
            data=session_summary,
            message="チャットセッションが正常に作成されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チャットセッション作成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チャットセッション作成に失敗しました: {e}"
        )


@router.post("/{paper_id}/chat/{session_id}/messages", response_model=ApiResponse[ChatResponse])
async def send_message(
    paper_id: str,
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """メッセージを送信"""
    try:
        repository = PaperRepository(session)
        
        # セッションの存在・権限確認
        chat_session = await repository.get_chat_session_by_id(session_id)
        if not chat_session or chat_session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="チャットセッションが見つかりません"
            )
        
        # 研究ディスカッションサービスでメッセージ処理
        discussion_service = ResearchDiscussionServiceV2(session)
        
        response = await discussion_service.process_user_message(
            session_id=session_id,
            user_message=message_data.message,
            user_id=current_user.id,
            paper_id=paper_id
        )
        
        chat_response = ChatResponse(
            message=response.get("message", ""),
            todo_tasks=[
                TodoTaskInfo(**task) for task in response.get("todo_tasks", [])
            ],
            task_results=response.get("task_results", {}),
            references=response.get("references", []),
            suggestions=response.get("suggestions", []),
            success=response.get("success", False)
        )
        
        return ApiResponse(success=True, data=chat_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"メッセージ送信エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"メッセージ送信に失敗しました: {e}"
        )


@router.get("/{paper_id}/sections/{section_id}", response_model=ApiResponse[SectionDetail])
async def get_section(
    paper_id: str,
    section_id: str,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """セクション詳細取得"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        # セクション取得
        section = await repository.get_section_by_id(section_id)
        if not section or section.paper_id != paper_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="セクションが見つかりません"
            )
        
        section_detail = SectionDetail(
            id=section.id,
            paper_id=section.paper_id,
            position=section.position,
            section_number=section.section_number,
            title=section.title,
            content=section.content,
            summary=section.summary,
            word_count=section.word_count,
            status=section.status,
            created_at=section.created_at,
            updated_at=section.updated_at
        )
        
        response_data = {
            "success": True,
            "data": section_detail.dict()
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=section_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション詳細取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション詳細取得に失敗しました: {e}"
        )


@router.put("/{paper_id}/sections/{section_id}", response_model=ApiResponse[SectionDetail])
async def update_section(
    paper_id: str,
    section_id: str,
    section_data: SectionUpdate,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """セクション更新"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        # セクション存在確認
        section = await repository.get_section_by_id(section_id)
        if not section or section.paper_id != paper_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="セクションが見つかりません"
            )
        
        # 更新データを準備
        update_data = section_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="更新するデータが指定されていません"
            )
        
        # コンテンツが更新される場合は単語数も再計算
        if "content" in update_data:
            update_data["word_count"] = len(update_data["content"].split()) if update_data["content"] else 0
        
        updated_section = await repository.update_section(section_id, update_data)
        
        section_detail = SectionDetail(
            id=updated_section.id,
            paper_id=updated_section.paper_id,
            position=updated_section.position,
            section_number=updated_section.section_number,
            title=updated_section.title,
            content=updated_section.content,
            summary=updated_section.summary,
            word_count=updated_section.word_count,
            status=updated_section.status,
            created_at=updated_section.created_at,
            updated_at=updated_section.updated_at
        )
        
        response_data = {
            "success": True,
            "data": section_detail.dict(),
            "message": "セクションが正常に更新されました"
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(
            success=True,
            data=section_detail,
            message="セクションが正常に更新されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション更新エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション更新に失敗しました: {e}"
        )


@router.delete("/{paper_id}/sections/{section_id}", response_model=ApiResponse[dict])
async def delete_section(
    paper_id: str,
    section_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """セクション削除（論理削除）"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        # セクション存在確認
        section = await repository.get_section_by_id(section_id)
        if not section or section.paper_id != paper_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="セクションが見つかりません"
            )
        
        success = await repository.delete_section(section_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="セクション削除に失敗しました"
            )
        
        return ApiResponse(
            success=True,
            data={"message": "セクションが正常に削除されました"},
            message="セクションが正常に削除されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション削除に失敗しました: {e}"
        )


@router.put("/{paper_id}/sections/{section_id}/move", response_model=ApiResponse[SectionMoveResponse])
async def move_section(
    paper_id: str,
    section_id: str,
    move_request: SectionMoveRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """セクションの順序を変更"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        # セクション存在確認
        section = await repository.get_section_by_id(section_id)
        if not section or section.paper_id != paper_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="セクションが見つかりません"
            )
        
        # 全セクション取得
        sections = await repository.get_sections_by_paper(paper_id)
        if not sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="移動可能なセクションがありません"
            )
        
        sections_list = list(sections)
        current_position = next(i for i, s in enumerate(sections_list, 1) if s.id == section_id)
        
        # 移動先位置を計算
        if move_request.action == "up":
            new_position = max(1, current_position - 1)
        elif move_request.action == "down":
            new_position = min(len(sections_list), current_position + 1)
        elif move_request.action == "top":
            new_position = 1
        elif move_request.action == "bottom":
            new_position = len(sections_list)
        elif move_request.action == "to_position":
            if move_request.new_position is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="to_positionの場合はnew_positionが必須です"
                )
            new_position = max(1, min(len(sections_list), move_request.new_position))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なアクションです"
            )
        
        # 位置が変わらない場合は何もしない
        if new_position == current_position:
            updated_sections = [
                SectionOutline(
                    id=s.id,
                    position=s.position,
                    section_number=s.section_number,
                    title=s.title,
                    word_count=s.word_count,
                    status=s.status,
                    summary=s.summary,
                    updated_at=s.updated_at
                )
                for s in sections_list
            ]
            
            return ApiResponse(
                success=True,
                data=SectionMoveResponse(
                    success=True,
                    message="セクションの位置は変更されませんでした",
                    updated_sections=updated_sections
                )
            )
        
        # セクション移動実行
        success = await repository.move_section_to_position(section_id, new_position)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="セクション移動に失敗しました"
            )
        
        # 更新後のセクション一覧を取得
        updated_sections_models = await repository.get_sections_by_paper(paper_id)
        updated_sections = [
            SectionOutline(
                id=s.id,
                position=s.position,
                section_number=s.section_number,
                title=s.title,
                word_count=s.word_count,
                status=s.status,
                summary=s.summary,
                updated_at=s.updated_at
            )
            for s in updated_sections_models
        ]
        
        move_response = SectionMoveResponse(
            success=True,
            message=f"セクションを{move_request.action}に移動しました",
            updated_sections=updated_sections
        )
        
        return ApiResponse(success=True, data=move_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション移動エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション移動に失敗しました: {e}"
        )


@router.get("/{paper_id}/sections/{section_id}/history", response_model=ApiResponse[List[SectionHistory]])
async def get_section_history(
    paper_id: str,
    section_id: str,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """セクション履歴取得"""
    try:
        repository = PaperRepository(session)
        
        # 論文・セクションの存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        section = await repository.get_section_by_id(section_id)
        if not section or section.paper_id != paper_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="セクションが見つかりません"
            )
        
        history_records = await repository.get_section_history(section_id)
        
        section_histories = [
            SectionHistory(
                id=record.id,
                version_number=record.version_number,
                title=record.title,
                content=record.content,
                summary=record.summary,
                change_description=record.change_description,
                created_at=record.created_at
            )
            for record in history_records
        ]
        
        response_data = {
            "success": True,
            "data": [history.dict() for history in section_histories]
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=section_histories)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セクション履歴取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"セクション履歴取得に失敗しました: {e}"
        )


@router.get("/{paper_id}/chat", response_model=ApiResponse[List[ChatSessionSummary]])
async def get_chat_sessions(
    paper_id: str,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """チャットセッション一覧取得"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        chat_sessions = await repository.get_chat_sessions_by_paper(paper_id)
        
        session_summaries = []
        for chat_session in chat_sessions:
            messages = await repository.get_chat_messages_by_session(chat_session.id)
            session_summary = ChatSessionSummary(
                id=chat_session.id,
                title=chat_session.title,
                message_count=len(messages),
                created_at=chat_session.created_at,
                updated_at=chat_session.updated_at
            )
            session_summaries.append(session_summary)
        
        response_data = {
            "success": True,
            "data": [summary.dict() for summary in session_summaries]
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=session_summaries)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チャットセッション一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チャットセッション一覧取得に失敗しました: {e}"
        )


@router.get("/{paper_id}/chat/{session_id}/messages", response_model=ApiResponse[List[ChatMessage]])
async def get_chat_messages(
    paper_id: str,
    session_id: str,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """チャットメッセージ一覧取得"""
    try:
        repository = PaperRepository(session)
        
        # セッションの存在・権限確認
        chat_session = await repository.get_chat_session_by_id(session_id)
        if not chat_session or chat_session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="チャットセッションが見つかりません"
            )
        
        if chat_session.paper_id != paper_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="セッションが指定された論文に属していません"
            )
        
        message_models = await repository.get_chat_messages_by_session(session_id)
        
        messages = [
            ChatMessage(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                agent_name=msg.agent_name,
                todo_tasks=[
                    TodoTaskInfo(**task) for task in msg.todo_tasks
                ],
                references=msg.references,
                created_at=msg.created_at
            )
            for msg in message_models
        ]
        
        response_data = {
            "success": True,
            "data": [message.dict() for message in messages]
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=messages)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チャットメッセージ一覧取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チャットメッセージ一覧取得に失敗しました: {e}"
        )


@router.post("/{paper_id}/agents/{agent_name}/execute", response_model=ApiResponse[AgentExecuteResponse])
async def execute_agent(
    paper_id: str,
    agent_name: str,
    request: AgentExecuteRequest,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """指定されたエージェントを実行"""
    try:
        repository = PaperRepository(session)
        
        # 論文の存在・権限確認
        paper = await repository.get_paper_by_id(paper_id)
        if not paper or paper.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="論文が見つかりません"
            )
        
        # エージェント名のマッピング
        agent_classes = {
            "outline": "OutlineAgent",
            "summary": "SummaryAgent",
            "writer": "WriterAgent",
            "logic_validator": "LogicValidatorAgent",
            "reference": "ReferenceAgent"
        }
        
        if agent_name not in agent_classes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"サポートされていないエージェントです: {agent_name}"
            )
        
        # エージェント実行
        from app.services.agents import (
            OutlineAgent, SummaryAgent, WriterAgent, 
            LogicValidatorAgent, ReferenceAgent
        )
        
        agent_map = {
            "outline": OutlineAgent,
            "summary": SummaryAgent,
            "writer": WriterAgent,
            "logic_validator": LogicValidatorAgent,
            "reference": ReferenceAgent
        }
        
        agent_class = agent_map[agent_name]
        agent = agent_class(session)
        
        # タスク作成
        task = agent.create_task(
            task_type=request.task,
            parameters={**request.parameters, "paper_id": paper_id},
            context=request.context or {}
        )
        
        # タスク実行
        import time
        start_time = time.time()
        result = await agent.execute_task(task)
        execution_time = time.time() - start_time
        
        agent_response = AgentExecuteResponse(
            result=result.result,
            execution_time=execution_time,
            status=result.status.value,
            agent_name=agent_name,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
        response_data = {
            "success": True,
            "data": agent_response.dict()
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=agent_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エージェント実行エラー ({agent_name}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"エージェント実行に失敗しました ({agent_name}): {e}"
        )


# === 文献検索エンドポイント ===

@router.post("/search/references", response_model=ApiResponse[ReferenceSearchResponse])
async def search_references(
    request: ReferenceSearchRequest,
    format: str = Query("json", description="レスポンス形式 (json/yaml)"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """文献検索"""
    try:
        # ReferenceAgentを使用して文献検索
        from app.services.agents import ReferenceAgent
        
        reference_agent = ReferenceAgent(session)
        
        task = reference_agent.create_task(
            task_type="search_references",
            parameters={
                "query": request.query,
                "keywords": request.keywords,
                "tags": request.tags,
                "limit": request.limit,
                "search_types": request.search_types
            }
        )
        
        result = await reference_agent.execute_task(task)
        
        if result.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文献検索に失敗しました: {result.error_message}"
            )
        
        search_data = result.result.get("search_response", {})
        search_response = ReferenceSearchResponse(**search_data)
        
        response_data = {
            "success": True,
            "data": search_response.dict()
        }
        
        if format.lower() == "yaml":
            return create_yaml_response(response_data)
        
        return ApiResponse(success=True, data=search_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文献検索エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文献検索に失敗しました: {e}"
        )