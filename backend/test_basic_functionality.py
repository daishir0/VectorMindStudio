#!/usr/bin/env python3
"""
論文執筆機能の基本動作確認テスト
"""
import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_database_models():
    """データベースモデルの基本テスト"""
    print("📊 データベースモデルのテスト...")
    
    try:
        from app.infrastructure.database.models import (
            ResearchPaperModel, PaperSectionModel, PaperSectionHistoryModel,
            PaperChatSessionModel, PaperChatMessageModel
        )
        
        # モデルの基本属性チェック
        paper = ResearchPaperModel()
        assert hasattr(paper, 'title')
        assert hasattr(paper, 'description')
        assert hasattr(paper, 'status')
        
        section = PaperSectionModel()
        assert hasattr(section, 'hierarchy_path')
        assert hasattr(section, 'section_number')
        assert hasattr(section, 'title')
        assert hasattr(section, 'content')
        
        print("✅ データベースモデル: OK")
        return True
        
    except Exception as e:
        print(f"❌ データベースモデル: {e}")
        return False

async def test_agent_imports():
    """AIエージェントのインポートテスト"""
    print("🤖 AIエージェントのインポートテスト...")
    
    try:
        from app.services.agents import (
            BaseAgent, OutlineAgent, SummaryAgent, WriterAgent,
            LogicValidatorAgent, ReferenceAgent,
            AgentTask, AgentResult, AgentStatus
        )
        
        # エージェントクラスの基本チェック
        assert issubclass(OutlineAgent, BaseAgent)
        assert issubclass(SummaryAgent, BaseAgent)
        assert issubclass(WriterAgent, BaseAgent)
        assert issubclass(LogicValidatorAgent, BaseAgent)
        assert issubclass(ReferenceAgent, BaseAgent)
        
        # ステータスの確認
        assert hasattr(AgentStatus, 'PENDING')
        assert hasattr(AgentStatus, 'IN_PROGRESS')
        assert hasattr(AgentStatus, 'COMPLETED')
        assert hasattr(AgentStatus, 'FAILED')
        
        print("✅ AIエージェント: OK")
        return True
        
    except Exception as e:
        print(f"❌ AIエージェント: {e}")
        return False

async def test_repository_import():
    """リポジトリクラスのインポートテスト"""
    print("🗄️ リポジトリクラスのインポートテスト...")
    
    try:
        from app.infrastructure.repositories.paper_repository import PaperRepository
        
        # リポジトリの基本メソッドチェック
        assert hasattr(PaperRepository, 'create_paper')
        assert hasattr(PaperRepository, 'get_paper_by_id')
        assert hasattr(PaperRepository, 'create_section')
        assert hasattr(PaperRepository, 'get_sections_by_paper')
        assert hasattr(PaperRepository, 'create_chat_session')
        
        print("✅ リポジトリクラス: OK")
        return True
        
    except Exception as e:
        print(f"❌ リポジトリクラス: {e}")
        return False

async def test_service_import():
    """サービスクラスのインポートテスト"""
    print("🧠 サービスクラスのインポートテスト...")
    
    try:
        from app.services.research_discussion_service import ResearchDiscussionService
        
        # サービスの基本メソッドチェック
        assert hasattr(ResearchDiscussionService, 'process_user_message')
        assert hasattr(ResearchDiscussionService, '_analyze_user_intent')
        assert hasattr(ResearchDiscussionService, '_generate_todo_tasks')
        assert hasattr(ResearchDiscussionService, '_execute_tasks')
        
        print("✅ サービスクラス: OK")
        return True
        
    except Exception as e:
        print(f"❌ サービスクラス: {e}")
        return False

async def test_api_import():
    """APIエンドポイントのインポートテスト"""
    print("🌐 APIエンドポイントのインポートテスト...")
    
    try:
        from app.api.v1 import papers
        
        # ルーターの確認
        assert hasattr(papers, 'router')
        
        # 基本的なエンドポイント関数の確認
        assert hasattr(papers, 'get_papers')
        assert hasattr(papers, 'create_paper')
        assert hasattr(papers, 'get_sections')
        assert hasattr(papers, 'create_section')
        
        print("✅ APIエンドポイント: OK")
        return True
        
    except Exception as e:
        print(f"❌ APIエンドポイント: {e}")
        return False

async def test_schemas():
    """スキーマのインポートテスト"""
    print("📋 スキーマのインポートテスト...")
    
    try:
        from app.schemas.paper import (
            PaperCreate, PaperUpdate, PaperDetail, PaperSummary,
            SectionCreate, SectionUpdate, SectionDetail, SectionOutline,
            ChatSessionCreate, ChatMessageCreate, ChatResponse,
            AgentExecuteRequest, AgentExecuteResponse
        )
        
        # 基本スキーマのインスタンス作成テスト
        paper_create = PaperCreate(title="テスト論文")
        assert paper_create.title == "テスト論文"
        
        section_create = SectionCreate(title="テストセクション")
        assert section_create.title == "テストセクション"
        
        print("✅ スキーマ: OK")
        return True
        
    except Exception as e:
        print(f"❌ スキーマ: {e}")
        return False

async def test_agent_task_creation():
    """エージェントタスク作成の基本テスト"""
    print("⚙️ エージェントタスク作成テスト...")
    
    try:
        from app.services.agents import OutlineAgent, AgentStatus
        from unittest.mock import AsyncMock
        
        # モックセッションでエージェント作成
        mock_session = AsyncMock()
        agent = OutlineAgent(mock_session)
        
        # タスク作成テスト
        task = agent.create_task(
            task_type="create_outline",
            parameters={"paper_id": "test-id", "research_topic": "テストトピック"}
        )
        
        assert task.task_type == "create_outline"
        assert task.parameters["paper_id"] == "test-id"
        assert task.status == AgentStatus.PENDING
        
        print("✅ エージェントタスク作成: OK")
        return True
        
    except Exception as e:
        print(f"❌ エージェントタスク作成: {e}")
        return False

async def main():
    """メインテスト実行関数"""
    print("🧪 VectorMindStudio 論文執筆機能 基本動作確認")
    print("=" * 60)
    
    tests = [
        test_database_models,
        test_agent_imports,
        test_repository_import,
        test_service_import,
        test_api_import,
        test_schemas,
        test_agent_task_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
    
    print("\n" + "=" * 60)
    print("📊 基本動作確認結果")
    print("=" * 60)
    print(f"総テスト数: {total}")
    print(f"成功: {passed}")
    print(f"失敗: {total - passed}")
    
    if passed == total:
        print("\n🎉 全ての基本動作確認が成功しました!")
        print("✨ 論文執筆機能の基本実装は正常に動作しています!")
        return True
    else:
        print(f"\n⚠️  {total - passed} 個のテストが失敗しました")
        print("🔧 実装を確認して修正してください")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)