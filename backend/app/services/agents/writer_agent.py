"""
簡素化されたライティングエージェント
"""
from typing import Any, Dict, List, Optional
import logging

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.infrastructure.external.openai_client import openai_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """簡素化されたライティングエージェント"""
    
    def __init__(self, session=None):
        super().__init__(
            name="WriterAgent",
            description="論文コンテンツの生成・改善を行うエージェント",
            max_retries=3,
            timeout=settings.AI_AGENT_TIMEOUT_SECONDS
        )
        self.session = session
    
    def _get_supported_task_types(self) -> List[str]:
        return [
            "generate_content",
            "rewrite_content", 
            "improve_style",
            "expand_content",
            "condense_content",
            "generate_draft",
            "academic_polish"
        ]
    
    async def _execute_core(self, task: AgentTask) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "generate_content":
            return await self._generate_content(parameters)
        elif task_type == "rewrite_content":
            return await self._rewrite_content(parameters)
        elif task_type == "improve_style":
            return await self._improve_style(parameters)
        elif task_type == "expand_content":
            return await self._expand_content(parameters)
        elif task_type == "condense_content":
            return await self._condense_content(parameters)
        elif task_type == "generate_draft":
            return await self._generate_draft(parameters)
        elif task_type == "academic_polish":
            return await self._academic_polish(parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _generate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """新規コンテンツを生成"""
        title = params.get("title")
        section_type = params.get("section_type", "general")
        requirements = params.get("requirements", "")
        target_length = params.get("target_length", 500)
        tone = params.get("tone", "academic")
        context = params.get("context", "")
        
        if not title:
            raise AgentValidationError("title は必須です")
        
        try:
            # コンテンツ生成
            content = await self._generate_content_with_openai(
                title, section_type, requirements, target_length, tone, context
            )
            
            return {
                "content": content,
                "word_count": len(content.split()),
                "character_count": len(content),
                "action": "generate_content",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"コンテンツ生成エラー: {e}")
            raise AgentExecutionError(f"コンテンツ生成に失敗しました: {e}")
    
    async def _rewrite_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """既存コンテンツをリライト"""
        original_content = params.get("original_content")
        improvement_instructions = params.get("improvement_instructions", "")
        
        if not original_content:
            raise AgentValidationError("original_content は必須です")
        
        try:
            prompt = f"""以下の文章をより良く改善してください。

【改善指示】
{improvement_instructions}

【元の文章】
{original_content}

【改善された文章】"""
            
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            rewritten_content = result.get("content", "")
            
            return {
                "original_content": original_content,
                "rewritten_content": rewritten_content,
                "word_count_change": len(rewritten_content.split()) - len(original_content.split()),
                "action": "rewrite_content",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"リライトエラー: {e}")
            raise AgentExecutionError(f"リライトに失敗しました: {e}")
    
    async def _improve_style(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """文章スタイルを改善"""
        content = params.get("content")
        target_style = params.get("target_style", "academic")
        
        if not content:
            raise AgentValidationError("content は必須です")
        
        try:
            prompt = f"""以下の文章を{target_style}スタイルに改善してください。

【元の文章】
{content}

【改善された文章】"""
            
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            improved_content = result.get("content", "")
            
            return {
                "original_content": content,
                "improved_content": improved_content,
                "target_style": target_style,
                "action": "improve_style",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"スタイル改善エラー: {e}")
            raise AgentExecutionError(f"スタイル改善に失敗しました: {e}")
    
    async def _expand_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツを展開"""
        content = params.get("content", "")
        expansion_points = params.get("expansion_points", [])
        
        prompt = f"""以下の文章を詳しく展開してください。

【元の文章】
{content}

【展開ポイント】
{', '.join(expansion_points) if expansion_points else '詳細説明を追加'}

【展開された文章】"""
        
        try:
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            expanded_content = result.get("content", "")
            
            return {
                "original_content": content,
                "expanded_content": expanded_content,
                "expansion_ratio": len(expanded_content) / len(content) if content else 1,
                "action": "expand_content",
                "success": True
            }
        except Exception as e:
            raise AgentExecutionError(f"コンテンツ展開に失敗しました: {e}")
    
    async def _condense_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツを要約"""
        content = params.get("content", "")
        target_length = params.get("target_length", 200)
        
        prompt = f"""以下の文章を{target_length}文字程度に要約してください。

【元の文章】
{content}

【要約】"""
        
        try:
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            condensed_content = result.get("content", "")
            
            return {
                "original_content": content,
                "condensed_content": condensed_content,
                "compression_ratio": len(condensed_content) / len(content) if content else 1,
                "action": "condense_content", 
                "success": True
            }
        except Exception as e:
            raise AgentExecutionError(f"コンテンツ要約に失敗しました: {e}")
    
    async def _generate_draft(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        論文セクションの初稿を生成（AAIDC準拠 - Clear Boundaries Pattern）
        責務: セクションコンテンツの生成のみ。DB保存は呼び出し元が担当。
        """
        section_title = params.get("section_title") 
        requirements = params.get("requirements", "")
        paper_id = params.get("paper_id")
        context = params.get("context", {})
        
        if not section_title:
            raise AgentValidationError("section_title は必須です")
        
        try:
            logger.info(f"[WriterAgent] ドラフト生成開始: '{section_title}'")
            
            # コンテキストから論文情報を取得
            paper_context = ""
            if context and "outline" in context:
                outline_result = context["outline"]
                if "section_metadata" in outline_result:
                    metadata = outline_result["section_metadata"]
                    paper_context += f"セクション番号: {metadata.get('section_number')}\n"
                    paper_context += f"階層: {metadata.get('hierarchy_path')}\n"
            
            # プロンプト構築
            prompt = f"""学術論文の以下のセクションの高品質なコンテンツを生成してください。

【セクション情報】
タイトル: {section_title}
{paper_context}

【要件】
{requirements if requirements else '学術的で論理的な内容を含む包括的なセクション'}

【生成指針】
- 学術論文にふさわしい専門的で客観的な文体
- 論理的な構成と説得力のある議論
- 適切な長さ（500-1000語程度）
- 必要に応じて具体例や分析を含める

【セクション内容】"""
            
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            draft_content = result.get("content", "")
            
            if not draft_content:
                raise AgentExecutionError("コンテンツ生成結果が空です")
            
            logger.info(f"[WriterAgent] ドラフト生成完了: {len(draft_content.split())}語")
            
            # Clear Boundaries Pattern: WriterAgentはコンテンツのみ返す
            return {
                "draft_content": draft_content,
                "content": draft_content,  # 後方互換性
                "section_title": section_title,
                "word_count": len(draft_content.split()),
                "character_count": len(draft_content),
                "action": "generate_draft",
                "success": True,
                "message": f"セクション「{section_title}」のコンテンツを生成しました"
            }
            
        except Exception as e:
            logger.error(f"[WriterAgent] ドラフト生成エラー: {e}")
            raise AgentExecutionError(f"ドラフト生成に失敗しました: {e}")
    
    async def _academic_polish(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """学術的な文章に磨き上げる"""
        content = params.get("content", "")
        
        prompt = f"""以下の文章を学術論文に適したより洗練された文章に改善してください。

【元の文章】
{content}

【改善された文章】"""
        
        try:
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            polished_content = result.get("content", "")
            
            return {
                "original_content": content,
                "polished_content": polished_content,
                "action": "academic_polish",
                "success": True
            }
        except Exception as e:
            raise AgentExecutionError(f"文章の磨き上げに失敗しました: {e}")
    
    async def _generate_content_with_openai(
        self,
        title: str,
        section_type: str,
        requirements: str,
        target_length: int,
        tone: str,
        context: str
    ) -> str:
        """OpenAI APIでコンテンツ生成"""
        
        prompt = f"""学術論文の{section_type}セクションを執筆してください。

【セクションタイトル】
{title}

【執筆要件】
- 文体: {tone}
- 目標文字数: {target_length}文字程度
- 要件: {requirements}

【文脈情報】
{context}

【執筆内容】"""
        
        try:
            result = await openai_client.generate_text(
                prompt=prompt,
                model="gpt-4o-mini"
            )
            content = result.get("content", "")
            
            return content.strip()
            
        except Exception as e:
            raise AgentExecutionError(f"OpenAIでのコンテンツ生成に失敗: {e}")