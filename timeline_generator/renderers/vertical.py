"""Vertical timeline renderer."""

from ..core.layout import LayoutEngine, TimelineLayout, MilestoneLayout
from ..core.scale import date_to_position
from .base import BaseRenderer


class VerticalRenderer(BaseRenderer):
    """Renderer for vertical timeline style."""
    
    def calculate_layout(self) -> TimelineLayout:
        """Calculate vertical layout."""
        engine = LayoutEngine(
            self.config,
            self.scale_info,
            self.width,
            self.height,
        )
        return engine.calculate_vertical_layout()
    
    def draw_axis(self, layout: TimelineLayout) -> None:
        """Draw the vertical timeline axis."""
        x1, y1 = layout.axis_start
        x2, y2 = layout.axis_end
        
        # Main line
        self.draw_line(
            x1, y1, x2, y2,
            self.theme.colors.primary,
            self.theme.line_width,
        )
        
        # Arrow head at bottom
        arrow_size = 12
        self.ctx.move_to(x2, y2)
        self.ctx.line_to(x2 - arrow_size / 2, y2 - arrow_size)
        self.ctx.line_to(x2 + arrow_size / 2, y2 - arrow_size)
        self.ctx.close_path()
        
        r, g, b, _ = self.theme.hex_to_rgba(self.theme.colors.primary)
        self.ctx.set_source_rgba(r, g, b, 1)
        self.ctx.fill()
    
    def draw_scale_markers(self, layout: TimelineLayout) -> None:
        """Draw time scale markers on the axis."""
        x1, y1 = layout.axis_start
        _, y2 = layout.axis_end
        timeline_height = y2 - y1
        
        # Draw major ticks
        for tick, label in zip(
            self.scale_info.major_ticks,
            self.scale_info.unit_labels,
        ):
            y = date_to_position(tick, self.scale_info, timeline_height) + y1
            
            # Tick mark
            tick_width = 10
            self.draw_line(
                x1 - tick_width / 2, y,
                x1 + tick_width / 2, y,
                self.theme.colors.primary,
                self.theme.connector_width,
            )
    
    def draw_milestone(
        self,
        ml: MilestoneLayout,
        layout: TimelineLayout,
        opacity: float = 1.0,
    ) -> None:
        """Draw a milestone on the vertical timeline."""
        milestone = ml.milestone
        
        # Get color
        if milestone.color:
            color = milestone.color
        else:
            idx = self.config.milestones.index(milestone)
            color = self.theme.colors.get_accent(idx)
        
        is_left = ml.is_above  # Reused for left/right
        
        # Draw connector line
        x1, y1 = ml.connector_start
        x2, y2 = ml.connector_end
        self.draw_line(
            x1, y1, x2, y2,
            color,
            self.theme.connector_width,
            opacity=opacity,
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
        else:
            self.draw_circle(
                marker_x, marker_y,
                self.theme.marker_radius,
                color,
                self.theme.colors.background,
                self.theme.marker_border_width,
                opacity=opacity,
            )
        
        # Draw content card
        card_x = ml.label_pos.x
        card_y = ml.label_pos.y - 10
        card_width = ml.label_pos.width
        card_height = ml.label_pos.height + 30
        
        if ml.description_pos and milestone.description:
            card_height += ml.description_pos.height + 10
        
        self.draw_rounded_rect(
            card_x, card_y,
            card_width, card_height,
            self.theme.corner_radius,
            self.theme.colors.background_alt,
            color,
            1.5,
            opacity=opacity,
        )
        
        # Draw date badge
        date_str = milestone.date.strftime("%b %d")
        badge_width = 60
        badge_height = 24
        
        if is_left:
            badge_x = card_x + card_width - badge_width - 8
        else:
            badge_x = card_x + 8
        
        self.draw_rounded_rect(
            badge_x, card_y + 8,
            badge_width, badge_height,
            badge_height / 2,
            color,
            opacity=opacity,
        )
        
        self.draw_text(
            date_str,
            badge_x, card_y + 10,
            self.theme.date_font,
            self.theme.colors.text_light,
            max_width=badge_width,
            align="center",
            opacity=opacity,
        )
        
        # Draw title
        self.draw_text(
            milestone.title,
            card_x + 12, card_y + 40,
            self.theme.label_font,
            self.theme.colors.text_primary,
            max_width=card_width - 24,
            align="left" if is_left else "left",
            opacity=opacity,
        )
        
        # Draw description
        if ml.description_pos and milestone.description:
            self.draw_text(
                milestone.description,
                card_x + 12, card_y + 60,
                self.theme.description_font,
                self.theme.colors.text_secondary,
                max_width=card_width - 24,
                opacity=opacity,
            )

