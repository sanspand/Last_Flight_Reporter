"""
Email service module for sending flight information to managers.
Supports Gmail SMTP with configurable settings.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with flight information."""

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
    ):
        """
        Initialize the email service.

        Args:
            sender_email: Email address to send from
            sender_password: Password or app-specific password
            smtp_server: SMTP server address
            smtp_port: SMTP server port
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_flight_report(
        self, recipient_email: str, flights: List[Dict[str, str]], subject: str = None
    ) -> bool:
        """
        Send flight information via email.

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
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email

            # Create plain text and HTML versions
            text_content = self._format_text_content(flights)
            html_content = self._format_html_content(flights)

            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            # Send email
            logger.info(f"Connecting to {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                logger.info("Logging in to email account...")
                server.login(self.sender_email, self.sender_password)
                logger.info(f"Sending email to {recipient_email}...")
                server.send_message(message)

            logger.info("Email sent successfully")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Email authentication failed. Check sender email and password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @staticmethod
    def _format_text_content(flights: List[Dict[str, str]]) -> str:
        """Format flights as plain text for email."""
        if not flights:
            return "No upcoming flights found."

        lines = ["Last 10 Flights Report\n", "=" * 60]
        lines.append(f"{'SCH':<10} {'ETA':<18} {'FLIGHT':<10} {'FROM':<6} {'STATUS'}")
        lines.append("-" * 60)

        for flight in flights:
            sch = flight["scheduled"][-5:] if flight["scheduled"] else "??:??"
            eta = flight["estimated"][-5:] if flight["estimated"] else "??:??"
            lines.append(
                f"{sch:<8} {eta:<18} {flight['flight']:<10} {flight['from']:<6} {flight['status']}"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_html_content(flights: List[Dict[str, str]]) -> str:
        """Format flights as HTML for email."""
        if not flights:
            html_table = "<p>No upcoming flights found.</p>"
        else:
            html_rows = ""
            for flight in flights:
                sch = flight["scheduled"][-5:] if flight["scheduled"] else "??:??"
                eta = flight["estimated"][-5:] if flight["estimated"] else "??:??"
                html_rows += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; font-family: monospace;">{sch}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; font-family: monospace;">{eta}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{flight['flight']}</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{flight['from']}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{flight['status']}</td>
                </tr>
                """

            html_table = f"""
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #333;">Scheduled</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #333;">Estimated</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #333;">Flight</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #333;">From</th>
                        <th style="padding: 8px; text-align: left; border-bottom: 2px solid #333;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
            """

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Last 10 Flights Report - Dallas Love FieldAirport</h2>
                <p>Here is the latest information about incoming flights:</p>
                {html_table}
                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    This report was automatically generated. Please contact the system administrator for inquiries.
                </p>
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
        sender_email=Config.EMAIL_SENDER,
        sender_password=Config.EMAIL_SENDER_PASSWORD,
        smtp_server=Config.EMAIL_SMTP_SERVER,
        smtp_port=Config.EMAIL_SMTP_PORT,
    )

    return service.send_flight_report(Config.EMAIL_RECIPIENT, flights)
