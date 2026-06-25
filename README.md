# Tira Beauty Scraper

Scrapes [tirabeauty.com](https://www.tirabeauty.com) product data into an Excel
file matching the Delhi Duty Free schema (`TIRA_` prefixed columns). Built on
[Scrapling](https://scrapling.readthedocs.io).

## Status
Fully working end-to-end. Core parsing (quantity, price), the data model, and
the Excel writer are unit-tested offline; the network layer is now implemented
and verified against the live site: it hits Tira's Fynd Storefront Catalog API
(`api.tirabeauty.com`) through Scrapling's `impersonate` fetch to clear Akamai,
with cursor pagination. A run of the `fragrances` collection produces real rows.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m scrapling install      # one-time: fetch the stealth browser (camoufox)

python -m pytest -q                                  # 10 tests should pass
python -m tira_scraper.main --categories fragrances --out tira.xlsx
```

## Building it out with Claude Code
Install Claude Code (Node.js 18+):
```bash
npm install -g @anthropic-ai/claude-code
cd tira-scraper
claude
```
Then prompt, e.g.:
> Read CLAUDE.md. Do the Recon step against tirabeauty.com, fill in the JSON
> endpoints and field names in parse.py and crawl.py, verify the Scrapling API in
> fetcher.py, then run the fragrance category and show me the first 20 rows.

Docs: https://docs.claude.com/en/docs/claude-code/overview

## Output columns
`TIRA_Product_Name, TIRA_SKU, TIRA_Qty_Normalized, TIRA_All_Qty_Found,
TIRA_Price, TIRA_Price_Number, TIRA_Brand, TIRA_Stock, TIRA_URL, TIRA_Status`

## Notes
- Fixes the DDF `2026g` bug: year-like values and implausible sizes are rejected
  by the quantity parser (`tira_scraper/quantity.py`).
- Be polite and lawful: honor robots.txt and Tira's ToS; keep request delays in.
