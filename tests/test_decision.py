"""Tests for the decision engine and rule engine."""

import pytest

from temvision.decision.rules import RuleEngine, RuleResult
from temvision.decision.engine import Decision, DecisionEngine
from temvision.skills.parser import Skill


class TestRuleEngine:
    def test_evaluate_true_condition(self):
        engine = RuleEngine()
        rules = [
            {
                "name": "test_rule",
                "condition": "enemy_visible == false",
                "action": "⚠️ Enemy missing",
                "priority": "high",
            }
        ]
        state = {"enemy_visible": False}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 1
        assert results[0].triggered is True
        assert results[0].action == "⚠️ Enemy missing"

    def test_evaluate_false_condition(self):
        engine = RuleEngine()
        rules = [
            {
                "name": "test_rule",
                "condition": "enemy_visible == false",
                "action": "alert",
            }
        ]
        state = {"enemy_visible": True}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 0

    def test_evaluate_numeric_comparison(self):
        engine = RuleEngine()
        rules = [
            {
                "name": "low_health",
                "condition": "health < 30",
                "action": "⚠️ Low health",
            }
        ]
        state = {"health": 20}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 1

    def test_evaluate_greater_than(self):
        engine = RuleEngine()
        rules = [
            {
                "name": "many_enemies",
                "condition": "enemy_count > 3",
                "action": "Back off",
            }
        ]
        state = {"enemy_count": 5}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 1

    def test_evaluate_missing_state_key(self):
        engine = RuleEngine()
        rules = [
            {
                "name": "test",
                "condition": "nonexistent == true",
                "action": "alert",
            }
        ]
        state = {}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 0

    def test_evaluate_empty_condition(self):
        engine = RuleEngine()
        rules = [{"name": "test", "condition": "", "action": "alert"}]
        state = {"x": 1}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 0

    def test_evaluate_not_equal(self):
        engine = RuleEngine()
        rules = [
            {
                "name": "test",
                "condition": "status != dead",
                "action": "alive",
            }
        ]
        state = {"status": "alive"}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 1

    def test_skill_conditions_all_true(self):
        engine = RuleEngine()
        conditions = ["enemy_visible == false", "health > 50"]
        state = {"enemy_visible": False, "health": 80}
        assert engine.evaluate_skill_conditions(conditions, state) is True

    def test_skill_conditions_one_false(self):
        engine = RuleEngine()
        conditions = ["enemy_visible == false", "health > 50"]
        state = {"enemy_visible": False, "health": 30}
        assert engine.evaluate_skill_conditions(conditions, state) is False

    def test_skill_conditions_empty(self):
        engine = RuleEngine()
        assert engine.evaluate_skill_conditions([], {}) is False

    def test_multiple_rules(self):
        engine = RuleEngine()
        rules = [
            {"name": "r1", "condition": "a == true", "action": "a1"},
            {"name": "r2", "condition": "b == true", "action": "a2"},
            {"name": "r3", "condition": "c == true", "action": "a3"},
        ]
        state = {"a": True, "b": False, "c": True}
        results = engine.evaluate_rules(rules, state)
        assert len(results) == 2
        actions = [r.action for r in results]
        assert "a1" in actions
        assert "a3" in actions


class TestDecisionEngine:
    def test_decide_with_rules(self):
        engine = DecisionEngine()
        rules = [
            {
                "name": "test",
                "condition": "enemy_visible == false",
                "action": "⚠️ Enemy missing",
                "priority": "high",
            }
        ]
        state = {"enemy_visible": False}
        decisions = engine.decide(state, rules)
        assert len(decisions) == 1
        assert decisions[0].action == "⚠️ Enemy missing"
        assert decisions[0].source == "rule"

    def test_decide_with_skills(self):
        engine = DecisionEngine()
        skill = Skill(
            name="Test Skill",
            conditions=["enemy_visible == false"],
            actions=[{"alert": "Gank warning"}],
            priority="high",
        )
        engine.set_skills([skill])
        state = {"enemy_visible": False}
        decisions = engine.decide(state, [])
        assert len(decisions) == 1
        assert decisions[0].action == "Gank warning"
        assert decisions[0].source == "skill"

    def test_decide_priority_sorting(self):
        engine = DecisionEngine()
        rules = [
            {"name": "low", "condition": "a == true", "action": "low", "priority": "low"},
            {"name": "high", "condition": "a == true", "action": "high", "priority": "high"},
            {"name": "critical", "condition": "a == true", "action": "critical", "priority": "critical"},
        ]
        state = {"a": True}
        decisions = engine.decide(state, rules)
        assert len(decisions) == 3
        assert decisions[0].priority == "critical"
        assert decisions[1].priority == "high"
        assert decisions[2].priority == "low"

    def test_decide_no_matches(self):
        engine = DecisionEngine()
        rules = [
            {"name": "test", "condition": "x == true", "action": "alert"}
        ]
        state = {"x": False}
        decisions = engine.decide(state, rules)
        assert len(decisions) == 0

    def test_decide_without_llm(self):
        engine = DecisionEngine()
        state = {"enemy_visible": False}
        decisions = engine.decide(state, [], use_llm=True)
        assert len(decisions) == 0  # No LLM configured
