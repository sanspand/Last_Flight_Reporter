"""
Email service module for sending flight information to managers.
Supports Brevo API for email delivery.
"""

import requests
import logging
from typing import List, Dict
from config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

# Brevo API endpoint
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailService:
    """Service for sending emails with flight information using Brevo API."""

    def __init__(
        self,
        api_key: str,
        sender_email: str,
        sender_name: str = "Last Flight Bot",
    ):
        """
        Initialize the Brevo email service.

        Args:
            api_key: Brevo API key
            sender_email: Email address to send from (must be verified in Brevo)
            sender_name: Display name for the sender
        """
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.api_key,
        }

    def send_flight_report(
        self, recipient_email: str, flights: List[Dict[str, str]], subject: str = None
    ) -> bool:
        """
        Send flight information via email using Brevo API.

        Args:
            recipient_email: Email address to send to
            flights: List of flight dictionaries
            subject: Email subject line

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not subject:
            subject = "Last 10 Flights Report - Dallas Airport"

        try:
            # Create plain text and HTML versions
            text_content = self._format_text_content(flights)
            html_content = self._format_html_content(flights)

            # Prepare Brevo API request payload
            payload = {
                "sender": {"name": self.sender_name, "email": self.sender_email},
                "to": [{"email": recipient_email}],
                "subject": subject,
                "textContent": text_content,
                "htmlContent": html_content,
            }

            logger.info(f"Sending email to {recipient_email} via Brevo API...")
            response = requests.post(BREVO_API_URL, json=payload, headers=self.headers)

            if response.status_code == 201:
                logger.info("Email sent successfully via Brevo")
                return True
            else:
                logger.error(
                    f"Brevo API error: Status {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @staticmethod
    def _format_text_content(flights: List[Dict[str, str]]) -> str:
        """Format flights as plain text for email."""
        if not flights:
            return "No upcoming flights found."

        lines = ["LAST 10 FLIGHTS REPORT\n", "=" * 50]
        lines.append(f"{'SCH':<8} {'ETA':<15} {'FROM':<8} {'STATUS'}")
        lines.append("-" * 50)

        for flight in flights:
            sch = flight["scheduled"][-5:] if flight["scheduled"] else "??:??"
            eta = flight["estimated"][-5:] if flight["estimated"] else "??:??"
            lines.append(
                f"{sch:<8} {eta:<15} {flight['from']:<8} {flight['status']}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_html_content(flights: List[Dict[str, str]]) -> str:
        """Format flights as HTML for email."""
        if not flights:
            html_table = "<p style='font-size: 18px; color: #666;'>No upcoming flights found.</p>"
        else:
            logger.info(f"time _milan asked {datetime.now()}")
            html_rows = ""
            for flight in flights:
                sch = flight["scheduled"][-5:] if flight["scheduled"] else "??:??"
                eta = flight["estimated"][-5:] if flight["estimated"] else "??:??"
                html_rows += f"""
                <tr>
                    <td style="padding: 12px 8px; border-bottom: 1px solid #ddd; font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold;">{sch}</td>
                    <td style="padding: 12px 8px; border-bottom: 1px solid #ddd; font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold;">{eta}</td>
                    <td style="padding: 12px 8px; border-bottom: 1px solid #ddd; font-size: 16px; font-weight: bold;">{flight['from']}</td>
                    <td style="padding: 12px 8px; border-bottom: 1px solid #ddd; font-size: 16px;">{flight['status']}</td>
                </tr>
                """

            html_table = f"""
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0; font-family: Arial, sans-serif;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 15px 8px; text-align: left; border-bottom: 2px solid #333; font-size: 18px; font-weight: bold; color: #333;">SCH</th>
                        <th style="padding: 15px 8px; text-align: left; border-bottom: 2px solid #333; font-size: 18px; font-weight: bold; color: #333;">ETA</th>
                        <th style="padding: 15px 8px; text-align: left; border-bottom: 2px solid #333; font-size: 18px; font-weight: bold; color: #333;">FROM</th>
                        <th style="padding: 15px 8px; text-align: left; border-bottom: 2px solid #333; font-size: 18px; font-weight: bold; color: #333;">STATUS</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
            """

        html = f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; background-color: #f8f9fa;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #2c3e50; margin-bottom: 10px; font-size: 24px; text-align: center;">✈️ Last 10 Flights Report</h1>
                    <h2 style="color: #34495e; margin-bottom: 20px; font-size: 18px; text-align: center;">Dallas Love Field Airport</h2>
                    <p style="font-size: 16px; line-height: 1.5; margin-bottom: 20px;">Here is the latest information about incoming flights:</p>
                    {html_table}
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="margin-top: 20px; font-size: 14px; color: #666; text-align: center;">
                        This report was automatically generated.<br>
                        Please contact the system administrator for inquiries.
                    </p>
                </div>
            </body>
        </html>
        """
        return html


def send_flights_email(flights: List[Dict[str, str]]) -> bool:
    """
    Convenience function to send flights via email using configured settings.

    Args:
        flights: List of flight dictionaries to send

    Returns:
        True if email was sent, False otherwise
    """
    if not Config.EMAIL_ENABLED:
        logger.info("Email is not enabled in configuration")
        return False

    service = EmailService(
        api_key=Config.BREVO_API_KEY,
        sender_email=Config.EMAIL_SENDER,
        sender_name=Config.EMAIL_SENDER_NAME,
    )

    return service.send_flight_report(Config.EMAIL_RECIPIENT, flights)
