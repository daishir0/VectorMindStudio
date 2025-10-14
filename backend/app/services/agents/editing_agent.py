"""
Editing Agent - 総合編集エージェント
統合機能: 文体編集、内容拡充、可読性向上
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

logger = logging.getLogger(__name__)

# 編集結果キャッシュ
_editing_cache = {}

class EditingAgent(EnhancedBaseAgent):
    """
    総合編集エージェント
    
    統合された責務:
    - 文体編集: 文章の簡潔化、可読性向上、文体調整
    - 内容拡充: セクション内容の拡充、不足要素の追加
    - 可読性向上: 文章の読みやすさ向上、接続詞改善
    """
    
    def __init__(self, session=None):
        super().__init__(session=session, timeout=60)
        self.repository = PaperRepository(session) if session else None
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "style_editing",           # 文体編集・調整
            "content_enhancement",     # 内容拡充
            "readability_improvement", # 可読性向上
            "conciseness_editing",     # 簡潔性向上
            "tone_adjustment",         # トーン調整
            "terminology_clarification", # 専門用語説明追加
            "flow_improvement",        # 文章流れ改善
            "comprehensive_editing"    # 包括的編集（全機能統合）
        ]
    
    async def _execute_core(self, task: AgentTask, metrics: ExecutionMetrics) -> Any:
        """コア実行ロジック"""
        if not self.repository:
            raise AgentExecutionError("データベースセッションが必要です")
        
        task_type = task.task_type
        
        if task_type == "style_editing":
            return await self._perform_style_editing(task.parameters, metrics)
        elif task_type == "content_enhancement":
            return await self._perform_content_enhancement(task.parameters, metrics)
        elif task_type == "readability_improvement":
            return await self._perform_readability_improvement(task.parameters, metrics)
        elif task_type == "conciseness_editing":
            return await self._perform_conciseness_editing(task.parameters, metrics)
        elif task_type == "tone_adjustment":
            return await self._perform_tone_adjustment(task.parameters, metrics)
        elif task_type == "terminology_clarification":
            return await self._perform_terminology_clarification(task.parameters, metrics)
        elif task_type == "flow_improvement":
            return await self._perform_flow_improvement(task.parameters, metrics)
        elif task_type == "comprehensive_editing":
            return await self._perform_comprehensive_editing(task.parameters, metrics)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _perform_style_editing(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """文体編集の実行"""
        paper_id = params.get("paper_id")
        target_sections = params.get("target_sections", [])
        style_target = params.get("style_target", "academic")  # "academic", "concise", "accessible"
        editing_focus = params.get("focus", "general")  # "clarity", "formality", "precision"
        
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
                    "editing_results": [],
                    "total_changes": 0,
                    "improvement_score": 0,
                    "success": True
                }
            
            # 各セクションの文体編集
            editing_results = []
            total_changes = 0
            
            for section in sections:
                # キャッシュキーの生成
                cache_key = self._generate_cache_key(
                    section.id, "style_editing", style_target, section.content
                )
                
                # キャッシュチェック
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    editing_data = cached_result
                else:
                    # OpenAI APIを使用した文体編集（リトライ付き）
                    editing_prompt = self._build_style_editing_prompt(
                        section.title, section.content, style_target, editing_focus
                    )
                    
                    response = await self._call_openai_with_retry(editing_prompt, max_tokens=1500)
                    
                    # レスポンス解析
                    try:
                        editing_data = json.loads(response)
                        # キャッシュに保存
                        self._save_to_cache(cache_key, editing_data)
                    except:
                        # JSONパースに失敗した場合のフォールバック
                        editing_data = {
                            "edited_content": response[:1000] + "...",
                            "changes_made": ["文体編集が部分的に完了"],
                            "improvement_areas": ["完全な解析が必要"]
                        }
                
                # 編集結果の構築
                section_result = {
                    "section_id": section.id,
                    "section_title": section.title,
                    "original_content": section.content,
                    "edited_content": editing_data.get("edited_content", section.content),
                    "changes_made": editing_data.get("changes_made", []),
                    "improvement_score": editing_data.get("improvement_score", 5),
                    "word_count_before": len(section.content.split()),
                    "word_count_after": len(editing_data.get("edited_content", section.content).split()),
                    "readability_improvement": editing_data.get("readability_improvement", "moderate")
                }
                
                editing_results.append(section_result)
                total_changes += len(editing_data.get("changes_made", []))
                metrics.items_successful += 1
            
            # 全体評価
            avg_improvement_score = sum(r["improvement_score"] for r in editing_results) / len(editing_results)
            
            return {
                "editing_results": editing_results,
                "total_changes": total_changes,
                "improvement_score": avg_improvement_score,
                "style_target": style_target,
                "editing_focus": editing_focus,
                "sections_edited": len(editing_results),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[EditingAgent] 文体編集エラー: {e}")
            raise AgentExecutionError(f"文体編集でエラーが発生しました: {e}")
    
    async def _perform_content_enhancement(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """内容拡充の実行"""
        paper_id = params.get("paper_id")
        target_sections = params.get("target_sections", [])
        enhancement_type = params.get("enhancement_type", "comprehensive")  # "detail", "examples", "explanation"
        target_length = params.get("target_length", "moderate")  # "brief", "moderate", "detailed"
        
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
            
            enhancement_results = []
            
            for section in sections:
                # キャッシュキー生成
                cache_key = self._generate_cache_key(
                    section.id, "content_enhancement", enhancement_type, section.content
                )
                
                # キャッシュチェック
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    enhancement_data = cached_result
                else:
                    # 内容拡充プロンプト
                    enhancement_prompt = self._build_content_enhancement_prompt(
                        section.title, section.content, enhancement_type, target_length
                    )
                    
                    response = await self._call_openai_with_retry(enhancement_prompt, max_tokens=2000)
                    
                    try:
                        enhancement_data = json.loads(response)
                        self._save_to_cache(cache_key, enhancement_data)
                    except:
                        enhancement_data = {
                            "enhanced_content": response[:1500] + "...",
                            "added_elements": ["内容拡充が部分的に完了"],
                            "enhancement_quality": "moderate"
                        }
                
                section_result = {
                    "section_id": section.id,
                    "section_title": section.title,
                    "original_content": section.content,
                    "enhanced_content": enhancement_data.get("enhanced_content", section.content),
                    "added_elements": enhancement_data.get("added_elements", []),
                    "enhancement_quality": enhancement_data.get("enhancement_quality", "good"),
                    "word_count_increase": len(enhancement_data.get("enhanced_content", section.content).split()) - len(section.content.split()),
                    "completeness_score": enhancement_data.get("completeness_score", 7)
                }
                
                enhancement_results.append(section_result)
                metrics.items_successful += 1
            
            return {
                "enhancement_results": enhancement_results,
                "enhancement_type": enhancement_type,
                "target_length": target_length,
                "sections_enhanced": len(enhancement_results),
                "total_content_added": sum(r["word_count_increase"] for r in enhancement_results),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[EditingAgent] 内容拡充エラー: {e}")
            raise AgentExecutionError(f"内容拡充でエラーが発生しました: {e}")
    
    async def _perform_readability_improvement(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """可読性向上の実行"""
        paper_id = params.get("paper_id")
        target_sections = params.get("target_sections", [])
        readability_target = params.get("readability_target", "academic")  # "general", "academic", "technical"
        improvement_focus = params.get("focus", "flow")  # "flow", "clarity", "transitions"
        
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
            
            readability_results = []
            
            for section in sections:
                # キャッシュ処理
                cache_key = self._generate_cache_key(
                    section.id, "readability_improvement", readability_target, section.content
                )
                
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    readability_data = cached_result
                else:
                    # 可読性向上プロンプト
                    readability_prompt = self._build_readability_improvement_prompt(
                        section.title, section.content, readability_target, improvement_focus
                    )
                    
                    response = await self._call_openai_with_retry(readability_prompt, max_tokens=1500)
                    
                    try:
                        readability_data = json.loads(response)
                        self._save_to_cache(cache_key, readability_data)
                    except:
                        readability_data = {
                            "improved_content": response[:1000] + "...",
                            "readability_improvements": ["可読性向上が部分的に完了"],
                            "flow_score": 7
                        }
                
                section_result = {
                    "section_id": section.id,
                    "section_title": section.title,
                    "original_content": section.content,
                    "improved_content": readability_data.get("improved_content", section.content),
                    "readability_improvements": readability_data.get("readability_improvements", []),
                    "flow_score": readability_data.get("flow_score", 7),
                    "clarity_score": readability_data.get("clarity_score", 7),
                    "transition_quality": readability_data.get("transition_quality", "good")
                }
                
                readability_results.append(section_result)
                metrics.items_successful += 1
            
            avg_flow_score = sum(r["flow_score"] for r in readability_results) / len(readability_results)
            avg_clarity_score = sum(r["clarity_score"] for r in readability_results) / len(readability_results)
            
            return {
                "readability_results": readability_results,
                "readability_target": readability_target,
                "improvement_focus": improvement_focus,
                "average_flow_score": avg_flow_score,
                "average_clarity_score": avg_clarity_score,
                "sections_improved": len(readability_results),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[EditingAgent] 可読性向上エラー: {e}")
            raise AgentExecutionError(f"可読性向上でエラーが発生しました: {e}")
    
    async def _perform_conciseness_editing(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """簡潔性向上編集 - style_editingの特化版"""
        params["style_target"] = "concise"
        params["focus"] = "brevity"
        return await self._perform_style_editing(params, metrics)
    
    async def _perform_tone_adjustment(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """トーン調整 - style_editingの特化版"""
        params["style_target"] = params.get("target_tone", "academic")
        params["focus"] = "tone"
        return await self._perform_style_editing(params, metrics)
    
    async def _perform_terminology_clarification(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """専門用語説明追加 - content_enhancementの特化版"""
        params["enhancement_type"] = "terminology"
        params["target_length"] = "detailed"
        return await self._perform_content_enhancement(params, metrics)
    
    async def _perform_flow_improvement(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """文章流れ改善 - readability_improvementの特化版"""
        params["readability_target"] = "academic"
        params["focus"] = "flow"
        return await self._perform_readability_improvement(params, metrics)
    
    async def _perform_comprehensive_editing(self, params: Dict[str, Any], metrics: ExecutionMetrics) -> Dict[str, Any]:
        """包括的編集 - 全機能統合"""
        try:
            # 段階的な編集の実行
            results = {}
            
            # 1. 文体編集
            style_result = await self._perform_style_editing(params, metrics)
            results["style_editing"] = style_result
            
            # 2. 内容拡充
            content_result = await self._perform_content_enhancement(params, metrics)  
            results["content_enhancement"] = content_result
            
            # 3. 可読性向上
            readability_result = await self._perform_readability_improvement(params, metrics)
            results["readability_improvement"] = readability_result
            
            # 統合評価
            overall_score = (
                style_result.get("improvement_score", 5) +
                content_result.get("enhancement_results", [{}])[0].get("completeness_score", 5) +
                readability_result.get("average_flow_score", 5)
            ) / 3
            
            return {
                "comprehensive_results": results,
                "overall_improvement_score": overall_score,
                "editing_phases": ["style", "content", "readability"],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[EditingAgent] 包括的編集エラー: {e}")
            raise AgentExecutionError(f"包括的編集でエラーが発生しました: {e}")
    
    # ==========================================
    # プロンプト生成メソッド
    # ==========================================
    
    def _build_style_editing_prompt(self, title: str, content: str, style_target: str, focus: str) -> str:
        """文体編集用プロンプト生成"""
        return f"""
