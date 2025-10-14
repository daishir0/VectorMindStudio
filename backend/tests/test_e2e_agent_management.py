"""
エージェント管理システムE2Eテスト

エージェントCRUD、プロファイル管理、動的エージェントロードのE2Eテスト
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_session
from app.infrastructure.database.models import Base, AIAgentModel, AgentProfileModel
from app.infrastructure.database.session import engine
from app.main import app


@pytest.fixture(scope="module")
def event_loop():
    """イベントループを作成"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def async_client():
    """非同期HTTPクライアントを作成"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    """テスト用データベースをセットアップ"""
    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # テーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """データベースセッションを取得"""
    async for session in get_session():
        yield session


class TestAgentCRUD:
    """エージェントCRUD操作のE2Eテスト"""

    @pytest.mark.asyncio
    async def test_create_llm_based_agent(self, async_client: AsyncClient):
        """LLMベースエージェント作成テスト"""
        agent_data = {
            "name": "test_llm_agent",
            "display_name": "Test LLM Agent",
            "description": "LLMベースのテストエージェント",
            "category": "custom",
            "executor_type": "llm_based",
            "llm_model": "gpt-4o-mini",
            "system_prompt": "You are a test agent.",
            "user_prompt_template": "Answer: {input}",
            "response_format": "text",
            "priority": 10,
            "is_active": True,
            "is_system": False,
        }

        response = await async_client.post("/api/v1/agents", json=agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test_llm_agent"
        assert data["data"]["executor_type"] == "llm_based"

        return data["data"]["id"]

    @pytest.mark.asyncio
    async def test_create_code_based_agent(self, async_client: AsyncClient):
        """コードベースエージェント作成テスト"""
        agent_data = {
            "name": "test_code_agent",
            "display_name": "Test Code Agent",
            "description": "コードベースのテストエージェント",
            "category": "custom",
            "executor_type": "code_based",
            "class_path": "app.services.agents.outline_agent:OutlineAgent",
            "priority": 10,
            "is_active": True,
            "is_system": False,
        }

        response = await async_client.post("/api/v1/agents", json=agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "test_code_agent"
        assert data["data"]["executor_type"] == "code_based"

        return data["data"]["id"]

    @pytest.mark.asyncio
    async def test_list_agents(self, async_client: AsyncClient):
        """エージェント一覧取得テスト"""
        # まずエージェントを作成
        await self.test_create_llm_based_agent(async_client)

        response = await async_client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "agents" in data["data"]
        assert len(data["data"]["agents"]) > 0

    @pytest.mark.asyncio
    async def test_get_agent(self, async_client: AsyncClient):
        """エージェント詳細取得テスト"""
        # エージェント作成
        agent_id = await self.test_create_llm_based_agent(async_client)

        # エージェント取得
        response = await async_client.get(f"/api/v1/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == agent_id

    @pytest.mark.asyncio
    async def test_update_agent(self, async_client: AsyncClient):
        """エージェント更新テスト"""
        # エージェント作成
        agent_id = await self.test_create_llm_based_agent(async_client)

        # エージェント更新
        update_data = {
            "display_name": "Updated Agent Name",
            "description": "更新された説明",
        }

        response = await async_client.put(f"/api/v1/agents/{agent_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["display_name"] == "Updated Agent Name"

    @pytest.mark.asyncio
    async def test_toggle_agent_active(self, async_client: AsyncClient):
        """エージェント有効/無効切り替えテスト"""
        # エージェント作成
        agent_id = await self.test_create_llm_based_agent(async_client)

        # 無効化
        response = await async_client.patch(
            f"/api/v1/agents/{agent_id}/toggle-active",
            json={"is_active": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_agent(self, async_client: AsyncClient):
        """エージェント削除テスト"""
        # エージェント作成
        agent_id = await self.test_create_llm_based_agent(async_client)

        # エージェント削除
        response = await async_client.delete(f"/api/v1/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 削除確認
        response = await async_client.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 404


class TestProfileCRUD:
    """プロファイルCRUD操作のE2Eテスト"""

    @pytest.mark.asyncio
    async def test_create_profile(self, async_client: AsyncClient):
        """プロファイル作成テスト"""
        profile_data = {
            "name": "医学論文プロファイル",
            "paper_type": "medical",
            "description": "医学論文用の設定",
            "is_active": True,
        }

        response = await async_client.post("/api/v1/agent-profiles", json=profile_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "医学論文プロファイル"
        assert data["data"]["paper_type"] == "medical"

        return data["data"]["id"]

    @pytest.mark.asyncio
    async def test_list_profiles(self, async_client: AsyncClient):
        """プロファイル一覧取得テスト"""
        # プロファイル作成
        await self.test_create_profile(async_client)

        response = await async_client.get("/api/v1/agent-profiles")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    @pytest.mark.asyncio
    async def test_get_profile(self, async_client: AsyncClient):
        """プロファイル詳細取得テスト"""
        # プロファイル作成
        profile_id = await self.test_create_profile(async_client)

        # プロファイル取得
        response = await async_client.get(f"/api/v1/agent-profiles/{profile_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == profile_id

    @pytest.mark.asyncio
    async def test_update_profile(self, async_client: AsyncClient):
        """プロファイル更新テスト"""
        # プロファイル作成
        profile_id = await self.test_create_profile(async_client)

        # プロファイル更新
        update_data = {
            "name": "更新された医学論文プロファイル",
            "description": "更新された説明",
        }

        response = await async_client.put(f"/api/v1/agent-profiles/{profile_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "更新された医学論文プロファイル"

    @pytest.mark.asyncio
    async def test_set_default_profile(self, async_client: AsyncClient):
        """デフォルトプロファイル設定テスト"""
        # プロファイル作成
        profile_id = await self.test_create_profile(async_client)

        # デフォルト設定
        response = await async_client.patch(f"/api/v1/agent-profiles/{profile_id}/set-default")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_default"] is True

    @pytest.mark.asyncio
    async def test_clone_profile(self, async_client: AsyncClient):
        """プロファイル複製テスト"""
        # プロファイル作成
        profile_id = await self.test_create_profile(async_client)

        # プロファイル複製
        clone_data = {"new_name": "医学論文プロファイル（コピー）"}
        response = await async_client.post(f"/api/v1/agent-profiles/{profile_id}/clone", json=clone_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "コピー" in data["data"]["name"]

    @pytest.mark.asyncio
    async def test_delete_profile(self, async_client: AsyncClient):
        """プロファイル削除テスト"""
        # プロファイル作成
        profile_id = await self.test_create_profile(async_client)

        # プロファイル削除
        response = await async_client.delete(f"/api/v1/agent-profiles/{profile_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 削除確認
        response = await async_client.get(f"/api/v1/agent-profiles/{profile_id}")
        assert response.status_code == 404


class TestProfileSettings:
    """プロファイル設定のE2Eテスト"""

    @pytest.mark.asyncio
    async def test_bulk_update_profile_settings(self, async_client: AsyncClient):
        """プロファイル設定一括更新テスト"""
        # プロファイルとエージェント作成
        profile_test = TestProfileCRUD()
        agent_test = TestAgentCRUD()

        profile_id = await profile_test.test_create_profile(async_client)
        agent_id1 = await agent_test.test_create_llm_based_agent(async_client)
        agent_id2 = await agent_test.test_create_code_based_agent(async_client)

        # プロファイル設定一括更新
        settings = [
            {
                "agent_id": agent_id1,
                "is_enabled": True,
                "priority": 10,
                "max_retries": 3,
                "timeout_seconds": 300,
            },
            {
                "agent_id": agent_id2,
                "is_enabled": False,
                "priority": 20,
            },
        ]

        response = await async_client.put(
            f"/api/v1/agent-profiles/{profile_id}/settings",
            json=settings
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["settings"]) == 2


class TestAgentStatistics:
    """エージェント統計情報のE2Eテスト"""

    @pytest.mark.asyncio
    async def test_get_agent_statistics(self, async_client: AsyncClient):
        """エージェント統計情報取得テスト"""
        response = await async_client.get("/api/v1/agents/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_agents" in data["data"]
        assert "active_agents" in data["data"]
        assert "by_category" in data["data"]
        assert "by_executor_type" in data["data"]

    @pytest.mark.asyncio
    async def test_get_agent_execution_stats(self, async_client: AsyncClient):
        """エージェント実行統計取得テスト"""
        # エージェント作成
        agent_test = TestAgentCRUD()
        agent_id = await agent_test.test_create_llm_based_agent(async_client)

        response = await async_client.get(f"/api/v1/agents/{agent_id}/execution-stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_executions" in data["data"]
        assert "success_count" in data["data"]
        assert "failure_count" in data["data"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
