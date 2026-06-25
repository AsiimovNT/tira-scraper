"""Fetching layer built on Scrapling.

Verified against scrapling 0.4.9. This module is intentionally the *only* place
that touches Scrapling, so swapping API names is a one-file change.

Strategy:
  1. Prefer Tira's internal JSON API (fast, clean) via the plain ``Fetcher``.
     Tira sits behind Akamai, which blocks naive HTTP clients; ``impersonate``
     gives curl_cffi a real browser TLS fingerprint so the request gets a 200.
  2. Fall back to a stealth/JS-rendering fetch for HTML pages that need a browser.

Auth: Tira runs on the Fynd commerce platform. Its public Storefront Catalog API
authorizes anonymous reads with ``Authorization: Bearer base64(appID:appToken)``.
The app id/token are published in the site's own page config (not secret).
"""
from __future__ import annotations

import base64
import time

try:
    # Plain HTTP fetcher (curl_cffi-backed, supports TLS impersonation).
    from scrapling.fetchers import Fetcher  # type: ignore
    _SCRAPLING = True
except Exception:  # pragma: no cover - import guard for offline scaffolding
    Fetcher = None  # type: ignore
    _SCRAPLING = False

try:
    # Stealth, browser-backed fetcher for JS-heavy / bot-protected HTML pages.
    from scrapling.fetchers import StealthyFetcher  # type: ignore
except Exception:  # pragma: no cover
    StealthyFetcher = None  # type: ignore


# Public Fynd storefront credentials for tirabeauty.com (read from its page
# config). Override via the Fetchers() constructor if they rotate.
TIRA_APP_ID = "62d53777f5ad942d3e505f77"
TIRA_APP_TOKEN = "ikdiQv6tj"
IMPERSONATE = "chrome"  # curl_cffi browser fingerprint that clears Akamai


def _auth_header(app_id: str, app_token: str) -> dict:
    basic = base64.b64encode(f"{app_id}:{app_token}".encode()).decode()
    return {"Authorization": f"Bearer {basic}"}


class Fetchers:
    def __init__(
        self,
        delay: float = 1.5,
        retries: int = 3,
        timeout: int = 30,
        app_id: str = TIRA_APP_ID,
        app_token: str = TIRA_APP_TOKEN,
    ):
        if not _SCRAPLING:
            raise RuntimeError(
                "scrapling is not installed. Run: pip install 'scrapling[fetchers]' "
                "(and `python -m scrapling install` for the stealth browser)."
            )
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json",
            **_auth_header(app_id, app_token),
        }

    def _sleep(self) -> None:
        time.sleep(self.delay)

    def get_json(self, url: str, params: dict | None = None):
        """Hit a JSON API endpoint. Returns parsed JSON (dict) or None.

        Retries network errors / 429 / 5xx with exponential backoff; fails fast
        on other 4xx (retrying an auth/not-found error is pointless).
        """
        last = None
        for attempt in range(self.retries):
            try:
                resp = Fetcher.get(
                    url,
                    params=params,
                    headers=self.headers,
                    impersonate=IMPERSONATE,
                    timeout=self.timeout,
                )
                status = getattr(resp, "status", None)
                if status is not None and status >= 400:
                    if status == 429 or status >= 500:
                        raise RuntimeError(f"retryable HTTP {status}")
                    raise RuntimeError(f"HTTP {status} for {url}")
                self._sleep()  # politeness delay only after a successful hit
                # scrapling Response exposes .json() as a method.
                accessor = getattr(resp, "json", None)
                if callable(accessor):
                    return accessor()
                return accessor
            except Exception as e:  # noqa: BLE001
                last = e
                msg = str(e)
                # Don't burn retries on non-retryable client errors.
                if msg.startswith("HTTP 4") and "429" not in msg:
                    break
                time.sleep(self.delay * (2 ** attempt))  # backoff
        raise RuntimeError(f"get_json failed for {url}: {last}")

    def get_page(self, url: str):
        """Fetch a JS-rendered HTML page. Returns a Scrapling page/adaptor.

        Fallback only — the JSON API path above is preferred. Requires the
        stealth browser (`python -m scrapling install`).
        """
        if StealthyFetcher is None:
            raise RuntimeError("StealthyFetcher unavailable; run `python -m scrapling install`.")
        last = None
        for attempt in range(self.retries):
            try:
                page = StealthyFetcher.fetch(url, headless=True)
                self._sleep()
                return page
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(self.delay * (2 ** attempt))
        raise RuntimeError(f"get_page failed for {url}: {last}")
