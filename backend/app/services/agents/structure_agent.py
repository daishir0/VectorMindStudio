"""
構造整理エージェント（StructureAgent）
ユーザーの意図を理解して論文構造を柔軟に整理
"""
from typing import Any, Dict, List, Optional
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from .base_agent import BaseAgent, AgentTask, AgentValidationError, AgentExecutionError
from app.infrastructure.database.models import PaperSectionModel
from app.infrastructure.repositories.paper_repository import PaperRepository
from app.infrastructure.external.openai_client import openai_client

logger = logging.getLogger(__name__)


class StructureAgent(BaseAgent):
    """
    構造整理エージェント

    責務:
    - ユーザーの意図を理解した構造最適化
    - 学術論文の標準形式（IMRAD等）への変換
    - セクションの論理的な並び替え
    - 構造の分析と改善提案
    """

    def __init__(self, session: AsyncSession):
        super().__init__(
            name="StructureAgent",
            description="論文構造を分析・最適化するエージェント",
            max_retries=2,
            timeout=30
        )
        self.session = session
        self.repository = PaperRepository(session)

        # 標準的な論文構造テンプレート
        self.structure_templates = {
            "imrad": {
                "name": "IMRAD形式",
                "description": "学術論文の標準形式（Introduction, Methods, Results, And Discussion）",
                "sections": [
                    {"title": "Abstract", "description": "研究の要約"},
                    {"title": "Introduction", "description": "研究背景と目的"},
                    {"title": "Methods", "description": "研究方法・手法"},
                    {"title": "Results", "description": "研究結果"},
                    {"title": "Discussion", "description": "考察・議論"},
                    {"title": "Conclusion", "description": "結論"},
                    {"title": "References", "description": "参考文献"}
                ]
            },
            "chronological": {
                "name": "時系列形式",
                "description": "時間軸に沿った構成",
                "sections": [
                    {"title": "背景", "description": "歴史的背景"},
                    {"title": "経緯", "description": "時系列の展開"},
                    {"title": "現状", "description": "現在の状況"},
                    {"title": "展望", "description": "将来の展望"}
                ]
            },
            "thematic": {
                "name": "主題別形式",
                "description": "テーマごとの構成",
                "sections": []  # 動的に生成
            },
            "problem_solution": {
                "name": "問題解決形式",
                "description": "問題定義→解決策の構成",
                "sections": [
                    {"title": "問題提起", "description": "解決すべき問題"},
                    {"title": "分析", "description": "問題の分析"},
                    {"title": "解決策", "description": "提案する解決策"},
                    {"title": "実装", "description": "実装方法"},
                    {"title": "評価", "description": "結果の評価"}
                ]
            },
            "kishoutenketsu": {
                "name": "起承転結形式",
                "description": "日本的な4部構成（起承転結）",
                "sections": [
                    {"title": "起（序論）", "description": "話の始まり、状況設定"},
                    {"title": "承（展開）", "description": "起の内容を受けて展開"},
                    {"title": "転（転換）", "description": "視点の転換、新展開"},
                    {"title": "結（結論）", "description": "まとめ、結論"}
                ]
            }
        }

    def _get_supported_task_types(self) -> List[str]:
        return [
            "analyze_structure",       # 現在の構造を分析
            "suggest_restructure",     # 構造改善を提案
            "apply_template",          # テンプレート適用
            "reorder_sections",        # セクション並び替え
            "detect_format",           # フォーマット検出
            "split_section",           # セクション分割
            "merge_sections",          # セクション統合
            "restructure_with_content" # 包括的再構成
        ]

    async def _execute_core(self, task: AgentTask) -> Any:
        """コア実行ロジック"""
        task_type = task.task_type
        parameters = task.parameters

        if task_type == "analyze_structure":
            return await self._analyze_structure(parameters)
        elif task_type == "suggest_restructure":
            return await self._suggest_restructure(parameters)
        elif task_type == "apply_template":
            return await self._apply_template(parameters)
        elif task_type == "reorder_sections":
            return await self._reorder_sections(parameters)
        elif task_type == "detect_format":
            return await self._detect_format(parameters)
        elif task_type == "split_section":
            return await self._split_section(parameters)
        elif task_type == "merge_sections":
            return await self._merge_sections(parameters)
        elif task_type == "restructure_with_content":
            return await self._restructure_with_content(parameters)
        else:
            raise AgentValidationError(f"未サポートのタスクタイプ: {task_type}")

    async def _analyze_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """現在の論文構造を分析"""
        paper_id = params.get("paper_id")

        if not paper_id:
            raise AgentValidationError("paper_id は必須です")

        try:
            logger.info(f"[StructureAgent] 構造分析開始: paper={paper_id}")

            # 既存セクション取得
            sections = await self.repository.get_sections_by_paper(paper_id)

            if not sections:
                return {
                    "analysis": {
                        "total_sections": 0,
                        "structure_type": "empty",
                        "issues": ["セクションが存在しません"]
                    },
                    "action": "analyze_structure",
                    "success": True
                }

            # セクション情報を整理
            section_info = []
            for section in sections:
                section_info.append({
                    "id": section.id,
                    "title": section.title,
                    "section_number": section.section_number,
                    "word_count": section.word_count or 0,
                    "summary": section.summary[:100] if section.summary else ""
                })

            # LLMで構造を分析
            analysis_result = await self._llm_analyze_structure(section_info)

            logger.info(f"[StructureAgent] 構造分析完了: {analysis_result.get('structure_type', 'unknown')}")

            return {
                "analysis": analysis_result,
                "sections": section_info,
                "action": "analyze_structure",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] 構造分析エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"構造分析に失敗しました: {e}")

    async def _suggest_restructure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """構造改善を提案"""
        paper_id = params.get("paper_id")
        user_requirements = params.get("requirements", "")
        target_format = params.get("target_format")  # imrad, chronological, thematic等

        if not paper_id:
            raise AgentValidationError("paper_id は必須です")

        try:
            logger.info(f"[StructureAgent] 構造改善提案開始: paper={paper_id}, format={target_format}")

            # 現在の構造を分析
            current_analysis = await self._analyze_structure({"paper_id": paper_id})
            sections = current_analysis.get("sections", [])

            if not sections:
                return {
                    "suggestion": {
                        "message": "セクションがないため、新規作成が必要です",
                        "actions": []
                    },
                    "action": "suggest_restructure",
                    "success": True
                }

            # LLMで改善提案を生成
            suggestion = await self._llm_suggest_restructure(
                sections=sections,
                current_structure=current_analysis.get("analysis", {}),
                user_requirements=user_requirements,
                target_format=target_format
            )

            logger.info(f"[StructureAgent] 構造改善提案完了: {len(suggestion.get('actions', []))}個のアクション")

            return {
                "suggestion": suggestion,
                "current_structure": current_analysis.get("analysis", {}),
                "action": "suggest_restructure",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] 構造改善提案エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"構造改善提案に失敗しました: {e}")

    async def _apply_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """テンプレートを適用"""
        paper_id = params.get("paper_id")
        template_name = params.get("template_name", "imrad")

        if not paper_id:
            raise AgentValidationError("paper_id は必須です")

        template = self.structure_templates.get(template_name)
        if not template:
            raise AgentValidationError(f"テンプレート '{template_name}' は存在しません")

        try:
            logger.info(f"[StructureAgent] テンプレート適用開始: paper={paper_id}, template={template_name}")

            # 既存セクション取得
            sections = await self.repository.get_sections_by_paper(paper_id)

            # テンプレートのセクション定義を取得
            template_sections = template.get("sections", [])

            # マッピング戦略をLLMで決定
            mapping = await self._llm_map_to_template(sections, template_sections)

            # 実際の並び替え・統合を実行
            reorder_result = await self._execute_restructure(paper_id, mapping)

            logger.info(f"[StructureAgent] テンプレート適用完了")

            return {
                "template": template,
                "mapping": mapping,
                "reorder_result": reorder_result,
                "action": "apply_template",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] テンプレート適用エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"テンプレート適用に失敗しました: {e}")

    async def _reorder_sections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクションを並び替え"""
        paper_id = params.get("paper_id")
        new_order = params.get("new_order", [])  # [{section_id, new_position}]

        if not paper_id:
            raise AgentValidationError("paper_id は必須です")

        try:
            logger.info(f"[StructureAgent] セクション並び替え開始: paper={paper_id}")

            # 並び替えを実行
            updated_sections = []
            for item in new_order:
                section_id = item.get("section_id")
                new_position = item.get("new_position")

                # 階層パスを再計算
                new_hierarchy_path = f"{new_position:03d}"
                new_section_number = str(new_position)

                # セクション更新
                updated_section = await self.repository.update_section(
                    section_id,
                    {
                        "hierarchy_path": new_hierarchy_path,
                        "section_number": new_section_number
                    }
                )
                updated_sections.append(updated_section)

            logger.info(f"[StructureAgent] セクション並び替え完了: {len(updated_sections)}個更新")

            return {
                "updated_sections": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "section_number": s.section_number,
                        "hierarchy_path": s.hierarchy_path
                    }
                    for s in updated_sections
                ],
                "action": "reorder_sections",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] セクション並び替えエラー: {e}", exc_info=True)
            raise AgentExecutionError(f"セクション並び替えに失敗しました: {e}")

    async def _detect_format(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """現在のフォーマットを検出"""
        paper_id = params.get("paper_id")

        if not paper_id:
            raise AgentValidationError("paper_id は必須です")

        try:
            sections = await self.repository.get_sections_by_paper(paper_id)

            if not sections:
                return {
                    "detected_format": "empty",
                    "confidence": 1.0,
                    "action": "detect_format",
                    "success": True
                }

            # セクションタイトルリスト
            titles = [s.title.lower() for s in sections]

            # パターンマッチングでフォーマット検出
            format_scores = {}

            # IMRAD形式チェック
            imrad_keywords = ["abstract", "introduction", "method", "result", "discussion", "conclusion"]
            imrad_score = sum(1 for keyword in imrad_keywords if any(keyword in title for title in titles))
            format_scores["imrad"] = imrad_score / len(imrad_keywords)

            # 時系列形式チェック
            chrono_keywords = ["背景", "経緯", "歴史", "現状", "展望", "将来"]
            chrono_score = sum(1 for keyword in chrono_keywords if any(keyword in title for title in titles))
            format_scores["chronological"] = chrono_score / len(chrono_keywords)

            # 問題解決形式チェック
            problem_keywords = ["問題", "課題", "分析", "解決", "提案", "評価"]
            problem_score = sum(1 for keyword in problem_keywords if any(keyword in title for title in titles))
            format_scores["problem_solution"] = problem_score / len(problem_keywords)

            # 最高スコアのフォーマットを選択
            detected_format = max(format_scores, key=format_scores.get)
            confidence = format_scores[detected_format]

            if confidence < 0.3:
                detected_format = "custom"
                confidence = 0.5

            return {
                "detected_format": detected_format,
                "confidence": confidence,
                "format_scores": format_scores,
                "action": "detect_format",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] フォーマット検出エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"フォーマット検出に失敗しました: {e}")

    # ========== LLMヘルパーメソッド ==========

    async def _llm_analyze_structure(self, sections: List[Dict]) -> Dict[str, Any]:
        """LLMで構造を分析"""
        system_prompt = """あなたは学術論文の構造分析の専門家です。
