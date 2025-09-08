"""
Quality Agent - 品質保証エージェント
統合機能: 品質評価、適合性チェック、倫理検証
"""
from typing import Dict, List, Any, Optional
import logging
import json
import hashlib
import asyncio
from datetime import datetime, timedelta

from .enhanced_base_agent import EnhancedBaseAgent, ExecutionMetrics, AgentTask
from .base_agent import AgentExecutionError, AgentValidationError
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.external.openai_client import openai_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# 品質評価キャッシュ
_quality_cache = {}

class QualityAgent(EnhancedBaseAgent):
    """
    品質保証エージェント
    
    統合された責務:
    - 品質評価: 学術的水準評価、完成度査定
    - 適合性チェック: ジャーナル要件確認、投稿規定照合
    - 倫理検証: 研究倫理確認、再現性検証
    """
    
    def __init__(self, session=None):
        super().__init__(session=session, timeout=settings.AI_AGENT_TIMEOUT_SECONDS)
        self.repository = PaperRepository(session) if session else None
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "quality_assessment",      # 品質評価
            "compliance_check",        # 適合性チェック
            "ethics_validation",       # 倫理検証
            "peer_review_prediction",  # 査読予測
            "journal_requirements_check", # ジャーナル要件チェック
            "reproducibility_check",   # 再現性チェック
            "academic_rigor_evaluation", # 学術的厳密性評価
            "comprehensive_quality_audit" # 包括的品質監査
        ]
    
    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コア実行ロジック"""
        if not self.repository:
            raise AgentExecutionError("データベースセッションが必要です")
        
        task_type = task.task_type
        
        if task_type == "quality_assessment":
            return await self._perform_quality_assessment(task.parameters, metrics)
        elif task_type == "compliance_check":
            return await self._perform_compliance_check(task.parameters, metrics)
        elif task_type == "ethics_validation":
            return await self._perform_ethics_validation(task.parameters, metrics)
        elif task_type == "peer_review_prediction":
            return await self._perform_peer_review_prediction(task.parameters, metrics)
        elif task_type == "journal_requirements_check":
            return await self._perform_journal_requirements_check(task.parameters, metrics)
        elif task_type == "reproducibility_check":
            return await self._perform_reproducibility_check(task.parameters, metrics)
        elif task_type == "academic_rigor_evaluation":
            return await self._perform_academic_rigor_evaluation(task.parameters, metrics)
        elif task_type == "comprehensive_quality_audit":
            return await self._perform_comprehensive_quality_audit(task.parameters, metrics)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _perform_quality_assessment(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """品質評価の実行"""
        paper_id = params.get("paper_id")
        assessment_criteria = params.get("criteria", "comprehensive")  # "novelty", "methodology", "presentation"
        evaluation_depth = params.get("depth", "detailed")  # "quick", "detailed", "thorough"
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        
        try:
            # 全セクション取得
            sections = await self.repository.get_sections_by_paper(paper_id)
            metrics.items_processed = len(sections)
            
            if not sections:
                return {
                    "quality_scores": {},
                    "overall_quality": 0,
                    "improvement_recommendations": [],
                    "readiness_assessment": "incomplete",
                    "success": True
                }
            
            # 各セクションの品質評価
            section_assessments = []
            overall_scores = {}
            
            for section in sections:
                # キャッシュキー生成
                cache_key = self._generate_cache_key(
                    section.id, "quality_assessment", assessment_criteria, section.content
                )
                
                # キャッシュチェック
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    assessment_data = cached_result
                else:
                    # 品質評価プロンプト
                    assessment_prompt = self._build_quality_assessment_prompt(
                        section.title, section.content, assessment_criteria, evaluation_depth
                    )
                    
                    response = await self._call_openai_with_retry(assessment_prompt)
                    
                    try:
                        assessment_data = json.loads(response)
                        self._save_to_cache(cache_key, assessment_data)
                    except:
                        assessment_data = {
                            "quality_score": 6,
                            "strengths": ["品質評価が部分的に完了"],
                            "weaknesses": ["詳細な評価が必要"],
                            "recommendations": ["再評価を推奨"]
                        }
                
                section_assessment = {
                    "section_id": section.id,
                    "section_title": section.title,
                    "quality_score": assessment_data.get("quality_score", 6),
                    "novelty_score": assessment_data.get("novelty_score", 6),
                    "methodology_score": assessment_data.get("methodology_score", 6),
                    "presentation_score": assessment_data.get("presentation_score", 6),
                    "strengths": assessment_data.get("strengths", []),
                    "weaknesses": assessment_data.get("weaknesses", []),
                    "critical_issues": assessment_data.get("critical_issues", []),
                    "improvement_priority": assessment_data.get("improvement_priority", "medium")
                }
                
                section_assessments.append(section_assessment)
                metrics.items_successful += 1
            
            # 全体品質スコア計算
            avg_quality = sum(s["quality_score"] for s in section_assessments) / len(section_assessments)
            avg_novelty = sum(s["novelty_score"] for s in section_assessments) / len(section_assessments)
            avg_methodology = sum(s["methodology_score"] for s in section_assessments) / len(section_assessments)
            avg_presentation = sum(s["presentation_score"] for s in section_assessments) / len(section_assessments)
            
            overall_scores = {
                "overall_quality": avg_quality,
                "novelty": avg_novelty,
                "methodology": avg_methodology,
                "presentation": avg_presentation
            }
            
            # 投稿準備度評価
            readiness = self._assess_publication_readiness(avg_quality, section_assessments)
            
            # 改善推奨事項
            recommendations = self._generate_improvement_recommendations(section_assessments)
            
            return {
                "section_assessments": section_assessments,
                "quality_scores": overall_scores,
                "overall_quality": avg_quality,
                "improvement_recommendations": recommendations,
                "readiness_assessment": readiness,
                "assessment_criteria": assessment_criteria,
                "sections_evaluated": len(section_assessments),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[QualityAgent] 品質評価エラー: {e}")
            raise AgentExecutionError(f"品質評価でエラーが発生しました: {e}")
    
    async def _perform_compliance_check(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """適合性チェックの実行"""
        paper_id = params.get("paper_id")
        target_journal = params.get("target_journal", "general")  # "Nature", "Science", "IEEE", etc.
        check_scope = params.get("scope", "format_and_content")  # "format", "content", "format_and_content"
        
        try:
            sections = await self.repository.get_sections_by_paper(paper_id)
            metrics.items_processed = len(sections)
            
            compliance_issues = []
            compliance_score = 100
            
            # ジャーナル固有のチェック
            journal_specific_checks = self._get_journal_requirements(target_journal)
            
            # 各セクションのフォーマットチェック
            for section in sections:
                section_issues = await self._check_section_compliance(
                    section, journal_specific_checks, check_scope
                )
                compliance_issues.extend(section_issues)
                compliance_score -= len(section_issues) * 5  # 1問題につき5点減点
            
            compliance_score = max(0, compliance_score)
            metrics.items_successful = len(sections)
            
            # 適合性レポート生成
            compliance_summary = self._generate_compliance_summary(
                compliance_score, compliance_issues, target_journal
            )
            
            return {
                "compliance_issues": compliance_issues,
                "compliance_score": compliance_score,
                "target_journal": target_journal,
                "check_scope": check_scope,
                "compliance_summary": compliance_summary,
                "sections_checked": len(sections),
                "journal_requirements": journal_specific_checks,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[QualityAgent] 適合性チェックエラー: {e}")
            raise AgentExecutionError(f"適合性チェックでエラーが発生しました: {e}")
    
    async def _perform_ethics_validation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """倫理検証の実行"""
        paper_id = params.get("paper_id")
        validation_scope = params.get("scope", "comprehensive")  # "human_subjects", "data_privacy", "reproducibility"
        
        try:
            sections = await self.repository.get_sections_by_paper(paper_id)
            metrics.items_processed = len(sections)
            
            ethics_issues = []
            ethics_score = 100
            
            # 倫理的問題のチェック
            for section in sections:
                # キャッシュ処理
                cache_key = self._generate_cache_key(
                    section.id, "ethics_validation", validation_scope, section.content
                )
                
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    section_ethics = cached_result
                else:
                    # 倫理検証プロンプト
                    ethics_prompt = self._build_ethics_validation_prompt(
                        section.title, section.content, validation_scope
                    )
                    
                    response = await self._call_openai_with_retry(ethics_prompt)
                    
                    try:
                        section_ethics = json.loads(response)
                        self._save_to_cache(cache_key, section_ethics)
                    except:
                        section_ethics = {
                            "ethics_issues": [],
                            "compliance_status": "needs_review",
                            "recommendations": ["詳細な倫理審査を推奨"]
                        }
                
                # 倫理問題の統合
                issues = section_ethics.get("ethics_issues", [])
                for issue in issues:
                    ethics_issues.append({
                        "section": section.title,
                        "issue_type": issue.get("type", "general"),
                        "description": issue.get("description", ""),
                        "severity": issue.get("severity", "medium"),
                        "recommendation": issue.get("recommendation", "")
                    })
                
                ethics_score -= len(issues) * 10  # 1問題につき10点減点
            
            ethics_score = max(0, ethics_score)
            metrics.items_successful = len(sections)
            
            # 倫理的適合性の判定
            ethics_status = self._determine_ethics_status(ethics_score, ethics_issues)
            
            return {
                "ethics_issues": ethics_issues,
                "ethics_score": ethics_score,
                "ethics_status": ethics_status,
                "validation_scope": validation_scope,
                "sections_validated": len(sections),
                "recommendations": self._generate_ethics_recommendations(ethics_issues),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[QualityAgent] 倫理検証エラー: {e}")
            raise AgentExecutionError(f"倫理検証でエラーが発生しました: {e}")
    
    async def _perform_peer_review_prediction(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """査読予測 - quality_assessmentの特化版"""
        params["criteria"] = "peer_review"
        params["depth"] = "thorough"
        result = await self._perform_quality_assessment(params, metrics)
        
        # 査読予測特有の情報を追加
        predicted_issues = []
        for assessment in result.get("section_assessments", []):
            for weakness in assessment.get("weaknesses", []):
                predicted_issues.append({
                    "section": assessment["section_title"],
                    "likely_reviewer_comment": weakness,
                    "severity": "medium",
                    "suggested_response": "詳細な説明を追加してください"
                })
        
        result["predicted_reviewer_issues"] = predicted_issues
        result["acceptance_probability"] = self._calculate_acceptance_probability(result["overall_quality"])
        
        return result
    
    async def _perform_journal_requirements_check(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """ジャーナル要件チェック - compliance_checkの特化版"""
        params["scope"] = "format_and_content"
        return await self._perform_compliance_check(params, metrics)
    
    async def _perform_reproducibility_check(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """再現性チェック - ethics_validationの特化版"""
        params["scope"] = "reproducibility"
        return await self._perform_ethics_validation(params, metrics)
    
    async def _perform_academic_rigor_evaluation(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """学術的厳密性評価 - quality_assessmentの特化版"""
        params["criteria"] = "methodology"
        params["depth"] = "thorough"
        return await self._perform_quality_assessment(params, metrics)
    
    async def _perform_comprehensive_quality_audit(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """包括的品質監査 - 全機能統合"""
        try:
            results = {}
            
            # 1. 品質評価
            quality_result = await self._perform_quality_assessment(params, metrics)
            results["quality_assessment"] = quality_result
            
            # 2. 適合性チェック
            compliance_result = await self._perform_compliance_check(params, metrics)
            results["compliance_check"] = compliance_result
            
            # 3. 倫理検証
            ethics_result = await self._perform_ethics_validation(params, metrics)
            results["ethics_validation"] = ethics_result
            
            # 統合スコア計算
            integrated_score = (
                quality_result.get("overall_quality", 0) * 0.5 +
                compliance_result.get("compliance_score", 0) / 100 * 10 * 0.3 +
                ethics_result.get("ethics_score", 0) / 100 * 10 * 0.2
            )
            
            # 最終判定
            final_recommendation = self._generate_final_recommendation(integrated_score, results)
            
            return {
                "comprehensive_results": results,
                "integrated_score": integrated_score,
                "final_recommendation": final_recommendation,
                "audit_phases": ["quality", "compliance", "ethics"],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[QualityAgent] 包括的品質監査エラー: {e}")
            raise AgentExecutionError(f"包括的品質監査でエラーが発生しました: {e}")
    
    # ==========================================
    # ヘルパーメソッド
    # ==========================================
    
    def _assess_publication_readiness(self, quality_score: float, assessments: List[Dict]) -> str:
        """投稿準備度の評価"""
        critical_issues = sum(len(a.get("critical_issues", [])) for a in assessments)
        
        if quality_score >= 8.0 and critical_issues == 0:
            return "ready_for_submission"
        elif quality_score >= 6.0 and critical_issues <= 2:
            return "minor_revisions_needed"
        elif quality_score >= 4.0:
            return "major_revisions_needed"
        else:
            return "substantial_rewriting_required"
    
    def _generate_improvement_recommendations(self, assessments: List[Dict]) -> List[str]:
        """改善推奨事項の生成"""
        recommendations = []
        
        # 高優先度の改善点を抽出
        for assessment in assessments:
            if assessment.get("improvement_priority") == "high":
                for weakness in assessment.get("weaknesses", []):
                    recommendations.append(f"{assessment['section_title']}: {weakness}")
        
        return recommendations[:10]  # 上位10件
    
    def _get_journal_requirements(self, journal: str) -> Dict[str, Any]:
        """ジャーナル固有要件の取得"""
        requirements = {
            "Nature": {
                "max_word_count": 3000,
                "required_sections": ["Abstract", "Introduction", "Results", "Discussion"],
                "reference_format": "Nature",
                "figure_requirements": "high_resolution"
            },
            "Science": {
                "max_word_count": 2500,
                "required_sections": ["Abstract", "Introduction", "Results", "Discussion"],
                "reference_format": "Science",
                "figure_requirements": "publication_ready"
            },
            "general": {
                "max_word_count": 8000,
                "required_sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
                "reference_format": "standard",
                "figure_requirements": "clear_labels"
            }
        }
        return requirements.get(journal, requirements["general"])
    
    async def _check_section_compliance(self, section: Any, requirements: Dict, scope: str) -> List[Dict]:
        """セクション適合性チェック"""
        issues = []
        
        # 基本的なチェック
        if len(section.content) < 100:
            issues.append({
                "type": "content_length",
                "description": f"{section.title}セクションが短すぎます",
                "severity": "medium"
            })
        
        # 必須セクションチェック
        required_sections = requirements.get("required_sections", [])
        if section.title not in required_sections and any(req in section.title for req in required_sections):
            issues.append({
                "type": "section_naming",
                "description": f"セクション名が標準と異なります: {section.title}",
                "severity": "low"
            })
        
        return issues
    
    def _generate_compliance_summary(self, score: int, issues: List[Dict], journal: str) -> str:
        """適合性サマリー生成"""
        if score >= 90:
            return f"{journal}誌の要件に十分適合しています。軽微な調整で投稿可能です。"
        elif score >= 70:
            return f"{journal}誌の要件におおむね適合していますが、いくつかの改善が必要です。"
        elif score >= 50:
            return f"{journal}誌の要件への適合には大幅な修正が必要です。"
        else:
            return f"{journal}誌の要件を満たすには根本的な見直しが必要です。"
    
    def _determine_ethics_status(self, score: int, issues: List[Dict]) -> str:
        """倫理的適合性の判定"""
        high_severity_issues = [i for i in issues if i.get("severity") == "high"]
        
        if score >= 90 and not high_severity_issues:
            return "ethically_compliant"
        elif score >= 70:
            return "minor_ethics_concerns"
        elif score >= 50:
            return "moderate_ethics_concerns"
        else:
            return "significant_ethics_concerns"
    
    def _generate_ethics_recommendations(self, issues: List[Dict]) -> List[str]:
        """倫理的推奨事項の生成"""
        recommendations = []
        
        for issue in issues:
            if issue.get("severity") in ["high", "medium"]:
                rec = issue.get("recommendation", "詳細な検討が必要")
                recommendations.append(f"{issue.get('issue_type', '一般')}: {rec}")
        
        return recommendations
    
    def _calculate_acceptance_probability(self, quality_score: float) -> float:
        """受諾確率の計算"""
        if quality_score >= 9.0:
            return 0.9
        elif quality_score >= 8.0:
            return 0.75
        elif quality_score >= 7.0:
            return 0.6
        elif quality_score >= 6.0:
            return 0.4
        elif quality_score >= 5.0:
            return 0.25
        else:
            return 0.1
    
    def _generate_final_recommendation(self, integrated_score: float, results: Dict) -> str:
        """最終推奨事項の生成"""
        if integrated_score >= 8.5:
            return "投稿準備完了。高い品質を維持しています。"
        elif integrated_score >= 7.0:
            return "軽微な修正後に投稿可能。全体的に良好な品質です。"
        elif integrated_score >= 5.5:
            return "中程度の修正が必要。品質向上後に投稿を検討してください。"
        elif integrated_score >= 4.0:
            return "大幅な修正が必要。構造的な改善を行ってください。"
        else:
            return "根本的な見直しが必要。専門家の指導を求めることを推奨します。"
    
    # ==========================================
    # プロンプト生成メソッド
    # ==========================================
    
    def _build_quality_assessment_prompt(self, title: str, content: str, criteria: str, depth: str) -> str:
        """品質評価用プロンプト生成"""
        return f"""
