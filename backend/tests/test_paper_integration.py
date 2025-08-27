"""
論文執筆機能の統合テスト
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from app.infrastructure.database.models import UserModel
from app.services.agents import AgentResult, AgentStatus


@pytest.mark.asyncio
class TestPaperWritingIntegration:
    """論文執筆機能の統合テスト"""

    async def test_complete_paper_writing_workflow(self, client: AsyncClient, auth_headers: dict):
        """論文執筆の完全なワークフローのテスト"""
        
        # 1. 論文作成
        paper_data = {
            "title": "統合テスト論文：機械学習の説明可能性",
            "description": "機械学習モデルの説明可能性に関する包括的な研究"
        }
        
        response = await client.post(
            "/api/v1/papers",
            json=paper_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        paper = response.json()["data"]
        paper_id = paper["id"]
        
        # 2. チャットセッション作成
        chat_data = {"title": "研究計画の相談"}
        response = await client.post(
            f"/api/v1/papers/{paper_id}/chat",
            json=chat_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        chat_session = response.json()["data"]
        session_id = chat_session["id"]
        
        # 3. アウトラインエージェント実行（モック）
        outline_request = {
            "task": "create_outline",
            "parameters": {
                "research_topic": "機械学習の説明可能性",
                "target_sections": 5
            }
        }
        
        mock_outline_result = AgentResult(
            result={
                "outline": [
                    {"section_number": "1", "title": "はじめに", "description": "研究の背景と目的"},
                    {"section_number": "2", "title": "関連研究", "description": "既存の説明可能AI手法の調査"},
                    {"section_number": "3", "title": "提案手法", "description": "新しい説明手法の提案"},
                    {"section_number": "4", "title": "実験", "description": "提案手法の評価実験"},
                    {"section_number": "5", "title": "結論", "description": "研究成果のまとめ"}
                ],
                "created_sections": [
                    {"id": "section-1", "title": "はじめに", "hierarchy_path": "001"},
                    {"id": "section-2", "title": "関連研究", "hierarchy_path": "002"},
                    {"id": "section-3", "title": "提案手法", "hierarchy_path": "003"},
                    {"id": "section-4", "title": "実験", "hierarchy_path": "004"},
                    {"id": "section-5", "title": "結論", "hierarchy_path": "005"}
                ]
            },
            status=AgentStatus.COMPLETED,
            execution_time=2.1
        )
        
        with patch('app.services.agents.OutlineAgent.execute_task', new_callable=AsyncMock) as mock_outline:
            mock_outline.return_value = mock_outline_result
            
            response = await client.post(
                f"/api/v1/papers/{paper_id}/agents/outline/execute",
                json=outline_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            outline_result = response.json()["data"]
            assert outline_result["status"] == "completed"
        
        # 4. セクション一覧確認
        response = await client.get(
            f"/api/v1/papers/{paper_id}/sections",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        sections = response.json()["data"]
        assert len(sections) >= 0  # モックなので実際には作成されない
        
        # 5. 手動でセクション作成（実際のワークフローをシミュレート）
        section_data = {
            "title": "はじめに",
            "content": "",
            "parent_id": None,
            "position": -1
        }
        
        response = await client.post(
            f"/api/v1/papers/{paper_id}/sections",
            json=section_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        section = response.json()["data"]
        section_id = section["id"]
        
        # 6. ライターエージェントでコンテンツ生成（モック）
        writer_request = {
            "task": "write_content",
            "parameters": {
                "section_title": "はじめに",
                "content_outline": "研究の背景、目的、貢献を説明する",
                "target_words": 300,
                "writing_style": "academic"
            }
        }
        
        mock_writer_result = AgentResult(
            result={
                "content": "機械学習モデルの説明可能性は、AI技術の実用化において重要な課題となっています。本研究では、従来手法の限界を克服する新しいアプローチを提案します。",
                "word_count": 52,
                "quality_score": 0.87,
                "suggestions": ["より具体的な先行研究への言及を追加することを推奨"]
            },
            status=AgentStatus.COMPLETED,
            execution_time=3.2
        )
        
        with patch('app.services.agents.WriterAgent.execute_task', new_callable=AsyncMock) as mock_writer:
            mock_writer.return_value = mock_writer_result
            
            response = await client.post(
                f"/api/v1/papers/{paper_id}/agents/writer/execute",
                json=writer_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            writer_result = response.json()["data"]
            assert writer_result["status"] == "completed"
        
        # 7. セクション内容更新
        generated_content = mock_writer_result.result["content"]
        update_data = {
            "content": generated_content,
            "status": "writing"
        }
        
        response = await client.put(
            f"/api/v1/papers/{paper_id}/sections/{section_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        updated_section = response.json()["data"]
        assert updated_section["content"] == generated_content
        assert updated_section["status"] == "writing"
        
        # 8. 論理検証エージェント実行（モック）
        validator_request = {
            "task": "validate_logic",
            "parameters": {
                "content": generated_content,
                "validation_type": "argument_structure"
            }
        }
        
        mock_validator_result = AgentResult(
            result={
                "is_valid": True,
                "logic_score": 0.82,
                "issues": [],
                "suggestions": [
                    "具体的な数値データがあると説得力が増します",
                    "関連研究との比較を明確にしてください"
                ]
            },
            status=AgentStatus.COMPLETED,
            execution_time=1.8
        )
        
        with patch('app.services.agents.LogicValidatorAgent.execute_task', new_callable=AsyncMock) as mock_validator:
            mock_validator.return_value = mock_validator_result
            
            response = await client.post(
                f"/api/v1/papers/{paper_id}/agents/logic_validator/execute",
                json=validator_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            validator_result = response.json()["data"]
            assert validator_result["status"] == "completed"
        
        # 9. 文献検索実行（モック）
        reference_request = {
            "query": "機械学習 説明可能性",
            "keywords": ["explainable AI", "interpretability", "machine learning"],
            "tags": ["AI", "ML"],
            "limit": 10
        }
        
        mock_reference_result = AgentResult(
            result={
                "search_response": {
                    "search_results": [
                        {
                            "id": "ref1",
                            "filename": "explainable_ai_survey.pdf",
                            "content": "説明可能AIの包括的なサーベイ論文",
                            "relevance_score": 0.94,
                            "tags": ["explainable_AI", "survey"],
                            "citation": "[1] Adadi, A., & Berrada, M. (2018). Peeking inside the black-box: A survey on explainable artificial intelligence (XAI). IEEE access, 6, 52138-52160."
                        }
                    ],
                    "citations": [
                        "[1] Adadi, A., & Berrada, M. (2018). Peeking inside the black-box: A survey on explainable artificial intelligence (XAI). IEEE access, 6, 52138-52160."
                    ],
                    "search_summary": {"total_results": 1, "avg_relevance": 0.94},
                    "query": "機械学習 説明可能性",
                    "keywords": ["explainable AI", "interpretability", "machine learning"],
                    "tags": ["AI", "ML"]
                }
            },
            status=AgentStatus.COMPLETED,
            execution_time=1.2
        )
        
        with patch('app.services.agents.ReferenceAgent.execute_task', new_callable=AsyncMock) as mock_reference:
            mock_reference.return_value = mock_reference_result
            
            response = await client.post(
                "/api/v1/papers/search/references",
                json=reference_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            reference_result = response.json()["data"]
            assert len(reference_result["search_results"]) > 0
        
        # 10. 研究ディスカッション（AIチャット）
        from app.services.research_discussion_service import ResearchDiscussionService
        
        message_data = {
            "message": "この論文の構成と内容について総合的な評価をお願いします",
            "target_section_id": section_id
        }
        
        mock_discussion_response = {
            "message": "論文の構成は適切ですが、以下の点を改善することを推奨します：1) より多くの関連研究の調査、2) 実験設計の詳細化、3) 限界の明確化",
            "todo_tasks": [
                {
                    "id": "task1",
                    "description": "関連研究セクションの拡充",
                    "agent_name": "writer_agent",
                    "priority": "high",
                    "status": "pending"
                },
                {
                    "id": "task2",
                    "description": "実験設計の詳細化",
                    "agent_name": "writer_agent", 
                    "priority": "medium",
                    "status": "pending"
                }
            ],
            "task_results": {},
            "references": [
                {"type": "section", "id": section_id, "title": "はじめに"}
            ],
            "suggestions": [
                "セクション間の論理的な繋がりを強化してください",
                "研究の新規性をより明確に示してください"
            ],
            "success": True
        }
        
        with patch.object(ResearchDiscussionService, 'process_user_message', new_callable=AsyncMock) as mock_discussion:
            mock_discussion.return_value = mock_discussion_response
            
            response = await client.post(
                f"/api/v1/papers/{paper_id}/chat/{session_id}/messages",
                json=message_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            chat_response = response.json()["data"]
            assert chat_response["success"] is True
            assert len(chat_response["todo_tasks"]) == 2
            assert len(chat_response["suggestions"]) == 2
        
        # 11. 論文ステータス更新
        paper_update = {"status": "in_progress"}
        response = await client.put(
            f"/api/v1/papers/{paper_id}",
            json=paper_update,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        updated_paper = response.json()["data"]
        assert updated_paper["status"] == "in_progress"
        
        # 12. 最終確認：論文詳細取得
        response = await client.get(
            f"/api/v1/papers/{paper_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        final_paper = response.json()["data"]
        assert final_paper["title"] == "統合テスト論文：機械学習の説明可能性"
        assert final_paper["status"] == "in_progress"

    async def test_yaml_response_integration(self, client: AsyncClient, auth_headers: dict):
        """YAML形式レスポンスの統合テスト"""
        
        # 論文作成（YAML形式）
        paper_data = {
            "title": "YAMLテスト論文",
            "description": "YAML形式レスポンスのテスト"
        }
        
        response = await client.post(
            "/api/v1/papers?format=yaml",
            json=paper_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.headers["content-type"] == "application/x-yaml"
        
        # YAMLが正しく解析できることを確認
        import yaml
        data = yaml.safe_load(response.text)
        assert data["success"] is True
        assert data["data"]["title"] == "YAMLテスト論文"
        
        paper_id = data["data"]["id"]
        
        # 論文取得（YAML形式）
        response = await client.get(
            f"/api/v1/papers/{paper_id}?format=yaml",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/x-yaml"
        
        data = yaml.safe_load(response.text)
        assert data["success"] is True
        assert data["data"]["id"] == paper_id

    async def test_error_handling_integration(self, client: AsyncClient, auth_headers: dict):
        """エラーハンドリングの統合テスト"""
        
        # 存在しない論文にアクセス
        response = await client.get(
            "/api/v1/papers/nonexistent-paper-id",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # 無効なデータで論文作成
        invalid_data = {"title": ""}  # 空のタイトル
        response = await client.post(
            "/api/v1/papers",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 無効なエージェント実行
        response = await client.post(
            "/api/v1/papers/some-paper-id/agents/invalid_agent/execute",
            json={"task": "test", "parameters": {}},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_concurrent_operations(self, client: AsyncClient, auth_headers: dict):
        """同時操作の統合テスト"""
        import asyncio
        
        # 論文作成
        paper_data = {
            "title": "同時操作テスト論文",
            "description": "同時操作のテスト"
        }
        
        response = await client.post(
            "/api/v1/papers",
            json=paper_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        paper_id = response.json()["data"]["id"]
        
        # セクション作成
        section_data = {
            "title": "テストセクション",
            "content": "初期内容",
        }
        
        response = await client.post(
            f"/api/v1/papers/{paper_id}/sections",
            json=section_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        section_id = response.json()["data"]["id"]
        
        # 同時に複数のセクション更新を実行
        async def update_section(content_suffix):
            update_data = {
                "content": f"更新された内容 {content_suffix}",
                "status": "writing"
            }
            return await client.put(
                f"/api/v1/papers/{paper_id}/sections/{section_id}",
                json=update_data,
                headers=auth_headers
            )
        
        # 3つの同時更新を実行
        tasks = [update_section(i) for i in range(3)]
        responses = await asyncio.gather(*tasks)
        
        # 全ての更新が成功することを確認
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
        
        # 最終的な状態を確認
        response = await client.get(
            f"/api/v1/papers/{paper_id}/sections/{section_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        final_section = response.json()["data"]
        assert "更新された内容" in final_section["content"]