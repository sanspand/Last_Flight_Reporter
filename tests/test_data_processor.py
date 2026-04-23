"""
Unit tests for the flight processing modules.
Run with: pytest tests/
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processor import FlightDataProcessor


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


if __name__ == "__main__":
    # Run basic tests
    test_format_time()
    test_process_flights_filtering()
    test_process_flights_sorting()
    test_process_flights_limit()
    test_format_flights_for_display()
    test_format_flights_for_email()
    print("All tests passed! ✓")
