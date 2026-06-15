# Playwright Setup and Usage

> Centralized reference for Playwright installation and runtime patterns.
> Referenced by `automation-prompt.md`, `backlog-prompt.md`, `new-source-prompt.md`, and `source-audit.md`.

---

## When to use Playwright

Use Playwright when a source's listing or publication pages are JS-rendered (Angular, React, Next.js, Nuxt) or return 403 via WebFetch. Check `meta/source-audit.md`'s "Routine source access matrix" for per-source guidance.

Sources currently requiring Playwright:

- **Digital Promise** — Angular SPA. Use `scripts/playwright_scrape.py digital-promise`.
- **TNTP** — JS-paginated listing (4 pages). Use `scripts/playwright_scrape.py tntp` for full coverage; WebFetch sees page 1 only.
- **Campbell Collaboration** — Listing page is JS-rendered; individual review pages are static.
- **Mathematica** — Listing is JS-rendered. Coveo search API needs bearer token intercepted via Playwright.
- **WWC / IES REL / JLA** — 403 from cloud WebFetch; Playwright with real Chromium headers bypasses.

---

## Installation

### Local (one-time)

```bash
pip install playwright
playwright install chromium
```

### Cloud routine (setup script, cached after first run)

```bash
#!/bin/bash
apt update && apt install -y gh
pip install playwright
npx -y playwright@latest install-deps chromium
npx -y playwright@latest install chromium
```

The cloud install adds ~2 minutes to the first run but is cached by the environment for subsequent runs.

---

## Runtime pattern

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    page.goto(url, wait_until="networkidle", timeout=30000)
    html = page.content()
    browser.close()
# Parse `html` normally (BeautifulSoup or regex).
```

**`--no-sandbox`** is required in sandboxed cloud VMs. Safe to include locally too — it's a no-op when already unsandboxed.

Cap at **one Playwright retry per URL**. If Playwright also fails, log as a non-critical failure and move on.

---

## Dedicated scraper

`scripts/playwright_scrape.py` handles TNTP and Digital Promise end-to-end (discovery, scraping, tag inference, staging). Usage:

```bash
python scripts/playwright_scrape.py tntp
python scripts/playwright_scrape.py digital-promise
```

For other JS-rendered sources, use the runtime pattern above inline.
