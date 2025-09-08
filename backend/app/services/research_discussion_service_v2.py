"""
研究ディスカッションAIサービス - AAIDC準拠版
Supervisor Pattern + Chain Pattern + Generator-Evaluator Loop Pattern実装

このファイルは paper_sections保存問題を根本解決し、
AAIDC文書のベストプラクティスに準拠した設計に変更します。
"""
from typing import Any, Dict, List, Optional, Union
import logging
import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum
import json
import time

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.external.openai_client import openai_client

# AIエージェント群のインポート
from app.services.agents import (
    BaseAgent, AgentTask, AgentResult, AgentStatus,
    OutlineAgent, SummaryAgent, WriterAgent, 
    LogicValidatorAgent
)

# 新しいパターンベース設計のインポート
from app.services.agent_responsibilities import (
    TaskType, AgentResponsibilities, TaskExecutionError, AgentResponsibilityViolation
)
from app.services.workflow_patterns import (
    WorkflowManager, WorkflowType, WorkflowTask, WorkflowResult,
    ChainWorkflow, GeneratorEvaluatorLoop, ParallelWorkflow, TaskStatus
)

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """ユーザー意図タイプ"""
    CREATE_SECTION = "create_section"
    UPDATE_CONTENT = "update_content"
    IMPROVE_QUALITY = "improve_quality"
    VALIDATE_STRUCTURE = "validate_structure"
    SEARCH_REFERENCES = "search_references"
    ANALYZE_CONTENT = "analyze_content"
    GENERAL_DISCUSSION = "general_discussion"


