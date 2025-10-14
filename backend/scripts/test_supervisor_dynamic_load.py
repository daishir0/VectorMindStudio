"""
SupervisorAgentの動的エージェント読み込みテスト
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数の読み込み
from dotenv import load_dotenv
env_path = project_root / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.agent_repository import AgentRepository
from app.services.agents.supervisor_agent import SupervisorAgent


async def test_supervisor_dynamic_load():
    """SupervisorAgentの動的エージェント読み込みテスト"""
    print("=" * 60)
    print("SupervisorAgent動的読み込みテスト開始")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # SupervisorAgentを初期化
        supervisor = SupervisorAgent(session=session)

        print(f"\n✅ SupervisorAgent初期化完了")
        print(f"   - agent_capabilities初期状態: {len(supervisor.agent_capabilities)}個")
        print(f"   - _agent_capabilities_loaded: {supervisor._agent_capabilities_loaded}")

        # DBからエージェント能力を読み込み
        print("\n📥 DBからエージェント能力を読み込み中...")
        await supervisor._load_agent_capabilities_from_db()

        print(f"\n✅ エージェント能力読み込み完了")
        print(f"   - agent_capabilities: {len(supervisor.agent_capabilities)}個")
        print(f"   - _agent_capabilities_loaded: {supervisor._agent_capabilities_loaded}")

        # 読み込まれたエージェント一覧を表示
        if supervisor.agent_capabilities:
            print("\n" + "=" * 60)
            print("読み込まれたエージェント一覧")
            print("=" * 60)

            for idx, (agent_key, agent_info) in enumerate(supervisor.agent_capabilities.items(), 1):
                print(f"\n{idx}. {agent_key}")
                print(f"   表示名: {agent_info.get('display_name', 'N/A')}")
                print(f"   説明: {agent_info.get('description', 'N/A')}")
                print(f"   優先度: {agent_info.get('priority', 'N/A')}")
                print(f"   機能: {len(agent_info.get('best_for', []))}個")
                print(f"   キーワード: {len(agent_info.get('keywords', []))}個")

                # 最初の3つのキーワードを表示
                keywords = agent_info.get('keywords', [])
                if keywords:
                    print(f"   キーワード例: {', '.join(keywords[:3])}")
        else:
            print("\n⚠️ エージェントが読み込まれませんでした")

        print("\n" + "=" * 60)
        print("テスト完了")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_supervisor_dynamic_load())
