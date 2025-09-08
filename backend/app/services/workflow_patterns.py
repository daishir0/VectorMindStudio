"""
Workflow Patterns実装
AAIDC文書のWorkflow Patternsに基づく実装
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid

from app.services.agent_responsibilities import TaskType, AgentResponsibilities, TaskExecutionError

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """ワークフロータイプ"""
    CHAIN = "chain"                     # 🔗 順次実行
    PARALLEL = "parallel"               # ☰ 並列実行  
    GENERATOR_EVALUATOR = "gen_eval"    # 🎭 生成→評価ループ
    ROUTER = "router"                   # 🔀 条件分岐
    ORCHESTRATOR = "orchestrator"       # 🎯 動的調整


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed" 
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowTask:
    """ワークフロータスク（TodoTaskの強化版）"""
    id: str
    agent_name: str
    task_type: TaskType
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    priority: int = 1  # 1=highest, 5=lowest
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass 
class WorkflowResult:
    """ワークフロー実行結果"""
    workflow_id: str
    status: TaskStatus
    tasks: List[WorkflowTask]
    execution_time: float
    success_count: int
    failure_count: int
    error_summary: Optional[str] = None


class ChainWorkflow:
    """🔗 Chain Pattern実装"""
    
    def __init__(self, tasks: List[WorkflowTask], max_retries: int = 2):
        self.tasks = tasks
        self.max_retries = max_retries
        self.workflow_id = str(uuid.uuid4())
    
    async def execute(self, executor_func) -> WorkflowResult:
        """チェーン実行 - タスクを順次実行"""
        start_time = time.time()
        results = {}
        success_count = 0
        failure_count = 0
        
        logger.info(f"Chain workflow {self.workflow_id} started with {len(self.tasks)} tasks")
        
        for task in self.tasks:
            try:
                # 依存関係チェック
                if not self._check_dependencies(task, results):
                    task.status = TaskStatus.FAILED
                    task.error_message = f"Dependencies not satisfied: {task.dependencies}"
                    failure_count += 1
                    continue
                
                # タスク実行（リトライ付き）
                task.status = TaskStatus.IN_PROGRESS
                task_result = await self._execute_task_with_retry(task, executor_func, results)
                
                if task_result:
                    task.status = TaskStatus.COMPLETED
                    task.result = task_result
                    results[task.agent_name] = task_result
                    success_count += 1
                    logger.info(f"Task {task.id} ({task.agent_name}:{task.task_type.value}) completed")
                else:
                    task.status = TaskStatus.FAILED
                    failure_count += 1
                    logger.error(f"Task {task.id} failed after retries")
                    
                    # Critical taskが失敗した場合はチェーン停止
                    if task.priority == 1:
                        logger.error(f"Critical task failed, stopping chain")
                        break
                        
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                failure_count += 1
                logger.error(f"Task {task.id} failed with error: {e}")
                
                if task.priority == 1:
                    break
        
        execution_time = time.time() - start_time
        workflow_status = TaskStatus.COMPLETED if failure_count == 0 else TaskStatus.FAILED
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=workflow_status,
            tasks=self.tasks,
            execution_time=execution_time,
            success_count=success_count,
            failure_count=failure_count
        )
    
    def _check_dependencies(self, task: WorkflowTask, completed_results: Dict[str, Any]) -> bool:
        """依存関係チェック"""
        if not task.dependencies:
            return True
        return all(dep in completed_results for dep in task.dependencies)
    
    async def _execute_task_with_retry(
        self, 
        task: WorkflowTask, 
        executor_func, 
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """リトライ付きタスク実行"""
        for attempt in range(self.max_retries + 1):
            try:
                task.retry_count = attempt
                
                # コンテキストを追加
                enhanced_parameters = {
                    **task.parameters,
                    "context": context,
                    "attempt": attempt
                }
                
                start_time = time.time()
                result = await asyncio.wait_for(
                    executor_func(task.agent_name, task.task_type, enhanced_parameters),
                    timeout=task.timeout_seconds
                )
                task.execution_time = time.time() - start_time
                
                if result and self._validate_result(task, result):
                    return result
                    
            except asyncio.TimeoutError:
                logger.warning(f"Task {task.id} timed out (attempt {attempt+1})")
                task.error_message = f"Timeout after {task.timeout_seconds}s"
            except Exception as e:
                logger.warning(f"Task {task.id} failed (attempt {attempt+1}): {e}")
                task.error_message = str(e)
        
        return None
    
    def _validate_result(self, task: WorkflowTask, result: Any) -> bool:
        """結果の妥当性検証"""
        if not result:
            return False
            
        # タスクタイプ別の結果検証
        if task.task_type == TaskType.CREATE_SECTION:
            return isinstance(result, dict) and "section_id" in result
        elif task.task_type == TaskType.GENERATE_DRAFT:
            return isinstance(result, dict) and "draft_content" in result
        
        return True


class GeneratorEvaluatorLoop:
    """🎭 Generator-Evaluator Loop Pattern実装"""
    
    def __init__(
        self, 
        generator_task: WorkflowTask,
        evaluator_task: WorkflowTask,
        max_iterations: int = 3,
        quality_threshold: float = 0.8
    ):
        self.generator_task = generator_task
        self.evaluator_task = evaluator_task
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.workflow_id = str(uuid.uuid4())
    
    async def execute(self, executor_func) -> WorkflowResult:
        """生成→評価→改善ループの実行"""
        start_time = time.time()
        iteration_results = []
        
        logger.info(f"Generator-Evaluator loop {self.workflow_id} started")
        
        for iteration in range(self.max_iterations):
            logger.info(f"Starting iteration {iteration + 1}")
            
            # 生成フェーズ
            self.generator_task.status = TaskStatus.IN_PROGRESS
            self.generator_task.parameters["iteration"] = iteration
            
            if iteration > 0:
                # 前回の評価結果を次の生成に活用
                if iteration_results:
                    last_evaluation = iteration_results[-1].get("evaluation")
                    if last_evaluation:
                        self.generator_task.parameters["feedback"] = last_evaluation.get("feedback")
                        self.generator_task.parameters["previous_attempt"] = iteration_results[-1].get("generation")
            
            generation_result = await executor_func(
                self.generator_task.agent_name,
                self.generator_task.task_type, 
                self.generator_task.parameters
            )
            
            if not generation_result:
                self.generator_task.status = TaskStatus.FAILED
                break
            
            self.generator_task.result = generation_result
            self.generator_task.status = TaskStatus.COMPLETED
            
            # 評価フェーズ
            self.evaluator_task.status = TaskStatus.IN_PROGRESS
            self.evaluator_task.parameters["content"] = generation_result
            self.evaluator_task.parameters["iteration"] = iteration
            
            evaluation_result = await executor_func(
                self.evaluator_task.agent_name,
                self.evaluator_task.task_type,
                self.evaluator_task.parameters
            )
            
            if not evaluation_result:
                self.evaluator_task.status = TaskStatus.FAILED
                break
            
            self.evaluator_task.result = evaluation_result
            self.evaluator_task.status = TaskStatus.COMPLETED
            
            iteration_results.append({
                "generation": generation_result,
                "evaluation": evaluation_result,
                "iteration": iteration
            })
            
            # 品質チェック
            quality_score = evaluation_result.get("score", 0.0)
            logger.info(f"Iteration {iteration + 1} quality score: {quality_score}")
            
            if quality_score >= self.quality_threshold:
                logger.info(f"Quality threshold reached at iteration {iteration + 1}")
                break
        
        execution_time = time.time() - start_time
        success = len(iteration_results) > 0 and iteration_results[-1]["evaluation"].get("score", 0) >= self.quality_threshold
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
            tasks=[self.generator_task, self.evaluator_task],
            execution_time=execution_time,
            success_count=2 if success else 0,
            failure_count=0 if success else 2
        )


class ParallelWorkflow:
    """☰ Parallel Pattern実装"""
    
    def __init__(self, tasks: List[WorkflowTask], max_concurrent: int = 3):
        self.tasks = tasks
        self.max_concurrent = max_concurrent
        self.workflow_id = str(uuid.uuid4())
    
    async def execute(self, executor_func) -> WorkflowResult:
        """並列実行"""
        start_time = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def execute_single_task(task: WorkflowTask):
            async with semaphore:
                try:
                    task.status = TaskStatus.IN_PROGRESS
                    result = await executor_func(task.agent_name, task.task_type, task.parameters)
                    if result:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                    else:
                        task.status = TaskStatus.FAILED
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                    logger.error(f"Parallel task {task.id} failed: {e}")
        
        # 全タスクを並列実行
        await asyncio.gather(*[execute_single_task(task) for task in self.tasks])
        
        execution_time = time.time() - start_time
        success_count = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        failure_count = len(self.tasks) - success_count
        
        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=TaskStatus.COMPLETED if failure_count == 0 else TaskStatus.FAILED,
            tasks=self.tasks,
            execution_time=execution_time,
            success_count=success_count,
            failure_count=failure_count
        )


class WorkflowManager:
    """ワークフロー管理マネージャー"""
    
    def __init__(self):
        self.active_workflows = {}
        self.workflow_history = []
    
    def create_paper_section_chain(
        self, 
        paper_id: str, 
        section_title: str, 
        requirements: str,
        user_id: str
    ) -> ChainWorkflow:
        """論文セクション作成用のチェーンワークフローを作成"""
        
        # Step 1: OutlineAgent - セクション構造作成
        outline_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="outline",
            task_type=TaskType.CREATE_SECTION,
            parameters={
                "paper_id": paper_id,
                "section_title": section_title,
                "user_id": user_id
            },
            priority=1,  # Critical task
            timeout_seconds=15
        )
        
        # Step 2: WriterAgent - コンテンツ生成
        writer_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="writer", 
            task_type=TaskType.GENERATE_DRAFT,
            parameters={
                "section_title": section_title,
                "requirements": requirements,
                "paper_id": paper_id
            },
            dependencies=["outline"],  # OutlineAgent完了後に実行
            priority=1,
            timeout_seconds=45
        )
        
        # Step 3: SummaryAgent - 要約作成
        summary_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="summary",
            task_type=TaskType.CREATE_SUMMARY,
            parameters={
                "summary_type": "section_summary",
                "focus_areas": ["key_points", "methodology", "conclusions"]
            },
            dependencies=["writer"],
            priority=2,
            timeout_seconds=20
        )
        
        return ChainWorkflow([outline_task, writer_task, summary_task])
    
    def create_quality_improvement_loop(
        self,
        section_id: str,
        content: str,
        improvement_criteria: Dict[str, Any]
    ) -> GeneratorEvaluatorLoop:
        """品質改善ループを作成"""
        
        generator_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="writer",
            task_type=TaskType.IMPROVE_STYLE,
            parameters={
                "section_id": section_id,
                "content": content,
                "improvement_criteria": improvement_criteria
            }
        )
        
        evaluator_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="logic_validator",
            task_type=TaskType.VALIDATE_STRUCTURE,
            parameters={
                "evaluation_criteria": improvement_criteria,
                "quality_metrics": ["clarity", "coherence", "academic_style"]
            }
        )
        
        return GeneratorEvaluatorLoop(
            generator_task=generator_task,
            evaluator_task=evaluator_task,
            max_iterations=3,
            quality_threshold=0.8
        )
    
    async def execute_workflow(
        self, 
        workflow: Union[ChainWorkflow, GeneratorEvaluatorLoop, ParallelWorkflow],
        executor_func
    ) -> WorkflowResult:
        """ワークフロー実行"""
        self.active_workflows[workflow.workflow_id] = workflow
        
        try:
            result = await workflow.execute(executor_func)
            self.workflow_history.append(result)
            return result
        finally:
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]