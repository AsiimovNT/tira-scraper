"""Map a raw product (JSON dict or HTML adaptor) to a ProductRow.

Two paths:
  - parse_from_json: Tira's Fynd Storefront Catalog API (preferred, verified).
  - parse_from_html: DOM fallback using Scrapling selectors (unused while the
    API path works; selectors remain placeholders).

The JSON field names below were confirmed against a live
``/collections/<slug>/items/`` response (see CLAUDE.md "Recon").
"""
from __future__ import annotations

from .models import ProductRow
from .price import parse_price
from .quantity import extract_quantities, normalize_primary


def _fmt_amount(v) -> str:
    """11350.0 -> '11350', 99.5 -> '99.5' (no trailing .0 on whole rupees)."""
    f = float(v)
    return str(int(f)) if f.is_integer() else str(f)


def parse_from_json(item: dict, base_url: str = "https://www.tirabeauty.com") -> ProductRow:
    """item = one product object from Tira's Fynd catalog listing JSON."""
    name = item.get("name") or ""
    # item_code is the cleanest SKU; fall back to the numeric uid.
    sku = str(item.get("item_code") or item.get("uid") or "")
    brand = (item.get("brand") or {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand")
    slug = item.get("slug") or ""
    url = slug if str(slug).startswith("http") else f"{base_url}/product/{slug}".rstrip("/")

    # Price: effective (selling) price; min == max for single-variant items.
    price_obj = item.get("price") if isinstance(item.get("price"), dict) else {}
    eff = price_obj.get("effective") or {}
    raw_price = eff.get("max", eff.get("min"))
    symbol = eff.get("currency_symbol") or "₹"
    price_text = f"{symbol}{_fmt_amount(raw_price)}" if raw_price not in (None, "") else None
    price_disp, price_num = parse_price(price_text)

    # Quantity: the strongest signal is attributes['pack-size'] ('60 ml');
    # the product name (often '... (50 ml)') is the fallback.
    pack_size = (item.get("attributes") or {}).get("pack-size") or ""
    all_qty = extract_quantities(f"{pack_size} {name}")
    primary = normalize_primary(all_qty, preferred=pack_size or None)

    sellable = item.get("sellable")
    stock = ("in_stock" if sellable else "out_of_stock") if sellable is not None else None

    return ProductRow(
        TIRA_Product_Name=name,
        TIRA_SKU=sku,
        TIRA_Qty_Normalized=primary,
        TIRA_All_Qty_Found=", ".join(all_qty) or None,
        TIRA_Price=price_disp,
        TIRA_Price_Number=price_num,
        TIRA_Brand=brand,
        TIRA_Stock=stock,
        TIRA_URL=url,
        TIRA_Status="ok" if price_num is not None else "no_price",
    )


def parse_from_html(page, url: str) -> ProductRow:
    """DOM fallback. `page` is a Scrapling Adaptor.

    VERIFY selector method (.css_first / .css(...).first) and TODO the selectors.
    """
    def text(selector: str) -> str | None:
        try:
            el = page.css_first(selector)  # VERIFY accessor
            return el.text.strip() if el else None
        except Exception:  # noqa: BLE001
            return None

    name = text("h1") or ""                                  # TODO real selector
    sku = text("[data-sku]") or ""                           # TODO
    brand = text(".brand-name")                              # TODO
    price_disp, price_num = parse_price(text(".pdp-price"))  # TODO
    size_text = text(".size-selector") or name
    all_qty = extract_quantities(size_text)
    primary = normalize_primary(all_qty)

    return ProductRow(
        TIRA_Product_Name=name,
        TIRA_SKU=sku,
        TIRA_Qty_Normalized=primary,
        TIRA_All_Qty_Found=", ".join(all_qty) or None,
        TIRA_Price=price_disp,
        TIRA_Price_Number=price_num,
        TIRA_Brand=brand,
        TIRA_Stock=None,
        TIRA_URL=url,
        TIRA_Status="ok" if price_num is not None else "no_price",
    )
