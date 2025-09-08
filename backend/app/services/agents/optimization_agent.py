"""
OptimizationAgent - 研究論文の最適化・パフォーマンス向上エージェント

研究論文の効率性、効果性、品質の最適化を行う。
パフォーマンス向上、リソース効率化、成果最大化の統合的最適化をサポート。
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
class OptimizationResult:
    """最適化結果"""
    optimization_type: str
    performance_improvements: List[str]
    efficiency_gains: List[str]
    quality_enhancements: List[str]
    optimization_score: float
    implementation_priority: str
    expected_roi: float
    optimization_recommendations: List[str]


class OptimizationAgent(EnhancedBaseAgent):
    """
    研究論文最適化・パフォーマンス向上エージェント
    
    主要機能：
    1. 効率最適化: 研究プロセス・ワークフローの効率化
    2. 品質最適化: 研究品質・アウトプット品質の向上
    3. リソース最適化: リソース配分・活用の最適化
    4. 時間最適化: 時間管理・スケジュール最適化
    5. 成果最適化: 研究成果・インパクトの最大化
    6. コスト最適化: コスト効率・費用対効果の改善
    7. プロセス最適化: 研究プロセス・手法の最適化
    8. 統合最適化: 包括的・統合的最適化の実施
    """
    
    def __init__(self, session=None, timeout: int = 30):
        super().__init__(session=session, timeout=timeout)
        
        # タスクタイプ定義
        self.supported_task_types = {
            "efficiency_optimization": "研究効率・ワークフローの最適化",
            "quality_optimization": "研究品質・アウトプット品質の最適化",
            "resource_optimization": "リソース配分・活用の最適化",
            "time_optimization": "時間管理・スケジュール最適化",
            "impact_optimization": "研究成果・インパクトの最大化",
            "cost_optimization": "コスト効率・費用対効果の改善",
            "process_optimization": "研究プロセス・手法の最適化",
            "integrated_optimization": "包括的・統合的最適化"
        }
        
        # 最適化領域定義
        self.optimization_domains = {
            "workflow": "ワークフロー最適化",
            "methodology": "方法論最適化",
            "resource_allocation": "リソース配分最適化",
            "time_management": "時間管理最適化",
            "quality_assurance": "品質保証最適化",
            "collaboration": "協働最適化",
            "technology": "技術活用最適化",
            "output": "アウトプット最適化"
        }
        
        # 最適化指標
        self.optimization_metrics = [
            "efficiency_ratio",      # 効率性比率
            "quality_score",         # 品質スコア
            "resource_utilization",  # リソース活用率
            "time_effectiveness",    # 時間効率性
            "cost_efficiency",       # コスト効率
            "output_quality",        # 出力品質
            "process_smoothness",    # プロセス円滑性
            "stakeholder_satisfaction" # ステークホルダー満足度
        ]

    @property
    def supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ一覧"""
        return list(self.supported_task_types.keys())

    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コアタスク実行"""
        return await self._execute_optimization_task(
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
        最適化タスクの実行
        
        Args:
            task_type: 実行するタスクの種類
            section_id: 対象セクションID
            content: 最適化対象のコンテンツ
            parameters: 追加パラメータ（最適化目標、制約条件等）
            
        Returns:
            Dict[str, Any]: 最適化結果
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
            result = await self._execute_optimization_task(task_type, params, metrics)
            
            return {
                "agent_name": self.agent_name,
                "task_type": task_type,
                "status": "success",
                "result": result,
                "metrics": metrics.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OptimizationAgentタスク実行エラー - {task_type}: {e}")
            return {
                "agent_name": self.agent_name,
                "task_type": task_type,
                "status": "error",
                "error": str(e),
                "metrics": metrics.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _execute_optimization_task(
        self, 
        task_type: str, 
        params: Dict[str, Any], 
        metrics: ExecutionMetrics
    ) -> Dict[str, Any]:
        """最適化タスクの実行"""
        
        task_methods = {
            "efficiency_optimization": self._perform_efficiency_optimization,
            "quality_optimization": self._perform_quality_optimization,
            "resource_optimization": self._perform_resource_optimization,
            "time_optimization": self._perform_time_optimization,
            "impact_optimization": self._perform_impact_optimization,
            "cost_optimization": self._perform_cost_optimization,
            "process_optimization": self._perform_process_optimization,
            "integrated_optimization": self._perform_integrated_optimization
        }
        
        method = task_methods.get(task_type)
        if not method:
            raise AgentExecutionError(f"未実装のタスクタイプ: {task_type}")
            
        return await method(params, metrics)

    async def _perform_efficiency_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究効率・ワークフローの最適化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            current_efficiency = params.get("current_efficiency", "moderate")
            optimization_goals = params.get("optimization_goals", "speed_and_quality")
            constraints = params.get("constraints", [])
            
            # キャッシュキー生成
            cache_key = self._generate_cache_key(section_id, "efficiency_optimization", optimization_goals, content)
            
            # キャッシュチェック
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            constraints_str = ", ".join(constraints) if constraints else "制約なし"
            
            prompt = f"""
研究論文の以下の内容について、効率・ワークフローの最適化を行ってください。

【研究内容】
{content}

【現在の効率レベル】
{current_efficiency}

【最適化目標】
{optimization_goals}

【制約条件】
{constraints_str}

【効率最適化指示】
以下の観点から包括的な効率最適化を行い、JSON形式で回答してください：

1. **ワークフロー分析**: 現在のワークフロー分析・ボトルネック特定
2. **プロセス改善**: 効率的なプロセス設計・改善策
3. **自動化機会**: 自動化可能な作業の特定
4. **ツール最適化**: 効率向上ツール・技術の活用
5. **時間配分**: 最適な時間配分・優先順位付け
6. **並列化**: 並列実行可能な作業の特定
7. **標準化**: 作業標準化・テンプレート化
8. **継続改善**: 継続的効率改善の仕組み

{{
    "efficiency_analysis": {{
        "current_state_assessment": {{
            "workflow_evaluation": "現在のワークフロー評価",
            "bottleneck_identification": [
                {{
                    "bottleneck": "ボトルネック箇所",
                    "impact": "high|medium|low",
                    "root_cause": "根本原因",
                    "frequency": "発生頻度",
                    "time_loss": "時間損失（推定）"
                }}
            ],
            "efficiency_score": 0.0-1.0,
            "waste_areas": ["無駄・非効率領域"]
        }},
        "improvement_opportunities": [
            {{
                "opportunity": "改善機会",
                "type": "process|tool|method|structure|automation",
                "potential_gain": 0.0-1.0,
                "implementation_effort": "high|medium|low",
                "priority": "high|medium|low",
                "expected_roi": "期待投資収益率"
            }}
        ]
    }},
    "optimization_strategies": {{
        "workflow_redesign": {{
            "optimized_workflow": "最適化されたワークフロー",
            "key_changes": ["主要変更点"],
            "efficiency_improvements": ["効率改善点"],
            "implementation_steps": ["実装ステップ"],
            "expected_benefits": ["期待される利益"]
        }},
        "automation_recommendations": [
            {{
                "task": "自動化対象タスク",
                "automation_approach": "自動化アプローチ",
                "tools_required": ["必要ツール"],
                "time_savings": "時間節約効果",
                "complexity": "実装複雑度",
                "maintenance_requirements": "維持要件"
            }}
        ],
        "tool_optimization": [
            {{
                "category": "ツールカテゴリ",
                "recommended_tools": ["推奨ツール"],
                "integration_strategy": "統合戦略",
                "learning_curve": "習得曲線",
                "efficiency_gain": 0.0-1.0
            }}
        ]
    }},
    "process_improvements": {{
        "standardization_opportunities": [
            {{
                "area": "標準化領域",
                "standardization_approach": "標準化アプローチ",
                "template_needs": ["必要テンプレート"],
                "consistency_benefits": "一貫性向上効果"
            }}
        ],
        "parallelization_strategies": [
            {{
                "parallel_tasks": "並列実行タスク",
                "coordination_mechanism": "調整メカニズム",
                "time_reduction": "時間短縮効果",
                "resource_requirements": ["リソース要件"]
            }}
        ],
        "quality_checkpoints": [
            {{
                "checkpoint": "品質チェックポイント",
                "frequency": "チェック頻度",
                "criteria": ["チェック基準"],
                "corrective_actions": ["是正措置"]
            }}
        ]
    }},
    "implementation_plan": {{
        "phased_approach": [
            {{
                "phase": "実装段階",
                "duration": "期間",
                "focus_areas": ["重点領域"],
                "deliverables": ["成果物"],
                "success_metrics": ["成功指標"],
                "risk_mitigation": ["リスク軽減策"]
            }}
        ],
        "resource_requirements": {{
            "human_resources": "人的リソース要件",
            "technology_resources": "技術リソース要件",
            "financial_investment": "金銭的投資",
            "time_commitment": "時間コミット"
        }},
        "change_management": {{
            "communication_strategy": "コミュニケーション戦略",
            "training_needs": ["研修ニーズ"],
            "resistance_management": "抵抗管理",
            "adoption_support": "採用支援"
        }}
    }},
    "performance_measurement": {{
        "efficiency_kpis": [
            {{
                "kpi": "効率性主要業績指標",
                "measurement_method": "測定方法",
                "baseline": "ベースライン値",
                "target": "目標値",
                "monitoring_frequency": "監視頻度"
            }}
        ],
        "improvement_tracking": "改善追跡方法",
        "benchmark_comparisons": ["ベンチマーク比較"],
        "continuous_monitoring": "継続監視体制"
    }},
    "risk_considerations": [
        {{
            "risk": "最適化リスク",
            "probability": "high|medium|low",
            "impact": "high|medium|low",
            "mitigation_strategy": "軽減戦略",
            "contingency_plan": "緊急時対応"
        }}
    ],
    "optimization_evaluation": {{
        "efficiency_improvement": 0.0-1.0,
        "implementation_feasibility": 0.0-1.0,
        "cost_effectiveness": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "overall_optimization_score": 0.0-1.0
    }},
    "recommendations": [
        "効率最適化のための主要推奨事項"
    ]
}}
"""
            
            # OpenAI API呼び出し
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "efficiency_optimization",
                "section_id": section_id,
                "current_efficiency": current_efficiency,
                "optimization_goals": optimization_goals,
                "constraints": constraints,
                "optimization_result": result_data,
                "bottlenecks_count": len(result_data.get("efficiency_analysis", {}).get("current_state_assessment", {}).get("bottleneck_identification", [])),
                "improvement_opportunities_count": len(result_data.get("efficiency_analysis", {}).get("improvement_opportunities", [])),
                "automation_recommendations_count": len(result_data.get("optimization_strategies", {}).get("automation_recommendations", [])),
                "overall_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"効率最適化エラー: {e}")

    async def _perform_quality_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究品質・アウトプット品質の最適化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            quality_standards = params.get("quality_standards", "high")
            quality_dimensions = params.get("quality_dimensions", ["accuracy", "rigor", "clarity"])
            
            cache_key = self._generate_cache_key(section_id, "quality_optimization", quality_standards, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            dimensions_str = ", ".join(quality_dimensions)
            
            prompt = f"""
