import rawData from "../../docs/data.json";
const data = typeof rawData === "string" ? JSON.parse(rawData) : rawData;

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, mcp-session-id",
};

// ── Data helpers (shared by HTTP API and MCP) ──

const EMBEDDING_MODEL = "@cf/baai/bge-base-en-v1.5";

// Embed the query and return entries nearest in the Vectorize index,
// ordered by similarity. Returns null when semantic search is unavailable
// (missing bindings, empty index, or a runtime error) so callers can fall
// back to keyword matching.
async function semanticCandidates(env, query) {
  if (!env || !env.AI || !env.VECTORIZE) return null;
  try {
    const emb = await env.AI.run(EMBEDDING_MODEL, { text: [query] });
    const vector = emb.data && emb.data[0];
    if (!vector) return null;
    const res = await env.VECTORIZE.query(vector, { topK: 100, returnMetadata: "none" });
    if (!res || !res.matches || res.matches.length === 0) return null;
    const byNum = new Map(data.entries.map((e) => [e.num, e]));
    return res.matches
      .map((m) => byNum.get(parseInt(m.id, 10)))
      .filter(Boolean);
  } catch {
    return null;
  }
}

function filterEntries({ tags = [], tagMode = "all", types = [], sources = [], query = "", limit = 20, offset = 0, sort_by = "index", candidates = null }) {
  // `candidates` (from semantic search) replaces the corpus as the result
  // pool and carries its own relevance order; keyword `query` matching is
  // skipped in that case.
  let results = candidates || data.entries;

  if (tags.length > 0) {
    const match = tagMode === "any"
      ? (e) => tags.some((t) => e.tags.includes(t))
      : (e) => tags.every((t) => e.tags.includes(t));
    results = results.filter(match);
  }
  if (types.length > 0) {
    results = results.filter((e) => types.includes(e.type));
  }
  if (sources.length > 0) {
    results = results.filter((e) =>
      sources.some((s) => e.source.toLowerCase().includes(s.toLowerCase()))
    );
  }
  if (query && !candidates) {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    results = results.filter((e) => {
      const text = `${e.title} ${e.desc} ${e.tags.join(" ")}`.toLowerCase();
      return words.every((w) => text.includes(w));
    });
  }

  if (sort_by === "title") {
    results = [...results].sort((a, b) => a.title.localeCompare(b.title));
  } else if (sort_by === "source") {
    results = [...results].sort((a, b) => a.source.localeCompare(b.source));
  } else if (sort_by === "type") {
    results = [...results].sort((a, b) => a.type.localeCompare(b.type));
  }

  const total = results.length;
  const capped = Math.min(limit, 100);
  const paged = results.slice(offset, offset + capped);
  const nextOffset = offset + capped < total ? offset + capped : null;
  return { results: paged, total, limited: total > offset + capped, nextCursor: nextOffset };
}

// Aggregates are immutable per deploy — compute once at module load
// instead of re-scanning all entries on every request.
const TAG_COUNTS = (() => {
  const counts = {};
  for (const e of data.entries) {
    for (const t of e.tags) counts[t] = (counts[t] || 0) + 1;
  }
  return counts;
})();

const TYPE_COUNTS = (() => {
  const counts = {};
  for (const e of data.entries) counts[e.type] = (counts[e.type] || 0) + 1;
  return counts;
})();

const SOURCE_COUNTS = (() => {
  const counts = {};
  for (const e of data.entries) counts[e.source] = (counts[e.source] || 0) + 1;
  return counts;
})();

// Derived from the data so the schema can never drift from the corpus.
const TYPE_VALUES = Object.keys(TYPE_COUNTS).sort();

function getTagCounts() { return TAG_COUNTS; }
function getTypeCounts() { return TYPE_COUNTS; }
function getSourceCounts() { return SOURCE_COUNTS; }

function formatEntry(e) {
  return {
    num: e.num,
    title: e.title,
    url: e.url,
    type: e.type,
    source: e.source,
    tags: e.tags,
    description: e.desc,
    description_source: e.description_source || null,
  };
}

