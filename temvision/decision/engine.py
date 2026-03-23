"""Main decision engine combining rules and LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from temvision.decision.rules import RuleEngine, RuleResult
from temvision.llm.base import BaseLLM
from temvision.skills.parser import Skill


@dataclass
class Decision:
    """Represents a decision made by the engine."""

    action: str
    source: str  # "rule", "skill", or "llm"
    priority: str = "normal"
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """Main decision engine that combines rule-based and LLM reasoning.

    Priority order:
    1. Config rules (fast, offline)
    2. Skill-based rules (fast, offline)
    3. LLM reasoning (advanced, requires API)
    """

    def __init__(self, llm: BaseLLM | None = None) -> None:
        self._rule_engine = RuleEngine()
        self._llm = llm
        self._skills: list[Skill] = []

    def set_skills(self, skills: list[Skill]) -> None:
        """Set the active skills."""
        self._skills = list(skills)

    def set_llm(self, llm: BaseLLM) -> None:
        """Set the LLM backend."""
        self._llm = llm

    def decide(
        self,
        state: dict[str, Any],
        rules: list[dict[str, Any]],
        use_llm: bool = False,
    ) -> list[Decision]:
        """Make decisions based on the current game state.

        Args:
            state: Current game state as a flat dictionary.
            rules: List of rule dictionaries from config.
            use_llm: Whether to also consult the LLM.

        Returns:
            List of Decision objects, sorted by priority.
        """
        decisions: list[Decision] = []

        # 1. Evaluate config rules
        rule_results = self._rule_engine.evaluate_rules(rules, state)
        for result in rule_results:
            decisions.append(
                Decision(
                    action=result.action,
                    source="rule",
                    priority=result.priority,
                )
            )

        # 2. Evaluate skill conditions
        for skill in self._skills:
            if self._rule_engine.evaluate_skill_conditions(
                skill.conditions, state
            ):
                for action_dict in skill.actions:
                    for key, value in action_dict.items():
                        if key == "alert":
                            decisions.append(
                                Decision(
                                    action=value,
                                    source="skill",
                                    priority=skill.priority,
                                    metadata={"skill": skill.name},
                                )
                            )

        # 3. LLM reasoning (optional)
        if use_llm and self._llm is not None:
            llm_decision = self._get_llm_decision(state)
            if llm_decision is not None:
                decisions.append(llm_decision)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        decisions.sort(key=lambda d: priority_order.get(d.priority, 2))

        return decisions

    def _get_llm_decision(self, state: dict[str, Any]) -> Decision | None:
        """Get a decision from the LLM based on game state."""
        if self._llm is None:
            return None

        prompt = self._build_llm_prompt(state)
        response = self._llm.complete(prompt)

        if response:
            return Decision(
                action=response,
                source="llm",
                priority="normal",
                confidence=0.8,
            )

        return None

    @staticmethod
    def _build_llm_prompt(state: dict[str, Any]) -> str:
        """Build a prompt for the LLM based on game state."""
        state_lines = [f"- {k}: {v}" for k, v in state.items()]
        state_str = "\n".join(state_lines)

        return (
            "You are an AI game coach. Based on the current game state, "
            "provide a brief tactical decision.\n\n"
            f"Game State:\n{state_str}\n\n"
            "Decision (one short sentence):"
        )