研究論文の以下の内容について、品質・アウトプット品質の最適化を行ってください。

【研究内容】
{content}

【品質基準】
{quality_standards}

【品質次元】
{dimensions_str}

【品質最適化指示】
以下の観点から包括的な品質最適化を行い、JSON形式で回答してください：

1. **品質評価**: 現在の品質レベル・問題点の評価
2. **品質基準**: 明確な品質基準・目標の設定
3. **品質保証**: 品質保証プロセス・仕組みの構築
4. **品質管理**: 継続的品質管理・監視体制
5. **品質改善**: 具体的品質改善策の策定
6. **検証体制**: 品質検証・バリデーション体制
7. **フィードバック**: 品質フィードバックループ
8. **持続的向上**: 持続的品質向上の仕組み

{{
    "quality_assessment": {{
        "current_quality_analysis": {{
            "overall_quality_score": 0.0-1.0,
            "dimension_scores": {{
                "accuracy": 0.0-1.0,
                "rigor": 0.0-1.0,
                "clarity": 0.0-1.0,
                "completeness": 0.0-1.0,
                "consistency": 0.0-1.0,
                "originality": 0.0-1.0,
                "relevance": 0.0-1.0,
                "impact": 0.0-1.0
            }},
            "quality_gaps": [
                {{
                    "gap": "品質ギャップ",
                    "severity": "high|medium|low",
                    "impact_area": "影響領域",
                    "root_cause": "根本原因",
                    "improvement_priority": "改善優先度"
                }}
            ],
            "strength_areas": ["品質強化領域"]
        }},
        "benchmark_analysis": {{
            "industry_standards": "業界標準との比較",
            "best_practices": ["ベストプラクティス参照"],
            "competitive_position": "競争ポジション",
            "improvement_potential": "改善ポテンシャル"
        }}
    }},
    "quality_optimization_strategies": {{
        "accuracy_enhancement": [
            {{
                "strategy": "精度向上戦略",
                "implementation": "実装方法",
                "tools_methods": ["ツール・手法"],
                "validation_approach": "検証アプローチ",
                "expected_improvement": 0.0-1.0
            }}
        ],
        "rigor_strengthening": [
            {{
                "approach": "厳密性強化アプローチ",
                "methodology_improvements": ["方法論改善"],
                "evidence_requirements": ["証拠要件"],
                "peer_review_integration": "査読統合",
                "quality_assurance": "品質保証策"
            }}
        ],
        "clarity_optimization": [
            {{
                "clarity_aspect": "明確性側面",
                "improvement_technique": "改善技法",
                "target_audience": "対象読者",
                "communication_enhancement": "コミュニケーション向上",
                "readability_score": 0.0-1.0
            }}
        ]
    }},
    "quality_assurance_framework": {{
        "qa_processes": [
            {{
                "process": "品質保証プロセス",
                "stage": "research|writing|review|publication",
                "activities": ["活動"],
                "checkpoints": ["チェックポイント"],
                "criteria": ["基準"],
                "responsible_party": "責任者"
            }}
        ],
        "quality_gates": [
            {{
                "gate": "品質ゲート",
                "entry_criteria": ["入力基準"],
                "exit_criteria": ["出力基準"],
                "approval_process": "承認プロセス",
                "escalation_procedure": "エスカレーション手順"
            }}
        ],
        "quality_metrics": [
            {{
                "metric": "品質指標",
                "measurement_method": "測定方法",
                "target_value": "目標値",
                "monitoring_frequency": "監視頻度",
                "corrective_actions": ["是正措置"]
            }}
        ]
    }},
    "verification_validation": {{
        "internal_verification": [
            {{
                "verification_type": "内部検証タイプ",
                "scope": "検証範囲",
                "methodology": "検証方法論",
                "frequency": "実施頻度",
                "documentation": "文書化要件"
            }}
        ],
        "external_validation": [
            {{
                "validation_approach": "外部バリデーションアプローチ",
                "validator_profile": "検証者プロファイル",
                "validation_criteria": ["検証基準"],
                "feedback_integration": "フィードバック統合"
            }}
        ],
        "peer_review_optimization": {{
            "reviewer_selection": "査読者選択戦略",
            "review_process": "査読プロセス最適化",
            "feedback_utilization": "フィードバック活用",
            "quality_improvement": "品質改善統合"
        }}
    }},
    "continuous_improvement": {{
        "feedback_loops": [
            {{
                "feedback_source": "フィードバック源",
                "collection_method": "収集方法",
                "analysis_approach": "分析アプローチ",
                "improvement_integration": "改善統合",
                "response_time": "応答時間"
            }}
        ],
        "learning_mechanisms": [
            {{
                "learning_type": "学習タイプ",
                "knowledge_capture": "知識獲得",
                "knowledge_application": "知識適用",
                "sharing_strategy": "共有戦略"
            }}
        ],
        "innovation_integration": {{
            "innovation_sources": ["革新源"],
            "adoption_criteria": "採用基準",
            "pilot_testing": "パイロットテスト",
            "scaling_strategy": "スケーリング戦略"
        }}
    }},
    "technology_enablers": {{
        "quality_tools": [
            {{
                "tool": "品質ツール",
                "application": "適用分野",
                "benefits": ["利益"],
                "implementation_requirements": ["実装要件"],
                "roi_estimate": "投資収益率推定"
            }}
        ],
        "automation_opportunities": ["自動化機会"],
        "ai_ml_applications": ["AI・ML活用"],
        "digital_transformation": "デジタル変革"
    }},
    "implementation_roadmap": {{
        "improvement_phases": [
            {{
                "phase": "改善段階",
                "duration": "期間",
                "focus_areas": ["重点領域"],
                "key_activities": ["主要活動"],
                "success_criteria": ["成功基準"],
                "resource_requirements": ["リソース要件"]
            }}
        ],
        "quick_wins": [
            {{
                "improvement": "即効改善",
                "implementation_time": "実装期間",
                "expected_benefit": "期待される利益",
                "effort_required": "必要努力"
            }}
        ],
        "long_term_initiatives": ["長期イニシアティブ"]
    }},
    "risk_management": {{
        "quality_risks": [
            {{
                "risk": "品質リスク",
                "probability": "high|medium|low",
                "impact": "high|medium|low",
                "mitigation_strategy": "軽減戦略",
                "monitoring_approach": "監視アプローチ"
            }}
        ],
        "risk_mitigation_plan": "リスク軽減計画"
    }},
    "optimization_evaluation": {{
        "quality_improvement_potential": 0.0-1.0,
        "implementation_complexity": 0.0-1.0,
        "resource_requirements": 0.0-1.0,
        "time_to_value": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "overall_quality_optimization_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "品質最適化のための戦略的推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "quality_optimization",
                "section_id": section_id,
                "quality_standards": quality_standards,
                "quality_dimensions": quality_dimensions,
                "optimization_result": result_data,
                "quality_gaps_count": len(result_data.get("quality_assessment", {}).get("current_quality_analysis", {}).get("quality_gaps", [])),
                "qa_processes_count": len(result_data.get("quality_assurance_framework", {}).get("qa_processes", [])),
                "current_quality_score": result_data.get("quality_assessment", {}).get("current_quality_analysis", {}).get("overall_quality_score", 0.0),
                "overall_quality_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_quality_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"品質最適化エラー: {e}")

    async def _perform_resource_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """リソース配分・活用の最適化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            available_resources = params.get("available_resources", {})
            resource_constraints = params.get("resource_constraints", [])
            
            cache_key = self._generate_cache_key(section_id, "resource_optimization", "allocation", content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            resources_str = json.dumps(available_resources, ensure_ascii=False) if available_resources else "リソース情報なし"
            constraints_str = ", ".join(resource_constraints) if resource_constraints else "制約なし"
            
            prompt = f"""
研究論文の以下の内容について、リソース配分・活用の最適化を行ってください。

【研究内容】
{content}

【利用可能リソース】
{resources_str}

【リソース制約】
{constraints_str}

【リソース最適化指示】
以下の観点から包括的なリソース最適化を行い、JSON形式で回答してください：

1. **リソース分析**: 現在のリソース状況・活用状況分析
2. **配分最適化**: 最適なリソース配分戦略
3. **効率向上**: リソース活用効率の向上策
4. **制約管理**: リソース制約下での最適化
5. **優先順位**: リソース投入優先順位の決定
6. **代替策**: リソース代替・補完策
7. **スケーリング**: リソーススケーリング戦略
8. **ROI最適化**: リソース投資収益率の最大化

{{
    "resource_analysis": {{
        "current_resource_assessment": {{
            "human_resources": {{
                "available_capacity": "利用可能人的キャパシティ",
                "skill_distribution": ["スキル分布"],
                "utilization_rate": 0.0-1.0,
                "bottlenecks": ["人的リソースボトルネック"],
                "optimization_potential": 0.0-1.0
            }},
            "financial_resources": {{
                "budget_allocation": "予算配分",
                "spending_efficiency": 0.0-1.0,
                "cost_centers": ["コストセンター"],
                "optimization_opportunities": ["最適化機会"],
                "roi_current": "現在のROI推定"
            }},
            "technological_resources": {{
                "infrastructure_utilization": 0.0-1.0,
                "tool_effectiveness": 0.0-1.0,
                "technology_gaps": ["技術ギャップ"],
                "upgrade_needs": ["アップグレード必要性"],
                "integration_opportunities": ["統合機会"]
            }},
            "time_resources": {{
                "time_allocation": "時間配分",
                "productivity_metrics": ["生産性指標"],
                "time_waste_areas": ["時間浪費領域"],
                "optimization_potential": 0.0-1.0
            }}
        }},
        "resource_gaps": [
            {{
                "gap_type": "ギャップタイプ",
                "description": "ギャップ詳細",
                "impact": "high|medium|low",
                "urgency": "high|medium|low",
                "filling_strategies": ["ギャップ解決戦略"]
            }}
        ]
    }},
    "optimization_strategies": {{
        "allocation_optimization": [
            {{
                "resource_type": "リソースタイプ",
                "current_allocation": "現在の配分",
                "optimized_allocation": "最適化された配分",
                "reallocation_rationale": "再配分根拠",
                "expected_improvement": 0.0-1.0,
                "implementation_timeline": "実装期間"
            }}
        ],
        "efficiency_improvements": [
            {{
                "improvement_area": "改善領域",
                "current_efficiency": 0.0-1.0,
                "target_efficiency": 0.0-1.0,
                "improvement_methods": ["改善手法"],
                "resource_requirements": ["必要リソース"],
                "timeline": "実装期間"
            }}
        ],
        "capacity_optimization": [
            {{
                "capacity_area": "キャパシティ領域",
                "utilization_increase": "活用率向上",
                "bottleneck_resolution": "ボトルネック解決",
                "scaling_strategy": "スケーリング戦略",
                "investment_requirements": ["投資要件"]
            }}
        ]
    }},
    "constraint_management": {{
        "constraint_analysis": [
            {{
                "constraint": "制約",
                "type": "budget|time|skill|technology|regulatory",
                "severity": "high|medium|low",
                "workaround_strategies": ["回避戦略"],
                "relaxation_opportunities": ["緩和機会"],
                "trade_off_options": ["トレードオフ選択肢"]
            }}
        ],
        "constraint_optimization": [
            {{
                "optimization_approach": "最適化アプローチ",
                "constraint_handling": "制約対処",
                "alternative_solutions": ["代替ソリューション"],
                "expected_outcomes": ["期待される成果"]
            }}
        ]
    }},
    "prioritization_framework": {{
        "priority_criteria": [
            {{
                "criterion": "優先基準",
                "weight": 0.0-1.0,
                "description": "基準説明",
                "measurement": "測定方法"
            }}
        ],
        "resource_priorities": [
            {{
                "priority_level": "high|medium|low",
                "resource_allocation": "リソース配分",
                "justification": "正当化",
                "expected_impact": 0.0-1.0,
                "timeline": "実装期間"
            }}
        ],
        "trade_off_analysis": [
            {{
                "trade_off": "トレードオフ",
                "options": ["選択肢"],
                "evaluation": "評価",
                "recommendation": "推奨"
            }}
        ]
    }},
    "alternative_strategies": {{
        "resource_substitution": [
            {{
                "original_resource": "元のリソース",
                "substitute": "代替リソース",
                "substitution_ratio": "代替率",
                "cost_impact": "コスト影響",
                "performance_impact": "パフォーマンス影響",
                "feasibility": 0.0-1.0
            }}
        ],
        "outsourcing_opportunities": [
            {{
                "activity": "外部委託活動",
                "outsourcing_benefits": ["外部委託利益"],
                "cost_comparison": "コスト比較",
                "quality_considerations": ["品質考慮事項"],
                "risk_assessment": "リスク評価"
            }}
        ],
        "partnership_leverage": [
            {{
                "partnership_type": "パートナーシップタイプ",
                "resource_sharing": "リソース共有",
                "mutual_benefits": ["相互利益"],
                "collaboration_model": "協働モデル"
            }}
        ]
    }},
    "scaling_strategies": {{
        "scale_up_options": [
            {{
                "scaling_dimension": "スケーリング次元",
                "scaling_approach": "スケーリングアプローチ",
                "resource_requirements": ["リソース要件"],
                "scaling_timeline": "スケーリング期間",
                "expected_benefits": ["期待される利益"]
            }}
        ],
        "scale_down_scenarios": [
            {{
                "scenario": "縮小シナリオ",
                "resource_reduction": "リソース削減",
                "impact_mitigation": "影響軽減",
                "critical_preservation": ["重要保全事項"]
            }}
        ]
    }},
    "roi_optimization": {{
        "investment_analysis": [
            {{
                "investment_area": "投資領域",
                "investment_amount": "投資金額",
                "expected_return": "期待リターン",
                "payback_period": "回収期間",
                "risk_level": "high|medium|low",
                "strategic_value": 0.0-1.0
            }}
        ],
        "value_maximization": [
            {{
                "value_driver": "価値ドライバー",
                "optimization_lever": "最適化レバー",
                "implementation_approach": "実装アプローチ",
                "value_creation": "価値創造"
            }}
        ]
    }},
    "implementation_plan": {{
        "optimization_phases": [
            {{
                "phase": "最適化段階",
                "duration": "期間",
                "resource_focus": ["リソース重点"],
                "key_activities": ["主要活動"],
                "success_metrics": ["成功指標"],
                "dependencies": ["依存関係"]
            }}
        ],
        "change_management": {{
            "stakeholder_communication": "ステークホルダーコミュニケーション",
            "training_requirements": ["研修要件"],
            "resistance_management": "抵抗管理",
            "support_mechanisms": ["支援メカニズム"]
        }}
    }},
    "monitoring_evaluation": {{
        "performance_indicators": [
            {{
                "indicator": "パフォーマンス指標",
                "measurement_method": "測定方法",
                "target_value": "目標値",
                "monitoring_frequency": "監視頻度",
                "corrective_triggers": ["是正発動条件"]
            }}
        ],
        "optimization_tracking": "最適化追跡",
        "continuous_adjustment": "継続的調整",
        "feedback_integration": "フィードバック統合"
    }},
    "optimization_evaluation": {{
        "resource_efficiency_gain": 0.0-1.0,
        "cost_reduction_potential": 0.0-1.0,
        "performance_improvement": 0.0-1.0,
        "implementation_feasibility": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "overall_resource_optimization_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "リソース最適化のための戦略的推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "resource_optimization",
                "section_id": section_id,
                "available_resources": available_resources,
                "resource_constraints": resource_constraints,
                "optimization_result": result_data,
                "resource_gaps_count": len(result_data.get("resource_analysis", {}).get("resource_gaps", [])),
                "optimization_strategies_count": len(result_data.get("optimization_strategies", {}).get("allocation_optimization", [])),
                "overall_resource_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_resource_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"リソース最適化エラー: {e}")

    async def _perform_time_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """時間管理・スケジュール最適化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            timeline_constraints = params.get("timeline_constraints", "")
            priority_tasks = params.get("priority_tasks", [])
            
            cache_key = self._generate_cache_key(section_id, "time_optimization", "schedule", content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            priority_tasks_str = ", ".join(priority_tasks) if priority_tasks else "優先タスク指定なし"
            
            prompt = f"""
研究論文の以下の内容について、時間管理・スケジュール最適化を行ってください。

【研究内容】
{content}

【期間制約】
{timeline_constraints}

【優先タスク】
{priority_tasks_str}

【時間最適化指示】
以下の観点から包括的な時間最適化を行い、JSON形式で回答してください：

1. **時間分析**: 現在の時間配分・使用状況の分析
2. **スケジュール最適化**: 効率的なスケジュール設計
3. **優先順位付け**: タスク優先順位の最適化
4. **時間節約**: 時間節約機会の特定・活用
5. **並列処理**: 並列実行可能な作業の最大化
6. **デッドライン管理**: 効果的なデッドライン管理
7. **バッファ管理**: 適切なバッファ・余裕の確保
8. **生産性向上**: 時間あたり生産性の向上

{{
    "time_analysis": {{
        "current_time_allocation": {{
            "research_activities": [
                {{
                    "activity": "研究活動",
                    "time_spent": "時間配分",
                    "efficiency_rating": 0.0-1.0,
                    "value_contribution": 0.0-1.0,
                    "optimization_potential": 0.0-1.0
                }}
            ],
            "time_waste_identification": [
                {{
                    "waste_source": "時間浪費源",
                    "time_lost": "損失時間",
                    "frequency": "high|medium|low",
                    "elimination_strategy": "排除戦略"
                }}
            ],
            "productivity_patterns": [
                {{
                    "pattern": "生産性パターン",
                    "description": "パターン説明",
                    "optimization_opportunity": "最適化機会"
                }}
            ]
        }},
        "bottleneck_analysis": [
            {{
                "bottleneck": "時間ボトルネック",
                "impact": "high|medium|low",
                "root_cause": "根本原因",
                "resolution_strategy": "解決戦略",
                "time_savings_potential": "時間節約ポテンシャル"
            }}
        ]
    }},
    "schedule_optimization": {{
        "optimized_timeline": [
            {{
                "phase": "研究段階",
                "duration": "期間",
                "key_activities": ["主要活動"],
                "deliverables": ["成果物"],
                "dependencies": ["依存関係"],
                "resource_requirements": ["リソース要件"],
                "risk_factors": ["リスク要因"],
                "buffer_allocation": "バッファ配分"
            }}
        ],
        "critical_path": {{
            "critical_activities": ["クリティカル活動"],
            "path_duration": "クリティカルパス期間",
            "acceleration_opportunities": ["短縮機会"],
            "risk_mitigation": ["リスク軽減策"]
        }},
        "parallel_processing": [
            {{
                "parallel_tasks": ["並列タスク"],
                "coordination_requirements": "調整要件",
                "resource_implications": "リソース含意",
                "time_savings": "時間節約効果"
            }}
        ]
    }},
    "priority_optimization": {{
        "task_prioritization": [
            {{
                "task": "タスク",
                "priority_level": "high|medium|low",
                "urgency": "high|medium|low",
                "importance": "high|medium|low",
                "impact": "high|medium|low",
                "effort_required": "必要努力",
                "dependencies": ["依存関係"],
                "deadline": "期限"
            }}
        ],
        "prioritization_matrix": {{
            "high_impact_urgent": ["高影響・緊急タスク"],
            "high_impact_not_urgent": ["高影響・非緊急タスク"],
            "low_impact_urgent": ["低影響・緊急タスク"],
            "low_impact_not_urgent": ["低影響・非緊急タスク"]
        }},
        "focus_areas": [
            {{
                "focus_area": "重点領域",
                "time_allocation": "時間配分",
                "rationale": "根拠",
                "expected_outcomes": ["期待される成果"]
            }}
        ]
    }},
    "time_saving_strategies": {{
        "automation_opportunities": [
            {{
                "task": "自動化対象タスク",
                "automation_approach": "自動化アプローチ",
                "time_saved": "節約時間",
                "implementation_effort": "実装努力",
                "roi": "投資収益率"
            }}
        ],
        "delegation_opportunities": [
            {{
                "task": "委譲対象タスク",
                "delegation_target": "委譲先",
                "time_freed": "解放時間",
                "quality_considerations": ["品質考慮事項"]
            }}
        ],
        "elimination_candidates": [
            {{
                "activity": "削除候補活動",
                "elimination_rationale": "削除根拠",
                "time_recovered": "回収時間",
                "impact_assessment": "影響評価"
            }}
        ]
    }},
    "deadline_management": {{
        "milestone_planning": [
            {{
                "milestone": "マイルストーン",
                "target_date": "目標日",
                "completion_criteria": ["完了基準"],
                "dependencies": ["依存関係"],
                "risk_factors": ["リスク要因"],
                "contingency_plans": ["緊急時計画"]
            }}
        ],
        "buffer_strategy": {{
            "buffer_allocation": "バッファ配分戦略",
            "buffer_usage_rules": ["バッファ使用ルール"],
            "buffer_monitoring": "バッファ監視",
            "buffer_optimization": "バッファ最適化"
        }},
        "early_warning_system": [
            {{
                "warning_indicator": "早期警戒指標",
                "trigger_threshold": "発動閾値",
                "response_action": "対応アクション",
                "escalation_procedure": "エスカレーション手順"
            }}
        ]
    }},
    "productivity_enhancement": {{
        "efficiency_techniques": [
            {{
                "technique": "効率化技法",
                "application": "適用方法",
                "expected_improvement": 0.0-1.0,
                "implementation_requirements": ["実装要件"]
            }}
        ],
        "focus_optimization": {{
            "concentration_strategies": ["集中戦略"],
            "distraction_management": "妨害管理",
            "energy_management": "エネルギー管理",
            "optimal_work_periods": ["最適作業時間"]
        }},
        "tool_optimization": [
            {{
                "tool": "ツール",
                "time_saving_benefit": "時間節約効果",
                "learning_investment": "習得投資",
                "net_time_benefit": "正味時間効果"
            }}
        ]
    }},
    "flexibility_mechanisms": {{
        "adaptation_triggers": [
            {{
                "trigger": "適応発動条件",
                "response_options": ["対応選択肢"],
                "decision_criteria": ["判断基準"],
                "implementation_speed": "実装速度"
            }}
        ],
        "contingency_planning": [
            {{
                "scenario": "緊急時シナリオ",
                "impact_assessment": "影響評価",
                "response_strategy": "対応戦略",
                "resource_reallocation": "リソース再配分"
            }}
        ]
    }},
    "monitoring_control": {{
        "progress_tracking": [
            {{
                "tracking_metric": "進捗追跡指標",
                "measurement_frequency": "測定頻度",
                "reporting_format": "報告形式",
                "corrective_actions": ["是正措置"]
            }}
        ],
        "time_management_kpis": [
            {{
                "kpi": "時間管理KPI",
                "target_value": "目標値",
                "current_performance": "現在のパフォーマンス",
                "improvement_target": "改善目標"
            }}
        ]
    }},
    "optimization_evaluation": {{
        "time_efficiency_gain": 0.0-1.0,
        "schedule_reliability": 0.0-1.0,
        "productivity_improvement": 0.0-1.0,
        "deadline_adherence": 0.0-1.0,
        "stress_reduction": 0.0-1.0,
        "overall_time_optimization_score": 0.0-1.0
    }},
    "implementation_recommendations": [
        "時間最適化のための実装推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "time_optimization",
                "section_id": section_id,
                "timeline_constraints": timeline_constraints,
                "priority_tasks": priority_tasks,
                "optimization_result": result_data,
                "time_waste_sources_count": len(result_data.get("time_analysis", {}).get("current_time_allocation", {}).get("time_waste_identification", [])),
                "bottlenecks_count": len(result_data.get("time_analysis", {}).get("bottleneck_analysis", [])),
                "optimization_phases_count": len(result_data.get("schedule_optimization", {}).get("optimized_timeline", [])),
                "overall_time_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_time_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"時間最適化エラー: {e}")

    async def _perform_impact_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究成果・インパクトの最大化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            target_impact = params.get("target_impact", "academic_and_practical")
            impact_metrics = params.get("impact_metrics", ["citations", "applications"])
            
            cache_key = self._generate_cache_key(section_id, "impact_optimization", target_impact, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            metrics_str = ", ".join(impact_metrics)
            
            prompt = f"""
研究論文の以下の内容について、研究成果・インパクトの最大化を行ってください。

【研究内容】
{content}

【目標インパクト】
{target_impact}

【インパクト指標】
{metrics_str}

【インパクト最適化指示】
以下の観点から包括的なインパクト最大化を行い、JSON形式で回答してください：

1. **インパクト分析**: 潜在的インパクトの分析・評価
2. **価値最大化**: 研究価値・意義の最大化
3. **到達範囲**: インパクト到達範囲の拡大
4. **永続性**: 長期的インパクトの確保
5. **測定可能性**: インパクトの測定・評価体制
6. **増幅戦略**: インパクト増幅・拡散戦略
7. **応用促進**: 実用・応用促進によるインパクト
8. **レガシー構築**: 持続的レガシーの構築

{{
    "impact_assessment": {{
        "potential_impact_areas": [
            {{
                "impact_domain": "academic|practical|social|economic|policy|technological",
                "description": "インパクト内容",
                "target_audience": "対象受益者",
                "magnitude": "high|medium|low",
                "probability": "high|medium|low",
                "timeline": "short_term|medium_term|long_term",
                "measurement_approach": "測定アプローチ"
            }}
        ],
        "impact_pathways": [
            {{
                "pathway": "インパクト経路",
                "mechanism": "作用メカニズム",
                "intermediary_steps": ["中間段階"],
                "enabling_factors": ["促進要因"],
                "barriers": ["阻害要因"],
                "optimization_opportunities": ["最適化機会"]
            }}
        ],
        "baseline_impact_potential": 0.0-1.0
    }},
    "value_maximization_strategies": {{
        "content_optimization": [
            {{
                "optimization_area": "最適化領域",
                "current_value": "現在の価値",
                "enhancement_strategy": "価値向上戦略",
                "expected_improvement": 0.0-1.0,
                "implementation_approach": "実装アプローチ"
            }}
        ],
        "novelty_enhancement": [
            {{
                "novelty_aspect": "新規性側面",
                "enhancement_method": "向上方法",
                "uniqueness_score": 0.0-1.0,
                "competitive_advantage": "競争優位性"
            }}
        ],
        "significance_amplification": [
            {{
                "significance_dimension": "重要性次元",
                "amplification_strategy": "増幅戦略",
                "impact_multiplier": "インパクト倍率",
                "sustainability": "持続可能性"
            }}
        ]
    }},
    "reach_expansion": {{
        "audience_diversification": [
            {{
                "audience_segment": "読者セグメント",
                "current_reach": "現在のリーチ",
                "expansion_strategy": "拡大戦略",
                "communication_approach": "コミュニケーションアプローチ",
                "expected_reach": "期待リーチ"
            }}
        ],
        "channel_optimization": [
            {{
                "channel": "チャネル",
                "optimization_approach": "最適化アプローチ",
                "reach_potential": "リーチポテンシャル",
                "engagement_quality": 0.0-1.0
            }}
        ],
        "geographic_expansion": [
            {{
                "region": "地域",
                "expansion_rationale": "拡大根拠",
                "localization_needs": ["現地化必要性"],
                "cultural_considerations": ["文化的考慮事項"]
            }}
        ]
    }},
    "persistence_strategies": {{
        "longevity_factors": [
            {{
                "factor": "持続性要因",
                "contribution": "貢献度",
                "maintenance_strategy": "維持戦略",
                "reinforcement_mechanisms": ["強化メカニズム"]
            }}
        ],
        "legacy_building": [
            {{
                "legacy_type": "レガシータイプ",
                "building_approach": "構築アプローチ",
                "preservation_method": "保存方法",
                "transmission_mechanism": "伝達メカニズム"
            }}
        ],
        "institutional_embedding": [
            {{
                "institution": "機関",
                "embedding_strategy": "埋め込み戦略",
                "integration_level": "統合レベル",
                "sustainability_assurance": "持続性保証"
            }}
        ]
    }},
    "amplification_mechanisms": {{
        "network_effects": [
            {{
                "network": "ネットワーク",
                "activation_strategy": "活性化戦略",
                "viral_potential": 0.0-1.0,
                "engagement_tactics": ["エンゲージメント戦術"]
            }}
        ],
        "multiplicative_impacts": [
            {{
                "multiplier_source": "増幅源",
                "multiplication_factor": "増幅係数",
                "activation_trigger": "活性化トリガー",
                "sustainability": "持続可能性"
            }}
        ],
        "cascade_effects": [
            {{
                "cascade_trigger": "連鎖発動要因",
                "cascade_sequence": ["連鎖順序"],
                "amplification_potential": 0.0-1.0,
                "control_mechanisms": ["制御メカニズム"]
            }}
        ]
    }},
    "application_facilitation": {{
        "practical_applications": [
            {{
                "application": "実用化応用",
                "facilitation_strategy": "促進戦略",
                "implementation_support": "実装支援",
                "adoption_barriers": ["採用障壁"],
                "barrier_removal_plan": "障壁除去計画"
            }}
        ],
        "technology_transfer": [
            {{
                "transfer_mechanism": "移転メカニズム",
                "target_recipient": "対象受益者",
                "transfer_process": "移転プロセス",
                "success_factors": ["成功要因"]
            }}
        ],
        "commercialization_support": [
            {{
                "commercialization_path": "商業化経路",
                "support_strategy": "支援戦略",
                "stakeholder_engagement": "ステークホルダーエンゲージメント",
                "value_proposition": "価値提案"
            }}
        ]
    }},
    "measurement_optimization": {{
        "impact_indicators": [
            {{
                "indicator": "インパクト指標",
                "measurement_method": "測定方法",
                "data_sources": ["データソース"],
                "collection_frequency": "収集頻度",
                "target_benchmarks": "目標ベンチマーク"
            }}
        ],
        "tracking_systems": [
            {{
                "system": "追跡システム",
                "capabilities": ["機能"],
                "implementation_requirements": ["実装要件"],
                "maintenance_needs": ["維持必要性"]
            }}
        ],
        "evaluation_framework": {{
            "evaluation_criteria": ["評価基準"],
            "assessment_methodology": "評価方法論",
            "reporting_structure": "報告構造",
            "feedback_integration": "フィードバック統合"
        }}
    }},
    "optimization_implementation": {{
        "implementation_phases": [
            {{
                "phase": "実装段階",
                "duration": "期間",
                "key_activities": ["主要活動"],
                "resource_requirements": ["リソース要件"],
                "success_metrics": ["成功指標"],
                "risk_factors": ["リスク要因"]
            }}
        ],
        "resource_allocation": {{
            "budget_distribution": "予算配分",
            "time_investment": "時間投資",
            "skill_requirements": ["必要スキル"],
            "infrastructure_needs": ["インフラニーズ"]
        }},
        "stakeholder_engagement": [
            {{
                "stakeholder": "ステークホルダー",
                "engagement_strategy": "エンゲージメント戦略",
                "value_proposition": "価値提案",
                "collaboration_model": "協働モデル"
            }}
        ]
    }},
    "optimization_evaluation": {{
        "impact_amplification": 0.0-1.0,
        "reach_expansion": 0.0-1.0,
        "value_enhancement": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "measurability": 0.0-1.0,
        "overall_impact_optimization_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "インパクト最適化のための戦略的推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "impact_optimization",
                "section_id": section_id,
                "target_impact": target_impact,
                "impact_metrics": impact_metrics,
                "optimization_result": result_data,
                "potential_impact_areas_count": len(result_data.get("impact_assessment", {}).get("potential_impact_areas", [])),
                "amplification_mechanisms_count": len(result_data.get("amplification_mechanisms", {}).get("network_effects", [])),
                "baseline_impact_potential": result_data.get("impact_assessment", {}).get("baseline_impact_potential", 0.0),
                "overall_impact_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_impact_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"インパクト最適化エラー: {e}")

    async def _perform_cost_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """コスト効率・費用対効果の改善"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            budget_constraints = params.get("budget_constraints", "")
            cost_targets = params.get("cost_targets", "efficiency_improvement")
            
            cache_key = self._generate_cache_key(section_id, "cost_optimization", cost_targets, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、コスト効率・費用対効果の改善を行ってください。

【研究内容】
{content}

【予算制約】
{budget_constraints}

【コスト目標】
{cost_targets}

【コスト最適化指示】
以下の観点から包括的なコスト最適化を行い、JSON形式で回答してください：

1. **コスト分析**: 現在のコスト構造・配分の分析
2. **効率改善**: コスト効率の向上策
3. **削減機会**: コスト削減機会の特定
4. **価値最適化**: コストパフォーマンスの最適化
5. **代替手法**: 低コスト代替手法の検討
6. **投資優先度**: コスト投資の優先順位付け
7. **ROI向上**: 投資収益率の改善
8. **持続可能性**: 持続可能なコスト管理

{{
    "cost_analysis": {{
        "current_cost_structure": {{
            "cost_categories": [
                {{
                    "category": "コストカテゴリ",
                    "amount": "金額",
                    "percentage": "割合",
                    "necessity": "high|medium|low",
                    "optimization_potential": 0.0-1.0,
                    "impact_on_quality": "品質への影響"
                }}
            ],
            "cost_drivers": [
                {{
                    "driver": "コストドライバー",
                    "impact": "high|medium|low",
                    "controllability": "high|medium|low",
                    "optimization_strategy": "最適化戦略"
                }}
            ],
            "cost_efficiency_ratio": 0.0-1.0
        }},
        "benchmark_analysis": {{
            "industry_benchmarks": "業界ベンチマーク",
            "best_practices": ["ベストプラクティス"],
            "performance_gaps": ["パフォーマンスギャップ"],
            "improvement_potential": "改善ポテンシャル"
        }}
    }},
    "optimization_opportunities": {{
        "cost_reduction_strategies": [
            {{
                "strategy": "コスト削減戦略",
                "target_area": "対象領域",
                "reduction_potential": 0.0-1.0,
                "implementation_difficulty": "high|medium|low",
                "quality_impact": "品質への影響",
                "timeline": "実装期間",
                "risk_level": "high|medium|low"
            }}
        ],
        "efficiency_improvements": [
            {{
                "improvement": "効率改善",
                "current_efficiency": 0.0-1.0,
                "target_efficiency": 0.0-1.0,
                "implementation_cost": "実装コスト",
                "payback_period": "回収期間",
                "net_benefit": "正味利益"
            }}
        ],
        "process_optimization": [
            {{
                "process": "プロセス",
                "optimization_approach": "最適化アプローチ",
                "cost_impact": "コスト影響",
                "efficiency_gain": 0.0-1.0,
                "implementation_requirements": ["実装要件"]
            }}
        ]
    }},
    "alternative_approaches": {{
        "low_cost_alternatives": [
            {{
                "alternative": "低コスト代替案",
                "original_approach": "元のアプローチ",
                "cost_reduction": "コスト削減額",
                "quality_comparison": "品質比較",
                "feasibility": 0.0-1.0,
                "trade_offs": ["トレードオフ"]
            }}
        ],
        "resource_substitution": [
            {{
                "original_resource": "元のリソース",
                "substitute": "代替リソース",
                "cost_difference": "コスト差",
                "performance_impact": "パフォーマンス影響",
                "availability": "入手可能性"
            }}
        ],
        "outsourcing_evaluation": [
            {{
                "activity": "活動",
                "internal_cost": "内製コスト",
                "external_cost": "外製コスト",
                "quality_considerations": ["品質考慮事項"],
                "control_implications": ["統制含意"],
                "recommendation": "推奨"
            }}
        ]
    }},
    "value_optimization": {{
        "value_engineering": [
            {{
                "component": "構成要素",
                "current_value": "現在の価値",
                "cost": "コスト",
                "value_cost_ratio": "価値コスト比",
                "optimization_strategy": "最適化戦略",
                "expected_improvement": 0.0-1.0
            }}
        ],
        "prioritization_matrix": {{
            "high_value_low_cost": ["高価値低コスト項目"],
            "high_value_high_cost": ["高価値高コスト項目"],
            "low_value_low_cost": ["低価値低コスト項目"],
            "low_value_high_cost": ["低価値高コスト項目"]
        }},
        "investment_optimization": [
            {{
                "investment": "投資",
                "expected_return": "期待リターン",
                "risk_level": "high|medium|low",
                "strategic_importance": 0.0-1.0,
                "recommendation": "推奨"
            }}
        ]
    }},
    "roi_enhancement": {{
        "roi_analysis": [
            {{
                "investment_area": "投資領域",
                "investment_amount": "投資金額",
                "expected_return": "期待リターン",
                "payback_period": "回収期間",
                "irr": "内部収益率",
                "npv": "正味現在価値",
                "risk_adjusted_return": "リスク調整リターン"
            }}
        ],
        "return_maximization": [
            {{
                "strategy": "リターン最大化戦略",
                "implementation": "実装方法",
                "expected_benefit": "期待される利益",
                "resource_requirements": ["リソース要件"]
            }}
        ],
        "risk_return_optimization": [
            {{
                "risk_level": "リスクレベル",
                "return_potential": "リターンポテンシャル",
                "optimization_approach": "最適化アプローチ",
                "portfolio_balance": "ポートフォリオバランス"
            }}
        ]
    }},
    "cost_control_mechanisms": {{
        "budgeting_optimization": {{
            "budget_allocation": "予算配分",
            "allocation_criteria": ["配分基準"],
            "flexibility_mechanisms": ["柔軟性メカニズム"],
            "monitoring_system": "監視システム"
        }},
        "cost_monitoring": [
            {{
                "monitoring_area": "監視領域",
                "key_indicators": ["主要指標"],
                "alert_thresholds": ["警告閾値"],
                "corrective_actions": ["是正措置"]
            }}
        ],
        "variance_management": {{
            "variance_tracking": "差異追跡",
            "analysis_methodology": "分析方法論",
            "response_protocols": ["対応プロトコル"],
            "continuous_improvement": "継続改善"
        }}
    }},
    "sustainability_measures": {{
        "long_term_cost_management": [
            {{
                "strategy": "長期コスト管理戦略",
                "sustainability_factors": ["持続性要因"],
                "maintenance_requirements": ["維持要件"],
                "evolution_plan": "発展計画"
            }}
        ],
        "scalability_considerations": [
            {{
                "scaling_dimension": "スケーリング次元",
                "cost_implications": "コスト含意",
                "efficiency_preservation": "効率性維持",
                "adaptation_strategies": ["適応戦略"]
            }}
        ]
    }},
    "implementation_plan": {{
        "optimization_phases": [
            {{
                "phase": "最適化段階",
                "duration": "期間",
                "cost_focus": ["コスト重点"],
                "expected_savings": "期待節約額",
                "implementation_cost": "実装コスト",
                "net_benefit": "正味利益"
            }}
        ],
        "quick_wins": [
            {{
                "opportunity": "即効機会",
                "savings_potential": "節約ポテンシャル",
                "implementation_ease": "実装容易性",
                "timeline": "実装期間"
            }}
        ],
        "change_management": {{
            "stakeholder_buy_in": "ステークホルダー賛同",
            "communication_plan": "コミュニケーション計画",
            "training_requirements": ["研修要件"],
            "resistance_mitigation": "抵抗軽減"
        }}
    }},
    "optimization_evaluation": {{
        "cost_reduction_potential": 0.0-1.0,
        "efficiency_improvement": 0.0-1.0,
        "roi_enhancement": 0.0-1.0,
        "implementation_feasibility": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "overall_cost_optimization_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "コスト最適化のための戦略的推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "cost_optimization",
                "section_id": section_id,
                "budget_constraints": budget_constraints,
                "cost_targets": cost_targets,
                "optimization_result": result_data,
                "cost_categories_count": len(result_data.get("cost_analysis", {}).get("current_cost_structure", {}).get("cost_categories", [])),
                "reduction_strategies_count": len(result_data.get("optimization_opportunities", {}).get("cost_reduction_strategies", [])),
                "cost_efficiency_ratio": result_data.get("cost_analysis", {}).get("current_cost_structure", {}).get("cost_efficiency_ratio", 0.0),
                "overall_cost_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_cost_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"コスト最適化エラー: {e}")

    async def _perform_process_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究プロセス・手法の最適化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            current_processes = params.get("current_processes", [])
            optimization_focus = params.get("optimization_focus", "efficiency_and_quality")
            
            cache_key = self._generate_cache_key(section_id, "process_optimization", optimization_focus, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            processes_str = ", ".join(current_processes) if current_processes else "プロセス情報なし"
            
            prompt = f"""
研究論文の以下の内容について、研究プロセス・手法の最適化を行ってください。

【研究内容】
{content}

【現在のプロセス】
{processes_str}

【最適化焦点】
{optimization_focus}

【プロセス最適化指示】
以下の観点から包括的なプロセス最適化を行い、JSON形式で回答してください：

1. **プロセス分析**: 現在のプロセスの分析・評価
2. **ボトルネック特定**: プロセスボトルネックの特定
3. **フロー最適化**: プロセスフローの最適化
4. **標準化**: プロセス標準化・体系化
5. **自動化**: プロセス自動化の機会
6. **品質統合**: 品質保証のプロセス統合
7. **継続改善**: 継続的プロセス改善
8. **ベストプラクティス**: ベストプラクティスの導入

{{
    "process_analysis": {{
        "current_process_assessment": [
            {{
                "process": "プロセス",
                "purpose": "目的",
                "current_efficiency": 0.0-1.0,
                "quality_output": 0.0-1.0,
                "resource_consumption": "リソース消費",
                "cycle_time": "サイクルタイム",
                "error_rate": 0.0-1.0,
                "stakeholder_satisfaction": 0.0-1.0,
                "improvement_potential": 0.0-1.0
            }}
        ],
        "process_mapping": {{
            "key_processes": ["主要プロセス"],
            "process_dependencies": ["プロセス依存関係"],
            "information_flow": "情報フロー",
            "decision_points": ["意思決定ポイント"],
            "handoff_points": ["引継ぎポイント"]
        }},
        "performance_gaps": [
            {{
                "gap": "パフォーマンスギャップ",
                "current_state": "現状",
                "desired_state": "望ましい状態",
                "gap_size": 0.0-1.0,
                "root_causes": ["根本原因"]
            }}
        ]
    }},
    "bottleneck_identification": {{
        "process_bottlenecks": [
            {{
                "bottleneck": "ボトルネック",
                "location": "発生箇所",
                "severity": "high|medium|low",
                "impact": "high|medium|low",
                "frequency": "発生頻度",
                "root_cause": "根本原因",
                "current_workarounds": ["現在の回避策"],
                "optimization_priority": "high|medium|low"
            }}
        ],
        "constraint_analysis": [
            {{
                "constraint": "制約",
                "type": "resource|policy|technology|skill|external",
                "impact_on_throughput": "スループットへの影響",
                "relaxation_possibilities": ["緩和可能性"],
                "alternative_approaches": ["代替アプローチ"]
            }}
        ]
    }},
    "flow_optimization": {{
        "optimized_workflow": {{
            "redesigned_process": "再設計されたプロセス",
            "key_improvements": ["主要改善点"],
            "eliminated_steps": ["削除ステップ"],
            "added_steps": ["追加ステップ"],
            "reordered_activities": ["順序変更活動"],
            "parallel_opportunities": ["並列化機会"]
        }},
        "efficiency_enhancements": [
            {{
                "enhancement": "効率向上策",
                "target_process": "対象プロセス",
                "improvement_method": "改善手法",
                "expected_benefit": 0.0-1.0,
                "implementation_effort": "high|medium|low",
                "risk_level": "high|medium|low"
            }}
        ],
        "integration_improvements": [
            {{
                "integration": "統合改善",
                "processes_involved": ["関与プロセス"],
                "integration_benefits": ["統合利益"],
                "coordination_mechanisms": ["調整メカニズム"]
            }}
        ]
    }},
    "standardization_strategies": {{
        "standardization_opportunities": [
            {{
                "area": "標準化領域",
                "current_variability": "現在のばらつき",
                "standardization_approach": "標準化アプローチ",
                "benefits": ["利益"],
                "implementation_challenges": ["実装課題"],
                "success_factors": ["成功要因"]
            }}
        ],
        "best_practice_codification": [
            {{
                "best_practice": "ベストプラクティス",
                "source": "出典",
                "applicability": "適用可能性",
                "adaptation_requirements": ["適応要件"],
                "training_needs": ["研修ニーズ"]
            }}
        ],
        "template_development": [
            {{
                "template_type": "テンプレートタイプ",
                "purpose": "目的",
                "components": ["構成要素"],
                "customization_options": ["カスタマイゼーション選択肢"],
                "maintenance_requirements": ["維持要件"]
            }}
        ]
    }},
    "automation_opportunities": {{
        "automation_candidates": [
            {{
                "process": "自動化候補プロセス",
                "automation_type": "rule_based|ai_driven|workflow|integration",
                "automation_feasibility": 0.0-1.0,
                "effort_savings": 0.0-1.0,
                "quality_improvement": 0.0-1.0,
                "implementation_complexity": "high|medium|low",
                "roi_estimate": "ROI推定",
                "technology_requirements": ["技術要件"]
            }}
        ],
        "digital_transformation": [
            {{
                "transformation_area": "変革領域",
                "current_state": "現状",
                "target_state": "目標状態",
                "transformation_path": "変革経路",
                "enableing_technologies": ["実現技術"],
                "change_impact": "変革影響"
            }}
        ]
    }},
    "quality_integration": {{
        "quality_checkpoints": [
            {{
                "checkpoint": "品質チェックポイント",
                "process_stage": "プロセス段階",
                "quality_criteria": ["品質基準"],
                "verification_method": "検証方法",
                "corrective_actions": ["是正措置"],
                "escalation_triggers": ["エスカレーション発動条件"]
            }}
        ],
        "quality_assurance_embedding": [
            {{
                "qa_activity": "品質保証活動",
                "integration_approach": "統合アプローチ",
                "process_impact": "プロセスへの影響",
                "value_addition": "付加価値",
                "resource_requirements": ["リソース要件"]
            }}
        ]
    }},
    "continuous_improvement": {{
        "improvement_mechanisms": [
            {{
                "mechanism": "改善メカニズム",
                "description": "詳細説明",
                "implementation": "実装方法",
                "feedback_loops": ["フィードバックループ"],
                "measurement_approach": "測定アプローチ"
            }}
        ],
        "learning_integration": [
            {{
                "learning_source": "学習源",
                "capture_method": "獲得方法",
                "application_strategy": "適用戦略",
                "knowledge_sharing": "知識共有",
                "institutionalization": "制度化"
            }}
        ],
        "innovation_adoption": [
            {{
                "innovation": "革新",
                "adoption_criteria": "採用基準",
                "pilot_approach": "パイロットアプローチ",
                "scaling_strategy": "スケーリング戦略",
                "risk_management": "リスク管理"
            }}
        ]
    }},
    "implementation_strategy": {{
        "optimization_roadmap": [
            {{
                "phase": "最適化段階",
                "duration": "期間",
                "focus_processes": ["重点プロセス"],
                "key_activities": ["主要活動"],
                "success_criteria": ["成功基準"],
                "resource_requirements": ["リソース要件"],
                "risk_mitigation": ["リスク軽減策"]
            }}
        ],
        "change_management": {{
            "stakeholder_engagement": "ステークホルダーエンゲージメント",
            "communication_strategy": "コミュニケーション戦略",
            "training_program": "研修プログラム",
            "resistance_management": "抵抗管理",
            "adoption_support": "採用支援"
        }},
        "pilot_implementation": [
            {{
                "pilot_scope": "パイロット範囲",
                "success_metrics": ["成功指標"],
                "learning_objectives": ["学習目標"],
                "scaling_criteria": ["スケーリング基準"]
            }}
        ]
    }},
    "performance_measurement": {{
        "process_kpis": [
            {{
                "kpi": "プロセスKPI",
                "measurement_method": "測定方法",
                "target_value": "目標値",
                "monitoring_frequency": "監視頻度",
                "reporting_mechanism": "報告メカニズム"
            }}
        ],
        "improvement_tracking": "改善追跡",
        "benchmark_comparison": "ベンチマーク比較",
        "continuous_monitoring": "継続監視"
    }},
    "optimization_evaluation": {{
        "process_efficiency_gain": 0.0-1.0,
        "quality_improvement": 0.0-1.0,
        "resource_optimization": 0.0-1.0,
        "cycle_time_reduction": 0.0-1.0,
        "error_rate_reduction": 0.0-1.0,
        "stakeholder_satisfaction": 0.0-1.0,
        "overall_process_optimization_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "プロセス最適化のための戦略的推奨事項"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=2000)
            result_data = json.loads(response)
            
            result = {
                "task_type": "process_optimization",
                "section_id": section_id,
                "current_processes": current_processes,
                "optimization_focus": optimization_focus,
                "optimization_result": result_data,
                "processes_assessed_count": len(result_data.get("process_analysis", {}).get("current_process_assessment", [])),
                "bottlenecks_identified_count": len(result_data.get("bottleneck_identification", {}).get("process_bottlenecks", [])),
                "automation_candidates_count": len(result_data.get("automation_opportunities", {}).get("automation_candidates", [])),
                "overall_process_optimization_score": result_data.get("optimization_evaluation", {}).get("overall_process_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"プロセス最適化エラー: {e}")

    async def _perform_integrated_optimization(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """包括的・統合的最適化"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            optimization_scope = params.get("optimization_scope", "comprehensive")
            priority_areas = params.get("priority_areas", ["efficiency", "quality", "cost"])
            
            cache_key = self._generate_cache_key(section_id, "integrated_optimization", optimization_scope, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            # 複数最適化の並列実行
            parallel_tasks = []
            
            if "efficiency" in priority_areas:
                parallel_tasks.append(self._perform_efficiency_optimization(params, metrics))
            
            if "quality" in priority_areas:
                parallel_tasks.append(self._perform_quality_optimization(params, metrics))
            
            if "cost" in priority_areas:
                parallel_tasks.append(self._perform_cost_optimization(params, metrics))
            
            # 並列実行
            individual_optimizations = await asyncio.gather(*parallel_tasks)
            
            # 統合最適化プロンプト
            integration_prompt = f"""
以下の個別最適化結果を統合して、包括的で一貫性のある統合最適化戦略を策定してください。

【基礎研究内容】
{content}

【最適化範囲】
{optimization_scope}

【優先領域】
{', '.join(priority_areas)}

【個別最適化結果】
{json.dumps([o for o in individual_optimizations if o], ensure_ascii=False, indent=2)}

【統合最適化指示】
上記の個別最適化を統合し、以下の観点から包括的な統合最適化戦略を策定してください：

1. **最適化統合**: 個別最適化の最適統合
2. **相互作用**: 最適化間の相互作用・依存関係
3. **トレードオフ**: 最適化間のトレードオフ管理
4. **バランス**: 多目的最適化のバランス
5. **シナジー**: 最適化間のシナジー効果
6. **優先順位**: 統合最適化の優先順位付け
7. **実装戦略**: 統合実装戦略の策定
8. **成果測定**: 統合成果測定システム

{{
    "integrated_optimization_framework": {{
        "optimization_vision": {{
            "vision_statement": "最適化ビジョン",
            "optimization_objectives": ["最適化目標"],
            "success_definition": "成功の定義",
            "optimization_principles": ["最適化原則"]
        }},
        "optimization_dimensions": [
            {{
                "dimension": "最適化次元",
                "current_state": "現状",
                "target_state": "目標状態",
                "improvement_potential": 0.0-1.0,
                "contributing_optimizations": ["貢献する個別最適化"],
                "key_strategies": ["主要戦略"]
            }}
        ],
        "optimization_priorities": [
            {{
                "priority": "最適化優先事項",
                "rationale": "優先理由",
                "impact_assessment": "影響評価",
                "resource_requirements": ["リソース要件"],
                "timeline": "実装期間",
                "dependencies": ["依存関係"]
            }}
        ]
    }},
    "synergy_analysis": {{
        "cross_optimization_synergies": [
            {{
                "synergy": "相乗効果",
                "involved_optimizations": ["関与する最適化"],
                "synergy_mechanism": "相乗効果メカニズム",
                "value_creation": "価値創造",
                "implementation_approach": "実装アプローチ",
                "expected_benefit": 0.0-1.0
            }}
        ],
        "reinforcement_opportunities": ["強化機会"],
        "amplification_effects": ["増幅効果"]
    }},
    "trade_off_management": {{
        "identified_trade_offs": [
            {{
                "trade_off": "トレードオフ",
                "conflicting_objectives": ["競合する目標"],
                "trade_off_analysis": "トレードオフ分析",
                "optimization_approach": "最適化アプローチ",
                "recommended_balance": "推奨バランス",
                "sensitivity_analysis": "感度分析"
            }}
        ],
        "multi_objective_optimization": {{
            "objective_weighting": "目標重み付け",
            "pareto_analysis": "パレート分析",
            "optimal_solutions": ["最適解"],
            "decision_criteria": ["決定基準"]
        }}
    }},
    "integration_strategies": {{
        "holistic_approaches": [
            {{
                "approach": "包括的アプローチ",
                "integration_method": "統合手法",
                "scope": "適用範囲",
                "implementation_strategy": "実装戦略",
                "expected_outcomes": ["期待される成果"]
            }}
        ],
        "coordination_mechanisms": [
            {{
                "mechanism": "調整メカニズム",
                "purpose": "目的",
                "operation": "運用方法",
                "effectiveness": 0.0-1.0,
                "maintenance_requirements": ["維持要件"]
            }}
        ],
        "integration_enablers": ["統合促進要因"]
    }},
    "implementation_roadmap": {{
        "integrated_phases": [
            {{
                "phase": "統合段階",
                "duration": "期間",
                "optimization_focus": ["最適化重点"],
                "parallel_activities": ["並列活動"],
                "sequential_dependencies": ["順次依存関係"],
                "key_deliverables": ["主要成果物"],
                "success_milestones": ["成功マイルストーン"],
                "resource_allocation": ["リソース配分"]
            }}
        ],
        "critical_success_factors": [
            {{
                "factor": "重要成功要因",
                "description": "要因説明",
                "management_approach": "管理アプローチ",
                "monitoring_method": "監視方法"
            }}
        ],
        "risk_integration": {{
            "integrated_risks": ["統合リスク"],
            "risk_interactions": ["リスク相互作用"],
            "mitigation_strategies": ["軽減戦略"],
            "contingency_planning": "緊急時計画"
        }}
    }},
    "performance_measurement_system": {{
        "integrated_metrics": [
            {{
                "metric": "統合指標",
                "measurement_approach": "測定アプローチ",
                "data_integration": "データ統合",
                "target_values": "目標値",
                "benchmarking": "ベンチマーキング",
                "reporting_frequency": "報告頻度"
            }}
        ],
        "dashboard_design": {{
            "visualization_approach": "可視化アプローチ",
            "key_indicators": ["主要指標"],
            "drill_down_capabilities": ["詳細分析機能"],
            "real_time_monitoring": "リアルタイム監視"
        }},
        "feedback_systems": [
            {{
                "feedback_source": "フィードバック源",
                "collection_method": "収集方法",
                "analysis_approach": "分析アプローチ",
                "action_triggers": ["アクション発動条件"],
                "improvement_integration": "改善統合"
            }}
        ]
    }},
    "continuous_optimization": {{
        "adaptive_mechanisms": [
            {{
                "mechanism": "適応メカニズム",
                "trigger_conditions": ["発動条件"],
                "adaptation_process": "適応プロセス",
                "learning_integration": "学習統合",
                "optimization_updates": "最適化更新"
            }}
        ],
        "innovation_integration": {{
            "innovation_monitoring": "革新監視",
            "evaluation_criteria": "評価基準",
            "adoption_process": "採用プロセス",
            "scaling_strategy": "スケーリング戦略"
        }},
        "knowledge_management": {{
            "knowledge_capture": "知識獲得",
            "knowledge_sharing": "知識共有",
            "best_practice_evolution": "ベストプラクティス進化",
            "organizational_learning": "組織学習"
        }}
    }},
    "optimization_evaluation": {{
        "integration_effectiveness": 0.0-1.0,
        "synergy_realization": 0.0-1.0,
        "trade_off_optimization": 0.0-1.0,
        "implementation_feasibility": 0.0-1.0,
        "sustainability": 0.0-1.0,
        "adaptability": 0.0-1.0,
        "overall_integrated_optimization_score": 0.0-1.0
    }},
    "strategic_recommendations": [
        "統合最適化のための戦略的推奨事項"
    ],
    "next_steps": [
        "統合最適化実装の次のステップ"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(integration_prompt, max_tokens=2000)
            integration_data = json.loads(response)
            
            result = {
                "task_type": "integrated_optimization",
                "section_id": section_id,
                "optimization_scope": optimization_scope,
                "priority_areas": priority_areas,
                "individual_optimizations": individual_optimizations,
                "integrated_optimization": integration_data,
                "optimization_dimensions_count": len(integration_data.get("integrated_optimization_framework", {}).get("optimization_dimensions", [])),
                "synergies_count": len(integration_data.get("synergy_analysis", {}).get("cross_optimization_synergies", [])),
                "implementation_phases_count": len(integration_data.get("implementation_roadmap", {}).get("integrated_phases", [])),
                "overall_integrated_optimization_score": integration_data.get("optimization_evaluation", {}).get("overall_integrated_optimization_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"統合最適化エラー: {e}")

    def _generate_cache_key(self, section_id: str, task_type: str, focus: str, content: str) -> str:
        """キャッシュキー生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"optimization:{task_type}:{section_id}:{focus}:{content_hash}"

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
            except Exception in e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    logger.warning(f"OpenAI API呼び出し失敗 (試行 {attempt + 1}/{max_retries}): {e}")
                else:
                    raise AgentExecutionError(f"OpenAI API呼び出しが{max_retries}回失敗しました: {e}")

    def get_supported_tasks(self) -> Dict[str, str]:
        """サポートされているタスクタイプの取得"""
        return self.supported_tasks.copy()

    def get_optimization_domains(self) -> Dict[str, str]:
        """最適化領域の取得"""
        return self.optimization_domains.copy()

    def get_optimization_metrics(self) -> List[str]:
        """最適化指標の取得"""
        return self.optimization_metrics.copy()


# エージェントインスタンスは必要な時に作成される