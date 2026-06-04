/**
 * MCP tool tests for renaissance-hub worker.
 * Run: start `npx wrangler dev --port 8787` then `node test-mcp.js`
 */
const BASE = "http://localhost:8787/mcp";
let passed = 0;
let failed = 0;
let sessionId = null;

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
  return res.json();
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
  assert(names.includes("get_full_index"), "has get_full_index");
  assert(names.length === 8, `tool count is 8 (got ${names.length})`);
});

await test("search_resources — basic keyword", async () => {
  const r = await callTool("search_resources", { query: "tutoring", limit: 5 });
  assert(r.total_matches > 0, `found matches (${r.total_matches})`);
  assert(r.entries.length <= 5, `respects limit (${r.entries.length})`);
  assert(r.entries[0].title !== undefined, "entries have titles");
  assert(r.entries[0].url !== undefined, "entries have URLs");
});

await test("search_resources — tag filter", async () => {
  const r = await callTool("search_resources", { tags: ["attendance"], limit: 5 });
  assert(r.total_matches > 0, `found attendance entries (${r.total_matches})`);
  for (const e of r.entries) {
    assert(e.tags.includes("attendance"), `entry ${e.num} has attendance tag`);
  }
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

// ── Summary ──
console.log(`\n${"=".repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
