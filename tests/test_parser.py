"""Tests for configuration parsing."""

import pytest

from timeline_generator.parser import (
    parse_yaml,
    parse_json,
    parse_toon,
    parse_quick_milestones,
    create_config_from_quick,
    ParserError,
)
from timeline_generator.models import TimelineStyle, ThemeName, OutputFormat


class TestYAMLParser:
    """Tests for YAML parsing."""

    def test_parse_valid_yaml(self, sample_yaml_config):
        """Test parsing valid YAML configuration."""
        config = parse_yaml(sample_yaml_config)
        assert config.title == "Test Timeline"
        assert config.subtitle == "Testing YAML parsing"
        assert config.theme == ThemeName.CORPORATE
        assert len(config.milestones) == 2

    def test_parse_minimal_yaml(self):
        """Test parsing minimal YAML with only required fields."""
        yaml_str = """
milestones:
  - date: "2024-01-01"
    title: "Start"
"""
        config = parse_yaml(yaml_str)
        assert len(config.milestones) == 1
        assert config.milestones[0].title == "Start"

    def test_parse_invalid_yaml(self):
        """Test that invalid YAML raises ParserError."""
        with pytest.raises(ParserError):
            parse_yaml("invalid: yaml: content: [")

    def test_parse_yaml_with_colors(self):
        """Test parsing YAML with custom colors."""
        yaml_str = """
title: "Colored Timeline"
milestones:
  - date: "2024-01-01"
    title: "Start"
colors:
  accent: "#FF5733"
  background: "#FFFFFF"
"""
        config = parse_yaml(yaml_str)
        assert config.colors is not None
        assert config.colors.accent == "#FF5733"

    def test_parse_yaml_with_transparent(self):
        """Test parsing YAML with transparent output."""
        yaml_str = """
title: "Transparent Timeline"
milestones:
  - date: "2024-01-01"
    title: "Start"
output:
  format: png
  transparent: true
"""
        config = parse_yaml(yaml_str)
        assert config.output.transparent is True


class TestJSONParser:
    """Tests for JSON parsing."""

    def test_parse_valid_json(self, sample_json_config):
        """Test parsing valid JSON configuration."""
        config = parse_json(sample_json_config)
        assert config.title == "Test Timeline"
        assert len(config.milestones) == 2

    def test_parse_invalid_json(self):
        """Test that invalid JSON raises ParserError."""
        with pytest.raises(ParserError):
            parse_json("{invalid json}")


