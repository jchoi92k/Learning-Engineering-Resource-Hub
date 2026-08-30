/**
 * MCP tool tests for renaissance-hub worker.
 *
 * Run: node test-mcp.mjs
 * Spawns `wrangler dev` itself and polls until ready — no manual server start,
 * no bash-only chaining, works on Windows and POSIX alike.
 * To test against an already-running server: node test-mcp.mjs --no-spawn
 */
import { spawn } from "node:child_process";
import process from "node:process";

const PORT = 8787;
const ORIGIN = `http://localhost:${PORT}`;
const BASE = `${ORIGIN}/mcp`;
let passed = 0;
let failed = 0;
let sessionId = null;
let server = null;
// Every tool response must stay well inside a model's context: 100,000
// characters is roughly the 25k-token cap Claude Code applies to tool results.
const MAX_RESPONSE_CHARS = 100_000;
let largestResponse = { chars: 0, tool: null };

async function startServer() {
  if (process.argv.includes("--no-spawn")) return;
  server = spawn("npx", ["wrangler", "dev", "--port", String(PORT)], {
    cwd: import.meta.dirname,
    shell: process.platform === "win32",
    stdio: "ignore",
  });
  // Poll readiness for up to 60s instead of a fixed sleep.
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(ORIGIN, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return;
    } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error("wrangler dev did not become ready within 60s");
}

function stopServer() {
  if (server) server.kill();
}

async function rpc(method, params = {}, id = 1) {
  const res = await fetch(BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(sessionId ? { "Mcp-Session-Id": sessionId } : {}),
    },
    body: JSON.stringify({ jsonrpc: "2.0", method, params, id }),
  });
  if (!sessionId) sessionId = res.headers.get("Mcp-Session-Id");
  const json = await res.json();
  if (method === "tools/call" && json.result) {
    const chars = JSON.stringify(json.result).length;
    if (chars > largestResponse.chars) largestResponse = { chars, tool: params.name };
  }
  return json;
}

async function callTool(name, args = {}) {
  const res = await rpc("tools/call", { name, arguments: args });
  if (res.error) throw new Error(`RPC error: ${res.error.message}`);
  const text = res.result.content[0].text;
  try { return JSON.parse(text); } catch { return text; }
}

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

async function test(name, fn) {
  console.log(`\n[${name}]`);
  try { await fn(); }
  catch (e) { failed++; console.error(`  ERROR: ${e.message}`); }
}

// ── Tests ──

await startServer();

