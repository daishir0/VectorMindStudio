"""
E2Eテスト: SupervisorAgent による複数エージェント連携

3つのストーリーをテスト:
1. 検索→要約→執筆 (シンプルなパイプライン)
2. 検索→複数セクション執筆→品質チェック
3. 検索→分析→執筆→編集→品質チェック (フルパイプライン)
"""
import pytest
import asyncio
import uuid
import sys
import os
from datetime import datetime

# パス設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import UserModel, ResearchPaperModel
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.services.supervisor_agent import SupervisorAgent
from app.services.dynamic_agent_loader import DynamicAgentLoader


class TestE2ESupervisorAgent:
    """SupervisorAgent E2Eテスト"""

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

        # DynamicAgentLoader初期化
        agent_loader = DynamicAgentLoader(agent_repo, llm_client=None)

        # SupervisorAgent初期化
        supervisor = SupervisorAgent(
            agent_loader=agent_loader,
            agent_repository=agent_repo,
            session=session
        )

        return {
            "session": session,
            "engine": engine,
            "agent_repo": agent_repo,
            "paper_repo": paper_repo,
            "user": user,
            "supervisor": supervisor,
            "agent_loader": agent_loader
        }

    async def create_test_paper(self, paper_repo, user_id: str, title: str) -> ResearchPaperModel:
        """テスト用論文を作成"""
        paper = await paper_repo.create_paper(
            user_id=user_id,
            title=title,
            description="SupervisorAgentによる自動生成論文"
        )
        return paper

    async def test_story_1_search_summarize_write(self):
        """
        ストーリー1: 検索→要約→執筆

        シナリオ:
        「AIエージェントに関する資料を検索して要約し、関連研究セクションを執筆して」
        """
        env = await self.setup_test_environment()

        try:
            supervisor = env["supervisor"]
            paper_repo = env["paper_repo"]
            user = env["user"]

            print("\n" + "="*80)
            print("【ストーリー1】検索→要約→執筆")
            print("="*80)

            # テスト論文作成
            paper = await self.create_test_paper(
                paper_repo,
                user.id,
                "AIエージェントシステムの最新動向"
            )

            # ユーザーリクエスト
            user_message = "AIエージェントに関する資料を検索して要約し、関連研究セクションを執筆してください"

            # SupervisorAgentで処理
            result = await supervisor.process_user_request(
                user_message=user_message,
                template_name="search_summarize_write",
                context={
                    "search_query": "AI agent",
                    "user_id": user.id,
                    "paper_id": paper.id,
                    "section_title": "関連研究"
                }
            )

            # チャット履歴表示
            print("\n【チャット履歴】")
            print(supervisor.get_chat_history())

            # 論文内容を取得
            updated_paper = await paper_repo.get_paper_by_id(paper.id)
            sections = await paper_repo.get_sections_by_paper(paper.id)

            # 論文全文生成
            paper_content = self._generate_paper_content(updated_paper, sections)

            print("\n【生成された論文】")
            print(paper_content)

            # 結果を返す
            return {
                "story": "ストーリー1: 検索→要約→執筆",
                "success": result.success,
                "chat_history": supervisor.get_chat_history(),
                "paper_content": paper_content,
                "paper_title": updated_paper.title,
                "execution_time": result.total_time
            }

        finally:
            await env["session"].close()
            await env["engine"].dispose()

    async def test_story_2_multi_section_with_quality(self):
        """
        ストーリー2: 検索→複数セクション執筆→品質チェック

        シナリオ:
        「機械学習に関する資料を検索し、『はじめに』と『関連研究』を執筆して品質チェックして」
        """
        env = await self.setup_test_environment()

        try:
            supervisor = env["supervisor"]
            paper_repo = env["paper_repo"]
            user = env["user"]

            print("\n" + "="*80)
            print("【ストーリー2】検索→複数セクション執筆→品質チェック")
            print("="*80)

            # テスト論文作成
            paper = await self.create_test_paper(
                paper_repo,
                user.id,
                "機械学習を用いたデータ分析手法"
            )

            # ユーザーリクエスト
            user_message = "機械学習に関する資料を検索し、『はじめに』と『関連研究』を執筆して品質チェックしてください"

            # SupervisorAgentで処理
            result = await supervisor.process_user_request(
                user_message=user_message,
                template_name="multi_section_with_quality",
                context={
                    "search_query": "machine learning",
                    "user_id": user.id,
                    "paper_id": paper.id
                }
            )

            # チャット履歴表示
            print("\n【チャット履歴】")
            print(supervisor.get_chat_history())

            # 論文内容を取得
            updated_paper = await paper_repo.get_paper_by_id(paper.id)
            sections = await paper_repo.get_sections_by_paper(paper.id)

            # 論文全文生成
            paper_content = self._generate_paper_content(updated_paper, sections)

            print("\n【生成された論文】")
            print(paper_content)

            # 結果を返す
            return {
                "story": "ストーリー2: 検索→複数セクション執筆→品質チェック",
                "success": result.success,
                "chat_history": supervisor.get_chat_history(),
                "paper_content": paper_content,
                "paper_title": updated_paper.title,
                "execution_time": result.total_time
            }

        finally:
            await env["session"].close()
            await env["engine"].dispose()

    async def test_story_3_full_pipeline(self):
        """
        ストーリー3: 検索→分析→執筆→編集→品質チェック

        シナリオ:
        「深層学習に関する資料を検索・分析し、提案手法セクションを執筆・編集して品質チェックまで行って」
        """
        env = await self.setup_test_environment()

        try:
            supervisor = env["supervisor"]
            paper_repo = env["paper_repo"]
            user = env["user"]

            print("\n" + "="*80)
            print("【ストーリー3】検索→分析→執筆→編集→品質チェック")
            print("="*80)

            # テスト論文作成
            paper = await self.create_test_paper(
                paper_repo,
                user.id,
                "深層学習による画像認識の新手法"
            )

            # ユーザーリクエスト
            user_message = "深層学習に関する資料を検索・分析し、提案手法セクションを執筆・編集して品質チェックまで行ってください"

            # SupervisorAgentで処理
            result = await supervisor.process_user_request(
                user_message=user_message,
                template_name="full_pipeline",
                context={
                    "search_query": "deep learning",
                    "user_id": user.id,
                    "paper_id": paper.id,
                    "section_title": "提案手法"
                }
            )

            # チャット履歴表示
            print("\n【チャット履歴】")
            print(supervisor.get_chat_history())

            # 論文内容を取得
            updated_paper = await paper_repo.get_paper_by_id(paper.id)
            sections = await paper_repo.get_sections_by_paper(paper.id)

            # 論文全文生成
            paper_content = self._generate_paper_content(updated_paper, sections)

            print("\n【生成された論文】")
            print(paper_content)

            # 結果を返す
            return {
                "story": "ストーリー3: 検索→分析→執筆→編集→品質チェック",
                "success": result.success,
                "chat_history": supervisor.get_chat_history(),
                "paper_content": paper_content,
                "paper_title": updated_paper.title,
                "execution_time": result.total_time
            }

        finally:
            await env["session"].close()
            await env["engine"].dispose()

    def _generate_paper_content(self, paper: ResearchPaperModel, sections: list) -> str:
        """論文全文を生成"""
        content = f"# {paper.title}\n\n"
        content += f"{paper.description}\n\n"
        content += "---\n\n"

        if sections:
            for section in sections:
                content += f"## {section.section_number}. {section.title}\n\n"
                if section.content:
                    content += f"{section.content}\n\n"
                else:
                    content += "(内容未記入)\n\n"
        else:
            content += "(セクションなし)\n"

        return content


