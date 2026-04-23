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

    def _parse_time(self, time_string: str, now: datetime) -> datetime | None:
        """
        Parse a flight time string into a datetime.

        Supports both full datetime strings ('YYYY-MM-DD HH:MM') and time-only strings ('HH:MM').
        For time-only values, this resolves to the next valid occurrence after the current time.
        """
        if not time_string:
            return None

        try:
            return datetime.strptime(time_string, '%Y-%m-%d %H:%M')
        except ValueError:
            pass

        try:
            parsed_time = datetime.strptime(time_string, '%H:%M').time()
            candidate = now.replace(
                hour=parsed_time.hour,
                minute=parsed_time.minute,
                second=0,
                microsecond=0,
            )
            if candidate < now:
                candidate += timedelta(days=1)
            return candidate
        except ValueError:
            logger.warning(f"Could not parse flight time: {time_string}")
            return None

    def _is_within_time_window(self, time_string: str, now: datetime | None = None) -> bool:
        """
        Check if a flight time is within the acceptable window.
        Include flights from now until 3 AM tomorrow.

        Args:
            time_string: Time string in format 'YYYY-MM-DD HH:MM' or 'HH:MM'
            now: Optional reference datetime to use for comparisons.

        Returns:
            True if flight is within time window, False otherwise
        """
        if not time_string:
            return False

        now = now or datetime.now()
        tomorrow = now + timedelta(days=1)
        cutoff = tomorrow.replace(hour=3, minute=0, second=0, microsecond=0)

        flight_time = self._parse_time(time_string, now)
        return bool(flight_time and now <= flight_time <= cutoff)

    def process_flights(
        self,
        raw_flights: List[Dict[str, Any]],
        now: datetime | None = None,
    ) -> List[Dict[str, str]]:
        """
        Process raw API flight data.

        Args:
            raw_flights: List of flight dictionaries from API
            now: Optional reference time for filtering and sorting

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
            # 1. 'arr_estimated' (the live revised time)
            # 2. 'arr_actual' (the actual arrival time)
            # 3. 'arr_time' (the original scheduled time)
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

        now = now or datetime.now()
        # Filter by time window using either estimated or scheduled time,
        # then sort in descending order and apply the configured limit.
        processed = [
            flight
            for flight in processed
            if self._is_within_time_window(flight["estimated"] or flight["scheduled"], now=now)
        ]

        processed.sort(key=self._flight_sort_key, reverse=True)

        if self.flights_limit:
            processed = processed[: self.flights_limit]

        logger.info(f"Processed {len(processed)} flights after filtering")
        return processed

    def _flight_sort_key(self, flight: Dict[str, str]) -> datetime:
        """
        Build a sorting key from the flight's estimated or scheduled time.
        """
        now = datetime.now()
        time_string = flight.get("estimated") or flight.get("scheduled") or ""
        parsed = self._parse_time(time_string, now)
        return parsed if parsed else datetime.min

    @staticmethod
    def format_time(time_string: str) -> str:
        """
        Extract time portion from datetime string.

        Args:
            time_string: Full datetime string (e.g., '2026-04-06 23:45') or time-only string ('23:45')

        Returns:
            Formatted time string (e.g., '23:45')
        """
        if not time_string:
            return "??:??"

        formatted = time_string[-5:]
        if len(formatted) == 5 and formatted[2] == ":" and formatted[:2].isdigit() and formatted[3:].isdigit():
            return formatted

        return time_string

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
