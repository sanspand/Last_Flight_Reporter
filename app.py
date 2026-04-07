"""
Main application module that orchestrates flight information retrieval and delivery.

This script fetches the latest flight arrivals from AirLabs API and can:
- Display them in the console
- Send them via email to a configured recipient
- Log all activities

Configuration is managed via environment variables (see .env.example)
"""

import logging
import sys
from config import Config
from api_client import get_flights_from_api
from data_processor import FlightDataProcessor
from email_service import send_flights_email


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger(__name__)
    return logger


def main():
    """Main application entry point."""
    logger = setup_logging()
    logger.info("Starting Flight Information Application")
    logger.info(f"Configuration: {Config}")

    try:
        # Validate configuration
        Config.validate()

        # Fetch flights from API
        logger.info(f"Fetching flights for airport {Config.AIRPORT_ICAO}...")
        raw_flights = get_flights_from_api(Config.AIRPORT_ICAO)

        # Process flight data
        processor = FlightDataProcessor(
            airlines_filter=Config.AIRLINES_FILTER,
            flights_limit=Config.FLIGHTS_LIMIT,
        )
        processed_flights = processor.process_flights(raw_flights)

        if not processed_flights:
            logger.warning("No flights found matching criteria")
            print("\nNo upcoming flights found for the selected airlines and airport.")
            return

        # Display flights in console
        logger.info(f"Displaying {len(processed_flights)} flights")
        display_output = processor.format_flights_for_display(processed_flights)
        print("\n" + display_output + "\n")

        # Send email if enabled
        if Config.EMAIL_ENABLED:
            logger.info("Sending email report...")
            success = send_flights_email(processed_flights)
            if success:
                logger.info("Email sent successfully")
                print("✓ Email report sent successfully\n")
            else:
                logger.error("Failed to send email")
                print("✗ Failed to send email report\n")
        else:
            logger.info("Email is disabled in configuration")

        logger.info("Application completed successfully")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()