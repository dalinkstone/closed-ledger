"""Date formatting helpers."""

from datetime import date, datetime


def format_date_display(iso_date: str) -> str:
    """Convert ISO date string to M/D/YYYY display format (no zero-padding).

    "2025-08-05" → "8/5/2025"
    """
    try:
        d = date.fromisoformat(iso_date)
        return f"{d.month}/{d.day}/{d.year}"
    except (ValueError, TypeError):
        return iso_date or ""


def parse_display_date(display: str) -> str:
    """Convert M/D/YYYY display date to ISO format.

    "8/5/2025" → "2025-08-05"
    """
    try:
        d = datetime.strptime(display.strip(), "%m/%d/%Y")
        return d.date().isoformat()
    except (ValueError, TypeError):
        return display or ""


def today_iso() -> str:
    """Return today's date as ISO string."""
    return date.today().isoformat()
