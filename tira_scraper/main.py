"""CLI entry point.

Examples:
    python -m tira_scraper.main --categories fragrance makeup --out tira.xlsx
    python -m tira_scraper.main --config config.yaml
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

import yaml

from .crawl import crawl_category
from .fetcher import Fetchers
from .writer import write_xlsx


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scrape tirabeauty.com into a DDF-schema xlsx.")
    ap.add_argument("--config", help="YAML config file")
    ap.add_argument("--categories", nargs="*", help="Category slugs to crawl")
    ap.add_argument("--out", default="tira_products.xlsx", help="Output .xlsx path")
    ap.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--max-pages", type=int, default=200)
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    categories = args.categories or cfg.get("categories") or []
    out = args.out or cfg.get("out", "tira_products.xlsx")
    delay = args.delay if args.delay is not None else cfg.get("delay", 1.5)

    if not categories:
        ap.error("No categories given (use --categories or config.yaml).")

    fetchers = Fetchers(delay=delay, retries=args.retries)

    all_rows = []
    for cat in categories:
        print(f"[info] crawling category: {cat}")
        all_rows.extend(crawl_category(fetchers, cat, out, max_pages=args.max_pages))

    write_xlsx(all_rows, out)

    summary = Counter(r.TIRA_Status for r in all_rows)
    print(f"[done] {len(all_rows)} rows -> {out}")
    print(f"[done] status: {dict(summary)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