以下の論文セクションを{style_target}スタイルで編集し、{focus}に重点を置いて改善してください。

セクション: {title}
内容: {content}

編集目標:
- スタイル: {style_target}
- 重点: {focus}

以下の形式でJSONを返してください:
{{
    "edited_content": "編集後の完全なテキスト",
    "changes_made": ["変更点1", "変更点2", "変更点3"],
    "improvement_score": 8,
    "readability_improvement": "significant/moderate/minor",
    "style_consistency": "excellent/good/adequate"
}}
"""
    
    def _build_content_enhancement_prompt(self, title: str, content: str, enhancement_type: str, target_length: str) -> str:
        """内容拡充用プロンプト生成"""
        return f"""
以下の論文セクションの内容を{enhancement_type}な観点から{target_length}レベルで拡充してください。

セクション: {title}
内容: {content}

拡充目標:
- 拡充タイプ: {enhancement_type}
- 目標レベル: {target_length}

以下の形式でJSONを返してください:
{{
    "enhanced_content": "拡充後の完全なテキスト",
    "added_elements": ["追加要素1", "追加要素2", "追加要素3"],
    "completeness_score": 8,
    "enhancement_quality": "excellent/good/adequate",
    "academic_rigor": "high/medium/low"
}}
"""
    
    def _build_readability_improvement_prompt(self, title: str, content: str, readability_target: str, focus: str) -> str:
        """可読性向上用プロンプト生成"""
        return f"""
