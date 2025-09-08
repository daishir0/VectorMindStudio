"""
AIエージェント責務定義
Clear Boundaries Patternの実装
"""
from typing import Dict, List, Set
from enum import Enum
from dataclasses import dataclass


class TaskType(Enum):
    """タスクタイプの列挙"""
    # OutlineAgent専用タスク
    CREATE_SECTION = "create_section"
    REORGANIZE_SECTIONS = "reorganize_sections" 
    UPDATE_HIERARCHY = "update_hierarchy"
    
    # WriterAgent専用タスク
    GENERATE_DRAFT = "generate_draft"
    UPDATE_CONTENT = "update_content"
    EXPAND_CONTENT = "expand_content"
    IMPROVE_STYLE = "improve_style"
    
    # LogicValidatorAgent専用タスク
    VALIDATE_STRUCTURE = "validate_structure"
    VALIDATE_ARGUMENTS = "validate_arguments"
    VALIDATE_CONSISTENCY = "validate_consistency"
    CHECK_COMPLETENESS = "check_completeness"
    
    # SummaryAgent専用タスク
    CREATE_SUMMARY = "create_summary"
    CREATE_ABSTRACT = "create_abstract"
    ANALYZE_SECTION = "analyze_section"
    
    # ReferenceAgent専用タスク
    SEARCH_REFERENCES = "search_references"
    VALIDATE_CITATIONS = "validate_citations"
    ADD_CITATIONS = "add_citations"
    
    # 汎用タスク（後方互換性のため残す）
    GENERAL = "general"


@dataclass
class AgentCapability:
    """エージェント能力定義"""
    name: str
    description: str
    required_inputs: List[str]
    expected_outputs: List[str]
    dependencies: List[str] = None