class TestTOONParser:
    """Tests for TOON (Token-Oriented Object Notation) parsing."""

    def test_parse_simple_toon(self):
        """Test parsing simple TOON key-value pairs."""
        toon_str = """
title: Test Timeline
style: horizontal
theme: corporate
milestones[1]: date title
2024-01-01 Start
"""
        config = parse_toon(toon_str)
        assert config.title == "Test Timeline"
        assert config.style == TimelineStyle.HORIZONTAL
        assert config.theme == ThemeName.CORPORATE

    def test_parse_tabular_milestones(self):
        """Test parsing tabular array format."""
        toon_str = """
title: Timeline
milestones[3]: date title description highlight
2024-01-15 Kickoff "Project begins" true
2024-06-01 Launch "Go live" false
2024-12-01 Review "Year end" false
"""
        config = parse_toon(toon_str)
        assert len(config.milestones) == 3
        assert config.milestones[0].title == "Kickoff"
        assert config.milestones[0].description == "Project begins"
        assert config.milestones[0].highlight is True
        assert config.milestones[1].highlight is False

    def test_parse_quoted_strings(self):
        """Test parsing quoted strings with spaces."""
        toon_str = """
title: "My Project Timeline"
subtitle: "With multiple words"
milestones[1]: date title
2024-01-01 "Multi Word Title"
"""
        config = parse_toon(toon_str)
        assert config.title == "My Project Timeline"
        assert config.subtitle == "With multiple words"
        assert config.milestones[0].title == "Multi Word Title"

    def test_parse_nested_output(self):
        """Test parsing nested object (output config)."""
        toon_str = """
title: Timeline
milestones[1]: date title
2024-01-01 Start
output:
  format: png
  width: 1920
  height: 800
"""
        config = parse_toon(toon_str)
        assert config.output.format == OutputFormat.PNG
        assert config.output.width == 1920
        assert config.output.height == 800

    def test_parse_null_values(self):
        """Test parsing null values."""
        toon_str = """
title: Timeline
milestones[2]: date title description color
2024-01-01 Start null null
2024-06-01 End "Has desc" #FF5733
"""
        config = parse_toon(toon_str)
        assert config.milestones[0].description is None
        assert config.milestones[0].color is None
        assert config.milestones[1].description == "Has desc"
        assert config.milestones[1].color == "#FF5733"

    def test_parse_gantt_with_dates(self):
        """Test parsing Gantt-style TOON with end dates and progress."""
        toon_str = """
title: Sprint Plan
style: gantt
theme: dark
milestones[2]: date title end_date progress category
2024-01-01 Planning 2024-01-14 100 "Phase 1"
2024-01-15 Development 2024-02-28 75 "Phase 1"
output:
  format: png
  width: 1920
  height: 900
"""
        config = parse_toon(toon_str)
        assert config.style == TimelineStyle.GANTT
        assert len(config.milestones) == 2
        assert config.milestones[0].progress == 100
        assert config.milestones[1].progress == 75

    def test_parse_comments_ignored(self):
        """Test that comments at start of lines are ignored."""
        toon_str = """
# This is a comment
title: Timeline
# Another comment
milestones[1]: date title
2024-01-01 Start
"""
        config = parse_toon(toon_str)
        assert config.title == "Timeline"
        assert len(config.milestones) == 1

    def test_parse_empty_toon_raises_error(self):
        """Test that empty TOON raises ParserError."""
        with pytest.raises(ParserError):
            parse_toon("")
        with pytest.raises(ParserError):
            parse_toon("   \n\n   ")


class TestQuickMilestones:
    """Tests for quick milestone parsing."""

    def test_parse_single_milestone(self):
        """Test parsing a single milestone string."""
        milestones = parse_quick_milestones(["2024-01-15:Project Start"])
        assert len(milestones) == 1
        assert milestones[0].title == "Project Start"

    def test_parse_multiple_milestones(self):
        """Test parsing multiple milestone strings."""
        strings = [
            "2024-01-01:Start",
            "2024-06-01:Middle",
            "2024-12-01:End",
        ]
        milestones = parse_quick_milestones(strings)
        assert len(milestones) == 3

    def test_parse_invalid_milestone(self):
        """Test that invalid milestone format raises error."""
        with pytest.raises(ParserError):
            parse_quick_milestones(["no-colon-here"])

    def test_parse_with_colon_in_title(self):
        """Test milestone with colon in title."""
        milestones = parse_quick_milestones(["2024-01-01:Time: 10:00 AM"])
        assert milestones[0].title == "Time: 10:00 AM"


class TestCreateConfigFromQuick:
    """Tests for creating config from quick milestones."""

    def test_create_default_config(self):
        """Test creating config with defaults."""
        from timeline_generator.models import Milestone
        from datetime import datetime
        
        milestones = [
            Milestone(date=datetime(2024, 1, 1), title="Start"),
            Milestone(date=datetime(2024, 12, 1), title="End"),
        ]
        
        config = create_config_from_quick(milestones=milestones)
        assert config.title == "Timeline"
        assert config.style == TimelineStyle.HORIZONTAL
        assert config.output.format == OutputFormat.PNG

    def test_create_custom_config(self):
        """Test creating config with custom options."""
        from timeline_generator.models import Milestone
        from datetime import datetime
        
        milestones = [Milestone(date=datetime(2024, 1, 1), title="Start")]
        
        config = create_config_from_quick(
            milestones=milestones,
            title="Custom Title",
            style="vertical",
            theme="dark",
            output_format="gif",
            width=1280,
            height=720,
            transparent=True,
        )
        
        assert config.title == "Custom Title"
        assert config.style == TimelineStyle.VERTICAL
        assert config.theme == ThemeName.DARK
        assert config.output.format == OutputFormat.GIF
        assert config.output.transparent is True