try {

await test("initialize", async () => {
  const res = await rpc("initialize", { protocolVersion: "2025-03-26", capabilities: {}, clientInfo: { name: "test", version: "1.0" } });
  assert(res.result.serverInfo.name === "renaissance-hub", "server name is renaissance-hub");
  assert(res.result.serverInfo.version === "2.0.0", "version is 2.0.0");
});

await test("tools/list", async () => {
  const res = await rpc("tools/list");
  const names = res.result.tools.map(t => t.name);
  assert(names.includes("search_resources"), "has search_resources");
  assert(names.includes("list_tags"), "has list_tags");
  assert(names.includes("list_sources"), "has list_sources");
  assert(names.includes("get_stats"), "has get_stats");
  assert(names.includes("get_entry"), "has get_entry");
  assert(names.includes("get_entries_batch"), "has get_entries_batch");
  assert(names.includes("find_related"), "has find_related");
  assert(names.includes("search"), "has search");
  assert(names.includes("fetch"), "has fetch");
  assert(!names.includes("get_full_index"), "get_full_index is gone");
  assert(names.length === 9, `tool count is 9 (got ${names.length})`);
  const fetchTool = res.result.tools.find(t => t.name === "fetch");
  assert(fetchTool.outputSchema && fetchTool.outputSchema.required.includes("text"), "fetch declares an outputSchema with text");
  const search = res.result.tools.find(t => t.name === "search_resources");
  const typeEnum = search.inputSchema.properties.type.enum;
  assert(typeEnum.includes("review"), "type enum includes review");
  assert(typeEnum.includes("article"), "type enum includes article");
});

await test("search_resources — basic query", async () => {
  const r = await callTool("search_resources", { query: "tutoring", limit: 5 });
  assert(r.total_matches > 0, `found matches (${r.total_matches})`);
  assert(r.entries.length <= 5, `respects limit (${r.entries.length})`);
  assert(r.entries[0].title !== undefined, "entries have titles");
  assert(r.entries[0].url !== undefined, "entries have URLs");
  assert(["semantic", "keyword"].includes(r.search_mode), `reports search_mode (${r.search_mode})`);
});

await test("search_resources — explicit keyword mode", async () => {
  const r = await callTool("search_resources", { query: "tutoring", search_mode: "keyword", limit: 5 });
  assert(r.search_mode === "keyword", "keyword mode honored");
  assert(r.total_matches > 0, `keyword matching still works (${r.total_matches})`);
});

await test("search_resources — semantic falls back gracefully when index empty", async () => {
  // In local dev the Vectorize simulator starts empty, so semantic search
  // must fall back to keyword rather than returning nothing.
  const r = await callTool("search_resources", { query: "tutoring", search_mode: "semantic", limit: 5 });
  assert(r.total_matches > 0, `results despite index state (${r.total_matches}, mode=${r.search_mode})`);
});

await test("search_resources — tag filter", async () => {
  const r = await callTool("search_resources", { tags: ["attendance"], limit: 5 });
  assert(r.total_matches > 0, `found attendance entries (${r.total_matches})`);
  for (const e of r.entries) {
    assert(e.tags.includes("attendance"), `entry ${e.num} has attendance tag`);
  }
});

await test("search_resources — tag_mode any vs all", async () => {
  const all = await callTool("search_resources", { tags: ["literacy", "rct"], tag_mode: "all", count_only: true });
  const any = await callTool("search_resources", { tags: ["literacy", "rct"], tag_mode: "any", count_only: true });
  assert(any.total_matches >= all.total_matches, `any (${any.total_matches}) >= all (${all.total_matches})`);
});

await test("search_resources — type filter reaches minority types", async () => {
  const r = await callTool("search_resources", { type: "review", count_only: true });
  assert(r.total_matches > 0, `review entries reachable via type filter (${r.total_matches})`);
});

await test("search_resources — count_only", async () => {
  const r = await callTool("search_resources", { tags: ["literacy"], count_only: true });
  assert(r.total_matches > 0, `counted literacy entries (${r.total_matches})`);
  assert(r.entries === undefined, "no entries returned when count_only=true");
});

await test("search_resources — sort_by title", async () => {
  const r = await callTool("search_resources", { tags: ["math-education"], sort_by: "title", limit: 10 });
  assert(r.entries.length > 1, "has multiple results");
  const titles = r.entries.map(e => e.title);
  const sorted = [...titles].sort((a, b) => a.localeCompare(b));
  assert(JSON.stringify(titles) === JSON.stringify(sorted), "entries are sorted by title");
});

await test("search_resources — pagination via cursor", async () => {
  const page1 = await callTool("search_resources", { tags: ["literacy"], limit: 5 });
  assert(page1.total_matches > 5, `more than 5 literacy entries (${page1.total_matches})`);
  assert(page1.next_cursor !== undefined, `page 1 has next_cursor (${page1.next_cursor})`);

  const page2 = await callTool("search_resources", { tags: ["literacy"], limit: 5, cursor: page1.next_cursor });
  assert(page2.entries.length > 0, "page 2 has entries");
  assert(page2.entries[0].num !== page1.entries[0].num, "page 2 entries differ from page 1");
});

await test("list_tags", async () => {
  const r = await callTool("list_tags");
  assert(r.total_entries > 0, `has total_entries (${r.total_entries})`);
  assert(Array.isArray(r.tags), "tags is an array");
  assert(r.tags[0].name !== undefined, "tag items have name");
  assert(r.tags[0].count > 0, "tag items have count");
  assert(Array.isArray(r.types), "types is an array");
});

await test("list_sources", async () => {
  const r = await callTool("list_sources");
  assert(r.total_entries > 0, `has total_entries (${r.total_entries})`);
  assert(Array.isArray(r.sources), "sources is an array");
  assert(r.sources[0].name !== undefined, "source items have name");
  assert(r.sources[0].count > 0, "source items have count");
  const names = r.sources.map(s => s.name);
  assert(names.includes("What Works Clearinghouse"), "includes WWC");
  assert(names.includes("Mathematica"), "includes Mathematica");
});

await test("get_stats", async () => {
  const r = await callTool("get_stats");
  assert(r.total_entries > 2000, `total entries > 2000 (${r.total_entries})`);
  assert(r.last_updated !== undefined, "has last_updated");
  assert(r.sources !== undefined, "has sources breakdown");
  assert(r.types !== undefined, "has types breakdown");
  assert(Array.isArray(r.top_tags), "has top_tags array");
  assert(r.top_tags.length === 15, `top_tags has 15 items (${r.top_tags.length})`);
});

await test("get_entry — valid", async () => {
  const r = await callTool("get_entry", { num: 1 });
  assert(r.num === 1, "returned entry 1");
  assert(r.title !== undefined, "has title");
  assert(r.url !== undefined, "has url");
  assert(r.description !== undefined, "has description");
});

await test("get_entry — invalid", async () => {
  const res = await rpc("tools/call", { name: "get_entry", arguments: { num: 999999 } });
  assert(res.result.isError === true, "returns isError for missing entry");
});

await test("get_entries_batch", async () => {
  const r = await callTool("get_entries_batch", { nums: [1, 2, 3, 999999] });
  assert(r.found === 3, `found 3 of 4 (${r.found})`);
  assert(r.entries.length === 3, "3 entries returned");
  assert(r.missing.length === 1, "1 missing entry");
  assert(r.missing[0] === 999999, "missing entry is 999999");
});

await test("get_entries_batch — max 50 cap", async () => {
  const bigList = Array.from({ length: 60 }, (_, i) => i + 1);
  const r = await callTool("get_entries_batch", { nums: bigList });
  assert(r.found <= 50, `capped at 50 (${r.found})`);
});

await test("find_related", async () => {
  const r = await callTool("find_related", { num: 1, limit: 5 });
  assert(r.entry === 1, "reports for entry 1");
  assert(r.related_count > 0, `found related entries (${r.related_count})`);
  assert(r.related_count <= 5, "respects limit");
  assert(r.related[0].shared_tags !== undefined, "has shared_tags");
  assert(r.related[0].overlap > 0, "has overlap count");
  assert(r.related[0].num !== 1, "doesn't include the source entry");
});

await test("find_related — invalid entry", async () => {
  const res = await rpc("tools/call", { name: "find_related", arguments: { num: 999999 } });
  assert(res.result.isError === true, "returns isError for missing entry");
});

await test("error handling — tools/call without params", async () => {
  const res = await rpc("tools/call");
  assert(res.error !== undefined, "returns JSON-RPC error, not a crash");
  assert(res.error.code === -32602, `error code is -32602 (${res.error?.code})`);
});

await test("error handling — bad argument type returns isError tool result", async () => {
  // tags must be an array; a string makes the handler throw, which per
  // MCP SEP-1303 must surface as a tool execution error, not a protocol error
  const res = await rpc("tools/call", { name: "search_resources", arguments: { tags: "literacy" } });
  assert(res.error === undefined, "no protocol-level error");
  assert(res.result.isError === true, "isError tool result");
  assert(res.result.content[0].text.includes("search_resources"), "message names the tool");
});

await test("protocol version negotiation", async () => {
  const known = await rpc("initialize", { protocolVersion: "2025-03-26", capabilities: {}, clientInfo: { name: "t", version: "1" } });
  assert(known.result.protocolVersion === "2025-03-26", "echoes supported requested version");
  const unknown = await rpc("initialize", { protocolVersion: "1999-01-01", capabilities: {}, clientInfo: { name: "t", version: "1" } });
  assert(unknown.result.protocolVersion === "2025-06-18", `falls back to latest supported (${unknown.result.protocolVersion})`);
});

await test("invalid Origin rejected with 403", async () => {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Origin": "file://evil" },
    body: JSON.stringify({ jsonrpc: "2.0", method: "ping", id: 1 }),
  });
  assert(res.status === 403, `403 for non-http(s) Origin (${res.status})`);
  const ok = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Origin": "https://claude.ai" },
    body: JSON.stringify({ jsonrpc: "2.0", method: "ping", id: 1 }),
  });
  assert(ok.status === 200, `https Origin passes (${ok.status})`);
});

