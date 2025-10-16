"""
アウトライン管理エージェント
章・節・項のCRUD、順序管理、構造最適化を担当
"""
from typing import Any, Dict, List, Optional, Tuple
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.infrastructure.database.models import ResearchPaperModel, PaperSectionModel
from app.infrastructure.repositories.paper_repository import PaperRepository

logger = logging.getLogger(__name__)


class OutlineAgent(BaseAgent):
    """
    アウトライン管理エージェント
    
    実装パターン: Tool-based Logic Node
    責務: 章・節・項の構造管理、階層パス管理
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(
            name="OutlineAgent",
            description="論文の章・節・項構造を管理するエージェント",
            max_retries=2,
            timeout=15
        )
        self.session = session
        self.repository = PaperRepository(session)
    
    def _get_supported_task_types(self) -> List[str]:
        return [
            "create_section",
            "update_section",
            "delete_section",
            "move_section",
            "split_section",
            "merge_sections",
            "get_outline",
            "validate_structure"
        ]
    
    async def _execute_core(self, task: AgentTask) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters
        
        if task_type == "create_section":
            return await self._create_section(parameters)
        elif task_type == "update_section":
            return await self._update_section(parameters)
        elif task_type == "delete_section":
            return await self._delete_section(parameters)
        elif task_type == "move_section":
            return await self._move_section(parameters)
        elif task_type == "split_section":
            return await self._split_section(parameters)
        elif task_type == "merge_sections":
            return await self._merge_sections(parameters)
        elif task_type == "get_outline":
            return await self._get_outline(parameters)
        elif task_type == "validate_structure":
            return await self._validate_structure(parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")
    
    def _normalize_sections_param(self, sections_raw: Any) -> List[Dict[str, Any]]:
        """
        様々な形式のsectionsパラメータを正規化

        入力形式例:
        - ["Introduction", "Methods", "Results"]  # 文字列リスト
        - [{"name": "Introduction"}, {"title": "Methods"}]  # 辞書リスト(キー混在)
        - [{"title": "Introduction", "key_points": [...]}]  # 完全な辞書

        出力形式:
        - [{"title": "Introduction"}, {"title": "Methods"}, ...]
        """
        if not sections_raw:
            return []

        if not isinstance(sections_raw, list):
            sections_raw = [sections_raw]

        normalized = []
        for item in sections_raw:
            if isinstance(item, str):
                # 文字列の場合はtitleとして扱う
                normalized.append({"title": item})
            elif isinstance(item, dict):
                # 辞書の場合、titleまたはnameまたはsection_titleを探す
                title = (item.get("title") or
                        item.get("name") or
                        item.get("section_title") or
                        str(item))
                normalized.append({"title": title, **item})
            else:
                # その他の型は文字列化
                normalized.append({"title": str(item)})

        return normalized

    async def _create_section(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        セクションを作成（AAIDC準拠 - Clear Boundaries Pattern）
        責務: セクションのDB作成のみ。コンテンツ生成はWriterAgentが担当。

        複数セクション対応: params.get("sections")がリストの場合、すべて作成
        """
        paper_id = params.get("paper_id")
        user_id = params.get("user_id")

        # 複数セクションの一括作成をサポート
        sections_raw = params.get("sections")
        if sections_raw and isinstance(sections_raw, list) and len(sections_raw) > 0:
            # パラメータ正規化
            sections = self._normalize_sections_param(sections_raw)
            return await self._create_multiple_sections(paper_id, user_id, sections)

        # 単一セクション作成（後方互換性）
        section_title = params.get("section_title") or params.get("title")

        if not all([paper_id, section_title, user_id]):
            raise AgentValidationError("paper_id, section_title, user_id は必須です")

        try:
            logger.info(f"[OutlineAgent] セクション作成開始: '{section_title}' (paper: {paper_id})")

            # 次のposition番号を取得
            next_position = await self.repository.get_next_position(paper_id)
            section_number = str(next_position)

            # セクション作成（初期状態は空コンテンツ）
            section = await self.repository.create_section(
                paper_id=paper_id,
                position=next_position,
                section_number=section_number,
                title=section_title,
                user_id=user_id,
                content="",  # 初期は空
                summary=""  # 初期は空
            )

            logger.info(f"[OutlineAgent] セクション作成完了: ID={section.id}, position={next_position}")

            # Clear Boundaries Pattern: OutlineAgentはセクション構造のみ返す
            return {
                "section": {
                    "id": section.id,
                    "position": section.position,
                    "section_number": section.section_number,
                    "title": section.title,
                    "status": section.status,
                    "created_at": section.created_at.isoformat()
                },
                "action": "create_section",
                "success": True,
                "message": f"セクション「{section_title}」の構造を作成しました"
            }
            
        except Exception as e:
            logger.error(f"[OutlineAgent] セクション作成エラー: {e}")
            raise AgentExecutionError(f"セクション作成に失敗しました: {e}")
    
    async def _update_section(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクションを更新"""
        section_id = params.get("section_id")
        title = params.get("title")
        content = params.get("content")
        
        if not section_id:
            raise AgentValidationError("section_id は必須です")
        
        try:
            section = await self.repository.get_section_by_id(section_id)
            if not section:
                raise AgentValidationError(f"セクション {section_id} が見つかりません")
            
            # 更新データを準備
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if content is not None:
                update_data["content"] = content
                update_data["word_count"] = len(content.split())
            
            # セクション更新
            updated_section = await self.repository.update_section(section_id, update_data)
            
            return {
                "section": {
                    "id": updated_section.id,
                    "title": updated_section.title,
                    "content": updated_section.content,
                    "word_count": updated_section.word_count,
                    "status": updated_section.status,
                    "updated_at": updated_section.updated_at.isoformat()
                },
                "action": "update_section",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"セクション更新エラー: {e}")
            raise AgentExecutionError(f"セクション更新に失敗しました: {e}")
    
    async def _create_multiple_sections(
        self,
        paper_id: str,
        user_id: str,
        sections_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        複数のセクションを一度に作成

        Args:
            paper_id: 論文ID
            user_id: ユーザーID
            sections_data: セクション情報のリスト [{"title": "...", "key_points": [...]}, ...]

        Returns:
            作成されたセクション情報
        """
        if not paper_id or not user_id:
            raise AgentValidationError("paper_id, user_id は必須です")

        created_sections = []
        errors = []

        try:
            logger.info(f"[OutlineAgent] 複数セクション作成開始: {len(sections_data)}個 (paper: {paper_id})")

            # 既存セクション数を取得
            existing_sections = await self.repository.get_sections_by_paper(paper_id)
            next_position = len(existing_sections) + 1

            for idx, section_data in enumerate(sections_data):
                section_title = section_data.get("title")
                if not section_title:
                    errors.append(f"セクション{idx + 1}: タイトルが未指定")
                    continue

                try:
                    # positionベースでセクション作成
                    position = next_position + idx
                    section_number = str(position)

                    section = await self.repository.create_section(
                        paper_id=paper_id,
                        position=position,
                        section_number=section_number,
                        title=section_title,
                        user_id=user_id,
                        content="",  # 初期は空
                        summary=""  # 初期は空
                    )

                    created_sections.append({
                        "id": section.id,
                        "position": section.position,
                        "section_number": section.section_number,
                        "title": section.title,
                        "status": section.status,
                    })

                    logger.info(f"[OutlineAgent] セクション作成完了: {idx + 1}/{len(sections_data)} - '{section_title}'")

                except Exception as e:
                    logger.error(f"[OutlineAgent] セクション'{section_title}'作成エラー: {e}")
                    errors.append(f"{section_title}: {str(e)}")

            logger.info(f"[OutlineAgent] 複数セクション作成完了: 成功{len(created_sections)}個, 失敗{len(errors)}個")

            return {
                "created_sections": created_sections,
                "total_created": len(created_sections),
                "errors": errors,
                "action": "create_multiple_sections",
                "success": len(created_sections) > 0,
                "message": f"{len(created_sections)}個のセクションを作成しました"
            }

        except Exception as e:
            logger.error(f"[OutlineAgent] 複数セクション作成エラー: {e}")
            raise AgentExecutionError(f"複数セクション作成に失敗しました: {e}")

    async def _delete_section(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクションを論理削除"""
        section_id = params.get("section_id")
        
        if not section_id:
            raise AgentValidationError("section_id は必須です")
        
        try:
            section = await self.repository.get_section_by_id(section_id)
            if not section:
                raise AgentValidationError(f"セクション {section_id} が見つかりません")
            
            # 子セクションもチェック
            children = await self.repository.get_child_sections(section_id)
            child_count = len(children) if children else 0
            
            # 論理削除実行
            await self.repository.delete_section(section_id)
            
            return {
                "deleted_section": {
                    "id": section.id,
                    "title": section.title,
                    "hierarchy_path": section.hierarchy_path
                },
                "deleted_children_count": child_count,
                "action": "delete_section",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"セクション削除エラー: {e}")
            raise AgentExecutionError(f"セクション削除に失敗しました: {e}")
    
    async def _get_outline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """論文のアウトラインを取得"""
        paper_id = params.get("paper_id")
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        
        try:
            sections = await self.repository.get_sections_by_paper(paper_id)
            
            outline = []
            for section in sections:
                outline.append({
                    "id": section.id,
                    "hierarchy_path": section.hierarchy_path,
                    "section_number": section.section_number,
                    "title": section.title,
                    "word_count": section.word_count,
                    "status": section.status,
                    "summary": section.summary[:100] + "..." if len(section.summary) > 100 else section.summary,
                    "updated_at": section.updated_at.isoformat()
                })
            
            return {
                "outline": outline,
                "total_sections": len(outline),
                "action": "get_outline",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"アウトライン取得エラー: {e}")
            raise AgentExecutionError(f"アウトライン取得に失敗しました: {e}")
    
    async def _validate_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """論文構造を検証"""
        paper_id = params.get("paper_id")
        
        if not paper_id:
            raise AgentValidationError("paper_id は必須です")
        
        try:
            sections = await self.repository.get_sections_by_paper(paper_id)
            issues = []
            
            # 階層パスの妥当性チェック
            hierarchy_paths = [s.hierarchy_path for s in sections]
            hierarchy_paths.sort()
            
            for i, path in enumerate(hierarchy_paths):
                # 階層パス形式チェック
                if not re.match(r'^(\d{3}\.)*\d{3}$', path):
                    issues.append({
                        "type": "invalid_hierarchy_path",
                        "message": f"不正な階層パス: {path}",
                        "section_id": sections[i].id
                    })
                
                # 親子関係チェック
                parts = path.split('.')
                if len(parts) > 1:
                    parent_path = '.'.join(parts[:-1])
                    if parent_path not in hierarchy_paths:
                        issues.append({
                            "type": "missing_parent",
                            "message": f"親セクションが存在しません: {parent_path}",
                            "section_id": sections[i].id
                        })
            
            # 空のセクションチェック
            for section in sections:
                if not section.content.strip() and section.status != "draft":
                    issues.append({
                        "type": "empty_content",
                        "message": f"内容が空のセクション: {section.title}",
                        "section_id": section.id
                    })
            
            return {
                "issues": issues,
                "is_valid": len(issues) == 0,
                "total_sections": len(sections),
                "action": "validate_structure",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"構造検証エラー: {e}")
            raise AgentExecutionError(f"構造検証に失敗しました: {e}")
    
    async def _generate_hierarchy_path(
        self, 
        paper_id: str, 
        parent_path: str = "", 
        position: int = -1
    ) -> str:
        """階層パスを生成"""
        try:
            if parent_path:
                # 子セクションの場合
                siblings = await self.repository.get_child_sections_by_path(paper_id, parent_path)
                if position == -1 or position >= len(siblings):
                    # 末尾に追加
                    next_number = len(siblings) + 1
                else:
                    # 指定位置に挿入（既存セクションの階層パスを更新する必要あり）
                    next_number = position + 1
                
                return f"{parent_path}.{next_number:03d}"
            else:
                # ルートレベルセクション
                root_sections = await self.repository.get_root_sections(paper_id)
                if position == -1 or position >= len(root_sections):
                    next_number = len(root_sections) + 1
                else:
                    next_number = position + 1
                
                return f"{next_number:03d}"
                
        except Exception as e:
            logger.error(f"階層パス生成エラー: {e}")
            raise AgentExecutionError(f"階層パス生成に失敗しました: {e}")
    
    def _hierarchy_path_to_number(self, hierarchy_path: str) -> str:
        """階層パスを表示用番号に変換 (例: "001.002.003" -> "1.2.3")"""
        parts = hierarchy_path.split('.')
        return '.'.join(str(int(part)) for part in parts)
    
    # 以下、他のメソッドは必要に応じて実装
    async def _move_section(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクション移動（今回は基本実装をスキップ）"""
        raise AgentExecutionError("move_section は未実装です")
    
    async def _split_section(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクション分割（今回は基本実装をスキップ）"""
        raise AgentExecutionError("split_section は未実装です")
    
    async def _merge_sections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクション統合（今回は基本実装をスキップ）"""
        raise AgentExecutionError("merge_sections は未実装です")