与えられたセクション情報から、論文の構造を分析してください。

分析項目:
1. structure_type: 構造タイプ（imrad, chronological, thematic, problem_solution, custom等）
2. coherence_score: 構造の一貫性（0.0-1.0）
3. issues: 問題点のリスト
4. strengths: 強みのリスト
5. suggestions: 改善提案のリスト

JSON形式で返してください。"""

        user_prompt = f"""以下のセクション情報を分析してください:

{json.dumps(sections, ensure_ascii=False, indent=2)}

構造を分析し、JSON形式で返してください。"""

        try:
            result = await openai_client.generate_text(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                model="gpt-4o-mini"
            )

            response_text = result.get("content", "").strip()

            # JSON抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            analysis = json.loads(json_text)
            return analysis

        except Exception as e:
            logger.warning(f"LLM構造分析失敗、フォールバック: {e}")
            return {
                "structure_type": "unknown",
                "coherence_score": 0.5,
                "issues": ["構造分析に失敗しました"],
                "strengths": [],
                "suggestions": []
            }

    async def _llm_suggest_restructure(
        self,
        sections: List[Dict],
        current_structure: Dict,
        user_requirements: str,
        target_format: Optional[str]
    ) -> Dict[str, Any]:
        """LLMで構造改善を提案"""
        system_prompt = """あなたは学術論文の構造最適化の専門家です。