// Results that carry both a text block and structuredContent (MCP spec:
// "a tool that returns structured content SHOULD also return the serialized
// JSON in a TextContent block").
function structured(payload) {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

// search/fetch follow the two-tool interface ChatGPT deep research and
// company knowledge require (search -> ids/titles/urls, fetch(id) -> document).
const SEARCH_FETCH_LIMIT = 20;

function findRelated(num, limit = 10) {
  const target = data.entries.find((e) => e.num === num);
  if (!target) return null;

  const targetTags = new Set(target.tags);
  const scored = data.entries
    .filter((e) => e.num !== num)
    .map((e) => {
      const overlap = e.tags.filter((t) => targetTags.has(t)).length;
      return { entry: e, overlap };
    })
    .filter((s) => s.overlap > 0)
    .sort((a, b) => b.overlap - a.overlap)
    .slice(0, limit);

  return scored.map((s) => ({
    ...formatEntry(s.entry),
    shared_tags: s.entry.tags.filter((t) => targetTags.has(t)),
    overlap: s.overlap,
  }));
}

// ── MCP Protocol (Streamable HTTP) ──

const TOOL_DEFINITIONS = [
  {
    name: "search_resources",
    description:
      `Search the Renaissance AI and Education Resource Hub — ${data.entries.length} curated evidence-based K-12 and higher education resources. Natural-language queries use semantic search by default; combine with tag, type, and source filters. Call list_tags first to see available filter values.`,
    inputSchema: {
      type: "object",
      properties: {
        tags: {
          type: "array",
          items: { type: "string" },
          description:
            "Filter by tags. Examples: math-education, meta-analysis, k-12, rct, literacy, sel, genai, open-datasets",
        },
        tag_mode: {
          type: "string",
          enum: ["all", "any"],
          description:
            "How to combine multiple tags: 'all' = entry must have ALL tags (default, use for precise queries), 'any' = entry must have at least ONE tag (use for broad queries)",
        },
        type: {
          type: "string",
          enum: TYPE_VALUES,
          description: "Filter by resource type",
        },
        source: {
          type: "string",
          description:
            "Filter by source organization (partial match). Examples: What Works Clearinghouse, Campbell, Mathematica, Digital Promise",
        },
        query: {
          type: "string",
          description:
            "Natural-language search across title, description, and tags. By default uses semantic (embedding) search, so concept-level queries work even without exact word overlap. Results are ordered by relevance. If results look off, retry with different phrasing, set search_mode: 'keyword' for exact substring matching, or browse list_tags and filter by tag.",
        },
        search_mode: {
          type: "string",
          enum: ["semantic", "keyword"],
          description:
            "How to match the query. 'semantic' (default): embedding similarity, best for concepts and questions; returns up to the 100 nearest entries. 'keyword': literal substring match, all words must appear (AND logic); best for exact terms, names, or exhaustive matching. count_only always uses keyword so counts are corpus-wide.",
        },
        sort_by: {
          type: "string",
          enum: ["index", "title", "source", "type"],
          description: "Sort results by field. Default: index (entry number order).",
        },
        limit: {
          type: "number",
          description: "Maximum results to return (default 20, max 100)",
        },
        cursor: {
          type: "number",
          description: "Pagination cursor returned from a previous search. Pass to get the next page of results.",
        },
        count_only: {
          type: "boolean",
          description: "If true, return only the count of matching entries without the entries themselves. Useful for scoping queries.",
        },
      },
    },
  },
  {
    name: "list_tags",
    description:
      "List all available tags in the Renaissance AI and Education Resource Hub with entry counts. Call this first to understand what filter values are available before searching.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "list_sources",
    description:
      "List all source organizations in the Renaissance AI and Education Resource Hub with entry counts.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "get_stats",
    description:
      "Get a summary of the Renaissance AI and Education Resource Hub: total entries, entries per source, per type, top tags, and last updated date.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "get_entry",
    description:
      "Get full details of a specific entry by its number.",
    inputSchema: {
      type: "object",
      properties: {
        num: {
          type: "number",
          description: `Entry number (1–${data.entries.length})`,
        },
      },
      required: ["num"],
    },
  },
  {
    name: "get_entries_batch",
    description:
      "Get full details of multiple entries by their numbers. More efficient than calling get_entry repeatedly.",
    inputSchema: {
      type: "object",
      properties: {
        nums: {
          type: "array",
          items: { type: "number" },
          description: "Array of entry numbers to retrieve (max 50).",
        },
      },
      required: ["nums"],
    },
  },
  {
    name: "find_related",
    description:
      "Find entries related to a given entry, ranked by shared tag overlap. Useful for discovering similar resources.",
    inputSchema: {
      type: "object",
      properties: {
        num: {
          type: "number",
          description: "Entry number to find related entries for.",
        },
        limit: {
          type: "number",
          description: "Maximum related entries to return (default 10, max 50).",
        },
      },
      required: ["num"],
    },
  },
  {
    name: "search",
    description:
      `Search the Renaissance AI and Education Resource Hub (${data.entries.length} curated evidence-based education resources) and get the ids, titles and URLs of the best matches — semantic search, keyword fallback, up to ${SEARCH_FETCH_LIMIT} results. Follow up with fetch(id) for an entry's description and metadata. This is the search/fetch interface used by ChatGPT deep research and company knowledge; for filters, pagination and counts use search_resources.`,
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Natural-language search query." },
      },
      required: ["query"],
    },
    outputSchema: {
      type: "object",
      properties: {
        results: {
          type: "array",
          items: {
            type: "object",
            properties: {
              id: { type: "string", description: "Entry id — pass to fetch" },
              title: { type: "string" },
              url: { type: "string", description: "Canonical URL of the resource, for citation" },
            },
            required: ["id", "title", "url"],
          },
        },
      },
      required: ["results"],
    },
  },
  {
    name: "fetch",
    description:
      "Fetch one hub entry by the id returned from search (the entry number as a string): its title, canonical URL, description and metadata (type, source organization, tags, description provenance).",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string", description: "Entry id from search results, e.g. \"1234\"" },
      },
      required: ["id"],
    },
    outputSchema: {
      type: "object",
      properties: {
        id: { type: "string" },
        title: { type: "string" },
        text: { type: "string", description: "The entry's description" },
        url: { type: "string" },
        metadata: { type: "object" },
      },
      required: ["id", "title", "text", "url"],
    },
  },
];

