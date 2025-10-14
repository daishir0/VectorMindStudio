"""
研究ディスカッションシステムE2Eテスト

ResearchDiscussionServiceV3を使った会話ベースの論文執筆フローをテスト:
1. ユーザーがメッセージを送信（ChromaDB検索+セクション作成）
2. SupervisorV3が意図を分析（search_and_create）
3. Discovery Agentが検索を実行
4. Writer Agentがコンテンツを生成
5. セクションがDBに保存される
"""
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.infrastructure.database.models import Base, UserModel, ResearchPaperModel
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.services.research_discussion_service_v3 import ResearchDiscussionServiceV3


class TestE2EResearchDiscussion:
    """研究ディスカッションE2Eテスト"""

    @pytest.mark.asyncio
    async def test_conversation_based_paper_writing(self):
        """会話ベースの論文執筆フロー"""
        print("\n" + "="*80)
        print("E2Eテスト: 会話ベースの論文執筆（ResearchDiscussionServiceV3）")
        print("="*80)

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

            # 既存のdemoユーザーを取得（ブラウザからアクセス可能なユーザー）
            from app.infrastructure.database.models import UserModel
            from sqlalchemy import select as sql_select

            stmt = sql_select(UserModel).where(UserModel.username == "demo")
            result = await session.execute(stmt)
            test_user = result.scalar_one_or_none()

            if not test_user:
                # demoユーザーがいない場合は、最初のユーザーを使用
                stmt = sql_select(UserModel).limit(1)
                result = await session.execute(stmt)
                test_user = result.scalar_one_or_none()

            if not test_user:
                pytest.fail("テスト用のユーザーが見つかりません")

            print(f"✅ 使用ユーザー: {test_user.username} (ID: {test_user.id})")

            # 新規論文を作成
            paper = await paper_repo.create_paper(
                user_id=test_user.id,
                title="[E2Eテスト] AIエージェントによる自動論文執筆システムの研究",
                description="ResearchDiscussionServiceV3を使った会話ベースの論文執筆システムのE2Eテスト論文"
            )

            print(f"✅ 新規論文作成: {paper.title} (ID: {paper.id})")
            print(f"   ユーザーID: {test_user.id}")
            print(f"   アクセスURL: http://localhost:3000/papers/{paper.id}/chat/test-session-e2e-001")

            # ResearchDiscussionServiceV3を初期化
            service = ResearchDiscussionServiceV3(session)

            # ステップ1: エージェントロードの確認
            print("\n[ステップ1] エージェント動的ロード確認")
            await service._ensure_agents_loaded()
            print(f"  ロードされたエージェント数: {len(service.specialist_agents)}")
            print(f"  エージェント一覧: {list(service.specialist_agents.keys())}")

            # 必須エージェントの存在確認
            required_agents = ['discovery', 'writer', 'summary']
            for agent_name in required_agents:
                assert agent_name in service.specialist_agents, f"必須エージェント '{agent_name}' が見つかりません"

            print(f"  ✅ 必須エージェント（{', '.join(required_agents)}）が正常にロード済み")

            # ステップ2: テストメッセージの処理
            print("\n[ステップ2] テストメッセージ処理")
            test_message = "戸田城聖の思想や活動についてChromatdbで検索してセクションを作成してください"
            print(f"  テストメッセージ: {test_message}")

            # セッションIDとユーザーID（セッションIDはユニークに生成）
            import uuid
            session_id = f"e2e-session-{str(uuid.uuid4())[:8]}"
            user_id = test_user.id  # 実際のdemoユーザーIDを使用

            # メッセージ処理
            print("\n[ステップ3] process_user_message実行")
            response = await service.process_user_message(
                session_id=session_id,
                user_message=test_message,
                user_id=user_id,
                paper_id=paper.id
            )

            # 結果検証
            print("\n" + "="*80)
            print("実行結果の検証")
            print("="*80)

            # 必須チェック
            assert response.get('success') is True, "処理が成功していません"
            print("✅ Success: True")

            # メタデータ検証
            metadata = response.get('metadata', {})
            assert metadata.get('intent_type') in ['search_and_create', 'create_new'], \
                f"意図タイプが期待値と異なります: {metadata.get('intent_type')}"
            print(f"✅ Intent Type: {metadata.get('intent_type')}")

            assert metadata.get('confidence', 0) >= 0.8, \
                f"信頼度が低すぎます: {metadata.get('confidence')}"
            print(f"✅ Confidence: {metadata.get('confidence')}")

            # タスク実行結果確認
            task_results = response.get('task_results', {})
            assert len(task_results) > 0, "タスクが実行されていません"
            print(f"✅ Tasks Executed: {list(task_results.keys())}")

            # task_resultsは {agent_name: "完了"} の形式なので、"完了"文字列が含まれているか確認
            # DiscoveryAgentまたはWriterAgentが実行されたか確認
            agent_executed = any(task in task_results for task in ['discovery', 'content_generation'])
            assert agent_executed, "Discovery または Content Generation タスクが実行されていません"
            print(f"✅ Agent Tasks Completed: {', '.join([k for k in task_results.keys() if k in ['discovery', 'content_generation']])}")

            # セクション保存確認
            sections = await paper_repo.get_sections_by_paper(paper.id)
            assert len(sections) > 0, "セクションが保存されていません"

            # 最新セクションの内容確認
            latest_section = sections[-1]
            assert latest_section.content, "セクションの内容が空です"
            assert len(latest_section.content) > 100, "セクションの内容が短すぎます"
            print(f"✅ Section Saved: '{latest_section.title}' ({len(latest_section.content)}文字)")

            # ステップ4: 複数メッセージの会話フロー
            print("\n[ステップ4] 複数メッセージの会話フロー")

            # 2つ目のメッセージ: 既存セクションの修正
            message2 = "戸田城聖のセクションに、彼の教育理念についても追加してください"
            print(f"  メッセージ2: {message2}")

            response2 = await service.process_user_message(
                session_id=session_id,
                user_message=message2,
                user_id=user_id,
                paper_id=paper.id
            )

            assert response2.get('success') is True, "2つ目のメッセージ処理が失敗しました"
            print("  ✅ 2つ目のメッセージ処理成功")

            # 3つ目のメッセージ: 一般的な質問
            message3 = "論文の進捗状況を教えてください"
            print(f"  メッセージ3: {message3}")

            response3 = await service.process_user_message(
                session_id=session_id,
                user_message=message3,
                user_id=user_id,
                paper_id=paper.id
            )

            assert response3.get('success') is True, "3つ目のメッセージ処理が失敗しました"
            print("  ✅ 3つ目のメッセージ処理成功")

            # 最終結果サマリー
            print("\n" + "="*80)
            print("E2Eテスト完了サマリー")
            print("="*80)
            print(f"論文ID: {paper.id}")
            print(f"論文タイトル: {paper.title}")
            print(f"ユーザーID: {test_user.id}")
            print(f"セッションID: {session_id}")
            print(f"処理メッセージ数: 3件")

            final_sections = await paper_repo.get_sections_by_paper(paper.id)
            print(f"総セクション数: {len(final_sections)}件")

            for section in final_sections:
                print(f"  - {section.title}: {len(section.content)}文字")

            print("\n" + "="*80)
            print("画面で確認するには以下のURLにアクセスしてください:")
            print("="*80)
            print(f"📱 フロントエンドURL: http://localhost:3000/papers/{paper.id}/chat/{session_id}")
            print(f"📋 論文詳細: http://localhost:3000/papers/{paper.id}")
            print("="*80)

            print("\n✅ 全E2Eテスト合格！")

            return {
                "success": True,
                "paper_id": paper.id,
                "user_id": test_user.id,
                "session_id": session_id,
                "sessions_tested": 1,
                "messages_processed": 3,
                "sections_created": len(final_sections),
                "access_url": f"http://localhost:3000/papers/{paper.id}/chat/{session_id}"
            }

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"E2Eテストが失敗しました: {e}")

        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    # 直接実行の場合
    async def run_test():
        test = TestE2EResearchDiscussion()
        result = await test.test_conversation_based_paper_writing()

        # Slack通知（環境変数から取得）
        if result.get('success'):
            import subprocess
            slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

            if slack_webhook_url:
                paper_id = result['paper_id']
                session_id = result['session_id']
                sections_created = result['sections_created']

                slack_message = f'''{{
                    "text": "🎉 *新規論文でE2Eテスト合格！*\\n\\n✅ *テスト結果*\\n• 論文タイトル: [E2Eテスト] AIエージェントによる自動論文執筆システムの研究\\n• 論文ID: `{paper_id}`\\n• セッションID: `{session_id}`\\n• 作成セクション数: {sections_created}件\\n• 処理メッセージ数: 3件\\n\\n📱 *画面で確認（demoユーザーでアクセス可能）*\\nhttp://localhost:3000/papers/{paper_id}/chat/{session_id}\\n\\n🚀 *確認事項*\\n1. 上記URLにアクセス\\n2. チャット履歴が表示されること\\n3. 戸田城聖のセクションが作成されていること\\n4. 新規メッセージを送信できること"
                }}'''

                subprocess.run([
                    'curl', '-X', 'POST',
                    slack_webhook_url,
                    '-H', 'Content-Type: application/json',
                    '-d', slack_message
                ])

                print(f"\n✅ Slack通知送信完了")
            else:
                print(f"\n⚠️  SLACK_WEBHOOK_URL環境変数が設定されていないため、Slack通知はスキップされました")

        return result

    asyncio.run(run_test())