現在のセクション情報とユーザーの要求から、最適な構造改善案を提案してください。

提案形式:
{
    "target_format": "提案するフォーマット名",
    "rationale": "提案理由",
    "actions": [
        {
            "action_type": "reorder|merge|split|rename",
            "section_id": "対象セクションID",
            "details": "詳細"
        }
    ],
    "expected_benefits": ["期待される効果のリスト"]
}"""

        template_info = ""
        if target_format and target_format in self.structure_templates:
            template_info = f"\n\n目標フォーマット: {self.structure_templates[target_format]['name']}\n{self.structure_templates[target_format]['description']}"

        user_prompt = f"""現在のセクション:
{json.dumps(sections, ensure_ascii=False, indent=2)}

現在の構造分析:
{json.dumps(current_structure, ensure_ascii=False, indent=2)}

ユーザーの要求: {user_requirements}{template_info}

最適な構造改善案をJSON形式で提案してください。"""

        try:
            result = await openai_client.generate_text(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                model="gpt-4o-mini"
            )

            response_text = result.get("content", "").strip()

            # JSON抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            suggestion = json.loads(json_text)
            return suggestion

        except Exception as e:
            logger.warning(f"LLM構造提案失敗、フォールバック: {e}")
            return {
                "target_format": target_format or "custom",
                "rationale": "構造提案の生成に失敗しました",
                "actions": [],
                "expected_benefits": []
            }

    async def _llm_map_to_template(
        self,
        sections: List[PaperSectionModel],
        template_sections: List[Dict]
    ) -> Dict[str, Any]:
        """既存セクションをテンプレートにマッピング"""
        section_info = [{"id": s.id, "title": s.title, "summary": s.summary[:100] if s.summary else ""} for s in sections]

        system_prompt = """既存のセクションを新しいテンプレート構造にマッピングしてください。