await test("error handling — unknown method", async () => {
  const res = await rpc("no/such/method");
  assert(res.error !== undefined, "returns JSON-RPC error");
  assert(res.error.code === -32601, `error code is -32601 (${res.error?.code})`);
});

await test("search — id/title/url results", async () => {
  const r = await callTool("search", { query: "tutoring" });
  assert(Array.isArray(r.results) && r.results.length > 0, `results array (${r.results?.length})`);
  const first = r.results[0];
  assert(typeof first.id === "string" && typeof first.title === "string" && typeof first.url === "string", "result has string id, title, url");
  assert(Object.keys(first).length === 3, "result carries only id, title, url");
  assert(r.results.length <= 20, `at most 20 results (${r.results.length})`);
});

await test("search — structuredContent mirrors the text block", async () => {
  const res = await rpc("tools/call", { name: "search", arguments: { query: "tutoring" } });
  assert(res.result.structuredContent && Array.isArray(res.result.structuredContent.results), "structuredContent.results present");
  assert(JSON.stringify(res.result.structuredContent) === JSON.stringify(JSON.parse(res.result.content[0].text)), "structuredContent equals the text block");
});

await test("search — empty query is a tool error", async () => {
  const res = await rpc("tools/call", { name: "search", arguments: { query: "   " } });
  assert(res.result.isError === true, "isError for empty query");
});

