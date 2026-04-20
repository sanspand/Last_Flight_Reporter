"""
Flask server wrapper for the Last Flight application.

This server exposes HTTP endpoints that allow the flight information
retrieval to be triggered from external services (cron jobs, etc).
"""

import logging
import sys
import os
from flask import Flask, jsonify, request
from config import Config
from api_client import get_flights_from_api
from data_processor import FlightDataProcessor
from email_service import send_flights_email

# Create Flask app
app = Flask(__name__)

# Setup logging
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
    return logging.getLogger(__name__)

logger = setup_logging()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy", "service": "Last Flight API"}), 200


@app.route("/run", methods=["POST", "GET"])
def run_flights():
    """
    Execute the flight information retrieval.
    
    GET and POST requests both trigger the flight processing.
    Can be called from cron jobs or external services.
    """
    try:
        logger.info("Flight retrieval triggered")
        
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
            return jsonify({
                "status": "success",
                "message": "No flights found matching criteria",
                "flights_count": 0
            }), 200
        
        # Send email if enabled
        email_sent = False
        if Config.EMAIL_ENABLED:
            logger.info("Sending email report...")
            email_sent = send_flights_email(processed_flights)
            if email_sent:
                logger.info("Email sent successfully")
            else:
                logger.error("Failed to send email")
        
        logger.info("Flight retrieval completed successfully")
        
        return jsonify({
            "status": "success",
            "message": "Flight retrieval completed",
            "flights_count": len(processed_flights),
            "email_sent": email_sent,
            "airport": Config.AIRPORT_ICAO
        }), 200
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Configuration error: {e}"
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {e}"
        }), 500


@app.route("/status", methods=["GET"])
def status():
    """Get application status and configuration info."""
    try:
        return jsonify({
            "status": "running",
            "service": "Last Flight API",
            "airport": Config.AIRPORT_ICAO,
            "email_enabled": Config.EMAIL_ENABLED,
            "flights_limit": Config.FLIGHTS_LIMIT,
            "airlines_filter": Config.AIRLINES_FILTER
        }), 200
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
