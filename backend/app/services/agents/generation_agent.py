"""
GenerationAgent - 研究論文のコンテンツ生成・拡張エージェント

研究論文の新規コンテンツ生成、既存内容の拡張、構造的改善を行う。
AI駆動によるコンテンツ作成、アウトライン生成、セクション拡充をサポート。
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from app.services.agents.base_agent import AgentExecutionError, AgentTask, AgentResult
from app.services.agents.enhanced_base_agent import EnhancedBaseAgent, ExecutionMetrics
from app.infrastructure.external.openai_client import openai_client


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """生成結果"""
    generated_content: str
    content_type: str
    quality_score: float
    word_count: int
    sections_generated: List[str]
    citations_added: int
    generation_confidence: float
    refinement_suggestions: List[str]


class GenerationAgent(EnhancedBaseAgent):
    """
    研究論文コンテンツ生成・拡張エージェント
    
    主要機能：
    1. セクション生成: 新規セクションの作成
    2. 内容拡充: 既存セクションの拡張・詳細化
    3. アウトライン生成: 論文構造の作成
    4. 引用生成: 適切な引用の生成・挿入
    5. 例示生成: 具体例・事例の作成
    6. 図表生成: 図表の構想・説明生成
    7. 結論生成: 結論・要約の生成
    8. 統合生成: 複数セクションの統合的生成
    """
    
    def __init__(self, session=None):
        super().__init__(session=session, timeout=30)
        self.agent_version = "1.0.0"
        self.cache_ttl_seconds = 1200  # 20分キャッシュ
        
        # タスクタイプ定義
        self.task_definitions = {
            "section_generation": "新規セクションの生成",
            "content_expansion": "既存内容の拡張・詳細化",
            "outline_generation": "論文アウトライン・構造の生成",
            "citation_generation": "適切な引用の生成・挿入",
            "example_generation": "具体例・事例の生成",
            "figure_table_generation": "図表の構想・説明生成",
            "conclusion_generation": "結論・要約の生成",
            "integrated_generation": "統合的コンテンツ生成"
        }
        
        # 生成コンテンツタイプ定義
        self.content_types = {
            "introduction": "導入・序論",
            "literature_review": "文献レビュー",
            "methodology": "研究方法",
            "results": "結果・分析",
            "discussion": "考察・議論",
            "conclusion": "結論・まとめ",
            "abstract": "要約・抄録",
            "background": "背景・関連研究"
        }
        
        # 生成品質基準
        self.quality_criteria = [
            "academic_rigor",      # 学術的厳密性
            "logical_coherence",   # 論理的一貫性
            "content_depth",       # 内容の深度
            "clarity_readability", # 明確性・可読性
            "originality",         # 独創性
            "evidence_support",    # 証拠に基づく論証
            "structural_integrity",# 構造的整合性
            "citation_appropriateness" # 引用の適切性
        ]

    @property
    def supported_tasks(self) -> List[str]:
        """サポートされるタスクタイプのリスト"""
        return list(self.task_definitions.keys())

    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters or {}
        
        if task_type == "section_generation":
            return await self._perform_section_generation(parameters, metrics)
        elif task_type == "content_expansion":
            return await self._perform_content_expansion(parameters, metrics)
        elif task_type == "outline_generation":
            return await self._perform_outline_generation(parameters, metrics)
        elif task_type == "citation_generation":
            return await self._perform_citation_generation(parameters, metrics)
        elif task_type == "example_generation":
            return await self._perform_example_generation(parameters, metrics)
        elif task_type == "figure_table_generation":
            return await self._perform_figure_table_generation(parameters, metrics)
        elif task_type == "conclusion_generation":
            return await self._perform_conclusion_generation(parameters, metrics)
        elif task_type == "integrated_generation":
            return await self._perform_integrated_generation(parameters, metrics)
        else:
            raise AgentExecutionError(f"サポートされていないタスクタイプ: {task_type}")

    async def execute_task(
        self, 
        task_type: str, 
        section_id: str, 
        content: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        コンテンツ生成タスクの実行
        
        Args:
            task_type: 実行するタスクの種類
            section_id: 対象セクションID
            content: 基となるコンテンツ（空の場合は新規生成）
            parameters: 追加パラメータ（生成要件、文字数制限等）
            
        Returns:
            AgentResult: 生成結果
        """
        try:
            metrics = ExecutionMetrics()
            
            if task_type not in self.supported_tasks:
                raise AgentExecutionError(f"サポートされていないタスクタイプ: {task_type}")
            
            # パラメータの準備
            params = {
                "section_id": section_id,
                "content": content,
                "task_type": task_type,
                **(parameters or {})
            }
            
            # タスク実行
            result = await self._execute_generation_task(task_type, params, metrics)
            
            return AgentResult(
                agent_name=self.agent_name,
                task_type=task_type,
                status="success",
                result=result,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"GenerationAgentタスク実行エラー - {task_type}: {e}")
            return AgentResult(
                agent_name=self.agent_name,
                task_type=task_type,
                status="error",
                error=str(e),
                metrics=metrics,
                timestamp=datetime.utcnow()
            )

    async def _execute_generation_task(
        self, 
        task_type: str, 
        params: Dict[str, Any], 
        metrics: ExecutionMetrics
    ) -> Dict[str, Any]:
        """コンテンツ生成タスクの実行"""
        
        task_methods = {
            "section_generation": self._perform_section_generation,
            "content_expansion": self._perform_content_expansion,
            "outline_generation": self._perform_outline_generation,
            "citation_generation": self._perform_citation_generation,
            "example_generation": self._perform_example_generation,
            "figure_table_generation": self._perform_figure_table_generation,
            "conclusion_generation": self._perform_conclusion_generation,
            "integrated_generation": self._perform_integrated_generation
        }
        
        method = task_methods.get(task_type)
        if not method:
            raise AgentExecutionError(f"未実装のタスクタイプ: {task_type}")
            
        return await method(params, metrics)

    async def _perform_section_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """新規セクションの生成"""
        try:
            section_id = params["section_id"]
            content_type = params.get("content_type", "general")
            requirements = params.get("requirements", "")
            word_count = params.get("word_count", 800)
            research_topic = params.get("research_topic", "")
            
            # キャッシュキー生成
            cache_key = self._generate_cache_key(section_id, "section_generation", content_type, requirements + research_topic)
            
            # キャッシュチェック
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の新規セクションを生成してください。

