"""Gantt chart style renderer."""

from ..core.layout import LayoutEngine, TimelineLayout, MilestoneLayout
from ..core.scale import date_to_position
from .base import BaseRenderer


class GanttRenderer(BaseRenderer):
    """Renderer for Gantt chart style timeline."""
    
    def calculate_layout(self) -> TimelineLayout:
        """Calculate Gantt layout."""
        engine = LayoutEngine(
            self.config,
            self.scale_info,
            self.width,
            self.height,
        )
        return engine.calculate_gantt_layout()
    
    def draw_axis(self, layout: TimelineLayout) -> None:
        """Draw the Gantt chart header/time axis."""
        x1, y1 = layout.axis_start
        x2, y2 = layout.axis_end
        
        # Header background
        self.draw_rounded_rect(
            x1, y1,
            x2 - x1, y2 - y1,
            0,  # No rounding for header
            self.theme.colors.primary,
        )
        
        # Draw time scale divisions
        chart_width = x2 - x1
        header_height = y2 - y1
        
        for i, (tick, label) in enumerate(zip(
            self.scale_info.major_ticks,
            self.scale_info.unit_labels,
        )):
            x = date_to_position(tick, self.scale_info, chart_width) + x1
            
            # Vertical grid line
            self.draw_line(
                x, y1,
                x, self.height - self.theme.margin,
                self.theme.colors.border,
                1,
            )
            
            # Label in header
            if i < len(self.scale_info.unit_labels):
                self.draw_text(
                    label,
                    x + 5, y1 + 8,
                    self.theme.date_font,
                    self.theme.colors.text_light,
                    max_width=80,
                )
    
    def draw_scale_markers(self, layout: TimelineLayout) -> None:
        """Draw row separators."""
        label_width = 150
        chart_left = self.theme.margin + label_width + 10
        
        # Horizontal row dividers
        num_milestones = len(self.config.milestones)
        timeline_height = layout.timeline_area.height
        row_height = min(50, max(30, timeline_height / max(1, num_milestones)))
        
        for i in range(num_milestones + 1):
            y = layout.timeline_area.y + i * row_height
            self.draw_line(
                self.theme.margin, y,
                self.width - self.theme.margin, y,
                self.theme.colors.border,
                0.5,
            )
    
    def draw_milestone(
        self,
        ml: MilestoneLayout,
        layout: TimelineLayout,
        opacity: float = 1.0,
    ) -> None:
        """Draw a Gantt bar for the milestone."""
        milestone = ml.milestone
        
        # Get color
        if milestone.color:
            color = milestone.color
        else:
            idx = self.config.milestones.index(milestone)
            color = self.theme.colors.get_accent(idx)
        
        # Draw label in left column
        self.draw_text(
            milestone.title,
            ml.label_pos.x + 10, ml.label_pos.y + 10,
            self.theme.label_font,
            self.theme.colors.text_primary,
            max_width=ml.label_pos.width - 20,
            opacity=opacity,
        )
        
        # Draw bar
        bar = ml.marker_pos
        bar_height = bar.height * 0.7
        bar_y = bar.y + (bar.height - bar_height) / 2
        
        # Bar background (full width shows incomplete)
        if milestone.progress is not None and milestone.progress < 100:
            self.draw_rounded_rect(
                bar.x, bar_y,
                bar.width, bar_height,
                bar_height / 4,
                self.theme.colors.background_alt,
                self.theme.colors.border,
                1,
                opacity=opacity,
            )
            
            # Progress fill
            progress_width = bar.width * (milestone.progress / 100)
            if progress_width > 0:
                self.draw_rounded_rect(
                    bar.x, bar_y,
                    progress_width, bar_height,
                    bar_height / 4,
                    color,
                    opacity=opacity,
                )
        else:
            # Full bar
            self.draw_rounded_rect(
                bar.x, bar_y,
                bar.width, bar_height,
                bar_height / 4,
                color,
                opacity=opacity,
            )
        
        # If it's a point milestone (no duration), draw a diamond
        if not milestone.end_date:
            diamond_size = bar_height * 0.8
            center_x = bar.x + bar.width / 2
            center_y = bar_y + bar_height / 2
            
            self.ctx.new_path()
            self.ctx.move_to(center_x, center_y - diamond_size / 2)
            self.ctx.line_to(center_x + diamond_size / 2, center_y)
            self.ctx.line_to(center_x, center_y + diamond_size / 2)
            self.ctx.line_to(center_x - diamond_size / 2, center_y)
            self.ctx.close_path()
            
            r, g, b, _ = self.theme.hex_to_rgba(color)
            self.ctx.set_source_rgba(r, g, b, opacity)
            self.ctx.fill()
        
        # Date labels
        date_str = milestone.date.strftime("%b %d")
        self.draw_text(
            date_str,
            bar.x, bar.y + bar.height + 2,
            self.theme.date_font,
            self.theme.colors.text_secondary,
            opacity=opacity * 0.8,
        )
        
        if milestone.end_date:
            end_str = milestone.end_date.strftime("%b %d")
            self.draw_text(
                end_str,
                bar.x + bar.width - 40, bar.y + bar.height + 2,
                self.theme.date_font,
                self.theme.colors.text_secondary,
                opacity=opacity * 0.8,
            )