以下の論文セクションの可読性を{readability_target}レベルで向上させ、特に{focus}を重視してください。

セクション: {title}
内容: {content}

改善目標:
- 対象レベル: {readability_target}
- 重点領域: {focus}

以下の形式でJSONを返してください:
{{
    "improved_content": "可読性向上後の完全なテキスト",
    "readability_improvements": ["改善点1", "改善点2", "改善点3"],
    "flow_score": 8,
    "clarity_score": 8,
    "transition_quality": "excellent/good/adequate"
}}
"""
    
    # ==========================================
    # キャッシュ・リトライ機能（AnalysisAgentと共通）
    # ==========================================
    
    def _generate_cache_key(self, section_id: str, editing_type: str, target: str, content: str) -> str:
        """キャッシュキー生成"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"edit:{editing_type}:{section_id}:{target}:{content_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュから取得（TTL付き）"""
        global _editing_cache
        if cache_key in _editing_cache:
            cached_data, timestamp = _editing_cache[cache_key]
            # 1時間のTTL
            if datetime.now() - timestamp < timedelta(hours=1):
                logger.info(f"[EditingAgent] キャッシュヒット: {cache_key}")
                return cached_data
            else:
                # 期限切れのため削除
                del _editing_cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """キャッシュに保存"""
        global _editing_cache
        _editing_cache[cache_key] = (data, datetime.now())
        logger.info(f"[EditingAgent] キャッシュ保存: {cache_key}")
    
    async def _call_openai_with_retry(self, prompt: str, max_tokens: int = 1500) -> str:
        """リトライ付きOpenAI API呼び出し"""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                logger.info(f"[EditingAgent] OpenAI API呼び出し (試行 {attempt + 1}/{max_retries})")

                response = await openai_client.generate_text(
                    prompt=prompt
                )

                return response["content"]
                
            except Exception as e:
                logger.warning(f"[EditingAgent] OpenAI API呼び出し失敗 (試行 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"[EditingAgent] {delay}秒待機後にリトライします")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[EditingAgent] 最大リトライ回数に達しました: {e}")
                    raise AgentExecutionError(f"OpenAI API呼び出しが3回失敗しました: {e}")