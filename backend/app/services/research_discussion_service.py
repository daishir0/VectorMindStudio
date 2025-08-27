"""
研究ディスカッションAIサービス
Supervisor Agentとして5つのAIエージェントを統括
"""
from typing import Any, Dict, List, Optional, Tuple
import logging
import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.external.openai_client import openai_client

# AIエージェント群のインポート
from app.services.agents import (
    BaseAgent, AgentTask, AgentResult, AgentStatus,
    OutlineAgent, SummaryAgent, WriterAgent, 
    LogicValidatorAgent, ReferenceAgent
)

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """タスク優先度"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class TodoTask:
    """TODOタスク"""
    id: str
    description: str
    agent_name: str
    priority: TaskPriority
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Any] = None


class ResearchDiscussionService:
    """
    研究ディスカッションAIサービス
    
    実装パターン: Supervisor Pattern (Orchestrator + Supervisor)
    責務: ユーザーとの対話窓口、タスク統括、エージェント調整
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PaperRepository(session)
        
        # エージェント群初期化
        self.outline_agent = OutlineAgent(session)
        self.summary_agent = SummaryAgent()
        self.writer_agent = WriterAgent()
        self.logic_validator_agent = LogicValidatorAgent()
        self.reference_agent = ReferenceAgent()
        
        self.agents = {
            "outline": self.outline_agent,
            "summary": self.summary_agent,
            "writer": self.writer_agent,
            "logic_validator": self.logic_validator_agent,
            "reference": self.reference_agent
        }
        
        # エスケープハッチ設定
        self.max_conversation_turns = 50
        self.max_parallel_agents = 3
        self.conversation_timeout = 300  # 5分
    
    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str,
        paper_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ユーザーメッセージを処理（メインエントリポイント）
        
        Args:
            session_id: チャットセッションID
            user_message: ユーザーメッセージ
            user_id: ユーザーID
            paper_id: 論文ID（オプション）
            
        Returns:
            処理結果辞書
        """
        try:
            logger.info(f"研究ディスカッションAI: ユーザーメッセージ処理開始 (session: {session_id})")
            
            # メッセージをDBに保存
            await self.repository.create_chat_message(
                session_id=session_id,
                role="user",
                content=user_message
            )
            
            # ユーザー意図解析
            intent_analysis = await self._analyze_user_intent(user_message, paper_id)
            
            # TODOタスク生成
            todo_tasks = await self._generate_todo_tasks(intent_analysis, user_id, paper_id)
            
            # タスク実行（並列処理）
            task_results = await self._execute_tasks(todo_tasks)
            
            # レスポンス生成
            response = await self._generate_response(
                user_message, intent_analysis, todo_tasks, task_results
            )
            
            # レスポンスをDBに保存
            await self.repository.create_chat_message(
                session_id=session_id,
                role="assistant",
                content=response["message"],
                agent_name="ResearchDiscussionAI",
                todo_tasks=[task.to_dict() for task in todo_tasks],
                references=response.get("references", [])
            )
            
            return {
                "message": response["message"],
                "todo_tasks": [task.to_dict() for task in todo_tasks],
                "task_results": task_results,
                "intent_analysis": intent_analysis,
                "references": response.get("references", []),
                "suggestions": response.get("suggestions", []),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"メッセージ処理エラー: {e}")
            
            # エラーレスポンス
            error_response = "申し訳ございません。処理中にエラーが発生しました。もう一度お試しください。"
            await self.repository.create_chat_message(
                session_id=session_id,
                role="assistant",
                content=error_response,
                agent_name="ResearchDiscussionAI"
            )
            
            return {
                "message": error_response,
                "error": str(e),
                "success": False
            }
    
    async def _analyze_user_intent(self, message: str, paper_id: Optional[str] = None) -> Dict[str, Any]:
        """ユーザー意図を解析"""
        try:
            # 現在の論文コンテキスト取得
            paper_context = ""
            if paper_id:
                paper = await self.repository.get_paper_by_id(paper_id)
                if paper:
                    sections = await self.repository.get_sections_by_paper(paper_id)
                    paper_context = f"論文タイトル: {paper.title}\n"
                    paper_context += f"セクション数: {len(sections)}\n"
                    if sections:
                        paper_context += "セクション一覧: " + ", ".join([s.title for s in sections[:5]])
            
            # OpenAI APIで意図解析
            system_prompt = """あなたは研究論文執筆支援の専門家です。
