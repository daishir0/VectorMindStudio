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
from app.infrastructure.repositories.agent_repository import AgentRepository
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
    
    def __init__(self, session=None, user_id=None):
        super().__init__(
            name="SupervisorAgent",
            description="LLMベースの高次タスク推論・エージェント管理を行うスーパーバイザー",
            max_retries=2,
            timeout=settings.AI_AGENT_TIMEOUT_SECONDS
        )
        self.session = session
        self.user_id = user_id
        self.repository = PaperRepository(session) if session else None
        self.agent_repository = AgentRepository(session) if session else None

        # エージェント能力のメタ知識（DBから動的に読み込み）
        self.agent_capabilities = {}
        self._agent_capabilities_loaded = False
    
    def _get_supported_task_types(self) -> List[str]:
        return [
            "analyze_intent",           # 意図解析
            "plan_workflow",           # ワークフロー計画
            "delegate_tasks",          # タスク委譲
            "supervise_execution",     # 実行監督
            "quality_control"          # 品質管理
        ]

    async def _load_agent_capabilities_from_db(self, user_id: Optional[str] = None):
        """DBからエージェント能力のメタ知識を動的に読み込み"""
        if self._agent_capabilities_loaded:
            return

        if not self.agent_repository:
            logger.warning("[SupervisorAgent] AgentRepositoryが未設定のため、エージェント能力を読み込めません")
            return

        try:
            # user_idを使用（引数優先、次にインスタンス変数）
            effective_user_id = user_id or self.user_id

            # DBからアクティブなエージェント一覧を取得
            agents = await self.agent_repository.get_active_agents(user_id=effective_user_id)

            logger.info(f"[SupervisorAgent] {len(agents)}個のアクティブエージェントを読み込みました")

            # エージェント名の正規化マッピング（既存コードとの互換性維持）
            # 例: "DiscoveryAgent" -> "discovery"
            name_mappings = {
                "DiscoveryAgent": "discovery",
                "WriterAgent": "writer",
                "SectionQueryAgent": "section_query",
                "SummaryAgent": "summary",
                "OutlineAgent": "outline",
                "LogicValidatorAgent": "logic_validator",
                "AnalysisAgent": "analysis",
                "EditingAgent": "editing",
                "QualityAgent": "quality",
                "GenerationAgent": "generation",
                "StrategyAgent": "strategy",
                "OptimizationAgent": "optimization",
                "StructureAgent": "structure"
            }

            for agent in agents:
                # エージェント名を正規化
                normalized_name = name_mappings.get(agent.name, agent.name.lower())

                # wake_wordsとcapabilitiesはeager loadされている
                wake_words = agent.wake_words if hasattr(agent, 'wake_words') else []
                capabilities = agent.capabilities if hasattr(agent, 'capabilities') else []

                # エージェント能力辞書を構築
                self.agent_capabilities[normalized_name] = {
                    "description": agent.description,
                    "best_for": [cap.description for cap in capabilities] if capabilities else [],
                    "keywords": [ww.keyword for ww in wake_words] if wake_words else [],
                    "agent_id": agent.id,
                    "display_name": agent.display_name,
                    "priority": agent.priority
                }

            self._agent_capabilities_loaded = True
            logger.info(f"[SupervisorAgent] エージェント能力メタ知識の読み込み完了: {len(self.agent_capabilities)}個")

        except Exception as e:
            logger.error(f"[SupervisorAgent] エージェント能力の読み込みエラー: {e}", exc_info=True)
            # エラー時はフォールバック：空の辞書を使用
            self.agent_capabilities = {}
    
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
        user_id = params.get("user_id")

        if not user_message:
            raise AgentValidationError("user_message は必須です")

        try:
            # DBからエージェント能力を動的に読み込み
            await self._load_agent_capabilities_from_db(user_id=user_id)

            logger.info(f"[SupervisorAgent] 意図解析開始: '{user_message[:50]}...'")

            # 既存セクション情報を取得（文脈として使用）
            sections_context = ""
            if paper_id and self.repository:
                sections = await self.repository.get_sections_by_paper(paper_id)
                if sections:
                    sections_list = [f"- {s.section_number}: {s.title}" for s in sections]
                    sections_context = f"\n\n既存セクション:\n" + "\n".join(sections_list)

            # 利用可能なエージェント一覧を動的に構築
            available_agents_text = ""
            if self.agent_capabilities:
                agent_list = []
                for i, (agent_key, agent_info) in enumerate(self.agent_capabilities.items(), 1):
                    agent_list.append(f"{i}. {agent_key}: {agent_info['description']}")
                available_agents_text = "\n".join(agent_list)
            else:
                # フォールバック：基本エージェントのみ
                available_agents_text = """1. discovery: ChromaDB検索・研究ギャップ発見・関連研究調査 【重要】
2. writer: 新しいコンテンツの生成・文章作成
3. section_query: 既存セクションの検索・参照・内容取得
4. summary: 要約・概要作成
5. outline: 論文構造・アウトライン管理
6. analysis: 研究論文の深度分析・批判的評価・構造解析
7. editing: 研究論文の編集・改善・文章品質向上
8. quality: 研究論文の品質評価・保証・学術基準チェック
9. generation: 新規コンテンツ生成・セクション作成・図表生成
10. strategy: 研究戦略立案・論証戦略・差別化戦略
11. optimization: 研究効率・品質・リソース最適化
12. logic_validator: 論理的整合性・品質チェック
13. structure: 論文構造の最適化・IMRAD形式等への変換・セクション並び替え 【重要】"""

            # LLMプロンプト構築
            system_prompt = f"""あなたは研究論文執筆支援システムのスーパーバイザーエージェントです。
ユーザーの要求を深く理解し、最適なタスク実行戦略を決定します。

利用可能なエージェント:
{available_agents_text}

【重要な判断基準】
- ユーザーが「ChromaDBから検索」「資料を検索」「関連研究」等を要求した場合は、必ずdiscoveryエージェントを使用してください
- 新規コンテンツ作成時も、まずdiscoveryで関連情報を検索してからwriterで執筆するのが望ましいです
- ユーザーが具体的な人物名・概念・テーマを指定した場合は、discoveryで資料検索してから執筆してください

【Intent Type の判断基準】
1. query_existing: 「教えて」「見せて」「内容は？」など既存情報への質問
2. create_new: 「作って」「執筆して」など完全に新しいセクションの作成
3. modify_existing: 「加筆」「詳しく」「さらに」「追加」「改善」など既存コンテンツの修正・拡充 【重要】
4. analyze_structure: 「分析」「問題点」「チェック」など論文構造の評価
5. search_and_create: ChromaDB検索が必要で、かつ新規セクション作成の場合
6. restructure: 「IMRAD形式」「構造を整理」「章節を並び替え」など論文構造の最適化 【重要】
7. general_help: その他の一般的な質問・サポート

あなたの役割:
- ユーザーの真の意図を理解する
- ChromaDB検索が必要かを判断する（重要！）
- 既存の情報を活用すべきか、新規作成すべきかを判断
- 最適なエージェントとタスク順序を決定
- 品質とコンテキストを重視した判断

回答は以下のJSON形式で返してください:
{{
    "intent_type": "query_existing|create_new|modify_existing|analyze_structure|search_and_create|restructure|general_help",
    "confidence": 0.0-1.0,
    "target_section": "セクション名またはnull",
    "primary_task": "主要タスクの説明",
    "recommended_agents": ["エージェント名のリスト"],
    "task_sequence": ["タスクの実行順序"],
    "reasoning": "判断理由の説明"
}}"""
            
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

        # ChromaDB検索 + セクション作成の判定（最優先）
        has_search_keywords = any(keyword in message_lower for keyword in ["chromadb", "検索", "探して", "資料", "文献", "関連研究"])
        has_create_keywords = any(keyword in message_lower for keyword in ["作って", "作成", "書いて", "生成", "執筆"])

        if has_search_keywords and has_create_keywords:
            return {
                "intent_type": "search_and_create",
                "confidence": 0.9,
                "target_section": target_section,
                "primary_task": "ChromaDBで資料検索してセクション作成",
                "recommended_agents": ["discovery", "writer"],
                "task_sequence": ["ChromaDB検索", "コンテンツ生成", "セクション作成"],
                "reasoning": "ChromaDB検索とセクション作成の両方を含むため"
            }

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
        elif has_create_keywords:
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
            
            elif intent_type == "search_and_create" or (intent_type == "create_new" and "discovery" in recommended_agents):
                # ChromaDB検索 + 新規作成のワークフロー
                user_message = params.get("user_message", "")

                # 1. まずDiscoveryAgentでChromatDB検索
                tasks.append({
                    "agent": "discovery",
                    "task_type": "search_chromadb",
                    "description": f"ChromaDBから「{user_message[:50]}...」に関連する資料を検索",
                    "parameters": {
                        "paper_id": paper_id,
                        "query": user_message,
                        "search_type": "semantic",
                        "max_results": 10
                    },
                    "priority": "high"
                })

                # 2. 検索結果をもとにWriterAgentがコンテンツ生成
                tasks.append({
                    "agent": "writer",
                    "task_type": "generate_draft",
                    "description": f"セクション「{target_section or '新規セクション'}」のコンテンツを生成（ChromaDB検索結果を活用）",
                    "parameters": {
                        "section_title": target_section or "新規セクション",
                        "paper_id": paper_id,
                        "requirements": user_message  # ユーザーの具体的な要求を渡す
                    },
                    "priority": "medium"
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
                    user_message = params.get("user_message", "")
                    tasks.append({
                        "agent": "writer",
                        "task_type": "generate_draft",
                        "description": f"セクション「{target_section or '新規セクション'}」のコンテンツを生成",
                        "parameters": {
                            "section_title": target_section or "新しいセクション",
                            "paper_id": paper_id,
                            "requirements": user_message if user_message else "学術的で論理的な内容"
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
            
            elif intent_type == "modify_existing":
                # 既存コンテンツの修正・加筆・改善の場合
                user_message = params.get("user_message", "")

                # ユーザーが具体的な人物名・概念・テーマに言及している場合、ChromaDB検索を先行
                if any(keyword in user_message for keyword in ["戸田城聖", "思想", "エピソード", "詳しく", "加筆", "追加", "について"]):
                    tasks.append({
                        "agent": "discovery",
                        "task_type": "search_chromadb",
                        "description": f"ChromaDBから「{user_message[:50]}...」に関連する資料を検索",
                        "parameters": {
                            "paper_id": paper_id,
                            "query": user_message,
                            "search_type": "semantic",
                            "max_results": 10
                        },
                        "priority": "high"
                    })

                # Editingエージェントで既存コンテンツを改善
                tasks.append({
                    "agent": "editing",
                    "task_type": "content_enhancement",
                    "description": f"既存コンテンツを「{user_message[:50]}...」に基づいて改善",
                    "parameters": {
                        "paper_id": paper_id,
                        "target_section": target_section,
                        "requirements": user_message,
                        "modification_type": "expand"  # expand, refine, clarify等
                    },
                    "priority": "medium"
                })

            elif intent_type == "restructure":
                # 論文構造の最適化の場合
                user_message = params.get("user_message", "")

                # 事前チェック: セクション数を確認
                sections = []
                if paper_id and self.repository:
                    sections = await self.repository.get_sections_by_paper(paper_id)

                if len(sections) == 0:
                    # セクションが0個の場合は、ユーザーフレンドリーなメッセージを返す
                    # 構造最適化はセクションがある場合にのみ有効
                    # 特別なタスクとして、メッセージのみを返すタスクを作成
                    tasks.append({
                        "agent": "summary",
                        "task_type": "create_paper_summary",
                        "description": "空の論文への適切なガイダンスを提供",
                        "parameters": {
                            "paper_id": paper_id,
                            "summary_type": "empty_paper_guidance",
                            "custom_message": "現在、論文にはまだセクションがありません。\n\n論文構造を整理・最適化するには、まず以下のいずれかの方法でコンテンツを作成してください：\n\n1. **新しいセクションを作成する**\n   例：「Introductionセクションを作成して」\n\n2. **具体的なテーマでコンテンツを生成する**\n   例：「〇〇について書いて」\n\n3. **アウトラインから始める**\n   例：「〇〇についての論文アウトラインを作成して」\n\nコンテンツが作成された後、構造の最適化やIMRAD形式への変換などをサポートいたします。"
                        },
                        "priority": "high"
                    })
                else:
                    # セクションが1個以上ある場合のみ、StructureAgentで構造最適化
                    # StructureAgentで構造分析
                    tasks.append({
                        "agent": "structure",
                        "task_type": "analyze_structure",
                        "description": "現在の論文構造を分析",
                        "parameters": {
                            "paper_id": paper_id
                        },
                        "priority": "high"
                    })

                    # StructureAgentで構造改善提案
                    tasks.append({
                        "agent": "structure",
                        "task_type": "suggest_restructure",
                        "description": f"「{user_message[:50]}...」に基づく構造改善を提案",
                        "parameters": {
                            "paper_id": paper_id,
                            "requirements": user_message,
                            "target_format": self._extract_format_from_message(user_message)
                        },
                        "priority": "high"
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

    def _extract_format_from_message(self, message: str) -> Optional[str]:
        """メッセージから目標フォーマットを抽出"""
        message_lower = message.lower()

        if "起承転結" in message or "きしょうてんけつ" in message:
            return "kishoutenketsu"
        elif "imrad" in message_lower or ("introduction" in message_lower and "methods" in message_lower):
            return "imrad"
        elif "時系列" in message or "chronological" in message_lower:
            return "chronological"
        elif "問題解決" in message or "problem" in message_lower:
            return "problem_solution"
        elif "主題" in message or "thematic" in message_lower:
            return "thematic"
        else:
            return None