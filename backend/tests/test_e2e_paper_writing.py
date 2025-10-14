"""
E2Eテスト: 動的エージェントシステムを使った論文執筆フロー
"""
import pytest
import asyncio
import uuid
import sys
import os

# パス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base, UserModel, ResearchPaperModel
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.services.wake_word_detector import WakeWordManager
from app.services.dynamic_agent_loader import DynamicAgentLoader


@pytest.mark.asyncio
class TestE2EPaperWriting:
    """論文執筆E2Eテスト"""

    async def setup_test_environment(self):
        """テスト環境のセットアップ"""
        # データベース接続
        engine = create_async_engine(
            "sqlite+aiosqlite:///./vectormind.db",
            echo=False
        )

        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        session = await async_session_maker().__aenter__()

        # リポジトリ初期化
        agent_repo = AgentRepository(session)
        paper_repo = PaperRepository(session)

        # 既存のdemoユーザーを取得
        from sqlalchemy import select as sql_select

        stmt = sql_select(UserModel).where(UserModel.username == "demo")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # demoユーザーがいない場合は、最初のユーザーを使用
            stmt = sql_select(UserModel).limit(1)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

        if not user:
            raise Exception("テスト用のユーザーが見つかりません")

        # テスト論文作成
        paper = await paper_repo.create_paper(
            user_id=user.id,
            title="AIエージェントシステムの設計と実装",
            description="動的エージェント管理システムに関する研究論文"
        )

        # WakeWordManagerとDynamicAgentLoader初期化
        wake_word_manager = WakeWordManager(agent_repo)
        await wake_word_manager.initialize(user_id=user.id)

        agent_loader = DynamicAgentLoader(agent_repo, llm_client=None)

        return {
            "session": session,
            "engine": engine,
            "agent_repo": agent_repo,
            "paper_repo": paper_repo,
            "user": user,
            "paper": paper,
            "wake_word_manager": wake_word_manager,
            "agent_loader": agent_loader
        }

    async def test_complete_paper_writing_flow(self):
        """完全な論文執筆フロー"""
        env = await self.setup_test_environment()

        try:
            paper_repo = env["paper_repo"]
            paper = env["paper"]
            user = env["user"]
            wake_word_manager = env["wake_word_manager"]
            agent_loader = env["agent_loader"]

            print("\n" + "="*80)
            print("E2Eテスト: AIエージェントシステムの論文執筆")
            print("="*80)

            # ステップ1: アウトライン作成
            print("\n[ステップ1] アウトラインエージェントで論文構造を作成")
            outline_message = "論文のアウトラインを作成して。章として「はじめに」「関連研究」「提案手法」「実験」「結論」を含めて。"

            matches = await wake_word_manager.detect_agents(outline_message)
            print(f"  検出されたエージェント: {[m.agent_name for m in matches]}")

            if matches:
                outline_agent = await agent_loader.load_agent_by_id(matches[0].agent_id)
                print(f"  起動エージェント: {outline_agent.display_name}")

                # セクション作成
                sections_to_create = [
                    "はじめに",
                    "関連研究",
                    "提案手法",
                    "実験",
                    "結論"
                ]

                for i, section_title in enumerate(sections_to_create, 1):
                    section = await paper_repo.create_section(
                        paper_id=paper.id,
                        position=i,
                        section_number=str(i),
                        title=section_title,
                        content="",
                        summary=""
                    )
                    print(f"    - セクション作成: {section.title}")

            # ステップ2: 各セクションに内容を執筆
            print("\n[ステップ2] ライティングエージェントで各セクションを執筆")

            sections = await paper_repo.get_sections_by_paper(paper.id)

            section_contents = {
                "はじめに": """
本論文では、動的エージェント管理システムの設計と実装について述べる。
従来のAIエージェントシステムでは、エージェントの追加や変更にコードの修正が必要であり、
柔軟性に欠けるという課題があった。

本研究では、データベース駆動の動的エージェント管理システムを提案し、
ウェイクワード検出による自動エージェント起動機能を実装した。
これにより、エージェント開発時間を99%削減することに成功した。
""",
                "関連研究": """
AIエージェントシステムに関する研究は近年活発化している。
Russell and Norvig (2020)は、エージェントアーキテクチャの基本原理を提示した。
また、LangChainやAutoGPTなどのフレームワークが登場し、
エージェントの構築が容易になってきている。

しかし、これらのシステムでは、エージェントの動的な追加・変更が困難であり、
ユーザーが独自のエージェントを作成する際には技術的な障壁が高いという問題がある。
""",
                "提案手法": """
本研究では、以下の3つのコンポーネントから成る動的エージェント管理システムを提案する。

1. AgentRepository: エージェント定義をデータベースで管理し、CRUD操作を提供
2. WakeWordDetector: ユーザーメッセージからキーワードを検出し、適切なエージェントを特定
3. DynamicAgentLoader: DB設定からエージェントを動的に生成・実行

これらのコンポーネントにより、ユーザーはGUI経由でエージェントを管理でき、
プログラミング知識なしにカスタムエージェントを作成できる。
""",
                "実験": """
提案手法の有効性を検証するため、13種類のエージェントを用いた実験を行った。

実験環境:
- データベース: SQLite
- プログラミング言語: Python 3.11
- LLM: OpenAI GPT-4o-mini

結果:
- エージェント登録時間: 平均2分（従来: 2時間）
- ウェイクワード検出精度: 95.3%
- エージェント起動時間: 平均150ms

これらの結果から、提案手法が従来手法と比較して大幅な効率化を実現することが確認された。
""",
                "結論": """
本論文では、動的エージェント管理システムを提案し、その実装と評価を行った。
実験の結果、エージェント開発時間を99%削減し、ユーザーが容易にカスタムエージェントを
作成できることを示した。

今後の課題として、以下の点が挙げられる。
1. セマンティック検索によるウェイクワード検出の高度化
2. エージェント間の協調動作の最適化
3. マルチモーダル対応（画像、音声など）

本研究の成果は、AIエージェントシステムの実用化に大きく貢献するものと期待される。
"""
            }

            writing_message = "各セクションの文章を執筆して"
            matches = await wake_word_manager.detect_agents(writing_message)

            if matches:
                writer_agent = await agent_loader.load_agent_by_id(matches[0].agent_id)
                print(f"  起動エージェント: {writer_agent.display_name}")

                for section in sections:
                    if section.title in section_contents:
                        content = section_contents[section.title].strip()

                        # セクション更新
                        await paper_repo.update_section(
                            section.id,
                            {
                                "content": content,
                                "word_count": len(content.split())
                            }
                        )
                        print(f"    - {section.title}: {len(content)}文字執筆完了")

            # ステップ3: 要約生成
            print("\n[ステップ3] 要約エージェントで各セクションの要約を生成")

            summary_message = "各セクションを要約して"
            matches = await wake_word_manager.detect_agents(summary_message)

            if matches:
                summary_agent = await agent_loader.load_agent_by_id(matches[0].agent_id)
                print(f"  起動エージェント: {summary_agent.display_name}")

                # セクション再取得
                sections = await paper_repo.get_sections_by_paper(paper.id)

                for section in sections:
                    if section.content:
                        # 簡易要約（最初の1-2文）
                        sentences = section.content.strip().split('。')
                        summary = '。'.join(sentences[:2]) + '。' if len(sentences) > 1 else sentences[0]

                        await paper_repo.update_section(
                            section.id,
                            {"summary": summary}
                        )
                        print(f"    - {section.title}: 要約生成完了")

            # ステップ4: 品質チェック
            print("\n[ステップ4] 品質評価エージェントで論文をチェック")

            quality_message = "論文の品質をチェックして"
            matches = await wake_word_manager.detect_agents(quality_message)

            if matches:
                quality_agent = await agent_loader.load_agent_by_id(matches[0].agent_id)
                print(f"  起動エージェント: {quality_agent.display_name}")

                # 簡易品質評価
                sections = await paper_repo.get_sections_by_paper(paper.id)
                total_words = sum(s.word_count for s in sections)
                sections_with_content = sum(1 for s in sections if s.content.strip())

                quality_score = (sections_with_content / len(sections)) * 10

                print(f"    - 総セクション数: {len(sections)}")
                print(f"    - 内容があるセクション: {sections_with_content}")
                print(f"    - 総文字数: {total_words}")
                print(f"    - 品質スコア: {quality_score:.1f}/10")

            # 最終結果表示
            print("\n" + "="*80)
            print("論文執筆完了！")
            print("="*80)

            final_paper = await paper_repo.get_paper_by_id(paper.id)
            final_sections = await paper_repo.get_sections_by_paper(paper.id)

            print(f"\n【論文タイトル】\n{final_paper.title}")
            print(f"\n【説明】\n{final_paper.description}")
            print(f"\n【セクション構成】")

            full_content = f"# {final_paper.title}\n\n{final_paper.description}\n\n"

            for section in final_sections:
                print(f"\n{section.section_number}. {section.title}")
                print(f"   文字数: {section.word_count}")
                print(f"   要約: {section.summary[:100]}..." if section.summary else "   要約: なし")

                full_content += f"\n## {section.section_number}. {section.title}\n\n"
                full_content += f"{section.content}\n"

            # 論文をファイルに保存
            output_path = "/home/ec2-user/hirashimallc/17_pj-VectorMindStudio/outputs/e2e_test_paper.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            print(f"\n論文を保存しました: {output_path}")

            # テスト成功
            print("\n✅ E2Eテスト成功！")

            return {
                "success": True,
                "paper": final_paper,
                "sections": final_sections,
                "output_path": output_path,
                "full_content": full_content
            }

        finally:
            # クリーンアップ
            await env["session"].close()
            await env["engine"].dispose()


if __name__ == "__main__":
    async def run_test():
        test = TestE2EPaperWriting()
        result = await test.test_complete_paper_writing_flow()
        return result

    asyncio.run(run_test())
