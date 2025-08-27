"""
論文リポジトリのテスト
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.database.models import UserModel


@pytest.mark.asyncio
class TestPaperRepository:
    """論文リポジトリのテストクラス"""

    async def test_create_and_get_paper(self, db_session: AsyncSession, test_user: UserModel):
        """論文作成と取得のテスト"""
        repository = PaperRepository(db_session)
        
        # 論文を作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="テスト論文",
            description="テスト用の論文です"
        )
        
        assert paper.id is not None
        assert paper.title == "テスト論文"
        assert paper.description == "テスト用の論文です"
        assert paper.status == "draft"
        assert paper.user_id == test_user.id
        
        # 作成した論文を取得
        retrieved_paper = await repository.get_paper_by_id(paper.id)
        assert retrieved_paper is not None
        assert retrieved_paper.id == paper.id
        assert retrieved_paper.title == paper.title

    async def test_get_papers_by_user(self, db_session: AsyncSession, test_user: UserModel):
        """ユーザーの論文一覧取得テスト"""
        repository = PaperRepository(db_session)
        
        # 複数の論文を作成
        for i in range(3):
            await repository.create_paper(
                user_id=test_user.id,
                title=f"テスト論文{i+1}",
                description=f"テスト用の論文{i+1}です"
            )
        
        # 論文一覧を取得
        papers, total = await repository.get_papers_by_user(test_user.id)
        
        assert len(papers) == 3
        assert total == 3
        assert all(paper.user_id == test_user.id for paper in papers)

    async def test_update_paper(self, db_session: AsyncSession, test_user: UserModel):
        """論文更新テスト"""
        repository = PaperRepository(db_session)
        
        # 論文を作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="元のタイトル",
            description="元の説明"
        )
        
        # 論文を更新
        update_data = {
            "title": "更新されたタイトル",
            "status": "in_progress"
        }
        updated_paper = await repository.update_paper(paper.id, update_data)
        
        assert updated_paper.title == "更新されたタイトル"
        assert updated_paper.status == "in_progress"
        assert updated_paper.description == "元の説明"  # 更新されていない項目

    async def test_delete_paper(self, db_session: AsyncSession, test_user: UserModel):
        """論文削除テスト"""
        repository = PaperRepository(db_session)
        
        # 論文を作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="削除テスト論文"
        )
        
        # 論文を削除
        success = await repository.delete_paper(paper.id)
        assert success is True
        
        # 削除後は取得できないことを確認
        deleted_paper = await repository.get_paper_by_id(paper.id)
        assert deleted_paper is None

    async def test_create_and_get_section(self, db_session: AsyncSession, test_user: UserModel):
        """セクション作成・取得テスト"""
        repository = PaperRepository(db_session)
        
        # 論文を作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="セクションテスト論文"
        )
        
        # セクションを作成
        section = await repository.create_section(
            paper_id=paper.id,
            hierarchy_path="001",
            section_number="1",
            title="はじめに",
            content="この論文では...",
            summary="論文の概要を説明するセクションです"
        )
        
        assert section.id is not None
        assert section.paper_id == paper.id
        assert section.hierarchy_path == "001"
        assert section.section_number == "1"
        assert section.title == "はじめに"
        assert section.content == "この論文では..."
        assert section.word_count == 4  # "この論文では..."を分割した単語数
        
        # セクションを取得
        retrieved_section = await repository.get_section_by_id(section.id)
        assert retrieved_section is not None
        assert retrieved_section.id == section.id

    async def test_get_sections_by_paper(self, db_session: AsyncSession, test_user: UserModel):
        """論文のセクション一覧取得テスト"""
        repository = PaperRepository(db_session)
        
        # 論文を作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="セクション一覧テスト論文"
        )
        
        # 複数のセクションを作成
        sections_data = [
            {"hierarchy_path": "001", "section_number": "1", "title": "はじめに"},
            {"hierarchy_path": "002", "section_number": "2", "title": "関連研究"},
            {"hierarchy_path": "003", "section_number": "3", "title": "提案手法"},
        ]
        
        for data in sections_data:
            await repository.create_section(
                paper_id=paper.id,
                hierarchy_path=data["hierarchy_path"],
                section_number=data["section_number"],
                title=data["title"]
            )
        
        # セクション一覧を取得
        sections = await repository.get_sections_by_paper(paper.id)
        
        assert len(sections) == 3
        assert all(section.paper_id == paper.id for section in sections)
        # 階層パス順でソートされていることを確認
        assert sections[0].hierarchy_path == "001"
        assert sections[1].hierarchy_path == "002"
        assert sections[2].hierarchy_path == "003"

    async def test_update_section_with_history(self, db_session: AsyncSession, test_user: UserModel):
        """セクション更新と履歴保存テスト"""
        repository = PaperRepository(db_session)
        
        # 論文とセクションを作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="履歴テスト論文"
        )
        
        section = await repository.create_section(
            paper_id=paper.id,
            hierarchy_path="001",
            section_number="1",
            title="元のタイトル",
            content="元の内容"
        )
        
        # セクションを更新（履歴が自動作成される）
        update_data = {
            "title": "更新されたタイトル",
            "content": "更新された内容"
        }
        updated_section = await repository.update_section(section.id, update_data)
        
        assert updated_section.title == "更新されたタイトル"
        assert updated_section.content == "更新された内容"
        
        # 履歴が作成されていることを確認
        history = await repository.get_section_history(section.id)
        assert len(history) == 1
        assert history[0].title == "元のタイトル"
        assert history[0].content == "元の内容"

    async def test_delete_section(self, db_session: AsyncSession, test_user: UserModel):
        """セクション削除テスト"""
        repository = PaperRepository(db_session)
        
        # 論文とセクションを作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="削除テスト論文"
        )
        
        section = await repository.create_section(
            paper_id=paper.id,
            hierarchy_path="001",
            section_number="1",
            title="削除テストセクション"
        )
        
        # セクションを削除（論理削除）
        success = await repository.delete_section(section.id)
        assert success is True
        
        # 削除後は取得できないことを確認（論理削除なので is_deleted=True になる）
        deleted_section = await repository.get_section_by_id(section.id)
        assert deleted_section is None

    async def test_chat_session_functionality(self, db_session: AsyncSession, test_user: UserModel):
        """チャットセッション機能テスト"""
        repository = PaperRepository(db_session)
        
        # 論文を作成
        paper = await repository.create_paper(
            user_id=test_user.id,
            title="チャットテスト論文"
        )
        
        # チャットセッションを作成
        chat_session = await repository.create_chat_session(
            paper_id=paper.id,
            user_id=test_user.id,
            title="研究ディスカッション"
        )
        
        assert chat_session.id is not None
        assert chat_session.paper_id == paper.id
        assert chat_session.user_id == test_user.id
        assert chat_session.title == "研究ディスカッション"
        
        # チャットメッセージを作成
        message = await repository.create_chat_message(
            session_id=chat_session.id,
            role="user",
            content="この論文の構成について相談したいです",
            todo_tasks=[{"id": "task1", "description": "タスク1"}],
            references=[{"type": "paper", "title": "参考文献1"}]
        )
        
        assert message.id is not None
        assert message.session_id == chat_session.id
        assert message.content == "この論文の構成について相談したいです"
        assert len(message.todo_tasks) == 1
        assert len(message.references) == 1
        
        # メッセージ一覧を取得
        messages = await repository.get_chat_messages_by_session(chat_session.id)
        assert len(messages) == 1
        assert messages[0].id == message.id