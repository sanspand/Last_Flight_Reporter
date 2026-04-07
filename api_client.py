"""
API Client module for AirLabs API.
Handles all API calls to fetch flight information.
"""

import requests
import logging
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)


class AirLabsAPIClient:
    """Client for interacting with the AirLabs API."""

    BASE_URL = "https://airlabs.co/api/v9"

    def __init__(self, api_key: str):
        """
        Initialize the API client.

        Args:
            api_key: AirLabs API key
        """
        self.api_key = api_key

    def get_arrivals(self, airport_icao: str) -> List[Dict[str, Any]]:
        """
        Fetch flight arrivals for a specific airport.

        Args:
            airport_icao: ICAO code of the airport (e.g., 'KDAL')

        Returns:
            List of flight dictionaries with raw API data

        Raises:
            requests.RequestException: If API call fails
            ValueError: If response is malformed
        """
        url = f"{self.BASE_URL}/schedules"
        params = {
            "arr_icao": airport_icao,
            "api_key": self.api_key,
        }

        try:
            logger.info(f"Fetching arrivals for {airport_icao}...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "response" not in data:
                logger.warning("No 'response' key in API response")
                return []

            logger.info(f"Successfully fetched {len(data['response'])} flights")
            return data["response"]

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse API response: {e}")
            raise


def get_flights_from_api(airport_icao: str) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch flights from the API.

    Args:
        airport_icao: ICAO code of the airport

    Returns:
        List of flight data from API
    """
    client = AirLabsAPIClient(Config.AIRLABS_API_KEY)
    return client.get_arrivals(airport_icao)
