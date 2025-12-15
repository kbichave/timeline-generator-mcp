"""Time scale calculations for timeline layout."""

from datetime import datetime, timedelta
from enum import Enum
from typing import NamedTuple

from dateutil.relativedelta import relativedelta


class TimeScale(str, Enum):
    """Supported time scales."""
    
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ScaleInfo(NamedTuple):
    """Information about a time scale calculation."""
    
    scale: TimeScale
    start: datetime
    end: datetime
    total_units: int
    unit_labels: list[str]
    major_ticks: list[datetime]
    minor_ticks: list[datetime]


def calculate_scale(
    start_date: datetime,
    end_date: datetime,
    scale: TimeScale,
    padding_units: int = 1,
) -> ScaleInfo:
    """
    Calculate scale information for a date range.
    
    Args:
        start_date: Start of the date range.
        end_date: End of the date range.
        scale: The time scale to use.
        padding_units: Extra units to add at start and end.
        
    Returns:
        ScaleInfo with calculated scale details.
    """
    # Normalize dates to appropriate boundaries
    start_norm, end_norm = _normalize_dates(start_date, end_date, scale)
    
    # Add padding
    start_padded = _subtract_units(start_norm, padding_units, scale)
    end_padded = _add_units(end_norm, padding_units, scale)
    
    # Calculate total units
    total_units = _count_units(start_padded, end_padded, scale)
    
    # Generate labels and ticks
    unit_labels = _generate_labels(start_padded, total_units, scale)
    major_ticks = _generate_major_ticks(start_padded, end_padded, scale)
    minor_ticks = _generate_minor_ticks(start_padded, end_padded, scale)
    
    return ScaleInfo(
        scale=scale,
        start=start_padded,
        end=end_padded,
        total_units=total_units,
        unit_labels=unit_labels,
        major_ticks=major_ticks,
        minor_ticks=minor_ticks,
    )


def _normalize_dates(
    start: datetime, end: datetime, scale: TimeScale
) -> tuple[datetime, datetime]:
    """Normalize dates to scale boundaries."""
    if scale == TimeScale.HOURLY:
        start_norm = start.replace(minute=0, second=0, microsecond=0)
        end_norm = end.replace(minute=0, second=0, microsecond=0)
    elif scale == TimeScale.DAILY:
        start_norm = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end_norm = end.replace(hour=0, minute=0, second=0, microsecond=0)
    elif scale == TimeScale.WEEKLY:
        # Start of week (Monday)
        start_norm = start - timedelta(days=start.weekday())
        start_norm = start_norm.replace(hour=0, minute=0, second=0, microsecond=0)
        end_norm = end - timedelta(days=end.weekday())
        end_norm = end_norm.replace(hour=0, minute=0, second=0, microsecond=0)
    elif scale == TimeScale.MONTHLY:
        start_norm = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_norm = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif scale == TimeScale.QUARTERLY:
        q_start = ((start.month - 1) // 3) * 3 + 1
        start_norm = start.replace(month=q_start, day=1, hour=0, minute=0, second=0, microsecond=0)
        q_end = ((end.month - 1) // 3) * 3 + 1
        end_norm = end.replace(month=q_end, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # YEARLY
        start_norm = start.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_norm = end.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    return start_norm, end_norm


def _add_units(dt: datetime, units: int, scale: TimeScale) -> datetime:
    """Add time units to a datetime."""
    if scale == TimeScale.HOURLY:
        return dt + timedelta(hours=units)
    elif scale == TimeScale.DAILY:
        return dt + timedelta(days=units)
    elif scale == TimeScale.WEEKLY:
        return dt + timedelta(weeks=units)
    elif scale == TimeScale.MONTHLY:
        return dt + relativedelta(months=units)
    elif scale == TimeScale.QUARTERLY:
        return dt + relativedelta(months=units * 3)
    else:  # YEARLY
        return dt + relativedelta(years=units)


def _subtract_units(dt: datetime, units: int, scale: TimeScale) -> datetime:
    """Subtract time units from a datetime."""
    return _add_units(dt, -units, scale)


def _count_units(start: datetime, end: datetime, scale: TimeScale) -> int:
    """Count the number of time units between two dates."""
    if scale == TimeScale.HOURLY:
        return int((end - start).total_seconds() / 3600)
    elif scale == TimeScale.DAILY:
        return (end - start).days
    elif scale == TimeScale.WEEKLY:
        return (end - start).days // 7
    elif scale == TimeScale.MONTHLY:
        return (end.year - start.year) * 12 + (end.month - start.month)
    elif scale == TimeScale.QUARTERLY:
        months = (end.year - start.year) * 12 + (end.month - start.month)
        return months // 3
    else:  # YEARLY
        return end.year - start.year


def _generate_labels(start: datetime, count: int, scale: TimeScale) -> list[str]:
    """Generate labels for each time unit."""
    labels = []
    current = start
    
    for _ in range(count + 1):
        if scale == TimeScale.HOURLY:
            labels.append(current.strftime("%H:%M"))
        elif scale == TimeScale.DAILY:
            labels.append(current.strftime("%b %d"))
        elif scale == TimeScale.WEEKLY:
            labels.append(f"W{current.isocalendar()[1]}")
        elif scale == TimeScale.MONTHLY:
            labels.append(current.strftime("%b %Y"))
        elif scale == TimeScale.QUARTERLY:
            q = (current.month - 1) // 3 + 1
            labels.append(f"Q{q} {current.year}")
        else:  # YEARLY
            labels.append(str(current.year))
        
        current = _add_units(current, 1, scale)
    
    return labels


def _generate_major_ticks(start: datetime, end: datetime, scale: TimeScale) -> list[datetime]:
    """Generate major tick positions."""
    ticks = []
    current = start
    
    while current <= end:
        ticks.append(current)
        current = _add_units(current, 1, scale)
    
    return ticks


def _generate_minor_ticks(start: datetime, end: datetime, scale: TimeScale) -> list[datetime]:
    """Generate minor tick positions between major ticks."""
    ticks = []
    current = start
    
    # Minor ticks are at half-unit intervals for most scales
    while current <= end:
        if scale == TimeScale.HOURLY:
            ticks.append(current + timedelta(minutes=30))
        elif scale == TimeScale.DAILY:
            ticks.append(current + timedelta(hours=12))
        elif scale == TimeScale.WEEKLY:
            for d in range(1, 7):
                ticks.append(current + timedelta(days=d))
        elif scale == TimeScale.MONTHLY:
            ticks.append(current + timedelta(days=15))
        elif scale == TimeScale.QUARTERLY:
            ticks.append(current + relativedelta(months=1))
            ticks.append(current + relativedelta(months=2))
        else:  # YEARLY
            for m in range(3, 12, 3):
                ticks.append(current + relativedelta(months=m))
        
        current = _add_units(current, 1, scale)
    
    # Filter ticks within range
    return [t for t in ticks if start <= t <= end]


def date_to_position(
    date: datetime,
    scale_info: ScaleInfo,
    total_length: float,
) -> float:
    """
    Convert a date to a position on the timeline.
    
    Args:
        date: The date to convert.
        scale_info: Scale information.
        total_length: Total length of the timeline in pixels.
        
    Returns:
        Position as a float between 0 and total_length.
    """
    total_seconds = (scale_info.end - scale_info.start).total_seconds()
    if total_seconds == 0:
        return total_length / 2
    
    date_seconds = (date - scale_info.start).total_seconds()
    return (date_seconds / total_seconds) * total_length

