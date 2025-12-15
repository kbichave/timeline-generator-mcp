"""Tests for time scale calculations."""

import pytest
from datetime import datetime

from timeline_generator.core.scale import (
    TimeScale,
    ScaleInfo,
    calculate_scale,
    date_to_position,
)


class TestTimeScale:
    """Tests for TimeScale enum."""

    def test_all_scales_exist(self):
        """Test that all expected scales exist."""
        scales = [s.value for s in TimeScale]
        assert "hourly" in scales
        assert "daily" in scales
        assert "weekly" in scales
        assert "monthly" in scales
        assert "quarterly" in scales
        assert "yearly" in scales


class TestCalculateScale:
    """Tests for calculate_scale function."""

    def test_monthly_scale(self):
        """Test calculating monthly scale."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        assert scale_info.scale == TimeScale.MONTHLY
        assert scale_info.start <= start
        assert scale_info.end >= end

    def test_yearly_scale(self):
        """Test calculating yearly scale."""
        start = datetime(2020, 1, 1)
        end = datetime(2024, 12, 31)
        
        scale_info = calculate_scale(start, end, TimeScale.YEARLY)
        
        assert scale_info.scale == TimeScale.YEARLY

    def test_daily_scale(self):
        """Test calculating daily scale."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        scale_info = calculate_scale(start, end, TimeScale.DAILY)
        
        assert scale_info.scale == TimeScale.DAILY

    def test_scale_with_same_dates(self):
        """Test scale when start and end are same."""
        date = datetime(2024, 6, 15)
        
        scale_info = calculate_scale(date, date, TimeScale.MONTHLY)
        
        # Should still have valid range
        assert scale_info.start <= date
        assert scale_info.end >= date

    def test_scale_info_has_ticks(self):
        """Test that scale info includes tick marks."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        assert len(scale_info.major_ticks) > 0
        assert len(scale_info.unit_labels) > 0


class TestDateToPosition:
    """Tests for date_to_position function."""

    def test_start_position(self):
        """Test that start date maps near 0."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        pos = date_to_position(start, scale_info, 1000)
        
        # Should be at or near 0 (allowing for padding)
        assert pos >= 0
        assert pos < 200

    def test_end_position(self):
        """Test that end date maps near total length."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        pos = date_to_position(end, scale_info, 1000)
        
        # Should be near 1000 (allowing for padding)
        assert pos > 750
        assert pos <= 1000

    def test_middle_position(self):
        """Test that middle date maps to middle."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        middle = datetime(2024, 7, 1)
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        pos = date_to_position(middle, scale_info, 1000)
        
        # Should be roughly in the middle
        assert 300 < pos < 700

    def test_proportional_positioning(self):
        """Test that positions are proportional."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        q1 = datetime(2024, 4, 1)
        q2 = datetime(2024, 7, 1)
        q3 = datetime(2024, 10, 1)
        
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        pos_q1 = date_to_position(q1, scale_info, 1000)
        pos_q2 = date_to_position(q2, scale_info, 1000)
        pos_q3 = date_to_position(q3, scale_info, 1000)
        
        # Positions should be increasing
        assert pos_q1 < pos_q2 < pos_q3


class TestScaleMarkers:
    """Tests for scale markers (ticks and labels)."""

    def test_monthly_markers(self):
        """Test getting monthly scale markers."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        # Should have labels for months
        assert len(scale_info.unit_labels) >= 12

    def test_yearly_markers(self):
        """Test getting yearly scale markers."""
        start = datetime(2020, 1, 1)
        end = datetime(2024, 12, 31)
        scale_info = calculate_scale(start, end, TimeScale.YEARLY)
        
        # Should have labels for years
        assert len(scale_info.unit_labels) >= 5

    def test_ticks_are_sorted(self):
        """Test that ticks are in chronological order."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        ticks = scale_info.major_ticks
        assert ticks == sorted(ticks)

    def test_labels_are_strings(self):
        """Test that labels are strings."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 6, 30)
        scale_info = calculate_scale(start, end, TimeScale.MONTHLY)
        
        for label in scale_info.unit_labels:
            assert isinstance(label, str)
            assert len(label) > 0
