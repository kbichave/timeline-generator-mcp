"""Infographic style renderer."""

import math

from ..core.layout import LayoutEngine, TimelineLayout, MilestoneLayout
from .base import BaseRenderer


class InfographicRenderer(BaseRenderer):
    """Renderer for creative infographic style timeline."""
    
    def calculate_layout(self) -> TimelineLayout:
        """Calculate infographic layout."""
        engine = LayoutEngine(
            self.config,
            self.scale_info,
            self.width,
            self.height,
        )
        return engine.calculate_infographic_layout()
    
    def draw_background(self) -> None:
        """Draw decorative background for infographic."""
        # Call base background first
        super().draw_background()
        
        # Skip decorative elements if transparent background
        if self.config.output.transparent:
            return
        
        # Add decorative elements
        # Subtle pattern or shapes
        r, g, b, _ = self.theme.hex_to_rgba(self.theme.colors.primary_light)
        self.ctx.set_source_rgba(r, g, b, 0.05)
        
        # Draw decorative circles in background
        for i in range(5):
            cx = (i + 0.5) * self.width / 5
            cy = self.height * 0.7 + (i % 2) * 100
            radius = 100 + (i % 3) * 50
            
            self.ctx.arc(cx, cy, radius, 0, 2 * math.pi)
            self.ctx.fill()
    
    def draw_axis(self, layout: TimelineLayout) -> None:
        """Draw connecting path between milestones."""
        if len(layout.milestone_layouts) < 2:
            return
        
        # Draw curved path connecting milestones
        self.ctx.set_line_width(self.theme.line_width)
        r, g, b, _ = self.theme.hex_to_rgba(self.theme.colors.primary)
        self.ctx.set_source_rgba(r, g, b, 0.3)
        
        # Start path
        first = layout.milestone_layouts[0]
        self.ctx.move_to(first.marker_pos.center_x, first.marker_pos.center_y)
        
        # Draw curves between milestones
        for i in range(1, len(layout.milestone_layouts)):
            current = layout.milestone_layouts[i]
            prev = layout.milestone_layouts[i - 1]
            
            # Control points for smooth curve
            mid_x = (prev.marker_pos.center_x + current.marker_pos.center_x) / 2
            
            self.ctx.curve_to(
                mid_x, prev.marker_pos.center_y,
                mid_x, current.marker_pos.center_y,
                current.marker_pos.center_x, current.marker_pos.center_y,
            )
        
        self.ctx.stroke()
        
        # Draw dotted continuation lines
        self.ctx.set_dash([8, 4])
        self.ctx.set_source_rgba(r, g, b, 0.15)
        
        for ml in layout.milestone_layouts:
            # Small decorative lines around each node
            cx = ml.marker_pos.center_x
            cy = ml.marker_pos.center_y
            radius = ml.marker_pos.width / 2 + 20
            
            for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
                x1 = cx + math.cos(angle) * radius
                y1 = cy + math.sin(angle) * radius
                x2 = cx + math.cos(angle) * (radius + 15)
                y2 = cy + math.sin(angle) * (radius + 15)
                
                self.ctx.move_to(x1, y1)
                self.ctx.line_to(x2, y2)
                self.ctx.stroke()
        
        self.ctx.set_dash([])
    
    def draw_scale_markers(self, layout: TimelineLayout) -> None:
        """No traditional scale markers for infographic style."""
        pass
    
    def draw_milestone(
        self,
        ml: MilestoneLayout,
        layout: TimelineLayout,
        opacity: float = 1.0,
    ) -> None:
        """Draw an infographic-style milestone."""
        milestone = ml.milestone
        
        # Get color
        if milestone.color:
            color = milestone.color
        else:
            idx = self.config.milestones.index(milestone)
            color = self.theme.colors.get_accent(idx)
        
        cx = ml.marker_pos.center_x
        cy = ml.marker_pos.center_y
        radius = ml.marker_pos.width / 2
        
        # Outer glow/ring
        if self.theme.use_shadows:
            for i in range(3):
                glow_radius = radius + 10 + i * 8
                r, g, b, _ = self.theme.hex_to_rgba(color)
                self.ctx.arc(cx, cy, glow_radius, 0, 2 * math.pi)
                self.ctx.set_source_rgba(r, g, b, 0.1 * opacity * (3 - i) / 3)
                self.ctx.fill()
        
        # Main circle
        self.draw_circle(
            cx, cy, radius,
            color,
            self.theme.colors.background,
            self.theme.marker_border_width * 2,
            opacity=opacity,
        )
        
        # Inner content area
        inner_radius = radius * 0.7
        self.draw_circle(
            cx, cy, inner_radius,
            self.theme.colors.background,
            opacity=opacity,
        )
        
        # Badge/step indicator - use custom badge text or default to number
        if milestone.badge:
            badge_text = milestone.badge
            # Smaller font for longer text
            base_font = self.theme.label_font if len(badge_text) > 3 else self.theme.title_font
        else:
            idx = self.config.milestones.index(milestone) + 1
            badge_text = str(idx)
            base_font = self.theme.title_font
        
        # Apply custom badge font size if configured
        badge_font = base_font
        if self.config.fonts and self.config.fonts.badge:
            from ..themes.base import FontConfig as ThemeFontConfig
            badge_font = ThemeFontConfig(
                family=base_font.family,
                size=self.config.fonts.badge,
                bold=base_font.bold,
                italic=base_font.italic,
            )
        
        self.theme.apply_font(self.ctx, badge_font)
        extents = self.ctx.text_extents(badge_text)
        
        r, g, b, _ = self.theme.hex_to_rgba(color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        self.ctx.move_to(
            cx - extents.width / 2,
            cy + extents.height / 3,
        )
        self.ctx.show_text(badge_text)
        
        # Title below - apply custom title font size if configured
        title_font = self.theme.label_font
        if self.config.fonts and self.config.fonts.title:
            from ..themes.base import FontConfig as ThemeFontConfig
            title_font = ThemeFontConfig(
                family=self.theme.label_font.family,
                size=self.config.fonts.title,
                bold=self.theme.label_font.bold,
                italic=self.theme.label_font.italic,
            )
        
        self.draw_text(
            milestone.title,
            ml.label_pos.x, ml.label_pos.y,
            title_font,
            self.theme.colors.text_primary,
            max_width=ml.label_pos.width,
            align="center",
            opacity=opacity,
        )
        
        # Date (skip if transparent - user likely has month in title already)
        if not self.config.output.transparent:
            date_str = milestone.date.strftime("%b %d, %Y")
            self.draw_text(
                date_str,
                ml.label_pos.x, ml.label_pos.y + self.theme.label_font.size + 5,
                self.theme.date_font,
                color,
                max_width=ml.label_pos.width,
                align="center",
                opacity=opacity,
            )
        
        # Description
        if ml.description_pos and milestone.description:
            self.draw_text(
                milestone.description,
                ml.description_pos.x, ml.description_pos.y,
                self.theme.description_font,
                self.theme.colors.text_secondary,
                max_width=ml.description_pos.width,
                align="center",
                opacity=opacity,
            )
        
        # Highlight badge
        if milestone.highlight:
            # Ribbon or special indicator
            ribbon_width = 60
            ribbon_height = 20
            ribbon_x = cx - ribbon_width / 2
            ribbon_y = cy - radius - 25
            
            self.draw_rounded_rect(
                ribbon_x, ribbon_y,
                ribbon_width, ribbon_height,
                ribbon_height / 2,
                self.theme.colors.warning,
                opacity=opacity,
            )
            
            self.draw_text(
                "KEY",
                ribbon_x, ribbon_y + 2,
                self.theme.date_font,
                self.theme.colors.text_light,
                max_width=ribbon_width,
                align="center",
                opacity=opacity,
            )

