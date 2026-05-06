import rawData from "../data.json";
const data = typeof rawData === "string" ? JSON.parse(rawData) : rawData;

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, mcp-session-id",
};

// ── Data helpers (shared by HTTP API and MCP) ──

function filterEntries({ tags = [], tagMode = "all", types = [], sources = [], query = "", limit = 20 }) {
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

  const total = results.length;
  const capped = Math.min(limit, 100);
  results = results.slice(0, capped);
  return { results, total, limited: total > capped };
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

// ── MCP Protocol (Streamable HTTP) ──

const TOOL_DEFINITIONS = [
  {
    name: "search_resources",
    description:
      "Search the Learning Engineering Resource Hub — 569 curated evidence-based K-12 and higher education resources. Filter by tags, type, source, or keyword. Call list_tags first to see available filter values.",
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
        limit: {
          type: "number",
          description: "Maximum results to return (default 20, max 100)",
        },
      },
    },
  },
  {
    name: "list_tags",
    description:
      "List all available tags, types, and sources in the Learning Engineering Resource Hub with entry counts. Call this first to understand what filter values are available before searching.",
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
    name: "get_full_index",
    description:
      `Get the complete index of all ${data.entries.length} entries in the Learning Engineering Resource Hub. Returns every entry with metadata and descriptions. Use this when you need comprehensive coverage or want to reason over the full corpus. For targeted queries, use search_resources instead.`,
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
      const { tags = [], tag_mode = "all", type, source, query, limit = 20 } = args;
      const tagMode = tag_mode;
      const types = type ? [type] : [];
      const sources = source ? [source] : [];
      const { results, total, limited } = filterEntries({ tags, tagMode, types, sources, query, limit });
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              { total_matches: total, showing: results.length, limited, entries: results.map(formatEntry) },
              null,
              2,
            ),
          },
        ],
      };
    }

    case "list_tags": {
      const sorted = (obj) =>
        Object.entries(obj)
          .sort((a, b) => b[1] - a[1])
          .map(([k, v]) => `${k} (${v})`)
          .join(", ");
      return {
        content: [
          {
            type: "text",
            text: [
              `Learning Engineering Resource Hub — ${data.meta.total} entries, updated ${data.meta.last_updated}`,
              "",
              `Tags: ${sorted(getTagCounts())}`,
              "",
              `Types: ${sorted(getTypeCounts())}`,
              "",
              `Sources: ${sorted(getSourceCounts())}`,
            ].join("\n"),
          },
        ],
      };
    }

    case "get_entry": {
      const entry = data.entries.find((e) => e.num === args.num);
      if (!entry) {
        return { content: [{ type: "text", text: `No entry with number ${args.num}` }], isError: true };
      }
      return { content: [{ type: "text", text: JSON.stringify(formatEntry(entry), null, 2) }] };
    }

    case "get_full_index": {
      const fmt = args.format || "full";
      const lines = [
        `# Learning Engineering Resource Hub — Full Index`,
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

const SESSION_ID = `le-hub-${data.meta.last_updated}`;

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
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "le-resource-hub", version: "1.0.0" },
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
  lines.push("# Learning Engineering Resource Hub — Search Results");
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

  return `# Learning Engineering Resource Hub — API

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

Tools: search_resources, list_tags, get_entry, get_full_index

Add to your MCP config:
  { "type": "http", "url": "https://le-resource-hub.joon-96a.workers.dev/mcp" }

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
      return mcpResponse({ name: "le-resource-hub", version: "1.0.0", tools: TOOL_DEFINITIONS.map((t) => t.name) });
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
