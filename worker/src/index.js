import rawData from "../../docs/data.json";
const data = typeof rawData === "string" ? JSON.parse(rawData) : rawData;

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, mcp-session-id",
};

// ── Data helpers (shared by HTTP API and MCP) ──

function filterEntries({ tags = [], tagMode = "all", types = [], sources = [], query = "", limit = 20, offset = 0, sort_by = "index" }) {
  let results = data.entries;

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
  if (query) {
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

function getTagCounts() {
  const counts = {};
  for (const e of data.entries) {
    for (const t of e.tags) counts[t] = (counts[t] || 0) + 1;
  }
  return counts;
}

function getTypeCounts() {
  const counts = {};
  for (const e of data.entries) counts[e.type] = (counts[e.type] || 0) + 1;
  return counts;
}

function getSourceCounts() {
  const counts = {};
  for (const e of data.entries) counts[e.source] = (counts[e.source] || 0) + 1;
  return counts;
}

function formatEntry(e) {
  return {
    num: e.num,
    title: e.title,
    url: e.url,
    type: e.type,
    source: e.source,
    tags: e.tags,
    description: e.desc,
  };
}

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
      `Search the Renaissance AI and Education Resource Hub — ${data.entries.length} curated evidence-based K-12 and higher education resources. Filter by tags, type, source, or keyword. Call list_tags first to see available filter values.`,
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
          enum: [
            "report", "dataset", "paper", "framework",
            "platform", "code", "blog-post", "presentation", "project-website",
          ],
          description: "Filter by resource type",
        },
        source: {
          type: "string",
          description:
            "Filter by source organization (partial match). Examples: What Works Clearinghouse, Campbell, JEDM, Digital Promise",
        },
        query: {
          type: "string",
          description:
            "Optional keyword search across title, description, and tags. All words must match (AND logic).",
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
    name: "get_full_index",
    description:
      `Get the complete index of all ${data.entries.length} entries in the Renaissance AI and Education Resource Hub. Returns every entry with metadata and descriptions. Use this when you need comprehensive coverage or want to reason over the full corpus. For targeted queries, use search_resources instead.`,
    inputSchema: {
      type: "object",
      properties: {
        format: {
          type: "string",
          enum: ["full", "compact"],
          description:
            "'full' (default) returns all entries with descriptions. 'compact' returns title, URL, type, source, and tags only — useful for scanning before fetching specific entries with get_entry.",
        },
      },
    },
  },
];

function handleToolCall(name, args) {
  switch (name) {
    case "search_resources": {
      const { tags = [], tag_mode = "all", type, source, query, sort_by = "index", limit = 20, cursor, count_only = false } = args;
      const tagMode = tag_mode;
      const types = type ? [type] : [];
      const sources = source ? [source] : [];
      const offset = cursor || 0;
      const { results, total, limited, nextCursor } = filterEntries({ tags, tagMode, types, sources, query, sort_by, limit, offset });

      if (count_only) {
        return {
          content: [{
            type: "text",
            text: JSON.stringify({ total_matches: total }, null, 2),
          }],
        };
      }

      const response = { total_matches: total, showing: results.length, limited, entries: results.map(formatEntry) };
      if (nextCursor !== null) response.next_cursor = nextCursor;
      return {
        content: [{
          type: "text",
          text: JSON.stringify(response, null, 2),
        }],
      };
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

    case "get_full_index": {
      const fmt = args.format || "full";
      const lines = [
        `# Renaissance AI and Education Resource Hub — Full Index`,
        `> ${data.meta.total} entries | Updated: ${data.meta.last_updated}`,
        "",
      ];
      for (const e of data.entries) {
        if (fmt === "compact") {
          lines.push(`${e.num}. ${e.title} | ${e.type} | ${e.source} | ${e.tags.join(", ")} | ${e.url}`);
        } else {
          lines.push(`### ${e.num}. ${e.title}`);
          lines.push(`- URL: ${e.url}`);
          lines.push(`- Type: ${e.type} | Source: ${e.source}`);
          lines.push(`- Tags: ${e.tags.join(", ")}`);
          if (e.desc) lines.push(`\n${e.desc}`);
          lines.push("\n---\n");
        }
      }
      return { content: [{ type: "text", text: lines.join("\n") }] };
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

function processMcpMessage(msg) {
  const { method, id, params } = msg;

  if (id === undefined) return null;

  switch (method) {
    case "initialize":
      return jsonRpc(id, {
        protocolVersion: "2025-03-26",
        capabilities: { tools: {} },
        serverInfo: { name: "renaissance-hub", version: "2.0.0" },
      });
    case "tools/list":
      return jsonRpc(id, { tools: TOOL_DEFINITIONS });
    case "tools/call":
      return jsonRpc(id, handleToolCall(params.name, params.arguments || {}));
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

async function handleMcpPost(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return mcpResponse(jsonRpcError(null, -32700, "Parse error"), 400);
  }

  if (Array.isArray(body)) {
    const responses = body.map(processMcpMessage).filter((r) => r !== null);
    return responses.length === 0 ? mcpResponse(null, 202) : mcpResponse(responses);
  }

  const response = processMcpMessage(body);
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

Tools: search_resources, list_tags, list_sources, get_stats, get_entry, get_entries_batch, find_related, get_full_index

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
  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (url.pathname === "/mcp") {

      if (request.method === "POST") return handleMcpPost(request);
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
