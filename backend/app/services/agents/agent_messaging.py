"""
AIエージェント統一メッセージングシステム
拡張性とメンテナンス性を重視した設計
"""
from typing import Dict, Any, List, Optional, Protocol, Union
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
from datetime import datetime

class MessageType(Enum):
    """メッセージタイプ定義"""
    PRE_EXECUTION = "pre_execution"      # 実行前メッセージ
    POST_EXECUTION = "post_execution"    # 実行後メッセージ
    PROGRESS_UPDATE = "progress_update"  # 進捗更新
    ERROR = "error"                      # エラーメッセージ
    WARNING = "warning"                  # 警告メッセージ
    SUCCESS = "success"                  # 成功メッセージ

class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExecutionMetrics:
    """実行メトリクス（共通）"""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    execution_time: Optional[str] = None
    items_processed: int = 0
    items_successful: int = 0
    success_rate: float = 0.0
    quality_score: Optional[float] = None
    api_calls: int = 0  # API呼び出し回数
    cache_hits: int = 0  # キャッシュヒット回数

    def complete(self):
        """実行完了時の処理"""
        self.end_time = time.time()
        self.execution_time = f"{(self.end_time - self.start_time)*1000:.0f}ms"
        if self.items_processed > 0:
            self.success_rate = self.items_successful / self.items_processed

@dataclass 
class AgentMessage:
    """統一エージェントメッセージ"""
    agent_name: str
    message_type: MessageType
    status: TaskStatus
    title: str
    content: str
    metrics: Optional[ExecutionMetrics] = None
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

class AgentMessagingProtocol(Protocol):
    """エージェントメッセージング統一インターフェース"""
    
    def create_pre_execution_message(self, task_params: Dict[str, Any]) -> AgentMessage:
        """実行前メッセージ作成"""
        ...
    
    def create_post_execution_message(
        self, 
        task_result: Dict[str, Any],
        metrics: ExecutionMetrics
    ) -> AgentMessage:
        """実行後メッセージ作成"""
        ...
    
    def create_error_message(self, error: Exception, context: Dict[str, Any]) -> AgentMessage:
        """エラーメッセージ作成"""
        ...

class BaseAgentMessaging(ABC):
    """エージェントメッセージング基底クラス"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.agent_display_name = self._get_display_name()
        self.agent_emoji = self._get_emoji()
        self.capabilities = self._get_capabilities()
    
    @abstractmethod
    def _get_display_name(self) -> str:
        """表示名を取得"""
        pass
    
    @abstractmethod
    def _get_emoji(self) -> str:
        """エージェント識別絵文字を取得"""
        pass
    
    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """エージェント能力リストを取得"""
        pass
    
    def create_pre_execution_message(self, task_params: Dict[str, Any]) -> AgentMessage:
        """実行前メッセージ（共通テンプレート）"""
        task_type = task_params.get("task_type", "未指定タスク")
        
        content = f"""{self.agent_emoji} **{self.agent_display_name}** が作業を開始します

🎯 **実行予定のタスク:**
- タスクタイプ: {task_type}
{self._format_task_specific_params(task_params)}

⚙️ **実行方法:**
{self._describe_execution_method(task_params)}

⏱️ **予想実行時間:** {self._estimate_execution_time(task_params)}

実行を開始します..."""

        return AgentMessage(
            agent_name=self.agent_name,
            message_type=MessageType.PRE_EXECUTION,
            status=TaskStatus.RUNNING,
            title=f"{self.agent_display_name} 作業開始",
            content=content,
            details=task_params
        )
    
    def create_post_execution_message(
        self, 
        task_result: Dict[str, Any],
        metrics: ExecutionMetrics
    ) -> AgentMessage:
        """実行後メッセージ（共通テンプレート）"""
        success = task_result.get("success", False)
        status_emoji = "✅" if success else "❌"
        status_text = "完了" if success else "失敗"
        
        content = f"""{status_emoji} **{self.agent_display_name}** のタスクが{status_text}しました！

📊 **実行結果サマリー:**
- ステータス: {status_text}
- 実行時間: {metrics.execution_time or '不明'}
- 処理件数: {metrics.items_processed}件
- 成功率: {metrics.success_rate:.0%}
{f"- 品質スコア: {metrics.quality_score:.1f}/10" if metrics.quality_score else ""}

{self._format_execution_details(task_result, metrics)}

