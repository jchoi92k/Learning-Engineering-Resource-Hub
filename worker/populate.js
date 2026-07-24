/**
 * Local-dev-only helper for populating the Vectorize index without a REST
 * API token. Run with remote bindings under wrangler's OAuth session:
 *
 *   npx wrangler dev --remote --config populate.toml --port 8788
 *
 * then drive it with: python scripts/embed_corpus.py --endpoint http://localhost:8788
 *
 * Never deployed — populate.toml exists only for `wrangler dev`.
 */
const MODEL = "@cf/baai/bge-base-en-v1.5";

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("POST only", { status: 405 });
    let body;
    try {
      body = await request.json();
    } catch {
      return Response.json({ ok: false, error: "invalid JSON" }, { status: 400 });
    }

    try {
      if (body.deleteIds && body.deleteIds.length) {
        const res = await env.VECTORIZE.deleteByIds(body.deleteIds);
        return Response.json({ ok: true, deleted: body.deleteIds.length, mutationId: res && res.mutationId });
      }
      const items = body.items || [];
      if (!items.length) return Response.json({ ok: false, error: "no items" }, { status: 400 });
      const emb = await env.AI.run(MODEL, { text: items.map((i) => i.text) });
      const vectors = items.map((it, i) => ({
        id: String(it.num),
        values: emb.data[i],
        metadata: { num: it.num },
      }));
      const res = await env.VECTORIZE.upsert(vectors);
      return Response.json({ ok: true, upserted: vectors.length, mutationId: res && res.mutationId });
    } catch (err) {
      return Response.json({ ok: false, error: err.message }, { status: 500 });
    }
  },
};
