"""
Analysis Agent - 総合分析エージェント
統合機能: 批判的分析、構造分析、整合性チェック、妥当性検証、比較分析
"""
from typing import Dict, List, Any, Optional
import logging
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from functools import lru_cache

from .enhanced_base_agent import EnhancedBaseAgent, ExecutionMetrics, AgentTask
from .base_agent import AgentExecutionError, AgentValidationError
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.external.openai_client import openai_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# シンプルなメモリキャッシュ（実運用ではRedis等を使用）
_analysis_cache = {}

class AnalysisAgent(EnhancedBaseAgent):
    """
    総合分析エージェント
    
    統合された責務:
    - 批判的分析: セクションの弱点・問題点の特定
    - 構造分析: 論理構造の可視化・図解
    - 整合性チェック: セクション間整合性チェック
    - 妥当性検証: 統計的・方法論的妥当性検証
    - 比較分析: 先行研究との比較分析
    """
    
    def __init__(self, session=None):
        super().__init__(session=session, timeout=settings.AI_AGENT_TIMEOUT_SECONDS)
        self.repository = PaperRepository(session) if session else None
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "critical_analysis",        # 批判的分析
            "structure_analysis",       # 構造分析
            "consistency_check",        # 整合性チェック
            "validity_verification",    # 妥当性検証
            "comparative_analysis",     # 比較分析
            "weakness_identification",  # 弱点特定
            "logic_structure_mapping",  # 論理構造マッピング
            "cross_section_validation"  # 横断的検証
        ]
    
    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コア実行ロジック"""
        if not self.repository:
            raise AgentExecutionError("データベースセッションが必要です")
        
        task_type = task.task_type
        
        if task_type == "critical_analysis":
            return await self._perform_critical_analysis(task.parameters, metrics)
        elif task_type == "structure_analysis":
            return await self._perform_structure_analysis(task.parameters, metrics)
        elif task_type == "consistency_check":
            return await self._perform_consistency_check(task.parameters, metrics)
        elif task_type == "validity_verification":
            return await self._perform_validity_verification(task.parameters, metrics)
        elif task_type == "comparative_analysis":
            return await self._perform_comparative_analysis(task.parameters, metrics)
        elif task_type == "weakness_identification":
            return await self._identify_weaknesses(task.parameters, metrics)
        elif task_type == "logic_structure_mapping":
            return await self._map_logic_structure(task.parameters, metrics)
        elif task_type == "cross_section_validation":
            return await self._validate_cross_sections(task.parameters, metrics)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _perform_critical_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """批判的分析の実行"""
        paper_id = params.get("paper_id")
        target_sections = params.get("target_sections", [])  # 特定セクションまたは全体
        analysis_focus = params.get("focus", "comprehensive")  # "methodology", "logic", "evidence", etc.
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        
        try:
            # セクション取得
            if target_sections:
                sections = []
                for section_id in target_sections:
                    section = await self.repository.get_section_by_id(section_id)
                    if section:
                        sections.append(section)
            else:
                sections = await self.repository.get_sections_by_paper(paper_id)
            
            metrics.items_processed = len(sections)
            
            if not sections:
                return {
                    "analysis_results": [],
                    "critical_issues": [],
                    "improvement_suggestions": [],
                    "overall_assessment": "分析対象セクションが見つかりません",
                    "success": True
                }
            
            # 各セクションの批判的分析
            analysis_results = []
            critical_issues = []
            improvement_suggestions = []
            
            for section in sections:
                # キャッシュキーの生成
                cache_key = self._generate_cache_key(
                    section.id, "critical_analysis", analysis_focus, section.content
                )
                
                # キャッシュチェック
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    analysis_data = cached_result
                else:
                    # OpenAI APIを使用した詳細分析（リトライ付き）
                    analysis_prompt = self._build_critical_analysis_prompt(
                        section.title, section.content, analysis_focus
                    )
                    
                    response = await self._call_openai_with_retry(analysis_prompt)
                    
                    # レスポンス解析
                    try:
                        analysis_data = json.loads(response)
                        # キャッシュに保存
                        self._save_to_cache(cache_key, analysis_data)
                    except:
                        # JSONパースに失敗した場合のフォールバック
                        analysis_data = {
                            "weaknesses": [response[:200] + "..."],
                            "strengths": ["分析結果の構造化に失敗"],
                            "suggestions": ["詳細な再分析が必要"]
                        }
                
                # レスポンス解析（キャッシュから取得した場合はここから継続）
                
                section_analysis = {
                    "section_id": section.id,
                    "section_title": section.title,
                    "weaknesses": analysis_data.get("weaknesses", []),
                    "strengths": analysis_data.get("strengths", []),
                    "critical_score": analysis_data.get("critical_score", 5),  # 1-10スケール
                    "evidence_quality": analysis_data.get("evidence_quality", "moderate"),
                    "logic_coherence": analysis_data.get("logic_coherence", "adequate")
                }
                
                analysis_results.append(section_analysis)
                critical_issues.extend(analysis_data.get("critical_issues", []))
                improvement_suggestions.extend(analysis_data.get("suggestions", []))
                
                metrics.items_successful += 1
            
            # 全体評価
            avg_critical_score = sum(r["critical_score"] for r in analysis_results) / len(analysis_results)
            overall_assessment = self._generate_overall_assessment(avg_critical_score, critical_issues)
            
            return {
                "analysis_results": analysis_results,
                "critical_issues": critical_issues[:10],  # 上位10件
                "improvement_suggestions": improvement_suggestions[:15],  # 上位15件
                "overall_assessment": overall_assessment,
                "average_critical_score": avg_critical_score,
                "sections_analyzed": len(analysis_results),
                "focus": analysis_focus,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[AnalysisAgent] 批判的分析エラー: {e}")
            raise AgentExecutionError(f"批判的分析でエラーが発生しました: {e}")
    
    async def _perform_structure_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """構造分析の実行"""
        paper_id = params.get("paper_id")
        visualization_type = params.get("visualization_type", "logic_flow")
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        
        try:
            sections = await self.repository.get_sections_by_paper(paper_id)
            metrics.items_processed = len(sections)
            
            if not sections:
                return {
                    "structure_map": {},
                    "flow_diagram": "",
                    "logical_connections": [],
                    "success": True
                }
            
            # 構造分析プロンプト作成
            structure_prompt = self._build_structure_analysis_prompt(sections, visualization_type)
            
            response_data = await openai_client.generate_text(
                prompt=structure_prompt
            )
            response = response_data.get("content", "")
            
            # 構造分析結果の解析
            try:
                structure_data = json.loads(response)
            except:
                structure_data = {
                    "structure_map": {"error": "構造解析に失敗"},
                    "flow_diagram": response[:500],
                    "logical_connections": []
                }
            
            metrics.items_successful = len(sections)
            
            return {
                "structure_map": structure_data.get("structure_map", {}),
                "flow_diagram": structure_data.get("flow_diagram", ""),
                "logical_connections": structure_data.get("logical_connections", []),
                "visualization_type": visualization_type,
                "sections_analyzed": len(sections),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[AnalysisAgent] 構造分析エラー: {e}")
            raise AgentExecutionError(f"構造分析でエラーが発生しました: {e}")
    
    async def _perform_consistency_check(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """整合性チェックの実行"""
        paper_id = params.get("paper_id")
        check_scope = params.get("scope", "all")  # "cross_section", "data_figure", "reference"
        
        try:
            sections = await self.repository.get_sections_by_paper(paper_id)
            metrics.items_processed = len(sections)
            
            consistency_issues = []
            consistency_score = 10.0
            
            # セクション間整合性チェック
            if check_scope in ["all", "cross_section"]:
                cross_issues = await self._check_cross_section_consistency(sections)
                consistency_issues.extend(cross_issues)
                consistency_score -= len(cross_issues) * 0.5
            
            # データと図表の整合性チェック  
            if check_scope in ["all", "data_figure"]:
                data_issues = await self._check_data_figure_consistency(sections)
                consistency_issues.extend(data_issues)
                consistency_score -= len(data_issues) * 0.3
            
            consistency_score = max(0, consistency_score)
            metrics.items_successful = len(sections)
            
            return {
                "consistency_issues": consistency_issues,
                "consistency_score": consistency_score,
                "check_scope": check_scope,
                "sections_checked": len(sections),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[AnalysisAgent] 整合性チェックエラー: {e}")
            raise AgentExecutionError(f"整合性チェックでエラーが発生しました: {e}")
    
    async def _perform_validity_verification(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """妥当性検証の実行 - 簡易実装"""
        return {"verification_result": "妥当性検証実装予定", "success": True}
    
    async def _perform_comparative_analysis(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """比較分析の実行 - 簡易実装"""
        return {"comparison_result": "比較分析実装予定", "success": True}
    
    async def _identify_weaknesses(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """弱点特定 - 批判的分析のサブセット"""
        params["focus"] = "weaknesses"
        return await self._perform_critical_analysis(params, metrics)
    
    async def _map_logic_structure(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """論理構造マッピング - 構造分析のサブセット"""
        params["visualization_type"] = "logic_map"
        return await self._perform_structure_analysis(params, metrics)
    
    async def _validate_cross_sections(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """横断的検証 - 整合性チェックのサブセット"""
        params["scope"] = "cross_section"
        return await self._perform_consistency_check(params, metrics)
    
    def _build_critical_analysis_prompt(self, title: str, content: str, focus: str) -> str:
        """批判的分析用プロンプト生成"""
        return f"""
