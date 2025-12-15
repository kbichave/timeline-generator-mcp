"""Layout engine for positioning timeline elements with collision detection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from ..models import Milestone, TimelineConfig
from .scale import ScaleInfo, date_to_position


@dataclass
class ElementPosition:
    """Position and dimensions of a layout element."""
    
    x: float
    y: float
    width: float
    height: float
    
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    def intersects(self, other: "ElementPosition", padding: float = 5) -> bool:
        """Check if this element intersects with another (with optional padding)."""
        return not (
            self.right + padding < other.x or
            other.right + padding < self.x or
            self.bottom + padding < other.y or
            other.bottom + padding < self.y
        )
    
    def horizontal_overlap(self, other: "ElementPosition", padding: float = 5) -> float:
        """Calculate horizontal overlap amount (0 if no overlap)."""
        left = max(self.x - padding, other.x - padding)
        right = min(self.right + padding, other.right + padding)
        return max(0, right - left)
    
    def move_by(self, dx: float = 0, dy: float = 0) -> "ElementPosition":
        """Return a new position moved by the given offsets."""
        return ElementPosition(
            x=self.x + dx,
            y=self.y + dy,
            width=self.width,
            height=self.height,
        )


@dataclass
class MilestoneLayout:
    """Layout information for a milestone."""
    
    milestone: Milestone
    marker_pos: ElementPosition
    label_pos: ElementPosition
    description_pos: Optional[ElementPosition] = None
    connector_start: tuple[float, float] = (0, 0)
    connector_end: tuple[float, float] = (0, 0)
    is_above: bool = True  # For horizontal: above or below line
    row: int = 0  # For vertical: alternating left/right or row index
    level: int = 0  # For multi-level layouts to avoid overlap


@dataclass
class TimelineLayout:
    """Complete layout for a timeline."""
    
    config: TimelineConfig
    scale_info: ScaleInfo
    canvas_width: float
    canvas_height: float
    
    # Layout regions
    title_area: ElementPosition = field(default_factory=lambda: ElementPosition(0, 0, 0, 0))
    timeline_area: ElementPosition = field(default_factory=lambda: ElementPosition(0, 0, 0, 0))
    legend_area: Optional[ElementPosition] = None
    
    # Milestone layouts
    milestone_layouts: list[MilestoneLayout] = field(default_factory=list)
    
    # Axis/line
    axis_start: tuple[float, float] = (0, 0)
    axis_end: tuple[float, float] = (0, 0)


class LayoutEngine:
    """Engine for calculating timeline layouts with collision detection."""
    
    def __init__(
        self,
        config: TimelineConfig,
        scale_info: ScaleInfo,
        width: float,
        height: float,
    ):
        self.config = config
        self.scale_info = scale_info
        self.width = width
        self.height = height
        
        # Margins and spacing
        self.margin = 40
        self.title_height = 60 if config.show_title else 0
        self.marker_size = 16
        self.label_height = 24
        self.description_height = 18
        self.row_spacing = 15
        self.min_label_gap = 15  # Minimum gap between labels
        
        # Auto-layout settings
        self.max_levels = 6  # Maximum levels for stacking
        self.level_spacing = 50  # Vertical spacing between levels
    
    def _detect_label_collisions(
        self, 
        layouts: List[MilestoneLayout],
        check_descriptions: bool = True
    ) -> List[tuple[int, int]]:
        """Detect collisions between milestone labels.
        
        Returns list of (index1, index2) pairs that collide.
        """
        collisions = []
        for i in range(len(layouts)):
            for j in range(i + 1, len(layouts)):
                # Check label collision
                if layouts[i].label_pos.intersects(layouts[j].label_pos, self.min_label_gap):
                    collisions.append((i, j))
                # Check description collision if both have descriptions
                elif (check_descriptions and 
                      layouts[i].description_pos and layouts[j].description_pos and
                      layouts[i].description_pos.intersects(layouts[j].description_pos, self.min_label_gap)):
                    collisions.append((i, j))
        return collisions
    
    def _calculate_density(self, x_positions: List[float], timeline_width: float) -> float:
        """Calculate how dense the timeline is (0-1, higher = more dense)."""
        if len(x_positions) <= 1:
            return 0.0
        
        # Calculate average distance between consecutive milestones
        sorted_positions = sorted(x_positions)
        gaps = [sorted_positions[i+1] - sorted_positions[i] for i in range(len(sorted_positions)-1)]
        avg_gap = sum(gaps) / len(gaps)
        
        # Minimum acceptable gap is label_width + min_gap
        min_acceptable_gap = 120 + self.min_label_gap
        
        return max(0.0, min(1.0, 1.0 - (avg_gap / min_acceptable_gap)))
    
    def _assign_smart_levels(
        self, 
        x_positions: List[float],
        timeline_width: float,
    ) -> List[int]:
        """Assign levels to milestones to minimize overlap.
        
        Uses a greedy interval scheduling approach to assign non-overlapping levels.
        Returns list of level assignments (0, 1, 2, etc.) for each milestone.
        """
        n = len(x_positions)
        if n == 0:
            return []
        
        # Create list of (x_pos, original_index) sorted by x position
        indexed_positions = sorted(enumerate(x_positions), key=lambda x: x[1])
        
        # Use a fixed label width that ensures readability
        label_width = 150  # Fixed width for consistent layout
        required_gap = label_width + self.min_label_gap
        
        # Assign levels greedily - each level tracks occupied x ranges
        levels = [0] * n
        
        # Track occupied ranges per level: level -> list of (start_x, end_x)
        level_ranges: dict[int, List[tuple[float, float]]] = {}
        
        def can_fit_at_level(x_pos: float, level: int) -> bool:
            """Check if a label at x_pos can fit at the given level."""
            if level not in level_ranges:
                return True
            
            label_start = x_pos - label_width / 2 - self.min_label_gap
            label_end = x_pos + label_width / 2 + self.min_label_gap
            
            for start, end in level_ranges[level]:
                # Check for overlap
                if not (label_end < start or label_start > end):
                    return False
            return True
        
        def add_to_level(x_pos: float, level: int):
            """Add a label range to a level."""
            if level not in level_ranges:
                level_ranges[level] = []
            
            label_start = x_pos - label_width / 2
            label_end = x_pos + label_width / 2
            level_ranges[level].append((label_start, label_end))
        
        for orig_idx, x_pos in indexed_positions:
            # Find the lowest level where this milestone fits without collision
            assigned_level = 0
            for level in range(self.max_levels):
                if can_fit_at_level(x_pos, level):
                    assigned_level = level
                    break
                assigned_level = level + 1
            
            # If we exceeded max levels, force fit at the level with least conflict
            if assigned_level >= self.max_levels:
                assigned_level = assigned_level % self.max_levels
            
            levels[orig_idx] = assigned_level
            add_to_level(x_pos, assigned_level)
        
        return levels
    
    def _optimize_layout(self, layouts: List[MilestoneLayout], axis_y: float) -> List[MilestoneLayout]:
        """Optimize layout to reduce overlaps by adjusting levels and positions."""
        if len(layouts) <= 1:
            return layouts
        
        # Get x positions and assign smart levels
        x_positions = [ml.marker_pos.center_x for ml in layouts]
        timeline_width = max(x_positions) - min(x_positions) if x_positions else self.width
        levels = self._assign_smart_levels(x_positions, timeline_width)
        
        # Use consistent label width
        label_width = 130
        
        # Calculate density for description visibility
        n = len(layouts)
        avg_spacing = timeline_width / max(1, n)
        
        # Update layouts with new levels
        optimized = []
        for i, ml in enumerate(layouts):
            level = levels[i]
            
            # Determine if above or below based on level
            # Even levels go above, odd levels go below
            is_above = level % 2 == 0
            level_offset = (level // 2) * self.level_spacing
            
            # Calculate new positions
            x_pos = ml.marker_pos.center_x
            
            if is_above:
                label_y = axis_y - self.marker_size - 20 - self.label_height - level_offset
            else:
                label_y = axis_y + self.marker_size + 20 + level_offset
            
            new_label_pos = ElementPosition(
                x=x_pos - label_width / 2,
                y=label_y,
                width=label_width,
                height=self.label_height,
            )
            
            # Update description position (only show for lower density)
            new_desc_pos = None
            if ml.description_pos and ml.milestone.description and avg_spacing > 180:
                if is_above:
                    desc_y = label_y - self.description_height - 5
                else:
                    desc_y = label_y + self.label_height + 5
                
                new_desc_pos = ElementPosition(
                    x=x_pos - label_width / 2 - 10,
                    y=desc_y,
                    width=label_width + 20,
                    height=self.description_height,
                )
            
            # Update connector
            if is_above:
                connector_start = (x_pos, axis_y - self.marker_size / 2)
                connector_end = (x_pos, new_label_pos.bottom)
            else:
                connector_start = (x_pos, axis_y + self.marker_size / 2)
                connector_end = (x_pos, new_label_pos.y)
            
            optimized.append(MilestoneLayout(
                milestone=ml.milestone,
                marker_pos=ml.marker_pos,
                label_pos=new_label_pos,
                description_pos=new_desc_pos,
                connector_start=connector_start,
                connector_end=connector_end,
                is_above=is_above,
                row=ml.row,
                level=level,
            ))
        
        return optimized
    
    def calculate_horizontal_layout(self) -> TimelineLayout:
        """Calculate layout for horizontal timeline with auto collision detection."""
        layout = TimelineLayout(
            config=self.config,
            scale_info=self.scale_info,
            canvas_width=self.width,
            canvas_height=self.height,
        )
        
        # Title area
        if self.config.show_title:
            layout.title_area = ElementPosition(
                x=self.margin,
                y=self.margin,
                width=self.width - 2 * self.margin,
                height=self.title_height,
            )
        
        # Timeline area (main content) - reduced gap from title
        timeline_top = self.margin + self.title_height + 10
        timeline_height = self.height - timeline_top - self.margin
        layout.timeline_area = ElementPosition(
            x=self.margin,
            y=timeline_top,
            width=self.width - 2 * self.margin,
            height=timeline_height,
        )
        
        # Axis line (horizontal center of timeline area)
        axis_y = layout.timeline_area.center_y
        layout.axis_start = (layout.timeline_area.x, axis_y)
        layout.axis_end = (layout.timeline_area.right, axis_y)
        
        # Calculate milestone positions
        timeline_width = layout.timeline_area.width
        
        # First pass: calculate initial positions
        initial_layouts = []
        x_positions = []
        
        for i, milestone in enumerate(self.config.milestones):
            x_pos = date_to_position(
                milestone.date,
                self.scale_info,
                timeline_width,
            ) + layout.timeline_area.x
            x_positions.append(x_pos)
            
            is_above = i % 2 == 0
            
            # Marker position (on the axis line)
            marker_pos = ElementPosition(
                x=x_pos - self.marker_size / 2,
                y=axis_y - self.marker_size / 2,
                width=self.marker_size,
                height=self.marker_size,
            )
            
            # Label position (above or below)
            if is_above:
                label_y = axis_y - self.marker_size - 10 - self.label_height
            else:
                label_y = axis_y + self.marker_size + 10
            
            label_pos = ElementPosition(
                x=x_pos - 65,  # Centered, with some width
                y=label_y,
                width=130,
                height=self.label_height,
            )
            
            # Description position
            desc_pos = None
            if self.config.show_descriptions and milestone.description:
                if is_above:
                    desc_y = label_y - self.description_height - 5
                else:
                    desc_y = label_y + self.label_height + 5
                
                desc_pos = ElementPosition(
                    x=x_pos - 80,
                    y=desc_y,
                    width=160,
                    height=self.description_height,
                )
            
            # Connector line
            if is_above:
                connector_start = (x_pos, axis_y - self.marker_size / 2)
                connector_end = (x_pos, label_y + self.label_height)
            else:
                connector_start = (x_pos, axis_y + self.marker_size / 2)
                connector_end = (x_pos, label_y)
            
            initial_layouts.append(
                MilestoneLayout(
                    milestone=milestone,
                    marker_pos=marker_pos,
                    label_pos=label_pos,
                    description_pos=desc_pos,
                    connector_start=connector_start,
                    connector_end=connector_end,
                    is_above=is_above,
                    level=0,
                )
            )
        
        # Always optimize layout to reduce overlaps (cleaner result)
        # Apply smart level assignment for all timelines with 3+ milestones
        if len(self.config.milestones) >= 3:
            optimized_layouts = self._optimize_layout(initial_layouts, axis_y)
            layout.milestone_layouts = optimized_layouts
        else:
            layout.milestone_layouts = initial_layouts
        
        return layout
    
    def _optimize_vertical_layout(
        self, 
        layouts: List[MilestoneLayout], 
        axis_x: float,
        content_width: float,
        min_card_height: float = 80,
    ) -> List[MilestoneLayout]:
        """Optimize vertical layout to prevent card overlaps."""
        if len(layouts) <= 1:
            return layouts
        
        # Separate left and right layouts
        left_layouts = [(i, ml) for i, ml in enumerate(layouts) if ml.is_above]
        right_layouts = [(i, ml) for i, ml in enumerate(layouts) if not ml.is_above]
        
        def adjust_side(side_layouts: List[tuple[int, MilestoneLayout]]) -> dict:
            """Adjust positions for one side to prevent overlaps."""
            adjustments = {}
            if len(side_layouts) <= 1:
                return adjustments
            
            # Sort by y position
            sorted_layouts = sorted(side_layouts, key=lambda x: x[1].marker_pos.center_y)
            
            last_bottom = 0
            for idx, (orig_idx, ml) in enumerate(sorted_layouts):
                current_y = ml.label_pos.y
                card_height = min_card_height
                
                if ml.description_pos:
                    card_height = ml.description_pos.bottom - ml.label_pos.y + 20
                
                # Check if this card would overlap with previous
                if current_y < last_bottom + self.min_label_gap:
                    # Push this card down
                    new_y = last_bottom + self.min_label_gap
                    adjustments[orig_idx] = new_y - ml.label_pos.y
                    last_bottom = new_y + card_height
                else:
                    last_bottom = current_y + card_height
            
            return adjustments
        
        # Get adjustments for both sides
        left_adjustments = adjust_side(left_layouts)
        right_adjustments = adjust_side(right_layouts)
        
        # Apply adjustments
        optimized = []
        for i, ml in enumerate(layouts):
            dy = left_adjustments.get(i, 0) or right_adjustments.get(i, 0)
            
            if dy != 0:
                new_label_pos = ml.label_pos.move_by(dy=dy)
                new_desc_pos = ml.description_pos.move_by(dy=dy) if ml.description_pos else None
                new_connector_end = (ml.connector_end[0], ml.connector_end[1] + dy)
                
                optimized.append(MilestoneLayout(
                    milestone=ml.milestone,
                    marker_pos=ml.marker_pos,
                    label_pos=new_label_pos,
                    description_pos=new_desc_pos,
                    connector_start=ml.connector_start,
                    connector_end=new_connector_end,
                    is_above=ml.is_above,
                    row=ml.row,
                    level=ml.level,
                ))
            else:
                optimized.append(ml)
        
        return optimized
    
    def calculate_vertical_layout(self) -> TimelineLayout:
        """Calculate layout for vertical timeline with collision detection."""
        layout = TimelineLayout(
            config=self.config,
            scale_info=self.scale_info,
            canvas_width=self.width,
            canvas_height=self.height,
        )
        
        # Title area
        if self.config.show_title:
            layout.title_area = ElementPosition(
                x=self.margin,
                y=self.margin,
                width=self.width - 2 * self.margin,
                height=self.title_height,
            )
        
        # Timeline area - reduced gap from title
        timeline_top = self.margin + self.title_height + 10
        timeline_height = self.height - timeline_top - self.margin
        layout.timeline_area = ElementPosition(
            x=self.margin,
            y=timeline_top,
            width=self.width - 2 * self.margin,
            height=timeline_height,
        )
        
        # Axis line (vertical center of width)
        axis_x = self.width / 2
        layout.axis_start = (axis_x, layout.timeline_area.y)
        layout.axis_end = (axis_x, layout.timeline_area.bottom)
        
        # Calculate milestone positions
        timeline_height = layout.timeline_area.height
        content_width = (self.width - 2 * self.margin - 40) / 2  # Width for each side
        
        initial_layouts = []
        
        for i, milestone in enumerate(self.config.milestones):
            y_pos = date_to_position(
                milestone.date,
                self.scale_info,
                timeline_height,
            ) + layout.timeline_area.y
            
            is_left = i % 2 == 0
            
            # Marker position (on the axis line)
            marker_pos = ElementPosition(
                x=axis_x - self.marker_size / 2,
                y=y_pos - self.marker_size / 2,
                width=self.marker_size,
                height=self.marker_size,
            )
            
            # Label position (left or right)
            if is_left:
                label_x = axis_x - 20 - content_width
            else:
                label_x = axis_x + 20
            
            label_pos = ElementPosition(
                x=label_x,
                y=y_pos - self.label_height / 2,
                width=content_width,
                height=self.label_height,
            )
            
            # Description position
            desc_pos = None
            if self.config.show_descriptions and milestone.description:
                desc_pos = ElementPosition(
                    x=label_x,
                    y=y_pos + self.label_height / 2 + 5,
                    width=content_width,
                    height=self.description_height * 2,  # Allow 2 lines
                )
            
            # Connector line
            if is_left:
                connector_start = (axis_x - self.marker_size / 2, y_pos)
                connector_end = (label_x + content_width, y_pos)
            else:
                connector_start = (axis_x + self.marker_size / 2, y_pos)
                connector_end = (label_x, y_pos)
            
            initial_layouts.append(
                MilestoneLayout(
                    milestone=milestone,
                    marker_pos=marker_pos,
                    label_pos=label_pos,
                    description_pos=desc_pos,
                    connector_start=connector_start,
                    connector_end=connector_end,
                    is_above=is_left,  # Reusing for left/right
                    level=0,
                )
            )
        
        # Optimize layout to prevent overlaps
        layout.milestone_layouts = self._optimize_vertical_layout(
            initial_layouts, axis_x, content_width
        )
        
        return layout
    
    def calculate_gantt_layout(self) -> TimelineLayout:
        """Calculate layout for Gantt chart."""
        layout = TimelineLayout(
            config=self.config,
            scale_info=self.scale_info,
            canvas_width=self.width,
            canvas_height=self.height,
        )
        
        # Title area
        if self.config.show_title:
            layout.title_area = ElementPosition(
                x=self.margin,
                y=self.margin,
                width=self.width - 2 * self.margin,
                height=self.title_height,
            )
        
        # Header row for time scale
        header_height = 40
        header_top = self.margin + self.title_height + 10
        
        # Timeline area (chart content)
        timeline_top = header_top + header_height + 10
        timeline_height = self.height - timeline_top - self.margin
        
        label_column_width = 150
        chart_left = self.margin + label_column_width + 10
        chart_width = self.width - chart_left - self.margin
        
        layout.timeline_area = ElementPosition(
            x=chart_left,
            y=timeline_top,
            width=chart_width,
            height=timeline_height,
        )
        
        # Row height based on number of milestones
        num_milestones = len(self.config.milestones)
        row_height = min(50, max(30, timeline_height / max(1, num_milestones)))
        
        for i, milestone in enumerate(self.config.milestones):
            row_y = timeline_top + i * row_height
            
            # Calculate bar position and width
            start_x = date_to_position(
                milestone.date,
                self.scale_info,
                chart_width,
            ) + chart_left
            
            if milestone.end_date:
                end_x = date_to_position(
                    milestone.end_date,
                    self.scale_info,
                    chart_width,
                ) + chart_left
                bar_width = max(10, end_x - start_x)
            else:
                bar_width = 20  # Point milestone
            
            # Bar position (the marker in Gantt is the bar)
            marker_pos = ElementPosition(
                x=start_x,
                y=row_y + 5,
                width=bar_width,
                height=row_height - 10,
            )
            
            # Label position (in the left column)
            label_pos = ElementPosition(
                x=self.margin,
                y=row_y,
                width=label_column_width,
                height=row_height,
            )
            
            layout.milestone_layouts.append(
                MilestoneLayout(
                    milestone=milestone,
                    marker_pos=marker_pos,
                    label_pos=label_pos,
                    row=i,
                )
            )
        
        # Axis represents the header timeline
        layout.axis_start = (chart_left, header_top)
        layout.axis_end = (chart_left + chart_width, header_top + header_height)
        
        return layout
    
    def _optimize_roadmap_lane(
        self,
        lane_layouts: List[MilestoneLayout],
        lane_y: float,
        lane_height: float,
        card_width: float = 140,
    ) -> List[MilestoneLayout]:
        """Optimize card positions within a lane to prevent overlaps."""
        if len(lane_layouts) <= 1:
            return lane_layouts
        
        # Sort by x position
        sorted_layouts = sorted(lane_layouts, key=lambda ml: ml.marker_pos.x)
        
        optimized = []
        last_right = 0
        
        for ml in sorted_layouts:
            current_x = ml.marker_pos.x
            
            # Check if this card overlaps with previous
            if current_x < last_right + self.min_label_gap:
                # Shift card to the right
                new_x = last_right + self.min_label_gap
                dx = new_x - current_x
                
                new_marker = ml.marker_pos.move_by(dx=dx)
                new_label = ml.label_pos.move_by(dx=dx)
                new_desc = ml.description_pos.move_by(dx=dx) if ml.description_pos else None
                
                optimized.append(MilestoneLayout(
                    milestone=ml.milestone,
                    marker_pos=new_marker,
                    label_pos=new_label,
                    description_pos=new_desc,
                    connector_start=ml.connector_start,
                    connector_end=ml.connector_end,
                    is_above=ml.is_above,
                    row=ml.row,
                    level=ml.level,
                ))
                last_right = new_x + card_width
            else:
                optimized.append(ml)
                last_right = current_x + card_width
        
        return optimized
    
    def calculate_roadmap_layout(self) -> TimelineLayout:
        """Calculate layout for roadmap style with collision detection."""
        layout = TimelineLayout(
            config=self.config,
            scale_info=self.scale_info,
            canvas_width=self.width,
            canvas_height=self.height,
        )
        
        # Title area
        if self.config.show_title:
            layout.title_area = ElementPosition(
                x=self.margin,
                y=self.margin,
                width=self.width - 2 * self.margin,
                height=self.title_height,
            )
        
        # Get categories for swimlanes
        categories = self.config.unique_categories
        num_lanes = len(categories)
        
        # Header for time scale
        header_height = 50
        header_top = self.margin + self.title_height + 10
        
        # Lane labels column
        lane_label_width = 120
        chart_left = self.margin + lane_label_width + 10
        chart_width = self.width - chart_left - self.margin
        
        # Swimlanes area
        lanes_top = header_top + header_height + 10
        lanes_height = self.height - lanes_top - self.margin
        lane_height = lanes_height / max(1, num_lanes)
        
        layout.timeline_area = ElementPosition(
            x=chart_left,
            y=lanes_top,
            width=chart_width,
            height=lanes_height,
        )
        
        # Group milestones by category
        category_map = {cat: i for i, cat in enumerate(categories)}
        
        # Collect layouts by lane for optimization
        lane_layouts: dict[int, List[MilestoneLayout]] = {i: [] for i in range(num_lanes)}
        
        for milestone in self.config.milestones:
            cat = milestone.category or "default"
            lane_idx = category_map.get(cat, 0)
            lane_y = lanes_top + lane_idx * lane_height
            
            # X position based on date
            x_pos = date_to_position(
                milestone.date,
                self.scale_info,
                chart_width,
            ) + chart_left
            
            # Card-like marker - use smaller cards if many milestones
            card_width = min(140, chart_width / max(3, len(self.config.milestones) / num_lanes))
            card_height = lane_height - 20
            
            marker_pos = ElementPosition(
                x=x_pos - card_width / 2,
                y=lane_y + 10,
                width=card_width,
                height=card_height,
            )
            
            # Label inside the card
            label_pos = ElementPosition(
                x=marker_pos.x + 10,
                y=marker_pos.y + 10,
                width=card_width - 20,
                height=24,
            )
            
            # Description below title in card
            desc_pos = None
            if self.config.show_descriptions and milestone.description:
                desc_pos = ElementPosition(
                    x=marker_pos.x + 10,
                    y=marker_pos.y + 38,
                    width=card_width - 20,
                    height=card_height - 48,
                )
            
            ml = MilestoneLayout(
                milestone=milestone,
                marker_pos=marker_pos,
                label_pos=label_pos,
                description_pos=desc_pos,
                row=lane_idx,
                level=0,
            )
            lane_layouts[lane_idx].append(ml)
        
        # Optimize each lane
        for lane_idx, layouts in lane_layouts.items():
            lane_y = lanes_top + lane_idx * lane_height
            optimized = self._optimize_roadmap_lane(layouts, lane_y, lane_height)
            layout.milestone_layouts.extend(optimized)
        
        # Sort by original order (date)
        layout.milestone_layouts.sort(key=lambda ml: ml.milestone.date)
        
        # Axis represents the header
        layout.axis_start = (chart_left, header_top)
        layout.axis_end = (chart_left + chart_width, header_top + header_height)
        
        return layout
    
    def calculate_infographic_layout(self) -> TimelineLayout:
        """Calculate layout for infographic style."""
        layout = TimelineLayout(
            config=self.config,
            scale_info=self.scale_info,
            canvas_width=self.width,
            canvas_height=self.height,
        )
        
        # Title area (larger for infographic)
        title_height = 100 if self.config.show_title else 0
        if self.config.show_title:
            layout.title_area = ElementPosition(
                x=self.margin,
                y=self.margin,
                width=self.width - 2 * self.margin,
                height=title_height,
            )
        
        # Main content area
        content_top = self.margin + title_height + 30
        content_height = self.height - content_top - self.margin
        content_width = self.width - 2 * self.margin
        
        layout.timeline_area = ElementPosition(
            x=self.margin,
            y=content_top,
            width=content_width,
            height=content_height,
        )
        
        # Winding path through milestones
        num_milestones = len(self.config.milestones)
        
        # Calculate positions in a flowing layout
        cols = 3
        row_height = content_height / ((num_milestones + cols - 1) // cols + 0.5)
        col_width = content_width / cols
        
        for i, milestone in enumerate(self.config.milestones):
            row = i // cols
            col = i % cols
            
            # Alternate direction for snake-like pattern
            if row % 2 == 1:
                col = cols - 1 - col
            
            x = self.margin + col * col_width + col_width / 2
            y = content_top + row * row_height + row_height / 2
            
            # Large circular marker
            marker_size = 80
            marker_pos = ElementPosition(
                x=x - marker_size / 2,
                y=y - marker_size / 2,
                width=marker_size,
                height=marker_size,
            )
            
            # Label below marker
            label_pos = ElementPosition(
                x=x - 80,
                y=y + marker_size / 2 + 10,
                width=160,
                height=30,
            )
            
            # Description
            desc_pos = None
            if self.config.show_descriptions and milestone.description:
                desc_pos = ElementPosition(
                    x=x - 90,
                    y=y + marker_size / 2 + 45,
                    width=180,
                    height=40,
                )
            
            layout.milestone_layouts.append(
                MilestoneLayout(
                    milestone=milestone,
                    marker_pos=marker_pos,
                    label_pos=label_pos,
                    description_pos=desc_pos,
                    row=row,
                )
            )
        
        return layout

