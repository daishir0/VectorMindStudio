"""
Hybrid Agent Loader - code_basedとllm_basedの両方をサポート

executor_typeに基づいてエージェントを動的にロード：
- code_based: Pythonクラスから動的インポート
- llm_based: DynamicAgentを使用（DBベース）
"""
from typing import Dict, Any, Optional, List, Union
import logging
import importlib
import sys
from pathlib import Path

from app.services.agents.base_agent import BaseAgent
from app.services.agents.enhanced_base_agent import EnhancedBaseAgent
from app.services.dynamic_agent_loader import DynamicAgent
from app.infrastructure.database.models import AIAgentModel

logger = logging.getLogger(__name__)


class HybridAgentLoader:
    """
    ハイブリッドエージェントローダー

    AgentRepositoryからエージェント設定を読み込み、
    executor_typeに応じて適切な方法でエージェントをロード：

    - code_based: class_pathからPythonクラスを動的インポート
    - llm_based: DynamicAgentとして生成（DBベース）
    """

    def __init__(self, agent_repository, llm_client: Any = None, session: Any = None):
        """
        Args:
            agent_repository: AgentRepository instance
            llm_client: LLM client (OpenAI等) for llm_based agents
            session: AsyncSession (code_basedエージェントのコンストラクタ引数用)
        """
        self.agent_repository = agent_repository
        self.llm_client = llm_client
        self.session = session

        # キャッシュ: agent_id -> agent instance
        self._agent_cache: Dict[str, Union[BaseAgent, EnhancedBaseAgent, DynamicAgent]] = {}

        # code_basedエージェントのクラスキャッシュ
        self._class_cache: Dict[str, type] = {}

    async def load_agent_by_id(
        self,
        agent_id: str,
        force_reload: bool = False
    ) -> Optional[Union[BaseAgent, DynamicAgent]]:
        """
        IDでエージェントをロード

        Args:
            agent_id: エージェントID
            force_reload: True の場合、キャッシュを無視して再ロード

        Returns:
            エージェントインスタンス、存在しない場合はNone
        """
        # キャッシュ確認
        if not force_reload and agent_id in self._agent_cache:
            logger.debug(f"Returning cached agent: {agent_id}")
            return self._agent_cache[agent_id]

        # DBから取得
        agent_model = await self.agent_repository.get_agent_by_id(agent_id)
        if agent_model is None:
            logger.warning(f"Agent not found: {agent_id}")
            return None

        # executor_typeに基づいてロード
        agent = await self._load_agent_from_model(agent_model)

        if agent:
            # キャッシュ
            self._agent_cache[agent_id] = agent
            logger.info(
                f"Loaded agent: {agent_model.name} ({agent_id}, "
                f"executor_type={agent_model.executor_type})"
            )

        return agent

    async def load_agent_by_name(
        self,
        agent_name: str,
        force_reload: bool = False
    ) -> Optional[Union[BaseAgent, DynamicAgent]]:
        """
        名前でエージェントをロード

        Args:
            agent_name: エージェント名
            force_reload: True の場合、キャッシュを無視して再ロード

        Returns:
            エージェントインスタンス、存在しない場合はNone
        """
        # DBから取得
        agent_model = await self.agent_repository.get_agent_by_name(agent_name)
        if agent_model is None:
            logger.warning(f"Agent not found: {agent_name}")
            return None

        # キャッシュ確認
        if not force_reload and agent_model.id in self._agent_cache:
            logger.debug(f"Returning cached agent: {agent_name} ({agent_model.id})")
            return self._agent_cache[agent_model.id]

        # executor_typeに基づいてロード
        agent = await self._load_agent_from_model(agent_model)

        if agent:
            # キャッシュ
            self._agent_cache[agent_model.id] = agent
            logger.info(
                f"Loaded agent: {agent_model.name} ({agent_model.id}, "
                f"executor_type={agent_model.executor_type})"
            )

        return agent

    async def load_all_active_agents(
        self,
        user_id: Optional[str] = None,
        force_reload: bool = False
    ) -> List[Union[BaseAgent, DynamicAgent]]:
        """
        アクティブなエージェント一覧をロード

        Args:
            user_id: ユーザーID（指定時はユーザー固有エージェントも含む）
            force_reload: True の場合、キャッシュを無視して再ロード

        Returns:
            エージェントインスタンスリスト
        """
        agent_models = await self.agent_repository.get_active_agents(user_id=user_id)

        agents = []
        for agent_model in agent_models:
            # キャッシュ確認
            if not force_reload and agent_model.id in self._agent_cache:
                agents.append(self._agent_cache[agent_model.id])
            else:
                # 新規ロード
                agent = await self._load_agent_from_model(agent_model)
                if agent:
                    self._agent_cache[agent_model.id] = agent
                    agents.append(agent)

        logger.info(f"Loaded {len(agents)} active agents")
        return agents

    async def _load_agent_from_model(
        self,
        agent_model: AIAgentModel
    ) -> Optional[Union[BaseAgent, DynamicAgent]]:
        """
        AgentModelからエージェントをロード

        Args:
            agent_model: エージェントモデル

        Returns:
            エージェントインスタンス
        """
        if agent_model.executor_type == "code_based":
            return self._load_code_based_agent(agent_model)
        elif agent_model.executor_type == "llm_based":
            return self._load_llm_based_agent(agent_model)
        else:
            logger.error(f"Unknown executor_type: {agent_model.executor_type} for agent {agent_model.id}")
            return None

    def _load_code_based_agent(self, agent_model: AIAgentModel) -> Optional[BaseAgent]:
        """
        code_basedエージェントをロード（Pythonクラスから動的インポート）

        Args:
            agent_model: エージェントモデル

        Returns:
            BaseAgentインスタンス、失敗時はNone
        """
        class_path = agent_model.class_path

        if not class_path:
            logger.error(f"code_based agent {agent_model.id} has no class_path")
            return None

        try:
            # class_pathをパース: "module.path:ClassName"
            if ":" not in class_path:
                logger.error(f"Invalid class_path format: {class_path} (expected 'module.path:ClassName')")
                return None

            module_path, class_name = class_path.split(":", 1)

            # クラスキャッシュ確認
            if class_path in self._class_cache:
                AgentClass = self._class_cache[class_path]
            else:
                # モジュールをインポート
                try:
                    module = importlib.import_module(module_path)
                except ModuleNotFoundError as e:
                    logger.error(f"Module not found: {module_path} for agent {agent_model.name}: {e}")
                    return None

                # クラスを取得
                if not hasattr(module, class_name):
                    logger.error(f"Class {class_name} not found in module {module_path}")
                    return None

                AgentClass = getattr(module, class_name)

                # BaseAgentまたはEnhancedBaseAgentのサブクラスかチェック
                if not issubclass(AgentClass, (BaseAgent, EnhancedBaseAgent)):
                    logger.error(f"Class {class_name} is not a subclass of BaseAgent or EnhancedBaseAgent")
                    return None

                # クラスキャッシュに保存
                self._class_cache[class_path] = AgentClass

            # インスタンス生成
            # sessionがある場合はコンストラクタに渡す（既存のcode_basedエージェント用）
            if self.session is not None:
                try:
                    agent_instance = AgentClass(self.session)
                except TypeError:
                    # sessionを受け取らないエージェントの場合は引数なしで試行
                    logger.warning(f"Agent {class_name} does not accept session, trying without args")
                    agent_instance = AgentClass()
            else:
                agent_instance = AgentClass()

            logger.info(f"Loaded code_based agent: {agent_model.name} from {class_path}")
            return agent_instance

        except Exception as e:
            logger.error(
                f"Failed to load code_based agent {agent_model.name} "
                f"from class_path {class_path}: {e}",
                exc_info=True
            )
            return None

    def _load_llm_based_agent(self, agent_model: AIAgentModel) -> DynamicAgent:
        """
        llm_basedエージェントをロード（DynamicAgent）

        Args:
            agent_model: エージェントモデル

        Returns:
            DynamicAgentインスタンス
        """
        agent = DynamicAgent(agent_model, llm_client=self.llm_client)
        logger.info(f"Loaded llm_based agent: {agent_model.name}")
        return agent

    def clear_cache(self, agent_id: Optional[str] = None) -> None:
        """
        エージェントキャッシュをクリア

        Args:
            agent_id: 指定時は特定のエージェントのみクリア、未指定時は全クリア
        """
        if agent_id:
            if agent_id in self._agent_cache:
                del self._agent_cache[agent_id]
                logger.info(f"Cleared agent cache: {agent_id}")
        else:
            self._agent_cache.clear()
            logger.info("Cleared all agent cache")

    def clear_class_cache(self, class_path: Optional[str] = None) -> None:
        """
        クラスキャッシュをクリア

        Args:
            class_path: 指定時は特定のクラスのみクリア、未指定時は全クリア
        """
        if class_path:
            if class_path in self._class_cache:
                del self._class_cache[class_path]
                logger.info(f"Cleared class cache: {class_path}")
        else:
            self._class_cache.clear()
            logger.info("Cleared all class cache")

    def get_cached_agent(
        self,
        agent_id: str
    ) -> Optional[Union[BaseAgent, DynamicAgent]]:
        """
        キャッシュからエージェントを取得

        Args:
            agent_id: エージェントID

        Returns:
            キャッシュされたエージェントインスタンス、存在しない場合はNone
        """
        return self._agent_cache.get(agent_id)

    async def reload_agent(self, agent_id: str) -> Optional[Union[BaseAgent, DynamicAgent]]:
        """
        エージェントを再ロード（キャッシュをクリアして再度ロード）

        Args:
            agent_id: エージェントID

        Returns:
            再ロードされたエージェントインスタンス
        """
        self.clear_cache(agent_id)
        return await self.load_agent_by_id(agent_id, force_reload=True)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得

        Returns:
            統計情報
        """
        return {
            "cached_agents_count": len(self._agent_cache),
            "cached_classes_count": len(self._class_cache),
            "cached_agent_ids": list(self._agent_cache.keys()),
            "cached_class_paths": list(self._class_cache.keys())
        }