await test("fetch — full entry by id", async () => {
  const s = await callTool("search", { query: "tutoring" });
  const id = s.results[0].id;
  const r = await callTool("fetch", { id });
  assert(r.id === id, "same id back");
  assert(typeof r.text === "string" && r.text.length >= 30, `text is the description (${r.text?.length} chars)`);
  assert(typeof r.url === "string" && r.url.startsWith("http"), "url present");
  assert(r.metadata && typeof r.metadata.source === "string" && Array.isArray(r.metadata.tags), "metadata has source and tags");
});

await test("fetch — unknown id is a tool error", async () => {
  const res = await rpc("tools/call", { name: "fetch", arguments: { id: "999999" } });
  assert(res.result.isError === true, "isError for unknown id");
});

await test("search_resources — structuredContent present", async () => {
  const res = await rpc("tools/call", { name: "search_resources", arguments: { query: "tutoring", limit: 3 } });
  assert(res.result.structuredContent && Array.isArray(res.result.structuredContent.entries), "structuredContent.entries present");
});

await test("get_full_index — removed", async () => {
  const res = await rpc("tools/call", { name: "get_full_index", arguments: {} });
  assert(res.error !== undefined || res.result?.isError === true, "calling the removed tool is an error, not a dump");
  const text = res.result?.content?.[0]?.text || res.error?.message || "";
  assert(text.includes("search(query)") && text.includes("fetch(id)"), "the error names the replacement tools");
  assert(text.includes("reconnect"), "the error tells a stale client to reconnect");
  assert(text.includes("search_resources"), "the error lists the current tools");
});

await test("unknown tool — lists current tools", async () => {
  const res = await rpc("tools/call", { name: "no_such_tool", arguments: {} });
  assert(res.result?.isError === true, "unknown tool is an isError result");
  const text = res.result?.content?.[0]?.text || "";
  assert(text.includes("Unknown tool: no_such_tool") && text.includes("Available tools:"), "names the tool and lists the current ones");
  assert(!text.includes("get_full_index was removed"), "the removal hint is specific to get_full_index");
});

await test("HTTP /search endpoint", async () => {
  const res = await fetch(`${ORIGIN}/search?q=tutoring&limit=5`);
  assert(res.ok, `/search returns 200 (${res.status})`);
  const body = await res.text();
  assert(body.includes("Search Results"), "returns markdown results");
});

await test("HTTP / help page", async () => {
  const res = await fetch(ORIGIN);
  assert(res.ok, `/ returns 200 (${res.status})`);
  const body = await res.text();
  assert(body.includes("MCP"), "help page mentions MCP");
});

await test("response size — every tool response stayed under the cap", async () => {
  assert(largestResponse.chars > 0, "at least one tool response was measured");
  assert(largestResponse.chars < MAX_RESPONSE_CHARS, `largest response ${largestResponse.chars} chars from ${largestResponse.tool} (cap ${MAX_RESPONSE_CHARS})`);
});

} finally {
  stopServer();
}

// ── Summary ──
console.log(`\n${"=".repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
