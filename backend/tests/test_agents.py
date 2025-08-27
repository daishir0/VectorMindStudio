"""
AIエージェントのテスト
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents import (
    OutlineAgent, SummaryAgent, WriterAgent, 
    LogicValidatorAgent, ReferenceAgent,
    AgentStatus, AgentTask
)
from app.infrastructure.database.models import UserModel, ResearchPaperModel, PaperSectionModel


@pytest.mark.asyncio
class TestOutlineAgent:
    """アウトラインエージェントのテストクラス"""

    async def test_create_outline_task(self, db_session: AsyncSession):
        """アウトライン作成タスクのテスト"""
        agent = OutlineAgent(db_session)
        
        task = agent.create_task(
            task_type="create_outline",
            parameters={
                "paper_id": "test-paper-id",
                "research_topic": "機械学習の説明可能性",
                "target_sections": 5
            }
        )
        
        assert task.task_type == "create_outline"
        assert task.parameters["paper_id"] == "test-paper-id"
        assert task.parameters["research_topic"] == "機械学習の説明可能性"
        assert task.status == AgentStatus.PENDING

    @patch('app.services.agents.outline_agent.OutlineAgent._call_openai_api')
    async def test_execute_create_outline(self, mock_openai, db_session: AsyncSession, test_user: UserModel):
        """アウトライン作成実行のテスト"""
        # モックレスポンスを設定
        mock_openai.return_value = {
            "outline": [
                {"section_number": "1", "title": "はじめに", "description": "研究の背景と目的"},
                {"section_number": "2", "title": "関連研究", "description": "既存研究の調査"},
                {"section_number": "3", "title": "提案手法", "description": "新手法の説明"},
            ]
        }
        
        agent = OutlineAgent(db_session)
        
        # 論文を作成（テスト用）
        paper = ResearchPaperModel(
            id="test-paper-id",
            user_id=test_user.id,
            title="テスト論文",
            status="draft"
        )
        db_session.add(paper)
        await db_session.commit()
        
        task = agent.create_task(
            task_type="create_outline",
            parameters={
                "paper_id": "test-paper-id",
                "research_topic": "機械学習の説明可能性"
            }
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.COMPLETED
        assert "outline" in result.result
        assert len(result.result["outline"]) == 3

    async def test_create_section_task(self, db_session: AsyncSession):
        """セクション作成タスクのテスト"""
        agent = OutlineAgent(db_session)
        
        task = agent.create_task(
            task_type="create_section",
            parameters={
                "paper_id": "test-paper-id",
                "title": "はじめに",
                "parent_id": None,
                "position": -1
            }
        )
        
        assert task.task_type == "create_section"
        assert task.parameters["title"] == "はじめに"


@pytest.mark.asyncio
class TestSummaryAgent:
    """サマリーエージェントのテストクラス"""

    @patch('app.services.agents.summary_agent.SummaryAgent._call_openai_api')
    async def test_execute_create_summary(self, mock_openai, db_session: AsyncSession):
        """サマリー作成実行のテスト"""
        # モックレスポンスを設定
        mock_openai.return_value = {
            "summary": "この論文では機械学習モデルの説明可能性について研究します。",
            "key_points": [
                "既存手法の限界",
                "新しいアプローチの提案",
                "実験による検証"
            ]
        }
        
        agent = SummaryAgent(db_session)
        
        task = agent.create_task(
            task_type="create_summary",
            parameters={
                "content": "機械学習モデルの説明可能性に関する詳細な研究内容...",
                "summary_type": "abstract"
            }
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.COMPLETED
        assert "summary" in result.result
        assert "key_points" in result.result


@pytest.mark.asyncio
class TestWriterAgent:
    """ライターエージェントのテストクラス"""

    @patch('app.services.agents.writer_agent.WriterAgent._call_openai_api')
    async def test_execute_write_content(self, mock_openai, db_session: AsyncSession):
        """コンテンツ執筆実行のテスト"""
        # モックレスポンスを設定
        mock_openai.return_value = {
            "content": "機械学習の分野において、モデルの説明可能性は重要な研究課題です。",
            "word_count": 150,
            "quality_score": 0.85
        }
        
        agent = WriterAgent(db_session)
        
        task = agent.create_task(
            task_type="write_content",
            parameters={
                "section_title": "はじめに",
                "content_outline": "研究の背景と目的を説明する",
                "target_words": 200
            }
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.COMPLETED
        assert "content" in result.result
        assert "word_count" in result.result


@pytest.mark.asyncio
class TestLogicValidatorAgent:
    """論理検証エージェントのテストクラス"""

    @patch('app.services.agents.logic_validator_agent.LogicValidatorAgent._call_openai_api')
    async def test_execute_validate_logic(self, mock_openai, db_session: AsyncSession):
        """論理検証実行のテスト"""
        # モックレスポンスを設定
        mock_openai.return_value = {
            "is_valid": True,
            "logic_score": 0.9,
            "issues": [],
            "suggestions": [
                "より具体的な例を追加することを推奨します"
            ]
        }
        
        agent = LogicValidatorAgent(db_session)
        
        task = agent.create_task(
            task_type="validate_logic",
            parameters={
                "content": "提案手法は既存手法よりも優れています。",
                "validation_type": "argument_structure"
            }
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.COMPLETED
        assert "is_valid" in result.result
        assert "logic_score" in result.result
        assert result.result["is_valid"] is True

    @patch('app.services.agents.logic_validator_agent.LogicValidatorAgent._call_openai_api')
    async def test_execute_validate_with_issues(self, mock_openai, db_session: AsyncSession):
        """論理的問題がある場合の検証テスト"""
        # モックレスポンスを設定
        mock_openai.return_value = {
            "is_valid": False,
            "logic_score": 0.3,
            "issues": [
                "根拠が不十分です",
                "因果関係が明確ではありません"
            ],
            "suggestions": [
                "実験データを追加してください",
                "理論的根拠を強化してください"
            ]
        }
        
        agent = LogicValidatorAgent(db_session)
        
        task = agent.create_task(
            task_type="validate_logic",
            parameters={
                "content": "提案手法は良いです。",
                "validation_type": "argument_structure"
            }
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.COMPLETED
        assert result.result["is_valid"] is False
        assert len(result.result["issues"]) == 2


@pytest.mark.asyncio
class TestReferenceAgent:
    """文献検索エージェントのテストクラス"""

    @patch('app.services.agents.reference_agent.ReferenceAgent._search_vector_db')
    async def test_execute_search_references(self, mock_search, db_session: AsyncSession):
        """文献検索実行のテスト"""
        # モックレスポンスを設定
        mock_search.return_value = {
            "search_results": [
                {
                    "id": "ref1",
                    "filename": "paper1.pdf",
                    "content": "機械学習の説明可能性に関する研究",
                    "relevance_score": 0.95,
                    "tags": ["machine_learning", "explainability"]
                }
            ],
            "citations": [
                "[1] Smith, J. (2023). Explainable AI Methods. Journal of ML."
            ]
        }
        
        agent = ReferenceAgent(db_session)
        
        task = agent.create_task(
            task_type="search_references",
            parameters={
                "query": "機械学習の説明可能性",
                "keywords": ["explainable AI", "interpretability"],
                "limit": 10
            }
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.COMPLETED
        assert "search_response" in result.result
        assert "search_results" in result.result["search_response"]

    async def test_format_citation(self, db_session: AsyncSession):
        """引用フォーマットのテスト"""
        agent = ReferenceAgent(db_session)
        
        reference_data = {
            "title": "Explainable AI: A Review",
            "authors": ["Smith, J.", "Doe, A."],
            "year": "2023",
            "journal": "Journal of Machine Learning",
            "volume": "15",
            "pages": "123-145"
        }
        
        citation = agent._format_citation_ieee(reference_data)
        
        assert "Smith, J." in citation
        assert "Explainable AI: A Review" in citation
        assert "2023" in citation


@pytest.mark.asyncio
class TestAgentErrorHandling:
    """エージェントのエラーハンドリングテスト"""

    async def test_task_timeout(self, db_session: AsyncSession):
        """タスクタイムアウトのテスト"""
        agent = OutlineAgent(db_session)
        agent.timeout = 0.001  # 極端に短いタイムアウト
        
        task = agent.create_task(
            task_type="create_outline",
            parameters={"paper_id": "test-paper-id"}
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.FAILED
        assert "timeout" in result.error_message.lower()

    async def test_max_retries_exceeded(self, db_session: AsyncSession):
        """最大リトライ回数超過のテスト"""
        agent = OutlineAgent(db_session)
        agent.max_retries = 1
        
        with patch.object(agent, '_execute_task_impl', side_effect=Exception("Test error")):
            task = agent.create_task(
                task_type="create_outline",
                parameters={"paper_id": "test-paper-id"}
            )
            
            result = await agent.execute_task(task)
            
            assert result.status == AgentStatus.FAILED
            assert "Test error" in result.error_message

    async def test_invalid_task_type(self, db_session: AsyncSession):
        """無効なタスクタイプのテスト"""
        agent = OutlineAgent(db_session)
        
        task = agent.create_task(
            task_type="invalid_task_type",
            parameters={"paper_id": "test-paper-id"}
        )
        
        result = await agent.execute_task(task)
        
        assert result.status == AgentStatus.FAILED
        assert "unsupported task type" in result.error_message.lower()