以下の論文セクションについて詳細な批判的分析を行い、JSON形式で回答してください。

セクション: {title}
内容: {content}

分析観点: {focus}

以下の形式でJSONを返してください:
{{
    "weaknesses": ["弱点1", "弱点2", "弱点3"],
    "strengths": ["長所1", "長所2", "長所3"], 
    "critical_issues": ["重要な問題1", "重要な問題2"],
    "suggestions": ["改善提案1", "改善提案2", "改善提案3"],
    "critical_score": 7,
    "evidence_quality": "good/moderate/poor",
    "logic_coherence": "excellent/good/adequate/poor"
}}
"""
    
    def _build_structure_analysis_prompt(self, sections: List[Any], viz_type: str) -> str:
        """構造分析用プロンプト生成"""
        sections_text = "\n".join([f"- {s.title}: {s.content[:200]}..." for s in sections])
        
        return f"""
以下の論文セクション群について構造分析を行い、{viz_type}形式で可視化してください。

セクション一覧:
{sections_text}

以下の形式でJSONを返してください:
{{
    "structure_map": {{
        "main_flow": ["section1", "section2", "section3"],
        "dependencies": {{"section1": ["section2"], "section2": ["section3"]}},
        "logical_gaps": ["ギャップ1", "ギャップ2"]
    }},
    "flow_diagram": "テキストベースのフロー図",
    "logical_connections": [
        {{"from": "section1", "to": "section2", "relationship": "supports", "strength": "strong"}},
        {{"from": "section2", "to": "section3", "relationship": "leads_to", "strength": "moderate"}}
    ]
}}
"""
    
    async def _check_cross_section_consistency(self, sections: List[Any]) -> List[Dict[str, Any]]:
        """セクション間整合性チェック"""
        issues = []
        
        # 簡易実装: Introduction と Conclusion の整合性
        intro_section = next((s for s in sections if "introduction" in s.title.lower()), None)
        conclusion_section = next((s for s in sections if "conclusion" in s.title.lower()), None)
        
        if intro_section and conclusion_section:
            # OpenAI APIを使用した整合性チェック
            consistency_prompt = f"""