以下の論文セクションの学術的品質を{criteria}の観点から{depth}レベルで評価してください。

セクション: {title}
内容: {content}

評価基準: {criteria}
評価深度: {depth}

以下の形式でJSONを返してください:
{{
    "quality_score": 8,
    "novelty_score": 7,
    "methodology_score": 8,
    "presentation_score": 9,
    "strengths": ["強み1", "強み2", "強み3"],
    "weaknesses": ["弱点1", "弱点2"],
    "critical_issues": ["重要な問題1", "重要な問題2"],
    "improvement_priority": "high/medium/low",
    "academic_contribution": "significant/moderate/minor"
}}
"""
    
    def _build_ethics_validation_prompt(self, title: str, content: str, scope: str) -> str:
        """倫理検証用プロンプト生成"""
        return f"""
以下の論文セクションを研究倫理の観点から{scope}スコープで検証してください。

セクション: {title}
内容: {content}

検証スコープ: {scope}

以下の形式でJSONを返してください:
{{
    "ethics_issues": [
        {{
            "type": "human_subjects/data_privacy/reproducibility",
            "description": "問題の詳細",
            "severity": "high/medium/low",
            "recommendation": "推奨される対応"
        }}
    ],
    "compliance_status": "compliant/needs_review/non_compliant",
    "reproducibility_score": 8,
    "data_availability": "adequate/limited/insufficient"
}}
"""
    
    # ==========================================
    # キャッシュ・リトライ機能
    # ==========================================
    
    def _generate_cache_key(self, section_id: str, quality_type: str, criteria: str, content: str) -> str:
        """キャッシュキー生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"quality:{quality_type}:{section_id}:{criteria}:{content_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュから取得（TTL付き）"""
        global _quality_cache
        if cache_key in _quality_cache:
            cached_data, timestamp = _quality_cache[cache_key]
            # 2時間のTTL（品質評価は長めに保持）
            if datetime.now() - timestamp < timedelta(hours=2):
                logger.info(f"[QualityAgent] キャッシュヒット: {cache_key}")
                return cached_data
            else:
                del _quality_cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """キャッシュに保存"""
        global _quality_cache
        _quality_cache[cache_key] = (data, datetime.now())
        logger.info(f"[QualityAgent] キャッシュ保存: {cache_key}")
    
    async def _call_openai_with_retry(self, prompt: str) -> str:
        """リトライ付きOpenAI API呼び出し"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[QualityAgent] OpenAI API呼び出し (試行 {attempt + 1}/{max_retries})")
                
                response_data = await openai_client.generate_text(
                    prompt=prompt
                )
                response = response_data.get("content", "")
                
                return response
                
            except Exception as e:
                logger.warning(f"[QualityAgent] OpenAI API呼び出し失敗 (試行 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"[QualityAgent] {delay}秒待機後にリトライします")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[QualityAgent] 最大リトライ回数に達しました: {e}")
                    raise AgentExecutionError(f"OpenAI API呼び出しが3回失敗しました: {e}")