"""Google Gemini LLM integration."""

from __future__ import annotations

import os

from temvision.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    """Google Gemini integration."""

    def __init__(
        self, model: str = "gemini-pro", api_key: str | None = None
    ) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")

    def complete(self, prompt: str) -> str:
        """Send a prompt to Gemini and get a completion."""
        if not self.is_available():
            return ""

        try:
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model)
            response = model.generate_content(prompt)
            return response.text if response.text else ""
        except Exception:
            return ""

    def is_available(self) -> bool:
        """Check if Google API key is configured."""
        return bool(self._api_key)
