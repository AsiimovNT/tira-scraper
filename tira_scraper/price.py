"""Price parsing: keep the display string, derive a clean number."""
import re

_PRICE_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def parse_price(text: str | None) -> tuple[str | None, float | int | None]:
    """('₹10,560', 10560). Returns (None, None) when no number is present."""
    if not text:
        return None, None
    m = _PRICE_NUM_RE.search(text)
    if not m:
        return None, None
    raw = m.group(0).replace(",", "")
    try:
        num: float = float(raw)
    except ValueError:
        return None, None
    if num.is_integer():
        num = int(num)
    return text.strip(), num