async function handleToolCall(name, args, env) {
  switch (name) {
    case "search_resources": {
      const { tags = [], tag_mode = "all", type, source, query, sort_by = "index", limit = 20, cursor, count_only = false, search_mode = "semantic" } = args;
      const tagMode = tag_mode;
      const types = type ? [type] : [];
      const sources = source ? [source] : [];
      const offset = cursor || 0;

      // Semantic search embeds the query and ranks by similarity; used by
      // default when a query is present. count_only always uses keyword
      // matching so the count stays an exhaustive corpus-wide number.
      let candidates = null;
      let modeUsed = "keyword";
      if (query && !count_only && search_mode !== "keyword") {
        candidates = await semanticCandidates(env, query);
        if (candidates) modeUsed = "semantic";
      }

      const { results, total, limited, nextCursor } = filterEntries({ tags, tagMode, types, sources, query, sort_by, limit, offset, candidates });

      if (count_only) {
        return structured({ total_matches: total });
      }

      const response = { total_matches: total, showing: results.length, limited, search_mode: query ? modeUsed : undefined, entries: results.map(formatEntry) };
      if (nextCursor !== null) response.next_cursor = nextCursor;
      return structured(response);
    }

    case "list_tags": {
      const sorted = (obj) =>
        Object.entries(obj)
          .sort((a, b) => b[1] - a[1])
          .map(([k, v]) => ({ name: k, count: v }));
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            total_entries: data.entries.length,
            tags: sorted(getTagCounts()),
            types: sorted(getTypeCounts()),
          }, null, 2),
        }],
      };
    }

    case "list_sources": {
      const counts = getSourceCounts();
      const sources = Object.entries(counts)
        .sort((a, b) => b[1] - a[1])
        .map(([name, count]) => ({ name, count }));
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ total_entries: data.entries.length, sources }, null, 2),
        }],
      };
    }

    case "get_stats": {
      const tagCounts = getTagCounts();
      const topTags = Object.entries(tagCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15)
        .map(([name, count]) => ({ name, count }));
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            total_entries: data.entries.length,
            last_updated: data.meta.last_updated,
            sources: getSourceCounts(),
            types: getTypeCounts(),
            top_tags: topTags,
          }, null, 2),
        }],
      };
    }

    case "get_entry": {
      const entry = data.entries.find((e) => e.num === args.num);
      if (!entry) {
        return { content: [{ type: "text", text: `No entry with number ${args.num}` }], isError: true };
      }
      return { content: [{ type: "text", text: JSON.stringify(formatEntry(entry), null, 2) }] };
    }

    case "get_entries_batch": {
      const nums = (args.nums || []).slice(0, 50);
      const entries = nums
        .map((n) => data.entries.find((e) => e.num === n))
        .filter(Boolean)
        .map(formatEntry);
      const missing = nums.filter((n) => !data.entries.find((e) => e.num === n));
      const response = { found: entries.length, entries };
      if (missing.length > 0) response.missing = missing;
      return { content: [{ type: "text", text: JSON.stringify(response, null, 2) }] };
    }

    case "find_related": {
      const limit = Math.min(args.limit || 10, 50);
      const related = findRelated(args.num, limit);
      if (related === null) {
        return { content: [{ type: "text", text: `No entry with number ${args.num}` }], isError: true };
      }
      return {
        content: [{
          type: "text",
          text: JSON.stringify({ entry: args.num, related_count: related.length, related }, null, 2),
        }],
      };
    }

    case "search": {
      const query = typeof args.query === "string" ? args.query.trim() : "";
      if (!query) {
        return { content: [{ type: "text", text: "search needs a non-empty query string." }], isError: true };
      }
      const candidates = await semanticCandidates(env, query);
      const { results } = filterEntries({ query, limit: SEARCH_FETCH_LIMIT, candidates });
      return structured({
        results: results.map((e) => ({ id: String(e.num), title: e.title, url: e.url })),
      });
    }

    case "fetch": {
      const num = parseInt(args.id, 10);
      const entry = Number.isFinite(num) ? data.entries.find((e) => e.num === num) : undefined;
      if (!entry) {
        return {
          content: [{ type: "text", text: `No entry with id ${args.id}. Ids are the entry numbers returned by search.` }],
          isError: true,
        };
      }
      return structured({
        id: String(entry.num),
        title: entry.title,
        text: entry.desc || "",
        url: entry.url,
        metadata: {
          num: entry.num,
          type: entry.type,
          source: entry.source,
          tags: entry.tags,
          description_source: entry.description_source || null,
        },
      });
    }

    default:
      return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
  }
}

