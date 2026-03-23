"""Tests for LLM integrations."""

import pytest

from temvision.llm.base import BaseLLM
from temvision.llm.openai_llm import OpenAILLM
from temvision.llm.claude_llm import ClaudeLLM
from temvision.llm.gemini_llm import GeminiLLM


class TestOpenAILLM:
    def test_not_available_without_key(self):
        llm = OpenAILLM(api_key="")
        assert llm.is_available() is False

    def test_available_with_key(self):
        llm = OpenAILLM(api_key="test-key")
        assert llm.is_available() is True

    def test_complete_without_key_returns_empty(self):
        llm = OpenAILLM(api_key="")
        assert llm.complete("test") == ""


class TestClaudeLLM:
    def test_not_available_without_key(self):
        llm = ClaudeLLM(api_key="")
        assert llm.is_available() is False

    def test_available_with_key(self):
        llm = ClaudeLLM(api_key="test-key")
        assert llm.is_available() is True

    def test_complete_without_key_returns_empty(self):
        llm = ClaudeLLM(api_key="")
        assert llm.complete("test") == ""


class TestGeminiLLM:
    def test_not_available_without_key(self):
        llm = GeminiLLM(api_key="")
        assert llm.is_available() is False

    def test_available_with_key(self):
        llm = GeminiLLM(api_key="test-key")
        assert llm.is_available() is True

    def test_complete_without_key_returns_empty(self):
        llm = GeminiLLM(api_key="")
        assert llm.complete("test") == ""