class ResearchDiscussionServiceV2:
    """
    研究ディスカッションAIサービス - AAIDC準拠版
    
    実装パターン:
    - Supervisor Pattern: 複数エージェントの統括管理
    - Chain Pattern: 依存関係のあるタスクの順次実行
    - Generator-Evaluator Loop: 品質向上のフィードバックループ
    - Clear Boundaries: 責務分界の明確化
    - Complete Escape Hatch: 堅牢性の確保
    
    責務: ユーザーとの対話窓口、ワークフロー統括、エージェント調整
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PaperRepository(session)
        
        # エージェント群初期化
        self.outline_agent = OutlineAgent(session)
        self.summary_agent = SummaryAgent(session)
        self.writer_agent = WriterAgent()
        self.logic_validator_agent = LogicValidatorAgent()
        # ReferenceAgentは一時的に無効化（ChromaDB依存のため）
        
        self.agents = {
            "outline": self.outline_agent,
            "summary": self.summary_agent,
            "writer": self.writer_agent,
            "logic_validator": self.logic_validator_agent,
            # "reference": self.reference_agent  # 一時的に無効化
        }
        
        # ワークフローマネージャー
        self.workflow_manager = WorkflowManager()
        
        # エスケープハッチ設定（Complete Escape Hatch Pattern）
        self.max_conversation_turns = 50
        self.max_parallel_agents = 3
        self.conversation_timeout = 300  # 5分
        self.quality_threshold = 0.75
        self.max_improvement_iterations = 3
    
    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str,
        paper_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ユーザーメッセージを処理（Supervisor Pattern + Workflow Patterns）
        
        フロー:
        1. 意図解析 (Orchestrator Pattern)
        2. ワークフロー選択と実行 (Chain/Generator-Evaluator/Parallel Pattern)
        3. 結果統合と応答生成 (Supervisor Pattern)
        4. データ永続化 (Clear Boundaries Pattern)
        
        Args:
            session_id: チャットセッションID
            user_message: ユーザーメッセージ
            user_id: ユーザーID
            paper_id: 論文ID（オプション）
            
        Returns:
            処理結果辞書
        """
        try:
            logger.info(f"[Supervisor] ユーザーメッセージ処理開始 (session: {session_id})")
            
            # Step 1: ユーザーメッセージをDBに保存
            await self.repository.create_chat_message(
                session_id=session_id,
                role="user",
                content=user_message
            )
            
            # Step 2: ユーザー意図解析（Orchestrator Pattern）
            intent_analysis = await self._analyze_user_intent(user_message, paper_id)
            logger.info(f"[Supervisor] 意図解析完了: {intent_analysis.get('main_intent')}")
            
            # Step 3: ワークフロー選択と実行（Pattern-based Execution）
            workflow_result = await self._execute_intent_workflow(
                intent_analysis, user_id, paper_id
            )
            
            # Step 4: データ永続化（Clear Boundaries Pattern）
            await self._persist_workflow_results(workflow_result, paper_id)
            
            # Step 5: 統合応答生成（Supervisor Pattern）
            response = await self._generate_integrated_response(
                user_message, intent_analysis, workflow_result
            )
            
            # Step 6: レスポンスをDBに保存
            await self.repository.create_chat_message(
                session_id=session_id,
                role="assistant",
                content=response["message"],
                agent_name="ResearchDiscussionAI",
                todo_tasks=self._convert_workflow_to_todos(workflow_result),
                references=response.get("references", [])
            )
            
            logger.info(f"[Supervisor] メッセージ処理完了: {workflow_result.success_count}成功, {workflow_result.failure_count}失敗")
            
            return {
                "message": response["message"],
                "workflow_result": self._serialize_workflow_result(workflow_result),
                "intent_analysis": intent_analysis,
                "references": response.get("references", []),
                "suggestions": response.get("suggestions", []),
                "success": workflow_result.status == TaskStatus.COMPLETED
            }
            
        except Exception as e:
            logger.error(f"[Supervisor] メッセージ処理エラー: {e}")
            
            # Complete Escape Hatch Pattern - 障害時の適切なハンドリング
            error_response = await self._generate_error_response(str(e), user_message)
            
            await self.repository.create_chat_message(
                session_id=session_id,
                role="assistant",
                content=error_response,
                agent_name="ResearchDiscussionAI"
            )
            
            return {
                "message": error_response,
                "error": str(e),
                "success": False,
                "fallback_used": True
            }
    
    async def _execute_intent_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        user_id: str, 
        paper_id: Optional[str]
    ) -> WorkflowResult:
        """意図に基づいてWorkflow Patternを選択・実行"""
        main_intent = intent_analysis.get("main_intent")
        
        try:
            if main_intent == "create_section":
                # Chain Pattern: セクション作成ワークフロー
                return await self._execute_create_section_workflow(
                    intent_analysis, user_id, paper_id
                )
            
            elif main_intent == "improve_quality":
                # Generator-Evaluator Loop Pattern: 品質向上ワークフロー
                return await self._execute_quality_improvement_workflow(
                    intent_analysis, paper_id
                )
            
            elif main_intent == "validate_structure":
                # Single Agent Pattern: 構造検証
                return await self._execute_validation_workflow(
                    intent_analysis, paper_id
                )
            
            elif main_intent == "search_references":
                # Single Agent Pattern: 文献検索
                return await self._execute_reference_search_workflow(
                    intent_analysis, user_id
                )
            
            else:
                # Fallback: General discussion workflow
                return await self._execute_general_discussion_workflow(
                    intent_analysis, user_id
                )
                
        except Exception as e:
            logger.error(f"[Workflow] ワークフロー実行エラー: {e}")
            # Complete Escape Hatch - フォールバック実行
            return await self._execute_fallback_workflow(intent_analysis, user_id)
    
    async def _execute_create_section_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        user_id: str, 
        paper_id: str
    ) -> WorkflowResult:
        """Chain Pattern: セクション作成ワークフロー（paper_sections保存問題の根本解決）"""
        section_title = intent_analysis.get("extracted_title", "新しいセクション")
        requirements = intent_analysis.get("specific_request", "")
        
        logger.info(f"[Chain] セクション作成ワークフロー開始: '{section_title}'")
        
        # Chain Workflowを作成（依存関係を明確に定義）
        chain_workflow = self.workflow_manager.create_paper_section_chain(
            paper_id=paper_id,
            section_title=section_title,
            requirements=requirements,
            user_id=user_id
        )
        
        # Chain実行（OutlineAgent → WriterAgent → SummaryAgent）
        return await self.workflow_manager.execute_workflow(
            chain_workflow, 
            self._execute_agent_task
        )
    
    async def _execute_quality_improvement_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        paper_id: str
    ) -> WorkflowResult:
        """Generator-Evaluator Loop Pattern: 品質向上ワークフロー"""
        target_section = intent_analysis.get("target_section")
        improvement_criteria = intent_analysis.get("improvement_criteria", {})
        
        if not target_section:
            # セクション特定が必要な場合のフォールバック
            sections = await self.repository.get_sections_by_paper(paper_id)
            if sections:
                target_section = sections[0].id  # 最初のセクションを対象
            else:
                raise TaskExecutionError("改善対象のセクションが見つかりません")
        
        logger.info(f"[Generator-Evaluator] 品質向上ループ開始: section {target_section}")
        
        # 現在のコンテンツを取得
        section = await self.repository.get_section_by_id(target_section)
        if not section:
            raise TaskExecutionError("対象セクションが存在しません")
        
        # Generator-Evaluator Loopを作成
        improvement_loop = self.workflow_manager.create_quality_improvement_loop(
            section_id=target_section,
            content=section.content,
            improvement_criteria=improvement_criteria
        )
        
        # Loop実行（Generate → Evaluate → Improve → Repeat）
        return await self.workflow_manager.execute_workflow(
            improvement_loop,
            self._execute_agent_task
        )
    
    async def _execute_validation_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        paper_id: str
    ) -> WorkflowResult:
        """Single Agent Pattern: 構造検証ワークフロー"""
        logger.info(f"[Validation] 構造検証ワークフロー開始")
        
        validation_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="logic_validator",
            task_type=TaskType.VALIDATE_STRUCTURE,
            parameters={
                "paper_id": paper_id,
                "validation_criteria": intent_analysis.get("validation_criteria", {})
            }
        )
        
        # 単一エージェント実行
        validation_task.status = TaskStatus.IN_PROGRESS
        result = await self._execute_agent_task(
            validation_task.agent_name,
            validation_task.task_type, 
            validation_task.parameters
        )
        
        if result:
            validation_task.status = TaskStatus.COMPLETED
            validation_task.result = result
        else:
            validation_task.status = TaskStatus.FAILED
        
        return WorkflowResult(
            workflow_id=str(uuid.uuid4()),
            status=validation_task.status,
            tasks=[validation_task],
            execution_time=validation_task.execution_time,
            success_count=1 if validation_task.status == TaskStatus.COMPLETED else 0,
            failure_count=1 if validation_task.status == TaskStatus.FAILED else 0
        )
    
    async def _execute_reference_search_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        user_id: str
    ) -> WorkflowResult:
        """Single Agent Pattern: 文献検索ワークフロー"""
        logger.info(f"[Reference] 文献検索ワークフロー開始")
        
        search_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="reference",
            task_type=TaskType.SEARCH_REFERENCES,
            parameters={
                "query": intent_analysis.get("specific_request", ""),
                "keywords": intent_analysis.get("keywords", []),
                "limit": 10,
                "user_id": user_id
            }
        )
        
        # 単一エージェント実行
        search_task.status = TaskStatus.IN_PROGRESS
        result = await self._execute_agent_task(
            search_task.agent_name,
            search_task.task_type,
            search_task.parameters
        )
        
        if result:
            search_task.status = TaskStatus.COMPLETED
            search_task.result = result
        else:
            search_task.status = TaskStatus.FAILED
        
        return WorkflowResult(
            workflow_id=str(uuid.uuid4()),
            status=search_task.status,
            tasks=[search_task],
            execution_time=search_task.execution_time,
            success_count=1 if search_task.status == TaskStatus.COMPLETED else 0,
            failure_count=1 if search_task.status == TaskStatus.FAILED else 0
        )
    
    async def _execute_general_discussion_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        user_id: str
    ) -> WorkflowResult:
        """Fallback Pattern: 一般的な対話ワークフロー"""
        logger.info(f"[General] 一般対話ワークフロー開始")
        
        discussion_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="writer",
            task_type=TaskType.IMPROVE_STYLE,  # 一般的なコンテンツ生成として使用
            parameters={
                "content": intent_analysis.get("specific_request", ""),
                "target_style": "conversational",
                "requirements": "一般的な質問への回答"
            }
        )
        
        discussion_task.status = TaskStatus.IN_PROGRESS
        result = await self._execute_agent_task(
            discussion_task.agent_name,
            discussion_task.task_type,
            discussion_task.parameters
        )
        
        if result:
            discussion_task.status = TaskStatus.COMPLETED
            discussion_task.result = result
        else:
            discussion_task.status = TaskStatus.FAILED
        
        return WorkflowResult(
            workflow_id=str(uuid.uuid4()),
            status=discussion_task.status,
            tasks=[discussion_task],
            execution_time=discussion_task.execution_time,
            success_count=1 if discussion_task.status == TaskStatus.COMPLETED else 0,
            failure_count=1 if discussion_task.status == TaskStatus.FAILED else 0
        )
    
    async def _execute_fallback_workflow(
        self, 
        intent_analysis: Dict[str, Any], 
        user_id: str
    ) -> WorkflowResult:
        """Complete Escape Hatch: フォールバックワークフロー"""
        logger.warning(f"[Fallback] フォールバックワークフロー実行")
        
        fallback_task = WorkflowTask(
            id=str(uuid.uuid4()),
            agent_name="summary",  # 最も安全なエージェント
            task_type=TaskType.ANALYZE_SECTION,
            parameters={
                "analysis_focus": "user_query_analysis",
                "content": intent_analysis.get("specific_request", "")
            }
        )
        
        fallback_task.status = TaskStatus.IN_PROGRESS
        try:
            result = await asyncio.wait_for(
                self._execute_agent_task(
                    fallback_task.agent_name,
                    fallback_task.task_type,
                    fallback_task.parameters
                ),
                timeout=15  # 短いタイムアウト
            )
            
            if result:
                fallback_task.status = TaskStatus.COMPLETED
                fallback_task.result = result
            else:
                fallback_task.status = TaskStatus.FAILED
                
        except Exception as e:
            logger.error(f"[Fallback] フォールバックワークフローも失敗: {e}")
            fallback_task.status = TaskStatus.FAILED
            fallback_task.error_message = str(e)
        
        return WorkflowResult(
            workflow_id=str(uuid.uuid4()),
            status=fallback_task.status,
            tasks=[fallback_task],
            execution_time=fallback_task.execution_time,
            success_count=1 if fallback_task.status == TaskStatus.COMPLETED else 0,
            failure_count=1 if fallback_task.status == TaskStatus.FAILED else 0
        )
    
    async def _analyze_user_intent(self, message: str, paper_id: Optional[str] = None) -> Dict[str, Any]:
        """ユーザー意図解析（Orchestrator Pattern）"""
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
            
            # OpenAI APIで意図解析（拡張版）
            system_prompt = """あなたは研究論文執筆支援の専門家です。
ユーザーのメッセージから以下の情報を抽出・分析してください：

1. 主要な意図:
   - create_section: 新しいセクション作成
   - update_content: 既存コンテンツ更新
   - improve_quality: 品質向上・改善
   - validate_structure: 構造・論理検証
   - search_references: 文献検索
   - analyze_content: 内容分析
   - general_discussion: 一般的な対話

2. 対象セクション（セクション名またはID）
3. 具体的な要求内容
4. 緊急度 (high, medium, low)
5. 抽出されたタイトル（セクション作成時）
6. 改善基準（品質向上時）
7. キーワード（文献検索時）

分析結果をJSONフォーマットで返してください。
例: {"main_intent": "create_section", "extracted_title": "Introduction", "urgency": "medium"}"""
            
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
        
        intent = "general_discussion"
        urgency = "medium"
        extracted_title = ""
        
        # キーワードベースの簡易分析
        if any(keyword in message_lower for keyword in ["作成", "新しい", "セクション", "追加", "create"]):
            intent = "create_section"
            extracted_title = self._extract_section_title(message, intent)
        elif any(keyword in message_lower for keyword in ["改善", "向上", "品質", "improve", "better"]):
            intent = "improve_quality"
        elif any(keyword in message_lower for keyword in ["検証", "チェック", "validate", "check"]):
            intent = "validate_structure"
        elif any(keyword in message_lower for keyword in ["文献", "参考", "引用", "reference"]):
            intent = "search_references"
        elif any(keyword in message_lower for keyword in ["分析", "analyze", "調べる"]):
            intent = "analyze_content"
        
        return {
            "main_intent": intent,
            "target_section": None,
            "specific_request": message,
            "extracted_title": extracted_title,
            "urgency": urgency,
            "improvement_criteria": {},
            "keywords": []
        }
    
    def _extract_section_title(self, message: str, intent: str) -> str:
        """ユーザーメッセージから適切なセクションタイトルを抽出"""
        import re
        
        # 「」や""で囲まれたタイトルを抽出
        quoted_patterns = [
            r'「([^」]+)」',
            r'"([^"]+)"',
            r'[「""]([^」""]+)[」""]'
        ]
        
        for pattern in quoted_patterns:
            matches = re.findall(pattern, message)
            if matches:
                title = matches[0].strip()
                if len(title) < 100:  # 適切な長さのタイトルの場合
                    return title
        
        # キーワードベースでタイトルを推定
        message_lower = message.lower()
        
        if intent == "create_section":
            if any(term in message_lower for term in ['introduction', 'はじめに']):
                return "Introduction"
            elif any(term in message_lower for term in ['methods', 'method', '方法']):
                return "Methods"  
            elif any(term in message_lower for term in ['results', '結果']):
                return "Results"
            elif any(term in message_lower for term in ['discussion', '考察', '結論']):
                return "Discussion"
            elif any(term in message_lower for term in ['conclusion', 'まとめ']):
                return "Conclusion"
            elif any(term in message_lower for term in ['abstract', '概要', '要約']):
                return "Abstract"
        
        # フォールバック: メッセージの最初の15文字を使用
        fallback_title = message[:15].replace('\n', ' ').strip()
        return fallback_title if fallback_title else "新しいセクション"
    
    async def _persist_workflow_results(self, workflow_result: WorkflowResult, paper_id: Optional[str]) -> None:
        """
        ワークフロー結果をデータベースに永続化（Clear Boundaries Pattern）
        
        🎯 これがpaper_sections保存問題の根本解決箇所 🎯
        """
        if not paper_id or workflow_result.status != TaskStatus.COMPLETED:
            return
            
        try:
            for task in workflow_result.tasks:
                if task.status != TaskStatus.COMPLETED or not task.result:
                    continue
                
                logger.info(f"[Persist] タスク結果を永続化: {task.agent_name}:{task.task_type.value}")
                
                # Clear Boundaries Pattern: 各エージェントの責務に応じた保存処理
                if task.agent_name == "outline" and task.task_type == TaskType.CREATE_SECTION:
                    # OutlineAgent: セクション構造の保存は既にエージェント内で実行済み
                    logger.info(f"[Persist] セクション構造は既に保存済み: {task.result.get('section_id')}")
                
                elif task.agent_name == "writer" and task.task_type == TaskType.GENERATE_DRAFT:
                    # WriterAgent: ドラフトコンテンツをpaper_sectionsに保存
                    await self._persist_writer_draft(task, paper_id)
                
                elif task.agent_name == "writer" and task.task_type == TaskType.UPDATE_CONTENT:
                    # WriterAgent: 更新されたコンテンツを保存
                    await self._persist_content_update(task, paper_id)
                
                elif task.agent_name == "summary" and task.task_type == TaskType.CREATE_SUMMARY:
                    # SummaryAgent: 要約をsummaryフィールドに保存
                    await self._persist_summary(task, paper_id)
                    
        except Exception as e:
            logger.error(f"[Persist] データ永続化エラー: {e}")
            # エラーでも処理は継続（Complete Escape Hatch）
    
    async def _persist_writer_draft(self, task: WorkflowTask, paper_id: str) -> None:
        """WriterAgentのドラフトコンテンツを保存"""
        try:
            draft_content = task.result.get("draft_content") or task.result.get("content")
            section_title = task.parameters.get("section_title")
            
            if not draft_content or not section_title:
                logger.warning(f"[Persist] ドラフト保存に必要なデータが不足: content={bool(draft_content)}, title={section_title}")
                return
            
            # タイトルでセクションを特定
            sections = await self.repository.get_sections_by_paper(paper_id)
            matching_section = None
            
            for section in sections:
                if section.title.strip().lower() == section_title.strip().lower():
                    matching_section = section
                    break
            
            if matching_section:
                # セクションコンテンツを更新
                await self.repository.update_section(
                    matching_section.id,
                    {
                        "content": draft_content,
                        "word_count": len(draft_content.split()) if draft_content else 0,
                        "status": "draft"
                    }
                )
                logger.info(f"[Persist] セクション'{section_title}'のコンテンツを保存しました (ID: {matching_section.id})")
            else:
                logger.warning(f"[Persist] セクション'{section_title}'が見つかりませんでした")
                
        except Exception as e:
            logger.error(f"[Persist] WriterAgent結果の保存エラー: {e}")
    
    async def _persist_content_update(self, task: WorkflowTask, paper_id: str) -> None:
        """コンテンツ更新を保存"""
        try:
            section_id = task.parameters.get("section_id")
            updated_content = task.result.get("updated_content") or task.result.get("content")
            
            if section_id and updated_content:
                await self.repository.update_section(
                    section_id,
                    {
                        "content": updated_content,
                        "word_count": len(updated_content.split()),
                        "status": "updated"
                    }
                )
                logger.info(f"[Persist] セクション更新を保存しました (ID: {section_id})")
                
        except Exception as e:
            logger.error(f"[Persist] コンテンツ更新の保存エラー: {e}")
    
    async def _persist_summary(self, task: WorkflowTask, paper_id: str) -> None:
        """要約を保存"""
        try:
            summary_text = task.result.get("summary") or task.result.get("content")
            target_section_title = task.parameters.get("section_title")
            
            if summary_text and target_section_title:
                # 対象セクションを特定して要約を保存
                sections = await self.repository.get_sections_by_paper(paper_id)
                for section in sections:
                    if section.title.strip().lower() == target_section_title.strip().lower():
                        await self.repository.update_section(
                            section.id,
                            {"summary": summary_text}
                        )
                        logger.info(f"[Persist] セクション要約を保存しました (ID: {section.id})")
                        break
                        
        except Exception as e:
            logger.error(f"[Persist] 要約の保存エラー: {e}")
    
    async def _execute_agent_task(
        self, 
        agent_name: str, 
        task_type: TaskType, 
        parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """
        個別エージェントタスクの実行（Clear Boundaries Pattern準拠）
        """
        try:
            # Clear Boundaries Pattern: 責務違反チェック
            if not AgentResponsibilities.validate_task_assignment(agent_name, task_type):
                raise AgentResponsibilityViolation(
                    f"Agent {agent_name} cannot handle task {task_type.value}"
                )
            
            logger.info(f"[Agent] {agent_name}エージェントでタスク実行: {task_type.value}")
            
            agent = self.agents.get(agent_name)
            if not agent:
                raise TaskExecutionError(f"Unknown agent: {agent_name}")
            
            # 旧システム互換のためのパラメータ変換
            agent_task = agent.create_task(
                task_type=self._convert_task_type_to_legacy(task_type),
                parameters=parameters
            )
            
            # エージェント実行
            start_time = time.time()
            result = await agent.execute_task(agent_task)
            execution_time = time.time() - start_time
            
            if result and result.status == AgentStatus.COMPLETED:
                logger.info(f"[Agent] {agent_name}タスク完了 ({execution_time:.1f}s)")
                return result.result
            else:
                logger.warning(f"[Agent] {agent_name}タスク失敗: {result.error_message if result else 'No result'}")
                return None
                
        except Exception as e:
            logger.error(f"[Agent] {agent_name}タスク実行エラー: {e}")
            return None
    
    def _convert_task_type_to_legacy(self, task_type: TaskType) -> str:
        """新しいTaskTypeを旧システム互換の文字列に変換"""
        conversion_map = {
            TaskType.CREATE_SECTION: "create_section",
            TaskType.GENERATE_DRAFT: "generate_draft", 
            TaskType.UPDATE_CONTENT: "update_content",
            TaskType.IMPROVE_STYLE: "improve_style",
            TaskType.VALIDATE_STRUCTURE: "validate_structure",
            TaskType.CREATE_SUMMARY: "create_summary",
            TaskType.SEARCH_REFERENCES: "search_references",
            TaskType.ANALYZE_SECTION: "analyze_section"
        }
        return conversion_map.get(task_type, "general")
    
    async def _generate_integrated_response(
        self,
        user_message: str,
        intent_analysis: Dict[str, Any],
        workflow_result: WorkflowResult
    ) -> Dict[str, Any]:
        """統合応答生成（Supervisor Pattern）"""
        try:
            # ワークフロー結果のサマリー
            completed_tasks = [task for task in workflow_result.tasks if task.status == TaskStatus.COMPLETED]
            failed_tasks = [task for task in workflow_result.tasks if task.status == TaskStatus.FAILED]
            
            # 成功したタスクの結果を整理
            successful_results = []
            references = []
            
            for task in completed_tasks:
                if task.result:
                    successful_results.append({
                        "agent": task.agent_name,
                        "task_type": task.task_type.value,
                        "description": f"{self._get_agent_name_jp(task.agent_name)}: {task.task_type.value}",
                        "result": task.result
                    })
                    
                    # 参考文献があれば収集
                    if isinstance(task.result, dict) and "references" in task.result:
                        references.extend(task.result["references"])
            
            # ユーザーフレンドリーな会話応答を生成
            conversational_response = await self._generate_conversational_response(
                user_message, intent_analysis, successful_results
            )
            
            # 処理状況報告
            response_parts = [conversational_response]
            
            if completed_tasks:
                response_parts.append(f"\n\n✅ {len(completed_tasks)}件のタスクを完了しました！")
                
                # 各エージェントの結果を要約
                for result in successful_results:
                    agent_name_jp = self._get_agent_name_jp(result["agent"])
                    response_parts.append(f"\n🔸 {agent_name_jp}: 処理完了")
                    
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
            logger.error(f"統合応答生成エラー: {e}")
            return {
                "message": "処理を完了しましたが、応答生成中にエラーが発生しました。",
                "references": [],
                "suggestions": []
            }
    
    async def _generate_conversational_response(
        self,
        user_message: str,
        intent_analysis: Dict[str, Any], 
        successful_results: List[Dict[str, Any]]
    ) -> str:
        """ユーザーフレンドリーな会話応答を生成"""
        try:
            main_intent = intent_analysis.get("main_intent", "general")
            
            # 意図別の基本応答
            if main_intent == "create_section":
                section_title = intent_analysis.get("extracted_title", "新しいセクション")
                return f"「{section_title}」セクションの作成を開始いたします！構造とコンテンツを生成し、論文に追加いたします。"
            
            elif main_intent == "improve_quality":
                return "コンテンツの品質向上に取り組みます！生成→評価→改善のサイクルで最適化いたします。"
            
            elif main_intent == "validate_structure":
                return "論文の構造と論理的整合性をチェックいたします！"
            
            elif main_intent == "search_references":
                return "関連する学術文献を検索いたします！"
            
            else:
                return "ご依頼いただきありがとうございます！AIエージェントが最適なアプローチで対応いたします。"
                
        except Exception as e:
            logger.error(f"会話応答生成エラー: {e}")
            return "ご依頼いただきありがとうございます！処理を実行いたします。"
    
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
            return "処理完了"
        
        # セクション作成
        if "section_id" in result:
            return f"セクションを作成（ID: {result['section_id']}）"
        
        # コンテンツ生成
        if "draft_content" in result or "content" in result:
            word_count = result.get("word_count", 0)
            return f"コンテンツを生成（{word_count}語）"
        
        # 文献検索
        if "search_results" in result:
            result_count = len(result["search_results"])
            return f"{result_count}件の関連文献を発見"
        
        return "処理完了"
    
    def _generate_next_action_suggestions(
        self,
        intent_analysis: Dict[str, Any],
        completed_tasks: List[WorkflowTask],
        failed_tasks: List[WorkflowTask]
    ) -> List[str]:
        """次のアクション提案を生成"""
        suggestions = []
        
        # 失敗したタスクがある場合
        if failed_tasks:
            suggestions.append("エラーが発生したタスクを再実行してみてください")
        
        # 成功したタスクに基づく提案
        for task in completed_tasks:
            if task.agent_name == "outline" and task.status == TaskStatus.COMPLETED:
                suggestions.append("作成したセクションに内容を追加してみましょう")
            elif task.agent_name == "writer" and task.status == TaskStatus.COMPLETED:
                suggestions.append("生成したコンテンツの品質をさらに向上させてみませんか？")
            elif task.agent_name == "reference" and task.status == TaskStatus.COMPLETED:
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
    
    async def _generate_error_response(self, error_message: str, user_message: str) -> str:
        """エラー時の適切な応答を生成（Complete Escape Hatch）"""
        try:
            # エラーの種類に応じた適切な応答
            if "timeout" in error_message.lower():
                return "処理に時間がかかりすぎたため、タイムアウトしました。もう一度お試しください。"
            elif "not found" in error_message.lower():
                return "指定されたリソースが見つかりませんでした。条件を確認してもう一度お試しください。"
            elif "permission" in error_message.lower():
                return "権限不足のため処理できませんでした。必要な権限があることを確認してください。"
            else:
                return "申し訳ございません。処理中にエラーが発生しました。もう一度お試しいただくか、別の方法でご相談ください。"
                
        except Exception:
            return "システムエラーが発生しました。時間をおいて再度お試しください。"
    
    def _convert_workflow_to_todos(self, workflow_result: WorkflowResult) -> List[Dict[str, Any]]:
        """WorkflowResultを旧形式のTodoリストに変換（後方互換性）"""
        todos = []
        for task in workflow_result.tasks:
            todos.append({
                "id": task.id,
                "description": f"{self._get_agent_name_jp(task.agent_name)}: {task.task_type.value}",
                "agent_name": task.agent_name,
                "priority": task.priority,
                "status": task.status.value,
                "parameters": task.parameters,
                "result": task.result
            })
        return todos
    
    def _serialize_workflow_result(self, workflow_result: WorkflowResult) -> Dict[str, Any]:
        """WorkflowResultをシリアライズ"""
        return {
            "workflow_id": workflow_result.workflow_id,
            "status": workflow_result.status.value,
            "execution_time": workflow_result.execution_time,
            "success_count": workflow_result.success_count,
            "failure_count": workflow_result.failure_count,
            "tasks": [
                {
                    "id": task.id,
                    "agent_name": task.agent_name,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "execution_time": task.execution_time,
                    "error_message": task.error_message
                }
                for task in workflow_result.tasks
            ]
        }