【セクション情報】
- セクションID: {section_id}
- セクションタイプ: {content_type}
- 研究トピック: {research_topic}

【生成要件】
{requirements}

【文字数指定】
約{word_count}文字

【生成指示】
以下の観点から高品質なセクションを生成し、JSON形式で回答してください：

1. **学術的厳密性**: 学術論文として適切な表現・構造
2. **論理的一貫性**: 明確な論理展開と一貫性
3. **内容の深度**: 十分な深度と専門性
4. **明確性**: 読みやすく理解しやすい表現
5. **独創性**: オリジナルな視点・アプローチ
6. **証拠支持**: 論拠に基づいた論証
7. **構造的整合**: 適切な段落構成・流れ
8. **引用適切性**: 適切な引用の想定・配置

{{
    "generated_content": "生成されたセクション内容（Markdown形式）",
    "section_structure": {{
        "main_sections": [
            {{
                "title": "セクション見出し",
                "content_summary": "内容要約",
                "key_points": ["主要ポイント"]
            }}
        ],
        "subsections": [
            {{
                "title": "サブセクション見出し",
                "content_summary": "内容要約",
                "purpose": "目的・役割"
            }}
        ]
    }},
    "quality_assessment": {{
        "academic_rigor": 0.0-1.0,
        "logical_coherence": 0.0-1.0,
        "content_depth": 0.0-1.0,
        "clarity": 0.0-1.0,
        "originality": 0.0-1.0,
        "evidence_support": 0.0-1.0,
        "structural_integrity": 0.0-1.0,
        "citation_readiness": 0.0-1.0
    }},
    "content_statistics": {{
        "estimated_word_count": 推定文字数,
        "paragraph_count": 段落数,
        "citation_placeholders": 引用プレースホルダー数,
        "technical_terms": ["専門用語リスト"]
    }},
    "improvement_suggestions": [
        {{
            "aspect": "改善対象",
            "suggestion": "具体的改善提案",
            "priority": "high|medium|low"
        }}
    ],
    "overall_quality_score": 0.0-1.0,
    "generation_confidence": 0.0-1.0
}}
"""
            
            # OpenAI API呼び出し
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "section_generation",
                "section_id": section_id,
                "content_type": content_type,
                "requirements": requirements,
                "word_count_target": word_count,
                "generated_result": result_data,
                "actual_word_count": result_data.get("content_statistics", {}).get("estimated_word_count", 0),
                "quality_score": result_data.get("overall_quality_score", 0.0),
                "generation_confidence": result_data.get("generation_confidence", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"セクション生成エラー: {e}")

    async def _perform_content_expansion(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """既存内容の拡張・詳細化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            expansion_type = params.get("expansion_type", "detail")
            expansion_ratio = params.get("expansion_ratio", 1.5)
            focus_areas = params.get("focus_areas", [])
            
            cache_key = self._generate_cache_key(section_id, "content_expansion", expansion_type, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            focus_areas_str = ", ".join(focus_areas) if focus_areas else "全般的な拡張"
            
            prompt = f"""
既存の研究論文内容を拡張・詳細化してください。

【既存内容】
{content}

【拡張タイプ】
{expansion_type}

【拡張倍率】
約{expansion_ratio}倍

【重点拡張領域】
{focus_areas_str}

【拡張指示】
以下の観点から既存内容を適切に拡張し、JSON形式で回答してください：

1. **詳細化**: より詳細な説明・分析の追加
2. **具体化**: 具体例・事例の挿入
3. **理論強化**: 理論的基盤の補強
4. **実証強化**: 実証的証拠の追加
5. **比較分析**: 比較・対比の拡張
6. **批判的検討**: 批判的視点の追加
7. **関連性拡張**: 関連研究・分野との接続
8. **応用可能性**: 実用・応用面の拡充

{{
    "expanded_content": "拡張された内容（Markdown形式）",
    "expansion_analysis": {{
        "original_length": 元の推定文字数,
        "expanded_length": 拡張後推定文字数,
        "expansion_ratio": 実際の拡張倍率,
        "expansion_areas": [
            {{
                "area": "拡張した領域",
                "type": "詳細化|具体化|理論強化|実証強化|比較分析|批判検討|関連拡張|応用拡充",
                "content_added": "追加内容の要約",
                "rationale": "拡張理由"
            }}
        ]
    }},
    "content_improvements": [
        {{
            "improvement_type": "改善の種類",
            "description": "改善内容の詳細",
            "impact": "改善による影響",
            "quality_enhancement": 0.0-1.0
        }}
    ],
    "structural_enhancements": {{
        "new_subsections": ["追加されたサブセクション"],
        "enhanced_transitions": "文章間の接続改善",
        "logical_flow_improvement": "論理的流れの改善"
    }},
    "quality_metrics": {{
        "content_depth": 0.0-1.0,
        "academic_rigor": 0.0-1.0,
        "coherence": 0.0-1.0,
        "readability": 0.0-1.0,
        "evidence_strength": 0.0-1.0
    }},
    "expansion_success_score": 0.0-1.0,
    "refinement_suggestions": [
        "さらなる改善提案"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "content_expansion",
                "section_id": section_id,
                "expansion_type": expansion_type,
                "target_expansion_ratio": expansion_ratio,
                "focus_areas": focus_areas,
                "expansion_result": result_data,
                "actual_expansion_ratio": result_data.get("expansion_analysis", {}).get("expansion_ratio", 1.0),
                "expansion_success_score": result_data.get("expansion_success_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"内容拡張エラー: {e}")

    async def _perform_outline_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """論文アウトライン・構造の生成"""
        try:
            research_topic = params.get("research_topic", "")
            research_type = params.get("research_type", "empirical")
            target_length = params.get("target_length", "standard")
            special_requirements = params.get("special_requirements", "")
            
            cache_key = self._generate_cache_key("outline", "outline_generation", research_type, research_topic)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の包括的なアウトライン・構造を生成してください。

【研究トピック】
{research_topic}

【研究タイプ】
{research_type}

【論文規模】
{target_length}

【特別要件】
{special_requirements}

【生成指示】
以下の観点から研究論文の詳細なアウトラインを生成し、JSON形式で回答してください：

1. **構造設計**: 論理的で一貫性のある構造
2. **セクション配分**: 適切な分量・重要度配分
3. **内容企画**: 各セクションの具体的内容計画
4. **流れ設計**: セクション間の論理的接続
5. **深度設計**: 各部分の分析深度計画
6. **証拠配置**: 実証・論拠の適切な配置
7. **引用計画**: 引用の戦略的配置計画
8. **読者配慮**: 読者理解を促進する構造

{{
    "paper_structure": {{
        "title": "論文タイトル（提案）",
        "abstract": {{
            "length": "150-200語",
            "key_components": ["研究背景", "方法", "主要結果", "結論"],
            "writing_approach": "アプローチ方針"
        }},
        "main_sections": [
            {{
                "section_number": "セクション番号",
                "title": "セクションタイトル",
                "purpose": "セクションの目的・役割",
                "key_content": ["主要な内容要素"],
                "subsections": [
                    {{
                        "title": "サブセクションタイトル",
                        "content_plan": "内容計画",
                        "estimated_length": "推定文字数"
                    }}
                ],
                "estimated_length": "推定総文字数",
                "critical_elements": ["必須要素"],
                "connection_to_next": "次セクションとの接続"
            }}
        ]
    }},
    "structural_rationale": {{
        "organization_logic": "構造化の論理・根拠",
        "flow_design": "論理的流れの設計意図",
        "emphasis_strategy": "重点配置戦略",
        "reader_journey": "読者の理解プロセス設計"
    }},
    "content_distribution": {{
        "introduction_ratio": "導入部の比率",
        "methodology_ratio": "方法論部の比率", 
        "results_ratio": "結果部の比率",
        "discussion_ratio": "考察部の比率",
        "conclusion_ratio": "結論部の比率",
        "total_estimated_length": "総推定文字数"
    }},
    "writing_strategy": {{
        "citation_strategy": "引用戦略",
        "evidence_placement": "証拠配置計画",
        "argumentation_flow": "論証の流れ",
        "critical_analysis_points": ["批判的分析ポイント"]
    }},
    "quality_considerations": [
        {{
            "aspect": "品質考慮事項",
            "strategy": "対応戦略",
            "success_metrics": "成功指標"
        }}
    ],
    "outline_completeness": 0.0-1.0,
    "structural_soundness": 0.0-1.0,
    "implementation_guidance": [
        "実装時のガイダンス"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "outline_generation",
                "research_topic": research_topic,
                "research_type": research_type,
                "target_length": target_length,
                "outline_result": result_data,
                "sections_count": len(result_data.get("paper_structure", {}).get("main_sections", [])),
                "estimated_total_length": result_data.get("content_distribution", {}).get("total_estimated_length", "unknown"),
                "outline_completeness": result_data.get("outline_completeness", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"アウトライン生成エラー: {e}")

    async def _perform_citation_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """適切な引用の生成・挿入"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            citation_style = params.get("citation_style", "APA")
            research_field = params.get("research_field", "general")
            
            cache_key = self._generate_cache_key(section_id, "citation_generation", citation_style, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、適切な引用を生成・挿入してください。

【対象内容】
{content}

【引用スタイル】
{citation_style}

【研究分野】
{research_field}

【引用生成指示】
以下の観点から適切な引用を生成・提案し、JSON形式で回答してください：

1. **引用必要箇所**: 引用が必要な箇所の特定
2. **引用タイプ**: 各箇所に適した引用タイプ
3. **引用戦略**: 論証を強化する引用配置
4. **信頼性確保**: 信頼できる情報源の想定
5. **バランス配慮**: 支持・批判的引用のバランス
6. **新しさ考慮**: 最新研究と古典的研究の組み合わせ
7. **多様性確保**: 多様な視点・研究者の包含
8. **適切性検証**: 内容と引用の適合性

{{
    "citation_analysis": {{
        "citation_needs": [
            {{
                "location": "引用が必要な箇所",
                "content_excerpt": "該当内容の抜粋",
                "citation_purpose": "引用の目的",
                "citation_type": "direct_quote|paraphrase|summary|statistical|theoretical",
                "priority": "high|medium|low",
                "rationale": "引用が必要な理由"
            }}
        ],
        "overall_citation_density": "適切な引用密度の評価"
    }},
    "suggested_citations": [
        {{
            "insertion_point": "挿入箇所",
            "citation_text": "引用テキスト（{citation_style}形式）",
            "source_type": "journal_article|book|conference|report|online",
            "source_description": {{
                "title": "想定される文献タイトル",
                "authors": ["想定著者名"],
                "publication_year": "想定発行年",
                "journal_or_publisher": "想定掲載誌・出版社",
                "relevance_explanation": "関連性の説明"
            }},
            "citation_strength": 0.0-1.0,
            "alternatives": ["代替的な引用オプション"]
        }}
    ],
    "enhanced_content": "引用を挿入した改良版内容",
    "citation_strategy": {{
        "overall_approach": "全体的な引用戦略",
        "balance_assessment": "引用バランスの評価",
        "credibility_enhancement": "信頼性向上への寄与",
        "argumentation_support": "論証強化への寄与"
    }},
    "quality_metrics": {{
        "citation_appropriateness": 0.0-1.0,
        "source_diversity": 0.0-1.0,
        "temporal_balance": 0.0-1.0,
        "credibility_score": 0.0-1.0
    }},
    "recommendations": [
        "引用改善のための提案"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1800)
            result_data = json.loads(response)
            
            result = {
                "task_type": "citation_generation",
                "section_id": section_id,
                "citation_style": citation_style,
                "research_field": research_field,
                "citation_result": result_data,
                "citations_suggested": len(result_data.get("suggested_citations", [])),
                "citation_needs_count": len(result_data.get("citation_analysis", {}).get("citation_needs", [])),
                "overall_credibility_score": result_data.get("quality_metrics", {}).get("credibility_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"引用生成エラー: {e}")

    async def _perform_example_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """具体例・事例の生成"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            example_type = params.get("example_type", "illustrative")
            examples_count = params.get("examples_count", 3)
            
            cache_key = self._generate_cache_key(section_id, "example_generation", example_type, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、適切な具体例・事例を生成してください。

【対象内容】
{content}

【例示タイプ】
{example_type}

【例示数】
{examples_count}個

【例示生成指示】
以下の観点から効果的な具体例・事例を生成し、JSON形式で回答してください：

1. **説明力**: 概念・理論の理解を促進する例示
2. **関連性**: 内容と密接に関連する事例
3. **具体性**: 具体的で理解しやすい事例
4. **多様性**: 異なる角度・領域からの例示
5. **現実性**: 現実的で説得力のある事例
6. **教育性**: 読者の学習を促進する事例
7. **記憶性**: 印象に残りやすい事例
8. **応用性**: 応用・拡張しやすい事例

{{
    "generated_examples": [
        {{
            "example_title": "例示のタイトル",
            "example_type": "case_study|illustration|analogy|scenario|comparison|application",
            "description": "具体例の詳細説明",
            "context": "例示の背景・文脈",
            "key_points": [
                {{
                    "point": "重要ポイント",
                    "explanation": "ポイントの説明",
                    "connection_to_theory": "理論との接続"
                }}
            ],
            "learning_value": "この例示から学べること",
            "applicability": "他への応用可能性",
            "memorability_score": 0.0-1.0,
            "clarity_score": 0.0-1.0
        }}
    ],
    "integration_suggestions": [
        {{
            "insertion_point": "挿入箇所の提案",
            "integration_method": "統合方法",
            "transition_text": "接続文の提案",
            "expected_impact": "期待される効果"
        }}
    ],
    "example_effectiveness": {{
        "conceptual_clarity": 0.0-1.0,
        "engagement_level": 0.0-1.0,
        "educational_value": 0.0-1.0,
        "diversity_score": 0.0-1.0
    }},
    "enhanced_content": "例示を統合した改良版内容",
    "example_strategy": {{
        "overall_approach": "例示戦略",
        "progression_logic": "例示の配置・進行論理",
        "reader_engagement": "読者エンゲージメント戦略"
    }},
    "alternatives": [
        {{
            "alternative_example": "代替例示の概要",
            "use_case": "使用場面・条件",
            "advantages": "利点"
        }}
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1800)
            result_data = json.loads(response)
            
            result = {
                "task_type": "example_generation",
                "section_id": section_id,
                "example_type": example_type,
                "target_examples_count": examples_count,
                "example_result": result_data,
                "examples_generated": len(result_data.get("generated_examples", [])),
                "average_clarity_score": sum([ex.get("clarity_score", 0.0) for ex in result_data.get("generated_examples", [])]) / max(len(result_data.get("generated_examples", [])), 1),
                "educational_value": result_data.get("example_effectiveness", {}).get("educational_value", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"例示生成エラー: {e}")

    async def _perform_figure_table_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """図表の構想・説明生成"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            figure_type = params.get("figure_type", "conceptual")
            
            cache_key = self._generate_cache_key(section_id, "figure_table_generation", figure_type, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、効果的な図表の構想と説明を生成してください。

【対象内容】
{content}

【図表タイプ】
{figure_type}

【図表設計指示】
以下の観点から効果的な図表を設計・提案し、JSON形式で回答してください：

1. **視覚的効果**: 内容理解を促進する視覚化
2. **情報整理**: 複雑な情報の整理・構造化
3. **比較促進**: 比較・対比を容易にする設計
4. **プロセス表現**: プロセス・流れの明確な表現
5. **関係性表現**: 要素間の関係性の可視化
6. **データ表現**: データ・結果の効果的な表示
7. **概念図式**: 抽象概念の図式化
8. **記憶支援**: 記憶・理解を助ける視覚的構造

{{
    "figure_table_proposals": [
        {{
            "type": "figure|table|diagram|chart|flowchart|model",
            "title": "図表のタイトル",
            "purpose": "図表の目的・役割",
            "description": "図表の詳細説明",
            "structure": {{
                "main_components": ["主要構成要素"],
                "layout_description": "レイアウト・配置の説明",
                "visual_elements": ["視覚的要素"],
                "text_elements": ["テキスト要素"]
            }},
            "data_requirements": {{
                "data_sources": ["必要なデータソース"],
                "data_types": ["データの種類"],
                "preparation_notes": "データ準備に関する注意事項"
            }},
            "creation_guidance": {{
                "software_suggestions": ["推奨作成ソフトウェア"],
                "design_principles": ["設計原則"],
                "best_practices": ["ベストプラクティス"],
                "common_pitfalls": ["避けるべき問題"]
            }},
            "integration_plan": {{
                "placement_in_text": "本文での配置",
                "reference_style": "参照方法",
                "caption_suggestion": "キャプションの提案",
                "explanation_in_text": "本文での説明方法"
            }},
            "effectiveness_score": 0.0-1.0,
            "complexity_level": "low|medium|high",
            "reader_benefit": "読者にとっての利益"
        }}
    ],
    "visual_strategy": {{
        "overall_approach": "全体的な視覚化戦略",
        "consistency_guidelines": "一貫性ガイドライン",
        "accessibility_considerations": "アクセシビリティ考慮事項"
    }},
    "implementation_priorities": [
        {{
            "priority": "high|medium|low",
            "figure_table": "図表の特定",
            "rationale": "優先度の理由",
            "expected_impact": "期待される効果"
        }}
    ],
    "alternative_visualizations": [
        {{
            "alternative_type": "代替視覚化タイプ",
            "description": "代替案の説明",
            "use_case": "使用場面・条件"
        }}
    ],
    "quality_assessment": {{
        "visual_clarity": 0.0-1.0,
        "information_density": 0.0-1.0,
        "educational_value": 0.0-1.0,
        "aesthetic_appeal": 0.0-1.0
    }}
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1800)
            result_data = json.loads(response)
            
            result = {
                "task_type": "figure_table_generation",
                "section_id": section_id,
                "figure_type": figure_type,
                "figure_table_result": result_data,
                "proposals_count": len(result_data.get("figure_table_proposals", [])),
                "high_priority_count": len([p for p in result_data.get("implementation_priorities", []) if p.get("priority") == "high"]),
                "average_effectiveness": sum([p.get("effectiveness_score", 0.0) for p in result_data.get("figure_table_proposals", [])]) / max(len(result_data.get("figure_table_proposals", [])), 1),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"図表生成エラー: {e}")

    async def _perform_conclusion_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """結論・要約の生成"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            conclusion_type = params.get("conclusion_type", "comprehensive")
            research_findings = params.get("research_findings", "")
            
            cache_key = self._generate_cache_key(section_id, "conclusion_generation", conclusion_type, content + research_findings)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、効果的な結論・要約を生成してください。

【論文内容】
{content}

【研究成果・発見】
{research_findings}

【結論タイプ】
{conclusion_type}

【結論生成指示】
以下の観点から効果的な結論・要約を生成し、JSON形式で回答してください：

1. **成果要約**: 主要な研究成果・発見の要約
2. **意義説明**: 研究の意義・貢献の明確化
3. **理論的含意**: 理論的貢献・含意の説明
4. **実践的含意**: 実践的応用・含意の説明
5. **限界認識**: 研究の限界・制約の適切な認識
6. **将来展望**: 今後の研究方向・展望
7. **社会的価値**: 社会・分野への価値・影響
8. **行動喚起**: 読者・研究者への行動喚起

{{
    "conclusion_content": {{
        "main_conclusion": "主たる結論・要約",
        "key_findings_summary": [
            {{
                "finding": "主要発見・成果",
                "significance": "重要性・意義", 
                "evidence_basis": "根拠となる証拠",
                "contribution_type": "theoretical|practical|methodological|empirical"
            }}
        ],
        "research_contributions": {{
            "theoretical_contributions": ["理論的貢献"],
            "practical_contributions": ["実践的貢献"],
            "methodological_contributions": ["方法論的貢献"],
            "empirical_contributions": ["実証的貢献"]
        }},
        "implications": {{
            "academic_implications": ["学術的含意"],
            "practical_implications": ["実践的含意"],
            "policy_implications": ["政策的含意"],
            "social_implications": ["社会的含意"]
        }},
        "limitations_acknowledgment": {{
            "methodological_limitations": ["方法論的限界"],
            "scope_limitations": ["範囲的限界"],
            "data_limitations": ["データ的限界"],
            "generalizability_limitations": ["一般化可能性の限界"]
        }},
        "future_directions": [
            {{
                "direction": "将来の研究方向",
                "rationale": "提案理由",
                "potential_impact": "期待される影響",
                "feasibility": "実現可能性"
            }}
        ]
    }},
    "conclusion_quality": {{
        "completeness": 0.0-1.0,
        "coherence": 0.0-1.0,
        "persuasiveness": 0.0-1.0,
        "actionability": 0.0-1.0,
        "forward_looking": 0.0-1.0
    }},
    "writing_effectiveness": {{
        "clarity_score": 0.0-1.0,
        "impact_score": 0.0-1.0,
        "engagement_score": 0.0-1.0,
        "memorability_score": 0.0-1.0
    }},
    "closing_strategy": {{
        "closing_approach": "結論の終了戦略",
        "final_message": "最終メッセージ",
        "call_to_action": "行動喚起の内容"
    }},
    "alternative_conclusions": [
        {{
            "approach": "代替結論のアプローチ",
            "focus": "重点",
            "use_case": "使用場面"
        }}
    ],
    "overall_conclusion_score": 0.0-1.0
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1800)
            result_data = json.loads(response)
            
            result = {
                "task_type": "conclusion_generation",
                "section_id": section_id,
                "conclusion_type": conclusion_type,
                "conclusion_result": result_data,
                "key_findings_count": len(result_data.get("conclusion_content", {}).get("key_findings_summary", [])),
                "future_directions_count": len(result_data.get("conclusion_content", {}).get("future_directions", [])),
                "overall_conclusion_score": result_data.get("overall_conclusion_score", 0.0),
                "impact_score": result_data.get("writing_effectiveness", {}).get("impact_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"結論生成エラー: {e}")

    async def _perform_integrated_generation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """統合的コンテンツ生成"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            generation_scope = params.get("generation_scope", "comprehensive")
            target_sections = params.get("target_sections", [])
            
            cache_key = self._generate_cache_key(section_id, "integrated_generation", generation_scope, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            # 複数生成タスクの並列実行
            parallel_tasks = []
            
            # セクション生成タスク
            if "section_generation" in target_sections or not target_sections:
                parallel_tasks.append(self._perform_section_generation({
                    **params,
                    "content_type": "integrated",
                    "word_count": 600
                }, metrics))
            
            # 内容拡張タスク
            if content and ("content_expansion" in target_sections or not target_sections):
                parallel_tasks.append(self._perform_content_expansion({
                    **params,
                    "expansion_type": "comprehensive",
                    "expansion_ratio": 1.3
                }, metrics))
            
            # 引用生成タスク
            if "citation_generation" in target_sections or not target_sections:
                parallel_tasks.append(self._perform_citation_generation({
                    **params,
                    "citation_style": "APA"
                }, metrics))
            
            # 並列実行
            individual_results = await asyncio.gather(*parallel_tasks)
            
            # 統合分析プロンプト
            integration_prompt = f"""
以下の個別コンテンツ生成結果を統合して、一貫性のある包括的なコンテンツを生成してください。

【基礎内容】
{content}

【個別生成結果】
{json.dumps([r for r in individual_results if r], ensure_ascii=False, indent=2)}

【統合生成指示】
上記の個別結果を統合し、以下の観点から包括的なコンテンツを生成してください：

1. **内容統合**: 各結果の最適な統合
2. **一貫性確保**: 全体的な一貫性・統一性
3. **品質最適化**: 品質の最適化・向上
4. **構造改善**: 構造・流れの改善
5. **重複解消**: 重複内容の整理・解消
6. **ギャップ補完**: 不足部分の補完
7. **接続強化**: 部分間の論理的接続強化
8. **読者体験**: 読者体験の最適化

{{
    "integrated_content": "統合されたコンテンツ（Markdown形式）",
    "integration_analysis": {{
        "content_sources": [
            {{
                "source": "統合元の生成結果",
                "contribution": "統合への寄与",
                "adaptation": "統合時の適応・調整"
            }}
        ],
        "integration_strategies": [
            {{
                "strategy": "統合戦略",
                "application": "適用方法",
                "effectiveness": 0.0-1.0
            }}
        ],
        "consistency_enhancements": ["一貫性向上のための調整"],
        "quality_improvements": ["品質改善事項"]
    }},
    "content_metrics": {{
        "total_word_count": 推定総文字数,
        "coherence_score": 0.0-1.0,
        "completeness_score": 0.0-1.0,
        "quality_score": 0.0-1.0,
        "readability_score": 0.0-1.0
    }},
    "structural_analysis": {{
        "section_flow": "セクション間の流れ",
        "logical_progression": "論理的進行",
        "transition_quality": "接続の質",
        "overall_structure": "全体構造の評価"
    }},
    "enhancement_opportunities": [
        {{
            "area": "改善領域",
            "current_state": "現状",
            "improvement_suggestion": "改善提案",
            "expected_benefit": "期待される利益"
        }}
    ],
    "final_recommendations": [
        "最終的な改善提案・推奨事項"
    ],
    "integration_success_score": 0.0-1.0
}}
"""
            
            response = await self._call_openai_with_retry(integration_prompt, max_tokens=2000)
            integration_data = json.loads(response)
            
            result = {
                "task_type": "integrated_generation",
                "section_id": section_id,
                "generation_scope": generation_scope,
                "target_sections": target_sections,
                "individual_results": individual_results,
                "integrated_result": integration_data,
                "content_sources_count": len(integration_data.get("integration_analysis", {}).get("content_sources", [])),
                "integration_success_score": integration_data.get("integration_success_score", 0.0),
                "final_quality_score": integration_data.get("content_metrics", {}).get("quality_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"統合コンテンツ生成エラー: {e}")

    def _generate_cache_key(self, section_id: str, task_type: str, focus: str, content: str) -> str:
        """キャッシュキー生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"generation:{task_type}:{section_id}:{focus}:{content_hash}"

    async def _call_openai_with_retry(self, prompt: str, max_tokens: int = 1000) -> str:
        """リトライ付きOpenAI API呼び出し"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await openai_client.generate_text(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens
                )
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    logger.warning(f"OpenAI API呼び出し失敗 (試行 {attempt + 1}/{max_retries}): {e}")
                else:
                    raise AgentExecutionError(f"OpenAI API呼び出しが{max_retries}回失敗しました: {e}")

    def get_supported_tasks(self) -> Dict[str, str]:
        """サポートされているタスクタイプの取得"""
        return self.supported_tasks.copy()

    def get_content_types(self) -> Dict[str, str]:
        """サポートされているコンテンツタイプの取得"""
        return self.content_types.copy()

    def get_quality_criteria(self) -> List[str]:
        """品質基準の取得"""
        return self.quality_criteria.copy()


