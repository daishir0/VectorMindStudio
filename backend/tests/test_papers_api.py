"""
論文執筆APIエンドポイントのテスト
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel, ResearchPaperModel, PaperSectionModel
from app.services.research_discussion_service import ResearchDiscussionService


@pytest.mark.asyncio
class TestPapersAPI:
    """論文API のテストクラス"""

    async def test_create_paper(self, client: AsyncClient, auth_headers: dict):
        """論文作成APIのテスト"""
        paper_data = {
            "title": "テスト論文",
            "description": "テスト用の論文です"
        }
        
        response = await client.post(
            "/api/v1/papers",
            json=paper_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "テスト論文"
        assert data["data"]["description"] == "テスト用の論文です"
        assert data["data"]["status"] == "draft"

    async def test_create_paper_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """論文作成API（無効なデータ）のテスト"""
        paper_data = {
            "title": "",  # 空のタイトル
            "description": "テスト用の論文です"
        }
        
        response = await client.post(
            "/api/v1/papers",
            json=paper_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_papers(self, client: AsyncClient, auth_headers: dict, test_papers: list):
        """論文一覧取得APIのテスト"""
        response = await client.get(
            "/api/v1/papers?page=1&limit=10",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert len(data["data"]["items"]) > 0

    async def test_get_paper_by_id(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """論文詳細取得APIのテスト"""
        response = await client.get(
            f"/api/v1/papers/{test_paper.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_paper.id
        assert data["data"]["title"] == test_paper.title

    async def test_get_nonexistent_paper(self, client: AsyncClient, auth_headers: dict):
        """存在しない論文の取得APIのテスト"""
        response = await client.get(
            "/api/v1/papers/nonexistent-id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_paper(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """論文更新APIのテスト"""
        update_data = {
            "title": "更新されたタイトル",
            "status": "in_progress"
        }
        
        response = await client.put(
            f"/api/v1/papers/{test_paper.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "更新されたタイトル"
        assert data["data"]["status"] == "in_progress"

    async def test_delete_paper(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """論文削除APIのテスト"""
        response = await client.delete(
            f"/api/v1/papers/{test_paper.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    async def test_yaml_response_format(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """YAML形式レスポンスのテスト"""
        response = await client.get(
            f"/api/v1/papers/{test_paper.id}?format=yaml",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/x-yaml"
        # YAMLが正しく解析できることを確認
        import yaml
        data = yaml.safe_load(response.text)
        assert data["success"] is True
        assert data["data"]["id"] == test_paper.id


@pytest.mark.asyncio
class TestSectionsAPI:
    """セクションAPIのテストクラス"""

    async def test_create_section(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """セクション作成APIのテスト"""
        section_data = {
            "title": "はじめに",
            "content": "この論文では...",
            "parent_id": None,
            "position": -1
        }
        
        response = await client.post(
            f"/api/v1/papers/{test_paper.id}/sections",
            json=section_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "はじめに"
        assert data["data"]["paper_id"] == test_paper.id

    async def test_get_sections(self, client: AsyncClient, auth_headers: dict, test_paper_with_sections: ResearchPaperModel):
        """セクション一覧取得APIのテスト"""
        response = await client.get(
            f"/api/v1/papers/{test_paper_with_sections.id}/sections",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    async def test_get_section_detail(self, client: AsyncClient, auth_headers: dict, test_section: PaperSectionModel):
        """セクション詳細取得APIのテスト"""
        response = await client.get(
            f"/api/v1/papers/{test_section.paper_id}/sections/{test_section.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_section.id
        assert data["data"]["title"] == test_section.title

    async def test_update_section(self, client: AsyncClient, auth_headers: dict, test_section: PaperSectionModel):
        """セクション更新APIのテスト"""
        update_data = {
            "title": "更新されたセクションタイトル",
            "content": "更新された内容です",
            "status": "writing"
        }
        
        response = await client.put(
            f"/api/v1/papers/{test_section.paper_id}/sections/{test_section.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "更新されたセクションタイトル"
        assert data["data"]["content"] == "更新された内容です"

    async def test_delete_section(self, client: AsyncClient, auth_headers: dict, test_section: PaperSectionModel):
        """セクション削除APIのテスト"""
        response = await client.delete(
            f"/api/v1/papers/{test_section.paper_id}/sections/{test_section.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    async def test_get_section_history(self, client: AsyncClient, auth_headers: dict, test_section: PaperSectionModel):
        """セクション履歴取得APIのテスト"""
        # まず更新を行って履歴を作成
        update_data = {"title": "履歴テスト"}
        await client.put(
            f"/api/v1/papers/{test_section.paper_id}/sections/{test_section.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # 履歴を取得
        response = await client.get(
            f"/api/v1/papers/{test_section.paper_id}/sections/{test_section.id}/history",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


@pytest.mark.asyncio
class TestChatAPI:
    """チャットAPIのテストクラス"""

    async def test_create_chat_session(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """チャットセッション作成APIのテスト"""
        session_data = {
            "title": "研究ディスカッション"
        }
        
        response = await client.post(
            f"/api/v1/papers/{test_paper.id}/chat",
            json=session_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "研究ディスカッション"

    async def test_get_chat_sessions(self, client: AsyncClient, auth_headers: dict, test_paper_with_chat: ResearchPaperModel):
        """チャットセッション一覧取得APIのテスト"""
        response = await client.get(
            f"/api/v1/papers/{test_paper_with_chat.id}/chat",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    async def test_send_message(self, client: AsyncClient, auth_headers: dict, test_chat_session):
        """メッセージ送信APIのテスト"""
        message_data = {
            "message": "この論文の構成について相談したいです",
            "target_section_id": None
        }
        
        # ResearchDiscussionServiceをモック
        from unittest.mock import patch, AsyncMock
        
        mock_response = {
            "message": "論文の構成について説明します...",
            "todo_tasks": [],
            "task_results": {},
            "references": [],
            "suggestions": ["セクション構成を検討してください"],
            "success": True
        }
        
        with patch.object(ResearchDiscussionService, 'process_user_message', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_response
            
            response = await client.post(
                f"/api/v1/papers/{test_chat_session.paper_id}/chat/{test_chat_session.id}/messages",
                json=message_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["success"] is True
            assert "message" in data["data"]

    async def test_get_chat_messages(self, client: AsyncClient, auth_headers: dict, test_chat_session_with_messages):
        """チャットメッセージ一覧取得APIのテスト"""
        response = await client.get(
            f"/api/v1/papers/{test_chat_session_with_messages.paper_id}/chat/{test_chat_session_with_messages.id}/messages",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


@pytest.mark.asyncio
class TestAgentExecutionAPI:
    """エージェント実行APIのテストクラス"""

    async def test_execute_outline_agent(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """アウトラインエージェント実行APIのテスト"""
        request_data = {
            "task": "create_outline",
            "parameters": {
                "research_topic": "機械学習の説明可能性",
                "target_sections": 5
            }
        }
        
        # OutlineAgentをモック
        from unittest.mock import patch, AsyncMock
        from app.services.agents import AgentResult, AgentStatus
        
        mock_result = AgentResult(
            result={"outline": [{"title": "はじめに", "description": "研究の背景"}]},
            status=AgentStatus.COMPLETED,
            execution_time=1.5
        )
        
        with patch.object(OutlineAgent, 'execute_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_result
            
            response = await client.post(
                f"/api/v1/papers/{test_paper.id}/agents/outline/execute",
                json=request_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "completed"

    async def test_execute_invalid_agent(self, client: AsyncClient, auth_headers: dict, test_paper: ResearchPaperModel):
        """無効なエージェント実行APIのテスト"""
        request_data = {
            "task": "test_task",
            "parameters": {}
        }
        
        response = await client.post(
            f"/api/v1/papers/{test_paper.id}/agents/invalid_agent/execute",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
class TestReferenceSearchAPI:
    """文献検索APIのテストクラス"""

    async def test_search_references(self, client: AsyncClient, auth_headers: dict):
        """文献検索APIのテスト"""
        search_data = {
            "query": "機械学習の説明可能性",
            "keywords": ["explainable AI", "interpretability"],
            "tags": ["machine_learning"],
            "limit": 10
        }
        
        # ReferenceAgentをモック
        from unittest.mock import patch, AsyncMock
        from app.services.agents import AgentResult, AgentStatus
        
        mock_search_response = {
            "search_results": [
                {
                    "id": "ref1",
                    "filename": "paper1.pdf",
                    "content": "機械学習の説明可能性に関する研究",
                    "relevance_score": 0.95,
                    "tags": ["machine_learning", "explainability"]
                }
            ],
            "citations": ["[1] Smith, J. (2023). Explainable AI."],
            "search_summary": {"total_results": 1},
            "query": "機械学習の説明可能性",
            "keywords": ["explainable AI", "interpretability"],
            "tags": ["machine_learning"]
        }
        
        mock_result = AgentResult(
            result={"search_response": mock_search_response},
            status=AgentStatus.COMPLETED,
            execution_time=0.8
        )
        
        with patch.object(ReferenceAgent, 'execute_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = mock_result
            
            response = await client.post(
                "/api/v1/papers/search/references",
                json=search_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "search_results" in data["data"]


@pytest.mark.asyncio
class TestAPIPermissions:
    """API権限のテストクラス"""

    async def test_unauthorized_access(self, client: AsyncClient):
        """認証なしアクセスのテスト"""
        response = await client.get("/api/v1/papers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_other_users_paper(self, client: AsyncClient, auth_headers: dict, other_users_paper: ResearchPaperModel):
        """他ユーザーの論文アクセステスト"""
        response = await client.get(
            f"/api/v1/papers/{other_users_paper.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND  # or 403_FORBIDDEN