"""Rule-based decision engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class RuleResult:
    """Result of a rule evaluation."""

    rule_name: str
    triggered: bool
    action: str
    priority: str = "normal"


class RuleEngine:
    """Evaluates rules against game state.

    Rules are defined in YAML configs or derived from skills.
    Conditions are simple expressions like:
        - "enemy_visible == false"
        - "enemy_count > 0"
    """

    def evaluate_rules(
        self, rules: list[dict[str, Any]], state: dict[str, Any]
    ) -> list[RuleResult]:
        """Evaluate a list of rules against the current state.

        Args:
            rules: List of rule dictionaries from config.
            state: Current game state as a flat dictionary.

        Returns:
            List of RuleResult for triggered rules.
        """
        results: list[RuleResult] = []

        for rule in rules:
            name = rule.get("name", "unnamed")
            condition = rule.get("condition", "")
            action = rule.get("action", "")
            priority = rule.get("priority", "normal")

            if self._evaluate_condition(condition, state):
                results.append(
                    RuleResult(
                        rule_name=name,
                        triggered=True,
                        action=action,
                        priority=priority,
                    )
                )

        return results

    def evaluate_skill_conditions(
        self, conditions: list[str], state: dict[str, Any]
    ) -> bool:
        """Evaluate skill conditions (all must be true).

        Args:
            conditions: List of condition expressions.
            state: Current game state dictionary.

        Returns:
            True if all conditions are met.
        """
        if not conditions:
            return False

        return all(
            self._evaluate_condition(cond, state) for cond in conditions
        )

    def _evaluate_condition(self, condition: str, state: dict[str, Any]) -> bool:
        """Evaluate a single condition expression.

        Supports: ==, !=, >, <, >=, <=
        Values: true, false, numbers, strings
        """
        condition = condition.strip()
        if not condition:
            return False

        # Parse the condition
        operators = ["==", "!=", ">=", "<=", ">", "<"]
        for op in operators:
            if op in condition:
                parts = condition.split(op, 1)
                if len(parts) == 2:
                    left_key = parts[0].strip()
                    right_value = parts[1].strip()

                    left = state.get(left_key)
                    right = self._parse_value(right_value)

                    return self._compare(left, right, op)

        return False

    @staticmethod
    def _parse_value(value_str: str) -> Any:
        """Parse a string value into its Python type."""
        value_str = value_str.strip().strip('"').strip("'")

        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        try:
            return int(value_str)
        except ValueError:
            pass

        try:
            return float(value_str)
        except ValueError:
            pass

        return value_str

    @staticmethod
    def _compare(left: Any, right: Any, op: str) -> bool:
        """Compare two values with the given operator."""
        if left is None:
            return False

        try:
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == ">":
                return left > right
            if op == "<":
                return left < right
            if op == ">=":
                return left >= right
            if op == "<=":
                return left <= right
        except TypeError:
            return False

        return False
