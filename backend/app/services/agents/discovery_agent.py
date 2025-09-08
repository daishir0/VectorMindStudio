"""
DiscoveryAgent - 研究論文の発見・探索・ギャップ分析エージェント

研究論文における知識ギャップの発見、関連研究の探索、研究空白領域の特定を行う。
既存研究の網羅性チェック、引用漏れの検出、新規研究テーマの発見をサポート。
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
class DiscoveryResult:
    """発見・探索結果"""
    gaps_identified: List[str]
    missing_areas: List[str]
    research_opportunities: List[str]
    citation_gaps: List[str]
    redundancies: List[str]
    balance_score: float
    discovery_confidence: float
    recommendations: List[str]


class DiscoveryAgent(EnhancedBaseAgent):
    """
    研究発見・探索・ギャップ分析エージェント
    
    主要機能：
    1. ギャップ分析: 研究領域の知識ギャップ特定
    2. 冗長性検出: 重複・冗長な内容の発見
    3. バランス分析: 研究内容の均衡性評価
    4. 引用分析: 引用の妥当性・網羅性チェック
    5. 新規テーマ発見: 新規研究方向の特定
    6. 関連研究探索: 見落とされた関連研究の発見
    7. 競合分析: 競合研究との差別化ポイント分析
    8. 統合探索: 複数セクションの統合的探索分析
    """
    
    def __init__(self, session=None):
        super().__init__(session=session, timeout=30)
        self.agent_version = "1.0.0"
        self.cache_ttl_seconds = 1800  # 30分キャッシュ
        
        # タスクタイプ定義
        self.task_definitions = {
            "gap_analysis": "知識・研究ギャップの特定",
            "redundancy_detection": "冗長性・重複内容の検出", 
            "balance_analysis": "研究内容のバランス分析",
            "citation_analysis": "引用の妥当性・網羅性分析",
            "novel_theme_discovery": "新規研究テーマの発見",
            "related_research_exploration": "関連研究の探索・発見",
            "competitive_analysis": "競合研究との差別化分析",
            "integrated_discovery": "統合的探索・発見分析"
        }
        
        # 分析対象領域定義
        self.analysis_domains = [
            "methodology",
            "theoretical_framework", 
            "empirical_evidence",
            "comparative_studies",
            "interdisciplinary_connections",
            "practical_applications",
            "future_directions",
            "limitations_discussion"
        ]

    @property
    def supported_tasks(self) -> List[str]:
        """サポートされるタスクタイプのリスト"""
        return list(self.task_definitions.keys())

    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters or {}
        
        if task_type == "gap_analysis":
            return await self._perform_gap_analysis(parameters, metrics)
        elif task_type == "redundancy_detection":
            return await self._perform_redundancy_detection(parameters, metrics)
        elif task_type == "balance_analysis":
            return await self._perform_balance_analysis(parameters, metrics)
        elif task_type == "citation_analysis":
            return await self._perform_citation_analysis(parameters, metrics)
        elif task_type == "novel_theme_discovery":
            return await self._perform_novel_theme_discovery(parameters, metrics)
        elif task_type == "related_research_exploration":
            return await self._perform_related_research_exploration(parameters, metrics)
        elif task_type == "competitive_analysis":
            return await self._perform_competitive_analysis(parameters, metrics)
        elif task_type == "integrated_discovery":
            return await self._perform_integrated_discovery(parameters, metrics)
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
        発見・探索タスクの実行
        
        Args:
            task_type: 実行するタスクの種類
            section_id: 対象セクションID
            content: 分析対象のコンテンツ
            parameters: 追加パラメータ
            
        Returns:
            AgentResult: 実行結果
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
            result = await self._execute_discovery_task(task_type, params, metrics)
            
            return AgentResult(
                agent_name=self.agent_name,
                task_type=task_type,
                status="success",
                result=result,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"DiscoveryAgentタスク実行エラー - {task_type}: {e}")
            return AgentResult(
                agent_name=self.agent_name,
                task_type=task_type,
                status="error",
                error=str(e),
                metrics=metrics,
                timestamp=datetime.utcnow()
            )

    async def _execute_discovery_task(
        self, 
        task_type: str, 
        params: Dict[str, Any], 
        metrics: ExecutionMetrics
    ) -> Dict[str, Any]:
        """発見・探索タスクの実行"""
        
        task_methods = {
            "gap_analysis": self._perform_gap_analysis,
            "redundancy_detection": self._perform_redundancy_detection,
            "balance_analysis": self._perform_balance_analysis,
            "citation_analysis": self._perform_citation_analysis,
            "novel_theme_discovery": self._perform_novel_theme_discovery,
            "related_research_exploration": self._perform_related_research_exploration,
            "competitive_analysis": self._perform_competitive_analysis,
            "integrated_discovery": self._perform_integrated_discovery
        }
        
        method = task_methods.get(task_type)
        if not method:
            raise AgentExecutionError(f"未実装のタスクタイプ: {task_type}")
            
        return await method(params, metrics)

    async def _perform_gap_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """知識・研究ギャップの特定"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            research_area = params.get("research_area", "general")
            
            # キャッシュキー生成
            cache_key = self._generate_cache_key(section_id, "gap_analysis", research_area, content)
            
            # キャッシュチェック
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            # ギャップ分析プロンプト
            prompt = f"""
研究論文の以下の内容について、知識ギャップと研究ギャップを特定してください。

【分析対象内容】
{content}

【分析領域】
{research_area}

【分析指示】
以下の観点から包括的なギャップ分析を行い、JSON形式で回答してください：

1. **理論的ギャップ**: 理論的フレームワークの不足・欠陥
2. **方法論的ギャップ**: 研究手法・アプローチの空白
3. **実証的ギャップ**: 実証データ・証拠の不足
4. **応用的ギャップ**: 実用化・応用面での空白
5. **学際的ギャップ**: 分野横断的視点の欠如
6. **時系列的ギャップ**: 時間軸での研究の空白
7. **地理的ギャップ**: 地域・文化的視点の不足
8. **比較的ギャップ**: 比較研究・対照研究の欠如

{{
    "identified_gaps": [
        {{
            "gap_type": "理論的|方法論的|実証的|応用的|学際的|時系列的|地理的|比較的",
            "description": "ギャップの詳細説明",
            "severity": "high|medium|low",
            "potential_impact": "このギャップを埋めることの影響度",
            "research_opportunity": "研究機会の具体的提案"
        }}
    ],
    "priority_gaps": [
        {{
            "gap": "最優先で取り組むべきギャップ",
            "rationale": "優先度の理由",
            "approach_suggestion": "取り組み方法の提案"
        }}
    ],
    "gap_analysis_score": 0.0-1.0の数値,
    "completeness_assessment": "現在の研究の網羅性評価",
    "recommendations": ["具体的な改善提案のリスト"]
}}
"""
            
            # OpenAI API呼び出し
            response = await self._call_openai_with_retry(prompt, max_tokens=1500)
            result_data = json.loads(response)
            
            # 結果の構造化
            result = {
                "task_type": "gap_analysis",
                "section_id": section_id,
                "research_area": research_area,
                "analysis_result": result_data,
                "gaps_count": len(result_data.get("identified_gaps", [])),
                "priority_gaps_count": len(result_data.get("priority_gaps", [])),
                "gap_score": result_data.get("gap_analysis_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # キャッシュ保存
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"ギャップ分析エラー: {e}")

    async def _perform_redundancy_detection(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """冗長性・重複内容の検出"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            comparison_content = params.get("comparison_content", "")
            
            cache_key = self._generate_cache_key(section_id, "redundancy_detection", "standard", content + comparison_content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、冗長性と重複を検出してください。

【主要分析内容】
{content}

【比較対象内容（ある場合）】
{comparison_content}

【分析指示】
以下の観点から冗長性検出を行い、JSON形式で回答してください：

1. **内容重複**: 同じ内容の繰り返し
2. **概念重複**: 似た概念の重複説明
3. **論点重複**: 同じ論点の多重議論
4. **引用重複**: 同じ情報源の重複引用
5. **説明重複**: 同じ説明の再提示
6. **結論重複**: 結論・主張の重複
7. **例示重複**: 同じ事例の重複使用
8. **構造重複**: 論文構造の重複パターン

{{
    "detected_redundancies": [
        {{
            "redundancy_type": "内容|概念|論点|引用|説明|結論|例示|構造",
            "description": "重複内容の詳細",
            "locations": ["重複箇所の特定"],
            "severity": "high|medium|low",
            "suggestion": "改善提案"
        }}
    ],
    "redundancy_score": 0.0-1.0の数値（高いほど冗長性が高い）,
    "efficiency_rating": "内容効率性の評価",
    "consolidation_opportunities": ["統合可能な内容の提案"],
    "removal_candidates": ["削除候補の内容"],
    "recommendations": ["冗長性削減の具体的提案"]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1200)
            result_data = json.loads(response)
            
            result = {
                "task_type": "redundancy_detection",
                "section_id": section_id,
                "analysis_result": result_data,
                "redundancies_count": len(result_data.get("detected_redundancies", [])),
                "redundancy_score": result_data.get("redundancy_score", 0.0),
                "efficiency_rating": result_data.get("efficiency_rating", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"冗長性検出エラー: {e}")

    async def _perform_balance_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """研究内容のバランス分析"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            target_domains = params.get("target_domains", self.analysis_domains)
            
            cache_key = self._generate_cache_key(section_id, "balance_analysis", "domains", content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            domains_str = ", ".join(target_domains)
            
            prompt = f"""
研究論文の以下の内容について、研究領域のバランス分析を行ってください。

【分析対象内容】
{content}

【分析対象領域】
{domains_str}

【分析指示】
以下の観点から包括的なバランス分析を行い、JSON形式で回答してください：

1. **領域カバレッジ**: 各研究領域の網羅度
2. **内容バランス**: 各領域の内容量バランス
3. **深度バランス**: 各領域の分析深度バランス
4. **重要度バランス**: 重要領域への適切な注力度
5. **時間軸バランス**: 過去・現在・未来の視点バランス
6. **理論・実証バランス**: 理論と実証のバランス
7. **批判・支持バランス**: 批判的視点と支持的視点のバランス
8. **ローカル・グローバルバランス**: 地域と世界的視点のバランス

{{
    "domain_coverage": {{
        "covered_domains": ["カバー済み領域"],
        "uncovered_domains": ["未カバー領域"],
        "partially_covered": ["部分的カバー領域"]
    }},
    "balance_scores": {{
        "content_balance": 0.0-1.0,
        "depth_balance": 0.0-1.0,
        "importance_balance": 0.0-1.0,
        "temporal_balance": 0.0-1.0,
        "theoretical_empirical_balance": 0.0-1.0,
        "critical_supportive_balance": 0.0-1.0,
        "local_global_balance": 0.0-1.0
    }},
    "overall_balance_score": 0.0-1.0,
    "imbalance_issues": [
        {{
            "issue_type": "バランス問題の種類",
            "description": "問題の詳細説明",
            "severity": "high|medium|low",
            "improvement_suggestion": "改善提案"
        }}
    ],
    "balance_recommendations": ["バランス改善の具体的提案"],
    "priority_adjustments": ["優先的に調整すべき項目"]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1400)
            result_data = json.loads(response)
            
            result = {
                "task_type": "balance_analysis",
                "section_id": section_id,
                "target_domains": target_domains,
                "analysis_result": result_data,
                "overall_balance_score": result_data.get("overall_balance_score", 0.0),
                "imbalance_count": len(result_data.get("imbalance_issues", [])),
                "covered_domains": result_data.get("domain_coverage", {}).get("covered_domains", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"バランス分析エラー: {e}")

    async def _perform_citation_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """引用の妥当性・網羅性分析"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            research_field = params.get("research_field", "general")
            
            cache_key = self._generate_cache_key(section_id, "citation_analysis", research_field, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、引用の妥当性と網羅性を分析してください。

【分析対象内容】
{content}

【研究分野】
{research_field}

【分析指示】
以下の観点から引用分析を行い、JSON形式で回答してください：

1. **引用適切性**: 引用の妥当性・正確性
2. **引用網羅性**: 重要文献の包含度
3. **引用新しさ**: 最新研究の引用状況
4. **引用バランス**: 支持・批判的引用のバランス
5. **引用多様性**: 多様な研究者・機関の引用
6. **引用関連性**: 内容と引用の関連度
7. **引用信頼性**: 引用元の信頼性・権威性
8. **引用不足領域**: 見落とされた重要な引用領域

{{
    "citation_assessment": {{
        "total_citations_estimated": 推定引用数,
        "citation_quality": "high|medium|low",
        "citation_coverage": "comprehensive|adequate|insufficient",
        "citation_balance": "balanced|biased_supportive|biased_critical"
    }},
    "citation_issues": [
        {{
            "issue_type": "適切性|網羅性|新しさ|バランス|多様性|関連性|信頼性|不足",
            "description": "問題の詳細説明",
            "severity": "high|medium|low",
            "suggestion": "改善提案"
        }}
    ],
    "missing_citation_areas": [
        {{
            "area": "不足している引用領域",
            "importance": "high|medium|low",
            "suggested_sources": ["推奨する引用元"],
            "rationale": "引用が必要な理由"
        }}
    ],
    "citation_scores": {{
        "appropriateness": 0.0-1.0,
        "comprehensiveness": 0.0-1.0,
        "recency": 0.0-1.0,
        "balance": 0.0-1.0,
        "diversity": 0.0-1.0,
        "relevance": 0.0-1.0,
        "reliability": 0.0-1.0
    }},
    "overall_citation_score": 0.0-1.0,
    "recommendations": ["引用改善の具体的提案"]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1400)
            result_data = json.loads(response)
            
            result = {
                "task_type": "citation_analysis", 
                "section_id": section_id,
                "research_field": research_field,
                "analysis_result": result_data,
                "citation_issues_count": len(result_data.get("citation_issues", [])),
                "missing_areas_count": len(result_data.get("missing_citation_areas", [])),
                "overall_citation_score": result_data.get("overall_citation_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"引用分析エラー: {e}")

    async def _perform_novel_theme_discovery(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """新規研究テーマの発見"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            innovation_focus = params.get("innovation_focus", "general")
            
            cache_key = self._generate_cache_key(section_id, "novel_theme_discovery", innovation_focus, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容から、新規研究テーマと研究機会を発見してください。

【分析対象内容】
{content}

【イノベーション焦点】
{innovation_focus}

【分析指示】
以下の観点から新規テーマ発見を行い、JSON形式で回答してください：

1. **未開拓領域**: まだ研究されていない領域
2. **学際融合**: 異分野融合による新テーマ
3. **方法論革新**: 新しい研究手法の可能性
4. **応用拡張**: 既存研究の新たな応用領域
5. **理論発展**: 理論的フレームワークの発展可能性
6. **技術革新**: 新技術による研究機会
7. **社会的需要**: 社会的ニーズに基づく研究テーマ
8. **未来予測**: 将来的に重要になる研究領域

{{
    "novel_themes": [
        {{
            "theme_title": "新規テーマのタイトル",
            "description": "テーマの詳細説明",
            "novelty_type": "未開拓|学際融合|方法論革新|応用拡張|理論発展|技術革新|社会的需要|未来予測",
            "research_potential": "high|medium|low",
            "feasibility": "high|medium|low",
            "impact_potential": "revolutionary|significant|moderate",
            "required_resources": "必要なリソース・専門性",
            "timeline_estimate": "研究期間の推定",
            "key_challenges": ["主要な課題・困難"],
            "success_indicators": ["成功指標"]
        }}
    ],
    "interdisciplinary_opportunities": [
        {{
            "combination": "融合する分野の組み合わせ",
            "potential_outcome": "期待される成果",
            "novelty_score": 0.0-1.0
        }}
    ],
    "methodological_innovations": [
        {{
            "innovation_type": "方法論革新の種類",
            "description": "革新の詳細",
            "applicability": "適用可能性"
        }}
    ],
    "discovery_confidence": 0.0-1.0の数値,
    "priority_themes": ["最優先で取り組むべきテーマ"],
    "recommendations": ["新規研究テーマ追求のための具体的提案"]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1600)
            result_data = json.loads(response)
            
            result = {
                "task_type": "novel_theme_discovery",
                "section_id": section_id,
                "innovation_focus": innovation_focus,
                "analysis_result": result_data,
                "novel_themes_count": len(result_data.get("novel_themes", [])),
                "interdisciplinary_count": len(result_data.get("interdisciplinary_opportunities", [])),
                "discovery_confidence": result_data.get("discovery_confidence", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"新規テーマ発見エラー: {e}")

    async def _perform_related_research_exploration(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """関連研究の探索・発見"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            exploration_scope = params.get("exploration_scope", "broad")
            
            cache_key = self._generate_cache_key(section_id, "related_research_exploration", exploration_scope, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、関連研究の探索と発見を行ってください。

【分析対象内容】
{content}

【探索範囲】
{exploration_scope}

【分析指示】
以下の観点から関連研究探索を行い、JSON形式で回答してください：

1. **直接関連研究**: 直接的に関連する研究領域
2. **間接関連研究**: 間接的に関連する研究分野
3. **競合研究**: 競合・類似研究の特定
4. **補完研究**: 補完的な研究アプローチ
5. **基盤研究**: 基礎となる理論・研究
6. **応用研究**: 応用・実装に関する研究
7. **批判研究**: 批判的視点を提供する研究
8. **未来研究**: 将来の発展方向を示唆する研究

{{
    "related_research_areas": [
        {{
            "area_title": "関連研究領域のタイトル",
            "relationship_type": "直接|間接|競合|補完|基盤|応用|批判|未来",
            "description": "関連性の詳細説明",
            "relevance_score": 0.0-1.0,
            "research_gap": "この領域での研究ギャップ",
            "key_researchers": ["主要研究者（推定）"],
            "important_works": ["重要な研究（推定）"],
            "research_methods": ["主要な研究手法"],
            "potential_collaboration": "コラボレーション可能性"
        }}
    ],
    "missed_connections": [
        {{
            "connection": "見落とされた関連性",
            "description": "関連性の説明",
            "importance": "high|medium|low",
            "exploration_benefit": "探索することの利益"
        }}
    ],
    "research_clusters": [
        {{
            "cluster_name": "研究クラスター名",
            "member_areas": ["クラスターの構成領域"],
            "central_theme": "中心テーマ",
            "research_density": "high|medium|low"
        }}
    ],
    "exploration_completeness": 0.0-1.0の数値,
    "discovery_potential": "high|medium|low",
    "recommendations": ["関連研究探索の具体的提案"],
    "priority_exploration_areas": ["優先的に探索すべき領域"]
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1500)
            result_data = json.loads(response)
            
            result = {
                "task_type": "related_research_exploration",
                "section_id": section_id,
                "exploration_scope": exploration_scope,
                "analysis_result": result_data,
                "related_areas_count": len(result_data.get("related_research_areas", [])),
                "missed_connections_count": len(result_data.get("missed_connections", [])),
                "exploration_completeness": result_data.get("exploration_completeness", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"関連研究探索エラー: {e}")

    async def _perform_competitive_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """競合研究との差別化分析"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            competitive_focus = params.get("competitive_focus", "differentiation")
            
            cache_key = self._generate_cache_key(section_id, "competitive_analysis", competitive_focus, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            prompt = f"""
研究論文の以下の内容について、競合研究との差別化分析を行ってください。

【分析対象内容】
{content}

【競合分析焦点】
{competitive_focus}

【分析指示】
以下の観点から競合分析を行い、JSON形式で回答してください：

1. **競合特定**: 直接・間接競合の特定
2. **差別化ポイント**: 独自性・差別化要素
3. **競争優位**: 競争上の優位性
4. **弱点分析**: 競合に対する弱点
5. **機会分析**: 競合空白による機会
6. **脅威分析**: 競合からの脅威
7. **ポジショニング**: 研究分野でのポジション
8. **戦略提案**: 競合対応戦略

{{
    "competitive_landscape": {{
        "direct_competitors": [
            {{
                "competitor_type": "競合の種類・特徴",
                "research_approach": "競合の研究アプローチ",
                "strengths": ["競合の強み"],
                "weaknesses": ["競合の弱み"],
                "threat_level": "high|medium|low"
            }}
        ],
        "indirect_competitors": [
            {{
                "competitor_type": "間接競合の種類",
                "overlap_areas": ["重複領域"],
                "potential_threat": "潜在的脅威"
            }}
        ]
    }},
    "differentiation_analysis": {{
        "unique_strengths": [
            {{
                "strength": "独自の強み",
                "description": "強みの詳細説明",
                "competitive_advantage": "競争優位性",
                "sustainability": "持続可能性"
            }}
        ],
        "differentiation_score": 0.0-1.0,
        "positioning": "research_positioning_description"
    }},
    "competitive_gaps": [
        {{
            "gap_area": "競合が未対応の領域",
            "opportunity_size": "high|medium|low",
            "entry_barrier": "参入障壁の程度",
            "strategic_value": "戦略的価値"
        }}
    ],
    "vulnerability_analysis": [
        {{
            "vulnerability": "競合に対する脆弱性",
            "impact": "high|medium|low", 
            "mitigation_strategy": "軽減戦略"
        }}
    ],
    "competitive_strategy_recommendations": [
        "競合対応戦略の具体的提案"
    ],
    "market_positioning": "研究分野での推奨ポジション"
}}
"""
            
            response = await self._call_openai_with_retry(prompt, max_tokens=1500)
            result_data = json.loads(response)
            
            result = {
                "task_type": "competitive_analysis",
                "section_id": section_id,
                "competitive_focus": competitive_focus,
                "analysis_result": result_data,
                "direct_competitors_count": len(result_data.get("competitive_landscape", {}).get("direct_competitors", [])),
                "competitive_gaps_count": len(result_data.get("competitive_gaps", [])),
                "differentiation_score": result_data.get("differentiation_analysis", {}).get("differentiation_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"競合分析エラー: {e}")

    async def _perform_integrated_discovery(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """統合的探索・発見分析"""
        try:
            content = params["content"]
            section_id = params["section_id"]
            integration_scope = params.get("integration_scope", "comprehensive")
            
            cache_key = self._generate_cache_key(section_id, "integrated_discovery", integration_scope, content)
            
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                metrics.cache_hits += 1
                return cached_result
            
            # 複数タスクの並列実行
            parallel_tasks = [
                self._perform_gap_analysis(params, metrics),
                self._perform_balance_analysis(params, metrics), 
                self._perform_novel_theme_discovery(params, metrics)
            ]
            
            gap_result, balance_result, novel_result = await asyncio.gather(*parallel_tasks)
            
            # 統合分析プロンプト
            integration_prompt = f"""
以下の個別分析結果を統合して、包括的な発見・探索分析を行ってください。

【ギャップ分析結果】
{json.dumps(gap_result.get('analysis_result', {}), ensure_ascii=False, indent=2)}

【バランス分析結果】
{json.dumps(balance_result.get('analysis_result', {}), ensure_ascii=False, indent=2)}

【新規テーマ発見結果】
{json.dumps(novel_result.get('analysis_result', {}), ensure_ascii=False, indent=2)}

【統合分析指示】
上記の個別分析結果を統合し、総合的な発見・探索結果をJSON形式で提供してください：

{{
    "integrated_insights": [
        {{
            "insight": "統合から得られた洞察",
            "supporting_analyses": ["洞察を支える分析結果"],
            "significance": "high|medium|low",
            "actionability": "行動可能性の評価"
        }}
    ],
    "cross_analysis_patterns": [
        {{
            "pattern": "複数分析で共通するパターン",
            "frequency": "出現頻度",
            "implications": "含意・影響"
        }}
    ],
    "priority_discovery_areas": [
        {{
            "area": "優先発見領域",
            "rationale": "優先する理由", 
            "expected_impact": "期待される影響",
            "approach_strategy": "取り組み戦略"
        }}
    ],
    "synthesis_score": 0.0-1.0の数値,
    "discovery_completeness": "発見の網羅性評価",
    "strategic_recommendations": [
        "戦略的推奨事項のリスト"
    ],
    "next_steps": [
        "次に取るべきステップ"
    ]
}}
"""
            
            response = await self._call_openai_with_retry(integration_prompt, max_tokens=1400)
            integration_data = json.loads(response)
            
            result = {
                "task_type": "integrated_discovery",
                "section_id": section_id,
                "integration_scope": integration_scope,
                "individual_results": {
                    "gap_analysis": gap_result,
                    "balance_analysis": balance_result,
                    "novel_theme_discovery": novel_result
                },
                "integrated_analysis": integration_data,
                "integrated_insights_count": len(integration_data.get("integrated_insights", [])),
                "priority_areas_count": len(integration_data.get("priority_discovery_areas", [])),
                "synthesis_score": integration_data.get("synthesis_score", 0.0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._cache_result(cache_key, result)
            metrics.api_calls += 1
            
            return result
            
        except Exception as e:
            raise AgentExecutionError(f"統合探索分析エラー: {e}")

    def _generate_cache_key(self, section_id: str, task_type: str, focus: str, content: str) -> str:
        """キャッシュキー生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"discovery:{task_type}:{section_id}:{focus}:{content_hash}"

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

    def get_analysis_domains(self) -> List[str]:
        """分析対象領域の取得"""
        return self.analysis_domains.copy()