class AgentResponsibilities:
    """
    エージェント責務マネージャー
    MECE原則（Mutually Exclusive, Collectively Exhaustive）を適用
    """
    
    # エージェント別タスク定義
    AGENT_TASKS: Dict[str, Dict[TaskType, AgentCapability]] = {
        "outline": {
            TaskType.CREATE_SECTION: AgentCapability(
                name="セクション作成",
                description="新しいセクションの構造とメタデータを作成",
                required_inputs=["paper_id", "section_title", "hierarchy_path"],
                expected_outputs=["section_id", "section_metadata"],
                dependencies=[]
            ),
            TaskType.REORGANIZE_SECTIONS: AgentCapability(
                name="セクション再構成",
                description="セクション順序とhierarchy_pathの調整",
                required_inputs=["paper_id", "reorganization_plan"],
                expected_outputs=["updated_sections"],
                dependencies=[]
            ),
            TaskType.UPDATE_HIERARCHY: AgentCapability(
                name="階層更新",
                description="セクション階層構造の更新",
                required_inputs=["paper_id", "new_hierarchy"],
                expected_outputs=["updated_hierarchy"],
                dependencies=[]
            )
        },
        
        "writer": {
            TaskType.GENERATE_DRAFT: AgentCapability(
                name="ドラフト生成",
                description="指定されたセクションの初期コンテンツを生成",
                required_inputs=["section_id", "requirements", "context"],
                expected_outputs=["draft_content", "word_count"],
                dependencies=["outline"]  # セクションが先に作成されている必要
            ),
            TaskType.UPDATE_CONTENT: AgentCapability(
                name="コンテンツ更新",
                description="既存コンテンツの改善・修正",
                required_inputs=["section_id", "current_content", "update_requirements"],
                expected_outputs=["updated_content", "word_count"],
                dependencies=[]
            ),
            TaskType.EXPAND_CONTENT: AgentCapability(
                name="コンテンツ拡張",
                description="既存コンテンツの詳細化・拡張",
                required_inputs=["section_id", "current_content", "expansion_areas"],
                expected_outputs=["expanded_content", "word_count"],
                dependencies=[]
            ),
            TaskType.IMPROVE_STYLE: AgentCapability(
                name="文体改善",
                description="文章の可読性と学術的品質の向上",
                required_inputs=["content", "target_style", "requirements"],
                expected_outputs=["improved_content", "style_changes"],
                dependencies=[]
            )
        },
        
        "logic_validator": {
            TaskType.VALIDATE_STRUCTURE: AgentCapability(
                name="構造検証",
                description="論文の論理構造と整合性をチェック",
                required_inputs=["paper_id", "sections"],
                expected_outputs=["validation_result", "issues", "score"],
                dependencies=["writer"]
            ),
            TaskType.VALIDATE_ARGUMENTS: AgentCapability(
                name="論証検証",
                description="論証の妥当性と説得力を評価",
                required_inputs=["content", "argument_criteria"],
                expected_outputs=["argument_analysis", "suggestions"],
                dependencies=["writer"]
            ),
            TaskType.VALIDATE_CONSISTENCY: AgentCapability(
                name="一貫性検証",
                description="用語使用や論調の一貫性をチェック",
                required_inputs=["paper_content", "consistency_rules"],
                expected_outputs=["consistency_report", "corrections"],
                dependencies=["writer"]
            )
        },
        
        "summary": {
            TaskType.CREATE_SUMMARY: AgentCapability(
                name="要約作成",
                description="セクションまたは論文全体の要約を生成",
                required_inputs=["content", "summary_length", "focus_areas"],
                expected_outputs=["summary_text", "key_points"],
                dependencies=["writer"]
            ),
            TaskType.CREATE_ABSTRACT: AgentCapability(
                name="抄録作成",
                description="学術論文の抄録を作成",
                required_inputs=["paper_content", "abstract_requirements"],
                expected_outputs=["abstract_text", "keywords"],
                dependencies=["writer"]
            ),
            TaskType.ANALYZE_SECTION: AgentCapability(
                name="セクション分析",
                description="特定セクションの内容を分析",
                required_inputs=["section_content", "analysis_focus"],
                expected_outputs=["analysis_result", "insights"],
                dependencies=[]
            )
        },
        
        "reference": {
            TaskType.SEARCH_REFERENCES: AgentCapability(
                name="文献検索",
                description="関連する学術文献を検索",
                required_inputs=["keywords", "search_criteria", "limit"],
                expected_outputs=["references", "search_metadata"],
                dependencies=[]
            ),
            TaskType.VALIDATE_CITATIONS: AgentCapability(
                name="引用検証",
                description="引用の正確性と適切性を検証",
                required_inputs=["citations", "content_context"],
                expected_outputs=["validation_result", "corrections"],
                dependencies=[]
            ),
            TaskType.ADD_CITATIONS: AgentCapability(
                name="引用追加",
                description="適切な引用をコンテンツに追加",
                required_inputs=["content", "references", "citation_style"],
                expected_outputs=["content_with_citations", "citation_list"],
                dependencies=["writer"]
            )
        }
    }
    
    @classmethod
    def validate_task_assignment(cls, agent_name: str, task_type: TaskType) -> bool:
        """タスク割り当ての妥当性を検証"""
        if agent_name not in cls.AGENT_TASKS:
            return False
        return task_type in cls.AGENT_TASKS[agent_name]
    
    @classmethod
    def get_agent_capabilities(cls, agent_name: str) -> Dict[TaskType, AgentCapability]:
        """エージェントの能力一覧を取得"""
        return cls.AGENT_TASKS.get(agent_name, {})
    
    @classmethod
    def get_task_dependencies(cls, agent_name: str, task_type: TaskType) -> List[str]:
        """タスクの依存関係を取得"""
        if not cls.validate_task_assignment(agent_name, task_type):
            return []
        
        capability = cls.AGENT_TASKS[agent_name][task_type]
        return capability.dependencies or []
    
    @classmethod
    def find_responsible_agent(cls, task_type: TaskType) -> str:
        """タスクタイプから責任エージェントを特定"""
        for agent_name, tasks in cls.AGENT_TASKS.items():
            if task_type in tasks:
                return agent_name
        return None
    
    @classmethod
    def get_all_task_types(cls) -> Set[TaskType]:
        """システム内で利用可能な全タスクタイプを取得"""
        all_tasks = set()
        for tasks in cls.AGENT_TASKS.values():
            all_tasks.update(tasks.keys())
        return all_tasks
    
    @classmethod
    def validate_workflow_chain(cls, chain: List[tuple]) -> bool:
        """ワークフローチェーンの妥当性を検証"""
        for i, (agent_name, task_type) in enumerate(chain):
            # タスク割り当ての妥当性チェック
            if not cls.validate_task_assignment(agent_name, task_type):
                return False
            
            # 依存関係チェック
            if i > 0:
                dependencies = cls.get_task_dependencies(agent_name, task_type)
                if dependencies:
                    # 前のステップで依存エージェントが実行されているかチェック
                    previous_agents = {agent for agent, _ in chain[:i]}
                    if not all(dep in previous_agents for dep in dependencies):
                        return False
        
        return True


class TaskExecutionError(Exception):
    """タスク実行エラー"""
    pass


class AgentResponsibilityViolation(Exception):
    """エージェント責務違反エラー"""
    pass