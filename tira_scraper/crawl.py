"""Crawl orchestration: walk a category, paginate, dedupe, collect rows.

Tira's listing API (Fynd Storefront Catalog) paginates with an opaque **cursor**:
the response carries ``page.has_next`` and ``page.next_id``; you pass the latter
back as ``page_id`` to get the following page. There is no usable integer page
counter, so we loop on the cursor and use ``max_pages`` purely as a safety stop.

A "category" here is a Tira **collection slug** (e.g. ``fragrances``), served at
``/collections/<slug>/items/``.
"""
from __future__ import annotations

import json
import os

from .fetcher import Fetchers
from .models import ProductRow
from .parse import parse_from_json

API_BASE = "https://api.tirabeauty.com/service/application/catalog/v1.0"


def _checkpoint_path(out_path: str) -> str:
    return out_path + ".seen.json"


def load_seen(out_path: str) -> set[str]:
    p = _checkpoint_path(out_path)
    if os.path.exists(p):
        with open(p) as f:
            return set(json.load(f))
    return set()


def save_seen(out_path: str, seen: set[str]) -> None:
    with open(_checkpoint_path(out_path), "w") as f:
        json.dump(sorted(seen), f)


def crawl_category(
    fetchers: Fetchers,
    category: str,
    out_path: str,
    max_pages: int = 200,
    page_size: int = 60,
) -> list[ProductRow]:
    """Page through one collection via the listing JSON API (cursor paging)."""
    listing_url = f"{API_BASE}/collections/{category}/items/"
    rows: list[ProductRow] = []
    seen = load_seen(out_path)

    page_id: str | None = None
    for page in range(1, max_pages + 1):
        params: dict = {"page_size": page_size}
        if page_id:
            params["page_id"] = page_id
        else:
            params["page_no"] = 1

        try:
            data = fetchers.get_json(listing_url, params=params)
        except Exception as e:  # noqa: BLE001
            rows.append(ProductRow(TIRA_URL=f"{listing_url} (page {page})", TIRA_Status="blocked"))
            print(f"[warn] page {page} blocked: {e}")
            break

        items = (data or {}).get("items") or []
        if not items:
            break

        for item in items:
            try:
                row = parse_from_json(item)
            except Exception:  # noqa: BLE001
                slug = item.get("slug") if isinstance(item, dict) else str(item)
                rows.append(ProductRow(TIRA_Status="parse_error", TIRA_URL=str(slug)[:120]))
                continue
            key = row.TIRA_SKU or row.TIRA_URL
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)

        save_seen(out_path, seen)

        page_info = (data or {}).get("page") or {}
        if not page_info.get("has_next"):
            break
        page_id = page_info.get("next_id")
        if not page_id:
            break

    return rows
