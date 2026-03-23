"""Claude (Anthropic) LLM integration."""

from __future__ import annotations

import logging
import os

from temvision.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class ClaudeLLM(BaseLLM):
    """Anthropic Claude integration."""

    def __init__(
        self, model: str = "claude-3-haiku-20240307", api_key: str | None = None
    ) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def complete(self, prompt: str) -> str:
        """Send a prompt to Claude and get a completion."""
        if not self.is_available():
            return ""

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self._api_key)
            message = client.messages.create(
                model=self._model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else ""
        except Exception as e:
            logger.error("Claude completion failed: %s", e)
            return ""

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(self._api_key)
