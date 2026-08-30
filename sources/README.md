# Source Profiles

Each `{source-slug}.md` file documents how to scrape a specific source: discovery method, access constraints, scope, metadata fields, and step-by-step instructions.

## Profile format

All profiles follow the same sections: Discovery, Access, Scope, Entry metadata, Scraping instructions, Quirks. Read the relevant profile before scraping a source.

## Two-pass scraping model

**Pass 1 (main scrape):** Use the discovery method in the profile (sitemap, API, pagination) to collect listing-level metadata. Items with adequate descriptions get staged as entries. Items with thin or missing descriptions go to the backlog. **Do NOT fetch individual resource pages during the main scrape** — the point of the backlog is to separate what's ready from what needs extra work.

**Pass 2 (backlog processing):** Done separately, on request. Fetch individual pages for backlog items to get richer descriptions. If a page still yields nothing usable, drop the item.

## Backlog convention

When scraping produces URLs that can't be fully indexed — missing description, 404, no usable metadata — write them to `{source-slug}-backlog.txt` in this directory. Format: one entry per line, tab-separated:

```
{url}\t{title}\t{reason}
```

Backlog items have a confirmed URL and source attribution but need individual page fetches or manual review to produce a description. Since 2026-08-29 they also travel in the staging JSON (`backlog_items`) and `process_staged.py` records them in hub.db as excluded rows with `exclude_reason = no_description_pending`, so they count as known on the next run; a backfill flips them active by filling the description.

## Post-run sniff test

After every scrape run that produces new entries, spot-check before integrating:

1. Pick 3-5 entries (mix of new and existing from the same source)
2. Verify: titles make sense, URLs look valid, descriptions are substantive (not truncated or garbled), tags are appropriate, types are correct
3. Click 1-2 URLs to confirm they resolve to the right page
4. If anything looks off, investigate before merging to `llms-full.txt`

## Fetch-failure handling

When fetching individual pages for descriptions:

1. If a fetch fails (404, 403, timeout, empty content), log it and move to the next URL.
2. If failures repeat 3 or more times consecutively, stop fetching and log the pattern — the source may be rate-limiting or blocking. Write all remaining unfetched URLs to the backlog file.
3. Never retry a failed URL in the same run. Backlogged URLs get retried in a future session.

## Run modes and the request audit

- `python scripts/scrape.py <src>` — weekly mode: diff against hub.db, early-stop where the config declares it.
- `python scripts/scrape.py <src> --backfill [--pages N]` — catch-up mode: every listing page up to the cap is scanned (early-stop off) but URLs already in hub.db are still skipped, so no known page is fetched twice; use it for one-off backfills of sparse sources.
- `--no-diff` — include already-indexed items in the staging file (ground-truth re-scrapes); `process_staged.py` still refuses to insert known URLs.
- The throttle clock is kept in memory for the process and, per host, in `docs/staging/logs/last-request.json`, so a run started right after another (a `--test` then the real run, two configs on one host) still waits the full delay before its first request. Every request (robots.txt, listing pages, API calls, detail pages, retries) is appended with its send time to `docs/staging/logs/<src>-requests.log`. A run ends with a request audit — count, unique URLs, retries, status histogram, smallest gap between sends — and warns if any URL was requested more than once (retries after 429/503 excepted) or a gap undercut the delay. `python scripts/scrape.py <src> --audit` re-checks the log without fetching. Run `--test`, then `--backfill --pages 1`, read the audit, and only then the full run.

## Config keys (`{source-slug}.json`)

- `discovery`: `sitemap` | `api` | `pagination` | `single_page`, with `discovery_url` and the matching `sitemap` / `api` / `pagination` / `selectors` block.
- `early_stop` (bool, default false): stop paginating once a page holds 3 consecutive or 5 total already-indexed URLs. **Declare it only for listings known to be newest-first** — for an API, make the sort explicit in `api.params` (Digital Promise `sort`, WordPress `orderby`/`order`, Mathematica `sortCriteria`). Without it every page up to the cap is scanned. Sparse-coverage sources should leave it off until backfilled.
- `detail_fetch`: `{selector, attr?, description_source?}` — fetch each new item's page for a description when the listing has none (CASEL, UChicago). `description_source` labels the rows it fills (`page-meta` for a one-sentence teaser, `page-abstract` for a full abstract); without it, meta tags count as `page-meta` and anything else as `page-abstract`. Allowed when the listing carries no usable blurb and the number of fetches per run is bounded by early-stop or `--pages`.
- `url_filter`: `{url, slug_prefix}` — keep only API items whose slug appears on a listing page (Campbell education-only).
- `type_allow`: list of source type labels to index (case-insensitive; e.g. `["Research", "Report"]`). Items with another label are not dropped: they are staged as `filtered_items` and `process_staged.py` inserts them as excluded rows with reason `type_filtered:<label>` (title, URL, blurb and raw item kept), so the scope call can be reversed with `curate.py reactivate` without re-scraping. Items with no type yet pass the first check; a `detail_fetch.extra_fields` type is checked after the page fetch.
- `detail_fetch.extra_fields`: `{"type": {selector, attr?}, "date": {...}}` — fill other item fields from the same detail page (a type or date that only the page carries). Every detail fetch also records `page_meta` (description, og:*, article:published_time, citation_*, canonical, title), `page_text` (the page's readable main text, capped at 20,000 characters), `fetched_status` and `fetched_at` on the item; a 200 makes the row `url_status = verified` at insert time so `verify_urls.py` does not request the page again.
- `lookups`: list of `{field, url, id_path?, name_path?, items_path?}` — fetch a taxonomy endpoint once per run and replace the ids in `item[field]` (a value or a list) with names; the ids are kept as `item[field + "_ids"]`, and for `type` the first name becomes the type while all names go to `type_labels` (EdTrust `type-of-content`/`topic`, NWEA's five taxonomies).
- `api.windows`: list of body/params patches (e.g. Algolia `numericFilters` date ranges) run as separate passes for indexes that cap total results; the URL dedup merges the passes (Brookings, 1,000-hit cap).
- `detail_fetch.text_selector`: CSS selector that scopes `page_text` to one container on templates without `<main>`/`<article>` (NWEA `div.txtcol`).
- `request_delay` (seconds, default 5, floor 5 - lower values are raised to the floor with a warning; robots.txt `Crawl-delay` overrides upward), `robots_txt`, `url_prefix`, `url_template`, `url_transform`, `test` (`--test` expectations).