async def run_all_stories():
    """全ストーリーを実行"""
    test = TestE2ESupervisorAgent()

    results = []

    print("\n" + "="*80)
    print("SupervisorAgent E2Eテスト - 3つのストーリー")
    print("="*80)

    # ストーリー1
    print("\n\n🎬 ストーリー1を開始...")
    result1 = await test.test_story_1_search_summarize_write()
    results.append(result1)

    # ストーリー2
    print("\n\n🎬 ストーリー2を開始...")
    result2 = await test.test_story_2_multi_section_with_quality()
    results.append(result2)

    # ストーリー3
    print("\n\n🎬 ストーリー3を開始...")
    result3 = await test.test_story_3_full_pipeline()
    results.append(result3)

    # 全体サマリー
    print("\n\n" + "="*80)
    print("【全ストーリー完了サマリー】")
    print("="*80)

    for i, result in enumerate(results, 1):
        status = "✅ 成功" if result["success"] else "❌ 失敗"
        print(f"\n{i}. {result['story']}")
        print(f"   ステータス: {status}")
        print(f"   論文タイトル: {result['paper_title']}")
        print(f"   実行時間: {result['execution_time']:.1f}秒")

    return results


if __name__ == "__main__":
    results = asyncio.run(run_all_stories())

    # 結果を保存
    output_dir = "/home/ec2-user/hirashimallc/17_pj-VectorMindStudio/outputs/supervisor_e2e"
    os.makedirs(output_dir, exist_ok=True)

    for i, result in enumerate(results, 1):
        # チャット履歴を保存
        chat_file = f"{output_dir}/story{i}_chat_history.txt"
        with open(chat_file, "w", encoding="utf-8") as f:
            f.write(f"【{result['story']}】\n\n")
            f.write(result["chat_history"])

        # 論文を保存
        paper_file = f"{output_dir}/story{i}_paper.md"
        with open(paper_file, "w", encoding="utf-8") as f:
            f.write(result["paper_content"])

        print(f"\n✅ ストーリー{i}の結果を保存: {output_dir}/")

    print(f"\n🎉 全ストーリーのテスト完了!")