マッピング形式:
{
    "mappings": [
        {
            "template_section_title": "テンプレートのセクションタイトル",
            "source_section_ids": ["マッピングする既存セクションID"],
            "action": "map|merge|create"
        }
    ]
}"""

        user_prompt = f"""既存セクション:
{json.dumps(section_info, ensure_ascii=False, indent=2)}

テンプレートセクション:
{json.dumps(template_sections, ensure_ascii=False, indent=2)}

マッピングをJSON形式で返してください。"""

        try:
            result = await openai_client.generate_text(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                model="gpt-4o-mini"
            )

            response_text = result.get("content", "").strip()

            # JSON抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            mapping = json.loads(json_text)
            return mapping

        except Exception as e:
            logger.warning(f"LLMマッピング失敗、フォールバック: {e}")
            return {"mappings": []}

    async def _execute_restructure(self, paper_id: str, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """マッピングに基づいて構造変更を実行"""
        try:
            mappings = mapping.get("mappings", [])
            executed_actions = []

            for idx, map_item in enumerate(mappings):
                template_title = map_item.get("template_section_title")
                source_ids = map_item.get("source_section_ids", [])
                action = map_item.get("action", "map")

                if action == "map" and len(source_ids) == 1:
                    # 単純マッピング: タイトル変更 + 位置変更
                    section_id = source_ids[0]
                    new_position = idx + 1

                    await self.repository.update_section(
                        section_id,
                        {
                            "title": template_title,
                            "section_number": str(new_position),
                            "hierarchy_path": f"{new_position:03d}"
                        }
                    )
                    executed_actions.append({"action": "mapped", "section_id": section_id, "new_title": template_title})

                elif action == "merge" and len(source_ids) > 1:
                    # 統合: 最初のセクションに統合し、他は削除
                    # 今回は簡略化のため、ログのみ
                    logger.info(f"統合が必要: {source_ids} -> {template_title}")
                    executed_actions.append({"action": "merge_needed", "source_ids": source_ids, "target_title": template_title})

                elif action == "create":
                    # 新規作成が必要
                    logger.info(f"新規作成が必要: {template_title}")
                    executed_actions.append({"action": "create_needed", "title": template_title})

            return {
                "executed_actions": executed_actions,
                "total_actions": len(executed_actions)
            }

        except Exception as e:
            logger.error(f"構造変更実行エラー: {e}")
            raise AgentExecutionError(f"構造変更実行に失敗しました: {e}")

    # ========== 新機能: セクション分割・統合・包括的再構成 ==========

    async def _split_section(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """セクションを分割"""
        paper_id = params.get("paper_id")
        section_id = params.get("section_id")
        split_count = params.get("split_count", 4)
        split_strategy = params.get("strategy", "auto")
        new_titles = params.get("new_titles", [])

        if not paper_id or not section_id:
            raise AgentValidationError("paper_id と section_id は必須です")

        try:
            logger.info(f"[StructureAgent] セクション分割開始: section={section_id}, count={split_count}")

            # 既存セクション取得
            section = await self.repository.get_section_by_id(section_id)
            if not section:
                raise AgentExecutionError(f"セクション {section_id} が見つかりません")

            # LLMで分割ポイントと各部分のタイトルを決定
            split_plan = await self._llm_plan_split(
                content=section.content,
                split_count=split_count,
                strategy=split_strategy,
                suggested_titles=new_titles
            )

            # 実際に分割を実行
            new_sections = await self._execute_split(
                paper_id=paper_id,
                original_section=section,
                split_plan=split_plan
            )

            logger.info(f"[StructureAgent] セクション分割完了: {len(new_sections)}個に分割")

            return {
                "original_section_id": section_id,
                "new_sections": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "word_count": s.word_count or 0
                    }
                    for s in new_sections
                ],
                "split_count": len(new_sections),
                "action": "split_section",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] セクション分割エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"セクション分割に失敗しました: {e}")

    async def _merge_sections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """複数セクションを統合"""
        paper_id = params.get("paper_id")
        section_ids = params.get("section_ids", [])
        new_title = params.get("new_title", "統合セクション")

        if not paper_id or len(section_ids) < 2:
            raise AgentValidationError("paper_id と 2個以上の section_ids は必須です")

        try:
            logger.info(f"[StructureAgent] セクション統合開始: {len(section_ids)}個を統合")

            # 既存セクション取得
            sections = []
            for sid in section_ids:
                section = await self.repository.get_section_by_id(sid)
                if section:
                    sections.append(section)

            if not sections:
                raise AgentExecutionError("統合対象のセクションが見つかりません")

            # コンテンツを結合
            merged_content = "\n\n".join([s.content for s in sections if s.content])

            # 最初のセクションを更新
            first_section = sections[0]
            updated_section = await self.repository.update_section(
                first_section.id,
                {
                    "title": new_title,
                    "content": merged_content,
                    "word_count": len(merged_content.split())
                }
            )

            # 残りのセクションを削除
            deleted_ids = []
            for section in sections[1:]:
                await self.repository.delete_section(section.id)
                deleted_ids.append(section.id)

            logger.info(f"[StructureAgent] セクション統合完了: {len(deleted_ids)}個削除")

            return {
                "merged_section": {
                    "id": updated_section.id,
                    "title": updated_section.title,
                    "word_count": updated_section.word_count or 0
                },
                "deleted_section_ids": deleted_ids,
                "action": "merge_sections",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] セクション統合エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"セクション統合に失敗しました: {e}")

    async def _restructure_with_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """コンテンツを含めた包括的再構成"""
        paper_id = params.get("paper_id")
        target_format = params.get("target_format")
        user_requirements = params.get("requirements", "")

        if not paper_id:
            raise AgentValidationError("paper_id は必須です")

        try:
            logger.info(f"[StructureAgent] 包括的再構成開始: paper={paper_id}, format={target_format}")

            # ステップ1: 現在の構造分析
            current_analysis = await self._analyze_structure({"paper_id": paper_id})
            sections = current_analysis.get("sections", [])

            if not sections:
                return {
                    "message": "セクションが存在しないため、再構成できません",
                    "action": "restructure_with_content",
                    "success": True
                }

            # ステップ2: 再構成計画を生成
            restructure_plan = await self._llm_plan_restructure(
                sections=sections,
                target_format=target_format,
                user_requirements=user_requirements
            )

            # ステップ3: 計画を実行
            execution_results = []

            for operation in restructure_plan.get("operations", []):
                op_type = operation.get("type", "")

                if op_type == "split":
                    result = await self._split_section({
                        "paper_id": paper_id,
                        "section_id": operation["section_id"],
                        "split_count": operation.get("split_into", 4),
                        "new_titles": operation.get("new_titles", [])
                    })
                    execution_results.append({"type": "split", "result": result})

                elif op_type == "merge":
                    result = await self._merge_sections({
                        "paper_id": paper_id,
                        "section_ids": operation["section_ids"],
                        "new_title": operation.get("new_title", "統合セクション")
                    })
                    execution_results.append({"type": "merge", "result": result})

                elif op_type == "rename":
                    section_id = operation.get("section_id")
                    new_title = operation.get("new_title", "")
                    await self.repository.update_section(
                        section_id,
                        {"title": new_title}
                    )
                    execution_results.append({"type": "rename", "section_id": section_id, "new_title": new_title})

                elif op_type == "reorder":
                    result = await self._reorder_sections({
                        "paper_id": paper_id,
                        "new_order": operation.get("new_order", [])
                    })
                    execution_results.append({"type": "reorder", "result": result})

            logger.info(f"[StructureAgent] 包括的再構成完了: {len(execution_results)}個の操作を実行")

            return {
                "restructure_plan": restructure_plan,
                "execution_results": execution_results,
                "target_format": target_format,
                "operations_count": len(execution_results),
                "action": "restructure_with_content",
                "success": True
            }

        except Exception as e:
            logger.error(f"[StructureAgent] 包括的再構成エラー: {e}", exc_info=True)
            raise AgentExecutionError(f"包括的再構成に失敗しました: {e}")

    # ========== 新しいLLMヘルパーメソッド ==========

    async def _llm_plan_split(
        self,
        content: str,
        split_count: int,
        strategy: str,
        suggested_titles: List[str] = None
    ) -> Dict[str, Any]:
        """LLMでセクション分割計画を生成"""

        system_prompt = f"""あなたは論文構成の専門家です。
