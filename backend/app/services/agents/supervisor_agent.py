"""
Supervisor Agent - LLMベースの高次意図解析・タスク推論エージェント
AAIDC準拠のSupervisor Pattern実装
"""
from typing import Dict, List, Any, Optional
import logging
import json

from .base_agent import BaseAgent, AgentTask, AgentResult, AgentExecutionError, AgentValidationError
from app.infrastructure.external.openai_client import openai_client
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """
    スーパーバイザーエージェント - AAIDC準拠
    
    責務:
    - ユーザーの意図を深く理解・推論
    - 利用可能なエージェントとツールを考慮した最適なタスク分解
    - 動的なワークフロー決定
    - 品質管理とエラー回復
    - 文脈に基づく専門エージェント選択
    
    特徴:
    - Rule-basedではなくLLM-basedの推論
    - 既存セクション情報を考慮した意図解析
    - 動的タスクプランニング
    - エージェント能力のメタ知識活用
    """
    
    def __init__(self, session=None):
        super().__init__(
            name="SupervisorAgent",
            description="LLMベースの高次タスク推論・エージェント管理を行うスーパーバイザー",
            max_retries=2,
            timeout=settings.AI_AGENT_TIMEOUT_SECONDS
        )
        self.session = session
        self.repository = PaperRepository(session) if session else None
        
        # エージェント能力のメタ知識
        self.agent_capabilities = {
            "section_query": {
                "description": "既存セクションの検索・参照・内容取得",
                "best_for": ["セクション内容の質問", "特定セクションの検索", "既存情報の参照"],
                "keywords": ["教えて", "について", "内容", "見せて", "Abstract", "Introduction", "Methods", "Results", "Discussion"]
            },
            "writer": {
                "description": "新しいコンテンツの生成・文章作成",
                "best_for": ["新規セクション作成", "文章生成", "コンテンツ執筆"],
                "keywords": ["作って", "書いて", "生成", "執筆", "ドラフト"]
            },
            "summary": {
                "description": "要約・概要作成",
                "best_for": ["要約作成", "論文全体のまとめ", "概要生成"],
                "keywords": ["要約", "まとめ", "概要", "サマリー"]
            },
            "outline": {
                "description": "論文構造・アウトライン管理",
                "best_for": ["構造設計", "セクション管理", "アウトライン作成"],
                "keywords": ["構造", "アウトライン", "セクション", "章立て"]
            },
            "logic_validator": {
                "description": "論理的整合性・品質チェック",
                "best_for": ["論理チェック", "整合性検証", "品質評価"],
                "keywords": ["チェック", "確認", "検証", "品質"]
            },
            "analysis": {
                "description": "研究論文の深度分析・批判的評価・構造解析",
                "best_for": ["批判的分析", "構造分析", "整合性チェック", "弱点特定", "比較分析"],
                "keywords": ["分析", "解析", "評価", "批判", "弱点", "問題", "改善", "レビュー", "査読"]
            },
            "editing": {
                "description": "研究論文の編集・改善・文章品質向上",
                "best_for": ["文体編集", "内容拡充", "可読性向上", "文章改善", "校正"],
                "keywords": ["編集", "改善", "修正", "校正", "文体", "読みやすく", "明確に", "洗練"]
            },
            "quality": {
                "description": "研究論文の品質評価・保証・学術基準チェック",
                "best_for": ["品質評価", "学術基準チェック", "倫理検証", "公開準備度評価", "査読準備"],
                "keywords": ["品質", "評価", "基準", "倫理", "学術", "公開", "準備", "査読", "適合性"]
            },
            "discovery": {
                "description": "研究ギャップ発見・新しいテーマ探索・関連研究調査",
                "best_for": ["ギャップ分析", "冗長性検出", "バランス分析", "新規テーマ発見", "関連研究探索"],
                "keywords": ["ギャップ", "不足", "足りない", "探索", "発見", "新しい", "関連", "競合", "類似", "重複"]
            },
            "generation": {
                "description": "新規コンテンツ生成・セクション作成・図表生成",
                "best_for": ["セクション生成", "内容拡充", "アウトライン生成", "引用生成", "図表生成", "結論生成"],
                "keywords": ["生成", "作成", "執筆", "書いて", "作って", "図", "表", "引用", "例", "結論", "まとめ"]
            },
            "strategy": {
                "description": "研究戦略立案・論証戦略・差別化戦略・影響力最大化",
                "best_for": ["研究戦略", "論証戦略", "差別化戦略", "リスク軽減", "影響力最大化", "公開戦略"],
                "keywords": ["戦略", "計画", "アプローチ", "方針", "差別化", "競争力", "影響", "リスク", "公開"]
            },
            "optimization": {
                "description": "研究効率・品質・リソース・時間・影響・コスト最適化",
                "best_for": ["効率最適化", "品質最適化", "リソース最適化", "時間最適化", "影響最適化", "コスト最適化"],
                "keywords": ["最適化", "効率", "改善", "向上", "短縮", "削減", "節約", "パフォーマンス", "リソース"]
            }
        }
    
    def _get_supported_task_types(self) -> List[str]:
        return [
            "analyze_intent",           # 意図解析
            "plan_workflow",           # ワークフロー計画
            "delegate_tasks",          # タスク委譲
            "supervise_execution",     # 実行監督
            "quality_control"          # 品質管理
        ]
    
    async def _execute_core(self, task: AgentTask) -> Any:
        """タスク実行"""
        task_type = task.parameters.get("task_type")
        
        if task_type == "analyze_intent":
            return await self._analyze_intent(task.parameters)
        elif task_type == "plan_workflow":
            return await self._plan_workflow(task.parameters)
        elif task_type == "delegate_tasks":
            return await self._delegate_tasks(task.parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _analyze_intent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """LLMベースの高度な意図解析"""
        user_message = params.get("user_message", "")
        paper_id = params.get("paper_id")
        
        if not user_message:
            raise AgentValidationError("user_message は必須です")
        
        try:
            logger.info(f"[SupervisorAgent] 意図解析開始: '{user_message[:50]}...'")
            
            # 既存セクション情報を取得（文脈として使用）
            sections_context = ""
            if paper_id and self.repository:
                sections = await self.repository.get_sections_by_paper(paper_id)
                if sections:
                    sections_list = [f"- {s.section_number}: {s.title}" for s in sections]
                    sections_context = f"\n\n既存セクション:\n" + "\n".join(sections_list)
            
            # LLMプロンプト構築
            system_prompt = """あなたは研究論文執筆支援システムのスーパーバイザーエージェントです。
ユーザーの要求を深く理解し、最適なタスク実行戦略を決定します。

利用可能なエージェント:
1. section_query: 既存セクションの検索・参照・内容取得
2. writer: 新しいコンテンツの生成・文章作成  
3. summary: 要約・概要作成
4. outline: 論文構造・アウトライン管理
5. logic_validator: 論理的整合性・品質チェック

あなたの役割:
- ユーザーの真の意図を理解する
- 既存の情報を活用すべきか、新規作成すべきかを判断
- 最適なエージェントとタスク順序を決定
- 品質とコンテキストを重視した判断

回答は以下のJSON形式で返してください:
{
    "intent_type": "query_existing|create_new|modify_existing|analyze_structure|general_help",
    "confidence": 0.0-1.0,
    "target_section": "セクション名またはnull",
    "primary_task": "主要タスクの説明",
    "recommended_agents": ["エージェント名のリスト"],
    "task_sequence": ["タスクの実行順序"],
    "reasoning": "判断理由の説明"
}"""
            
            user_prompt = f"""ユーザーの要求: "{user_message}"{sections_context}

このユーザー要求を分析し、最適な実行戦略を提案してください。
特に以下を考慮してください:
1. 既存セクションの活用可能性
2. 新規作成 vs 参照のどちらが適切か
3. タスクの複雑さと必要なエージェント
4. 実行順序の最適化"""
            
            # LLM呼び出し
            result = await openai_client.generate_text(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                model="gpt-4o-mini"
            )
            
            # JSON解析
            response_text = result.get("content", "").strip()
            try:
                # JSONブロックを抽出
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                intent_analysis = json.loads(json_text)
                
                logger.info(f"[SupervisorAgent] 意図解析完了: {intent_analysis.get('intent_type')} (信頼度: {intent_analysis.get('confidence', 0):.2f})")
                
                return {
                    "intent_analysis": intent_analysis,
                    "raw_response": response_text,
                    "sections_context": sections_context,
                    "action": "analyze_intent",
                    "success": True,
                    "message": f"意図「{intent_analysis.get('intent_type', 'unknown')}」を解析しました（信頼度: {intent_analysis.get('confidence', 0):.0%}）"
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"[SupervisorAgent] JSON解析失敗: {e}, フォールバック実行")
                
                # フォールバック: 従来のルールベース解析
                fallback_analysis = self._fallback_intent_analysis(user_message, sections_context)
                
                return {
                    "intent_analysis": fallback_analysis,
                    "raw_response": response_text,
                    "sections_context": sections_context,
                    "fallback_used": True,
                    "action": "analyze_intent",
                    "success": True,
                    "message": f"フォールバック分析: 意図「{fallback_analysis.get('intent_type', 'unknown')}」"
                }
                
        except Exception as e:
            logger.error(f"[SupervisorAgent] 意図解析エラー: {e}")
            raise AgentExecutionError(f"意図解析に失敗しました: {e}")
    
    def _fallback_intent_analysis(self, user_message: str, sections_context: str) -> Dict[str, Any]:
        """フォールバック: 従来のルールベース意図解析"""
        message_lower = user_message.lower()
        
        # セクション名検出
        common_sections = ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]
        target_section = None
        for section in common_sections:
            if section in message_lower:
                target_section = section.title()
                break
        
        # 意図タイプ決定
        if any(keyword in message_lower for keyword in ["教えて", "について", "見せて", "内容"]):
            if target_section:
                return {
                    "intent_type": "query_existing",
                    "confidence": 0.8,
                    "target_section": target_section,
                    "primary_task": f"「{target_section}」セクションの内容を取得・表示",
                    "recommended_agents": ["section_query"],
                    "task_sequence": ["セクション検索", "内容取得", "回答生成"],
                    "reasoning": "特定セクションに対する内容照会として解析"
                }
            else:
                return {
                    "intent_type": "general_help",
                    "confidence": 0.6,
                    "target_section": None,
                    "primary_task": "一般的な質問への対応",
                    "recommended_agents": ["summary"],
                    "task_sequence": ["情報整理", "回答生成"],
                    "reasoning": "一般的な質問として解析"
                }
        elif any(keyword in message_lower for keyword in ["作って", "書いて", "生成"]):
            return {
                "intent_type": "create_new",
                "confidence": 0.7,
                "target_section": target_section,
                "primary_task": "新しいコンテンツの作成",
                "recommended_agents": ["outline", "writer"],
                "task_sequence": ["アウトライン作成", "コンテンツ生成"],
                "reasoning": "新規作成要求として解析"
            }
        else:
            return {
                "intent_type": "general_help",
                "confidence": 0.5,
                "target_section": None,
                "primary_task": "一般的な要求処理",
                "recommended_agents": ["summary"],
                "task_sequence": ["状況分析", "適切な回答生成"],
                "reasoning": "明確な意図が特定できないため一般対応"
            }
    
    async def _plan_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロープランニング"""
        intent_analysis = params.get("intent_analysis", {})
        paper_id = params.get("paper_id")
        user_id = params.get("user_id")
        
        try:
            logger.info(f"[SupervisorAgent] ワークフロープランニング開始")
            
            # 意図に基づくタスク生成
            tasks = []
            intent_type = intent_analysis.get("intent_type", "general_help")
            target_section = intent_analysis.get("target_section")
            recommended_agents = intent_analysis.get("recommended_agents", [])
            
            if intent_type == "query_existing" and "section_query" in recommended_agents:
                tasks.append({
                    "agent": "section_query",
                    "task_type": "answer_section_query",
                    "description": f"セクション「{target_section}」の内容を回答",
                    "parameters": {
                        "paper_id": paper_id,
                        "target_section": target_section,
                        "question": params.get("user_message", "")
                    },
                    "priority": "high"
                })
            
            elif intent_type == "create_new":
                if "outline" in recommended_agents:
                    tasks.append({
                        "agent": "outline",
                        "task_type": "create_section",
                        "description": f"新しいセクション「{target_section or '新規セクション'}」を作成",
                        "parameters": {
                            "paper_id": paper_id,
                            "user_id": user_id,
                            "title": target_section or "新しいセクション"
                        },
                        "priority": "high"
                    })
                
                if "writer" in recommended_agents:
                    tasks.append({
                        "agent": "writer",
                        "task_type": "generate_draft",
                        "description": f"セクション「{target_section or '新規セクション'}」のコンテンツを生成",
                        "parameters": {
                            "section_title": target_section or "新しいセクション",
                            "paper_id": paper_id,
                            "requirements": "学術的で論理的な内容"
                        },
                        "priority": "medium"
                    })
            
            elif intent_type == "analyze_structure":
                # 構造分析・問題点分析の場合
                # 推奨エージェントに関わらず、analysisエージェントを使用
                tasks.append({
                    "agent": "analysis",
                    "task_type": "critical_analysis",
                    "description": "論文全体の構造・問題点・改善点を分析",
                    "parameters": {
                        "paper_id": paper_id,
                        "analysis_focus": params.get("user_message", "全体的な問題点"),
                        "sections": "all"
                    },
                    "priority": "high"
                })
                
                # 品質評価も追加で実行
                tasks.append({
                    "agent": "quality",
                    "task_type": "quality_assessment",
                    "description": "論文の品質評価と改善提案",
                    "parameters": {
                        "paper_id": paper_id,
                        "assessment_criteria": ["academic_rigor", "methodological_soundness", "clarity", "contribution"],
                        "evaluation_depth": "comprehensive"
                    },
                    "priority": "medium"
                })
            
            elif intent_type == "general_help":
                tasks.append({
                    "agent": "summary",
                    "task_type": "create_paper_summary",
                    "description": "論文の現状を要約・説明",
                    "parameters": {
                        "paper_id": paper_id,
                        "summary_type": "brief",
                        "requirements": params.get("user_message", "")
                    },
                    "priority": "medium"
                })
            
            return {
                "workflow_plan": {
                    "intent_type": intent_type,
                    "tasks": tasks,
                    "estimated_duration": len(tasks) * 15,  # 推定実行時間（秒）
                    "parallel_execution": len(tasks) == 1,  # 単一タスクは並列不要
                    "quality_checks": intent_type in ["create_new", "modify_existing"]
                },
                "reasoning": intent_analysis.get("reasoning", ""),
                "confidence": intent_analysis.get("confidence", 0.5),
                "action": "plan_workflow",
                "success": True,
                "message": f"{len(tasks)}個のタスクを含むワークフローを計画しました"
            }
            
        except Exception as e:
            logger.error(f"[SupervisorAgent] ワークフロープランニングエラー: {e}")
            raise AgentExecutionError(f"ワークフロープランニングに失敗しました: {e}")