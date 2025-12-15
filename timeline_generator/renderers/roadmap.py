"""Roadmap style renderer."""

from ..core.layout import LayoutEngine, TimelineLayout, MilestoneLayout
from ..core.scale import date_to_position
from .base import BaseRenderer


class RoadmapRenderer(BaseRenderer):
    """Renderer for product roadmap style timeline."""
    
    def calculate_layout(self) -> TimelineLayout:
        """Calculate roadmap layout."""
        engine = LayoutEngine(
            self.config,
            self.scale_info,
            self.width,
            self.height,
        )
        return engine.calculate_roadmap_layout()
    
    def draw_axis(self, layout: TimelineLayout) -> None:
        """Draw the roadmap header with time periods."""
        x1, y1 = layout.axis_start
        x2, y2 = layout.axis_end
        
        # Header background
        self.draw_rounded_rect(
            x1, y1,
            x2 - x1, y2 - y1,
            self.theme.corner_radius,
            self.theme.colors.primary_dark,
        )
        
        # Time period labels
        chart_width = x2 - x1
        
        for i, (tick, label) in enumerate(zip(
            self.scale_info.major_ticks,
            self.scale_info.unit_labels,
        )):
            x = date_to_position(tick, self.scale_info, chart_width) + x1
            
            # Separator line
            if i > 0:
                self.draw_line(
                    x, y1 + 5,
                    x, y2 - 5,
                    self.theme.colors.primary_light,
                    1,
                )
            
            # Label
            self.draw_text(
                label,
                x + 10, y1 + 12,
                self.theme.label_font,
                self.theme.colors.text_light,
                max_width=100,
            )
        
        # Draw swimlane labels
        categories = self.config.unique_categories
        lane_label_width = 120
        lanes_top = y2 + 10
        lanes_height = self.height - lanes_top - self.theme.margin
        lane_height = lanes_height / max(1, len(categories))
        
        for i, cat in enumerate(categories):
            lane_y = lanes_top + i * lane_height
            
            # Lane background (alternating)
            if i % 2 == 0:
                self.draw_rounded_rect(
                    self.theme.margin, lane_y,
                    self.width - 2 * self.theme.margin, lane_height,
                    0,
                    self.theme.colors.background_alt,
                )
            
            # Lane label
            self.draw_rounded_rect(
                self.theme.margin, lane_y + 5,
                lane_label_width - 10, lane_height - 10,
                self.theme.corner_radius,
                self.theme.colors.secondary,
            )
            
            self.draw_text(
                cat.title() if cat != "default" else "General",
                self.theme.margin + 10, lane_y + 15,
                self.theme.label_font,
                self.theme.colors.text_light,
                max_width=lane_label_width - 30,
            )
    
    def draw_scale_markers(self, layout: TimelineLayout) -> None:
        """Draw vertical time grid lines."""
        x1, _ = layout.axis_start
        x2, y2 = layout.axis_end
        chart_width = x2 - x1
        
        # Draw grid lines extending to the bottom
        for tick in self.scale_info.major_ticks:
            x = date_to_position(tick, self.scale_info, chart_width) + x1
            
            self.draw_line(
                x, y2,
                x, self.height - self.theme.margin,
                self.theme.colors.border,
                0.5,
                dashed=True,
            )
    
    def draw_milestone(
        self,
        ml: MilestoneLayout,
        layout: TimelineLayout,
        opacity: float = 1.0,
    ) -> None:
        """Draw a roadmap card for the milestone."""
        milestone = ml.milestone
        
        # Get color
        if milestone.color:
            color = milestone.color
        else:
            idx = self.config.milestones.index(milestone)
            color = self.theme.colors.get_accent(idx)
        
        # Draw card
        card = ml.marker_pos
        
        # Shadow effect
        if self.theme.use_shadows:
            shadow_offset = 3
            self.draw_rounded_rect(
                card.x + shadow_offset, card.y + shadow_offset,
                card.width, card.height,
                self.theme.corner_radius,
                self.theme.colors.shadow,
                opacity=opacity * 0.3,
            )
        
        # Card background
        self.draw_rounded_rect(
            card.x, card.y,
            card.width, card.height,
            self.theme.corner_radius,
            self.theme.colors.background,
            color,
            2,
            opacity=opacity,
        )
        
        # Color bar at top
        bar_height = 6
        self.draw_rounded_rect(
            card.x, card.y,
            card.width, bar_height + self.theme.corner_radius,
            self.theme.corner_radius,
            color,
            opacity=opacity,
        )
        # Cover bottom corners of the color bar
        self.ctx.rectangle(card.x, card.y + bar_height, card.width, self.theme.corner_radius)
        r, g, b, _ = self.theme.hex_to_rgba(color)
        self.ctx.set_source_rgba(r, g, b, opacity)
        self.ctx.fill()
        
        # Title
        self.draw_text(
            milestone.title,
            card.x + 10, card.y + bar_height + 10,
            self.theme.label_font,
            self.theme.colors.text_primary,
            max_width=card.width - 20,
            opacity=opacity,
        )
        
        # Date
        date_str = milestone.date.strftime("%b %d, %Y")
        self.draw_text(
            date_str,
            card.x + 10, card.y + bar_height + 32,
            self.theme.date_font,
            self.theme.colors.text_secondary,
            max_width=card.width - 20,
            opacity=opacity,
        )
        
        # Description (if space allows)
        if ml.description_pos and milestone.description:
            self.draw_text(
                milestone.description,
                card.x + 10, card.y + bar_height + 50,
                self.theme.description_font,
                self.theme.colors.text_secondary,
                max_width=card.width - 20,
                opacity=opacity,
            )
        
        # Highlight indicator
        if milestone.highlight:
            # Star or badge
            badge_size = 20
            self.draw_circle(
                card.x + card.width - 15, card.y + 15,
                badge_size / 2,
                self.theme.colors.warning,
                opacity=opacity,
            )
            
            # Star symbol (simple)
            self.draw_text(
                "★",
                card.x + card.width - 23, card.y + 5,
                self.theme.label_font,
                self.theme.colors.text_light,
                opacity=opacity,
            )

