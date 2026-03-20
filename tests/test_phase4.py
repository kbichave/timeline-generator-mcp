"""Tests for Phase 4: Product packaging — demo, version, presets command."""

import pytest
from datetime import datetime

from timeline_generator import __version__
from timeline_generator.models import (
    Milestone,
    TimelineConfig,
    TimelineStyle,
    ThemeName,
    ExportPreset,
    PRESET_DIMENSIONS,
    AnimationEffect,
    WatermarkConfig,
    OutputConfig,
)
from timeline_generator.themes import THEMES


class TestVersioning:
    """Test version is set to 1.0.0."""

    def test_version_is_1_0_0(self):
        assert __version__ == "1.0.0"


class TestProductCompleteness:
    """Ensure all advertised features exist and work."""

    def test_eight_themes_available(self):
        assert len(THEMES) == 8
        expected = {"minimal", "corporate", "creative", "dark", "neon", "pastel", "ocean", "sunset"}
        assert set(THEMES.keys()) == expected

    def test_five_styles_available(self):
        styles = [s.value for s in TimelineStyle]
        assert len(styles) == 5
        assert set(styles) == {"horizontal", "vertical", "gantt", "roadmap", "infographic"}

    def test_eight_presets_available(self):
        # custom + 8 platform presets
        assert len(ExportPreset) == 9
        assert len(PRESET_DIMENSIONS) == 8

    def test_five_animation_effects(self):
        effects = [e.value for e in AnimationEffect]
        assert len(effects) == 5

    def test_watermark_model_complete(self):
        wm = WatermarkConfig(text="test", position="top-left", opacity=0.5, font_size=20)
        assert wm.text == "test"
        assert wm.position == "top-left"

    def test_all_theme_style_combos_render(self):
        """Smoke test: every theme x every style should render without error."""
        milestones = [
            Milestone(date=datetime(2024, 1, 1), title="A"),
            Milestone(date=datetime(2024, 6, 1), title="B"),
        ]

        gantt_milestones = [
            Milestone(date=datetime(2024, 1, 1), title="Task", end_date=datetime(2024, 2, 1)),
            Milestone(date=datetime(2024, 2, 1), title="Task2", end_date=datetime(2024, 3, 1)),
        ]

        roadmap_milestones = [
            Milestone(date=datetime(2024, 1, 1), title="A", category="x"),
            Milestone(date=datetime(2024, 6, 1), title="B", category="y"),
        ]

        from timeline_generator.renderers import (
            HorizontalRenderer, VerticalRenderer, GanttRenderer,
            RoadmapRenderer, InfographicRenderer,
        )

        style_map = {
            TimelineStyle.HORIZONTAL: (HorizontalRenderer, milestones),
            TimelineStyle.VERTICAL: (VerticalRenderer, milestones),
            TimelineStyle.GANTT: (GanttRenderer, gantt_milestones),
            TimelineStyle.ROADMAP: (RoadmapRenderer, roadmap_milestones),
            TimelineStyle.INFOGRAPHIC: (InfographicRenderer, milestones),
        }

        errors = []
        for theme_name in ThemeName:
            for style in TimelineStyle:
                renderer_cls, ms = style_map[style]
                try:
                    config = TimelineConfig(
                        title="Smoke",
                        style=style,
                        theme=theme_name,
                        milestones=ms,
                        output=OutputConfig(width=640, height=360),
                    )
                    theme = THEMES[theme_name.value]()
                    renderer = renderer_cls(config, theme)
                    renderer.render()
                    img = renderer.surface_to_pil()
                    assert img.size[0] == 640
                except Exception as e:
                    errors.append(f"{theme_name.value}/{style.value}: {e}")

        assert errors == [], f"Failed combos: {errors}"


class TestDemoCommand:
    """Test the demo command generates files."""

    def test_demo_generates_files(self, tmp_path):
        """Run the demo generation logic directly (not via CLI)."""
        from timeline_generator.cli import get_renderer, get_theme
        from timeline_generator.output.image import ImageExporter
        from timeline_generator.models import OutputConfig, TimeScale

        demo_milestones = [
            Milestone(date=datetime(2024, 1, 15), title="Start", highlight=True),
            Milestone(date=datetime(2024, 6, 1), title="Mid"),
            Milestone(date=datetime(2024, 12, 1), title="End"),
        ]

        count = 0
        for theme_name in ["minimal", "neon", "sunset"]:
            config = TimelineConfig(
                title=f"Demo {theme_name}",
                style=TimelineStyle.HORIZONTAL,
                theme=ThemeName(theme_name),
                scale=TimeScale.MONTHLY,
                milestones=demo_milestones,
                output=OutputConfig(width=800, height=400),
            )
            theme = get_theme(config.theme.value)
            renderer = get_renderer(config, theme)
            exporter = ImageExporter(renderer)
            out = tmp_path / f"demo_{theme_name}.png"
            exporter.export_png(out)
            assert out.exists()
            assert out.stat().st_size > 0
            count += 1

        assert count == 3
