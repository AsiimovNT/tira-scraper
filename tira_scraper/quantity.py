"""Size/quantity parsing and normalization.

Fixes the DDF `2026g` bug: a 4-digit year leaking off the page and being read
as a gram quantity. We reject year-like values and implausible magnitudes.
"""
import re

# Map every spelling we accept to a single canonical unit token.
UNIT_ALIASES = {
    "ml": "ml", "mls": "ml",
    "l": "l", "ltr": "l", "litre": "l", "liter": "l", "litres": "l", "liters": "l",
    "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
    "kg": "kg",
    "oz": "oz",
}

# number followed by a unit. Leading lookbehind stops us matching the tail of a
# longer number; the alternation is ordered longest-first so "ml" wins over "l".
_QTY_RE = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)?)\s*"
    r"(mls|ml|litres|liters|litre|liter|ltr|l|grams|gram|gms|gm|g|kg|oz)\b",
    re.IGNORECASE,
)
_PACK_RE = re.compile(r"\b(?:pack|set|combo)\s+of\s+(\d+)\b", re.IGNORECASE)

# Plausible size ranges per canonical unit for beauty products.
PLAUSIBLE = {
    "ml": (1, 5000),
    "l": (0.01, 10),
    "g": (1, 5000),
    "kg": (0.01, 10),
    "oz": (0.1, 200),
}

# Treat a 4-digit integer in this window as a year, never a product size.
YEAR_MIN, YEAR_MAX = 1990, 2099


def _is_year_like(value: float) -> bool:
    return float(value).is_integer() and YEAR_MIN <= int(value) <= YEAR_MAX


def _fmt_num(n: float) -> str:
    f = float(n)
    return str(int(f)) if f.is_integer() else str(f)


def _is_valid(value: float, unit: str) -> bool:
    if _is_year_like(value):
        return False
    lo, hi = PLAUSIBLE.get(unit, (None, None))
    if lo is None:
        return True
    return lo <= value <= hi


def extract_quantities(text: str) -> list[str]:
    """Return every *valid*, de-duplicated size string found in `text`."""
    found: list[str] = []
    seen: set[str] = set()
    for num, unit in _QTY_RE.findall(text or ""):
        canon = UNIT_ALIASES.get(unit.lower())
        if not canon:
            continue
        val = float(num)
        if not _is_valid(val, canon):
            continue
        norm = f"{_fmt_num(val)}{canon}"
        if norm not in seen:
            seen.add(norm)
            found.append(norm)
    for n in _PACK_RE.findall(text or ""):
        norm = f"pack of {n}"
        if norm not in seen:
            seen.add(norm)
            found.append(norm)
    return found


def normalize_primary(found: list[str], preferred: str | None = None) -> str | None:
    """Pick the single best size: the PDP-selected one if given, else the first."""
    if preferred:
        pq = extract_quantities(preferred)
        if pq:
            return pq[0]
    return found[0] if found else None
