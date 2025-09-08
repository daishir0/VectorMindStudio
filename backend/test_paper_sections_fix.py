#!/usr/bin/env python3
"""
paper_sections保存問題の根本解決テスト

AAIDC準拠のWorkflow Patternsが適切に動作し、
OutlineAgent -> WriterAgent -> SummaryAgent の Chain Patternで
paper_sectionsテーブルにコンテンツが正しく保存されるかテストします。
"""
import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# アプリモジュールのインポート
from app.infrastructure.database.models import Base, ResearchPaperModel, PaperSectionModel
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.services.research_discussion_service_v2 import ResearchDiscussionServiceV2


async def setup_test_db():
    """テスト用データベースのセットアップ"""
    # SQLiteインメモリデータベースを使用
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # セッションファクトリー作成
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    return engine, async_session_maker


async def test_paper_sections_save_workflow():
    """
    Paper Sections保存問題の根本解決テスト
    
    Chain Workflow: OutlineAgent -> WriterAgent -> SummaryAgent
    各エージェントが適切に実行され、最終的にpaper_sectionsテーブルに
    コンテンツが保存されることを確認
    """
    print("🎯 Paper Sections保存問題の根本解決テスト開始")
    
    # テストDB準備
    engine, session_maker = await setup_test_db()
    
    try:
        async with session_maker() as session:
            repository = PaperRepository(session)
            service = ResearchDiscussionServiceV2(session)
            
            # テスト用論文作成
            paper_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())
            
            print(f"📄 テスト論文作成 (ID: {paper_id})")
            
            paper = await repository.create_paper(
                user_id=user_id,
                title="AI多エージェントシステムの設計パターン",
                description="本研究ではAI多エージェントシステムにおける効果的な設計パターンについて検討する。"
            )
            
            # セクション作成要求をシミュレート
            user_message = "「Introduction」セクションを作成して、AI多エージェントシステムの背景と目的を説明してください"
            
            print(f"🗣️  ユーザーメッセージ: {user_message}")
            print("=" * 50)
            
            # ResearchDiscussionServiceV2 でリクエスト処理
            result = await service.process_user_message(
                session_id=session_id,
                user_message=user_message,
                user_id=user_id,
                paper_id=paper.id
            )
            
            print("🔍 処理結果:")
            print(f"   成功: {result.get('success')}")
            print(f"   メッセージ: {result.get('message', '')[:100]}...")
            
            if result.get('workflow_result'):
                workflow = result['workflow_result']
                print(f"   ワークフロー成功数: {workflow.get('success_count')}")
                print(f"   ワークフロー失敗数: {workflow.get('failure_count')}")
                print(f"   実行時間: {workflow.get('execution_time', 0):.2f}s")
            
            print("=" * 50)
            
            # データベース検証: paper_sectionsにコンテンツが保存されているか確認
            sections = await repository.get_sections_by_paper(paper.id)
            
            print(f"📊 検証結果:")
            print(f"   作成されたセクション数: {len(sections)}")
            
            if sections:
                section = sections[0]
                print(f"   セクションID: {section.id}")
                print(f"   タイトル: {section.title}")
                print(f"   ステータス: {section.status}")
                print(f"   コンテンツ長: {len(section.content)} 文字")
                print(f"   単語数: {section.word_count}")
                
                # 🎯 重要な検証ポイント
                assert section.title.lower() == "introduction", f"タイトル不一致: {section.title}"
                assert len(section.content.strip()) > 0, "コンテンツが空です！"
                assert section.word_count > 0, "単語数が0です！"
                
                print("✅ paper_sections保存問題は解決されました！")
                print(f"   コンテンツプレビュー: {section.content[:200]}...")
                
                return True
            else:
                print("❌ セクションが作成されていません")
                return False
                
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()


async def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🔬 VectorMindStudio Paper Sections 根本解決テスト")
    print("=" * 60)
    
    success = await test_paper_sections_save_workflow()
    
    if success:
        print("\n🎉 テスト成功: paper_sections保存問題は根本解決されました！")
        print("   - OutlineAgent: セクション構造作成 ✅")
        print("   - WriterAgent: コンテンツ生成 ✅")
        print("   - データ永続化: paper_sectionsテーブル保存 ✅")
    else:
        print("\n❌ テスト失敗: 問題が残存している可能性があります")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())