"""Pytest fixtures for timeline generator tests."""

import pytest
from datetime import datetime

from timeline_generator.models import (
    Milestone,
    TimelineConfig,
    OutputConfig,
    TimeScale,
    TimelineStyle,
    ThemeName,
    OutputFormat,
    ColorConfig,
)


@pytest.fixture
def sample_milestone():
    """Create a sample milestone."""
    return Milestone(
        date=datetime(2024, 1, 15),
        title="Project Kickoff",
        description="Initial planning meeting",
        highlight=True,
    )


@pytest.fixture
def sample_milestones():
    """Create a list of sample milestones."""
    return [
        Milestone(
            date=datetime(2024, 1, 15),
            title="Project Start",
            description="Kickoff meeting",
            highlight=True,
        ),
        Milestone(
            date=datetime(2024, 3, 1),
            title="Phase 1 Complete",
            description="First milestone reached",
        ),
        Milestone(
            date=datetime(2024, 6, 1),
            title="MVP Launch",
            description="Minimum viable product release",
            highlight=True,
        ),
        Milestone(
            date=datetime(2024, 12, 1),
            title="v1.0 Release",
            description="First stable release",
            color="#4CAF50",
        ),
    ]


@pytest.fixture
def sample_config(sample_milestones):
    """Create a sample timeline configuration."""
    return TimelineConfig(
        title="Test Timeline",
        subtitle="For testing purposes",
        scale=TimeScale.MONTHLY,
        style=TimelineStyle.HORIZONTAL,
        theme=ThemeName.MINIMAL,
        milestones=sample_milestones,
        output=OutputConfig(
            format=OutputFormat.PNG,
            width=1920,
            height=1080,
        ),
    )


@pytest.fixture
def gantt_milestones():
    """Create milestones suitable for Gantt chart."""
    return [
        Milestone(
            date=datetime(2024, 1, 1),
            title="Planning",
            end_date=datetime(2024, 1, 31),
            progress=100,
            category="planning",
        ),
        Milestone(
            date=datetime(2024, 2, 1),
            title="Development",
            end_date=datetime(2024, 5, 31),
            progress=75,
            category="development",
        ),
        Milestone(
            date=datetime(2024, 6, 1),
            title="Testing",
            end_date=datetime(2024, 7, 31),
            progress=50,
            category="testing",
        ),
    ]


@pytest.fixture
def sample_yaml_config():
    """Return a sample YAML configuration string."""
    return """
title: "Test Timeline"
subtitle: "Testing YAML parsing"
scale: monthly
style: horizontal
theme: corporate

milestones:
  - date: "2024-01-15"
    title: "Start"
    description: "Project begins"
    highlight: true
    
  - date: "2024-06-01"
    title: "Launch"
    description: "Go live"

output:
  format: png
  width: 1920
  height: 1080
"""


@pytest.fixture
def sample_json_config():
    """Return a sample JSON configuration string."""
    return """
{
    "title": "Test Timeline",
    "scale": "monthly",
    "style": "horizontal",
    "theme": "minimal",
    "milestones": [
        {"date": "2024-01-15", "title": "Start"},
        {"date": "2024-06-01", "title": "End"}
    ],
    "output": {
        "format": "png",
        "width": 1920,
        "height": 1080
    }
}
"""