const SESSION_ID = `renaissance-hub-${data.meta.last_updated}`;

function jsonRpc(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function jsonRpcError(id, code, message) {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

// Spec revisions this stateless tools-only server is compatible with.
// We echo the client's requested version when we support it (per spec
// version negotiation), otherwise answer with our latest supported.
const SUPPORTED_PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"];

async function processMcpMessage(msg, env) {
  const { method, id, params } = msg;

  if (id === undefined) return null;

  switch (method) {
    case "initialize": {
      const requested = params && params.protocolVersion;
      const negotiated = SUPPORTED_PROTOCOL_VERSIONS.includes(requested)
        ? requested
        : SUPPORTED_PROTOCOL_VERSIONS[0];
      return jsonRpc(id, {
        protocolVersion: negotiated,
        capabilities: { tools: {} },
        serverInfo: { name: "renaissance-hub", version: "2.0.0" },
      });
    }
    case "tools/list":
      return jsonRpc(id, { tools: TOOL_DEFINITIONS });
    case "tools/call":
      if (!params || typeof params.name !== "string") {
        return jsonRpcError(id, -32602, "Invalid params: tools/call requires params.name");
      }
      try {
        return jsonRpc(id, await handleToolCall(params.name, params.arguments || {}, env));
      } catch (err) {
        // Per MCP SEP-1303, argument/validation failures are tool execution
        // errors (isError results), not protocol errors — the model can read
        // the message and self-correct on the next call.
        return jsonRpc(id, {
          content: [{
            type: "text",
            text: `Tool '${params.name}' failed: ${err.message}. Check the argument types and values against the tool's input schema, then retry.`,
          }],
          isError: true,
        });
      }
    case "ping":
      return jsonRpc(id, {});
    default:
      return jsonRpcError(id, -32601, `Method not found: ${method}`);
  }
}

function mcpResponse(body, status = 200) {
  return new Response(body ? JSON.stringify(body) : null, {
    status,
    headers: {
      "Content-Type": "application/json",
      "Mcp-Session-Id": SESSION_ID,
      ...CORS_HEADERS,
    },
  });
}

async function handleMcpPost(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return mcpResponse(jsonRpcError(null, -32700, "Parse error"), 400);
  }

  if (Array.isArray(body)) {
    const responses = (await Promise.all(body.map((m) => processMcpMessage(m, env)))).filter((r) => r !== null);
    return responses.length === 0 ? mcpResponse(null, 202) : mcpResponse(responses);
  }

  const response = await processMcpMessage(body, env);
  return response === null ? mcpResponse(null, 202) : mcpResponse(response);
}

// ── HTTP API ──

function textResponse(body, status = 200) {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", ...CORS_HEADERS },
  });
}

