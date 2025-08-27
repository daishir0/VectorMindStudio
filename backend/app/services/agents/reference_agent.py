"""
文献検索・引用整形エージェント
ベクター検索による文献発見、IEEE形式引用生成を担当
"""
from typing import Any, Dict, List, Optional, Tuple
import logging
import re
from datetime import datetime

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.services.vector_service import VectorService
from app.infrastructure.external.openai_client import openai_client

logger = logging.getLogger(__name__)


class ReferenceAgent(BaseAgent):
    """
    文献検索・引用整形エージェント
    
    実装パターン: Parallel Search + Competitive Selection
    責務: 内部DBのタグ/ベクター検索、IEEE形式引用生成
    """
    
    def __init__(self):
        super().__init__(
            name="ReferenceAgent",
            description="文献検索と引用整形を行うエージェント",
            max_retries=3,
            timeout=25
        )
        self.vector_service = VectorService()
    
    def _get_supported_task_types(self) -> List[str]:
        return [
            "search_references",
            "generate_citation",
            "format_bibliography",
            "validate_references",
            "suggest_references",
            "extract_key_points"
        ]
    
    async def _execute_core(self, task: AgentTask) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "search_references":
            return await self._search_references(parameters)
        elif task_type == "generate_citation":
            return await self._generate_citation(parameters)
        elif task_type == "format_bibliography":
            return await self._format_bibliography(parameters)
        elif task_type == "validate_references":
            return await self._validate_references(parameters)
        elif task_type == "suggest_references":
            return await self._suggest_references(parameters)
        elif task_type == "extract_key_points":
            return await self._extract_key_points(parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    async def _search_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """文献検索（並列検索実装）"""
        user_id = params.get("user_id")
        query = params.get("query", "")
        keywords = params.get("keywords", [])
        tags = params.get("tags", [])
        limit = params.get("limit", 10)
        search_types = params.get("search_types", ["vector", "tag", "keyword"])
        
        if not user_id:
            raise AgentValidationError("user_id は必須です")
        
        if not any([query, keywords, tags]):
            raise AgentValidationError("query、keywords、tagsのいずれかは必須です")
        
        try:
            # 並列検索実行（Competitive Selectionパターン）
            search_results = {}
            
            # 1. ベクター検索
            if "vector" in search_types and query:
                vector_results = await self._vector_search(user_id, query, limit)
                search_results["vector"] = vector_results
            
            # 2. タグ検索
            if "tag" in search_types and tags:
                tag_results = await self._tag_search(user_id, tags, limit)
                search_results["tag"] = tag_results
            
            # 3. キーワード検索
            if "keyword" in search_types and keywords:
                keyword_results = await self._keyword_search(user_id, keywords, limit)
                search_results["keyword"] = keyword_results
            
            # 結果を統合・ランキング
            unified_results = await self._unify_search_results(search_results, limit)
            
            # 関連度スコアでソート
            unified_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            # IEEE形式の引用候補を生成
            citations = []
            for result in unified_results[:limit]:
                citation = await self._generate_ieee_citation(result)
                citations.append(citation)
            
            return {
                "query": query,
                "keywords": keywords,
                "tags": tags,
                "search_results": unified_results[:limit],
                "citations": citations,
                "search_summary": {
                    "total_found": len(unified_results),
                    "vector_results": len(search_results.get("vector", [])),
                    "tag_results": len(search_results.get("tag", [])),
                    "keyword_results": len(search_results.get("keyword", []))
                },
                "action": "search_references",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文献検索エラー: {e}")
            raise AgentExecutionError(f"文献検索に失敗しました: {e}")
    
    async def _vector_search(self, user_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """ベクター検索"""
        try:
            vector_results = await self.vector_service.search_similar_content(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            return [{
                "id": result.get("upload_id"),
                "filename": result.get("filename"),
                "content": result.get("content", "")[:300],  # 最初の300文字
                "relevance_score": result.get("relevance_score", 0),
                "tags": result.get("tags", []),
                "search_type": "vector",
                "chunk_number": result.get("chunk_number", 0)
            } for result in vector_results]
            
        except Exception as e:
            logger.warning(f"ベクター検索エラー: {e}")
            return []
    
    async def _tag_search(self, user_id: str, tags: List[str], limit: int) -> List[Dict[str, Any]]:
        """タグ検索"""
        try:
            # タグベースの検索（既存のベクターサービスを活用）
            tag_results = await self.vector_service.search_similar(
                query=" ".join(tags),  # タグをクエリとして使用
                user_id=user_id,
                limit=limit,
                tags=tags
            )
            
            return [{
                "id": result.get("upload_id"),
                "filename": result.get("filename"),
                "content": result.get("document", "")[:300],
                "relevance_score": result.get("relevance_score", 0),
                "tags": result.get("tags", []),
                "search_type": "tag",
                "matched_tags": [tag for tag in tags if tag in result.get("tags", [])]
            } for result in tag_results]
            
        except Exception as e:
            logger.warning(f"タグ検索エラー: {e}")
            return []
    
    async def _keyword_search(self, user_id: str, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        """キーワード検索"""
        try:
            # キーワードベースの検索
            keyword_query = " ".join(keywords)
            keyword_results = await self.vector_service.search_similar_content(
                query=keyword_query,
                user_id=user_id,
                limit=limit
            )
            
            return [{
                "id": result.get("upload_id"),
                "filename": result.get("filename"),
                "content": result.get("content", "")[:300],
                "relevance_score": result.get("relevance_score", 0),
                "tags": result.get("tags", []),
                "search_type": "keyword",
                "matched_keywords": self._find_matched_keywords(result.get("content", ""), keywords)
            } for result in keyword_results]
            
        except Exception as e:
            logger.warning(f"キーワード検索エラー: {e}")
            return []
    
    async def _unify_search_results(
        self, 
        search_results: Dict[str, List[Dict]], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """検索結果を統合"""
        unified = {}
        
        # 各検索タイプの結果をマージ
        for search_type, results in search_results.items():
            for result in results:
                file_id = result.get("id")
                if not file_id:
                    continue
                
                if file_id in unified:
                    # 既存結果と統合
                    existing = unified[file_id]
                    # 最高のスコアを採用
                    if result.get("relevance_score", 0) > existing.get("relevance_score", 0):
                        existing["relevance_score"] = result.get("relevance_score", 0)
                    # 検索タイプを追加
                    existing_types = existing.get("search_types", [])
                    if search_type not in existing_types:
                        existing_types.append(search_type)
                        existing["search_types"] = existing_types
                    # スコアブースト（複数検索でヒットしたファイルを優遇）
                    existing["relevance_score"] = existing.get("relevance_score", 0) * 1.1
                else:
                    # 新規結果
                    result["search_types"] = [search_type]
                    unified[file_id] = result
        
        return list(unified.values())
    
    async def _generate_citation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """IEEE形式の引用を生成"""
        reference_info = params.get("reference_info", {})
        citation_style = params.get("citation_style", "ieee")
        
        if not reference_info:
            raise AgentValidationError("reference_info は必須です")
        
        try:
            if citation_style.lower() == "ieee":
                citation = await self._generate_ieee_citation(reference_info)
            else:
                raise AgentValidationError(f"未サポートの引用スタイル: {citation_style}")
            
            return {
                "reference_info": reference_info,
                "citation": citation,
                "citation_style": citation_style,
                "action": "generate_citation",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"引用生成エラー: {e}")
            raise AgentExecutionError(f"引用生成に失敗しました: {e}")
    
    async def _generate_ieee_citation(self, reference_info: Dict[str, Any]) -> str:
        """IEEE形式の引用を生成"""
        try:
            filename = reference_info.get("filename", "Unknown Document")
            upload_id = reference_info.get("id", "")
            
            # ファイル名から情報を抽出
            title = self._extract_title_from_filename(filename)
            
            # OpenAI APIを使ってより詳細な引用情報を生成
            if reference_info.get("content"):
                enhanced_citation = await self._enhance_citation_with_ai(
                    filename, reference_info.get("content", ""), title
                )
                if enhanced_citation:
                    return enhanced_citation
            
            # フォールバック: 基本的なIEEE形式
            year = datetime.now().year
            citation = f'"{title}," {filename}, {year}.'
            
            return citation
            
        except Exception as e:
            logger.warning(f"IEEE引用生成エラー: {e}")
            # 最小限の引用形式
            return f'"{reference_info.get("filename", "Unknown")}"'
    
    async def _enhance_citation_with_ai(self, filename: str, content: str, title: str) -> Optional[str]:
        """AIを使って引用情報を強化"""
        try:
            prompt = f"""以下の文書から IEEE 形式の引用情報を抽出・生成してください。

ファイル名: {filename}
文書内容（抜粋）: {content[:500]}...

IEEE 形式の例:
[1] A. B. Author, "Title of paper," in Proc. Conference Name, 2023, pp. 123-130.
[2] C. D. Author and E. F. Author, "Journal article title," Journal Name, vol. 12, no. 3, pp. 45-67, Mar. 2023.

可能な限り正確なIEEE形式で引用を生成してください。情報が不足している場合は合理的な推定を行ってください。"""
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            
            result = await openai_client.generate_text(

            
                prompt=full_prompt,

            
                model="gpt-4o-mini"

            
            )

            
            enhanced_citation = result.get("content", "")
            
            # 生成された引用をクリーンアップ
            citation = enhanced_citation.strip()
            if citation.startswith('[') and ']' in citation:
                # 番号を除去
                citation = citation.split(']', 1)[1].strip()
            
            return citation
            
        except Exception as e:
            logger.warning(f"AI引用強化エラー: {e}")
            return None
    
    async def _format_bibliography(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """参考文献リストをフォーマット"""
        references = params.get("references", [])
        style = params.get("style", "ieee")
        
        if not references:
            raise AgentValidationError("references は必須です")
        
        try:
            formatted_bibliography = []
            
            for i, ref in enumerate(references, 1):
                if style.lower() == "ieee":
                    citation = await self._generate_ieee_citation(ref)
                    formatted_citation = f"[{i}] {citation}"
                else:
                    formatted_citation = f"{i}. {ref.get('filename', 'Unknown')}"
                
                formatted_bibliography.append(formatted_citation)
            
            bibliography_text = "\n".join(formatted_bibliography)
            
            return {
                "bibliography": formatted_bibliography,
                "bibliography_text": bibliography_text,
                "style": style,
                "reference_count": len(references),
                "action": "format_bibliography",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"参考文献フォーマットエラー: {e}")
            raise AgentExecutionError(f"参考文献フォーマットに失敗しました: {e}")
    
    async def _suggest_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツに基づく文献推奨"""
        content = params.get("content", "")
        user_id = params.get("user_id")
        section_type = params.get("section_type", "general")
        
        if not content or not user_id:
            raise AgentValidationError("content と user_id は必須です")
        
        try:
            # コンテンツからキーワードを抽出
            keywords = await self._extract_keywords_from_content(content)
            
            # キーワードベースで関連文献を検索
            search_result = await self._search_references({
                "user_id": user_id,
                "keywords": keywords[:5],  # 上位5キーワード
                "query": content[:200],  # 最初の200文字
                "limit": 5,
                "search_types": ["vector", "keyword"]
            })
            
            # 推奨理由を生成
            suggestions_with_reasons = []
            for result in search_result.get("search_results", []):
                reason = self._generate_suggestion_reason(result, keywords, section_type)
                suggestions_with_reasons.append({
                    **result,
                    "suggestion_reason": reason,
                    "confidence_score": result.get("relevance_score", 0) * 0.8
                })
            
            return {
                "suggested_references": suggestions_with_reasons,
                "extracted_keywords": keywords,
                "section_type": section_type,
                "suggestion_count": len(suggestions_with_reasons),
                "action": "suggest_references",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"文献推奨エラー: {e}")
            raise AgentExecutionError(f"文献推奨に失敗しました: {e}")
    
    async def _extract_key_points(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """文献から重要ポイントを抽出"""
        reference_content = params.get("reference_content", "")
        context = params.get("context", "")  # 論文の文脈
        
        if not reference_content:
            raise AgentValidationError("reference_content は必須です")
        
        try:
            # AIを使って重要ポイントを抽出
            extraction_prompt = f"""以下の文献から、論文執筆に役立つ重要なポイントを抽出してください：

【文献内容】
{reference_content[:1000]}...

【論文の文脈】
{context}

抽出する情報：
1. 主要な発見・結論
2. 使用された方法・手法
3. 重要な数値・データ
4. 引用に適した箇所

各ポイントを簡潔にまとめてください。"""
            
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            
            result = await openai_client.generate_text(

            
                prompt=full_prompt,

            
                model="gpt-4o-mini"

            
            )

            
            key_points = result.get("content", "")
            
            return {
                "key_points": key_points,
                "reference_content_length": len(reference_content),
                "context": context,
                "action": "extract_key_points",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"重要ポイント抽出エラー: {e}")
            raise AgentExecutionError(f"重要ポイント抽出に失敗しました: {e}")
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """ファイル名からタイトルを抽出"""
        # 拡張子を除去
        title = re.sub(r'\.[^.]+$', '', filename)
        
        # アンダースコア・ハイフンをスペースに変換
        title = re.sub(r'[_-]', ' ', title)
        
        # 数字のプレフィックスを除去 (例: "01_title" -> "title")
        title = re.sub(r'^\d+[._-]*', '', title)
        
        return title.strip()
    
    def _find_matched_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """コンテンツ内で一致するキーワードを検索"""
        matched = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched.append(keyword)
        
        return matched
    
    async def _extract_keywords_from_content(self, content: str) -> List[str]:
        """コンテンツからキーワードを抽出（簡易実装）"""
        # 簡易的なキーワード抽出
        # 実際の実装では、より高度なNLP手法を使用
        words = re.findall(r'\b[A-Za-z]{3,}\b|\b[ァ-ヶー]{2,}\b|\b[一-龯]{2,}\b', content)
        
        # 頻出単語を除外し、重要そうな単語を抽出
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'である', 'です', 'ます', 'として', 'について'}
        keywords = [word for word in set(words) if word.lower() not in stop_words and len(word) > 2]
        
        return keywords[:10]  # 上位10キーワード
    
    def _generate_suggestion_reason(self, result: Dict[str, Any], keywords: List[str], section_type: str) -> str:
        """推奨理由を生成"""
        reasons = []
        
        # 関連度スコアに基づく理由
        score = result.get("relevance_score", 0)
        if score > 0.8:
            reasons.append("高い関連性")
        elif score > 0.6:
            reasons.append("中程度の関連性")
        
        # 一致したキーワードに基づく理由
        matched_keywords = result.get("matched_keywords", [])
        if matched_keywords:
            reasons.append(f"キーワード一致: {', '.join(matched_keywords[:3])}")
        
        # セクションタイプに基づく理由
        if section_type in ["method", "methodology"]:
            if any(word in result.get("content", "").lower() for word in ["method", "approach", "technique"]):
                reasons.append("手法に関連")
        
        return "、".join(reasons) if reasons else "類似コンテンツ"
    
    async def _validate_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """参考文献の検証（基本実装）"""
        references = params.get("references", [])
        
        validation_results = []
        for ref in references:
            validation_results.append({
                "reference": ref,
                "is_valid": True,  # 簡易実装
                "issues": []
            })
        
        return {
            "validation_results": validation_results,
            "overall_valid": True,
            "action": "validate_references",
            "success": True
        }