"""
モックエージェント - テスト用の簡易実装
"""
from typing import Any, Dict
import uuid
from app.infrastructure.repositories.paper_repository import PaperRepository


class MockReferenceRetrievalAgent:
    """参考資料検索エージェント (モック)"""

    name = "ReferenceRetrievalAgent"

    async def execute(self, task):
        """モック実行"""
        return {
            "chunks_found": 5,
            "files_found": 3,
            "search_summary": "AI agent に関連する資料を5件発見しました。主にエージェントアーキテクチャと実装手法に関する研究です。",
            "chunk_results": [
                {"content": "AIエージェントは自律的に目標を達成するシステムです...", "filename": "ai_agent_basics.txt", "chunk_number": 1, "relevance_score": 0.92},
                {"content": "マルチエージェントシステムでは複数のエージェントが協調動作します...", "filename": "multi_agent.txt", "chunk_number": 2, "relevance_score": 0.88},
            ],
            "file_metadata": [
                {"filename": "ai_agent_basics.txt", "tags": ["AI", "agent"]},
                {"filename": "multi_agent.txt", "tags": ["multi-agent", "coordination"]}
            ],
            "success": True
        }


class MockSummaryAgent:
    """要約エージェント (モック)"""

    name = "SummaryAgent"

    async def execute(self, task):
        """モック実行"""
        return {
            "summary": "AIエージェントは自律的に目標を達成するシステムであり、環境を認識し、意思決定を行い、行動を実行する能力を持ちます。マルチエージェントシステムでは複数のエージェントが協調・競合しながら問題解決を行います。",
            "summary_length": 120,
            "success": True
        }


class MockWriterAgent:
    """ライティングエージェント (モック)"""

    name = "WriterAgent"

    def __init__(self, session=None):
        self.session = session
        self.paper_repo = PaperRepository(session) if session else None

    async def execute(self, task):
        """モック実行 - 実際にDBに保存"""
        params = task.parameters
        section_title = params.get("section_title", "セクション")
        paper_id = params.get("paper_id")

        # 簡易的な内容生成
        content = f"""
{section_title}に関する内容をここに記載します。

本研究では、AIエージェントシステムの設計と実装について検討します。
近年、AIエージェント技術は急速に発展しており、様々な分野での応用が期待されています。

本セクションでは、以下の点について述べます:
1. AIエージェントの基本概念
2. エージェントアーキテクチャの設計
3. 実装上の課題と解決策

これらの検討を通じて、効果的なAIエージェントシステムの構築手法を提案します。
""".strip()

        # 実際にデータベースに保存
        section_id = None
        if self.paper_repo and paper_id:
            # 既存のセクションをチェック
            existing_sections = await self.paper_repo.get_sections_by_paper(paper_id)
            section_number = len(existing_sections) + 1

            # セクション作成
            section = await self.paper_repo.create_section(
                paper_id=paper_id,
                position=section_number,
                section_number=str(section_number),
                title=section_title,
                content=content,
                summary=f"{section_title}の要約です。"
            )
            section_id = section.id

        return {
            "content": content,
            "section_id": section_id or str(uuid.uuid4()),
            "word_count": len(content),
            "success": True
        }


class MockQualityAgent:
    """品質評価エージェント (モック)"""

    name = "QualityAgent"

    async def execute(self, task):
        """モック実行"""
        return {
            "quality_score": 8.5,
            "issues": ["セクション間の整合性を改善できます", "参考文献の追加を推奨します"],
            "strengths": ["論理構成が明確", "内容が具体的"],
            "overall_assessment": "良好な品質レベルです。いくつかの改善を行うことでさらに向上します。",
            "success": True
        }


class MockAnalysisAgent:
    """分析エージェント (モック)"""

    name = "AnalysisAgent"

    async def execute(self, task):
        """モック実行"""
        return {
            "analysis_result": "深層学習に関する最新のトレンドを分析しました。Transformer アーキテクチャとAttentionメカニズムが主流となっています。",
            "key_findings": [
                "Transformer モデルの普及",
                "自己注意機構の重要性",
                "大規模事前学習の効果"
            ],
            "success": True
        }


class MockEditingAgent:
    """編集エージェント (モック)"""

    name = "EditingAgent"

    async def execute(self, task):
        """モック実行"""
        return {
            "edited_content": "編集後の内容: 文章の流れを改善し、専門性を高めました。各段落の接続詞を調整し、論理展開を明確にしました。",
            "changes_made": ["接続詞の調整", "専門用語の統一", "段落構成の改善"],
            "success": True
        }
