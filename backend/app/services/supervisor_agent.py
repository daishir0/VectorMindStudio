"""
Supervisor Agent - 動的オーケストレーター

ユーザーの自然言語リクエストから動的にワークフローを構成し、
複数のエージェントを調整・監督する司令塔
"""
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from app.services.dynamic_agent_loader import DynamicAgentLoader
from app.infrastructure.repositories.agent_repository import AgentRepository
from .agents.base_agent import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class TaskStep:
    """タスクステップ"""
    step: int
    description: str
    agent_name: str
    task_type: str
    parameters: Dict[str, Any]
    input_from_step: Optional[int] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_to_user: bool = False


@dataclass
class ExecutionPlan:
    """実行計画"""
    intent_summary: str
    tasks: List[TaskStep]
    estimated_time: str


@dataclass
class StepResult:
    """ステップ実行結果"""
    step: int
    agent_name: str
    description: str
    result: Any
    status: str  # success, failed
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ExecutionResult:
    """実行結果"""
    plan: ExecutionPlan
    step_results: List[StepResult]
    context: Dict[str, Any]
    success: bool
    total_time: float = 0.0


class SupervisorAgent:
    """
    スーパーバイザーエージェント

    ユーザーの自然言語リクエストから動的にワークフローを構成し、
    複数のエージェントを調整・監督する司令塔
    """

    def __init__(
        self,
        agent_loader: DynamicAgentLoader,
        agent_repository: AgentRepository,
        llm_client=None,  # 簡略化のため、今回はLLMを使わず手動計画
        session=None  # データベースセッション
    ):
        self.agent_loader = agent_loader
        self.agent_repository = agent_repository
        self.llm_client = llm_client
        self.session = session
        self.chat_messages: List[str] = []  # チャット履歴

    def add_chat_message(self, role: str, message: str):
        """チャットメッセージを追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_messages.append(f"[{timestamp}] {role}: {message}")

    def get_chat_history(self) -> str:
        """チャット履歴を取得"""
        return "\n".join(self.chat_messages)

    async def _load_agent_instance(self, agent_name: str):
        """エージェントインスタンスを直接ロード (モック実装)"""
        # テスト用のモックエージェントを使用
        from app.services.mock_agents import (
            MockReferenceRetrievalAgent,
            MockSummaryAgent,
            MockWriterAgent,
            MockQualityAgent,
            MockAnalysisAgent,
            MockEditingAgent
        )

        if agent_name == "ReferenceRetrievalAgent":
            return MockReferenceRetrievalAgent()
        elif agent_name == "SummaryAgent":
            return MockSummaryAgent()
        elif agent_name == "WriterAgent":
            return MockWriterAgent(session=self.session)
        elif agent_name == "QualityAgent":
            return MockQualityAgent()
        elif agent_name == "AnalysisAgent":
            return MockAnalysisAgent()
        elif agent_name == "EditingAgent":
            return MockEditingAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

    async def create_plan_from_template(
        self,
        user_message: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        テンプレートから実行計画を作成

        簡略化のため、LLMを使わずに事前定義されたテンプレートを使用

        Args:
            user_message: ユーザーメッセージ
            template_name: テンプレート名
            context: コンテキスト

        Returns:
            ExecutionPlan: 実行計画
        """

        # テンプレート定義
        templates = {
            # ストーリー1: 資料検索→要約→執筆
            "search_summarize_write": ExecutionPlan(
                intent_summary="キーワードで資料を検索し、要約して、論文セクションを執筆する",
                tasks=[
                    TaskStep(
                        step=1,
                        description="キーワードで資料を検索",
                        agent_name="ReferenceRetrievalAgent",
                        task_type="search_references",
                        parameters={
                            "query": context.get("search_query", "AI agent"),
                            "user_id": context.get("user_id"),
                            "limit": 5
                        },
                        output_to_user=True
                    ),
                    TaskStep(
                        step=2,
                        description="検索結果を要約",
                        agent_name="SummaryAgent",
                        task_type="summarize_content",
                        parameters={
                            "max_words": 300
                        },
                        input_from_step=1,
                        input_mapping={"content": "search_summary"},
                        output_to_user=True
                    ),
                    TaskStep(
                        step=3,
                        description="論文セクションを執筆",
                        agent_name="WriterAgent",
                        task_type="write_section",
                        parameters={
                            "section_title": context.get("section_title", "関連研究"),
                            "paper_id": context.get("paper_id")
                        },
                        input_from_step=2,
                        input_mapping={"reference_summary": "summary"},
                        output_to_user=True
                    )
                ],
                estimated_time="約30秒"
            ),

            # ストーリー2: 資料検索→複数セクション執筆→品質チェック
            "multi_section_with_quality": ExecutionPlan(
                intent_summary="資料を検索し、複数セクションを執筆して品質チェックを行う",
                tasks=[
                    TaskStep(
                        step=1,
                        description="関連資料を検索",
                        agent_name="ReferenceRetrievalAgent",
                        task_type="search_references",
                        parameters={
                            "query": context.get("search_query", "machine learning"),
                            "user_id": context.get("user_id"),
                            "limit": 5
                        },
                        output_to_user=True
                    ),
                    TaskStep(
                        step=2,
                        description="「はじめに」セクションを執筆",
                        agent_name="WriterAgent",
                        task_type="write_section",
                        parameters={
                            "section_title": "はじめに",
                            "paper_id": context.get("paper_id")
                        },
                        input_from_step=1,
                        output_to_user=True
                    ),
                    TaskStep(
                        step=3,
                        description="「関連研究」セクションを執筆",
                        agent_name="WriterAgent",
                        task_type="write_section",
                        parameters={
                            "section_title": "関連研究",
                            "paper_id": context.get("paper_id")
                        },
                        input_from_step=1,
                        output_to_user=True
                    ),
                    TaskStep(
                        step=4,
                        description="論文全体の品質をチェック",
                        agent_name="QualityAgent",
                        task_type="evaluate_quality",
                        parameters={
                            "paper_id": context.get("paper_id")
                        },
                        output_to_user=True
                    )
                ],
                estimated_time="約45秒"
            ),

            # ストーリー3: 資料検索→分析→執筆→編集→品質チェック
            "full_pipeline": ExecutionPlan(
                intent_summary="資料を検索・分析し、執筆・編集して品質チェックまで行う",
                tasks=[
                    TaskStep(
                        step=1,
                        description="研究資料を検索",
                        agent_name="ReferenceRetrievalAgent",
                        task_type="search_references",
                        parameters={
                            "query": context.get("search_query", "deep learning"),
                            "user_id": context.get("user_id"),
                            "limit": 5
                        },
                        output_to_user=True
                    ),
                    TaskStep(
                        step=2,
                        description="検索結果を分析",
                        agent_name="AnalysisAgent",
                        task_type="analyze_content",
                        parameters={
                            "analysis_type": "trend_analysis"
                        },
                        input_from_step=1,
                        output_to_user=True
                    ),
                    TaskStep(
                        step=3,
                        description="分析結果をもとに執筆",
                        agent_name="WriterAgent",
                        task_type="write_section",
                        parameters={
                            "section_title": context.get("section_title", "提案手法"),
                            "paper_id": context.get("paper_id")
                        },
                        input_from_step=2,
                        output_to_user=True
                    ),
                    TaskStep(
                        step=4,
                        description="執筆内容を編集・改善",
                        agent_name="EditingAgent",
                        task_type="edit_content",
                        parameters={
                            "edit_instructions": "文章の流れを改善し、専門性を高める"
                        },
                        input_from_step=3,
                        output_to_user=True
                    ),
                    TaskStep(
                        step=5,
                        description="最終品質チェック",
                        agent_name="QualityAgent",
                        task_type="evaluate_quality",
                        parameters={
                            "paper_id": context.get("paper_id")
                        },
                        output_to_user=True
                    )
                ],
                estimated_time="約60秒"
            )
        }

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")

        return templates[template_name]

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        report_progress: bool = True
    ) -> ExecutionResult:
        """
        実行計画を実行

        Args:
            plan: 実行計画
            report_progress: 進捗を報告するか

        Returns:
            ExecutionResult: 実行結果
        """

        start_time = datetime.now()
        context = {}
        step_results = []

        logger.info(f"[SupervisorAgent] 実行計画を開始: {plan.intent_summary}")

        if report_progress:
            self.add_chat_message("Supervisor", f"📋 実行計画: {plan.intent_summary}")
            self.add_chat_message("Supervisor", f"⏱ 予想実行時間: {plan.estimated_time}")
            self.add_chat_message("Supervisor", "")

        for task in plan.tasks:
            step_start = datetime.now()

            # 進捗報告
            if report_progress:
                msg = f"📍 [ステップ {task.step}] {task.description} を実行中..."
                logger.info(f"[SupervisorAgent] {msg}")
                self.add_chat_message("Supervisor", msg)

            try:
                # エージェント取得 (直接実装クラスをインポート)
                agent = await self._load_agent_instance(task.agent_name)

                # 前ステップの出力を入力にマッピング
                task_params = task.parameters.copy()
                if task.input_from_step and task.input_mapping:
                    prev_result = context.get(f"step_{task.input_from_step}_result")
                    if prev_result:
                        for param_key, context_key in task.input_mapping.items():
                            if context_key in prev_result:
                                task_params[param_key] = prev_result[context_key]

                # エージェント実行
                import uuid
                agent_task = AgentTask(
                    id=str(uuid.uuid4()),
                    task_type=task.task_type,
                    parameters=task_params
                )

                result = await agent.execute(agent_task)

                step_time = (datetime.now() - step_start).total_seconds()

                # 結果を保存
                step_result = StepResult(
                    step=task.step,
                    agent_name=task.agent_name,
                    description=task.description,
                    result=result,
                    status="success",
                    execution_time=step_time
                )
                step_results.append(step_result)
                context[f"step_{task.step}_result"] = result

                # 結果報告
                if report_progress:
                    success_msg = f"✅ [ステップ {task.step}] 完了 ({step_time:.1f}秒)"
                    logger.info(f"[SupervisorAgent] {success_msg}")
                    self.add_chat_message("Supervisor", success_msg)

                    if task.output_to_user and result:
                        # 結果の概要を表示
                        result_summary = self._format_result_summary(result, task.agent_name)
                        if result_summary:
                            self.add_chat_message("Supervisor", f"   {result_summary}")

                    self.add_chat_message("Supervisor", "")

            except Exception as e:
                # エラーハンドリング
                step_time = (datetime.now() - step_start).total_seconds()

                error_result = StepResult(
                    step=task.step,
                    agent_name=task.agent_name,
                    description=task.description,
                    result=None,
                    status="failed",
                    error=str(e),
                    execution_time=step_time
                )
                step_results.append(error_result)

                error_msg = f"❌ [ステップ {task.step}] エラー: {str(e)}"
                logger.error(f"[SupervisorAgent] {error_msg}")

                if report_progress:
                    self.add_chat_message("Supervisor", error_msg)
                    self.add_chat_message("Supervisor", "")

                # エラー時は実行を中断
                break

        total_time = (datetime.now() - start_time).total_seconds()

        result = ExecutionResult(
            plan=plan,
            step_results=step_results,
            context=context,
            success=all(r.status == "success" for r in step_results),
            total_time=total_time
        )

        # 最終報告
        if report_progress:
            self._report_final_result(result)

        return result

    def _format_result_summary(self, result: Any, agent_name: str) -> str:
        """結果の概要をフォーマット"""
        try:
            if isinstance(result, dict):
                if agent_name == "ReferenceRetrievalAgent":
                    chunks_found = result.get("chunks_found", 0)
                    files_found = result.get("files_found", 0)
                    return f"→ {chunks_found}件のチャンク、{files_found}件のファイルを発見"

                elif agent_name == "SummaryAgent":
                    summary = result.get("summary", "")
                    return f"→ 要約完成 ({len(summary)}文字)"

                elif agent_name == "WriterAgent":
                    content = result.get("content", "")
                    return f"→ 執筆完了 ({len(content)}文字)"

                elif agent_name == "QualityAgent":
                    score = result.get("quality_score", 0)
                    return f"→ 品質スコア: {score}/10"

                elif agent_name == "AnalysisAgent":
                    return "→ 分析完了"

                elif agent_name == "EditingAgent":
                    return "→ 編集完了"

            return ""

        except Exception:
            return ""

    def _report_final_result(self, execution_result: ExecutionResult):
        """最終結果を報告"""
        self.add_chat_message("Supervisor", "=" * 60)

        if execution_result.success:
            self.add_chat_message("Supervisor", f"🎉 すべてのタスクが完了しました！ (総実行時間: {execution_result.total_time:.1f}秒)")
        else:
            self.add_chat_message("Supervisor", "⚠️ タスク実行中にエラーが発生しました")

        self.add_chat_message("Supervisor", "")
        self.add_chat_message("Supervisor", "【実行結果】")

        for step_result in execution_result.step_results:
            if step_result.status == "success":
                self.add_chat_message("Supervisor", f"✅ {step_result.description}")
            else:
                self.add_chat_message("Supervisor", f"❌ {step_result.description}: {step_result.error}")

        self.add_chat_message("Supervisor", "=" * 60)

    async def process_user_request(
        self,
        user_message: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """
        ユーザーリクエストを処理

        Args:
            user_message: ユーザーメッセージ
            template_name: 使用するテンプレート名
            context: コンテキスト

        Returns:
            ExecutionResult: 実行結果
        """

        # ユーザーメッセージを記録
        self.add_chat_message("User", user_message)
        self.add_chat_message("", "")

        # 実行計画を作成
        plan = await self.create_plan_from_template(user_message, template_name, context)

        # 計画を実行
        result = await self.execute_plan(plan, report_progress=True)

        return result
