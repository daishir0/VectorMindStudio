"""
研究ディスカッションAIサービス V3 - LLM-based Supervisor Pattern
AAIDC準拠の真のスーパーバイザーパターン実装
"""
from typing import Any, Dict, List, Optional, Tuple
import logging
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

# ドメインエンティティ
from app.schemas.paper import TodoTaskInfo
from app.services.research_discussion_service import TaskPriority
from app.services.workflow_patterns import TaskStatus
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.external.openai_client import openai_client

# エージェント群 - Enhanced版
from app.services.agents import (
    BaseAgent, AgentTask, AgentResult, AgentStatus,
    OutlineAgent, SummaryAgent, WriterAgent, LogicValidatorAgent,
    AnalysisAgent, EditingAgent, QualityAgent, DiscoveryAgent, GenerationAgent,
    StrategyAgent, OptimizationAgent, StructureAgent
)
from app.services.agents.section_query_agent import SectionQueryAgent
from app.services.agents.supervisor_agent import SupervisorAgent
from app.services.agents.enhanced_base_agent import EnhancedBaseAgent
from app.services.response_formatter import ResponseFormatter
from app.services.enhanced_error_handler import enhanced_error_handler

logger = logging.getLogger(__name__)


class ResearchDiscussionServiceV3:
    """
    研究ディスカッションAIサービス V3
    
    特徴:
    - LLM-based Supervisor Agentによる高度な意図解析
    - 既存情報を考慮した動的タスクプランニング  
    - 真のタスクについての推論
    - AAIDC準拠のスーパーバイザーパターン実装
    - Rule-basedからAI-basedへの進化
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = PaperRepository(session)
        
        # スーパーバイザーエージェント（中心的な意思決定者）
        self.supervisor = SupervisorAgent(session)
        
        # 専門エージェント群（Enhanced版）- 全エージェントにセッション渡し
        self.specialist_agents = {
            "outline": OutlineAgent(session),
            "summary": SummaryAgent(session),
            "writer": WriterAgent(session),
            "logic_validator": LogicValidatorAgent(session),
            "section_query": SectionQueryAgent(session),  # Enhanced版
            "analysis": AnalysisAgent(session),  # 研究論文分析エージェント
            "editing": EditingAgent(session),  # 研究論文編集エージェント
            "quality": QualityAgent(session),  # 研究論文品質保証エージェント
            "discovery": DiscoveryAgent(session),  # Phase 2：研究発見・探索エージェント
            "generation": GenerationAgent(session),  # Phase 2：コンテンツ生成・拡張エージェント
            "strategy": StrategyAgent(session),  # Phase 3：研究戦略・計画エージェント
            "optimization": OptimizationAgent(session),  # Phase 3：研究最適化・効率化エージェント
            "structure": StructureAgent(session)  # Phase 3：論文構造最適化エージェント
        }
        
        # 全エージェント統合
        self.all_agents = {
            "supervisor": self.supervisor,
            **self.specialist_agents
        }
        
        # システム設定
        self.max_conversation_turns = 50
        self.max_parallel_agents = 3
        self.timeout_seconds = 120
    
    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str,
        paper_id: Optional[str] = None,
        target_section_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ユーザーメッセージの処理 - Supervisor Pattern
        
        フロー:
        1. Supervisor Agentによる高度な意図解析
        2. 動的ワークフロープランニング
        3. 専門エージェントへのタスク委譲
        4. 実行結果の統合・品質管理
        """
        try:
            logger.info(f"[ServiceV3] メッセージ処理開始: '{user_message[:50]}...' (paper: {paper_id})")
            
            # Step 1: Supervisor Agentによる意図解析
            intent_result = await self._supervisor_analyze_intent(
                user_message, paper_id, user_id
            )
            
            # Step 2: ワークフロープランニング
            workflow_result = await self._supervisor_plan_workflow(
                intent_result, user_message, paper_id, user_id
            )
            
            # Step 3: 専門エージェントでのタスク実行
            execution_results = await self._execute_specialist_tasks(
                workflow_result["workflow_plan"]["tasks"],
                paper_id
            )
            
            # Step 4: 結果の統合と回答生成
            response = await self._generate_integrated_response(
                user_message, intent_result, workflow_result, execution_results
            )
            
            # Step 5: セッションにメッセージを記録
            await self._record_conversation(
                session_id, user_message, response, user_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"[ServiceV3] メッセージ処理エラー: {e}")
            
            # 強化されたエラーハンドリングを使用
            error_context = {
                "user_message": user_message,
                "paper_id": paper_id,
                "user_id": user_id,
                "session_id": session_id
            }
            
            error_result = await enhanced_error_handler.handle_error_with_recovery(e, error_context)
            
            if error_result["success"]:
                # 回復成功時の処理
                return {
                    "message": error_result.get("fallback_content", "代替処理で応答しました。"),
                    "todo_tasks": [],
                    "task_results": {},
                    "success": True,
                    "recovery_info": "エラー回復処理により代替応答を生成"
                }
            else:
                # 回復失敗時の詳細なユーザー対応
                return {
                    "message": error_result["user_message"],
                    "todo_tasks": [],
                    "task_results": {},
                    "success": False,
                    "error_type": error_result.get("error_type"),
                    "recovery_attempted": True,
                    "technical_details": error_result.get("technical_details") if error_result.get("severity") == "high" else None
                }
    
    async def _supervisor_analyze_intent(
        self, 
        user_message: str, 
        paper_id: Optional[str], 
        user_id: str
    ) -> Dict[str, Any]:
        """Step 1: Supervisor Agentによる高度な意図解析"""
        try:
            logger.info(f"[ServiceV3] Supervisor意図解析開始")
            
            # SupervisorAgentのタスク作成
            intent_task = AgentTask(
                id=str(uuid.uuid4()),
                task_type="analyze_intent",
                parameters={
                    "task_type": "analyze_intent",
                    "user_message": user_message,
                    "paper_id": paper_id,
                    "user_id": user_id
                },
                priority=1
            )
            
            # 実行
            result = await self.supervisor.execute_task(intent_task)
            
            if hasattr(result, 'result') and isinstance(result.result, dict):
                actual_result = result.result
                logger.info(f"[ServiceV3] Supervisor意図解析完了: {actual_result.get('intent_analysis', {}).get('intent_type', 'unknown')}")
                return actual_result
            elif isinstance(result, dict):
                logger.info(f"[ServiceV3] Supervisor意図解析完了: {result.get('intent_analysis', {}).get('intent_type', 'unknown')}")
                return result
            else:
                logger.warning(f"[ServiceV3] Supervisor結果が期待した形式ではありません: {type(result)}")
                return {"intent_analysis": {}, "success": False}
                
        except Exception as e:
            logger.error(f"[ServiceV3] Supervisor意図解析エラー: {e}")
            # フォールバック: 従来の意図解析
            return {
                "intent_analysis": {
                    "intent_type": "general_help",
                    "confidence": 0.3,
                    "target_section": None,
                    "primary_task": "一般的な処理",
                    "recommended_agents": ["summary"],
                    "reasoning": f"エラーのためフォールバック処理: {e}"
                },
                "fallback_used": True,
                "success": False
            }
    
    async def _supervisor_plan_workflow(
        self, 
        intent_result: Dict[str, Any], 
        user_message: str,
        paper_id: Optional[str], 
        user_id: str
    ) -> Dict[str, Any]:
        """Step 2: Supervisor Agentによるワークフロープランニング"""
        try:
            logger.info(f"[ServiceV3] Supervisorワークフロープランニング開始")
            
            workflow_task = AgentTask(
                id=str(uuid.uuid4()),
                task_type="plan_workflow",
                parameters={
                    "task_type": "plan_workflow",
                    "intent_analysis": intent_result.get("intent_analysis", {}),
                    "user_message": user_message,
                    "paper_id": paper_id,
                    "user_id": user_id
                },
                priority=1
            )
            
            result = await self.supervisor.execute_task(workflow_task)
            
            if hasattr(result, 'result') and isinstance(result.result, dict):
                actual_result = result.result
                tasks = actual_result.get("workflow_plan", {}).get("tasks", [])
                logger.info(f"[ServiceV3] Supervisorワークフロープランニング完了: {len(tasks)}タスク")
                return actual_result
            elif isinstance(result, dict):
                tasks = result.get("workflow_plan", {}).get("tasks", [])
                logger.info(f"[ServiceV3] Supervisorワークフロープランニング完了: {len(tasks)}タスク")
                return result
            else:
                logger.warning(f"[ServiceV3] Supervisor結果が期待した形式ではありません")
                return {"workflow_plan": {"tasks": []}, "success": False}
                
        except Exception as e:
            logger.error(f"[ServiceV3] Supervisorワークフロープランニングエラー: {e}")
            return {"workflow_plan": {"tasks": []}, "success": False}
    
    async def _execute_specialist_tasks(
        self,
        planned_tasks: List[Dict[str, Any]],
        paper_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Step 3: 専門エージェントでのタスク実行"""
        if not planned_tasks:
            return []

        try:
            logger.info(f"[ServiceV3] 専門エージェント実行開始: {len(planned_tasks)}タスク, paper_id={paper_id}")

            execution_results = []

            # タスクの並列実行（最大3個まで）
            semaphore = asyncio.Semaphore(self.max_parallel_agents)

            async def execute_single_task(task_config: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    agent_name = task_config.get("agent")
                    if agent_name not in self.specialist_agents:
                        logger.warning(f"[ServiceV3] 未知のエージェント: {agent_name}")
                        return {
                            "agent": agent_name,
                            "success": False,
                            "error": f"未知のエージェント: {agent_name}"
                        }

                    try:
                        # タスクparametersにpaper_idを追加
                        task_parameters = task_config.get("parameters", {}).copy()
                        if paper_id:
                            task_parameters["paper_id"] = paper_id

                        logger.info(f"[ServiceV3] エージェント {agent_name} 実行開始, parameters keys: {list(task_parameters.keys())}")

                        # AgentTaskオブジェクト作成
                        agent_task = AgentTask(
                            id=str(uuid.uuid4()),
                            task_type=task_config.get("task_type", "unknown"),
                            parameters=task_parameters,
                            priority=1 if task_config.get("priority") == "high" else 2
                        )
                        
                        # エージェント実行
                        agent = self.specialist_agents[agent_name]
                        result = await agent.execute_task(agent_task)

                        # WriterAgentの結果をセクションとして保存
                        if agent_name == "writer" and result:
                            await self._save_writer_result_to_section(result, task_parameters)

                        # AgentResultの実際のステータスをチェック
                        agent_succeeded = (
                            hasattr(result, 'status') and
                            result.status == AgentStatus.COMPLETED and
                            result.result is not None
                        )

                        return {
                            "agent": agent_name,
                            "task_type": task_config.get("task_type"),
                            "description": task_config.get("description"),
                            "result": result,
                            "success": agent_succeeded
                        }
                        
                    except Exception as e:
                        logger.error(f"[ServiceV3] エージェント実行エラー ({agent_name}): {e}")
                        return {
                            "agent": agent_name,
                            "task_type": task_config.get("task_type"),
                            "description": task_config.get("description"),
                            "success": False,
                            "error": str(e)
                        }
            
            # 並列実行
            tasks = [execute_single_task(task) for task in planned_tasks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 例外処理
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"[ServiceV3] タスク実行例外: {result}")
                    execution_results.append({
                        "success": False,
                        "error": str(result)
                    })
                else:
                    execution_results.append(result)
            
            successful_tasks = sum(1 for r in execution_results if r.get("success"))
            logger.info(f"[ServiceV3] 専門エージェント実行完了: {successful_tasks}/{len(planned_tasks)}成功")
            
            return execution_results
            
        except Exception as e:
            logger.error(f"[ServiceV3] 専門エージェント実行エラー: {e}")
            return []
    
    async def _generate_integrated_response(
        self,
        user_message: str,
        intent_result: Dict[str, Any],
        workflow_result: Dict[str, Any], 
        execution_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Step 4: 結果統合と最終回答生成"""
        try:
            # デバッグログ追加（ファイルにも出力）
            import json
            debug_file = "/tmp/supervisor_debug.log"
            with open(debug_file, "a") as f:
                f.write(f"\n\n=== {datetime.now()} ===\n")
                f.write(f"execution_results数: {len(execution_results)}\n")
                for idx, r in enumerate(execution_results):
                    f.write(f"Result {idx}: agent={r.get('agent')}, success={r.get('success')}, error={r.get('error')}\n")
                    f.write(f"  task_type: {r.get('task_type')}\n")
                    f.write(f"  description: {r.get('description')}\n")
                    f.write(f"  result type: {type(r.get('result'))}\n")
                    if r.get('result'):
                        result_obj = r.get('result')
                        if hasattr(result_obj, 'result'):
                            f.write(f"  result.result: {result_obj.result}\n")
                            f.write(f"  result.status: {result_obj.status}\n")
                        f.write(f"  result keys: {list(result_obj.keys() if isinstance(result_obj, dict) else [])}\n")

            logger.info(f"[ServiceV3] execution_results数: {len(execution_results)}")
            for idx, r in enumerate(execution_results):
                logger.info(f"[ServiceV3] Result {idx}: agent={r.get('agent')}, success={r.get('success')}, error={r.get('error')}")

            # 成功したタスクの抽出
            successful_results = [r for r in execution_results if r.get("success")]

            with open(debug_file, "a") as f:
                f.write(f"successful_results数: {len(successful_results)}\n")

            logger.info(f"[ServiceV3] successful_results数: {len(successful_results)}")

            # エージェント実行結果を適切な形式に変換（Enhanced対応）
            formatted_task_results = {}
            for result in successful_results:
                agent_name = result.get("agent", "unknown")
                agent_result = result.get("result", {})
                
                # エージェント名をResponseFormatter期待形式に変換
                formatter_agent_name = {
                    "section_query": "SectionQueryAgent",
                    "writer": "WriterAgent",
                    "outline": "OutlineAgent",
                    "summary": "SummaryAgent",
                    "logic_validator": "LogicValidatorAgent",
                    "analysis": "AnalysisAgent",
                    "editing": "EditingAgent",
                    "quality": "QualityAgent",
                    "discovery": "DiscoveryAgent",
                    "generation": "GenerationAgent",
                    "strategy": "StrategyAgent",
                    "optimization": "OptimizationAgent",
                    "structure": "StructureAgent"
                }.get(agent_name, agent_name)
                
                # EnhancedBaseAgentの結果処理
                if hasattr(agent_result, 'result') and isinstance(agent_result.result, dict):
                    formatted_task_results[formatter_agent_name] = agent_result.result
                elif isinstance(agent_result, dict):
                    formatted_task_results[formatter_agent_name] = agent_result
                else:
                    formatted_task_results[formatter_agent_name] = {"success": False, "error": "結果形式が無効"}
            
            # ResponseFormatterを使用して統合レスポンス生成
            integrated_response = ResponseFormatter.integrate_all_results(
                intent_analysis=intent_result.get("intent_analysis", {}),
                task_results=formatted_task_results,
                original_query=user_message
            )
            
            # メタデータ追加
            integrated_response["metadata"] = {
                "intent_type": intent_result.get("intent_analysis", {}).get("intent_type", "unknown"),
                "confidence": intent_result.get("intent_analysis", {}).get("confidence", 0.0),
                "tasks_executed": len(successful_results),
                "supervisor_used": True
            }
            
            return integrated_response
            
        except Exception as e:
            logger.error(f"[ServiceV3] 回答生成エラー: {e}")
            return {
                "message": "処理は完了しましたが、回答生成中にエラーが発生しました。",
                "todo_tasks": [],
                "task_results": {},
                "references": [],
                "suggestions": [],
                "success": False,
                "error": str(e)
            }
    
    async def _generate_conversational_response(
        self,
        user_message: str,
        intent_result: Dict[str, Any],
        successful_results: List[Dict[str, Any]]
    ) -> str:
        """自然な会話応答の生成"""
        try:
            intent_analysis = intent_result.get("intent_analysis", {})
            intent_type = intent_analysis.get("intent_type", "general")
            
            # 主要な結果を特定
            primary_content = ""
            for result in successful_results:
                agent_name = result.get("agent")
                result_data = result.get("result", {})
                
                if agent_name == "section_query":
                    # セクション内容の表示
                    if isinstance(result_data, dict) and result_data.get("found"):
                        section = result_data.get("section", {})
                        content = section.get("content", "")
                        summary = section.get("summary", "")
                        title = section.get("title", "")
                        
                        response = f"「{title}」セクションの内容をお答えします。\n\n"
                        
                        if summary:
                            response += f"【要約】\n{summary}\n\n"
                        
                        if content:
                            if len(content) > 800:
                                response += f"【詳細内容（冒頭部分）】\n{content[:800]}...\n\n"
                                response += f"（全体: {section.get('word_count', 0)}語）"
                            else:
                                response += f"【詳細内容】\n{content}"
                        else:
                            response += "まだ内容が執筆されていません。"
                        
                        return response
                    
                    elif isinstance(result_data, dict):
                        answer = result_data.get("answer", "")
                        if answer:
                            return answer
                
                elif agent_name == "writer":
                    # 生成されたコンテンツの表示
                    if isinstance(result_data, dict):
                        content = result_data.get("draft_content") or result_data.get("content", "")
                        if content:
                            return f"新しいコンテンツを生成しました。\n\n{content}"
                
                elif agent_name == "summary":
                    # 要約結果の表示
                    if isinstance(result_data, dict):
                        summary = result_data.get("summary", "")
                        if summary:
                            return f"論文の要約をお答えします。\n\n{summary}"
                
                elif agent_name == "analysis":
                    # 分析結果の表示
                    if isinstance(result_data, dict):
                        response = "論文の構造分析結果をお答えします。\n\n"
                        
                        # 全体評価
                        if "overall_assessment" in result_data:
                            assessment = result_data["overall_assessment"]
                            response += f"【全体評価】\n{assessment}\n\n"
                        
                        # 平均スコア
                        if "average_critical_score" in result_data:
                            score = result_data["average_critical_score"]
                            response += f"【批判的評価スコア】\n{score:.1f}/10\n\n"
                        
                        # 批判的問題点
                        critical_issues = result_data.get("critical_issues", [])
                        if critical_issues:
                            response += "【発見された問題点】\n"
                            for i, issue in enumerate(critical_issues[:5], 1):
                                response += f"{i}. {issue}\n"
                            response += "\n"
                        
                        # 改善提案
                        suggestions = result_data.get("improvement_suggestions", [])
                        if suggestions:
                            response += "【改善提案】\n"
                            for i, suggestion in enumerate(suggestions[:5], 1):
                                response += f"{i}. {suggestion}\n"
                            response += "\n"
                        
                        # セクション別分析結果
                        analysis_results = result_data.get("analysis_results", [])
                        if analysis_results:
                            response += f"【分析対象】\n{len(analysis_results)}個のセクションを分析しました。\n"
                            for analysis in analysis_results[:3]:
                                section_title = analysis.get("section_title", "不明")
                                score = analysis.get("critical_score", 0)
                                response += f"・{section_title}: {score}/10\n"
                        
                        return response
                
                elif agent_name == "editing":
                    # 編集結果の表示
                    if isinstance(result_data, dict):
                        editing_result = result_data.get("editing_result", {})
                        task_type = result_data.get("task_type", "editing")
                        
                        if editing_result:
                            response = f"論文の{task_type}編集結果をお答えします。\n\n"
                            
                            # 編集後のコンテンツ
                            if "improved_content" in editing_result:
                                content = editing_result["improved_content"]
                                if len(content) > 800:
                                    response += f"【編集後内容（冒頭部分）】\n{content[:800]}...\n\n"
                                else:
                                    response += f"【編集後内容】\n{content}\n\n"
                            
                            # 改善点
                            if "improvements" in editing_result:
                                improvements = editing_result["improvements"]
                                if isinstance(improvements, list) and improvements:
                                    response += "【主な改善点】\n"
                                    for i, improvement in enumerate(improvements[:3], 1):
                                        response += f"{i}. {improvement}\n"
                                    response += "\n"
                            
                            # 品質スコア
                            if "quality_score" in editing_result:
                                score = editing_result["quality_score"]
                                response += f"【品質スコア】\n{score:.1f}/1.0\n"
                            
                            return response
                
                elif agent_name == "quality":
                    # 品質評価結果の表示
                    if isinstance(result_data, dict):
                        response = "論文の品質評価結果をお答えします。\n\n"
                        
                        # 総合品質スコア
                        if "overall_quality" in result_data:
                            score = result_data["overall_quality"]
                            response += f"【総合品質スコア】\n{score:.1f}/10\n\n"
                        
                        # 出版準備度
                        if "readiness_assessment" in result_data:
                            readiness = result_data["readiness_assessment"]
                            response += f"【出版準備度】\n{readiness}\n\n"
                        
                        # 改善推奨事項
                        recommendations = result_data.get("improvement_recommendations", [])
                        if recommendations:
                            response += "【改善推奨事項】\n"
                            for i, rec in enumerate(recommendations[:5], 1):
                                response += f"{i}. {rec}\n"
                            response += "\n"
                        
                        # セクション別品質スコア
                        quality_scores = result_data.get("quality_scores", {})
                        if quality_scores:
                            response += "【セクション別品質】\n"
                            for section, score in list(quality_scores.items())[:3]:
                                response += f"・{section}: {score:.1f}/10\n"
                        
                        return response
                
                elif agent_name == "discovery":
                    # 発見・探索結果の表示
                    if isinstance(result_data, dict):
                        discovery_result = result_data.get("discovery_result", {})
                        task_type = result_data.get("task_type", "発見")
                        
                        if discovery_result:
                            response = f"研究{task_type}分析結果をお答えします。\n\n"
                            
                            # 発見されたギャップや要素
                            if "identified_gaps" in discovery_result:
                                gaps = discovery_result["identified_gaps"]
                                if isinstance(gaps, list) and gaps:
                                    response += "【発見されたギャップ】\n"
                                    for i, gap in enumerate(gaps[:3], 1):
                                        response += f"{i}. {gap}\n"
                                    response += "\n"
                            
                            # 新規テーマや発見事項
                            if "novel_themes" in discovery_result:
                                themes = discovery_result["novel_themes"]
                                if isinstance(themes, list) and themes:
                                    response += "【新規発見事項】\n"
                                    for i, theme in enumerate(themes[:3], 1):
                                        response += f"{i}. {theme}\n"
                                    response += "\n"
                            
                            # 推奨アクション
                            if "recommendations" in discovery_result:
                                recommendations = discovery_result["recommendations"]
                                if isinstance(recommendations, list) and recommendations:
                                    response += "【推奨アクション】\n"
                                    for i, rec in enumerate(recommendations[:3], 1):
                                        response += f"{i}. {rec}\n"
                            
                            return response
                
                elif agent_name == "generation":
                    # 生成結果の表示
                    if isinstance(result_data, dict):
                        generation_result = result_data.get("generation_result", {})
                        task_type = result_data.get("task_type", "コンテンツ生成")
                        
                        if generation_result:
                            response = f"{task_type}結果をお答えします。\n\n"
                            
                            # 生成されたコンテンツ
                            if "generated_content" in generation_result:
                                content = generation_result["generated_content"]
                                if isinstance(content, str) and content.strip():
                                    response += "【生成されたコンテンツ】\n"
                                    response += content + "\n\n"
                            
                            # 生成されたアウトライン
                            if "generated_outline" in generation_result:
                                outline = generation_result["generated_outline"]
                                if isinstance(outline, list) and outline:
                                    response += "【生成されたアウトライン】\n"
                                    for i, item in enumerate(outline, 1):
                                        response += f"{i}. {item}\n"
                                    response += "\n"
                            
                            # 生成統計
                            if "generation_metrics" in generation_result:
                                metrics = generation_result["generation_metrics"]
                                if isinstance(metrics, dict):
                                    response += "【生成統計】\n"
                                    if "word_count" in metrics:
                                        response += f"文字数: {metrics['word_count']}\n"
                                    if "quality_score" in metrics:
                                        response += f"品質スコア: {metrics['quality_score']:.1f}/1.0\n"
                            
                            return response
                
                elif agent_name == "strategy":
                    # 戦略立案結果の表示
                    if isinstance(result_data, dict):
                        strategy_result = result_data.get("strategy_result", {})
                        task_type = result_data.get("task_type", "戦略立案")
                        
                        if strategy_result:
                            response = f"研究{task_type}結果をお答えします。\n\n"
                            
                            # 立案された戦略
                            if "strategy_plan" in strategy_result:
                                plan = strategy_result["strategy_plan"]
                                if isinstance(plan, str) and plan.strip():
                                    response += "【戦略プラン】\n"
                                    response += plan + "\n\n"
                            
                            # 戦略的推奨事項
                            if "strategic_recommendations" in strategy_result:
                                recommendations = strategy_result["strategic_recommendations"]
                                if isinstance(recommendations, list) and recommendations:
                                    response += "【戦略的推奨事項】\n"
                                    for i, rec in enumerate(recommendations[:3], 1):
                                        response += f"{i}. {rec}\n"
                                    response += "\n"
                            
                            # リスク評価
                            if "risk_assessment" in strategy_result:
                                risk_assessment = strategy_result["risk_assessment"]
                                if isinstance(risk_assessment, dict):
                                    response += "【リスク評価】\n"
                                    if "risk_level" in risk_assessment:
                                        response += f"リスクレベル: {risk_assessment['risk_level']}\n"
                                    if "mitigation_strategies" in risk_assessment:
                                        mitigations = risk_assessment["mitigation_strategies"]
                                        if isinstance(mitigations, list):
                                            response += "軽減戦略:\n"
                                            for mitigation in mitigations[:2]:
                                                response += f"- {mitigation}\n"
                            
                            return response
                
                elif agent_name == "optimization":
                    # 最適化結果の表示
                    if isinstance(result_data, dict):
                        optimization_result = result_data.get("optimization_result", {})
                        task_type = result_data.get("task_type", "最適化")
                        
                        if optimization_result:
                            response = f"研究{task_type}結果をお答えします。\n\n"
                            
                            # 最適化提案
                            if "optimization_proposals" in optimization_result:
                                proposals = optimization_result["optimization_proposals"]
                                if isinstance(proposals, list) and proposals:
                                    response += "【最適化提案】\n"
                                    for i, proposal in enumerate(proposals[:3], 1):
                                        response += f"{i}. {proposal}\n"
                                    response += "\n"
                            
                            # 効率化指標
                            if "efficiency_metrics" in optimization_result:
                                metrics = optimization_result["efficiency_metrics"]
                                if isinstance(metrics, dict):
                                    response += "【効率化指標】\n"
                                    if "time_savings" in metrics:
                                        response += f"時間短縮: {metrics['time_savings']}\n"
                                    if "cost_reduction" in metrics:
                                        response += f"コスト削減: {metrics['cost_reduction']}\n"
                                    if "quality_improvement" in metrics:
                                        response += f"品質向上: {metrics['quality_improvement']}\n"
                                    response += "\n"
                            
                            # 実装優先度
                            if "implementation_priority" in optimization_result:
                                priority_list = optimization_result["implementation_priority"]
                                if isinstance(priority_list, list) and priority_list:
                                    response += "【実装優先度】\n"
                                    for i, item in enumerate(priority_list[:3], 1):
                                        response += f"{i}. {item}\n"
                            
                            return response
            
            # フォールバック応答
            if intent_type == "query_existing":
                return "お探しの情報が見つかりませんでした。他のセクションについてお聞きになりたいことはありますか？"
            elif intent_type == "create_new": 
                return "新しいコンテンツの作成を開始いたします。"
            else:
                return "ご質問を承りました。どのようなお手伝いが必要でしょうか？"
                
        except Exception as e:
            logger.error(f"[ServiceV3] 会話応答生成エラー: {e}")
            return "申し訳ありません。回答の生成中にエラーが発生しました。"
    
    def _generate_suggestions(
        self, 
        intent_result: Dict[str, Any], 
        successful_results: List[Dict[str, Any]]
    ) -> List[str]:
        """次のアクション提案"""
        suggestions = []
        intent_type = intent_result.get("intent_analysis", {}).get("intent_type", "")
        
        if intent_type == "query_existing":
            suggestions.extend([
                "他のセクションについても教えて",
                "このセクションを編集したい", 
                "論文全体を要約して"
            ])
        elif intent_type == "create_new":
            suggestions.extend([
                "作成したコンテンツをレビューして",
                "論文の構造をチェックして",
                "関連する文献を探して"
            ])
        else:
            suggestions.extend([
                "論文の進捗を教えて",
                "新しいセクションを作成したい",
                "論文全体をエクスポートしたい"
            ])
        
        return suggestions[:3]
    
    async def _save_writer_result_to_section(
        self,
        agent_result: Any,
        task_params: Dict[str, Any]
    ) -> None:
        """WriterAgentの結果をセクションとして保存"""
        try:
            logger.info(f"[ServiceV3] _save_writer_result_to_section開始")
            logger.info(f"[ServiceV3] task_params: {task_params}")

            # AgentResultオブジェクトから実際の結果を抽出
            if hasattr(agent_result, 'result') and isinstance(agent_result.result, dict):
                writer_result = agent_result.result
                logger.info(f"[ServiceV3] AgentResult.resultから抽出")
            elif isinstance(agent_result, dict):
                writer_result = agent_result
                logger.info(f"[ServiceV3] dictから直接使用")
            else:
                logger.warning(f"[ServiceV3] WriterAgent結果の形式が不正: {type(agent_result)}")
                return

            # コンテンツとタイトルを取得
            draft_content = writer_result.get("draft_content") or writer_result.get("content", "")
            section_title = writer_result.get("section_title") or task_params.get("section_title", "新規セクション")
            paper_id = task_params.get("paper_id")

            logger.info(f"[ServiceV3] draft_content length: {len(draft_content) if draft_content else 0}")
            logger.info(f"[ServiceV3] section_title: {section_title}")
            logger.info(f"[ServiceV3] paper_id: {paper_id}")

            if not draft_content or not paper_id:
                logger.warning(f"[ServiceV3] セクション保存に必要な情報が不足: draft_content={bool(draft_content)}, paper_id={paper_id}")
                return

            # 次のポジションを取得
            next_position = await self.repository.get_next_position(paper_id)
            logger.info(f"[ServiceV3] next_position: {next_position}")

            # セクション番号を自動生成（簡易版）
            section_number = f"{next_position}"

            # セクションを作成
            section = await self.repository.create_section(
                paper_id=paper_id,
                position=next_position,
                section_number=section_number,
                title=section_title,
                content=draft_content,
                summary=writer_result.get("summary", "")
            )

            logger.info(f"[ServiceV3] WriterAgent結果をセクションとして保存成功: section_id={section.id}, title={section_title}, content_length={len(draft_content)}")

        except Exception as e:
            logger.error(f"[ServiceV3] WriterAgent結果の保存エラー: {e}", exc_info=True)
            # エラーでも処理を中断しない（チャットには表示されている）

    async def _record_conversation(
        self,
        session_id: str,
        user_message: str,
        response: Dict[str, Any],
        user_id: str
    ) -> None:
        """会話履歴の記録"""
        try:
            # ユーザーメッセージを記録
            await self.repository.create_chat_message(
                session_id=session_id,
                role="user",
                content=user_message
            )

            # AIの応答を記録
            await self.repository.create_chat_message(
                session_id=session_id,
                role="assistant",
                content=response.get("message", ""),
                agent_name="SupervisorV3",
                todo_tasks=[],
                references=response.get("references", [])
            )

        except Exception as e:
            logger.error(f"[ServiceV3] 会話記録エラー: {e}")
            # エラーでも処理を中断しない