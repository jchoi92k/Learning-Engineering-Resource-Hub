# Legacy endpoint proxy (`le-resource-hub`)

Forwards the old MCP endpoint to the current one so early agent configs keep working.

- **Old URL:** `https://le-resource-hub.joon-96a.workers.dev/mcp`
- **Current URL:** `https://renaissance-hub.joon-96a.workers.dev/mcp` (source in `../worker/`)

The old `le-resource-hub` worker used to run an outdated copy of the MCP server
(serverInfo `1.0.0`, protocol pinned to `2025-03-26`) and drifted further behind
on every corpus refresh. This worker replaces that with a thin shim that forwards
every request — method, body, and headers preserved — to `renaissance-hub` via a
Cloudflare **service binding** (`env.HUB.fetch(request)`).

Why a service binding rather than `fetch()` to the workers.dev URL: worker-to-worker
requests over a public `*.workers.dev` URL are not supported by default. A service
binding is an internal, zero-latency, zero-extra-cost link between two Workers on
the same account.

Callers only ever see `le-resource-hub`; there is no redirect and no cross-origin
hop, so there is no CORS concern (the current worker already returns
`Access-Control-Allow-Origin: *`, which passes through).

## Deploy

```bash
cd worker-le-resource-hub && npx wrangler deploy
```

No data lives here — nothing to rebuild or re-deploy when the corpus changes.
The canonical worker to keep updated is `../worker/`.