与えられたコンテンツを{split_count}個の論理的な部分に分割してください。

分割戦略: {strategy}
- auto: コンテンツの論理構造に基づいて自動分割
- logical: トピックやテーマの変化点で分割
- equal: ほぼ均等に分割

以下のJSON形式で返してください:
{{
    "splits": [
        {{
            "title": "新しいセクションタイトル",
            "content_start": 開始位置（文字数）,
            "content_end": 終了位置（文字数）,
            "rationale": "このように分割した理由"
        }}
    ]
}}"""

        user_prompt = f"""以下のコンテンツを{split_count}個に分割してください:

{content[:3000]}...

（全文字数: {len(content)}文字）"""

        if suggested_titles:
            user_prompt += f"\n\n提案されたタイトル: {', '.join(suggested_titles)}"

        user_prompt += "\n\n分割計画をJSON形式で返してください。"

        try:
            result = await openai_client.generate_text(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                model="gpt-4o"
            )

            response_text = result.get("content", "").strip()

            # JSON抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            split_plan = json.loads(json_text)
            return split_plan

        except Exception as e:
            logger.warning(f"LLM分割計画失敗、均等分割フォールバック: {e}")
            # フォールバック: 均等分割
            chunk_size = len(content) // split_count
            splits = []
            for i in range(split_count):
                splits.append({
                    "title": suggested_titles[i] if suggested_titles and i < len(suggested_titles) else f"第{i+1}部",
                    "content_start": i * chunk_size,
                    "content_end": (i + 1) * chunk_size if i < split_count - 1 else len(content),
                    "rationale": "均等分割"
                })
            return {"splits": splits}

    async def _llm_plan_restructure(
        self,
        sections: List[Dict],
        target_format: str,
        user_requirements: str
    ) -> Dict[str, Any]:
        """LLMで包括的な再構成計画を生成"""

        template = self.structure_templates.get(target_format, {})

        system_prompt = f"""あなたは論文構成の専門家です。
