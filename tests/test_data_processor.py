"""
Unit tests for the flight processing modules.
Run with: pytest tests/
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processor import FlightDataProcessor
from app_time import local_reference, LocalTimeFormatter
import logging


def test_format_time():
    """Test time formatting function."""
    processor = FlightDataProcessor()
    
    assert processor.format_time("2026-04-06 23:45") == "23:45"
    assert processor.format_time("2026-04-06 08:00") == "08:00"
    assert processor.format_time("") == "??:??"
    assert processor.format_time(None) == "??:??"
    assert processor.format_time("invalid") == "invalid"


def test_process_flights_filtering():
    """Test that flight filtering works correctly."""
    processor = FlightDataProcessor(airlines_filter=["WN", "DL"], flights_limit=10)
    now = datetime.now()

    raw_flights = [
        {
            "flight_iata": "SW4521",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "arr_estimated": (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "status": "landed",
        },
        {
            "flight_iata": "UA4521",
            "airline_iata": "UA",  # Should be filtered out
            "dep_iata": "JFK",
            "arr_time": (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "arr_estimated": (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "status": "scheduled",
        },
        {
            "flight_iata": "DL2891",
            "airline_iata": "DL",
            "dep_iata": "JFK",
            "arr_time": (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
            "arr_estimated": (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
            "status": "scheduled",
        },
    ]
    
    result = processor.process_flights(raw_flights, now=now)
    
    # Should only have 2 flights (WN and DL, not UA)
    assert len(result) == 2
    assert result[0]["flight"] == "DL2891"
    assert result[1]["flight"] == "SW4521"


def test_process_flights_sorting():
    """Test that flights are sorted by scheduled time in descending order."""
    processor = FlightDataProcessor()
    now = datetime.now()

    raw_flights = [
        {
            "flight_iata": "FL3",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
            "status": "landed",
        },
        {
            "flight_iata": "FL1",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "status": "landed",
        },
        {
            "flight_iata": "FL2",
            "airline_iata": "DL",
            "dep_iata": "JFK",
            "arr_time": (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "status": "scheduled",
        },
    ]
    
    result = processor.process_flights(raw_flights, now=now)
    
    # Should be sorted by scheduled time in descending order
    assert result[0]["flight"] == "FL3"  # latest
    assert result[1]["flight"] == "FL2"
    assert result[2]["flight"] == "FL1"


def test_process_flights_cutoff_excludes_after_3am():
    """Test that flights after 3 AM tomorrow are excluded."""
    processor = FlightDataProcessor(airlines_filter=["WN", "DL"], flights_limit=10)
    fixed_now = datetime.strptime("2026-04-06 21:30", "%Y-%m-%d %H:%M")

    raw_flights = [
        {
            "flight_iata": "FL_EARLY",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": "2026-04-06 23:00",
            "status": "scheduled",
        },
        {
            "flight_iata": "FL_LATE",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": "2026-04-07 07:25",
            "status": "scheduled",
        },
    ]

    result = processor.process_flights(raw_flights, now=fixed_now)

    assert len(result) == 1
    assert result[0]["flight"] == "FL_EARLY"


def test_process_flights_limit():
    """Test that flight limit is respected."""
    processor = FlightDataProcessor(airlines_filter=["WN", "DL"], flights_limit=2)
    now = datetime.now()
    
    raw_flights = [
        {
            "flight_iata": f"FL{i}",
            "airline_iata": "WN" if i % 2 == 0 else "DL",
            "dep_iata": "LAX",
            "arr_time": (now + timedelta(hours=i + 1)).strftime("%Y-%m-%d %H:%M"),
            "status": "scheduled",
        }
        for i in range(5)
    ]
    
    result = processor.process_flights(raw_flights, now=now)
    
    # Should only have 2 flights due to limit
    assert len(result) == 2


def test_format_flights_for_display():
    """Test flight formatting for console display."""
    processor = FlightDataProcessor()
    
    flights = [
        {
            "flight": "SW4521",
            "from": "LAX",
            "scheduled": "2026-04-06 14:30",
            "estimated": "2026-04-06 14:45",
            "status": "landed",
        },
    ]
    
    result = processor.format_flights_for_display(flights)
    
    assert "SW4521" in result
    assert "LAX" in result
    assert "14:30" in result
    assert "14:45" in result
    assert "landed" in result


def test_format_flights_for_email():
    """Test flight formatting for email HTML."""
    processor = FlightDataProcessor()
    
    flights = [
        {
            "flight": "SW4521",
            "from": "LAX",
            "scheduled": "2026-04-06 14:30",
            "estimated": "2026-04-06 14:45",
            "status": "landed",
        },
    ]
    
    result = processor.format_flights_for_email(flights)
    
    assert "<table" in result
    assert "SW4521" in result
    assert "LAX" in result
    assert "14:30" in result
    assert "landed" in result


def test_chicago_offset_tracks_daylight_saving():
    winter = local_reference(datetime(2026, 1, 15, 18, tzinfo=timezone.utc))
    summer = local_reference(datetime(2026, 7, 15, 18, tzinfo=timezone.utc))
    assert (winter.hour, winter.utcoffset()) == (12, timedelta(hours=-6))
    assert (summer.hour, summer.utcoffset()) == (13, timedelta(hours=-5))


def test_local_cutoff_with_utc_clock_and_dst_transitions():
    processor = FlightDataProcessor()
    # Each UTC instant falls at 9:30 PM on the previous Chicago calendar day.
    for utc_now, local_date, next_date in [
        (datetime(2026, 1, 16, 3, 30, tzinfo=timezone.utc), "2026-01-15", "2026-01-16"),
        (datetime(2026, 7, 16, 2, 30, tzinfo=timezone.utc), "2026-07-15", "2026-07-16"),
        (datetime(2026, 3, 8, 3, 30, tzinfo=timezone.utc), "2026-03-07", "2026-03-08"),
        (datetime(2026, 11, 1, 2, 30, tzinfo=timezone.utc), "2026-10-31", "2026-11-01"),
    ]:
        with patch("app_time.local_now", return_value=local_reference(utc_now)):
            assert not processor._is_within_time_window(f"{local_date} 21:00")
            assert processor._is_within_time_window(f"{local_date} 22:00")
            assert processor._is_within_time_window(f"{next_date} 03:00")
            assert not processor._is_within_time_window(f"{next_date} 03:01")
        assert processor._is_within_time_window(f"{local_date} 22:00", now=utc_now)


def test_time_only_sorting_uses_same_reference_as_filtering():
    processor = FlightDataProcessor()
    flights = [
        {"flight_iata": "LATE", "airline_iata": "WN", "arr_time": "00:30"},
        {"flight_iata": "EARLY", "airline_iata": "WN", "arr_time": "23:00"},
    ]
    result = processor.process_flights(flights, now=datetime(2026, 1, 15, 21, 30))
    assert [flight["flight"] for flight in result] == ["LATE", "EARLY"]


def test_logs_include_chicago_time_and_offset():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    formatter = LocalTimeFormatter("%(asctime)s %(message)s")
    record.created = datetime(2026, 1, 15, 18, tzinfo=timezone.utc).timestamp()
    assert "2026-01-15 12:00:00 CST-0600" in formatter.format(record)
    record.created = datetime(2026, 7, 15, 18, tzinfo=timezone.utc).timestamp()
    assert "2026-07-15 13:00:00 CDT-0500" in formatter.format(record)


if __name__ == "__main__":
    # Run basic tests
    test_format_time()
    test_process_flights_filtering()
    test_process_flights_sorting()
    test_process_flights_limit()
    test_format_flights_for_display()
    test_format_flights_for_email()
    print("All tests passed! ✓")
