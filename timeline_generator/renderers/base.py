"""Base renderer class with Cairo setup."""

from abc import ABC, abstractmethod
from typing import Optional
import io
import math

import cairo
from PIL import Image

from ..models import TimelineConfig, AnimationEffect
from ..core.scale import ScaleInfo, calculate_scale, TimeScale as CoreTimeScale
from ..core.layout import TimelineLayout, LayoutEngine
from ..themes.base import Theme


def _ease_out_cubic(t: float) -> float:
    """Cubic ease-out for smooth animation deceleration."""
    return 1 - pow(1 - t, 3)


class BaseRenderer(ABC):
    """Abstract base class for timeline renderers."""
    
    def __init__(self, config: TimelineConfig, theme: Theme):
        """
        Initialize the renderer.
        
        Args:
            config: Timeline configuration.
            theme: Theme to apply.
        """
        self.config = config
        self.theme = theme
        self.width = config.output.width
        self.height = config.output.height
        
        # Calculate scale info
        start_date, end_date = config.date_range
        self.scale_info = calculate_scale(
            start_date,
            end_date,
            CoreTimeScale(config.scale.value),
        )
        
        # Cairo surfaces and contexts
        self._surface: Optional[cairo.ImageSurface] = None
        self._ctx: Optional[cairo.Context] = None
    
    @property
    def surface(self) -> cairo.ImageSurface:
        """Get or create the Cairo surface."""
        if self._surface is None:
            self._surface = cairo.ImageSurface(
                cairo.FORMAT_ARGB32,
                self.width,
                self.height,
            )
        return self._surface
    
    @property
    def ctx(self) -> cairo.Context:
        """Get or create the Cairo context."""
        if self._ctx is None:
            self._ctx = cairo.Context(self.surface)
        return self._ctx
    
    def reset_surface(self) -> None:
        """Reset the surface for a new render."""
        self._surface = None
        self._ctx = None
    
    def render(self) -> cairo.ImageSurface:
        """
        Render the timeline to a Cairo surface.

        Returns:
            The rendered Cairo surface.
        """
        self.reset_surface()

        # Draw background
        self.draw_background()

        # Calculate layout
        layout = self.calculate_layout()

        # Draw title
        if self.config.show_title:
            self.draw_title(layout)

        # Draw the timeline axis/structure
        self.draw_axis(layout)

        # Draw scale markers
        self.draw_scale_markers(layout)

        # Draw milestones
        for ml in layout.milestone_layouts:
            self.draw_milestone(ml, layout)

        # Draw watermark if configured
        self._draw_watermark()

        return self.surface

    def _draw_watermark(self) -> None:
        """Draw watermark/branding text if configured."""
        if not self.config.watermark or not self.config.watermark.text:
            return

        wm = self.config.watermark
        from ..themes.base import FontConfig as ThemeFontConfig

        font = ThemeFontConfig(family="Sans", size=wm.font_size, italic=True)
        self.theme.apply_font(self.ctx, font)

        extents = self.ctx.text_extents(wm.text)
        pad = 15

        # Position mapping
        if wm.position == "bottom-right":
            x = self.width - extents.width - pad
            y = self.height - pad
        elif wm.position == "bottom-left":
            x = pad
            y = self.height - pad
        elif wm.position == "top-right":
            x = self.width - extents.width - pad
            y = pad + wm.font_size
        elif wm.position == "top-left":
            x = pad
            y = pad + wm.font_size
        else:
            x = self.width - extents.width - pad
            y = self.height - pad

        self.ctx.set_source_rgba(0.5, 0.5, 0.5, wm.opacity)
        self.ctx.move_to(x, y)
        self.ctx.show_text(wm.text)
    
    def render_frame(self, progress: float) -> cairo.ImageSurface:
        """
        Render a frame for animation.

        Args:
            progress: Animation progress from 0.0 to 1.0.

        Returns:
            The rendered Cairo surface for this frame.
        """
        self.reset_surface()

        # Draw background
        self.draw_background()

        # Calculate layout
        layout = self.calculate_layout()

        # Draw title (always visible)
        if self.config.show_title:
            self.draw_title(layout)

        # Draw axis (always visible so hold frames aren't blank)
        self.draw_axis(layout)

        num_milestones = len(layout.milestone_layouts)
        if num_milestones == 0:
            return self.surface

        # Map progress to a float count of milestones to reveal.
        # At progress=0 we show 0 milestones; at progress=1 we show all.
        reveal = progress * num_milestones

        # Draw scale markers once any milestone starts appearing
        if reveal > 0.1:
            self.draw_scale_markers(layout)

        # Draw visible milestones with configured animation effect
        effect = self.config.output.animation_effect
        for i, ml in enumerate(layout.milestone_layouts):
            # Per-milestone progress: 0 = not started, 1 = fully visible
            raw_t = max(0.0, min(1.0, reveal - i))
            if raw_t <= 0:
                continue

            # Apply easing for smoother animation
            t = _ease_out_cubic(raw_t)

            if effect == AnimationEffect.FADE:
                self.draw_milestone(ml, layout, opacity=t)
            elif effect in (AnimationEffect.SLIDE_UP, AnimationEffect.SLIDE_LEFT):
                # Save context, apply translation, draw, restore
                self.ctx.save()
                if effect == AnimationEffect.SLIDE_UP:
                    self.ctx.translate(0, 30 * (1 - t))
                else:
                    self.ctx.translate(-40 * (1 - t), 0)
                self.draw_milestone(ml, layout, opacity=t)
                self.ctx.restore()
            elif effect == AnimationEffect.POP:
                # Scale from center of marker
                cx = ml.marker_pos.center_x
                cy = ml.marker_pos.center_y
                scale = 0.5 + 0.5 * t
                self.ctx.save()
                self.ctx.translate(cx * (1 - scale), cy * (1 - scale))
                self.ctx.scale(scale, scale)
                self.draw_milestone(ml, layout, opacity=t)
                self.ctx.restore()
            elif effect == AnimationEffect.SCALE:
                scale = t
                cx = ml.marker_pos.center_x
                cy = ml.marker_pos.center_y
                self.ctx.save()
                self.ctx.translate(cx * (1 - scale), cy * (1 - scale))
                self.ctx.scale(scale, scale)
                self.draw_milestone(ml, layout, opacity=min(1.0, t * 1.5))
                self.ctx.restore()
            else:
                self.draw_milestone(ml, layout, opacity=t)

        return self.surface
    
    @abstractmethod
    def calculate_layout(self) -> TimelineLayout:
        """Calculate the layout for this style."""
        pass
    
    def draw_background(self) -> None:
        """Draw the background with optional gradient support."""
        if self.config.output.transparent:
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
            self.ctx.rectangle(0, 0, self.width, self.height)
            self.ctx.fill()
            self.ctx.set_operator(cairo.OPERATOR_OVER)
            return

        # Check for explicit gradient config
        if self.theme.gradient.enabled and len(self.theme.gradient.colors) >= 2:
            self._draw_gradient_background()
            return

        # Solid background
        r, g, b, a = self.theme.hex_to_rgba(self.theme.colors.background)
        self.ctx.set_source_rgba(r, g, b, a)
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()

        # Auto gradient from background/background_alt
        if self.theme.colors.background != self.theme.colors.background_alt:
            gradient = cairo.LinearGradient(0, 0, 0, self.height)
            r1, g1, b1, _ = self.theme.hex_to_rgba(self.theme.colors.background)
            r2, g2, b2, _ = self.theme.hex_to_rgba(self.theme.colors.background_alt)
            gradient.add_color_stop_rgba(0, r1, g1, b1, 1)
            gradient.add_color_stop_rgba(1, r2, g2, b2, 1)
            self.ctx.set_source(gradient)
            self.ctx.rectangle(0, 0, self.width, self.height)
            self.ctx.fill()

    def _draw_gradient_background(self) -> None:
        """Draw a multi-stop gradient background."""
        grad_cfg = self.theme.gradient
        colors = grad_cfg.colors
        stops = grad_cfg.stops if len(grad_cfg.stops) == len(colors) else [
            i / max(1, len(colors) - 1) for i in range(len(colors))
        ]

        if grad_cfg.direction == "horizontal":
            gradient = cairo.LinearGradient(0, 0, self.width, 0)
        elif grad_cfg.direction == "radial":
            cx, cy = self.width / 2, self.height / 2
            radius = max(self.width, self.height) * 0.7
            gradient = cairo.RadialGradient(cx, cy, 0, cx, cy, radius)
        else:
            gradient = cairo.LinearGradient(0, 0, 0, self.height)

        for stop, color in zip(stops, colors):
            r, g, b, _ = self.theme.hex_to_rgba(color)
            gradient.add_color_stop_rgba(stop, r, g, b, 1.0)

        self.ctx.set_source(gradient)
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()
    
    def draw_title(self, layout: TimelineLayout) -> None:
        """Draw the title and subtitle."""
        if not layout.title_area:
            return
        
        # Title
        self.theme.apply_font(self.ctx, self.theme.title_font)
        r, g, b, a = self.theme.hex_to_rgba(self.theme.colors.text_primary)
        self.ctx.set_source_rgba(r, g, b, a)
        
        # Center the title
        extents = self.ctx.text_extents(self.config.title)
        x = layout.title_area.x + (layout.title_area.width - extents.width) / 2
        y = layout.title_area.y + self.theme.title_font.size
        
        self.ctx.move_to(x, y)
        self.ctx.show_text(self.config.title)
        
        # Subtitle
        if self.config.subtitle:
            self.theme.apply_font(self.ctx, self.theme.subtitle_font)
            r, g, b, a = self.theme.hex_to_rgba(self.theme.colors.text_secondary)
            self.ctx.set_source_rgba(r, g, b, a)
            
            extents = self.ctx.text_extents(self.config.subtitle)
            x = layout.title_area.x + (layout.title_area.width - extents.width) / 2
            y = layout.title_area.y + self.theme.title_font.size + self.theme.subtitle_font.size + 10
            
            self.ctx.move_to(x, y)
            self.ctx.show_text(self.config.subtitle)
    
    @abstractmethod
    def draw_axis(self, layout: TimelineLayout) -> None:
        """Draw the timeline axis/line."""
        pass
    
    def draw_scale_markers(self, layout: TimelineLayout) -> None:
        """Draw time scale markers and labels."""
        # Default implementation - can be overridden
        pass
    
    @abstractmethod
    def draw_milestone(
        self,
        ml,
        layout: TimelineLayout,
        opacity: float = 1.0,
    ) -> None:
        """Draw a single milestone."""
        pass
    
    def draw_circle(
        self,
        x: float,
        y: float,
        radius: float,
        fill_color: str,
        stroke_color: Optional[str] = None,
        stroke_width: float = 2.0,
        opacity: float = 1.0,
    ) -> None:
        """Draw a circle (marker)."""
        self.ctx.arc(x, y, radius, 0, 2 * math.pi)
        
        # Fill
        r, g, b, _ = self.theme.hex_to_rgba(fill_color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        self.ctx.fill_preserve()
        
        # Stroke
        if stroke_color:
            r, g, b, _ = self.theme.hex_to_rgba(stroke_color)
            self.ctx.set_source_rgba(r, g, b, opacity)
            self.ctx.set_line_width(stroke_width)
            self.ctx.stroke()
        else:
            self.ctx.new_path()
    
    def _rounded_rect_path(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
    ) -> None:
        """Create a rounded rectangle path (does not fill or stroke)."""
        radius = min(radius, width / 2, height / 2)
        self.ctx.new_path()
        self.ctx.arc(x + radius, y + radius, radius, math.pi, 1.5 * math.pi)
        self.ctx.arc(x + width - radius, y + radius, radius, 1.5 * math.pi, 2 * math.pi)
        self.ctx.arc(x + width - radius, y + height - radius, radius, 0, 0.5 * math.pi)
        self.ctx.arc(x + radius, y + height - radius, radius, 0.5 * math.pi, math.pi)
        self.ctx.close_path()

    def draw_shadow(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float = 8.0,
        opacity: float = 1.0,
    ) -> None:
        """Draw a soft drop shadow using layered semi-transparent rects."""
        if not self.theme.use_shadows:
            return
        dx, dy = self.theme.shadow_offset
        blur = self.theme.shadow_blur
        layers = max(3, int(blur / 2))

        for i in range(layers):
            spread = (i + 1) * (blur / layers)
            layer_opacity = opacity * 0.08 * (1 - i / layers)
            self._rounded_rect_path(
                x + dx - spread / 2,
                y + dy - spread / 2,
                width + spread,
                height + spread,
                radius + spread / 2,
            )
            self.ctx.set_source_rgba(0, 0, 0, layer_opacity)
            self.ctx.fill()

    def draw_rounded_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
        fill_color: str,
        stroke_color: Optional[str] = None,
        stroke_width: float = 1.0,
        opacity: float = 1.0,
        shadow: bool = False,
    ) -> None:
        """Draw a rounded rectangle with optional drop shadow."""
        if shadow:
            self.draw_shadow(x, y, width, height, radius, opacity)

        self._rounded_rect_path(x, y, width, height, radius)

        # Fill
        r, g, b, _ = self.theme.hex_to_rgba(fill_color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        self.ctx.fill_preserve()

        # Stroke
        if stroke_color:
            r, g, b, _ = self.theme.hex_to_rgba(stroke_color)
            self.ctx.set_source_rgba(r, g, b, opacity)
            self.ctx.set_line_width(stroke_width)
            self.ctx.stroke()
        else:
            self.ctx.new_path()
    
    def draw_line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: str,
        width: float = 2.0,
        opacity: float = 1.0,
        dashed: bool = False,
    ) -> None:
        """Draw a line."""
        r, g, b, _ = self.theme.hex_to_rgba(color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        self.ctx.set_line_width(width)
        
        if dashed:
            self.ctx.set_dash([5, 5])
        else:
            self.ctx.set_dash([])
        
        self.ctx.move_to(x1, y1)
        self.ctx.line_to(x2, y2)
        self.ctx.stroke()
    
    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        font_config,
        color: str,
        max_width: Optional[float] = None,
        align: str = "left",
        opacity: float = 1.0,
        wrap: Optional[bool] = None,
    ) -> None:
        """Draw text with optional wrapping and alignment."""
        self.theme.apply_font(self.ctx, font_config)
        r, g, b, _ = self.theme.hex_to_rgba(color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        
        # Use config's text_wrap setting if wrap is not explicitly specified
        should_wrap = wrap if wrap is not None else self.config.text_wrap
        
        if max_width and should_wrap:
            # Word wrap text
            lines = self._wrap_text(text, max_width)
            line_height = font_config.size * 1.3
            
            for i, line in enumerate(lines):
                extents = self.ctx.text_extents(line)
                line_x = x
                
                if align == "center":
                    line_x = x + (max_width - extents.width) / 2
                elif align == "right":
                    line_x = x + max_width - extents.width
                
                self.ctx.move_to(line_x, y + font_config.size + (i * line_height))
                self.ctx.show_text(line)
            return
        
        extents = self.ctx.text_extents(text)
        
        if align == "center" and max_width:
            x = x + (max_width - extents.width) / 2
        elif align == "right" and max_width:
            x = x + max_width - extents.width
        
        self.ctx.move_to(x, y + font_config.size)
        self.ctx.show_text(text)
    
    def _wrap_text(self, text: str, max_width: float, max_lines: int = 3) -> list[str]:
        """Wrap text to fit within max_width.

        Args:
            text: The text to wrap.
            max_width: Maximum width in pixels for each line.
            max_lines: Maximum number of lines before truncating with ellipsis.
        """
        words = text.split()
        lines: list[str] = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            extents = self.ctx.text_extents(test_line)

            if extents.width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # Check if single word is too long
                if self.ctx.text_extents(word).width > max_width:
                    truncated = word
                    while len(truncated) > 3 and self.ctx.text_extents(truncated + "...").width > max_width:
                        truncated = truncated[:-1]
                    word = truncated + "..."
                current_line = word

        if current_line:
            lines.append(current_line)

        # Enforce max_lines: truncate the last visible line with ellipsis
        if len(lines) > max_lines:
            last_line = lines[max_lines - 1]
            remaining_words = " ".join(lines[max_lines:])
            # Indicate truncation
            while last_line and self.ctx.text_extents(last_line + "...").width > max_width:
                last_line = last_line.rsplit(" ", 1)[0] if " " in last_line else last_line[:-1]
            lines = lines[: max_lines - 1] + [last_line + "..."]

        return lines if lines else [text]
    
    def surface_to_pil(self) -> Image.Image:
        """Convert Cairo surface to PIL Image."""
        # Get the data from the surface
        buf = self.surface.get_data()
        
        # Create PIL Image from buffer
        img = Image.frombuffer(
            "RGBA",
            (self.width, self.height),
            buf,
            "raw",
            "BGRA",
            0,
            1,
        )
        
        return img.copy()  # Copy to detach from buffer
    
    def surface_to_bytes(self, format: str = "png") -> bytes:
        """Convert surface to bytes in specified format."""
        img = self.surface_to_pil()
        
        buffer = io.BytesIO()
        img.save(buffer, format=format.upper())
        return buffer.getvalue()

