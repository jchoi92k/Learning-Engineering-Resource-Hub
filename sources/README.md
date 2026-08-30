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

## Config keys (`{source-slug}.json`)

- `discovery`: `sitemap` | `api` | `pagination` | `single_page`, with `discovery_url` and the matching `sitemap` / `api` / `pagination` / `selectors` block.
- `early_stop` (bool, default false): stop paginating once a page holds 3 consecutive or 5 total already-indexed URLs. **Declare it only for listings known to be newest-first** — for an API, make the sort explicit in `api.params` (Digital Promise `sort`, WordPress `orderby`/`order`, Mathematica `sortCriteria`). Without it every page up to the cap is scanned. Sparse-coverage sources should leave it off until backfilled.
- `detail_fetch`: `{selector, attr?, description_source?}` — fetch each new item's page for a description when the listing has none (CASEL, UChicago). `description_source` labels the rows it fills (`page-meta` for a one-sentence teaser, `page-abstract` for a full abstract); without it, meta tags count as `page-meta` and anything else as `page-abstract`. Allowed when the listing carries no usable blurb and the number of fetches per run is bounded by early-stop or `--pages`.
- `url_filter`: `{url, slug_prefix}` — keep only API items whose slug appears on a listing page (Campbell education-only).
- `request_delay` (seconds, default 5, floor 5 - lower values are raised to the floor with a warning; robots.txt `Crawl-delay` overrides upward), `robots_txt`, `url_prefix`, `url_template`, `url_transform`, `test` (`--test` expectations).

