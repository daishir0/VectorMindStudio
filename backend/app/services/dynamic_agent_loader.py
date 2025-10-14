"""
Dynamic Agent Loader - DBからエージェント設定を読み込んで動的にエージェントを生成
"""
from typing import Dict, Any, Optional, List
import logging
from app.services.agents.base_agent import BaseAgent, AgentTask
from app.infrastructure.database.models import AIAgentModel

logger = logging.getLogger(__name__)


class DynamicAgent(BaseAgent):
    """
    動的に生成されたエージェント

    DBから読み込んだ設定を元にLLMベースで動作する汎用エージェント
    """

    def __init__(
        self,
        agent_model: AIAgentModel,
        llm_client: Any = None  # OpenAI clientなど
    ):
        super().__init__(
            name=agent_model.name,
            description=agent_model.description,
            max_retries=agent_model.max_retries,
            timeout=agent_model.timeout_seconds
        )

        self.agent_id = agent_model.id
        self.display_name = agent_model.display_name
        self.category = agent_model.category
        self.executor_type = agent_model.executor_type
        self.llm_model = agent_model.llm_model
        self.system_prompt = agent_model.system_prompt
        self.user_prompt_template = agent_model.user_prompt_template
        self.response_format = agent_model.response_format
        self.tags = agent_model.tags or []
        self.agent_metadata = agent_model.agent_metadata or {}

        self.llm_client = llm_client

        # 能力情報（relationshipから取得）
        self.capabilities = agent_model.capabilities if hasattr(agent_model, 'capabilities') else []

    async def _execute_core(self, task: AgentTask) -> Any:
        """
        コア実行ロジック（LLMベース）

        Args:
            task: 実行タスク

        Returns:
            LLM生成結果
        """
        if self.executor_type == "llm_based":
            return await self._execute_llm_based(task)
        elif self.executor_type == "rule_based":
            return await self._execute_rule_based(task)
        else:
            raise ValueError(f"Unknown executor_type: {self.executor_type}")

    async def _execute_llm_based(self, task: AgentTask) -> Any:
        """LLMベースのタスク実行"""
        # ユーザープロンプトをテンプレートから生成
        user_prompt = self._render_user_prompt(task.parameters)

        # LLM APIを呼び出し
        if self.llm_client is None:
            # LLM clientがない場合はスタブレスポンス
            logger.warning(f"{self.name}: LLM client not configured, returning stub response")
            return {
                "content": f"[Stub Response] エージェント {self.display_name} がタスクを処理しました。",
                "model": self.llm_model,
                "usage": {"total_tokens": 0}
            }

        try:
            # OpenAI API呼び出し
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=task.parameters.get("temperature", 0.7),
                max_tokens=task.parameters.get("max_tokens", 2000)
            )

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            logger.error(f"{self.name}: LLM API call failed: {e}")
            raise

    async def _execute_rule_based(self, task: AgentTask) -> Any:
        """ルールベースのタスク実行（将来拡張用）"""
        # ルールベースのロジックを実装
        # 例: 事前定義されたルールに基づいて処理
        raise NotImplementedError("Rule-based execution not yet implemented")

    def _render_user_prompt(self, parameters: Dict[str, Any]) -> str:
        """
        ユーザープロンプトテンプレートをレンダリング

        Args:
            parameters: テンプレート変数

        Returns:
            レンダリング済みプロンプト
        """
        prompt = self.user_prompt_template

        # 単純な変数置換（{variable_name}形式）
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt

    def _get_supported_task_types(self) -> List[str]:
        """サポートするタスクタイプのリスト"""
        # capabilitiesから取得
        task_types = set()
        for capability in self.capabilities:
            if hasattr(capability, 'supported_task_types'):
                task_types.update(capability.supported_task_types or [])

        return list(task_types) if task_types else ["general"]


class DynamicAgentLoader:
    """
    動的エージェントローダー

    AgentRepositoryからエージェント設定を読み込み、
    DynamicAgentインスタンスを生成・管理する
    """

    def __init__(self, agent_repository, llm_client: Any = None):
        self.agent_repository = agent_repository
        self.llm_client = llm_client
        self._agent_cache: Dict[str, DynamicAgent] = {}

    async def load_agent_by_id(self, agent_id: str) -> Optional[DynamicAgent]:
        """
        IDでエージェントをロード

        Args:
            agent_id: エージェントID

        Returns:
            DynamicAgentインスタンス、存在しない場合はNone
        """
        # キャッシュ確認
        if agent_id in self._agent_cache:
            return self._agent_cache[agent_id]

        # DBから取得
        agent_model = await self.agent_repository.get_agent_by_id(agent_id)
        if agent_model is None:
            logger.warning(f"Agent not found: {agent_id}")
            return None

        # DynamicAgentインスタンス生成
        agent = DynamicAgent(agent_model, llm_client=self.llm_client)

        # キャッシュ
        self._agent_cache[agent_id] = agent

        logger.info(f"Loaded agent: {agent.name} ({agent_id})")
        return agent

    async def load_agent_by_name(self, agent_name: str) -> Optional[DynamicAgent]:
        """
        名前でエージェントをロード

        Args:
            agent_name: エージェント名

        Returns:
            DynamicAgentインスタンス、存在しない場合はNone
        """
        # DBから取得
        agent_model = await self.agent_repository.get_agent_by_name(agent_name)
        if agent_model is None:
            logger.warning(f"Agent not found: {agent_name}")
            return None

        # キャッシュ確認
        if agent_model.id in self._agent_cache:
            return self._agent_cache[agent_model.id]

        # DynamicAgentインスタンス生成
        agent = DynamicAgent(agent_model, llm_client=self.llm_client)

        # キャッシュ
        self._agent_cache[agent_model.id] = agent

        logger.info(f"Loaded agent: {agent.name} ({agent_model.id})")
        return agent

    async def load_all_active_agents(self, user_id: Optional[str] = None) -> List[DynamicAgent]:
        """
        アクティブなエージェント一覧をロード

        Args:
            user_id: ユーザーID（指定時はユーザー固有エージェントも含む）

        Returns:
            DynamicAgentインスタンスリスト
        """
        agent_models = await self.agent_repository.get_active_agents(user_id=user_id)

        agents = []
        for agent_model in agent_models:
            # キャッシュ確認
            if agent_model.id in self._agent_cache:
                agents.append(self._agent_cache[agent_model.id])
            else:
                # 新規生成
                agent = DynamicAgent(agent_model, llm_client=self.llm_client)
                self._agent_cache[agent_model.id] = agent
                agents.append(agent)

        logger.info(f"Loaded {len(agents)} active agents")
        return agents

    def clear_cache(self) -> None:
        """エージェントキャッシュをクリア"""
        self._agent_cache.clear()
        logger.info("Agent cache cleared")

    def get_cached_agent(self, agent_id: str) -> Optional[DynamicAgent]:
        """キャッシュからエージェントを取得"""
        return self._agent_cache.get(agent_id)
