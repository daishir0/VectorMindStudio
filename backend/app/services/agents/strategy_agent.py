"""
StrategyAgent - 研究戦略・アプローチ最適化エージェント

研究論文の戦略的アプローチ、論証戦略、研究設計の最適化を行う。
研究目標に基づく戦略立案、論証構造の強化、競争優位性の確立をサポート。
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from app.services.agents.base_agent import AgentExecutionError
from app.services.agents.enhanced_base_agent import EnhancedBaseAgent, ExecutionMetrics
from app.services.agents.base_agent import AgentTask
from app.services.agents.base_agent import AgentResult
from app.infrastructure.external.openai_client import openai_client


logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """戦略分析結果"""
    strategy_type: str
    strategic_recommendations: List[str]
    competitive_advantages: List[str]
    implementation_priority: str
    expected_impact: float
    feasibility_score: float
    risk_factors: List[str]
    success_metrics: List[str]


class StrategyAgent(EnhancedBaseAgent):
    """
    研究戦略・アプローチ最適化エージェント
    
    主要機能：
    1. 研究戦略立案: 研究目標に基づく戦略的アプローチの立案
    2. 論証戦略構築: 効果的な論証構造・戦略の構築
    3. 差別化戦略: 競合研究との差別化戦略の策定
    4. リスク戦略: 研究リスクの評価・軽減戦略
    5. 影響力戦略: 研究の影響力最大化戦略
    6. 公開戦略: 論文公開・普及戦略の策定
    7. 協働戦略: 研究協働・ネットワーキング戦略
    8. 統合戦略: 包括的研究戦略の統合立案
    """
    
    def __init__(self, session=None, timeout: int = 30):
        super().__init__(session=session, timeout=timeout)
        
        # タスクタイプ定義
        self.supported_task_types = {
            "research_strategy_planning": "研究戦略・アプローチの立案",
            "argumentation_strategy": "論証戦略・構造の構築",
            "differentiation_strategy": "差別化・競争優位戦略の策定",
            "risk_mitigation_strategy": "研究リスク評価・軽減戦略",
            "impact_maximization_strategy": "影響力最大化戦略の策定",
            "publication_strategy": "論文公開・普及戦略の立案",
            "collaboration_strategy": "研究協働・ネットワーキング戦略",
            "integrated_strategy_planning": "統合的研究戦略の立案"
        }
        
        # 戦略領域定義
        self.strategy_domains = {
            "methodological": "方法論戦略",
            "theoretical": "理論戦略", 
            "empirical": "実証戦略",
            "competitive": "競争戦略",
            "collaborative": "協働戦略",
            "publication": "公開戦略",
            "impact": "影響力戦略",
            "risk_management": "リスク管理戦略"
        }
        
        # 戦略評価基準
        self.evaluation_criteria = [
            "feasibility",        # 実現可能性
            "impact_potential",   # 影響力ポテンシャル
            "resource_efficiency", # リソース効率性
            "competitive_advantage", # 競争優位性
            "risk_level",         # リスクレベル
            "timeline_appropriateness", # 時間軸適切性
            "sustainability",     # 持続可能性
            "scalability"         # スケーラビリティ
        ]

    @property
    def supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ一覧"""
        return list(self.supported_task_types.keys())

    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コアタスク実行"""
        return await self._execute_strategy_task(
            task.task_type, 
            task.parameters, 
            metrics
        )

    async def execute_task(
        self, 
        task_type: str, 
        section_id: str, 
        content: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        戦略立案タスクの実行
        
        Args:
            task_type: 実行するタスクの種類
            section_id: 対象セクションID
            content: 分析対象のコンテンツ
            parameters: 追加パラメータ（研究目標、制約条件等）
            
        Returns:
            Dict[str, Any]: 戦略立案結果
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
            result = await self._execute_strategy_task(task_type, params, metrics)
            
            return {
                "agent_name": self.agent_name,
                "task_type": task_type,
                "status": "success",
                "result": result,
                "metrics": metrics.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"StrategyAgentタスク実行エラー - {task_type}: {e}")
            return {
                "agent_name": self.agent_name,
                "task_type": task_type,
                "status": "error",
                "error": str(e),
                "metrics": metrics.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _execute_strategy_task(
        self, 
        task_type: str, 
        params: Dict[str, Any], 
        metrics: ExecutionMetrics
    ) -> Dict[str, Any]:
        """戦略立案タスクの実行"""
        
        task_methods = {
            "research_strategy_planning": self._perform_research_strategy_planning,
            "argumentation_strategy": self._perform_argumentation_strategy,
            "differentiation_strategy": self._perform_differentiation_strategy,
            "risk_mitigation_strategy": self._perform_risk_mitigation_strategy,
            "impact_maximization_strategy": self._perform_impact_maximization_strategy,
            "publication_strategy": self._perform_publication_strategy,
            "collaboration_strategy": self._perform_collaboration_strategy,
            "integrated_strategy_planning": self._perform_integrated_strategy_planning
        }
        
        method = task_methods.get(task_type)
        if not method:
            raise AgentExecutionError(f"未実装のタスクタイプ: {task_type}")
            
        return await method(params, metrics)

    async def _perform_research_strategy_planning(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究戦略・アプローチの立案"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            research_goals = params.get("research_goals", "")
            constraints = params.get("constraints", "")
            timeline = params.get("timeline", "medium-term")
            
            # キャッシュキー生成
            cache_key = self._generate_cache_key(section_id, "research_strategy_planning", timeline, content + research_goals)
            
            # キャッシュチェック
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、包括的な研究戦略・アプローチを立案してください。

【研究内容】
{content}

【研究目標】
{research_goals}

【制約条件】
{constraints}

【時間軸】
{timeline}

【戦略立案指示】
以下の観点から包括的な研究戦略を立案し、JSON形式で回答してください：

1. **戦略的目標**: 明確な戦略目標の設定
2. **アプローチ選択**: 最適な研究アプローチの選択
3. **方法論戦略**: 方法論的優位性の確立
4. **リソース戦略**: 効率的なリソース配分
5. **時間軸戦略**: 段階的実行計画
6. **品質戦略**: 研究品質確保戦略
7. **リスク対策**: 潜在リスクへの対策
8. **成果最大化**: 研究成果の最大化戦略

{{
    "strategic_framework": {{
        "primary_objectives": [
            {{
                "objective": "主要戦略目標",
                "rationale": "目標設定理由",
                "success_criteria": ["成功基準"],
                "priority": "high|medium|low"
            }}
        ],
        "research_approach": {{
            "approach_type": "quantitative|qualitative|mixed_methods|theoretical|empirical",
            "justification": "アプローチ選択の正当化",
            "competitive_advantages": ["競争優位性"],
            "implementation_strategy": "実装戦略"
        }},
        "methodological_strategy": {{
            "core_methods": ["中核的手法"],
            "supporting_methods": ["補助的手法"],
            "innovation_aspects": ["革新的要素"],
            "quality_assurance": ["品質保証策"]
        }}
    }},
    "execution_plan": {{
        "phases": [
            {{
                "phase": "実行フェーズ名",
                "duration": "期間",
                "key_activities": ["主要活動"],
                "deliverables": ["成果物"],
                "milestones": ["マイルストーン"],
                "risk_factors": ["リスク要因"]
            }}
        ],
        "resource_allocation": {{
            "time_distribution": "時間配分",
            "skill_requirements": ["必要スキル"],
            "tool_requirements": ["必要ツール・設備"],
            "collaboration_needs": ["協働必要性"]
        }},
        "quality_checkpoints": [
            {{
                "checkpoint": "品質チェックポイント",
                "criteria": ["評価基準"],
                "corrective_actions": ["是正措置"]
            }}
        ]
    }},
    "competitive_positioning": {{
        "unique_value_proposition": "独自価値提案",
        "differentiation_factors": ["差別化要因"],
        "competitive_barriers": ["競争障壁の構築"],
        "market_positioning": "研究分野でのポジション"
    }},
    "risk_management": {{
        "identified_risks": [
            {{
                "risk": "リスク内容",
                "probability": "high|medium|low",
                "impact": "high|medium|low",
                "mitigation_strategy": "軽減戦略",
                "contingency_plan": "緊急時対応計画"
            }}
        ],
        "monitoring_mechanisms": ["監視メカニズム"]
    }},
    "success_metrics": {{
        "quantitative_metrics": [
            {{
                "metric": "定量的指標",
                "target": "目標値",
                "measurement_method": "測定方法"
            }}
        ],
        "qualitative_indicators": ["定性的指標"],
        "impact_measures": ["影響度測定"]
    }},
    "strategy_evaluation": {{
        "feasibility_score": 0.0-1.0,
        "impact_potential": 0.0-1.0,
        "resource_efficiency": 0.0-1.0,
        "competitive_advantage": 0.0-1.0,
        "overall_strategy_score": 0.0-1.0
    }},
    "implementation_recommendations": [
        "戦略実装のための具体的推奨事項"
    ]
}}
"""
            
            # OpenAI API呼び出し
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "research_strategy_planning",
                "section_id": section_id,
                "research_goals": research_goals,
                "constraints": constraints,
                "timeline": timeline,
                "strategy_result": result_data,
                "objectives_count": len(result_data.get("strategic_framework", {}).get("primary_objectives", [])),
                "phases_count": len(result_data.get("execution_plan", {}).get("phases", [])),
                "risks_count": len(result_data.get("risk_management", {}).get("identified_risks", [])),
                "overall_strategy_score": result_data.get("strategy_evaluation", {}).get("overall_strategy_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"研究戦略立案エラー: {e}")

    async def _perform_argumentation_strategy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """論証戦略・構造の構築"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            argument_type = params.get("argument_type", "persuasive")
            target_audience = params.get("target_audience", "academic")
            
            cache_key = self._generate_cache_key(section_id, "argumentation_strategy", argument_type, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、効果的な論証戦略・構造を構築してください。

【研究内容】
{content}

【論証タイプ】
{argument_type}

【対象読者】
{target_audience}

【論証戦略構築指示】
以下の観点から強力な論証戦略を構築し、JSON形式で回答してください：

1. **論証構造**: 論理的で説得力のある論証構造
2. **主張階層**: 主張の階層化・優先順位付け
3. **証拠戦略**: 効果的な証拠の配置・活用
4. **反駁対策**: 反論・批判への対策
5. **論理展開**: 論理的な展開・流れ
6. **説得技法**: 説得力向上技法
7. **読者配慮**: 読者理解を促進する工夫
8. **影響最大化**: 論証の影響力最大化

{{
    "argumentation_framework": {{
        "central_thesis": {{
            "main_claim": "中心的主張",
            "thesis_statement": "論文声明",
            "supporting_rationale": "支持根拠",
            "significance": "重要性・意義"
        }},
        "argument_hierarchy": [
            {{
                "level": "primary|secondary|tertiary",
                "claim": "主張内容",
                "evidence_type": "empirical|theoretical|logical|comparative",
                "strength": 0.0-1.0,
                "dependencies": ["依存関係"],
                "role_in_overall_argument": "全体論証での役割"
            }}
        ],
        "logical_structure": {{
            "progression_type": "deductive|inductive|abductive|dialectical",
            "flow_strategy": "論理展開戦略",
            "connection_mechanisms": ["接続メカニズム"],
            "coherence_strategies": ["一貫性確保策"]
        }}
    }},
    "evidence_strategy": {{
        "evidence_types": [
            {{
                "type": "empirical|statistical|theoretical|anecdotal|expert|comparative",
                "usage_strategy": "使用戦略",
                "placement_strategy": "配置戦略",
                "strength_assessment": 0.0-1.0
            }}
        ],
        "evidence_sequencing": "証拠の順序付け戦略",
        "integration_approach": "証拠統合アプローチ",
        "credibility_enhancement": ["信頼性向上策"]
    }},
    "counter_argument_strategy": {{
        "anticipated_objections": [
            {{
                "objection": "予想される反論",
                "strength": "high|medium|low",
                "response_strategy": "対応戦略",
                "preemptive_measures": ["予防措置"]
            }}
        ],
        "refutation_techniques": ["反駁技法"],
        "defensive_strategies": ["防御戦略"],
        "offense_strategies": ["攻撃的戦略"]
    }},
    "persuasion_techniques": {{
        "logical_appeals": ["論理的アピール手法"],
        "emotional_appeals": ["感情的アピール手法"],
        "credibility_appeals": ["権威的アピール手法"],
        "audience_adaptation": ["読者適応技法"]
    }},
    "rhetorical_strategy": {{
        "opening_strategy": "導入戦略",
        "development_strategy": "展開戦略", 
        "climax_strategy": "クライマックス戦略",
        "closing_strategy": "結論戦略",
        "emphasis_techniques": ["強調技法"]
    }},
    "effectiveness_assessment": {{
        "logical_strength": 0.0-1.0,
        "persuasive_power": 0.0-1.0,
        "evidence_quality": 0.0-1.0,
        "coherence_level": 0.0-1.0,
        "audience_impact": 0.0-1.0,
        "overall_argumentation_score": 0.0-1.0
    }},
    "implementation_guidance": [
        "論証戦略実装のためのガイダンス"
    ],
    "optimization_opportunities": [
        {{
            "area": "最適化領域",
            "current_status": "現状",
            "improvement_strategy": "改善戦略",
            "expected_benefit": "期待される利益"
        }}
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1800)
            result_data = json.loads(response)
            
            result = {
                "task_type": "argumentation_strategy",
                "section_id": section_id,
                "argument_type": argument_type,
                "target_audience": target_audience,
                "argumentation_result": result_data,
                "argument_hierarchy_levels": len(result_data.get("argumentation_framework", {}).get("argument_hierarchy", [])),
                "counter_arguments_count": len(result_data.get("counter_argument_strategy", {}).get("anticipated_objections", [])),
                "overall_argumentation_score": result_data.get("effectiveness_assessment", {}).get("overall_argumentation_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"論証戦略構築エラー: {e}")

    async def _perform_differentiation_strategy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """差別化・競争優位戦略の策定"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            competitive_landscape = params.get("competitive_landscape", "")
            differentiation_focus = params.get("differentiation_focus", "methodology")
            
            cache_key = self._generate_cache_key(section_id, "differentiation_strategy", differentiation_focus, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、差別化・競争優位戦略を策定してください。

【研究内容】
{content}

【競争環境】
{competitive_landscape}

【差別化焦点】
{differentiation_focus}

【差別化戦略策定指示】
以下の観点から効果的な差別化戦略を策定し、JSON形式で回答してください：

1. **独自性分析**: 研究の独自性・独創性の分析
2. **競争優位**: 競合に対する優位性の確立
3. **価値提案**: 独自の価値提案の構築
4. **差別化要因**: 明確な差別化要因の特定
5. **ポジショニング**: 研究分野でのポジション確立
6. **防御戦略**: 競争優位の維持・防御
7. **成長戦略**: 優位性の拡大・発展戦略
8. **ブランド戦略**: 研究ブランドの構築

{{
    "differentiation_analysis": {{
        "unique_strengths": [
            {{
                "strength": "独自の強み",
                "description": "強みの詳細説明",
                "competitive_advantage": "競争優位性",
                "sustainability": "持続可能性",
                "impact_potential": 0.0-1.0
            }}
        ],
        "innovation_aspects": [
            {{
                "innovation": "革新的要素",
                "type": "methodological|theoretical|empirical|technological|conceptual",
                "novelty_degree": "breakthrough|significant|moderate|incremental",
                "market_gap_filled": "埋められる市場ギャップ"
            }}
        ],
        "competitive_moats": [
            {{
                "moat": "競争障壁",
                "type": "knowledge|methodology|data|network|timing",
                "strength": "high|medium|low",
                "durability": "競争障壁の持続性"
            }}
        ]
    }},
    "positioning_strategy": {{
        "target_positioning": "目指すポジション",
        "positioning_rationale": "ポジショニング根拠",
        "key_messages": ["キーメッセージ"],
        "positioning_pillars": [
            {{
                "pillar": "ポジショニングの柱",
                "supporting_evidence": ["支持証拠"],
                "communication_strategy": "伝達戦略"
            }}
        ]
    }},
    "value_proposition": {{
        "core_value": "中核価値",
        "value_dimensions": [
            {{
                "dimension": "価値次元",
                "description": "価値の詳細",
                "target_beneficiary": "価値受益者",
                "quantifiable_benefit": "定量化可能な利益"
            }}
        ],
        "value_communication": "価値伝達方法",
        "proof_points": ["価値の証明ポイント"]
    }},
    "competitive_strategy": {{
        "competitive_response": [
            {{
                "competitor_action": "競合行動",
                "response_strategy": "対応戦略",
                "defensive_measures": ["防御措置"],
                "offensive_opportunities": ["攻撃機会"]
            }}
        ],
        "market_expansion": "市場拡大戦略",
        "barrier_reinforcement": "障壁強化策",
        "innovation_pipeline": "革新パイプライン"
    }},
    "implementation_roadmap": {{
        "short_term_actions": [
            {{
                "action": "短期アクション",
                "timeline": "実行時期",
                "resources_needed": ["必要リソース"],
                "expected_outcome": "期待成果"
            }}
        ],
        "medium_term_strategies": ["中期戦略"],
        "long_term_vision": "長期ビジョン"
    }},
    "success_indicators": {{
        "differentiation_metrics": [
            {{
                "metric": "差別化指標",
                "measurement": "測定方法",
                "target": "目標値",
                "timeline": "達成期限"
            }}
        ],
        "competitive_benchmarks": ["競争ベンチマーク"],
        "market_feedback_indicators": ["市場フィードバック指標"]
    }},
    "risk_considerations": [
        {{
            "risk": "差別化リスク",
            "impact": "高|中|低",
            "mitigation": "軽減策",
            "monitoring": "監視方法"
        }}
    ],
    "differentiation_score": 0.0-1.0,
    "competitive_advantage_score": 0.0-1.0,
    "sustainability_score": 0.0-1.0,
    "overall_strategy_effectiveness": 0.0-1.0
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1800)
            result_data = json.loads(response)
            
            result = {
                "task_type": "differentiation_strategy",
                "section_id": section_id,
                "differentiation_focus": differentiation_focus,
                "strategy_result": result_data,
                "unique_strengths_count": len(result_data.get("differentiation_analysis", {}).get("unique_strengths", [])),
                "competitive_moats_count": len(result_data.get("differentiation_analysis", {}).get("competitive_moats", [])),
                "differentiation_score": result_data.get("differentiation_score", 0.0),
                "overall_strategy_effectiveness": result_data.get("overall_strategy_effectiveness", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"差別化戦略策定エラー: {e}")

    async def _perform_risk_mitigation_strategy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究リスク評価・軽減戦略"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            research_phase = params.get("research_phase", "execution")
            risk_tolerance = params.get("risk_tolerance", "moderate")
            
            cache_key = self._generate_cache_key(section_id, "risk_mitigation_strategy", risk_tolerance, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、包括的なリスク評価と軽減戦略を策定してください。

【研究内容】
{content}

【研究フェーズ】
{research_phase}

【リスク許容度】
{risk_tolerance}

【リスク戦略策定指示】
以下の観点から包括的なリスク管理戦略を策定し、JSON形式で回答してください：

1. **リスク特定**: 潜在的リスクの包括的特定
2. **リスク評価**: リスクの影響度・発生確率評価
3. **優先順位付け**: リスクの優先順位決定
4. **軽減戦略**: 効果的なリスク軽減戦略
5. **緊急時対応**: 緊急時・クライシス対応計画
6. **監視体制**: リスク監視・早期警戒システム
7. **予防措置**: 予防的リスク管理措置
8. **継続改善**: リスク管理の継続的改善

{{
    "risk_assessment": {{
        "identified_risks": [
            {{
                "risk_category": "methodological|data|technical|timeline|resource|ethical|publication|competitive",
                "risk_description": "リスクの詳細説明",
                "probability": "high|medium|low",
                "impact": "high|medium|low",
                "severity_score": 0.0-1.0,
                "risk_indicators": ["リスク兆候・指標"],
                "potential_consequences": ["想定される結果"]
            }}
        ],
        "risk_interdependencies": [
            {{
                "primary_risk": "主要リスク",
                "related_risks": ["関連リスク"],
                "cascade_effects": ["連鎖影響"]
            }}
        ],
        "risk_matrix": {{
            "high_probability_high_impact": ["リスク一覧"],
            "high_probability_low_impact": ["リスク一覧"],
            "low_probability_high_impact": ["リスク一覧"],
            "low_probability_low_impact": ["リスク一覧"]
        }}
    }},
    "mitigation_strategies": [
        {{
            "risk": "対象リスク",
            "strategy_type": "avoidance|mitigation|transfer|acceptance",
            "specific_actions": [
                {{
                    "action": "具体的対策",
                    "timeline": "実行時期",
                    "resources_required": ["必要リソース"],
                    "effectiveness": 0.0-1.0,
                    "cost": "high|medium|low"
                }}
            ],
            "success_criteria": ["成功基準"],
            "fallback_plans": ["代替計画"]
        }}
    ],
    "contingency_planning": {{
        "crisis_scenarios": [
            {{
                "scenario": "危機シナリオ",
                "triggers": ["発動条件"],
                "response_plan": "対応計画",
                "key_decisions": ["重要な判断事項"],
                "communication_plan": "コミュニケーション計画"
            }}
        ],
        "emergency_procedures": ["緊急手順"],
        "escalation_protocols": ["エスカレーション手順"],
        "recovery_strategies": ["復旧戦略"]
    }},
    "monitoring_framework": {{
        "key_risk_indicators": [
            {{
                "indicator": "主要リスク指標",
                "measurement_method": "測定方法",
                "threshold_levels": {{
                    "green": "正常レベル",
                    "yellow": "注意レベル",
                    "red": "警戒レベル"
                }},
                "monitoring_frequency": "監視頻度",
                "responsible_party": "責任者"
            }}
        ],
        "reporting_mechanisms": ["報告メカニズム"],
        "review_cycles": "見直しサイクル"
    }},
    "preventive_measures": {{
        "risk_prevention_strategies": [
            {{
                "strategy": "予防戦略",
                "implementation": "実装方法",
                "cost_benefit": "コストベネフィット",
                "maintenance_requirements": "維持要件"
            }}
        ],
        "quality_controls": ["品質管理策"],
        "process_improvements": ["プロセス改善"]
    }},
    "risk_communication": {{
        "stakeholder_communication": [
            {{
                "stakeholder": "ステークホルダー",
                "communication_approach": "コミュニケーション方針",
                "key_messages": ["主要メッセージ"],
                "frequency": "連絡頻度"
            }}
        ],
        "transparency_level": "透明性レベル",
        "documentation_requirements": ["文書化要件"]
    }},
    "strategy_evaluation": {{
        "risk_coverage": 0.0-1.0,
        "mitigation_effectiveness": 0.0-1.0,
        "resource_efficiency": 0.0-1.0,
        "implementation_feasibility": 0.0-1.0,
        "overall_risk_management_score": 0.0-1.0
    }},
    "continuous_improvement": [
        "リスク管理の継続的改善策"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "risk_mitigation_strategy",
                "section_id": section_id,
                "research_phase": research_phase,
                "risk_tolerance": risk_tolerance,
                "risk_strategy_result": result_data,
                "identified_risks_count": len(result_data.get("risk_assessment", {}).get("identified_risks", [])),
                "mitigation_strategies_count": len(result_data.get("mitigation_strategies", [])),
                "crisis_scenarios_count": len(result_data.get("contingency_planning", {}).get("crisis_scenarios", [])),
                "overall_risk_management_score": result_data.get("strategy_evaluation", {}).get("overall_risk_management_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"リスク軽減戦略策定エラー: {e}")

    async def _perform_impact_maximization_strategy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """影響力最大化戦略の策定"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            target_impact = params.get("target_impact", "academic")
            impact_metrics = params.get("impact_metrics", ["citation", "practical_application"])
            
            cache_key = self._generate_cache_key(section_id, "impact_maximization_strategy", target_impact, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            impact_metrics_str = ", ".join(impact_metrics)
            
            prompt = f"""
研究論文の以下の内容について、影響力最大化戦略を策定してください。

【研究内容】
{content}

【目標影響領域】
{target_impact}

【影響指標】
{impact_metrics_str}

【影響力戦略策定指示】
以下の観点から効果的な影響力最大化戦略を策定し、JSON形式で回答してください：

1. **影響力分析**: 潜在的影響力の分析・評価
2. **ターゲット設定**: 影響対象・読者の明確化
3. **価値訴求**: 価値・意義の効果的な訴求
4. **普及戦略**: 研究成果の普及・拡散戦略
5. **エンゲージメント**: ステークホルダーエンゲージメント
6. **応用促進**: 実用化・応用促進戦略
7. **持続的影響**: 長期的影響の確保
8. **測定・評価**: 影響力の測定・評価体制

{{
    "impact_analysis": {{
        "potential_impacts": [
            {{
                "impact_type": "academic|practical|social|policy|economic|technological",
                "description": "影響の詳細説明",
                "target_audience": "影響対象",
                "magnitude": "high|medium|low",
                "timeline": "short_term|medium_term|long_term",
                "evidence_basis": "影響の根拠"
            }}
        ],
        "impact_pathways": [
            {{
                "pathway": "影響経路",
                "mechanism": "影響メカニズム",
                "intermediary_steps": ["中間ステップ"],
                "facilitating_factors": ["促進要因"],
                "barriers": ["阻害要因"]
            }}
        ],
        "impact_potential_score": 0.0-1.0
    }},
    "target_audience_strategy": {{
        "primary_audiences": [
            {{
                "audience": "主要対象読者",
                "characteristics": "読者特性",
                "needs": ["ニーズ・関心"],
                "engagement_channels": ["エンゲージメント手段"],
                "value_proposition": "価値提案",
                "communication_style": "コミュニケーションスタイル"
            }}
        ],
        "secondary_audiences": ["二次対象読者"],
        "influence_network": "影響ネットワーク分析"
    }},
    "dissemination_strategy": {{
        "publication_strategy": {{
            "journal_selection": "ジャーナル選択戦略",
            "publication_timing": "公開タイミング",
            "open_access_strategy": "オープンアクセス戦略",
            "preprint_strategy": "プレプリント戦略"
        }},
        "communication_channels": [
            {{
                "channel": "コミュニケーションチャネル",
                "target_audience": "対象読者",
                "content_format": "コンテンツ形式",
                "frequency": "頻度",
                "success_metrics": ["成功指標"]
            }}
        ],
        "multi_media_strategy": "マルチメディア活用戦略",
        "social_media_strategy": "ソーシャルメディア戦略"
    }},
    "engagement_tactics": {{
        "academic_engagement": [
            {{
                "tactic": "学術エンゲージメント戦術",
                "description": "戦術の詳細",
                "implementation": "実装方法",
                "expected_outcome": "期待される成果"
            }}
        ],
        "industry_engagement": ["産業界エンゲージメント"],
        "policy_engagement": ["政策エンゲージメント"],
        "public_engagement": ["一般市民エンゲージメント"]
    }},
    "application_promotion": {{
        "practical_applications": [
            {{
                "application": "実用化・応用",
                "promotion_strategy": "促進戦略",
                "key_partners": ["主要パートナー"],
                "implementation_support": "実装支援",
                "barrier_removal": "障壁除去策"
            }}
        ],
        "technology_transfer": "技術移転戦略",
        "commercialization_potential": "商業化ポテンシャル"
    }},
    "sustainability_measures": {{
        "long_term_impact_strategies": [
            {{
                "strategy": "長期影響戦略",
                "maintenance_approach": "維持アプローチ",
                "evolution_plan": "発展計画",
                "legacy_building": "レガシー構築"
            }}
        ],
        "community_building": "コミュニティ構築",
        "knowledge_base_contribution": "知識基盤への貢献"
    }},
    "measurement_framework": {{
        "impact_metrics": [
            {{
                "metric": "影響指標",
                "measurement_method": "測定方法",
                "data_sources": ["データソース"],
                "collection_frequency": "収集頻度",
                "target_values": "目標値"
            }}
        ],
        "tracking_mechanisms": ["追跡メカニズム"],
        "evaluation_timeline": "評価スケジュール",
        "reporting_framework": "報告フレームワーク"
    }},
    "resource_optimization": {{
        "budget_allocation": "予算配分",
        "time_investment": "時間投資",
        "skill_requirements": ["必要スキル"],
        "partnership_opportunities": ["パートナーシップ機会"]
    }},
    "strategy_evaluation": {{
        "feasibility_score": 0.0-1.0,
        "impact_potential": 0.0-1.0,
        "resource_efficiency": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "overall_impact_strategy_score": 0.0-1.0
    }},
    "implementation_roadmap": [
        {{
            "phase": "実装フェーズ",
            "duration": "期間",
            "key_activities": ["主要活動"],
            "milestones": ["マイルストーン"],
            "success_criteria": ["成功基準"]
        }}
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "impact_maximization_strategy",
                "section_id": section_id,
                "target_impact": target_impact,
                "impact_metrics": impact_metrics,
                "impact_strategy_result": result_data,
                "potential_impacts_count": len(result_data.get("impact_analysis", {}).get("potential_impacts", [])),
                "primary_audiences_count": len(result_data.get("target_audience_strategy", {}).get("primary_audiences", [])),
                "impact_potential_score": result_data.get("impact_analysis", {}).get("impact_potential_score", 0.0),
                "overall_impact_strategy_score": result_data.get("strategy_evaluation", {}).get("overall_impact_strategy_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"影響力最大化戦略策定エラー: {e}")

    async def _perform_publication_strategy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """論文公開・普及戦略の立案"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            research_field = params.get("research_field", "general")
            publication_goals = params.get("publication_goals", "high_impact")
            
            cache_key = self._generate_cache_key(section_id, "publication_strategy", publication_goals, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、効果的な公開・普及戦略を立案してください。

【研究内容】
{content}

【研究分野】
{research_field}

【公開目標】
{publication_goals}

【公開戦略立案指示】
以下の観点から包括的な公開・普及戦略を立案し、JSON形式で回答してください：

1. **ジャーナル戦略**: 最適なジャーナル選択・投稿戦略
2. **タイミング戦略**: 公開タイミングの最適化
3. **普及戦略**: 効果的な普及・拡散手法
4. **可視性戦略**: 研究の可視性向上策
5. **アクセス戦略**: アクセシビリティ向上策
6. **プロモーション**: 効果的なプロモーション手法
7. **ネットワーク活用**: 研究ネットワークの戦略的活用
8. **持続的普及**: 長期的な普及・影響力確保

{{
    "journal_selection_strategy": {{
        "target_journals": [
            {{
                "journal_name": "対象ジャーナル（仮想）",
                "tier": "top_tier|high_tier|medium_tier|specialized",
                "impact_factor_range": "影響因子範囲（推定）",
                "fit_score": 0.0-1.0,
                "acceptance_probability": "high|medium|low",
                "review_timeline": "査読期間（推定）",
                "advantages": ["利点"],
                "considerations": ["考慮事項"],
                "submission_strategy": "投稿戦略"
            }}
        ],
        "submission_sequence": "投稿順序戦略",
        "backup_options": ["代替選択肢"],
        "journal_selection_criteria": ["選択基準"]
    }},
    "timing_optimization": {{
        "optimal_submission_timing": {{
            "preferred_months": ["最適投稿月"],
            "timing_rationale": "タイミングの根拠",
            "market_considerations": "市場考慮事項",
            "competitive_timing": "競合タイミング分析"
        }},
        "pre_submission_activities": [
            {{
                "activity": "投稿前活動",
                "timeline": "実行時期",
                "purpose": "目的",
                "expected_benefit": "期待される効果"
            }}
        ],
        "post_acceptance_plan": "受理後計画"
    }},
    "visibility_enhancement": {{
        "seo_optimization": {{
            "keyword_strategy": ["キーワード戦略"],
            "title_optimization": "タイトル最適化",
            "abstract_optimization": "要約最適化",
            "metadata_strategy": "メタデータ戦略"
        }},
        "online_presence": [
            {{
                "platform": "オンラインプラットフォーム",
                "strategy": "活用戦略",
                "content_approach": "コンテンツアプローチ",
                "engagement_tactics": ["エンゲージメント戦術"]
            }}
        ],
        "academic_profiles": "学術プロファイル最適化"
    }},
    "dissemination_tactics": {{
        "multi_channel_approach": [
            {{
                "channel": "普及チャネル",
                "target_audience": "対象読者",
                "content_format": "コンテンツ形式",
                "distribution_strategy": "配信戦略",
                "success_metrics": ["成功指標"]
            }}
        ],
        "conference_strategy": {{
            "target_conferences": ["対象会議"],
            "presentation_strategy": "発表戦略",
            "networking_approach": "ネットワーキング方針"
        }},
        "media_outreach": "メディアアウトリーチ戦略"
    }},
    "access_optimization": {{
        "open_access_strategy": {{
            "oa_approach": "オープンアクセス方針",
            "repository_strategy": "リポジトリ戦略",
            "cost_considerations": "コスト考慮事項",
            "compliance_requirements": ["コンプライアンス要件"]
        }},
        "accessibility_features": ["アクセシビリティ機能"],
        "global_reach_strategy": "グローバル展開戦略"
    }},
    "promotion_campaign": {{
        "launch_strategy": {{
            "launch_timeline": "ローンチスケジュール",
            "key_messages": ["主要メッセージ"],
            "target_stakeholders": ["対象ステークホルダー"],
            "promotional_materials": ["プロモーション素材"]
        }},
        "sustained_promotion": [
            {{
                "phase": "プロモーション段階",
                "duration": "期間",
                "activities": ["活動"],
                "goals": ["目標"]
            }}
        ],
        "partnership_promotion": "パートナーシップ活用"
    }},
    "network_utilization": {{
        "professional_networks": [
            {{
                "network": "専門ネットワーク",
                "utilization_strategy": "活用戦略",
                "contribution_approach": "貢献アプローチ",
                "expected_benefits": ["期待される利益"]
            }}
        ],
        "collaboration_opportunities": ["コラボレーション機会"],
        "mentorship_engagement": "メンターシップ活用"
    }},
    "long_term_sustainability": {{
        "citation_enhancement": [
            {{
                "strategy": "引用向上戦略",
                "implementation": "実装方法",
                "maintenance": "維持方法"
            }}
        ],
        "follow_up_research": "フォローアップ研究計画",
        "community_engagement": "コミュニティエンゲージメント",
        "legacy_building": "レガシー構築"
    }},
    "success_measurement": {{
        "key_performance_indicators": [
            {{
                "kpi": "主要業績指標",
                "measurement_method": "測定方法",
                "target_value": "目標値",
                "tracking_frequency": "追跡頻度"
            }}
        ],
        "milestone_tracking": ["マイルストーン追跡"],
        "adjustment_triggers": ["戦略調整の発動条件"]
    }},
    "resource_planning": {{
        "budget_requirements": "予算要件",
        "time_investment": "時間投資",
        "skill_needs": ["必要スキル"],
        "external_support": ["外部サポート"]
    }},
    "strategy_evaluation": {{
        "feasibility_score": 0.0-1.0,
        "impact_potential": 0.0-1.0,
        "resource_efficiency": 0.0-1.0,
        "timeline_realism": 0.0-1.0,
        "overall_publication_strategy_score": 0.0-1.0
    }}
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "publication_strategy",
                "section_id": section_id,
                "research_field": research_field,
                "publication_goals": publication_goals,
                "publication_strategy_result": result_data,
                "target_journals_count": len(result_data.get("journal_selection_strategy", {}).get("target_journals", [])),
                "dissemination_channels_count": len(result_data.get("dissemination_tactics", {}).get("multi_channel_approach", [])),
                "overall_publication_strategy_score": result_data.get("strategy_evaluation", {}).get("overall_publication_strategy_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"公開戦略立案エラー: {e}")

    async def _perform_collaboration_strategy(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究協働・ネットワーキング戦略"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            collaboration_goals = params.get("collaboration_goals", "knowledge_sharing")
            current_network = params.get("current_network", "limited")
            
            cache_key = self._generate_cache_key(section_id, "collaboration_strategy", collaboration_goals, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、効果的な協働・ネットワーキング戦略を策定してください。

【研究内容】
{content}

【協働目標】
{collaboration_goals}

【現在のネットワーク】
{current_network}

【協働戦略策定指示】
以下の観点から効果的な協働・ネットワーキング戦略を策定し、JSON形式で回答してください：

1. **協働機会**: 潜在的協働機会の特定・分析
2. **パートナー戦略**: 最適なパートナーの特定・アプローチ
3. **ネットワーク構築**: 戦略的ネットワーク構築
4. **価値創造**: 相互価値創造の仕組み
5. **関係管理**: 長期的関係管理戦略
6. **知識共有**: 効果的な知識共有システム
7. **共同研究**: 共同研究プロジェクトの企画
8. **コミュニティ貢献**: 研究コミュニティへの貢献

{{
    "collaboration_landscape": {{
        "potential_collaborators": [
            {{
                "collaborator_type": "academic|industry|government|ngo|international",
                "description": "協働相手の特徴",
                "collaboration_value": "協働価値",
                "mutual_benefits": ["相互利益"],
                "compatibility_score": 0.0-1.0,
                "approach_strategy": "アプローチ戦略",
                "potential_challenges": ["潜在的課題"]
            }}
        ],
        "collaboration_opportunities": [
            {{
                "opportunity": "協働機会",
                "type": "research|publication|funding|knowledge_exchange|capacity_building",
                "scope": "local|national|international",
                "timeline": "short_term|medium_term|long_term",
                "resource_requirements": ["必要リソース"],
                "success_probability": "high|medium|low"
            }}
        ]
    }},
    "partner_identification": {{
        "target_partners": [
            {{
                "partner": "対象パートナー",
                "rationale": "選択理由",
                "complementary_strengths": ["補完的強み"],
                "collaboration_potential": 0.0-1.0,
                "contact_strategy": "コンタクト戦略",
                "relationship_building_approach": "関係構築方法"
            }}
        ],
        "partner_prioritization": "パートナー優先順位付け",
        "diversification_strategy": "多様化戦略"
    }},
    "network_development": {{
        "network_expansion_strategy": [
            {{
                "expansion_area": "拡張領域",
                "target_connections": "対象コネクション",
                "networking_channels": ["ネットワーキング手段"],
                "engagement_tactics": ["エンゲージメント戦術"],
                "value_proposition": "価値提案"
            }}
        ],
        "network_maintenance": [
            {{
                "maintenance_activity": "維持活動",
                "frequency": "頻度",
                "resource_requirement": "リソース要件",
                "expected_outcome": "期待される成果"
            }}
        ],
        "network_quality_metrics": ["ネットワーク品質指標"]
    }},
    "value_creation_framework": {{
        "mutual_value_propositions": [
            {{
                "value_type": "knowledge|resource|skill|network|reputation",
                "offering": "提供価値",
                "receiving": "受け取り価値",
                "exchange_mechanism": "交換メカニズム",
                "sustainability": "持続可能性"
            }}
        ],
        "collaboration_models": [
            {{
                "model": "協働モデル",
                "structure": "構造",
                "governance": "ガバナンス",
                "benefit_sharing": "利益分配",
                "risk_sharing": "リスク分担"
            }}
        ]
    }},
    "knowledge_sharing_strategy": {{
        "sharing_mechanisms": [
            {{
                "mechanism": "共有メカニズム",
                "content_type": "共有コンテンツタイプ",
                "platform": "プラットフォーム",
                "frequency": "頻度",
                "audience": "対象読者"
            }}
        ],
        "intellectual_property": "知的財産管理",
        "open_science_approach": "オープンサイエンス方針",
        "knowledge_protection": "知識保護策"
    }},
    "joint_research_planning": {{
        "research_themes": [
            {{
                "theme": "共同研究テーマ",
                "research_gap": "研究ギャップ",
                "collaboration_advantage": "協働による優位性",
                "resource_pooling": "リソースプール",
                "timeline": "研究期間",
                "expected_outcomes": ["期待される成果"]
            }}
        ],
        "project_structuring": "プロジェクト構造化",
        "funding_strategy": "資金調達戦略",
        "publication_strategy": "共同発表戦略"
    }},
    "community_engagement": {{
        "contribution_opportunities": [
            {{
                "opportunity": "貢献機会",
                "community": "対象コミュニティ",
                "contribution_type": "貢献タイプ",
                "time_commitment": "時間コミット",
                "impact_potential": 0.0-1.0,
                "skill_development": "スキル開発効果"
            }}
        ],
        "leadership_roles": ["リーダーシップ役割"],
        "mentorship_engagement": "メンターシップ参加",
        "peer_review_participation": "査読参加"
    }},
    "relationship_management": {{
        "relationship_categories": [
            {{
                "category": "関係カテゴリ",
                "management_approach": "管理アプローチ",
                "communication_frequency": "コミュニケーション頻度",
                "maintenance_activities": ["維持活動"],
                "value_reinforcement": "価値強化策"
            }}
        ],
        "conflict_resolution": "紛争解決メカニズム",
        "relationship_evaluation": "関係評価方法"
    }},
    "implementation_roadmap": {{
        "phases": [
            {{
                "phase": "実装段階",
                "duration": "期間",
                "key_activities": ["主要活動"],
                "success_criteria": ["成功基準"],
                "milestones": ["マイルストーン"]
            }}
        ],
        "resource_allocation": "リソース配分",
        "timeline_management": "タイムライン管理"
    }},
    "success_measurement": {{
        "collaboration_metrics": [
            {{
                "metric": "協働指標",
                "measurement_method": "測定方法",
                "target_value": "目標値",
                "review_frequency": "見直し頻度"
            }}
        ],
        "network_health_indicators": ["ネットワーク健全性指標"],
        "roi_assessment": "投資収益率評価"
    }},
    "strategy_evaluation": {{
        "feasibility_score": 0.0-1.0,
        "network_potential": 0.0-1.0,
        "value_creation_potential": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "overall_collaboration_strategy_score": 0.0-1.0
    }}
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "collaboration_strategy",
                "section_id": section_id,
                "collaboration_goals": collaboration_goals,
                "current_network": current_network,
                "collaboration_strategy_result": result_data,
                "potential_collaborators_count": len(result_data.get("collaboration_landscape", {}).get("potential_collaborators", [])),
                "target_partners_count": len(result_data.get("partner_identification", {}).get("target_partners", [])),
                "overall_collaboration_strategy_score": result_data.get("strategy_evaluation", {}).get("overall_collaboration_strategy_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"協働戦略策定エラー: {e}")

    async def _perform_integrated_strategy_planning(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """統合的研究戦略の立案"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            strategic_scope = params.get("strategic_scope", "comprehensive")
            priority_areas = params.get("priority_areas", ["research", "publication", "impact"])
            
            cache_key = self._generate_cache_key(section_id, "integrated_strategy_planning", strategic_scope, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            # 複数戦略の並列実行
            parallel_tasks = []
            
            if "research" in priority_areas:
                parallel_tasks.append(self._perform_research_strategy_planning(params, metrics))
            
            if "publication" in priority_areas:
                parallel_tasks.append(self._perform_publication_strategy({**params, "publication_goals": "high_impact"}, metrics))
            
            if "impact" in priority_areas:
                parallel_tasks.append(self._perform_impact_maximization_strategy({**params, "target_impact": "comprehensive"}, metrics))
            
            # 並列実行
            individual_strategies = await asyncio.gather(*parallel_tasks)
            
            # 統合戦略プロンプト
            integration_prompt = f"""
以下の個別戦略結果を統合して、包括的で一貫性のある統合研究戦略を策定してください。

【基礎研究内容】
{content}

【戦略範囲】
{strategic_scope}

【優先領域】
{', '.join(priority_areas)}

【個別戦略結果】
{json.dumps([s for s in individual_strategies if s], ensure_ascii=False, indent=2)}

【統合戦略策定指示】
上記の個別戦略を統合し、以下の観点から包括的な統合研究戦略を策定してください：

1. **戦略統合**: 個別戦略の最適統合
2. **一貫性確保**: 戦略間の一貫性・整合性確保
3. **相乗効果**: 戦略間の相乗効果最大化
4. **優先順位**: 統合戦略の優先順位付け
5. **リソース最適化**: リソース配分の最適化
6. **リスク統合**: 統合的リスク管理
7. **実行計画**: 統合実行計画の策定
8. **成果測定**: 統合成果測定体系

{{
    "integrated_strategy_framework": {{
        "strategic_vision": {{
            "vision_statement": "戦略ビジョン",
            "strategic_objectives": ["戦略的目標"],
            "success_definition": "成功の定義",
            "timeline_horizon": "戦略時間軸"
        }},
        "strategy_pillars": [
            {{
                "pillar": "戦略の柱",
                "description": "詳細説明",
                "contributing_strategies": ["貢献する個別戦略"],
                "key_initiatives": ["主要イニシアティブ"],
                "success_metrics": ["成功指標"]
            }}
        ],
        "strategic_priorities": [
            {{
                "priority": "戦略優先事項",
                "rationale": "優先理由",
                "resource_allocation": "リソース配分",
                "timeline": "実行期間",
                "dependencies": ["依存関係"],
                "success_criteria": ["成功基準"]
            }}
        ]
    }},
    "synergy_analysis": {{
        "cross_strategy_synergies": [
            {{
                "synergy": "相乗効果",
                "involved_strategies": ["関与戦略"],
                "value_creation": "価値創造",
                "implementation_approach": "実装アプローチ",
                "expected_benefit": "期待される利益"
            }}
        ],
        "integration_opportunities": ["統合機会"],
        "optimization_areas": ["最適化領域"]
    }},
    "resource_optimization": {{
        "resource_categories": [
            {{
                "category": "リソースカテゴリ",
                "total_requirement": "総必要量",
                "allocation_strategy": "配分戦略",
                "sharing_opportunities": ["共有機会"],
                "efficiency_measures": ["効率化措置"]
            }}
        ],
        "cost_benefit_analysis": "費用便益分析",
        "investment_priorities": ["投資優先順位"]
    }},
    "integrated_risk_management": {{
        "strategic_risks": [
            {{
                "risk": "戦略リスク",
                "impact_scope": "影響範囲",
                "mitigation_approach": "軽減アプローチ",
                "contingency_planning": "緊急時計画",
                "monitoring_strategy": "監視戦略"
            }}
        ],
        "risk_interdependencies": ["リスク相互依存"],
        "integrated_monitoring": "統合監視体制"
    }},
    "execution_roadmap": {{
        "implementation_phases": [
            {{
                "phase": "実装段階",
                "duration": "期間",
                "strategic_focus": ["戦略焦点"],
                "key_deliverables": ["主要成果物"],
                "resource_requirements": ["リソース要件"],
                "success_milestones": ["成功マイルストーン"],
                "phase_dependencies": ["段階依存関係"]
            }}
        ],
        "critical_path": "クリティカルパス",
        "flexibility_mechanisms": ["柔軟性メカニズム"],
        "adaptation_triggers": ["適応発動条件"]
    }},
    "performance_measurement": {{
        "integrated_kpis": [
            {{
                "kpi": "統合主要業績指標",
                "measurement_approach": "測定アプローチ",
                "data_sources": ["データソース"],
                "reporting_frequency": "報告頻度",
                "target_benchmarks": "目標ベンチマーク"
            }}
        ],
        "dashboard_design": "ダッシュボード設計",
        "review_mechanisms": ["見直しメカニズム"],
        "adjustment_protocols": ["調整プロトコル"]
    }},
    "strategic_governance": {{
        "decision_making_framework": "意思決定フレームワーク",
        "accountability_structure": "責任構造",
        "communication_plan": "コミュニケーション計画",
        "stakeholder_engagement": "ステークホルダーエンゲージメント"
    }},
    "continuous_improvement": {{
        "learning_mechanisms": ["学習メカニズム"],
        "feedback_loops": ["フィードバックループ"],
        "innovation_processes": ["革新プロセス"],
        "knowledge_management": "知識管理"
    }},
    "strategy_evaluation": {{
        "integration_quality": 0.0-1.0,
        "coherence_score": 0.0-1.0,
        "feasibility_score": 0.0-1.0,
        "impact_potential": 0.0-1.0,
        "sustainability_score": 0.0-1.0,
        "overall_integrated_strategy_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "統合戦略実装のための主要推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(integration_prompt, max_tokens=2000)
            integration_data = json.loads(response)
            
            result = {
                "task_type": "integrated_strategy_planning",
                "section_id": section_id,
                "strategic_scope": strategic_scope,
                "priority_areas": priority_areas,
                "individual_strategies": individual_strategies,
                "integrated_strategy": integration_data,
                "strategy_pillars_count": len(integration_data.get("integrated_strategy_framework", {}).get("strategy_pillars", [])),
                "synergies_count": len(integration_data.get("synergy_analysis", {}).get("cross_strategy_synergies", [])),
                "implementation_phases_count": len(integration_data.get("execution_roadmap", {}).get("implementation_phases", [])),
                "overall_integrated_strategy_score": integration_data.get("strategy_evaluation", {}).get("overall_integrated_strategy_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"統合戦略策定エラー: {e}")

    def _generate_cache_key(self, section_id: str, task_type: str, focus: str, content: str) -> str:
        """キャッシュキー生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"strategy:{task_type}:{section_id}:{focus}:{content_hash}"

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

    def get_strategy_domains(self) -> Dict[str, str]:
        """戦略領域の取得"""
        return self.strategy_domains.copy()

    def get_evaluation_criteria(self) -> List[str]:
        """戦略評価基準の取得"""
        return self.evaluation_criteria.copy()


# エージェントインスタンスは必要な時に作成される