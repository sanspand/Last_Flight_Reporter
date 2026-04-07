"""
Unit tests for the flight processing modules.
Run with: pytest tests/
"""

import sys
import os
from pathlib import Path

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
    
    raw_flights = [
        {
            "flight_iata": "SW4521",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": "2026-04-06 14:30",
            "arr_estimated": "2026-04-06 14:45",
            "status": "landed",
        },
        {
            "flight_iata": "UA4521",
            "airline_iata": "UA",  # Should be filtered out
            "dep_iata": "JFK",
            "arr_time": "2026-04-06 15:00",
            "arr_estimated": "2026-04-06 15:15",
            "status": "scheduled",
        },
        {
            "flight_iata": "DL2891",
            "airline_iata": "DL",
            "dep_iata": "JFK",
            "arr_time": "2026-04-06 15:30",
            "arr_estimated": "2026-04-06 15:45",
            "status": "scheduled",
        },
    ]
    
    result = processor.process_flights(raw_flights)
    
    # Should only have 2 flights (WN and DL, not UA)
    assert len(result) == 2
    assert result[0]["flight"] == "SW4521"
    assert result[1]["flight"] == "DL2891"


def test_process_flights_sorting():
    """Test that flights are sorted by scheduled time."""
    processor = FlightDataProcessor()
    
    raw_flights = [
        {
            "flight_iata": "FL3",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": "2026-04-06 14:30",
            "status": "landed",
        },
        {
            "flight_iata": "FL1",
            "airline_iata": "WN",
            "dep_iata": "LAX",
            "arr_time": "2026-04-06 10:00",
            "status": "landed",
        },
        {
            "flight_iata": "FL2",
            "airline_iata": "DL",
            "dep_iata": "JFK",
            "arr_time": "2026-04-06 12:00",
            "status": "scheduled",
        },
    ]
    
    result = processor.process_flights(raw_flights)
    
    # Should be sorted by scheduled time (ascending)
    assert result[0]["flight"] == "FL1"  # 10:00
    assert result[1]["flight"] == "FL2"  # 12:00
    assert result[2]["flight"] == "FL3"  # 14:30


def test_process_flights_limit():
    """Test that flight limit is respected."""
    processor = FlightDataProcessor(airlines_filter=["WN", "DL"], flights_limit=2)
    
    raw_flights = [
        {
            "flight_iata": f"FL{i}",
            "airline_iata": "WN" if i % 2 == 0 else "DL",
            "dep_iata": "LAX",
            "arr_time": f"2026-04-06 {10+i}:00",
            "status": "scheduled",
        }
        for i in range(5)
    ]
    
    result = processor.process_flights(raw_flights)
    
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
