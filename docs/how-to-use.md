# How to Use the Resource Hub

This hub indexes evidence-based K-12 and higher education resources from 20+ curated sources. It does not host content — every entry links out to the original source. There are four ways to access it.

---

## 1. Web interface

[Browse, filter by tag/source/type, and full-text search.](https://jchoi92k.github.io/Learning-Engineering-Resource-Hub) No setup required. Data refreshes on every push to main.

## 2. LLM agent (llms.txt)

Agents that can follow links start from the root index:

```
https://jchoi92k.github.io/Learning-Engineering-Resource-Hub/llms.txt
```

It lists every source with a link to a compact per-source file (entry number, title, URL, type, tags; large sources are split into parts under 100,000 characters) and to a per-source file with full descriptions (`llms-full-<source>.txt`), plus the tag vocabulary.

To load everything at once — for example when pasting one URL into a chat assistant that cannot follow links — use the self-contained full file (all entries with descriptions, about 2 MB):

```
https://jchoi92k.github.io/Learning-Engineering-Resource-Hub/llms-full.txt
```

**Use cases:**
- Feed it to an agent as context for answering education research questions
- Build a RAG pipeline over the entries
- Use it as a grounding source for an education-focused chatbot

## 3. MCP server

Connect any MCP-compatible client (Claude Desktop, Cursor, Windsurf, custom agents) to:

```
https://renaissance-hub.joon-96a.workers.dev/mcp
```

Available tools: `search` and `fetch` (the search/fetch pair that ChatGPT deep research and company knowledge require: `search(query)` returns ids, titles and URLs; `fetch(id)` returns the entry with its description), plus `search_resources` (filters, pagination, counts), `get_entry`, `get_entries_batch`, `list_tags`, `list_sources`, `get_stats`, `find_related`.

The tool list changed on 2026-08-30: `get_full_index` was removed (the corpus outgrew a single response). If your client still shows it, reconnect so it refreshes its tool list; calling it returns an error that names the replacements.

**Client setup** — add to your MCP config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "renaissance-hub": {
      "type": "http",
      "url": "https://renaissance-hub.joon-96a.workers.dev/mcp"
    }
  }
}
```

Then ask Claude things like "search the resource hub for RCT studies on math tutoring."

## 4. Gemini Gem

[Chat-based access with no setup.](https://gemini.google.com/gem/1UCri-Go8-5nngceVAvtqFVkaHOC5sbkW?usp=sharing) The Gem searches the knowledge base first and cites entries directly. It can also supplement with web results on request.

Want to set up your own Gem? The instructions and knowledge file are in the repo:
- [`meta/gem-instructions.md`](../meta/gem-instructions.md) — system prompt (copy into the Gem's instruction field)
- [`docs/gem-knowledge.txt`](gem-knowledge.txt) — knowledge file (upload to the Gem)

---

## Working with the data

### data.json

Structured JSON with all entries, tag counts, and source metadata. If you want to build your own frontend or integration:

```
https://jchoi92k.github.io/Learning-Engineering-Resource-Hub/data.json
```

Each entry includes: `title`, `url`, `type`, `source`, `tags`, `description`, `date_added`.

### Tags as a discovery tool

Entries are tagged across four dimensions — use these to narrow searches:

- **Domain:** k-12, higher-ed, early-childhood, literacy, math-education, english-learners
- **Method:** rct, meta-analysis, longitudinal, genai, computer-assisted-learning
- **Topic:** formative-assessment, sel, professional-development, personalized-learning, open-datasets
- **Affiliation:** wwc, lpi, digital-promise, aims, campbell-collaboration

Full tag vocabulary in `schema.md`.

---

## Suggesting a source

Want a source or resource included? Open a [New source suggestion](https://github.com/jchoi92k/Learning-Engineering-Resource-Hub/issues/new?template=new-source.md) issue on GitHub.
