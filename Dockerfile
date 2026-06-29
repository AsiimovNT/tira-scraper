# Tira Beauty Scraper — container image
#
# The scraper's real work goes through Scrapling's plain `Fetcher`
# (curl_cffi under the hood) against Tira's JSON API. That needs NO browser,
# so the default image stays small.
#
# The optional StealthyFetcher fallback (get_page) DOES need a Playwright
# browser. Enable it at build time with:
#   docker build --build-arg INSTALL_BROWSER=true -t tira-scraper .

FROM python:3.13-slim AS base

# - PYTHONUNBUFFERED: print() shows up live in `docker logs`
# - PYTHONDONTWRITEBYTECODE: don't litter the image with .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# ca-certificates: TLS trust store for HTTPS requests to api.tirabeauty.com
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first so this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optionally pull the stealth browser (Chromium + system libs) for the
# StealthyFetcher fallback. Off by default to keep the image lean.
ARG INSTALL_BROWSER=false
RUN if [ "$INSTALL_BROWSER" = "true" ]; then \
        python -m scrapling install ; \
    fi

# Copy the application code (after deps, so code edits don't bust the dep cache).
COPY tira_scraper/ ./tira_scraper/
COPY config.yaml ./config.yaml

# /data is where the .xlsx output lands — mount a host volume here so the
# spreadsheet survives the container.
RUN mkdir -p /data
VOLUME ["/data"]

# `docker run tira-scraper <args>` appends to this. Default args write to /data.
ENTRYPOINT ["python", "-m", "tira_scraper.main"]
CMD ["--config", "config.yaml", "--out", "/data/tira_products.xlsx"]
