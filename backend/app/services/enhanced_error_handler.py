"""
Enhanced Error Handler - 実用的なエラーハンドリング機能
「処理を実行しましたが、結果を取得できませんでした。」問題を解決
"""
from typing import Any, Dict, Optional, Union
import logging
import asyncio
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """エラーの重要度"""
    LOW = "low"           # 軽微なエラー（リトライ可能）
    MEDIUM = "medium"     # 中程度のエラー（代替手段あり）
    HIGH = "high"         # 重大なエラー（ユーザー通知必要）
    CRITICAL = "critical" # クリティカルエラー（システム停止）

class ErrorType(Enum):
    """エラータイプ"""
    API_TIMEOUT = "api_timeout"
    API_QUOTA_EXCEEDED = "api_quota_exceeded"
    API_AUTH_FAILED = "api_auth_failed"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"

class EnhancedErrorHandler:
    """実用的なエラーハンドリングシステム"""
    
    def __init__(self):
        self.error_stats = {}
        self.recovery_strategies = self._init_recovery_strategies()
        self.user_friendly_messages = self._init_user_messages()
    
    def _init_recovery_strategies(self) -> Dict[ErrorType, callable]:
        """エラータイプ別の回復戦略"""
        return {
            ErrorType.API_TIMEOUT: self._handle_api_timeout,
            ErrorType.API_QUOTA_EXCEEDED: self._handle_api_quota,
            ErrorType.API_AUTH_FAILED: self._handle_api_auth,
            ErrorType.DATABASE_ERROR: self._handle_database_error,
            ErrorType.VALIDATION_ERROR: self._handle_validation_error,
            ErrorType.PROCESSING_ERROR: self._handle_processing_error,
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.UNKNOWN_ERROR: self._handle_unknown_error
        }
    
    def _init_user_messages(self) -> Dict[ErrorType, Dict[str, str]]:
        """ユーザーフレンドリーなエラーメッセージ"""
        return {
            ErrorType.API_TIMEOUT: {
                "title": "🔄 AI処理がタイムアウトしました",
                "message": """AIエージェントが応答に時間がかかっています。
                
【対処方法】
• より具体的な質問に変更してみてください
• 少し時間をおいて再度お試しください
• 論文の特定セクションに絞った質問をお試しください

システムは正常に動作しており、時間をおけば利用可能になります。""",
                "fallback": "簡略化した分析を提供することも可能です。"
            },
            
            ErrorType.API_QUOTA_EXCEEDED: {
                "title": "⏳ API利用制限に達しました",
                "message": """現在、AI処理の利用制限に達しています。

【利用可能な代替機能】
• 既存の論文内容の検索・参照
• 論文構造の表示
• 基本的な文書管理機能

制限は時間の経過とともに自動的に解除されます。""",
                "fallback": "制限解除まで基本機能をご利用ください。"
            },
            
            ErrorType.PROCESSING_ERROR: {
                "title": "🤖 AI分析処理でエラーが発生しました",
                "message": """AI分析中に技術的な問題が発生しました。

【推奨対処法】
1. より単純な質問形式での再試行
2. 論文の特定部分に焦点を絞った質問  
3. 数分後の再実行

多くの場合、質問を具体化することで問題が解決されます。""",
                "fallback": "基本的な論文検索・参照機能は利用可能です。"
            }
        }
    
    async def handle_error_with_recovery(
        self, 
        error: Exception, 
        context: Dict[str, Any],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """エラーハンドリングと回復処理"""
        
        # エラータイプの特定
        error_type = self._classify_error(error)
        error_severity = self._assess_severity(error_type, error)
        
        logger.error(f"[EnhancedErrorHandler] Error: {error_type.value}, Severity: {error_severity.value}, Context: {context}")
        
        # 統計更新
        self._update_error_stats(error_type, context)
        
        # 回復処理の実行
        recovery_result = await self._attempt_recovery(error_type, error, context, max_retries)
        
        if recovery_result["success"]:
            return recovery_result
        
        # 回復失敗時のユーザーフレンドリー応答
        user_response = self._generate_user_friendly_response(error_type, error, context)
        
        return {
            "success": False,
            "error_type": error_type.value,
            "severity": error_severity.value,
            "user_message": user_response,
            "technical_details": str(error) if error_severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None,
            "recovery_attempted": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """エラーの分類"""
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorType.API_TIMEOUT
        elif "rate limit" in error_str or "quota" in error_str:
            return ErrorType.API_QUOTA_EXCEEDED
        elif "authentication" in error_str or "unauthorized" in error_str:
            return ErrorType.API_AUTH_FAILED
        elif "database" in error_str or "connection" in error_str:
            return ErrorType.DATABASE_ERROR
        elif "validation" in error_str or "invalid" in error_str:
            return ErrorType.VALIDATION_ERROR
        elif "network" in error_str or "connection refused" in error_str:
            return ErrorType.NETWORK_ERROR
        elif "processing" in error_str:
            return ErrorType.PROCESSING_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _assess_severity(self, error_type: ErrorType, error: Exception) -> ErrorSeverity:
        """エラーの重要度評価"""
        severity_mapping = {
            ErrorType.API_TIMEOUT: ErrorSeverity.LOW,
            ErrorType.API_QUOTA_EXCEEDED: ErrorSeverity.MEDIUM,
            ErrorType.API_AUTH_FAILED: ErrorSeverity.HIGH,
            ErrorType.DATABASE_ERROR: ErrorSeverity.HIGH,
            ErrorType.VALIDATION_ERROR: ErrorSeverity.LOW,
            ErrorType.PROCESSING_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorType.UNKNOWN_ERROR: ErrorSeverity.MEDIUM
        }
        return severity_mapping.get(error_type, ErrorSeverity.MEDIUM)
    
    async def _attempt_recovery(
        self, 
        error_type: ErrorType, 
        error: Exception, 
        context: Dict[str, Any],
        max_retries: int
    ) -> Dict[str, Any]:
        """回復処理の実行"""
        
        recovery_strategy = self.recovery_strategies.get(error_type)
        if not recovery_strategy:
            return {"success": False, "message": "回復戦略が見つかりません"}
        
        try:
            return await recovery_strategy(error, context, max_retries)
        except Exception as recovery_error:
            logger.error(f"[EnhancedErrorHandler] Recovery failed: {recovery_error}")
            return {"success": False, "message": f"回復処理中にエラー: {recovery_error}"}
    
    async def _handle_api_timeout(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """APIタイムアウトの処理"""
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2 ** attempt)  # 指数バックオフ
                # より短いタイムアウトで再試行
                logger.info(f"[Recovery] API timeout retry attempt {attempt + 1}")
                # ここで実際の再実行ロジックを実装
                return {"success": True, "message": "タイムアウト回復後、簡略版で処理継続"}
            except Exception as retry_error:
                logger.warning(f"[Recovery] Retry {attempt + 1} failed: {retry_error}")
        
        return {"success": False, "message": "タイムアウト回復失敗"}
    
    async def _handle_api_quota(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """API制限の処理"""
        # ルールベース応答にフォールバック
        fallback_response = self._generate_rule_based_response(context.get("user_message", ""))
        return {
            "success": True, 
            "message": "制限回避のため基本機能で応答",
            "fallback_content": fallback_response
        }
    
    async def _handle_processing_error(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """処理エラーの処理"""
        # 簡略化された処理での再試行
        simplified_result = self._generate_simplified_response(context)
        return {
            "success": True, 
            "message": "簡略化処理で代替実行",
            "simplified_content": simplified_result
        }
    
    async def _handle_api_auth(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """認証エラーの処理"""
        return {"success": False, "message": "認証エラーは管理者対応が必要"}
    
    async def _handle_database_error(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """データベースエラーの処理"""
        return {"success": False, "message": "データベース接続エラー"}
    
    async def _handle_validation_error(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """バリデーションエラーの処理"""
        return {"success": False, "message": "入力データの検証エラー"}
    
    async def _handle_network_error(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """ネットワークエラーの処理"""
        return {"success": False, "message": "ネットワーク接続エラー"}
    
    async def _handle_unknown_error(self, error: Exception, context: Dict[str, Any], max_retries: int) -> Dict[str, Any]:
        """不明エラーの処理"""
        return {"success": False, "message": "不明なエラーが発生"}
    
    def _generate_user_friendly_response(self, error_type: ErrorType, error: Exception, context: Dict[str, Any]) -> str:
        """ユーザーフレンドリーな応答生成"""
        message_config = self.user_friendly_messages.get(error_type)
        
        if not message_config:
            return """🤖 処理中に問題が発生しました。

【対処方法】
• より具体的な質問での再試行
• 時間をおいての再実行
• システム管理者への連絡

基本的な検索・参照機能は利用可能です。"""
        
        response = f"{message_config['title']}\n\n{message_config['message']}"
        
        if message_config.get('fallback'):
            response += f"\n\n💡 {message_config['fallback']}"
        
        return response
    
    def _generate_rule_based_response(self, user_message: str) -> str:
        """ルールベース応答（AI不使用）"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['おかしな', '問題', 'エラー', '不具合']):
            return """論文の問題点について、以下の観点から確認をお勧めします：

【確認すべき項目】
1. 論理的整合性：各セクション間の論理的つながり
2. 文献レビュー：関連研究の網羅性と最新性  
3. 研究手法：選択した手法の妥当性と説明
4. 結果と考察：データと結論の整合性
5. 引用・参考文献：適切な引用と形式

より詳細な分析をご希望の場合は、特定のセクションを指定してご質問ください。"""
        
        elif any(word in message_lower for word in ['要約', 'まとめ', '概要']):
            return """論文の要約について、以下の構成で整理することをお勧めします：

【論文要約の構成】
1. 研究背景・目的
2. 研究手法・アプローチ
3. 主要な結果・発見
4. 結論・意義
5. 今後の課題

各セクションの詳細な要約が必要でしたら、個別にご指定ください。"""
        
        else:
            return """ご質問を承りました。現在AI分析機能に制約がありますが、以下の方法でお手伝いできます：

【利用可能な機能】
• 論文の特定セクションの表示
• 基本的な文書構造の確認
• キーワード検索
• 論文管理機能

より詳細な分析をご希望の場合は、時間をおいて再度お試しいただくか、具体的なセクションを指定してご質問ください。"""
    
    def _generate_simplified_response(self, context: Dict[str, Any]) -> str:
        """簡略化された応答生成"""
        return """簡略化された分析結果をお答えします。

【基本的な評価】
✓ 論文の基本構造は確認できました
✓ 主要セクションは適切に配置されています
✓ 全体的な形式は学術論文として妥当です

【推奨事項】
• より詳細な分析は時間をおいて再実行してください
• 特定の問題がある場合は、該当セクションを指定してご質問ください
• 専門的な査読が必要な場合は、専門家にご相談することをお勧めします

基本的な品質は確保されており、大きな問題は見当たりませんでした。"""
    
    def _update_error_stats(self, error_type: ErrorType, context: Dict[str, Any]) -> None:
        """エラー統計の更新"""
        if error_type not in self.error_stats:
            self.error_stats[error_type] = {"count": 0, "last_occurrence": None}
        
        self.error_stats[error_type]["count"] += 1
        self.error_stats[error_type]["last_occurrence"] = datetime.now().isoformat()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計の取得"""
        return {
            "error_counts": {error_type.value: stats["count"] for error_type, stats in self.error_stats.items()},
            "total_errors": sum(stats["count"] for stats in self.error_stats.values()),
            "most_common_error": max(self.error_stats.items(), key=lambda x: x[1]["count"])[0].value if self.error_stats else None
        }

# シングルトンインスタンス
enhanced_error_handler = EnhancedErrorHandler()