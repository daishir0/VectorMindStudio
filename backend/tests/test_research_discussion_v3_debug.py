"""
ResearchDiscussionServiceV3の動作確認テスト
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base, UserModel, ResearchPaperModel
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.services.research_discussion_service_v3 import ResearchDiscussionServiceV3


async def test_research_discussion():
    """研究ディスカッション動作確認"""
    print("\n" + "=" * 80)
    print("ResearchDiscussionServiceV3 動作確認テスト")
    print("=" * 80)

    # データベース接続
    engine = create_async_engine(
        "sqlite+aiosqlite:///./vectormind.db",
        echo=False
    )

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    session = await async_session_maker().__aenter__()

    try:
        # ChromaDBクライアントを初期化
        from app.infrastructure.external.chroma_client import chroma_client
        try:
            await chroma_client.connect()
            print("✅ ChromaDB接続成功")
        except Exception as e:
            print(f"⚠️  ChromaDB接続失敗（テストは続行）: {e}")

        paper_repo = PaperRepository(session)

        # テストユーザーとペーパーを取得（既存のものを使用）
        # 直接SQLでペーパーを取得
        from sqlalchemy import select
        stmt = select(ResearchPaperModel).limit(1)
        result = await session.execute(stmt)
        paper = result.scalar_one_or_none()

        if not paper:
            print("❌ テスト用の論文が見つかりません")
            return

        print(f"✅ テスト論文: {paper.title} (ID: {paper.id})")

        # ResearchDiscussionServiceV3を初期化
        service = ResearchDiscussionServiceV3(session)

        # Step 1: エージェントロードの確認
        print("\n[Step 1] エージェント動的ロード確認")
        await service._ensure_agents_loaded()
        print(f"  ロードされたエージェント数: {len(service.specialist_agents)}")
        print(f"  エージェント一覧: {list(service.specialist_agents.keys())}")

        # Step 2: テストメッセージの処理
        print("\n[Step 2] テストメッセージ処理")
        test_message = "戸田城聖の思想や活動についてChromatdbで検索してセクションを作成してください"
        print(f"  テストメッセージ: {test_message}")

        # 仮のセッションIDとユーザーID
        session_id = "test-session-001"
        user_id = "test-user-001"

        # メッセージ処理
        print("\n[Step 3] process_user_message実行")
        response = await service.process_user_message(
            session_id=session_id,
            user_message=test_message,
            user_id=user_id,
            paper_id=paper.id
        )

        # 結果表示
        print("\n" + "=" * 80)
        print("実行結果")
        print("=" * 80)
        print(f"Success: {response.get('success')}")
        print(f"Message: {response.get('message', '')[:200]}")
        print(f"Task Results: {list(response.get('task_results', {}).keys())}")
        print(f"Metadata: {response.get('metadata', {})}")

        # デバッグログファイルの内容を表示
        debug_log_path = "/tmp/supervisor_debug.log"
        if os.path.exists(debug_log_path):
            print("\n[デバッグログ]")
            with open(debug_log_path, "r") as f:
                log_content = f.read()
                # 最後の500文字を表示
                print(log_content[-500:])

        print("\n✅ テスト完了")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_research_discussion())