現在のセクション構成を分析し、目標フォーマット「{template.get('name', target_format)}」に
変換するための詳細な計画を立ててください。

利用可能な操作:
1. split: セクションを複数に分割
2. merge: 複数セクションを統合
3. rename: セクションタイトルを変更
4. reorder: セクションの順序を変更

JSON形式で操作のリストを返してください:
{{
    "operations": [
        {{
            "type": "split",
            "section_id": "対象セクションID",
            "split_into": 分割数,
            "new_titles": ["新しいタイトル1", "新しいタイトル2"]
        }},
        {{
            "type": "merge",
            "section_ids": ["統合するセクションID"],
            "new_title": "統合後のタイトル"
        }},
        {{
            "type": "rename",
            "section_id": "対象セクションID",
            "new_title": "新しいタイトル"
        }},
        {{
            "type": "reorder",
            "new_order": [{{"section_id": "ID", "new_position": 1}}]
        }}
    ],
    "rationale": "この計画の理由"
}}"""

        user_prompt = f"""現在のセクション:
{json.dumps(sections, ensure_ascii=False, indent=2)}

目標フォーマット: {template.get('name')}
{template.get('description')}

目標セクション構成:
{json.dumps(template.get('sections', []), ensure_ascii=False, indent=2)}

ユーザーの要求: {user_requirements}

