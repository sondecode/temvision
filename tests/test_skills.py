"""Tests for the skill parser and loader."""

import pytest

from temvision.skills.parser import Skill, SkillParser
from temvision.skills.loader import SkillLoader


SAMPLE_SKILL_MD = """# Enemy Missing

## Condition
- enemy_visible == false

## Action
- alert: "⚠️ Cẩn thận bị gank"
- priority: high
"""


class TestSkillParser:
    def test_parse_skill_name(self):
        parser = SkillParser()
        skill = parser.parse(SAMPLE_SKILL_MD)
        assert skill.name == "Enemy Missing"

    def test_parse_conditions(self):
        parser = SkillParser()
        skill = parser.parse(SAMPLE_SKILL_MD)
        assert len(skill.conditions) == 1
        assert "enemy_visible == false" in skill.conditions

    def test_parse_actions(self):
        parser = SkillParser()
        skill = parser.parse(SAMPLE_SKILL_MD)
        assert len(skill.actions) == 2
        assert {"alert": "⚠️ Cẩn thận bị gank"} in skill.actions

    def test_parse_priority(self):
        parser = SkillParser()
        skill = parser.parse(SAMPLE_SKILL_MD)
        assert skill.priority == "high"

    def test_parse_empty_content(self):
        parser = SkillParser()
        skill = parser.parse("")
        assert skill.name == ""
        assert skill.conditions == []
        assert skill.actions == []

    def test_parse_source_file(self):
        parser = SkillParser()
        skill = parser.parse(SAMPLE_SKILL_MD, source_file="test.md")
        assert skill.source_file == "test.md"

    def test_parse_multiple_conditions(self):
        content = """# Multi Condition

## Condition
- enemy_visible == false
- health > 50

## Action
- alert: "Safe to engage"
"""
        parser = SkillParser()
        skill = parser.parse(content)
        assert len(skill.conditions) == 2

    def test_parse_no_actions(self):
        content = """# No Actions

## Condition
- something == true
"""
        parser = SkillParser()
        skill = parser.parse(content)
        assert skill.conditions == ["something == true"]
        assert skill.actions == []


class TestSkillLoader:
    def test_load_all_from_directory(self, tmp_path):
        skill_file = tmp_path / "test_skill.md"
        skill_file.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

        loader = SkillLoader(str(tmp_path))
        skills = loader.load_all()
        assert len(skills) == 1
        assert skills[0].name == "Enemy Missing"

    def test_load_empty_directory(self, tmp_path):
        loader = SkillLoader(str(tmp_path))
        skills = loader.load_all()
        assert skills == []

    def test_load_nonexistent_directory(self):
        loader = SkillLoader("/nonexistent/path")
        skills = loader.load_all()
        assert skills == []

    def test_load_single_file(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

        loader = SkillLoader(str(tmp_path))
        skill = loader.load_file(str(skill_file))
        assert skill is not None
        assert skill.name == "Enemy Missing"

    def test_load_missing_file(self):
        loader = SkillLoader(".")
        skill = loader.load_file("/nonexistent/file.md")
        assert skill is None

    def test_ignores_non_md_files(self, tmp_path):
        (tmp_path / "note.txt").write_text("not a skill")
        (tmp_path / "skill.md").write_text(SAMPLE_SKILL_MD, encoding="utf-8")

        loader = SkillLoader(str(tmp_path))
        skills = loader.load_all()
        assert len(skills) == 1


class TestLoLGuideSkill:
    """Tests for the League of Legends guide skill file."""

    def test_lol_guide_parses(self):
        loader = SkillLoader("skills")
        skill = loader.load_file("skills/lol_guide.md")
        assert skill is not None
        assert skill.name == "League of Legends - Hướng Dẫn Toàn Diện"

    def test_lol_guide_has_conditions(self):
        parser = SkillParser()
        with open("skills/lol_guide.md", "r", encoding="utf-8") as f:
            skill = parser.parse(f.read())
        assert len(skill.conditions) >= 1
        assert "game == lol" in skill.conditions

    def test_lol_guide_has_actions(self):
        parser = SkillParser()
        with open("skills/lol_guide.md", "r", encoding="utf-8") as f:
            skill = parser.parse(f.read())
        assert len(skill.actions) >= 1

    def test_lol_guide_content_has_key_sections(self):
        with open("skills/lol_guide.md", "r", encoding="utf-8") as f:
            content = f.read()
        assert "## Hướng Dẫn Lên Đồ" in content
        assert "## Khắc Chế Theo Meta Game" in content
        assert "## Xem Lịch Sử Đối Thủ" in content
        assert "## Meta Cấm Chọn" in content


class TestTFTGuideSkill:
    """Tests for the Teamfight Tactics guide skill file."""

    def test_tft_guide_parses(self):
        loader = SkillLoader("skills")
        skill = loader.load_file("skills/tft_guide.md")
        assert skill is not None
        assert skill.name == "Teamfight Tactics - Hướng Dẫn Toàn Diện"

    def test_tft_guide_has_conditions(self):
        parser = SkillParser()
        with open("skills/tft_guide.md", "r", encoding="utf-8") as f:
            skill = parser.parse(f.read())
        assert len(skill.conditions) >= 1
        assert "game == tft" in skill.conditions

    def test_tft_guide_has_actions(self):
        parser = SkillParser()
        with open("skills/tft_guide.md", "r", encoding="utf-8") as f:
            skill = parser.parse(f.read())
        assert len(skill.actions) >= 1

    def test_tft_guide_content_has_key_sections(self):
        with open("skills/tft_guide.md", "r", encoding="utf-8") as f:
            content = f.read()
        assert "## Hướng Dẫn Lên Đồ" in content
        assert "## Augment Tier List" in content
        assert "## Xem Lịch Sử" in content
        assert "## Economy" in content


class TestAllSkillsLoader:
    """Tests that all skill files load together correctly."""

    def test_loads_all_three_skills(self):
        loader = SkillLoader("skills")
        skills = loader.load_all()
        assert len(skills) == 3
        names = [s.name for s in skills]
        assert "Enemy Missing" in names
        assert "League of Legends - Hướng Dẫn Toàn Diện" in names
        assert "Teamfight Tactics - Hướng Dẫn Toàn Diện" in names