ユーザーのメッセージから以下の情報を抽出・分析してください：

1. 主要な意図 (create_section, edit_content, check_structure, find_references, improve_writing など)
2. 対象セクション（もしあれば）
3. 具体的な要求内容
4. 緊急度 (high, medium, low)
5. 必要なエージェント (outline, summary, writer, logic_validator, reference)

分析結果をJSONフォーマットで返してください。"""
            
            user_prompt = f"""【ユーザーメッセージ】
{message}

【論文コンテキスト】
{paper_context}

上記を分析してください。"""
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            
            result = await openai_client.generate_text(

            
                prompt=full_prompt,

            
                model="gpt-4o-mini"

            
            )

            
            analysis_result = result.get("content", "")
            
            # JSONパース（エラーハンドリング付き）
            try:
                import json
                intent_data = json.loads(analysis_result)
            except json.JSONDecodeError:
                # フォールバック: 基本的な意図解析
                intent_data = self._fallback_intent_analysis(message)
            
            return intent_data
            
        except Exception as e:
            logger.warning(f"意図解析エラー: {e}")
            return self._fallback_intent_analysis(message)
    
    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """フォールバック意図解析（キーワードベース）"""
        message_lower = message.lower()
        
        intent = "general"
        urgency = "medium"
        required_agents = []
        
        # キーワードベースの簡易分析
        if any(keyword in message_lower for keyword in ["追加", "作成", "新しい", "セクション"]):
            intent = "create_section"
            required_agents = ["outline", "writer"]
        elif any(keyword in message_lower for keyword in ["編集", "修正", "改善", "リライト"]):
            intent = "edit_content"
            required_agents = ["writer", "summary"]
        elif any(keyword in message_lower for keyword in ["構造", "流れ", "論理", "一貫性"]):
            intent = "check_structure"
            required_agents = ["logic_validator", "outline"]
        elif any(keyword in message_lower for keyword in ["文献", "参考", "引用", "参照"]):
            intent = "find_references"
            required_agents = ["reference"]
        
        return {
            "main_intent": intent,
            "target_section": None,
            "specific_request": message,
            "urgency": urgency,
            "required_agents": required_agents
        }
    
    async def _generate_todo_tasks(
        self, 
        intent_analysis: Dict[str, Any], 
        user_id: str, 
        paper_id: Optional[str]
    ) -> List[TodoTask]:
        """意図分析結果からTODOタスクを生成"""
        tasks = []
        main_intent = intent_analysis.get("main_intent", "general")
        required_agents = intent_analysis.get("required_agents", [])
        urgency = intent_analysis.get("urgency", "medium")
        
        priority = TaskPriority.HIGH if urgency == "high" else TaskPriority.MEDIUM
        
        # 意図に応じたタスク生成
        if main_intent == "create_section":
            tasks.append(TodoTask(
                id=str(uuid.uuid4()),
                description="新しいセクションを作成",
                agent_name="outline",
                priority=priority,
                parameters={
                    "task_type": "create_section",
                    "paper_id": paper_id,
                    "title": intent_analysis.get("specific_request", "新しいセクション"),
                    "user_id": user_id
                }
            ))
            
            if len(required_agents) > 1:
                tasks.append(TodoTask(
                    id=str(uuid.uuid4()),
                    description="セクション内容の初稿を生成",
                    agent_name="writer",
                    priority=priority,
                    parameters={
                        "task_type": "generate_draft",
                        "section_info": {"title": intent_analysis.get("specific_request", "新しいセクション")},
                        "paper_context": {"paper_title": "論文タイトル"},
                        "requirements": "学術的で論理的な内容を作成"
                    }
                ))
        
        elif main_intent == "edit_content":
            if "writer" in required_agents:
                tasks.append(TodoTask(
                    id=str(uuid.uuid4()),
                    description="コンテンツを改善",
                    agent_name="writer",
                    priority=priority,
                    parameters={
                        "task_type": "improve_style",
                        "content": intent_analysis.get("specific_request", ""),
                        "target_style": "academic"
                    }
                ))
        
        elif main_intent == "check_structure":
            tasks.append(TodoTask(
                id=str(uuid.uuid4()),
                description="論理構造を検証",
                agent_name="logic_validator",
                priority=priority,
                parameters={
                    "task_type": "validate_logic_flow",
                    "paper_outline": [],  # 実際には論文アウトラインを取得
                    "paper_type": "research"
                }
            ))
        
        elif main_intent == "find_references":
            tasks.append(TodoTask(
                id=str(uuid.uuid4()),
                description="関連文献を検索",
                agent_name="reference",
                priority=priority,
                parameters={
                    "task_type": "search_references",
                    "user_id": user_id,
                    "query": intent_analysis.get("specific_request", ""),
                    "limit": 5
                }
            ))
        
        # デフォルトタスク（意図が不明な場合）
        if not tasks:
            tasks.append(TodoTask(
                id=str(uuid.uuid4()),
                description="一般的な質問に回答",
                agent_name="writer",
                priority=TaskPriority.LOW,
                parameters={
                    "task_type": "generate_content",
                    "title": "回答",
                    "requirements": intent_analysis.get("specific_request", ""),
                    "target_length": 300
                }
            ))
        
        return tasks
    
    async def _execute_tasks(self, todo_tasks: List[TodoTask]) -> Dict[str, Any]:
        """TODOタスクを並列実行"""
        task_results = {}
        
        # 並列実行制限（エスケープハッチ）
        semaphore = asyncio.Semaphore(self.max_parallel_agents)
        
        async def execute_single_task(todo_task: TodoTask) -> Tuple[str, AgentResult]:
            async with semaphore:
                try:
                    todo_task.status = "in_progress"
                    agent = self.agents.get(todo_task.agent_name)
                    
                    if not agent:
                        raise ValueError(f"Unknown agent: {todo_task.agent_name}")
                    
                    # エージェントタスクを作成
                    agent_task = agent.create_task(
                        task_type=todo_task.parameters.get("task_type", "general"),
                        parameters=todo_task.parameters,
                        priority=todo_task.priority.value,
                        timeout=30
                    )
                    
                    # タスク実行
                    result = await agent.execute_task(agent_task)
                    
                    if result.status == AgentStatus.COMPLETED:
                        todo_task.status = "completed"
                        todo_task.result = result.result
                    else:
                        todo_task.status = "failed"
                        todo_task.result = {"error": result.error_message}
                    
                    return todo_task.id, result
                    
                except Exception as e:
                    logger.error(f"タスク実行エラー ({todo_task.id}): {e}")
                    todo_task.status = "failed"
                    todo_task.result = {"error": str(e)}
                    
                    # エラー結果を返す
                    return todo_task.id, AgentResult(
                        agent_name=todo_task.agent_name,
                        status=AgentStatus.FAILED,
                        result=None,
                        execution_time=0.0,
                        error_message=str(e)
                    )
        
        # 全タスクを並列実行
        if todo_tasks:
            try:
                task_coroutines = [execute_single_task(task) for task in todo_tasks]
                results = await asyncio.wait_for(
                    asyncio.gather(*task_coroutines, return_exceptions=True),
                    timeout=self.conversation_timeout
                )
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"タスク実行中の例外: {result}")
                    else:
                        task_id, agent_result = result
                        task_results[task_id] = agent_result
                        
            except asyncio.TimeoutError:
                logger.error(f"タスク実行タイムアウト ({self.conversation_timeout}秒)")
                # タイムアウト時は部分的な結果を返す
                for task in todo_tasks:
                    if task.status == "in_progress":
                        task.status = "failed"
                        task.result = {"error": "タイムアウト"}
        
        return task_results
    
    async def _generate_response(
        self,
        user_message: str,
        intent_analysis: Dict[str, Any],
        todo_tasks: List[TodoTask],
        task_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """レスポンスを生成"""
        try:
            # タスク実行結果のサマリー
            completed_tasks = [task for task in todo_tasks if task.status == "completed"]
            failed_tasks = [task for task in todo_tasks if task.status == "failed"]
            
            # 成功したタスクの結果を整理
            successful_results = []
            references = []
            
            for task in completed_tasks:
                if task.result:
                    successful_results.append({
                        "agent": task.agent_name,
                        "description": task.description,
                        "result": task.result
                    })
                    
                    # 参考文献があれば収集
                    if isinstance(task.result, dict) and "references" in task.result:
                        references.extend(task.result["references"])
            
            # レスポンステキスト生成
            response_parts = []
            
            # 処理状況報告
            if completed_tasks:
                response_parts.append(f"✅ {len(completed_tasks)}件のタスクを完了しました！")
                
                # 各エージェントの結果を要約
                for result in successful_results:
                    agent_name_jp = self._get_agent_name_jp(result["agent"])
                    response_parts.append(f"\n🔸 {agent_name_jp}: {result['description']}")
                    
                    # 簡潔な結果サマリー
                    result_summary = self._summarize_agent_result(result["result"])
                    if result_summary:
                        response_parts.append(f"   → {result_summary}")
            
            if failed_tasks:
                response_parts.append(f"\n⚠️ {len(failed_tasks)}件のタスクでエラーが発生しました。")
            
            # 次のアクション提案
            suggestions = self._generate_next_action_suggestions(
                intent_analysis, completed_tasks, failed_tasks
            )
            
            main_message = "".join(response_parts)
            if not main_message:
                main_message = "ご質問ありがとうございます。どのようなサポートが必要でしょうか？"
            
            return {
                "message": main_message,
                "references": references,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"レスポンス生成エラー: {e}")
            return {
                "message": "処理を完了しましたが、レスポンス生成中にエラーが発生しました。",
                "references": [],
                "suggestions": []
            }
    
    def _get_agent_name_jp(self, agent_name: str) -> str:
        """エージェント名を日本語に変換"""
        name_map = {
            "outline": "アウトライン管理",
            "summary": "要約生成",
            "writer": "ライティング",
            "logic_validator": "論理構造検証",
            "reference": "文献検索"
        }
        return name_map.get(agent_name, agent_name)
    
    def _summarize_agent_result(self, result: Any) -> str:
        """エージェント結果を要約"""
        if not isinstance(result, dict):
            return ""
        
        # アウトライン管理
        if "section" in result and "action" in result:
            if result["action"] == "create_section":
                return f"新しいセクション「{result['section'].get('title', '')}」を作成"
        
        # 要約生成
        if "summary" in result and "character_count" in result:
            return f"要約を生成（{result['character_count']}文字）"
        
        # ライティング
        if "content" in result and "word_count" in result:
            return f"コンテンツを生成（{result['word_count']}語）"
        
        # 論理構造検証
        if "issues" in result and "validation_score" in result:
            issue_count = len(result["issues"])
            score = result["validation_score"]
            return f"構造検証完了（スコア: {score:.1f}, 課題: {issue_count}件）"
        
        # 文献検索
        if "search_results" in result:
            result_count = len(result["search_results"])
            return f"{result_count}件の関連文献を発見"
        
        return "処理完了"
    
    def _generate_next_action_suggestions(
        self,
        intent_analysis: Dict[str, Any],
        completed_tasks: List[TodoTask],
        failed_tasks: List[TodoTask]
    ) -> List[str]:
        """次のアクション提案を生成"""
        suggestions = []
        
        # 失敗したタスクがある場合
        if failed_tasks:
            suggestions.append("エラーが発生したタスクを再実行してみてください")
        
        # 成功したタスクに基づく提案
        for task in completed_tasks:
            if task.agent_name == "outline" and task.status == "completed":
                suggestions.append("作成したセクションに内容を追加してみましょう")
            elif task.agent_name == "writer" and task.status == "completed":
                suggestions.append("生成したコンテンツの論理構造をチェックしてみませんか？")
            elif task.agent_name == "reference" and task.status == "completed":
                suggestions.append("見つかった文献を論文に引用してみましょう")
        
        # デフォルト提案
        if not suggestions:
            suggestions.extend([
                "新しいセクションを追加する",
                "既存の内容を改善する",
                "関連文献を検索する",
                "論文の構造をチェックする"
            ])
        
        return suggestions[:3]  # 最大3件の提案


# TodoTaskのto_dictメソッド追加用の拡張
def _todo_task_to_dict(self) -> Dict[str, Any]:
    """TodoTaskを辞書形式に変換"""
    return {
        "id": self.id,
        "description": self.description,
        "agent_name": self.agent_name,
        "priority": self.priority.name,
        "status": self.status,
        "parameters": self.parameters,
        "result": self.result
    }

# TodoTaskクラスにto_dictメソッドを追加
TodoTask.to_dict = _todo_task_to_dict