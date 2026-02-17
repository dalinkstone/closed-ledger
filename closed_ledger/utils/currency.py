"""Currency formatting utilities. All money is stored as integer cents."""


def cents_to_display(cents: int, show_cents: bool = True) -> str:
    """Format cents as a display string with $ sign.

    123456 → "$1,234.56" (show_cents=True) or "$1,235" (show_cents=False)
    -523400 → "-$5,234.00"
    """
    negative = cents < 0
    abs_cents = abs(cents)
    if show_cents:
        dollars = abs_cents // 100
        remainder = abs_cents % 100
        formatted = f"${dollars:,}.{remainder:02d}"
    else:
        dollars = round(abs_cents / 100)
        formatted = f"${dollars:,}"
    if negative:
        formatted = f"-{formatted}"
    return formatted


def display_to_cents(text: str) -> int:
    """Parse a display string to cents.

    "$1,234.56" or "1234.56" or "1,234.56" → 123456
    """
    cleaned = text.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0
    return int(round(float(cleaned) * 100))


def cents_to_table(cents: int) -> str:
    """Format cents for table cells (no $ sign).

    123456 → "1,234.56"
    """
    abs_cents = abs(cents)
    dollars = abs_cents // 100
    remainder = abs_cents % 100
    return f"{dollars:,}.{remainder:02d}"