{self._format_task_specific_results(task_result)}"""

        suggestions = self._generate_next_action_suggestions(task_result)
        references = self._extract_references(task_result)
        
        return AgentMessage(
            agent_name=self.agent_name,
            message_type=MessageType.POST_EXECUTION,
            status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
            title=f"{self.agent_display_name} 作業{status_text}",
            content=content,
            metrics=metrics,
            details=task_result,
            suggestions=suggestions,
            references=references
        )
    
    def create_error_message(self, error: Exception, context: Dict[str, Any]) -> AgentMessage:
        """エラーメッセージ"""
        content = f"""❌ **{self.agent_display_name}** でエラーが発生しました

🔍 **エラー詳細:**
- エラータイプ: {type(error).__name__}
- エラーメッセージ: {str(error)}
- 発生箇所: {context.get('location', '不明')}

💡 **推奨対応:**
{self._suggest_error_recovery(error, context)}

🔄 **次のアクション:**
- パラメータを確認して再実行
- 別のエージェントでの代替処理を検討
- 技術サポートへの問い合わせ"""
        
        return AgentMessage(
            agent_name=self.agent_name,
            message_type=MessageType.ERROR,
            status=TaskStatus.FAILED,
            title=f"{self.agent_display_name} エラー",
            content=content,
            details={"error": str(error), "context": context}
        )
    
    # 子クラスでオーバーライドする抽象メソッド
    @abstractmethod
    def _format_task_specific_params(self, task_params: Dict[str, Any]) -> str:
        """タスク固有パラメータのフォーマット"""
        pass
    
    @abstractmethod
    def _describe_execution_method(self, task_params: Dict[str, Any]) -> str:
        """実行方法の説明"""
        pass
    
    @abstractmethod
    def _estimate_execution_time(self, task_params: Dict[str, Any]) -> str:
        """実行時間の予測"""
        pass
    
    @abstractmethod
    def _format_execution_details(self, task_result: Dict[str, Any], metrics: ExecutionMetrics) -> str:
        """実行詳細のフォーマット"""
        pass
    
    @abstractmethod
    def _format_task_specific_results(self, task_result: Dict[str, Any]) -> str:
        """タスク固有結果のフォーマット"""
        pass
    
    @abstractmethod
    def _generate_next_action_suggestions(self, task_result: Dict[str, Any]) -> List[str]:
        """次のアクション提案生成"""
        pass
    
    @abstractmethod
    def _extract_references(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """参照情報抽出"""
        pass
    
    @abstractmethod
    def _suggest_error_recovery(self, error: Exception, context: Dict[str, Any]) -> str:
        """エラー回復提案"""
        pass

# =====================================================
# 具体的なエージェントメッセージング実装例
# =====================================================

class SectionQueryAgentMessaging(BaseAgentMessaging):
    """セクション検索エージェント専用メッセージング"""
    
    def _get_display_name(self) -> str:
        return "セクション検索エージェント"
    
    def _get_emoji(self) -> str:
        return "🔍"
    
    def _get_capabilities(self) -> List[str]:
        return ["セクション検索", "ファジーマッチング", "コンテンツ抽出", "類似度計算"]
    
    def _format_task_specific_params(self, task_params: Dict[str, Any]) -> str:
        query = task_params.get("query", "未指定")
        paper_id = task_params.get("paper_id", "不明")[:8] + "..." if task_params.get("paper_id") else "不明"
        
        return f"""- 検索クエリ: 「{query}」
- 対象論文: {paper_id}
- マッチング手法: ファジー文字列マッチング"""
    
    def _describe_execution_method(self, task_params: Dict[str, Any]) -> str:
        return """1. 論文内の全セクションを取得
2. 完全一致 → 部分一致 → 曖昧一致の順で検索
3. 類似度スコア計算（fuzzywuzzy使用）
4. 最適マッチの選定・コンテンツ抽出"""
    
    def _estimate_execution_time(self, task_params: Dict[str, Any]) -> str:
        return "100-500ms（セクション数に依存）"
    
    def _format_execution_details(self, task_result: Dict[str, Any], metrics: ExecutionMetrics) -> str:
        sections_searched = task_result.get("sections_searched", 0)
        found_sections = task_result.get("found_sections", [])
        
        return f"""
