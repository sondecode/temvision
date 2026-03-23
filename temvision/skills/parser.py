"""Markdown skill parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    """Represents a parsed skill from a .md file."""

    name: str = ""
    conditions: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    priority: str = "normal"
    source_file: str = ""


class SkillParser:
    """Parses skill definitions from Markdown files.

    Skill format:
        # Skill Name

        ## Condition
        - condition_expression

        ## Action
        - alert: "message"
        - priority: high
    """

    def parse(self, content: str, source_file: str = "") -> Skill:
        """Parse a skill from markdown content.

        Args:
            content: Markdown content of the skill file.
            source_file: Path to the source file (for reference).

        Returns:
            Parsed Skill object.
        """
        skill = Skill(source_file=source_file)

        # Extract skill name from H1 heading
        name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if name_match:
            skill.name = name_match.group(1).strip()

        # Extract sections
        sections = self._extract_sections(content)

        # Parse conditions
        if "Condition" in sections:
            skill.conditions = self._parse_list_items(sections["Condition"])

        # Parse actions
        if "Action" in sections:
            skill.actions = self._parse_action_items(sections["Action"])

        # Extract priority from actions if present
        for action in skill.actions:
            if "priority" in action:
                skill.priority = action["priority"]

        return skill

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract H2 sections from markdown content."""
        sections: dict[str, str] = {}
        current_section: str | None = None
        current_content: list[str] = []

        for line in content.split("\n"):
            h2_match = re.match(r"^##\s+(.+)$", line)
            if h2_match:
                if current_section is not None:
                    sections[current_section] = "\n".join(current_content)
                current_section = h2_match.group(1).strip()
                current_content = []
            elif current_section is not None:
                current_content.append(line)

        if current_section is not None:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _parse_list_items(self, section_content: str) -> list[str]:
        """Parse list items from a section."""
        items: list[str] = []
        for line in section_content.split("\n"):
            match = re.match(r"^\s*-\s+(.+)$", line)
            if match:
                items.append(match.group(1).strip())
        return items

    def _parse_action_items(self, section_content: str) -> list[dict[str, str]]:
        """Parse action items (key: value pairs) from a section."""
        actions: list[dict[str, str]] = []
        for line in section_content.split("\n"):
            match = re.match(r'^\s*-\s+(\w+):\s*"?([^"]*)"?\s*$', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                actions.append({key: value})
        return actions