function formatMarkdown({ results, total, limited }) {
  const lines = [];
  lines.push("# Renaissance AI and Education Resource Hub — Search Results");
  lines.push("");
  lines.push(
    `> ${total} entries matched. ${limited ? `Showing first ${results.length}. Add &limit=100 for more.` : `Showing all ${results.length}.`}`,
  );
  lines.push(`> Last updated: ${data.meta.last_updated} | Total in hub: ${data.meta.total}`);
  lines.push("");

  for (const e of results) {
    lines.push(`### ${e.num}. ${e.title}`);
    lines.push("");
    lines.push(`- **URL:** ${e.url}`);
    lines.push(`- **Type:** ${e.type}`);
    lines.push(`- **Source:** ${e.source}`);
    lines.push(`- **Tags:** ${e.tags.join(", ")}`);
    lines.push("");
    if (e.desc) {
      lines.push(e.desc);
      lines.push("");
    }
    lines.push("---");
    lines.push("");
  }

  return lines.join("\n");
}

function helpPage() {
  const sorted = (obj) =>
    Object.entries(obj)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${k} (${v})`)
      .join(", ");

  return `# Renaissance AI and Education Resource Hub — API

> ${data.meta.total} curated evidence-based K-12 and higher education resources.
> Last updated: ${data.meta.last_updated}

## HTTP API

Fetch /search with query parameters:

  /search?tag=meta-analysis&tag=math-education
  /search?type=dataset&q=knowledge+tracing
  /search?source=campbell&limit=30

| Param | Effect | Example |
|---|---|---|
| tag | Filter by tag (multiple, OR logic) | tag=rct&tag=meta-analysis |
| type | Filter by resource type | type=paper |
| source | Filter by source (partial match) | source=campbell |
| q | Keyword search (title, desc, tags) | q=tutoring |
| limit | Max results (default 50, max 100) | limit=20 |

## MCP (Model Context Protocol)

POST /mcp — Streamable HTTP transport.
Compatible with Claude Code, Cursor, Windsurf, Codex, GitHub Copilot.

Tools: search, fetch (the ChatGPT deep-research search/fetch interface), search_resources, list_tags, list_sources, get_stats, get_entry, get_entries_batch, find_related

Add to your MCP config:
  { "type": "http", "url": "https://renaissance-hub.joon-96a.workers.dev/mcp" }

## Tags

${sorted(getTagCounts())}

## Types

${sorted(getTypeCounts())}
`;
}

// ── Router ──

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // Per-IP rate limit (binding configured in wrangler.toml; skipped if absent).
    if (env && env.RATE_LIMITER) {
      const ip = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const { success } = await env.RATE_LIMITER.limit({ key: ip });
        if (!success) {
          return new Response("Rate limit exceeded. Try again shortly.", {
            status: 429,
            headers: { "Retry-After": "60", ...CORS_HEADERS },
          });
        }
      } catch {
        // Rate limiter unavailable — serve the request rather than fail closed.
      }
    }

    if (url.pathname === "/mcp") {
      // Streamable HTTP spec: reject requests with an invalid Origin (403).
      // Non-browser clients send no Origin and pass through untouched.
      const origin = request.headers.get("Origin");
      if (origin && !/^https?:\/\//.test(origin)) {
        return new Response("Forbidden: invalid Origin", { status: 403, headers: CORS_HEADERS });
      }

      if (request.method === "POST") return handleMcpPost(request, env);
      if (request.method === "DELETE") return mcpResponse(null, 200);
      if (request.method === "GET") return new Response("Method Not Allowed", { status: 405, headers: CORS_HEADERS });
      return mcpResponse({ name: "renaissance-hub", version: "2.0.0", tools: TOOL_DEFINITIONS.map((t) => t.name) });
    }

    if (url.pathname === "/" || url.pathname === "") {
      return textResponse(helpPage());
    }

    if (url.pathname === "/search") {
      const params = url.searchParams;
      const result = filterEntries({
        tags: params.getAll("tag"),
        tagMode: params.get("tag_mode") || "any",
        types: params.getAll("type"),
        sources: params.getAll("source"),
        query: params.get("q") || "",
        limit: Math.min(parseInt(params.get("limit") || "50", 10), 100),
      });
      return textResponse(formatMarkdown(result));
    }

    return textResponse("Not found. Try / for usage, /search for HTTP API, or POST /mcp for MCP.", 404);
  },
};
