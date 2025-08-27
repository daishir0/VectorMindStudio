"""
論文執筆機能テスト用のフィクスチャ
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    ResearchPaperModel, PaperSectionModel, PaperSectionHistoryModel,
    PaperChatSessionModel, PaperChatMessageModel, UserModel
)


@pytest.fixture
async def test_paper(db_session: AsyncSession, test_user: UserModel) -> ResearchPaperModel:
    """テスト用論文フィクスチャ"""
    paper = ResearchPaperModel(
        id="test-paper-id",
        user_id=test_user.id,
        title="テスト論文",
        description="テスト用の論文です",
        status="draft"
    )
    db_session.add(paper)
    await db_session.commit()
    await db_session.refresh(paper)
    return paper


@pytest.fixture
async def test_papers(db_session: AsyncSession, test_user: UserModel) -> list:
    """テスト用複数論文フィクスチャ"""
    papers = []
    for i in range(3):
        paper = ResearchPaperModel(
            id=f"test-paper-{i+1}",
            user_id=test_user.id,
            title=f"テスト論文{i+1}",
            description=f"テスト用の論文{i+1}です",
            status="draft"
        )
        db_session.add(paper)
        papers.append(paper)
    
    await db_session.commit()
    return papers


@pytest.fixture
async def test_section(db_session: AsyncSession, test_paper: ResearchPaperModel) -> PaperSectionModel:
    """テスト用セクションフィクスチャ"""
    section = PaperSectionModel(
        id="test-section-id",
        paper_id=test_paper.id,
        user_id=test_paper.user_id,
        hierarchy_path="001",
        section_number="1",
        title="はじめに",
        content="この論文では機械学習について説明します。",
        summary="論文の導入部分です。",
        word_count=8,
        status="draft"
    )
    db_session.add(section)
    await db_session.commit()
    await db_session.refresh(section)
    return section


@pytest.fixture
async def test_paper_with_sections(db_session: AsyncSession, test_user: UserModel) -> ResearchPaperModel:
    """セクション付きテスト論文フィクスチャ"""
    paper = ResearchPaperModel(
        id="paper-with-sections",
        user_id=test_user.id,
        title="セクション付きテスト論文",
        description="複数のセクションを持つテスト論文です",
        status="draft"
    )
    db_session.add(paper)
    await db_session.flush()
    
    # セクションを作成
    sections_data = [
        {"hierarchy_path": "001", "section_number": "1", "title": "はじめに"},
        {"hierarchy_path": "002", "section_number": "2", "title": "関連研究"},
        {"hierarchy_path": "003", "section_number": "3", "title": "提案手法"},
        {"hierarchy_path": "003.001", "section_number": "3.1", "title": "アルゴリズム"},
        {"hierarchy_path": "004", "section_number": "4", "title": "実験結果"},
    ]
    
    for i, section_data in enumerate(sections_data):
        section = PaperSectionModel(
            id=f"section-{i+1}",
            paper_id=paper.id,
            user_id=test_user.id,
            hierarchy_path=section_data["hierarchy_path"],
            section_number=section_data["section_number"],
            title=section_data["title"],
            content=f"セクション {section_data['section_number']} の内容です。",
            summary=f"セクション {section_data['section_number']} の要約です。",
            word_count=10,
            status="draft"
        )
        db_session.add(section)
    
    await db_session.commit()
    await db_session.refresh(paper)
    return paper


@pytest.fixture
async def test_chat_session(db_session: AsyncSession, test_paper: ResearchPaperModel) -> PaperChatSessionModel:
    """テスト用チャットセッションフィクスチャ"""
    session = PaperChatSessionModel(
        id="test-chat-session",
        paper_id=test_paper.id,
        user_id=test_paper.user_id,
        title="研究ディスカッション"
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def test_paper_with_chat(db_session: AsyncSession, test_user: UserModel) -> ResearchPaperModel:
    """チャットセッション付きテスト論文フィクスチャ"""
    paper = ResearchPaperModel(
        id="paper-with-chat",
        user_id=test_user.id,
        title="チャット付きテスト論文",
        description="チャットセッションを持つテスト論文です",
        status="draft"
    )
    db_session.add(paper)
    await db_session.flush()
    
    # チャットセッションを作成
    sessions_data = [
        {"title": "初期相談"},
        {"title": "構成について"},
        {"title": "文献調査"},
    ]
    
    for i, session_data in enumerate(sessions_data):
        session = PaperChatSessionModel(
            id=f"chat-session-{i+1}",
            paper_id=paper.id,
            user_id=test_user.id,
            title=session_data["title"]
        )
        db_session.add(session)
    
    await db_session.commit()
    await db_session.refresh(paper)
    return paper


@pytest.fixture
async def test_chat_session_with_messages(db_session: AsyncSession, test_paper: ResearchPaperModel) -> PaperChatSessionModel:
    """メッセージ付きチャットセッションフィクスチャ"""
    session = PaperChatSessionModel(
        id="chat-with-messages",
        paper_id=test_paper.id,
        user_id=test_paper.user_id,
        title="メッセージ付きセッション"
    )
    db_session.add(session)
    await db_session.flush()
    
    # メッセージを作成
    messages_data = [
        {
            "role": "user",
            "content": "この論文の構成について相談したいです",
            "agent_name": None,
            "todo_tasks": [],
            "references": []
        },
        {
            "role": "assistant",
            "content": "論文の構成について説明します。まず、以下の構成を提案します...",
            "agent_name": "outline_agent",
            "todo_tasks": [
                {
                    "id": "task1",
                    "description": "論文アウトラインの作成",
                    "agent_name": "outline_agent",
                    "priority": "high",
                    "status": "pending"
                }
            ],
            "references": []
        },
        {
            "role": "user",
            "content": "ありがとうございます。関連研究についても相談したいです",
            "agent_name": None,
            "todo_tasks": [],
            "references": []
        }
    ]
    
    for i, msg_data in enumerate(messages_data):
        message = PaperChatMessageModel(
            id=f"message-{i+1}",
            session_id=session.id,
            role=msg_data["role"],
            content=msg_data["content"],
            agent_name=msg_data.get("agent_name"),
            todo_tasks=msg_data["todo_tasks"],
            references=msg_data["references"]
        )
        db_session.add(message)
    
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
async def test_section_with_history(db_session: AsyncSession, test_paper: ResearchPaperModel) -> PaperSectionModel:
    """履歴付きセクションフィクスチャ"""
    section = PaperSectionModel(
        id="section-with-history",
        paper_id=test_paper.id,
        user_id=test_paper.user_id,
        hierarchy_path="001",
        section_number="1",
        title="履歴テストセクション",
        content="現在の内容です",
        summary="現在の要約です",
        word_count=5,
        status="draft"
    )
    db_session.add(section)
    await db_session.flush()
    
    # 履歴を作成
    histories_data = [
        {
            "version_number": 1,
            "title": "初期タイトル",
            "content": "初期の内容です",
            "summary": "初期の要約です",
            "change_description": "初期作成"
        },
        {
            "version_number": 2,
            "title": "更新されたタイトル",
            "content": "更新された内容です",
            "summary": "更新された要約です",
            "change_description": "内容を改善"
        }
    ]
    
    for history_data in histories_data:
        history = PaperSectionHistoryModel(
            id=f"history-{history_data['version_number']}",
            section_id=section.id,
            version_number=history_data["version_number"],
            title=history_data["title"],
            content=history_data["content"],
            summary=history_data["summary"],
            change_description=history_data["change_description"]
        )
        db_session.add(history)
    
    await db_session.commit()
    await db_session.refresh(section)
    return section


@pytest.fixture
async def other_users_paper(db_session: AsyncSession) -> ResearchPaperModel:
    """他のユーザーの論文フィクスチャ（権限テスト用）"""
    # 他のユーザーを作成
    other_user = UserModel(
        id="other-user-id",
        username="otheruser",
        email="other@example.com",
        hashed_password="hashedpassword",
        is_active=True
    )
    db_session.add(other_user)
    await db_session.flush()
    
    # 他のユーザーの論文を作成
    paper = ResearchPaperModel(
        id="other-users-paper",
        user_id=other_user.id,
        title="他のユーザーの論文",
        description="アクセス権限テスト用",
        status="draft"
    )
    db_session.add(paper)
    await db_session.commit()
    await db_session.refresh(paper)
    return paper