Introduction: {intro_section.content[:500]}
Conclusion: {conclusion_section.content[:500]}

この2つのセクションの整合性をチェックし、不整合な点があれば指摘してください。
JSON形式で返答: {{"issues": ["不整合1", "不整合2"], "score": 8.5}}
"""
            
            try:
                response_data = await openai_client.generate_text(
                    prompt=consistency_prompt
                )
                response = response_data.get("content", "")
                result = json.loads(response)
                for issue in result.get("issues", []):
                    issues.append({
                        "type": "cross_section_inconsistency",
                        "sections": [intro_section.title, conclusion_section.title],
                        "issue": issue,
                        "severity": "medium"
                    })
            except:
                pass
        
        return issues
    
    async def _check_data_figure_consistency(self, sections: List[Any]) -> List[Dict[str, Any]]:
        """データと図表の整合性チェック - 簡易実装"""
        issues = []
        
        # Results セクションのチェック
        results_section = next((s for s in sections if "result" in s.title.lower()), None)
        if results_section:
            # 図表参照の整合性チェック（簡易）
            content = results_section.content.lower()
            if "figure" in content or "table" in content:
                if "fig" not in content and "table" not in content:
                    issues.append({
                        "type": "figure_reference_inconsistency", 
                        "section": results_section.title,
                        "issue": "図表への参照が不完全な可能性があります",
                        "severity": "low"
                    })
        
        return issues
    
    def _generate_overall_assessment(self, avg_score: float, issues: List[str]) -> str:
        """全体評価の生成"""
        if avg_score >= 8.0:
            return "優秀な品質レベルです。軽微な改善で投稿可能です。"
        elif avg_score >= 6.0:
            return "良好な品質レベルです。いくつかの改善が推奨されます。"
        elif avg_score >= 4.0:
            return "改善が必要です。主要な問題を解決してから投稿を検討してください。"
        else:
            return "大幅な改善が必要です。構造的な見直しを推奨します。"
    
    # ==========================================
    # キャッシュ・リトライ機能
    # ==========================================
    
    def _generate_cache_key(self, section_id: str, analysis_type: str, focus: str, content: str) -> str:
        """キャッシュキーの生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{analysis_type}:{section_id}:{focus}:{content_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュから取得（TTL付き）"""
        global _analysis_cache
        if cache_key in _analysis_cache:
            cached_data, timestamp = _analysis_cache[cache_key]
            # 1時間のTTL
            if datetime.now() - timestamp < timedelta(hours=1):
                logger.info(f"[AnalysisAgent] キャッシュヒット: {cache_key}")
                return cached_data
            else:
                # 期限切れのため削除
                del _analysis_cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """キャッシュに保存"""
        global _analysis_cache
        _analysis_cache[cache_key] = (data, datetime.now())
        logger.info(f"[AnalysisAgent] キャッシュ保存: {cache_key}")
    
    async def _call_openai_with_retry(self, prompt: str) -> str:
        """リトライ付きOpenAI API呼び出し"""
        max_retries = 3
        base_delay = 1.0  # 初回待機時間（秒）
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[AnalysisAgent] OpenAI API呼び出し (試行 {attempt + 1}/{max_retries})")
                
                response_data = await openai_client.generate_text(
                    prompt=prompt
                )
                
                response = response_data.get("content", "")
                
                return response
                
            except Exception as e:
                logger.warning(f"[AnalysisAgent] OpenAI API呼び出し失敗 (試行 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:  # 最後の試行でない場合
                    # 指数バックオフ
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"[AnalysisAgent] {delay}秒待機後にリトライします")
                    await asyncio.sleep(delay)
                else:
                    # 全てのリトライが失敗
                    logger.error(f"[AnalysisAgent] 最大リトライ回数に達しました: {e}")
                    raise AgentExecutionError(f"OpenAI API呼び出しが3回失敗しました: {e}")