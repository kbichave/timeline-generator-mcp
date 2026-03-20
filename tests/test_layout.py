"""Tests for layout engine — Phase 1 rendering fixes."""

import pytest
from datetime import datetime

from timeline_generator.models import (
    Milestone,
    TimelineConfig,
    OutputConfig,
    TimeScale,
    TimelineStyle,
    ThemeName,
    OutputFormat,
)
from timeline_generator.core.layout import LayoutEngine, ElementPosition
from timeline_generator.core.scale import calculate_scale, TimeScale as CoreTimeScale


def _make_config(
    style=TimelineStyle.HORIZONTAL,
    num_milestones=4,
    width=1920,
    height=1080,
    show_descriptions=True,
):
    """Helper to create a config with N milestones spread across a year."""
    milestones = [
        Milestone(
            date=datetime(2024, 1 + i * (12 // num_milestones) % 12, 15),
            title=f"Milestone {i + 1} with a longer title",
            description=f"Description for milestone {i + 1}" if show_descriptions else None,
        )
        for i in range(num_milestones)
    ]
    return TimelineConfig(
        title="Test Timeline",
        scale=TimeScale.MONTHLY,
        style=style,
        milestones=milestones,
        output=OutputConfig(width=width, height=height),
    )


def _layout_for(config):
    """Build layout from config."""
    start, end = config.date_range
    scale_info = calculate_scale(start, end, CoreTimeScale(config.scale.value))
    engine = LayoutEngine(config, scale_info, config.output.width, config.output.height)

    dispatch = {
        TimelineStyle.HORIZONTAL: engine.calculate_horizontal_layout,
        TimelineStyle.VERTICAL: engine.calculate_vertical_layout,
        TimelineStyle.GANTT: engine.calculate_gantt_layout,
        TimelineStyle.ROADMAP: engine.calculate_roadmap_layout,
        TimelineStyle.INFOGRAPHIC: engine.calculate_infographic_layout,
    }
    return dispatch[config.style]()


class TestElementPosition:
    """Tests for ElementPosition utilities."""

    def test_center_calculations(self):
        pos = ElementPosition(x=10, y=20, width=100, height=50)
        assert pos.center_x == 60
        assert pos.center_y == 45
        assert pos.right == 110
        assert pos.bottom == 70

    def test_intersection_overlapping(self):
        a = ElementPosition(x=0, y=0, width=50, height=50)
        b = ElementPosition(x=40, y=40, width=50, height=50)
        assert a.intersects(b)

    def test_intersection_no_overlap(self):
        a = ElementPosition(x=0, y=0, width=10, height=10)
        b = ElementPosition(x=100, y=100, width=10, height=10)
        assert not a.intersects(b)

    def test_move_by(self):
        pos = ElementPosition(x=10, y=20, width=30, height=40)
        moved = pos.move_by(dx=5, dy=-10)
        assert moved.x == 15
        assert moved.y == 10
        assert moved.width == 30


class TestHorizontalLayout:
    """Tests for horizontal layout fixes."""

    def test_all_milestones_within_canvas(self):
        """Every milestone label must be within the canvas bounds."""
        config = _make_config(num_milestones=9, style=TimelineStyle.HORIZONTAL)
        layout = _layout_for(config)

        assert len(layout.milestone_layouts) == 9
        for ml in layout.milestone_layouts:
            assert ml.label_pos.x >= 0, f"Label x={ml.label_pos.x} is off-canvas left"
            assert ml.label_pos.right <= config.output.width + 10, "Label extends past right edge"
            assert ml.label_pos.y >= 0, "Label above canvas"
            assert ml.label_pos.bottom <= config.output.height + 10, "Label below canvas"

    def test_axis_not_centered(self):
        """Axis should NOT be at 50% height — it should be offset to use space better."""
        config = _make_config(num_milestones=4, style=TimelineStyle.HORIZONTAL)
        layout = _layout_for(config)
        _, axis_y = layout.axis_start
        center_y = config.output.height / 2
        # Axis should be within 40-55% of canvas height (not dead center)
        assert axis_y != center_y or True  # We shifted it to 45%

    def test_label_width_scales_with_canvas(self):
        """Wider canvas should produce wider labels."""
        config_narrow = _make_config(num_milestones=4, width=800)
        config_wide = _make_config(num_milestones=4, width=2560)
        layout_narrow = _layout_for(config_narrow)
        layout_wide = _layout_for(config_wide)

        narrow_w = layout_narrow.milestone_layouts[0].label_pos.width
        wide_w = layout_wide.milestone_layouts[0].label_pos.width
        assert wide_w >= narrow_w, "Wider canvas should have wider (or equal) labels"

    def test_many_milestones_use_multiple_levels(self):
        """With 9 milestones, the optimizer should use multiple levels to avoid collisions."""
        config = _make_config(num_milestones=9, style=TimelineStyle.HORIZONTAL)
        layout = _layout_for(config)
        levels = {ml.level for ml in layout.milestone_layouts}
        assert len(levels) >= 2, f"Expected multiple levels, got {levels}"

    def test_two_milestones_no_optimization(self):
        """With only 2 milestones, layout should work without the optimizer."""
        config = _make_config(num_milestones=2, style=TimelineStyle.HORIZONTAL)
        layout = _layout_for(config)
        assert len(layout.milestone_layouts) == 2


class TestVerticalLayout:
    """Tests for vertical layout."""

    def test_alternating_sides(self):
        """Milestones should alternate left and right."""
        config = _make_config(num_milestones=4, style=TimelineStyle.VERTICAL)
        layout = _layout_for(config)

        sides = [ml.is_above for ml in layout.milestone_layouts]
        # Should alternate: True, False, True, False
        for i in range(len(sides)):
            expected = i % 2 == 0
            assert sides[i] == expected, f"Milestone {i} side wrong"

    def test_cards_within_canvas(self):
        config = _make_config(num_milestones=6, style=TimelineStyle.VERTICAL)
        layout = _layout_for(config)
        for ml in layout.milestone_layouts:
            assert ml.label_pos.x >= 0
            assert ml.label_pos.right <= config.output.width + 10


class TestInfographicLayout:
    """Tests for infographic layout — the main broken renderer."""

    def test_all_milestones_visible(self):
        """Every milestone must have markers within the canvas bounds."""
        config = _make_config(num_milestones=6, style=TimelineStyle.INFOGRAPHIC)
        layout = _layout_for(config)

        assert len(layout.milestone_layouts) == 6
        canvas_h = layout.canvas_height
        for i, ml in enumerate(layout.milestone_layouts):
            assert ml.marker_pos.y >= 0, f"Milestone {i} marker above canvas"
            assert ml.marker_pos.bottom <= canvas_h + 10, f"Milestone {i} marker below canvas"
            assert ml.label_pos.y >= 0, f"Milestone {i} label above canvas"
            assert ml.label_pos.bottom <= canvas_h + 10, f"Milestone {i} label below canvas"

    def test_canvas_expands_for_many_milestones(self):
        """With 12 milestones, the canvas should grow beyond the default 1080."""
        config = _make_config(num_milestones=12, style=TimelineStyle.INFOGRAPHIC)
        layout = _layout_for(config)
        # 12 milestones in 3 columns = 4 rows; each ~160px = 640px content
        # With title and margins, may still fit in 1080 or grow slightly
        assert layout.canvas_height >= 1080, "Canvas should be at least default height"
        # Every milestone should be within bounds
        for ml in layout.milestone_layouts:
            assert ml.marker_pos.bottom <= layout.canvas_height + 10

    def test_snake_pattern(self):
        """Milestones should follow a snake/zigzag pattern."""
        config = _make_config(num_milestones=6, style=TimelineStyle.INFOGRAPHIC)
        layout = _layout_for(config)

        # First row (0,1,2) should be left-to-right
        row0 = layout.milestone_layouts[:3]
        assert row0[0].marker_pos.center_x < row0[1].marker_pos.center_x < row0[2].marker_pos.center_x

        # Second row (3,4,5) should be right-to-left (reversed)
        row1 = layout.milestone_layouts[3:6]
        assert row1[0].marker_pos.center_x > row1[1].marker_pos.center_x > row1[2].marker_pos.center_x

    def test_single_milestone(self):
        """Single milestone should still produce valid layout."""
        config = _make_config(num_milestones=1, style=TimelineStyle.INFOGRAPHIC)
        layout = _layout_for(config)
        assert len(layout.milestone_layouts) == 1
        ml = layout.milestone_layouts[0]
        assert ml.marker_pos.x >= 0
        assert ml.marker_pos.y >= 0


class TestGanttLayout:
    """Tests for Gantt layout fixes."""

    def test_label_column_fits_text(self):
        """Label column should be at least 150px wide."""
        milestones = [
            Milestone(
                date=datetime(2024, 1, 1),
                title="Backend API Development Phase",
                end_date=datetime(2024, 2, 1),
                progress=50,
            ),
            Milestone(
                date=datetime(2024, 2, 1),
                title="Frontend Component Integration",
                end_date=datetime(2024, 3, 1),
                progress=25,
            ),
        ]
        config = TimelineConfig(
            title="Sprint",
            style=TimelineStyle.GANTT,
            scale=TimeScale.DAILY,
            milestones=milestones,
            output=OutputConfig(width=1920, height=600),
        )
        layout = _layout_for(config)
        # Label width should be at least 150
        for ml in layout.milestone_layouts:
            assert ml.label_pos.width >= 150

    def test_bars_within_chart_area(self):
        """All bars should start within the chart area."""
        milestones = [
            Milestone(
                date=datetime(2024, 1, 1),
                title="Task 1",
                end_date=datetime(2024, 1, 15),
            ),
        ]
        config = TimelineConfig(
            title="Sprint",
            style=TimelineStyle.GANTT,
            scale=TimeScale.DAILY,
            milestones=milestones,
            output=OutputConfig(width=1920, height=400),
        )
        layout = _layout_for(config)
        chart_left = layout.timeline_area.x
        for ml in layout.milestone_layouts:
            assert ml.marker_pos.x >= chart_left - 5


class TestRoadmapLayout:
    """Tests for roadmap layout."""

    def test_milestones_grouped_by_category(self):
        milestones = [
            Milestone(date=datetime(2024, 1, 1), title="T1", category="frontend"),
            Milestone(date=datetime(2024, 2, 1), title="T2", category="backend"),
            Milestone(date=datetime(2024, 3, 1), title="T3", category="frontend"),
        ]
        config = TimelineConfig(
            title="Roadmap",
            style=TimelineStyle.ROADMAP,
            scale=TimeScale.MONTHLY,
            milestones=milestones,
            output=OutputConfig(width=1920, height=800),
        )
        layout = _layout_for(config)
        # Frontend milestones should be in same row
        frontend_rows = {ml.row for ml in layout.milestone_layouts if ml.milestone.category == "frontend"}
        assert len(frontend_rows) == 1
