"""Base LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract base class for LLM integrations."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Send a prompt and get a completion.

        Args:
            prompt: The prompt text.

        Returns:
            The model's response text.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM is configured and available."""
