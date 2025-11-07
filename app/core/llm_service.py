"""
LLM orchestration service.
Handles calling different LLM APIs (OpenAI, Anthropic, DeepSeek) for trading decisions.
"""

import json
import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import asyncio

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from .schemas import LLMDecision


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def get_trading_decision(
        self,
        system_prompt: str,
        market_data: str,
        account_state: str,
    ) -> LLMDecision:
        """Get trading decision from LLM"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4, GPT-4-mini, etc)"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    async def get_trading_decision(
        self,
        system_prompt: str,
        market_data: str,
        account_state: str,
        model: str = "gpt-4-mini",
    ) -> LLMDecision:
        """Get trading decision from OpenAI"""
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Current Market Data:
{market_data}

Account State:
{account_state}

Based on the above, what is your trading decision? Respond with valid JSON only.""",
            },
        ]

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        raw_response = response.choices[0].message.content
        return self._parse_response(raw_response)

    def _parse_response(self, response_text: str) -> LLMDecision:
        """Parse LLM response into structured decision"""
        try:
            # Extract JSON from response
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            return LLMDecision(
                action=data.get("action", "hold").lower(),
                ticker=data.get("ticker"),
                quantity=data.get("quantity"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                raw_response=response_text,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback to hold if parsing fails
            return LLMDecision(
                action="hold",
                confidence=0.0,
                reasoning=f"Failed to parse response: {str(e)}",
                raw_response=response_text,
            )


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude models)"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncAnthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    async def get_trading_decision(
        self,
        system_prompt: str,
        market_data: str,
        account_state: str,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> LLMDecision:
        """Get trading decision from Claude"""
        user_message = f"""Current Market Data:
{market_data}

Account State:
{account_state}

Based on the above, what is your trading decision? Respond with valid JSON only."""

        response = await self.client.messages.create(
            model=model,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_response = response.content[0].text
        return self._parse_response(raw_response)

    def _parse_response(self, response_text: str) -> LLMDecision:
        """Parse LLM response into structured decision"""
        try:
            # Extract JSON from response
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            return LLMDecision(
                action=data.get("action", "hold").lower(),
                ticker=data.get("ticker"),
                quantity=data.get("quantity"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                raw_response=response_text,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback to hold if parsing fails
            return LLMDecision(
                action="hold",
                confidence=0.0,
                reasoning=f"Failed to parse response: {str(e)}",
                raw_response=response_text,
            )


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider (OpenAI-compatible)"""

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )

    async def get_trading_decision(
        self,
        system_prompt: str,
        market_data: str,
        account_state: str,
        model: str = "deepseek-chat",
    ) -> LLMDecision:
        """Get trading decision from DeepSeek"""
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""Current Market Data:
{market_data}

Account State:
{account_state}

Based on the above, what is your trading decision? Respond with valid JSON only.""",
            },
        ]

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        raw_response = response.choices[0].message.content
        return self._parse_response(raw_response)

    def _parse_response(self, response_text: str) -> LLMDecision:
        """Parse LLM response into structured decision"""
        try:
            # Extract JSON from response
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            return LLMDecision(
                action=data.get("action", "hold").lower(),
                ticker=data.get("ticker"),
                quantity=data.get("quantity"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                raw_response=response_text,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback to hold if parsing fails
            return LLMDecision(
                action="hold",
                confidence=0.0,
                reasoning=f"Failed to parse response: {str(e)}",
                raw_response=response_text,
            )


class LLMOrchestrator:
    """Orchestrates LLM calls across different providers"""

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "deepseek": DeepSeekProvider(),
        }

    async def get_decision(
        self,
        model_name: str,
        system_prompt: str,
        market_data: str,
        account_state: str,
    ) -> LLMDecision:
        """
        Get trading decision from specified LLM model.

        Args:
            model_name: Full model identifier (e.g., 'gpt-4-mini', 'claude-3-haiku')
            system_prompt: System prompt for the agent
            market_data: Current market data
            account_state: Current account state

        Returns:
            LLMDecision from the model
        """
        # Determine provider and model from model_name
        if model_name.startswith("gpt-"):
            provider = self.providers["openai"]
            model = model_name
        elif model_name.startswith("claude-"):
            provider = self.providers["anthropic"]
            # Map short names to full model IDs
            model_map = {
                "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
                "claude-3-haiku": "claude-3-haiku-20240307",
            }
            model = model_map.get(model_name, model_name)
        elif model_name.startswith("deepseek-"):
            provider = self.providers["deepseek"]
            model = model_name
        else:
            raise ValueError(f"Unknown model: {model_name}")

        return await provider.get_trading_decision(
            system_prompt=system_prompt,
            market_data=market_data,
            account_state=account_state,
            model=model,
        )

    async def get_decisions_parallel(
        self,
        decisions_config: list[Dict[str, Any]],
    ) -> Dict[int, LLMDecision]:
        """
        Get decisions from multiple agents in parallel.

        Args:
            decisions_config: List of dicts with keys:
                - agent_id: int
                - model_name: str
                - system_prompt: str
                - market_data: str
                - account_state: str

        Returns:
            Dict mapping agent_id to LLMDecision
        """
        tasks = []
        agent_ids = []

        for config in decisions_config:
            agent_ids.append(config["agent_id"])
            task = self.get_decision(
                model_name=config["model_name"],
                system_prompt=config["system_prompt"],
                market_data=config["market_data"],
                account_state=config["account_state"],
            )
            tasks.append(task)

        # Run all decisions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        decisions = {}
        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                # Fallback to hold on error
                decisions[agent_id] = LLMDecision(
                    action="hold",
                    confidence=0.0,
                    reasoning=f"Error getting decision: {str(result)}",
                )
            else:
                decisions[agent_id] = result

        return decisions
