"""
Wake Word Detector - ユーザーメッセージからエージェントを特定する
"""
from typing import List, Optional, Dict, Any
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WakeWordMatch:
    """ウェイクワードマッチ結果"""
    agent_id: str
    agent_name: str
    keyword: str
    keyword_type: str
    priority: int
    similarity_score: float = 1.0  # exact/partial/regexの場合は1.0


class WakeWordDetector:
    """
    ウェイクワード検出クラス

    4つのマッチングタイプをサポート:
    1. exact: 完全一致
    2. partial: 部分一致
    3. regex: 正規表現マッチ
    4. semantic: 意味的類似性マッチ（将来拡張）
    """

    def __init__(self):
        self.wake_words: List[Dict[str, Any]] = []

    def load_wake_words(self, wake_words: List[Dict[str, Any]]) -> None:
        """
        ウェイクワードをロード

        Args:
            wake_words: ウェイクワードリスト
                [
                    {
                        "id": "wake_word_id",
                        "agent_id": "agent_id",
                        "agent_name": "agent_name",
                        "keyword": "keyword",
                        "keyword_type": "exact|partial|regex|semantic",
                        "priority": 10,
                        "min_similarity_score": 0.7  # semanticの場合のみ使用
                    },
                    ...
                ]
        """
        self.wake_words = sorted(wake_words, key=lambda x: x.get("priority", 10))
        logger.info(f"Loaded {len(self.wake_words)} wake words")

    async def detect(self, message: str) -> List[WakeWordMatch]:
        """
        メッセージからウェイクワードを検出

        Args:
            message: ユーザーメッセージ

        Returns:
            マッチしたウェイクワードリスト（優先順位順）
        """
        matches: List[WakeWordMatch] = []

        for wake_word in self.wake_words:
            keyword_type = wake_word.get("keyword_type", "exact")

            if keyword_type == "exact":
                match = self._match_exact(message, wake_word)
            elif keyword_type == "partial":
                match = self._match_partial(message, wake_word)
            elif keyword_type == "regex":
                match = self._match_regex(message, wake_word)
            elif keyword_type == "semantic":
                match = await self._match_semantic(message, wake_word)
            else:
                logger.warning(f"Unknown keyword_type: {keyword_type}")
                continue

            if match:
                matches.append(match)

        return matches

    def _match_exact(self, message: str, wake_word: Dict[str, Any]) -> Optional[WakeWordMatch]:
        """完全一致マッチング"""
        keyword = wake_word.get("keyword", "")

        if keyword.lower() in message.lower():
            return WakeWordMatch(
                agent_id=wake_word["agent_id"],
                agent_name=wake_word.get("agent_name", "Unknown"),
                keyword=keyword,
                keyword_type="exact",
                priority=wake_word.get("priority", 10),
                similarity_score=1.0
            )
        return None

    def _match_partial(self, message: str, wake_word: Dict[str, Any]) -> Optional[WakeWordMatch]:
        """部分一致マッチング"""
        keyword = wake_word.get("keyword", "")

        # キーワードの部分文字列がメッセージに含まれているか
        if keyword.lower() in message.lower():
            return WakeWordMatch(
                agent_id=wake_word["agent_id"],
                agent_name=wake_word.get("agent_name", "Unknown"),
                keyword=keyword,
                keyword_type="partial",
                priority=wake_word.get("priority", 10),
                similarity_score=1.0
            )
        return None

    def _match_regex(self, message: str, wake_word: Dict[str, Any]) -> Optional[WakeWordMatch]:
        """正規表現マッチング"""
        keyword = wake_word.get("keyword", "")

        try:
            pattern = re.compile(keyword, re.IGNORECASE)
            if pattern.search(message):
                return WakeWordMatch(
                    agent_id=wake_word["agent_id"],
                    agent_name=wake_word.get("agent_name", "Unknown"),
                    keyword=keyword,
                    keyword_type="regex",
                    priority=wake_word.get("priority", 10),
                    similarity_score=1.0
                )
        except re.error as e:
            logger.error(f"Invalid regex pattern '{keyword}': {e}")

        return None

    async def _match_semantic(
        self,
        message: str,
        wake_word: Dict[str, Any]
    ) -> Optional[WakeWordMatch]:
        """
        意味的類似性マッチング

        TODO: OpenAI Embeddings APIを使用した実装
        現在はスタブ実装
        """
        # 将来の実装:
        # 1. messageとkeywordの両方をEmbeddings化
        # 2. コサイン類似度を計算
        # 3. min_similarity_score以上ならマッチ

        min_score = wake_word.get("min_similarity_score", 0.7)

        # スタブ実装: 常にFalseを返す
        logger.debug(f"Semantic matching not yet implemented for: {wake_word.get('keyword')}")
        return None


class WakeWordManager:
    """
    ウェイクワード管理クラス

    AgentRepositoryと連携してウェイクワードを管理
    """

    def __init__(self, agent_repository):
        self.agent_repository = agent_repository
        self.detector = WakeWordDetector()

    async def initialize(self, user_id: Optional[str] = None) -> None:
        """
        ウェイクワードをDBから読み込んで初期化

        Args:
            user_id: ユーザーID（指定時はユーザー固有のウェイクワードも含む）
        """
        # DBからアクティブなウェイクワード一覧を取得
        wake_word_models = await self.agent_repository.get_active_wake_words(user_id=user_id)

        # モデルを辞書形式に変換
        wake_words = []
        for ww in wake_word_models:
            # エージェント情報を取得
            agent = await self.agent_repository.get_agent_by_id(ww.agent_id)
            if agent:
                wake_words.append({
                    "id": ww.id,
                    "agent_id": ww.agent_id,
                    "agent_name": agent.name,
                    "keyword": ww.keyword,
                    "keyword_type": ww.keyword_type,
                    "priority": ww.priority,
                    "min_similarity_score": ww.min_similarity_score or 0.7
                })

        self.detector.load_wake_words(wake_words)
        logger.info(f"Initialized WakeWordManager with {len(wake_words)} wake words")

    async def detect_agents(self, message: str) -> List[WakeWordMatch]:
        """
        メッセージからエージェントを検出

        Args:
            message: ユーザーメッセージ

        Returns:
            マッチしたエージェントリスト（優先順位順）
        """
        matches = await self.detector.detect(message)

        # ウェイクワード使用回数を更新
        for match in matches:
            # wake_word_idを取得するために、matchから元のwake_wordを探す
            for ww in self.detector.wake_words:
                if ww["agent_id"] == match.agent_id and ww["keyword"] == match.keyword:
                    await self.agent_repository.update_wake_word_usage(ww["id"])
                    break

        return matches