再構成計画をJSON形式で返してください。"""

        try:
            result = await openai_client.generate_text(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                model="gpt-4o"
            )

            response_text = result.get("content", "").strip()

            # JSON抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            restructure_plan = json.loads(json_text)
            return restructure_plan

        except Exception as e:
            logger.warning(f"LLM再構成計画失敗、フォールバック: {e}")
            return {
                "operations": [],
                "rationale": "再構成計画の生成に失敗しました"
            }

    async def _execute_split(
        self,
        paper_id: str,
        original_section: PaperSectionModel,
        split_plan: Dict[str, Any]
    ) -> List[PaperSectionModel]:
        """分割計画に基づいてセクションを実際に分割"""
        try:
            splits = split_plan.get("splits", [])
            new_sections = []

            # 元のセクションの位置を取得
            original_position = int(original_section.section_number) if original_section.section_number else 1

            for idx, split in enumerate(splits):
                title = split.get("title", f"第{idx+1}部")
                content_start = split.get("content_start", 0)
                content_end = split.get("content_end", len(original_section.content))

                # コンテンツを切り出し
                split_content = original_section.content[content_start:content_end]

                if idx == 0:
                    # 最初の分割は元のセクションを更新
                    updated_section = await self.repository.update_section(
                        original_section.id,
                        {
                            "title": title,
                            "content": split_content,
                            "word_count": len(split_content.split())
                        }
                    )
                    new_sections.append(updated_section)
                else:
                    # 2番目以降は新規セクションとして作成
                    new_section = await self.repository.create_section(
                        paper_id=paper_id,
                        title=title,
                        content=split_content,
                        section_number=str(original_position + idx),
                        hierarchy_path=f"{original_position + idx:03d}"
                    )
                    new_sections.append(new_section)

            return new_sections

        except Exception as e:
            logger.error(f"分割実行エラー: {e}")
            raise AgentExecutionError(f"分割実行に失敗しました: {e}")
