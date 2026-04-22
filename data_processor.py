"""
Data processing module for flight information.
Handles filtering, transformation, and formatting of flight data.
"""

import logging
from typing import List, Dict, Any
from config import Config
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FlightDataProcessor:
    """Processes and transforms raw flight data."""

    def __init__(
        self,
        airlines_filter: List[str] = None,
        flights_limit: int = None,
    ):
        """
        Initialize the flight data processor.

        Args:
            airlines_filter: List of airline IATA codes to filter (e.g., ['WN', 'DL'])
            flights_limit: Maximum number of flights to return
        """
        self.airlines_filter = airlines_filter or Config.AIRLINES_FILTER
        self.flights_limit = flights_limit or Config.FLIGHTS_LIMIT

    def _is_within_time_window(self, time_string: str) -> bool:
        """
        Check if a flight time is within the acceptable window.
        Include flights from now until 3 AM tomorrow.

        Args:
            time_string: Time string in format 'YYYY-MM-DD HH:MM'

        Returns:
            True if flight is within time window, False otherwise
        """
        if not time_string:
            return False

        try:
            # Parse the datetime string
            flight_time = datetime.strptime(time_string, '%Y-%m-%d %H:%M')

            # Get current time
            now = datetime.now()

            # Define the cutoff time: 3 AM tomorrow
            tomorrow = now + timedelta(days=1)
            cutoff = tomorrow.replace(hour=3, minute=0, second=0, microsecond=0)

            # Include flights from now until 3 AM tomorrow
            return now <= flight_time <= cutoff

        except ValueError:
            # If we can't parse the time, include it (better to show than hide)
            logger.warning(f"Could not parse flight time: {time_string}")
            return True

    def process_flights(self, raw_flights: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Process raw API flight data.

        Args:
            raw_flights: List of flight dictionaries from API

        Returns:
            List of processed flight dictionaries
        """
        processed = []

        for flight in raw_flights:
            # Filter by airline
            airline = flight.get("airline_iata", "")
            if airline not in self.airlines_filter:
                continue

            # Extract and prioritize times
            # 1. 'arr_estimated' (The live revised time)
            # 2. 'arr_time' (The original scheduled time)
            eta = flight.get("arr_estimated") or flight.get("arr_time")
            scheduled = flight.get("arr_actual") or flight.get("arr_time")

            processed_flight = {
                "flight": flight.get("flight_iata", ""),
                "from": flight.get("dep_iata", ""),
                "scheduled": scheduled,
                "estimated": eta,
                "status": flight.get("status", ""),
            }

            processed.append(processed_flight)

        # Filter by time window (today's flights up to 2 AM next day)
        processed = [flight for flight in processed if self._is_within_time_window(flight["estimated"])]

        # Sort by estimated time in descending order
        processed.sort(key=lambda x: x["estimated"] if x["estimated"] else "0000", reverse=True)

        # Limit results
        if self.flights_limit:
            processed = processed[: self.flights_limit]

        logger.info(f"Processed {len(processed)} flights after filtering")
        return processed

    @staticmethod
    def format_time(time_string: str) -> str:
        """
        Extract time portion from datetime string.

        Args:
            time_string: Full datetime string (e.g., '2026-04-06 23:45')

        Returns:
            Formatted time string (e.g., '23:45')
        """
        if not time_string:
            return "??:??"
        return time_string[-5:] if len(time_string) >= 5 else time_string

    def format_flights_for_display(self, flights: List[Dict[str, str]]) -> str:
        """
        Format flights for console/text display.

        Args:
            flights: List of processed flight dictionaries

        Returns:
            Formatted string with flight information
        """
        lines = [
            f"{'SCH':<10} {'ETA':<18} {'FLIGHT':<10} {'FROM':<6} {'STATUS'}"
        ]
        lines.append("-" * 60)

        for flight in flights:
            scheduled_time = self.format_time(flight["scheduled"])
            estimated_time = self.format_time(flight["estimated"])

            line = (
                f"{scheduled_time:<8} "
                f"{estimated_time:<18} "
                f"{flight['flight']:<10} "
                f"{flight['from']:<6} "
                f"{flight['status']}"
            )
            lines.append(line)

        return "\n".join(lines)

    def format_flights_for_email(self, flights: List[Dict[str, str]]) -> str:
        """
        Format flights for email display (HTML-compatible).

        Args:
            flights: List of processed flight dictionaries

        Returns:
            Formatted HTML string with flight information
        """
        if not flights:
            return "<p>No upcoming flights found.</p>"

        html_rows = ""
        for flight in flights:
            scheduled_time = self.format_time(flight["scheduled"])
            estimated_time = self.format_time(flight["estimated"])

            html_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{scheduled_time}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{estimated_time}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{flight['flight']}</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{flight['from']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{flight['status']}</td>
            </tr>
            """

        html = f"""
        <table style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Scheduled</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Estimated</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Flight</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">From</th>
                    <th style="padding: 8px; text-align: left; border-bottom: 2px solid #ddd;">Status</th>
                </tr>
            </thead>
            <tbody>
                {html_rows}
            </tbody>
        </table>
        """
        return html
