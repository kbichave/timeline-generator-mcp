"""Tests for rendering pipeline — verifies all styles produce valid images/GIFs."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from PIL import Image

from timeline_generator.models import (
    Milestone,
    TimelineConfig,
    OutputConfig,
    TimeScale,
    TimelineStyle,
    ThemeName,
    OutputFormat,
)
from timeline_generator.themes import THEMES
from timeline_generator.renderers import (
    HorizontalRenderer,
    VerticalRenderer,
    GanttRenderer,
    RoadmapRenderer,
    InfographicRenderer,
)
from timeline_generator.output.image import ImageExporter
from timeline_generator.output.video import VideoExporter


RENDERERS = {
    TimelineStyle.HORIZONTAL: HorizontalRenderer,
    TimelineStyle.VERTICAL: VerticalRenderer,
    TimelineStyle.GANTT: GanttRenderer,
    TimelineStyle.ROADMAP: RoadmapRenderer,
    TimelineStyle.INFOGRAPHIC: InfographicRenderer,
}

SAMPLE_MILESTONES = [
    Milestone(date=datetime(2024, 1, 15), title="Project Kickoff", description="Initial planning"),
    Milestone(date=datetime(2024, 3, 1), title="Phase 1 Complete", description="First milestone"),
    Milestone(date=datetime(2024, 6, 1), title="MVP Launch", description="Go live", highlight=True),
    Milestone(date=datetime(2024, 9, 1), title="Scale Phase", description="Growth"),
    Milestone(date=datetime(2024, 12, 1), title="v1.0 Release", description="Stable release", color="#4CAF50"),
]

GANTT_MILESTONES = [
    Milestone(date=datetime(2024, 1, 1), title="Planning Phase", end_date=datetime(2024, 1, 31), progress=100),
    Milestone(date=datetime(2024, 2, 1), title="Development Sprint", end_date=datetime(2024, 4, 30), progress=60),
    Milestone(date=datetime(2024, 5, 1), title="Testing & QA", end_date=datetime(2024, 6, 30), progress=20),
]

ROADMAP_MILESTONES = [
    Milestone(date=datetime(2024, 1, 1), title="Core API", category="backend"),
    Milestone(date=datetime(2024, 3, 1), title="Dashboard", category="frontend"),
    Milestone(date=datetime(2024, 5, 1), title="Mobile App", category="mobile"),
    Milestone(date=datetime(2024, 7, 1), title="API v2", category="backend"),
]


def _make_config(style, milestones=None, theme="minimal", fmt=OutputFormat.PNG, width=1920, height=1080):
    if milestones is None:
        if style == TimelineStyle.GANTT:
            milestones = GANTT_MILESTONES
        elif style == TimelineStyle.ROADMAP:
            milestones = ROADMAP_MILESTONES
        else:
            milestones = SAMPLE_MILESTONES

    return TimelineConfig(
        title="Test Timeline",
        subtitle="For rendering tests",
        scale=TimeScale.MONTHLY,
        style=style,
        theme=ThemeName(theme),
        milestones=milestones,
        output=OutputConfig(format=fmt, width=width, height=height, fps=10, duration=1.0),
    )


def _get_renderer(config):
    theme_class = THEMES.get(config.theme.value, THEMES["minimal"])
    theme = theme_class()
    renderer_class = RENDERERS[config.style]
    return renderer_class(config, theme)


class TestStaticRendering:
    """Test that all style+theme combos render valid PNGs."""

    @pytest.mark.parametrize("style", list(TimelineStyle))
    @pytest.mark.parametrize("theme", ["minimal", "corporate", "creative", "dark"])
    def test_render_produces_image(self, style, theme):
        """Render each style+theme combo and verify it produces a non-empty image."""
        config = _make_config(style, theme=theme)
        renderer = _get_renderer(config)
        surface = renderer.render()
        img = renderer.surface_to_pil()

        assert img.size[0] == config.output.width
        assert img.size[1] >= config.output.height  # Infographic may grow
        assert img.mode == "RGBA"

        # Image should not be entirely one color (blank)
        colors = img.getcolors(maxcolors=10)
        assert colors is None or len(colors) > 1, "Image appears to be blank (single color)"

    @pytest.mark.parametrize("style", list(TimelineStyle))
    def test_export_png(self, style, tmp_path):
        """Export to PNG file and verify it's readable."""
        config = _make_config(style)
        renderer = _get_renderer(config)
        exporter = ImageExporter(renderer)
        out = tmp_path / f"test_{style.value}.png"
        exporter.export_png(out)

        assert out.exists()
        assert out.stat().st_size > 0

        img = Image.open(out)
        assert img.size[0] == config.output.width


