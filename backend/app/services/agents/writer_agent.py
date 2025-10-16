"""
簡素化されたライティングエージェント
"""
from typing import Any, Dict, List, Optional
import logging

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.infrastructure.external.openai_client import openai_client
from app.infrastructure.repositories.paper_repository import PaperRepository
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
        self.repository = PaperRepository(session) if session else None
    
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
        """新規コンテンツを生成してDBに保存（複数セクション対応）"""
        title = params.get("title")
        section_type = params.get("section_type", "general")
        requirements = params.get("requirements", "")
        target_length = params.get("target_length", 500)
        tone = params.get("tone", "academic")
        context = params.get("context", "")
        paper_id = params.get("paper_id")

        if not title:
            raise AgentValidationError("title は必須です")

        # 複数セクションタイトルの分割（", "、" and "、"と"で区切られている場合）
        import re
        titles = re.split(r',\s*|\s+and\s+|\s+と\s+', title)
        titles = [t.strip() for t in titles if t.strip()]

        if len(titles) == 0:
            raise AgentValidationError("有効なタイトルが見つかりません")

        try:
            results = []
            all_section_ids = []
            total_word_count = 0
            total_char_count = 0

            # 各セクションを処理
            for single_title in titles:
                # コンテンツ生成
                content = await self._generate_content_with_openai(
                    single_title, section_type, requirements, target_length, tone, context
                )

                logger.info(f"[WriterAgent] コンテンツ生成完了: '{single_title}' ({len(content)}文字)")

                # DBに保存（repositoryが利用可能な場合）
                section_id = None
                if self.repository and paper_id:
                    try:
                        # 該当セクションを検索
                        sections = await self.repository.get_sections_by_paper(paper_id)
                        target_section = None
                        for section in sections:
                            if section.title == single_title:
                                target_section = section
                                break

                        if target_section:
                            # word_countも一緒に更新
                            word_count = len(content.split())
                            await self.repository.update_section(
                                section_id=target_section.id,
                                update_data={
                                    "content": content,
                                    "word_count": word_count
                                }
                            )
                            section_id = target_section.id
                            logger.info(f"[WriterAgent] セクション更新完了: ID={section_id}, title='{single_title}', word_count={word_count}")
                        else:
                            logger.warning(f"[WriterAgent] セクションが見つかりません: title='{single_title}', paper_id={paper_id}")
                    except Exception as db_error:
                        logger.error(f"[WriterAgent] DB保存エラー: {db_error}")
                        # DB保存失敗してもコンテンツ生成は成功として返す

                word_count = len(content.split())
                char_count = len(content)
                total_word_count += word_count
                total_char_count += char_count

                results.append({
                    "title": single_title,
                    "content": content,
                    "section_id": section_id,
                    "word_count": word_count,
                    "character_count": char_count
                })

                if section_id:
                    all_section_ids.append(section_id)

            # 複数セクションの場合は統合結果を返す
            if len(results) == 1:
                return {
                    "content": results[0]["content"],
                    "section_id": results[0]["section_id"],
                    "word_count": results[0]["word_count"],
                    "character_count": results[0]["character_count"],
                    "action": "generate_content",
                    "success": True
                }
            else:
                return {
                    "results": results,
                    "section_ids": all_section_ids,
                    "total_sections": len(results),
                    "total_word_count": total_word_count,
                    "total_character_count": total_char_count,
                    "action": "generate_content",
                    "success": True,
                    "message": f"{len(results)}個のセクションを生成しました"
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
        論文セクションの初稿を生成してDBに保存（複数セクション対応）
        責務拡張: セクションコンテンツの生成とDB保存（OutlineAgentと同様の設計）
        """
        section_title = params.get("section_title")
        requirements = params.get("requirements", "")
        paper_id = params.get("paper_id")
        context = params.get("context", {})

        if not section_title:
            raise AgentValidationError("section_title は必須です")

        # 複数セクションタイトルの分割（", "、" and "、"と"で区切られている場合）
        import re
        section_titles = re.split(r',\s*|\s+and\s+|\s+と\s+', section_title)
        section_titles = [t.strip() for t in section_titles if t.strip()]

        if len(section_titles) == 0:
            raise AgentValidationError("有効なセクションタイトルが見つかりません")

        try:
            results = []
            all_section_ids = []
            total_word_count = 0
            total_char_count = 0

            # 各セクションを処理
            for single_title in section_titles:
                logger.info(f"[WriterAgent] ドラフト生成開始: '{single_title}'")

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
タイトル: {single_title}
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
                    raise AgentExecutionError(f"コンテンツ生成結果が空です: '{single_title}'")

                logger.info(f"[WriterAgent] ドラフト生成完了: '{single_title}' ({len(draft_content)}文字, {len(draft_content.split())}語)")

                # DBに保存（repositoryが利用可能な場合）
                section_id = None
                if self.repository and paper_id:
                    try:
                        # 該当セクションを検索
                        sections = await self.repository.get_sections_by_paper(paper_id)
                        target_section = None
                        for section in sections:
                            if section.title == single_title:
                                target_section = section
                                break

                        if target_section:
                            # word_countも一緒に更新
                            word_count = len(draft_content.split())
                            await self.repository.update_section(
                                section_id=target_section.id,
                                update_data={
                                    "content": draft_content,
                                    "word_count": word_count
                                }
                            )
                            section_id = target_section.id
                            logger.info(f"[WriterAgent] セクション更新完了: ID={section_id}, title='{single_title}', word_count={word_count}")
                        else:
                            logger.warning(f"[WriterAgent] セクションが見つかりません: title='{single_title}', paper_id={paper_id}")
                    except Exception as db_error:
                        logger.error(f"[WriterAgent] DB保存エラー: {db_error}")
                        # DB保存失敗してもコンテンツ生成は成功として返す

                word_count = len(draft_content.split())
                char_count = len(draft_content)
                total_word_count += word_count
                total_char_count += char_count

                results.append({
                    "title": single_title,
                    "draft_content": draft_content,
                    "content": draft_content,  # 後方互換性
                    "section_id": section_id,
                    "word_count": word_count,
                    "character_count": char_count
                })

                if section_id:
                    all_section_ids.append(section_id)

            # 複数セクションの場合は統合結果を返す
            if len(results) == 1:
                return {
                    "draft_content": results[0]["draft_content"],
                    "content": results[0]["content"],
                    "section_id": results[0]["section_id"],
                    "section_title": results[0]["title"],
                    "word_count": results[0]["word_count"],
                    "character_count": results[0]["character_count"],
                    "action": "generate_draft",
                    "success": True,
                    "message": f"セクション「{results[0]['title']}」のコンテンツを生成しました"
                }
            else:
                return {
                    "results": results,
                    "section_ids": all_section_ids,
                    "total_sections": len(results),
                    "total_word_count": total_word_count,
                    "total_character_count": total_char_count,
                    "action": "generate_draft",
                    "success": True,
                    "message": f"{len(results)}個のセクションのコンテンツを生成しました"
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