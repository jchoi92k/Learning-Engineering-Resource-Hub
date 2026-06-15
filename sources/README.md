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

Backlog items have a confirmed URL and source attribution but need individual page fetches or manual review to produce a description.

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