class TestInfographicRendering:
    """Focused tests for the infographic renderer — the main broken one."""

    def test_milestones_actually_visible(self):
        """The rendered image must have colored pixels where milestones should be."""
        config = _make_config(TimelineStyle.INFOGRAPHIC, theme="creative")
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()

        # Convert to RGB for color analysis
        rgb = img.convert("RGB")

        # The creative theme has a warm background (#FFF8E7).
        # Milestones should add non-background colors (reds, turquoise, etc.)
        # Sample the center area where milestones should be
        w, h = rgb.size
        center_region = rgb.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
        colors = center_region.getcolors(maxcolors=100)

        # There should be multiple distinct colors (not just background)
        assert colors is None or len(colors) > 3, "Center area has too few colors — milestones likely not rendering"

    def test_many_milestones_render_without_error(self):
        """12 milestones should render without any errors."""
        milestones = [
            Milestone(date=datetime(2024, 1 + i, 1), title=f"Month {i + 1}")
            for i in range(12)
        ]
        config = _make_config(TimelineStyle.INFOGRAPHIC, milestones=milestones)
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size[0] == config.output.width
        assert img.size[1] >= config.output.height


class TestAnimationFrames:
    """Test GIF frame generation."""

    def test_frame_at_zero_not_blank(self):
        """A frame at progress=0 should show axis and title, not be completely blank."""
        config = _make_config(TimelineStyle.HORIZONTAL)
        renderer = _get_renderer(config)
        renderer.render_frame(0.0)
        img = renderer.surface_to_pil()

        # Should have more than just background
        colors = img.getcolors(maxcolors=5)
        assert colors is None or len(colors) > 1, "Frame at progress=0 is blank"

    def test_frame_at_one_shows_all_milestones(self):
        """A frame at progress=1.0 should show all milestones."""
        config = _make_config(TimelineStyle.HORIZONTAL)
        renderer = _get_renderer(config)
        renderer.render_frame(1.0)
        img = renderer.surface_to_pil()

        colors = img.getcolors(maxcolors=10)
        assert colors is None or len(colors) > 3, "Frame at progress=1.0 has too few colors"

    def test_progressive_reveal(self):
        """Frames at increasing progress should have increasing visual complexity."""
        config = _make_config(TimelineStyle.VERTICAL)
        renderer = _get_renderer(config)

        unique_colors = []
        for p in [0.0, 0.25, 0.5, 0.75, 1.0]:
            renderer.render_frame(p)
            img = renderer.surface_to_pil()
            colors = img.getcolors(maxcolors=1000)
            unique_colors.append(len(colors) if colors else 1000)

        # Later frames should have at least as many colors as earlier ones
        # (more milestones = more visual content)
        assert unique_colors[-1] >= unique_colors[0], "Full frame should have >= colors as empty frame"

    @pytest.mark.parametrize("style", list(TimelineStyle))
    def test_gif_export(self, style, tmp_path):
        """Export GIF for each style and verify it's valid."""
        config = _make_config(style, fmt=OutputFormat.GIF)
        renderer = _get_renderer(config)
        exporter = VideoExporter(renderer)

        out = tmp_path / f"test_{style.value}.gif"
        exporter.export_gif(out, fps=10, duration=1.0)

        assert out.exists()
        assert out.stat().st_size > 100

        # Verify it's a valid GIF
        gif = Image.open(out)
        assert gif.format == "GIF"
        # Should have multiple frames
        n_frames = getattr(gif, 'n_frames', 1)
        assert n_frames >= 2, f"GIF has only {n_frames} frame(s)"


class TestTextWrapping:
    """Test that long titles wrap correctly instead of truncating."""

    def test_long_title_wraps(self):
        """A milestone with a very long title should still render without error."""
        milestones = [
            Milestone(
                date=datetime(2024, 1, 1),
                title="This is a very long milestone title that should wrap to multiple lines",
                description="And this description is also quite long and should wrap properly",
            ),
            Milestone(date=datetime(2024, 6, 1), title="Short"),
        ]
        config = _make_config(TimelineStyle.HORIZONTAL, milestones=milestones)
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size[0] == config.output.width

    def test_no_wrap_mode(self):
        """With text_wrap=False, rendering should still succeed."""
        milestones = [
            Milestone(date=datetime(2024, 1, 1), title="A moderately long title here"),
            Milestone(date=datetime(2024, 6, 1), title="Another title"),
        ]
        config = TimelineConfig(
            title="Test",
            style=TimelineStyle.HORIZONTAL,
            milestones=milestones,
            text_wrap=False,
            output=OutputConfig(width=1920, height=1080),
        )
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size[0] == 1920