🔍 **検索詳細:**
- 検索対象セクション数: {sections_searched}件
- 発見セクション数: {len(found_sections)}件
- 検索アルゴリズム: Fuzzy String Matching"""
    
    def _format_task_specific_results(self, task_result: Dict[str, Any]) -> str:
        found_sections = task_result.get("found_sections", [])
        
        if not found_sections:
            return "\n📄 **検索結果:** 該当するセクションが見つかりませんでした"
        
        best_match = found_sections[0]  # 最初が最高スコア
        similarity = best_match.get("similarity_score", 0)
        title = best_match.get("title", "不明")
        word_count = best_match.get("word_count", 0)
        content = best_match.get("content", "")[:200] + "..." if len(best_match.get("content", "")) > 200 else best_match.get("content", "")
        
        return f"""
📄 **発見したセクション:**
- タイトル: "{title}"
- 類似度: {similarity:.0%} {'(完全一致)' if similarity >= 1.0 else ''}
- 文字数: {word_count}語
- 内容プレビュー: {content}

📖 **完全な内容:**

{best_match.get("content", "内容を取得できませんでした")}"""
    
    def _generate_next_action_suggestions(self, task_result: Dict[str, Any]) -> List[str]:
        found_sections = task_result.get("found_sections", [])
        
        if found_sections:
            title = found_sections[0].get("title", "このセクション")
            return [
                f"{title}を編集・改善する",
                "関連する他のセクションも検索する", 
                "このセクションの要約を作成する",
                "論理構造を検証する"
            ]
        else:
            return [
                "検索キーワードを変更して再検索",
                "新しいセクションを作成する",
                "既存セクション一覧を確認する"
            ]
    
    def _extract_references(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        found_sections = task_result.get("found_sections", [])
        references = []
        
        for section in found_sections:
            references.append({
                "type": "section",
                "section_id": section.get("id"),
                "title": section.get("title"),
                "content": section.get("content"),
                "similarity_score": section.get("similarity_score")
            })
        
        return references
    
    def _suggest_error_recovery(self, error: Exception, context: Dict[str, Any]) -> str:
        if "database" in str(error).lower():
            return "データベース接続を確認し、セッションを再初期化してください"
        elif "permission" in str(error).lower():
            return "論文へのアクセス権限を確認してください"
        else:
            return "クエリパラメータを確認し、有効な論文IDと検索キーワードを指定してください"

class WriterAgentMessaging(BaseAgentMessaging):
    """コンテンツ生成エージェント専用メッセージング"""
    
    def _get_display_name(self) -> str:
        return "コンテンツ生成エージェント"
    
    def _get_emoji(self) -> str:
        return "✍️"
    
    def _get_capabilities(self) -> List[str]:
        return ["学術文章生成", "スタイル調整", "構造化ライティング", "品質評価"]
    
    def _format_task_specific_params(self, task_params: Dict[str, Any]) -> str:
        section_title = task_params.get("section_title", "未指定")
        style = task_params.get("style", "academic")
        word_target = task_params.get("word_target", "指定なし")
        
        return f"""- 対象セクション: {section_title}
- 文章スタイル: {style}
- 目標語数: {word_target}語
- 生成モード: 新規作成"""
    
    def _describe_execution_method(self, task_params: Dict[str, Any]) -> str:
        return """1. 論文コンテキストの分析
2. セクション要件の特定
3. 構造化されたアウトライン作成
4. LLMによる段落別コンテンツ生成
5. 品質評価・最適化"""
    
    def _estimate_execution_time(self, task_params: Dict[str, Any]) -> str:
        word_target = task_params.get("word_target", 300)
        estimated_time = max(5, word_target // 50)  # 50語/秒として計算
        return f"{estimated_time}-{estimated_time*2}秒"
    
    def _format_execution_details(self, task_result: Dict[str, Any], metrics: ExecutionMetrics) -> str:
        word_count = task_result.get("word_count", 0)
        style = task_result.get("style", "不明")
        
        return f"""
✍️ **生成詳細:**
- 生成語数: {word_count}語
- 文章スタイル: {style}
- 品質チェック: 実施済み"""
    
    def _format_task_specific_results(self, task_result: Dict[str, Any]) -> str:
        content = task_result.get("generated_content", "")
        section_title = task_result.get("target_section", "新規セクション")
        quality_metrics = task_result.get("quality_metrics", {})
        
        quality_info = ""
        if quality_metrics:
            readability = quality_metrics.get("readability_score", "N/A")
            tone = quality_metrics.get("academic_tone", "不明")
            coherence = quality_metrics.get("coherence", "不明")
            quality_info = f"""
