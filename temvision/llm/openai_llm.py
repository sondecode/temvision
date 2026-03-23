"""OpenAI LLM integration."""

from __future__ import annotations

import os

from temvision.llm.base import BaseLLM


class OpenAILLM(BaseLLM):
    """OpenAI GPT integration."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def complete(self, prompt: str) -> str:
        """Send a prompt to OpenAI and get a completion."""
        if not self.is_available():
            return ""

        try:
            import openai

            client = openai.OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception:
            return ""

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self._api_key)
