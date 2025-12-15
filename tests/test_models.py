"""Tests for data models."""

import pytest
from datetime import datetime

from timeline_generator.models import (
    Milestone,
    TimelineConfig,
    OutputConfig,
    ColorConfig,
    TimeScale,
    TimelineStyle,
    ThemeName,
    OutputFormat,
    QuickMilestone,
)


class TestMilestone:
    """Tests for the Milestone model."""

    def test_basic_milestone(self):
        """Test creating a basic milestone."""
        m = Milestone(date=datetime(2024, 1, 15), title="Test")
        assert m.title == "Test"
        assert m.date == datetime(2024, 1, 15)
        assert m.description is None
        assert m.highlight is False

    def test_milestone_with_all_fields(self):
        """Test milestone with all optional fields."""
        m = Milestone(
            date=datetime(2024, 1, 15),
            title="Full Milestone",
            description="A description",
            icon="🚀",
            color="#FF5733",
            highlight=True,
            category="launch",
            end_date=datetime(2024, 2, 15),
            progress=50.0,
        )
        assert m.title == "Full Milestone"
        assert m.description == "A description"
        assert m.color == "#FF5733"
        assert m.highlight is True
        assert m.progress == 50.0

    def test_date_string_parsing(self):
        """Test that date strings are parsed correctly."""
        m = Milestone(date="2024-01-15", title="Test")
        assert m.date == datetime(2024, 1, 15)

    def test_end_date_validation(self):
        """Test that end_date must be after start date."""
        with pytest.raises(ValueError):
            Milestone(
                date=datetime(2024, 2, 15),
                title="Test",
                end_date=datetime(2024, 1, 15),  # Before start
            )

    def test_invalid_color_format(self):
        """Test that invalid color formats are rejected."""
        with pytest.raises(ValueError):
            Milestone(date=datetime(2024, 1, 15), title="Test", color="red")


class TestColorConfig:
    """Tests for the ColorConfig model."""

    def test_empty_config(self):
        """Test creating empty color config."""
        c = ColorConfig()
        assert c.background is None
        assert c.accent is None

    def test_partial_config(self):
        """Test creating partial color config."""
        c = ColorConfig(accent="#FF5733", background="#FFFFFF")
        assert c.accent == "#FF5733"
        assert c.background == "#FFFFFF"
        assert c.text is None

    def test_invalid_color(self):
        """Test that invalid colors are rejected."""
        with pytest.raises(ValueError):
            ColorConfig(accent="invalid")


class TestOutputConfig:
    """Tests for the OutputConfig model."""

    def test_default_values(self):
        """Test default output config values."""
        o = OutputConfig()
        assert o.format == OutputFormat.PNG
        assert o.width == 1920
        assert o.height == 1080
        assert o.fps == 30
        assert o.duration == 5.0
        assert o.transparent is False

    def test_custom_values(self):
        """Test custom output config."""
        o = OutputConfig(
            format=OutputFormat.GIF,
            width=1280,
            height=720,
            fps=24,
            duration=3.0,
            transparent=True,
        )
        assert o.format == OutputFormat.GIF
        assert o.width == 1280
        assert o.transparent is True


class TestTimelineConfig:
    """Tests for the TimelineConfig model."""

    def test_minimal_config(self, sample_milestones):
        """Test creating minimal timeline config."""
        config = TimelineConfig(milestones=sample_milestones)
        assert config.title == "Timeline"
        assert config.scale == TimeScale.MONTHLY
        assert config.style == TimelineStyle.HORIZONTAL
        assert len(config.milestones) == 4

    def test_milestones_sorted(self, sample_milestones):
        """Test that milestones are sorted by date."""
        # Reverse the order
        reversed_milestones = list(reversed(sample_milestones))
        config = TimelineConfig(milestones=reversed_milestones)
        
        # Should still be in chronological order
        dates = [m.date for m in config.milestones]
        assert dates == sorted(dates)

    def test_date_range(self, sample_config):
        """Test date range calculation."""
        start, end = sample_config.date_range
        assert start == datetime(2024, 1, 15)
        assert end == datetime(2024, 12, 1)

    def test_unique_categories(self, gantt_milestones):
        """Test unique categories extraction."""
        config = TimelineConfig(milestones=gantt_milestones)
        cats = config.unique_categories
        assert "planning" in cats
        assert "development" in cats
        assert "testing" in cats

    def test_custom_colors(self, sample_milestones):
        """Test config with custom colors."""
        config = TimelineConfig(
            milestones=sample_milestones,
            colors=ColorConfig(accent="#FF0000", background="#000000"),
        )
        assert config.colors.accent == "#FF0000"


class TestQuickMilestone:
    """Tests for QuickMilestone parsing."""

    def test_from_string(self):
        """Test parsing milestone from string."""
        qm = QuickMilestone.from_string("2024-01-15:Project Start")
        assert qm.date == datetime(2024, 1, 15)
        assert qm.title == "Project Start"

    def test_to_milestone(self):
        """Test converting to full milestone."""
        qm = QuickMilestone.from_string("2024-06-01:Launch")
        m = qm.to_milestone()
        assert isinstance(m, Milestone)
        assert m.title == "Launch"

    def test_invalid_format(self):
        """Test that invalid formats raise error."""
        with pytest.raises(ValueError):
            QuickMilestone.from_string("no-colon-here")

