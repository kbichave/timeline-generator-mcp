"""Tests for Phase 3: Personalization — presets, watermarks, font overrides."""

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
    ExportPreset,
    PRESET_DIMENSIONS,
    FontConfig,
    WatermarkConfig,
)
from timeline_generator.themes import THEMES
from timeline_generator.renderers import HorizontalRenderer, VerticalRenderer
from timeline_generator.output.image import ImageExporter


MILESTONES = [
    Milestone(date=datetime(2024, 1, 1), title="Start"),
    Milestone(date=datetime(2024, 6, 1), title="Mid"),
    Milestone(date=datetime(2024, 12, 1), title="End"),
]


def _get_renderer(config):
    theme_class = THEMES.get(config.theme.value, THEMES["minimal"])
    theme = theme_class()
    if config.colors:
        theme.apply_color_overrides(config.colors)
    if config.fonts:
        theme.apply_font_overrides(config.fonts)
    return HorizontalRenderer(config, theme)


class TestExportPresets:
    """Test that preset dimensions override width/height."""

    @pytest.mark.parametrize("preset,expected", [
        ("ig-story", (1080, 1920)),
        ("ig-post", (1080, 1080)),
        ("linkedin", (1200, 627)),
        ("twitter", (1600, 900)),
        ("yt-thumbnail", (1280, 720)),
    ])
    def test_preset_overrides_dimensions(self, preset, expected):
        config = OutputConfig(preset=ExportPreset(preset))
        assert config.width == expected[0]
        assert config.height == expected[1]

    def test_custom_preset_keeps_dimensions(self):
        config = OutputConfig(preset=ExportPreset.CUSTOM, width=800, height=600)
        assert config.width == 800
        assert config.height == 600

    def test_preset_renders(self):
        """Instagram story preset should produce a tall image."""
        config = TimelineConfig(
            title="IG Story",
            milestones=MILESTONES,
            output=OutputConfig(preset=ExportPreset.INSTAGRAM_STORY),
        )
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size == (1080, 1920)

    def test_all_presets_in_dimensions(self):
        """Every non-custom preset should have an entry in PRESET_DIMENSIONS."""
        for preset in ExportPreset:
            if preset != ExportPreset.CUSTOM:
                assert preset.value in PRESET_DIMENSIONS


class TestWatermark:
    """Test watermark rendering."""

    def test_watermark_config(self):
        wm = WatermarkConfig(text="Made with TimelineGen", opacity=0.5)
        assert wm.text == "Made with TimelineGen"
        assert wm.opacity == 0.5
        assert wm.position == "bottom-right"

    def test_watermark_renders(self):
        config = TimelineConfig(
            title="Watermarked",
            milestones=MILESTONES,
            watermark=WatermarkConfig(text="© 2024 MyBrand"),
        )
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size[0] == 1920

    def test_no_watermark_by_default(self):
        config = TimelineConfig(milestones=MILESTONES)
        assert config.watermark is None

    @pytest.mark.parametrize("position", ["bottom-right", "bottom-left", "top-right", "top-left"])
    def test_watermark_positions(self, position):
        config = TimelineConfig(
            title="WM Test",
            milestones=MILESTONES,
            watermark=WatermarkConfig(text="test", position=position),
        )
        renderer = _get_renderer(config)
        renderer.render()
        # Should render without error
        img = renderer.surface_to_pil()
        assert img.size[0] == 1920


class TestFontOverrides:
    """Test custom font family and size overrides."""

    def test_font_family_override(self):
        config = TimelineConfig(
            milestones=MILESTONES,
            fonts=FontConfig(family="Courier"),
        )
        theme = THEMES["minimal"]()
        theme.apply_font_overrides(config.fonts)
        assert theme.title_font.family == "Courier"
        assert theme.label_font.family == "Courier"
        assert theme.description_font.family == "Courier"

    def test_font_size_override(self):
        config = TimelineConfig(
            milestones=MILESTONES,
            fonts=FontConfig(title=20, description=14),
        )
        theme = THEMES["corporate"]()
        theme.apply_font_overrides(config.fonts)
        assert theme.label_font.size == 20
        assert theme.description_font.size == 14

    def test_font_override_renders(self):
        config = TimelineConfig(
            title="Font Test",
            milestones=MILESTONES,
            fonts=FontConfig(family="Georgia", title=18),
        )
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size[0] == 1920

    def test_none_font_config_no_op(self):
        theme = THEMES["minimal"]()
        original_family = theme.title_font.family
        theme.apply_font_overrides(None)
        assert theme.title_font.family == original_family


class TestPresetYAMLParsing:
    """Test that preset can be specified in YAML config."""

    def test_parse_preset_from_yaml(self):
        from timeline_generator.parser import parse_yaml
        yaml_str = """
title: "Preset Test"
milestones:
  - date: "2024-01-01"
    title: "Start"
output:
  format: png
  preset: ig-post
"""
        config = parse_yaml(yaml_str)
        assert config.output.preset == ExportPreset.INSTAGRAM_POST
        assert config.output.width == 1080
        assert config.output.height == 1080