📊 **品質指標:**
- 可読性: {readability}/10
- 学術性: {tone}
- 一貫性: {coherence}"""
        
        preview = content[:300] + "..." if len(content) > 300 else content
        
        return f"""
📝 **生成結果:**{quality_info}
- セクション: {section_title}

📖 **生成されたコンテンツ:**

{content}"""
    
    def _generate_next_action_suggestions(self, task_result: Dict[str, Any]) -> List[str]:
        if task_result.get("success"):
            return [
                "生成されたコンテンツを校正・編集する",
                "論理構造を検証する", 
                "他のセクションも生成する",
                "生成コンテンツを論文に統合する"
            ]
        else:
            return [
                "生成パラメータを調整して再試行",
                "異なる文章スタイルで生成",
                "手動でコンテンツを作成"
            ]
    
    def _extract_references(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        # WriterAgentは通常外部リファレンスを生成しない
        generated_content = task_result.get("generated_content")
        if generated_content:
            return [{
                "type": "generated_content",
                "content": generated_content,
                "word_count": task_result.get("word_count", 0),
                "section": task_result.get("target_section", "不明")
            }]
        return []
    
    def _suggest_error_recovery(self, error: Exception, context: Dict[str, Any]) -> str:
        if "token" in str(error).lower() or "api" in str(error).lower():
            return "OpenAI APIの接続とトークン設定を確認してください"
        elif "timeout" in str(error).lower():
            return "生成時間が長すぎる可能性があります。語数を減らして再試行してください"
        else:
            return "生成パラメータ（セクションタイトル、スタイル等）を確認してください"

# =====================================================
# メッセージングファクトリー
# =====================================================

class AgentMessagingFactory:
    """エージェントメッセージング ファクトリークラス"""
    
    _messaging_classes = {
        "SectionQueryAgent": SectionQueryAgentMessaging,
        "WriterAgent": WriterAgentMessaging,
        # 新しいエージェントはここに追加するだけ
    }
    
    @classmethod
    def create_messaging(self, agent_name: str) -> BaseAgentMessaging:
        """エージェントに対応するメッセージングインスタンスを作成"""
        messaging_class = self._messaging_classes.get(agent_name)
        
        if messaging_class:
            return messaging_class(agent_name)
        else:
            # フォールバック: 汎用メッセージング
            return GenericAgentMessaging(agent_name)
    
    @classmethod
    def register_agent_messaging(cls, agent_name: str, messaging_class: type):
        """新しいエージェントメッセージングを登録"""
        cls._messaging_classes[agent_name] = messaging_class

class GenericAgentMessaging(BaseAgentMessaging):
    """汎用エージェントメッセージング（フォールバック）"""
    
    def _get_display_name(self) -> str:
        return f"{self.agent_name.replace('Agent', '')} エージェント"
    
    def _get_emoji(self) -> str:
        return "🤖"
    
    def _get_capabilities(self) -> List[str]:
        return ["汎用タスク処理"]
    
    def _format_task_specific_params(self, task_params: Dict[str, Any]) -> str:
        params_str = "\n".join([f"- {k}: {v}" for k, v in task_params.items() if k != "task_type"])
        return params_str or "- パラメータ: なし"
    
    def _describe_execution_method(self, task_params: Dict[str, Any]) -> str:
        return f"{self.agent_name}の標準処理手順に従って実行します"
    
    def _estimate_execution_time(self, task_params: Dict[str, Any]) -> str:
        return "数秒～数十秒"
    
    def _format_execution_details(self, task_result: Dict[str, Any], metrics: ExecutionMetrics) -> str:
        return f"🔄 **処理詳細:**\n- 処理件数: {metrics.items_processed}件"
    
    def _format_task_specific_results(self, task_result: Dict[str, Any]) -> str:
        result_summary = task_result.get("summary", "処理が完了しました")
        return f"\n📋 **処理結果:**\n{result_summary}"
    
    def _generate_next_action_suggestions(self, task_result: Dict[str, Any]) -> List[str]:
        return ["結果を確認する", "追加の処理を実行する", "他のエージェントを起動する"]
    
    def _extract_references(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
    
    def _suggest_error_recovery(self, error: Exception, context: Dict[str, Any]) -> str:
        return "パラメータと設定を確認し、再度実行してください"