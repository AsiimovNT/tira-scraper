"""The output row schema — mirrors the DDF export with a TIRA_ prefix."""
from dataclasses import dataclass, asdict

# Exact output column order. Drop TIRA_Brand for strict 9-column DDF parity.
COLUMNS = [
    "TIRA_Product_Name",
    "TIRA_SKU",
    "TIRA_Qty_Normalized",
    "TIRA_All_Qty_Found",
    "TIRA_Price",
    "TIRA_Price_Number",
    "TIRA_Brand",
    "TIRA_Stock",
    "TIRA_URL",
    "TIRA_Status",
]


@dataclass
class ProductRow:
    TIRA_Product_Name: str = ""
    TIRA_SKU: str = ""
    TIRA_Qty_Normalized: str | None = None
    TIRA_All_Qty_Found: str | None = None
    TIRA_Price: str | None = None
    TIRA_Price_Number: float | int | None = None
    TIRA_Brand: str | None = None
    TIRA_Stock: str | None = None
    TIRA_URL: str = ""
    TIRA_Status: str = "ok"

    def as_ordered_dict(self) -> dict:
        d = asdict(self)
        return {c: d[c] for c in COLUMNS}
