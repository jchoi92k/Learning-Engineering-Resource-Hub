# Contributing

Thanks for your interest in the Renaissance AI and Education Resource Hub.

## Suggest a source or resource

The most useful contribution is pointing us at a source we should index. Open a
[New source suggestion](../../issues/new?template=new-source.md) issue. The bar for inclusion:

1. **Documented editorial review** — the organization vets what it publishes (evidence standards, peer review, or an editorial process).
2. **Public accessibility** — content reachable without a paywall or login.
3. **Scope** — directly about K-12 or higher-education learning.

Full criteria: `meta/inclusion-criteria.md`.

## Report a problem

Broken link, wrong description, miscategorized entry — open an issue with the entry number
(the `### N.` heading in `llms-full.txt`) and what's wrong.

## Code and content changes

1. Fork, then clone your fork.
2. Set up the pipeline environment: `pip install -r requirements.txt`
3. Make your change. The important invariants:
   - `data/hub.db` is the single source of truth. Never hand-edit files in `docs/` — change the DB (or the scripts), then regenerate with `python scripts/build_from_db.py`.
   - Entry descriptions must come from fetched page content, never from titles alone.
   - All files are UTF-8, no BOM.
4. Run `python scripts/build_from_db.py` and include the regenerated outputs in your PR.
5. Open a pull request describing what changed and why.

Orientation for the repo layout: `index.md`. Operational detail (entry format, tag schema, scraping conventions): `meta/agent-guide.md` and `sources/README.md`.

## MCP server

The worker in `worker/` serves the MCP interface. Test locally with `npx wrangler dev` from `worker/`
and run `node test-mcp.mjs` against it. Deploys are maintainer-only.
