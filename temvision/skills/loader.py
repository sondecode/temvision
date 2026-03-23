"""Skill loader - loads skills from directory."""

from __future__ import annotations

import os

from temvision.skills.parser import Skill, SkillParser


class SkillLoader:
    """Loads skill files from a directory."""

    def __init__(self, skills_dir: str = "skills") -> None:
        self.skills_dir = skills_dir
        self._parser = SkillParser()

    def load_all(self) -> list[Skill]:
        """Load all skill files from the skills directory.

        Returns:
            List of parsed Skill objects.
        """
        skills: list[Skill] = []

        if not os.path.isdir(self.skills_dir):
            return skills

        for filename in sorted(os.listdir(self.skills_dir)):
            if filename.endswith(".md"):
                filepath = os.path.join(self.skills_dir, filename)
                skill = self.load_file(filepath)
                if skill is not None:
                    skills.append(skill)

        return skills

    def load_file(self, filepath: str) -> Skill | None:
        """Load a single skill file.

        Args:
            filepath: Path to the .md skill file.

        Returns:
            Parsed Skill object, or None on error.
        """
        if not os.path.isfile(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return self._parser.parse(content, source_file=filepath)
