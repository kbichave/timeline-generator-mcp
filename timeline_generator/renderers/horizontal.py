"""Horizontal timeline renderer."""

from ..core.layout import LayoutEngine, TimelineLayout, MilestoneLayout
from ..core.scale import date_to_position
from .base import BaseRenderer


class HorizontalRenderer(BaseRenderer):
    """Renderer for horizontal timeline style."""
    
    def calculate_layout(self) -> TimelineLayout:
        """Calculate horizontal layout."""
        engine = LayoutEngine(
            self.config,
            self.scale_info,
            self.width,
            self.height,
        )
        return engine.calculate_horizontal_layout()
    
    def draw_axis(self, layout: TimelineLayout) -> None:
        """Draw the horizontal timeline axis."""
        x1, y1 = layout.axis_start
        x2, y2 = layout.axis_end
        
        # Main line
        self.draw_line(
            x1, y1, x2, y2,
            self.theme.colors.primary,
            self.theme.line_width,
        )
        
        # Arrow head at end
        arrow_size = 12
        self.ctx.move_to(x2, y2)
        self.ctx.line_to(x2 - arrow_size, y2 - arrow_size / 2)
        self.ctx.line_to(x2 - arrow_size, y2 + arrow_size / 2)
        self.ctx.close_path()
        
        r, g, b, _ = self.theme.hex_to_rgba(self.theme.colors.primary)
        self.ctx.set_source_rgba(r, g, b, 1)
        self.ctx.fill()
    
    def draw_scale_markers(self, layout: TimelineLayout) -> None:
        """Draw time scale markers on the axis."""
        x1, y1 = layout.axis_start
        x2, _ = layout.axis_end
        timeline_width = x2 - x1
        
        # Draw major ticks
        for i, (tick, label) in enumerate(zip(
            self.scale_info.major_ticks,
            self.scale_info.unit_labels,
        )):
            x = date_to_position(tick, self.scale_info, timeline_width) + x1
            
            # Tick mark
            tick_height = 10
            self.draw_line(
                x, y1 - tick_height / 2,
                x, y1 + tick_height / 2,
                self.theme.colors.primary,
                self.theme.connector_width,
            )
            
            # Label below the line
            self.draw_text(
                label,
                x - 30, y1 + 15,
                self.theme.date_font,
                self.theme.colors.text_secondary,
                max_width=60,
                align="center",
            )
    
    def draw_milestone(
        self,
        ml: MilestoneLayout,
        layout: TimelineLayout,
        opacity: float = 1.0,
    ) -> None:
        """Draw a milestone on the horizontal timeline."""
        milestone = ml.milestone
        
        # Get color
        if milestone.color:
            color = milestone.color
        else:
            idx = self.config.milestones.index(milestone)
            color = self.theme.colors.get_accent(idx)
        
        # Draw connector line
        x1, y1 = ml.connector_start
        x2, y2 = ml.connector_end
        self.draw_line(
            x1, y1, x2, y2,
            color,
            self.theme.connector_width,
            opacity=opacity,
            dashed=True,
        )
        
        # Draw marker
        marker_x = ml.marker_pos.center_x
        marker_y = ml.marker_pos.center_y
        
        if milestone.highlight:
            # Larger, highlighted marker
            self.draw_circle(
                marker_x, marker_y,
                self.theme.marker_radius * 1.5,
                color,
                self.theme.colors.background,
                self.theme.marker_border_width * 1.5,
                opacity=opacity,
            )
            # Inner circle
            self.draw_circle(
                marker_x, marker_y,
                self.theme.marker_radius * 0.8,
                self.theme.colors.background,
                opacity=opacity,
            )
        else:
            self.draw_circle(
                marker_x, marker_y,
                self.theme.marker_radius,
                color,
                self.theme.colors.background,
                self.theme.marker_border_width,
                opacity=opacity,
            )
        
        # Draw label
        self.draw_text(
            milestone.title,
            ml.label_pos.x, ml.label_pos.y,
            self.theme.label_font,
            self.theme.colors.text_primary,
            max_width=ml.label_pos.width,
            align="center",
            opacity=opacity,
        )
        
        # Draw date
        date_str = milestone.date.strftime("%b %d, %Y")
        if ml.is_above:
            date_y = ml.label_pos.y + self.theme.label_font.size + 5
        else:
            date_y = ml.label_pos.y - 15
        
        self.draw_text(
            date_str,
            ml.label_pos.x, date_y,
            self.theme.date_font,
            self.theme.colors.text_secondary,
            max_width=ml.label_pos.width,
            align="center",
            opacity=opacity,
        )
        
        # Draw description
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

