"""
Agent generation and management service.
Handles creation of LLM agents (Model x Style combinations).
"""

from typing import List, Dict, Any
from ..core.schemas import Agent, AgentCreate
from ..core.trading_styles import TRADING_STYLES, LLM_MODELS


class AgentService:
    """Service for managing AI trading agents"""

    def __init__(self, db_client=None):
        """
        Initialize agent service.

        Args:
            db_client: Supabase or database client (optional for MVP)
        """
        self.db = db_client
        self.trading_styles = TRADING_STYLES
        self.llm_models = LLM_MODELS

    def generate_all_agents(self) -> List[Dict[str, Any]]:
        """
        Generate all agent combinations (Model x Style).
        For MVP, generates 5 models x 5 styles = 25 agents.

        Returns:
            List of agent configurations
        """
        agents = []

        for model_name, model_config in self.llm_models.items():
            for style_name, style_config in self.trading_styles.items():
                agent = {
                    "model_name": model_name,
                    "style_name": style_name,
                    "system_prompt": style_config["system_prompt"],
                    "cost_tier": model_config["cost_tier"],
                    "description": f"{style_config['description']} ({model_name})",
                }
                agents.append(agent)

        return agents

    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """
        Create a single agent in the database.

        Args:
            agent_data: Agent configuration

        Returns:
            Created agent
        """
        if not self.db:
            raise ValueError("Database client not initialized")

        # Insert into agents table
        response = await self.db.table("agents").insert({
            "model_name": agent_data.model_name,
            "style_name": agent_data.style_name,
            "system_prompt": agent_data.system_prompt,
            "cost_tier": agent_data.cost_tier,
        }).execute()

        if response.data:
            return Agent(**response.data[0])
        raise ValueError("Failed to create agent")

    async def get_agent(self, agent_id: int) -> Agent:
        """Get agent by ID"""
        if not self.db:
            raise ValueError("Database client not initialized")

        response = await self.db.table("agents").select("*").eq("id", agent_id).single().execute()
        return Agent(**response.data)

    async def list_agents(self, limit: int = 100) -> List[Agent]:
        """List all agents"""
        if not self.db:
            raise ValueError("Database client not initialized")

        response = await self.db.table("agents").select("*").limit(limit).execute()
        return [Agent(**row) for row in response.data]

    async def get_agents_by_cost_tier(self, cost_tier: str) -> List[Agent]:
        """Get agents filtered by cost tier"""
        if not self.db:
            raise ValueError("Database client not initialized")

        response = await self.db.table("agents").select("*").eq("cost_tier", cost_tier).execute()
        return [Agent(**row) for row in response.data]

    async def get_agent_by_model_style(self, model_name: str, style_name: str) -> Agent:
        """Get agent by model and style combination"""
        if not self.db:
            raise ValueError("Database client not initialized")

        response = (
            await self.db.table("agents")
            .select("*")
            .eq("model_name", model_name)
            .eq("style_name", style_name)
            .single()
            .execute()
        )
        return Agent(**response.data)

    def get_style_prompt(self, style_name: str) -> str:
        """Get system prompt for a trading style"""
        if style_name not in self.trading_styles:
            raise ValueError(f"Unknown style: {style_name}")
        return self.trading_styles[style_name]["system_prompt"]

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for an LLM model"""
        if model_name not in self.llm_models:
            raise ValueError(f"Unknown model: {model_name}")
        return self.llm_models[model_name]

    def validate_agent_config(self, model_name: str, style_name: str) -> bool:
        """Validate that a model and style combination exists"""
        return (
            model_name in self.llm_models
            and style_name in self.trading_styles
        )
