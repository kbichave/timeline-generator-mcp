"""Base renderer class with Cairo setup."""

from abc import ABC, abstractmethod
from typing import Optional
import io
import math

import cairo
from PIL import Image

from ..models import TimelineConfig
from ..core.scale import ScaleInfo, calculate_scale, TimeScale as CoreTimeScale
from ..core.layout import TimelineLayout, LayoutEngine
from ..themes.base import Theme


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
        
        return self.surface
    
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
        
        # Draw axis
        self.draw_axis(layout)
        
        # Calculate how many milestones to show
        num_milestones = len(layout.milestone_layouts)
        visible_count = int(progress * (num_milestones + 1))  # +1 for axis reveal
        
        # Draw scale markers progressively
        if progress > 0.1:
            self.draw_scale_markers(layout)
        
        # Draw visible milestones
        for i, ml in enumerate(layout.milestone_layouts):
            if i < visible_count:
                # Calculate per-milestone opacity for smooth transitions
                milestone_progress = min(1.0, (progress * (num_milestones + 1) - i))
                self.draw_milestone(ml, layout, opacity=milestone_progress)
        
        return self.surface
    
    @abstractmethod
    def calculate_layout(self) -> TimelineLayout:
        """Calculate the layout for this style."""
        pass
    
    def draw_background(self) -> None:
        """Draw the background (or clear for transparency)."""
        # Check if transparent background is requested
        if self.config.output.transparent:
            # Clear to transparent
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
            self.ctx.rectangle(0, 0, self.width, self.height)
            self.ctx.fill()
            self.ctx.set_operator(cairo.OPERATOR_OVER)
            return
        
        r, g, b, a = self.theme.hex_to_rgba(self.theme.colors.background)
        self.ctx.set_source_rgba(r, g, b, a)
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()
        
        # Optional gradient or pattern
        if self.theme.colors.background != self.theme.colors.background_alt:
            # Subtle gradient
            gradient = cairo.LinearGradient(0, 0, 0, self.height)
            r1, g1, b1, _ = self.theme.hex_to_rgba(self.theme.colors.background)
            r2, g2, b2, _ = self.theme.hex_to_rgba(self.theme.colors.background_alt)
            gradient.add_color_stop_rgba(0, r1, g1, b1, 1)
            gradient.add_color_stop_rgba(1, r2, g2, b2, 1)
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
    ) -> None:
        """Draw a rounded rectangle."""
        # Create rounded rectangle path
        self.ctx.new_path()
        self.ctx.arc(x + radius, y + radius, radius, math.pi, 1.5 * math.pi)
        self.ctx.arc(x + width - radius, y + radius, radius, 1.5 * math.pi, 2 * math.pi)
        self.ctx.arc(x + width - radius, y + height - radius, radius, 0, 0.5 * math.pi)
        self.ctx.arc(x + radius, y + height - radius, radius, 0.5 * math.pi, math.pi)
        self.ctx.close_path()
        
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
    ) -> None:
        """Draw text with optional wrapping and alignment."""
        self.theme.apply_font(self.ctx, font_config)
        r, g, b, _ = self.theme.hex_to_rgba(color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        
        if max_width:
            # Simple text truncation
            extents = self.ctx.text_extents(text)
            if extents.width > max_width:
                while len(text) > 3 and self.ctx.text_extents(text + "...").width > max_width:
                    text = text[:-1]
                text = text + "..."
        
        extents = self.ctx.text_extents(text)
        
        if align == "center" and max_width:
            x = x + (max_width - extents.width) / 2
        elif align == "right" and max_width:
            x = x + max_width - extents.width
        
        self.ctx.move_to(x, y + font_config.size)
        self.ctx.show_text(text)
    
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

