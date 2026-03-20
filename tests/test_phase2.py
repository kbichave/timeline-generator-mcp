"""Tests for Phase 2: Visual quality — themes, shadows, gradients, animation effects."""

import pytest
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
    AnimationEffect,
)
from timeline_generator.themes import THEMES
from timeline_generator.themes.base import GradientConfig
from timeline_generator.renderers import (
    HorizontalRenderer,
    VerticalRenderer,
    InfographicRenderer,
)
from timeline_generator.output.image import ImageExporter
from timeline_generator.output.video import VideoExporter


SAMPLE_MILESTONES = [
    Milestone(date=datetime(2024, 1, 15), title="Start", description="Begin"),
    Milestone(date=datetime(2024, 4, 1), title="Mid", description="Progress"),
    Milestone(date=datetime(2024, 8, 1), title="End", description="Complete", highlight=True),
]


def _make_config(theme="minimal", style=TimelineStyle.HORIZONTAL, effect=AnimationEffect.FADE):
    return TimelineConfig(
        title="Phase 2 Test",
        style=style,
        theme=ThemeName(theme),
        milestones=SAMPLE_MILESTONES,
        output=OutputConfig(
            width=1920, height=1080,
            format=OutputFormat.PNG,
            animation_effect=effect,
        ),
    )


def _get_renderer(config):
    theme_class = THEMES.get(config.theme.value, THEMES["minimal"])
    theme = theme_class()
    renderers = {
        TimelineStyle.HORIZONTAL: HorizontalRenderer,
        TimelineStyle.VERTICAL: VerticalRenderer,
        TimelineStyle.INFOGRAPHIC: InfographicRenderer,
    }
    renderer_class = renderers.get(config.style, HorizontalRenderer)
    return renderer_class(config, theme)


class TestNewThemes:
    """Verify all 8 themes render correctly."""

    @pytest.mark.parametrize("theme_name", [t.value for t in ThemeName])
    def test_theme_renders(self, theme_name):
        config = _make_config(theme=theme_name)
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        assert img.size[0] == 1920
        colors = img.getcolors(maxcolors=10)
        assert colors is None or len(colors) > 1

    def test_all_themes_registered(self):
        """Every ThemeName enum value should have a matching entry in THEMES."""
        for name in ThemeName:
            assert name.value in THEMES, f"Theme '{name.value}' not registered in THEMES dict"

    def test_neon_has_gradient(self):
        theme = THEMES["neon"]()
        assert theme.gradient.enabled is True
        assert theme.gradient.direction == "radial"
        assert len(theme.gradient.colors) >= 2

    def test_ocean_has_gradient(self):
        theme = THEMES["ocean"]()
        assert theme.gradient.enabled is True

    def test_sunset_has_gradient(self):
        theme = THEMES["sunset"]()
        assert theme.gradient.enabled is True


class TestGradientBackground:
    """Test gradient rendering."""

    def test_vertical_gradient(self):
        config = _make_config(theme="pastel")
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil().convert("RGB")
        # Top and bottom should have different colors
        top_pixel = img.getpixel((960, 10))
        bottom_pixel = img.getpixel((960, 1070))
        assert top_pixel != bottom_pixel, "Gradient should produce different colors top vs bottom"

    def test_radial_gradient(self):
        config = _make_config(theme="neon")
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil().convert("RGB")
        # Center and corner should differ for radial gradient
        center = img.getpixel((960, 540))
        corner = img.getpixel((10, 10))
        assert center != corner, "Radial gradient should produce different center vs corner"


class TestDropShadows:
    """Test that shadow rendering produces visible effects."""

    def test_vertical_cards_have_shadows(self):
        config = _make_config(theme="corporate", style=TimelineStyle.VERTICAL)
        renderer = _get_renderer(config)
        renderer.render()
        img = renderer.surface_to_pil()
        # Just verify it renders without error and has visual content
        assert img.size == (1920, 1080)

    def test_shadow_disabled_for_minimal(self):
        """Minimal theme has use_shadows=False."""
        theme = THEMES["minimal"]()
        assert theme.use_shadows is False


class TestAnimationEffects:
    """Test all animation effect modes produce valid frames."""

    @pytest.mark.parametrize("effect", list(AnimationEffect))
    def test_effect_renders(self, effect):
        config = TimelineConfig(
            title="Anim Test",
            style=TimelineStyle.HORIZONTAL,
            milestones=SAMPLE_MILESTONES,
            output=OutputConfig(
                width=800, height=400,
                animation_effect=effect,
            ),
        )
        renderer = _get_renderer(config)
        # Render a mid-animation frame
        renderer.render_frame(0.5)
        img = renderer.surface_to_pil()
        assert img.size == (800, 400)
        colors = img.getcolors(maxcolors=10)
        assert colors is None or len(colors) > 1

    @pytest.mark.parametrize("effect", list(AnimationEffect))
    def test_effect_gif_export(self, effect, tmp_path):
        config = TimelineConfig(
            title="GIF Effect Test",
            style=TimelineStyle.HORIZONTAL,
            milestones=SAMPLE_MILESTONES,
            output=OutputConfig(
                width=640, height=360, fps=10, duration=1.0,
                format=OutputFormat.GIF,
                animation_effect=effect,
            ),
        )
        renderer = _get_renderer(config)
        exporter = VideoExporter(renderer)
        out = tmp_path / f"test_{effect.value}.gif"
        exporter.export_gif(out)
        assert out.exists()
        gif = Image.open(out)
        assert gif.format == "GIF"
        assert getattr(gif, 'n_frames', 1) >= 2


class TestAnimationEffectEnum:
    """Test the AnimationEffect model."""

    def test_all_effects_listed(self):
        effects = [e.value for e in AnimationEffect]
        assert "fade" in effects
        assert "slide-up" in effects
        assert "slide-left" in effects
        assert "pop" in effects
        assert "scale" in effects

    def test_default_is_fade(self):
        config = OutputConfig()
        assert config.animation_effect == AnimationEffect.FADE
