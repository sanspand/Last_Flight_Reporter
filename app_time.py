"""Application time independent of the hosting machine's timezone."""

from datetime import datetime
import logging

from config import Config


def local_now() -> datetime:
    return datetime.now(Config.TIMEZONE)


def local_reference(value: datetime | None = None) -> datetime:
    """Treat naive references as airport local time; convert aware references."""
    if value is None:
        return local_now()
    if value.tzinfo is None:
        return value.replace(tzinfo=Config.TIMEZONE)
    return value.astimezone(Config.TIMEZONE)


class LocalTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        timestamp = datetime.fromtimestamp(record.created, Config.TIMEZONE)
        return timestamp.strftime(datefmt or "%Y-%m-%d %H:%M:%S %Z%z")
