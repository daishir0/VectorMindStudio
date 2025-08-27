"""
要約生成エージェント
セクション要約の自動生成・更新を担当（150-250文字）
"""
from typing import Any, Dict, List, Optional
import logging
import re

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.infrastructure.external.openai_client import openai_client

logger = logging.getLogger(__name__)


class SummaryAgent(BaseAgent):
    """
    要約生成エージェント
    
    実装パターン: Generator with Retry/Fallback
    責務: セクション要約の自動生成（150-250文字）
    """
    
    def __init__(self):
        super().__init__(
            name="SummaryAgent",
            description="論文セクションの要約を自動生成するエージェント",
            max_retries=3,
            timeout=20
        )
    
    def _get_supported_task_types(self) -> List[str]:
        return [
            "generate_summary",
            "batch_generate_summaries",
            "evaluate_summary_quality",
            "optimize_summary"
        ]
    
    async def _execute_core(self, task: AgentTask) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "generate_summary":
            return await self._generate_summary(parameters)
        elif task_type == "batch_generate_summaries":
            return await self._batch_generate_summaries(parameters)
        elif task_type == "evaluate_summary_quality":
            return await self._evaluate_summary_quality(parameters)
        elif task_type == "optimize_summary":
            return await self._optimize_summary(parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _generate_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクション要約を生成"""
        content = params.get("content")
        title = params.get("title", "")
        section_type = params.get("section_type", "general")  # intro, method, result, discussion, general
        target_length = params.get("target_length", 200)  # 文字数目標
        
        if not content or not content.strip():
            raise AgentValidationError("content は必須で、空でない文字列である必要があります")
        
        try:
            # セクションタイプに応じたプロンプト調整
            system_prompt = self._get_system_prompt(section_type, target_length)
            
            # 要約生成
            summary = await self._call_openai_for_summary(
                system_prompt, content, title, target_length
            )
            
            # 品質評価
            quality_score = await self._evaluate_summary_quality({
                "content": content,
                "summary": summary,
                "target_length": target_length
            })
            
            # 文字数チェック
            char_count = len(summary)
            is_within_range = 150 <= char_count <= 250
            
            return {
                "summary": summary,
                "character_count": char_count,
                "target_length": target_length,
                "within_range": is_within_range,
                "quality_score": quality_score.get("score", 0.0),
                "quality_details": quality_score.get("details", {}),
                "section_type": section_type,
                "action": "generate_summary",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"要約生成エラー: {e}")
            raise AgentExecutionError(f"要約生成に失敗しました: {e}")
    
    async def _batch_generate_summaries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """複数セクションの要約を一括生成"""
        sections = params.get("sections", [])
        
        if not sections or not isinstance(sections, list):
            raise AgentValidationError("sections は空でないリストである必要があります")
        
        try:
            results = []
            failed_count = 0
            
            for section in sections:
                try:
                    section_result = await self._generate_summary({
                        "content": section.get("content", ""),
                        "title": section.get("title", ""),
                        "section_type": section.get("section_type", "general"),
                        "target_length": 200
                    })
                    
                    results.append({
                        "section_id": section.get("id"),
                        "title": section.get("title"),
                        **section_result
                    })
                    
                except Exception as e:
                    logger.warning(f"セクション {section.get('id')} の要約生成失敗: {e}")
                    failed_count += 1
                    results.append({
                        "section_id": section.get("id"),
                        "title": section.get("title"),
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "results": results,
                "total_sections": len(sections),
                "successful_count": len(sections) - failed_count,
                "failed_count": failed_count,
                "action": "batch_generate_summaries",
                "success": failed_count == 0
            }
            
        except Exception as e:
            logger.error(f"一括要約生成エラー: {e}")
            raise AgentExecutionError(f"一括要約生成に失敗しました: {e}")
    
    async def _evaluate_summary_quality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """要約品質を評価"""
        content = params.get("content")
        summary = params.get("summary")
        target_length = params.get("target_length", 200)
        
        if not content or not summary:
            raise AgentValidationError("content と summary は必須です")
        
        try:
            details = {}
            
            # 文字数評価
            char_count = len(summary)
            length_score = self._evaluate_length(char_count, target_length)
            details["length"] = {
                "score": length_score,
                "character_count": char_count,
                "target_length": target_length,
                "within_range": 150 <= char_count <= 250
            }
            
            # キーワード含有率評価
            keyword_score = self._evaluate_keyword_coverage(content, summary)
            details["keyword_coverage"] = {
                "score": keyword_score,
                "description": "重要キーワードの含有率"
            }
            
            # 可読性評価
            readability_score = self._evaluate_readability(summary)
            details["readability"] = {
                "score": readability_score,
                "description": "文章の可読性"
            }
            
            # 総合スコア計算（重み付き平均）
            total_score = (
                length_score * 0.3 +
                keyword_score * 0.4 +
                readability_score * 0.3
            )
            
            return {
                "score": round(total_score, 2),
                "details": details,
                "recommendation": self._get_quality_recommendation(total_score, details),
                "action": "evaluate_summary_quality",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"要約品質評価エラー: {e}")
            raise AgentExecutionError(f"要約品質評価に失敗しました: {e}")
    
    async def _optimize_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """要約を最適化"""
        content = params.get("content")
        current_summary = params.get("current_summary")
        feedback = params.get("feedback", "")
        target_length = params.get("target_length", 200)
        
        if not content or not current_summary:
            raise AgentValidationError("content と current_summary は必須です")
        
        try:
            # 最適化プロンプト作成
            system_prompt = f"""あなたは学術論文の要約最適化の専門家です。
以下の要約を改善してください：

改善指針：
- 文字数: {target_length}文字程度（150-250文字範囲内）
- フィードバック反映: {feedback}
- より正確で簡潔な表現
- 重要ポイントの強調

元の内容と現在の要約を比較し、最適化された要約を生成してください。"""
            
            user_prompt = f"""【元の内容】
{content[:1000]}...

【現在の要約】
{current_summary}

【フィードバック】
{feedback}

上記を踏まえて、最適化された要約を生成してください。"""
            
            # OpenAI API呼び出し
            optimized_summary = await openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o-mini",
                max_tokens=300,
                temperature=0.3
            )
            
            # 最適化結果の評価
            quality_result = await self._evaluate_summary_quality({
                "content": content,
                "summary": optimized_summary,
                "target_length": target_length
            })
            
            return {
                "original_summary": current_summary,
                "optimized_summary": optimized_summary,
                "improvement": {
                    "original_length": len(current_summary),
                    "optimized_length": len(optimized_summary),
                    "quality_improvement": quality_result.get("score", 0.0)
                },
                "quality_details": quality_result.get("details", {}),
                "action": "optimize_summary",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"要約最適化エラー: {e}")
            raise AgentExecutionError(f"要約最適化に失敗しました: {e}")
    
    def _get_system_prompt(self, section_type: str, target_length: int) -> str:
        """セクションタイプ別のシステムプロンプト"""
        base_prompt = f"""あなたは学術論文の要約作成の専門家です。
与えられた内容を{target_length}文字程度（150-250文字以内）で要約してください。

要約の要件：
- 正確性: 元の内容を正確に反映
- 簡潔性: 冗長な表現を避ける
- 完結性: 要約だけで内容が理解できる
- 学術性: 適切な学術用語を使用"""
        
        section_specific = {
            "intro": "\n特に研究背景、目的、意義を中心に要約してください。",
            "method": "\n特に実験方法、データ収集方法、分析手法を中心に要約してください。",
            "result": "\n特に主要な発見、数値結果、統計的有意性を中心に要約してください。",
            "discussion": "\n特に結果の解釈、意義、限界、今後の課題を中心に要約してください。",
            "general": "\n内容に応じて最も重要なポイントを中心に要約してください。"
        }
        
        return base_prompt + section_specific.get(section_type, section_specific["general"])
    
    async def _call_openai_for_summary(
        self, 
        system_prompt: str, 
        content: str, 
        title: str, 
        target_length: int
    ) -> str:
        """OpenAI APIを使って要約生成"""
        user_prompt = f"""【タイトル】
{title}

【内容】
{content}

上記の内容を{target_length}文字程度で要約してください。"""
        
        try:
            summary = await openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o-mini",
                max_tokens=350,
                temperature=0.3
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API呼び出しエラー: {e}")
            raise AgentExecutionError(f"OpenAI APIでの要約生成に失敗しました: {e}")
    
    def _evaluate_length(self, char_count: int, target_length: int) -> float:
        """文字数評価（0.0-1.0）"""
        if 150 <= char_count <= 250:
            # 理想範囲内
            deviation = abs(char_count - target_length) / target_length
            return max(0.0, 1.0 - deviation)
        else:
            # 範囲外はペナルティ
            if char_count < 150:
                return max(0.0, char_count / 150 * 0.8)
            else:  # char_count > 250
                return max(0.0, 250 / char_count * 0.8)
    
    def _evaluate_keyword_coverage(self, content: str, summary: str) -> float:
        """キーワード含有率評価"""
        # 簡易実装：重要そうな単語の含有率をチェック
        import re
        
        # 内容から重要キーワードを抽出（カタカナ、英数字、漢字熟語）
        content_keywords = set(re.findall(r'[ア-ヲ]{2,}|[a-zA-Z]{3,}|[一-龯]{2,}', content))
        summary_keywords = set(re.findall(r'[ア-ヲ]{2,}|[a-zA-Z]{3,}|[一-龯]{2,}', summary))
        
        if not content_keywords:
            return 1.0
        
        # 重要キーワードのうち要約に含まれている割合
        coverage = len(content_keywords & summary_keywords) / len(content_keywords)
        return min(1.0, coverage * 2)  # 50%含有で満点
    
    def _evaluate_readability(self, summary: str) -> float:
        """可読性評価（簡易版）"""
        # 簡易実装：文の長さと複雑さをチェック
        sentences = re.split(r'[。．！？]', summary)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # 平均文長
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        # 理想的な文長は30-60文字
        if 30 <= avg_sentence_length <= 60:
            length_score = 1.0
        else:
            length_score = max(0.0, 1.0 - abs(avg_sentence_length - 45) / 45)
        
        # 文数の適切性（150-250文字で2-4文が理想）
        sentence_count = len(sentences)
        if 2 <= sentence_count <= 4:
            count_score = 1.0
        else:
            count_score = max(0.0, 1.0 - abs(sentence_count - 3) / 3)
        
        return (length_score + count_score) / 2
    
    def _get_quality_recommendation(self, score: float, details: Dict) -> str:
        """品質スコアに基づく改善推奨"""
        if score >= 0.8:
            return "高品質な要約です。"
        elif score >= 0.6:
            return "良好な要約ですが、微調整の余地があります。"
        elif score >= 0.4:
            return "改善が必要です。特に文字数とキーワードカバー率を確認してください。"
        else:
            return "大幅な改善が必要です。要約の再生成を推奨します。"