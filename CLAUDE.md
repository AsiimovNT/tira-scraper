# CLAUDE.md — Tira Beauty Scraper

Context for Claude Code working in this repo. Read this first.

## Goal
Scrape **tirabeauty.com** product data into an `.xlsx` matching the Delhi Duty
Free (DDF) schema, prefix `TIRA_`. Full spec: `PRD_Tira_Beauty_Scraper.md`.

## Output schema (column order is contractual)
`TIRA_Product_Name, TIRA_SKU, TIRA_Qty_Normalized, TIRA_All_Qty_Found,
TIRA_Price, TIRA_Price_Number, TIRA_Brand, TIRA_Stock, TIRA_URL, TIRA_Status`
Defined in `tira_scraper/models.py`. Drop `TIRA_Brand` for strict 9-col DDF parity.

## Architecture (one responsibility per module)
- `quantity.py` — size parsing + normalization. **Done & tested.** Includes the
  fix for the DDF `2026g` bug (rejects year-like values 1990–2099 and implausible
  magnitudes).
- `price.py` — `'₹10,560' -> ('₹10,560', 10560)`. **Done & tested.**
- `models.py` — `ProductRow` dataclass + column order. **Done.**
- `writer.py` — pandas/openpyxl xlsx writer, SKU as text. **Done & tested.**
- `fetcher.py` — the **only** file that imports Scrapling. **Done & verified**
  (scrapling 0.4.9; `impersonate="chrome"` + Bearer auth clears Akamai).
- `parse.py` — raw item -> `ProductRow`. **JSON keys verified** against the live
  Fynd catalog response (`parse_from_html` remains an unused DOM fallback).
- `crawl.py` — **Done.** Cursor pagination over `/collections/<slug>/items/`,
  dedupe, resume checkpoint.
- `main.py` — CLI.

## Recon findings (verified live — already wired in)
Tira runs on the **Fynd** commerce platform. Its public Storefront Catalog API
serves the data; no DOM scraping needed.

- **Base:** `https://api.tirabeauty.com/service/application/catalog/v1.0`
  (the central `api.fynd.com` host returns 401 — must use the tira host).
- **Listing:** `GET /collections/<slug>/items/` — a "category" is a collection
  slug (e.g. `fragrances`, item_total ~6097). Also: `GET /products/`.
- **Auth:** `Authorization: Bearer base64(appID:appToken)` with the public
  app creds from the site config (`62d53777f5ad942d3e505f77` / `ikdiQv6tj`).
- **Akamai:** plain HTTP gets "Access Denied"; Scrapling `Fetcher.get(...,
  impersonate="chrome")` returns 200. Response JSON via `resp.json()` (method).
- **Pagination:** cursor — `page.has_next` + `page.next_id`, pass back as
  `page_id`. No usable integer page counter.
- **Field map:** name←`name`, sku←`item_code`, brand←`brand.name`,
  url←`/product/{slug}`, price←`price.effective.max` (+`currency_symbol`),
  stock←`sellable`, **qty←`attributes['pack-size']`** ("60 ml"); multi-piece
  gift sets have no pack-size, so qty is correctly left blank.

**Deps:** `pip install "scrapling[fetchers]"` then `python -m scrapling install`
(also needs `playwright` importable). Scrapling 0.4.9.

**Verified offline:** quantity, price, models, writer (10 unit tests pass).
**Fallback:** `parse.py::parse_from_html` selectors are still placeholders —
only needed if the API path ever gets blocked.

## Commands
```bash
pip install -r requirements.txt          # then any scrapling browser install step
python -m pytest -q                       # run tests (add pytest to your env)
python -m tira_scraper.main --categories fragrance --out tira.xlsx --delay 1.5
python -m tira_scraper.main --config config.yaml
```

## Conventions
- Keep all Scrapling calls inside `fetcher.py`.
- Keep `TIRA_SKU` a string everywhere (leading zeros matter).
- Be polite: honor robots.txt, keep `--delay` ≥ 1s, back off on 429/403.
- Never abort a run on one bad page — set `TIRA_Status` (`ok` / `no_price` /
  `parse_error` / `blocked`) and continue.
- Add a unit test when you add a parser branch.

## Compliance
Public, non-personalized data only. Check Tira's ToS and robots.txt before any
scaled or recurring run.
