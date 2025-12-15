"""Pydantic data models for timeline configuration and milestones."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TimeScale(str, Enum):
    """Supported time scales for timeline display."""
    
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TimelineStyle(str, Enum):
    """Available timeline visualization styles."""
    
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    GANTT = "gantt"
    ROADMAP = "roadmap"
    INFOGRAPHIC = "infographic"


class ThemeName(str, Enum):
    """Available theme names."""
    
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    DARK = "dark"


class OutputFormat(str, Enum):
    """Supported output formats."""
    
    PNG = "png"
    SVG = "svg"
    GIF = "gif"
    MP4 = "mp4"


class Milestone(BaseModel):
    """A single milestone on the timeline."""
    
    date: datetime
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None, description="Icon name or emoji")
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight: bool = Field(default=False, description="Make this milestone stand out")
    category: Optional[str] = Field(default=None, max_length=50)
    end_date: Optional[datetime] = Field(
        default=None, description="End date for duration-based milestones (Gantt)"
    )
    progress: Optional[float] = Field(
        default=None, ge=0, le=100, description="Completion percentage for Gantt charts"
    )
    
    @field_validator("date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse date strings into datetime objects."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            from dateutil.parser import parse
            return parse(v)
        raise ValueError(f"Cannot parse date: {v}")

    @field_validator("end_date")
    @classmethod
    def end_date_after_start(cls, v, info):
        """Ensure end_date is after date if provided."""
        if v is not None and info.data.get("date") is not None:
            if v < info.data["date"]:
                raise ValueError("end_date must be after date")
        return v


class ColorConfig(BaseModel):
    """Custom color configuration to override theme colors."""
    
    background: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    axis: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class OutputConfig(BaseModel):
    """Configuration for output generation."""
    
    format: OutputFormat = Field(default=OutputFormat.PNG)
    width: int = Field(default=1920, ge=100, le=8000)
    height: int = Field(default=1080, ge=100, le=8000)
    fps: int = Field(default=30, ge=1, le=120, description="Frames per second for animations")
    duration: float = Field(
        default=5.0, ge=0.5, le=60.0, description="Duration in seconds for animations"
    )
    quality: int = Field(default=95, ge=1, le=100, description="Output quality for images")
    transparent: bool = Field(
        default=False, description="Use transparent background (PNG/GIF only)"
    )


class TimelineConfig(BaseModel):
    """Complete timeline configuration."""
    
    title: str = Field(default="Timeline", min_length=1, max_length=200)
    subtitle: Optional[str] = Field(default=None, max_length=300)
    scale: TimeScale = Field(default=TimeScale.MONTHLY)
    style: TimelineStyle = Field(default=TimelineStyle.HORIZONTAL)
    theme: ThemeName = Field(default=ThemeName.MINIMAL)
    milestones: list[Milestone] = Field(default_factory=list, min_length=1)
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Custom color overrides
    colors: Optional[ColorConfig] = Field(
        default=None, description="Custom colors to override theme defaults"
    )
    
    # Optional layout customization
    show_title: bool = Field(default=True)
    show_dates: bool = Field(default=True)
    show_descriptions: bool = Field(default=True)
    compact_mode: bool = Field(default=False, description="Reduce spacing for dense timelines")
    
    # Category/swimlane settings (for roadmap and gantt)
    categories: Optional[list[str]] = Field(
        default=None, description="Ordered list of categories for swimlanes"
    )
    
    @field_validator("milestones")
    @classmethod
    def sort_milestones(cls, v):
        """Sort milestones by date."""
        return sorted(v, key=lambda m: m.date)
    
    @property
    def date_range(self) -> tuple[datetime, datetime]:
        """Get the date range covered by milestones."""
        if not self.milestones:
            now = datetime.now()
            return now, now
        dates = [m.date for m in self.milestones]
        # Include end dates for duration milestones
        for m in self.milestones:
            if m.end_date:
                dates.append(m.end_date)
        return min(dates), max(dates)
    
    @property
    def unique_categories(self) -> list[str]:
        """Get all unique categories from milestones."""
        if self.categories:
            return self.categories
        cats = []
        for m in self.milestones:
            if m.category and m.category not in cats:
                cats.append(m.category)
        return cats if cats else ["default"]


class QuickMilestone(BaseModel):
    """Simplified milestone for quick inline generation."""
    
    date: datetime
    title: str
    
    @classmethod
    def from_string(cls, s: str) -> "QuickMilestone":
        """Parse a string like '2024-01-01:Title' into a QuickMilestone."""
        if ":" not in s:
            raise ValueError(f"Invalid format: {s}. Expected 'DATE:TITLE'")
        parts = s.split(":", 1)
        from dateutil.parser import parse
        return cls(date=parse(parts[0]), title=parts[1].strip())
    
    def to_milestone(self) -> Milestone:
        """Convert to a full Milestone object."""
        return Milestone(date=self.date, title=self.title)

