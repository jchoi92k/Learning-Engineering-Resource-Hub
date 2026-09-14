// Legacy-endpoint proxy for the old `le-resource-hub` deployment.
//
// The MCP worker moved to `renaissance-hub.joon-96a.workers.dev`. Some early
// agent configs still point at the old `le-resource-hub` hostname, which used
// to run an outdated copy of the worker (serverInfo 1.0.0). This shim forwards
// every request — method, body, headers preserved — to the current worker via
// a service binding, so the old URL transparently serves current data and
// never drifts again.
//
// Service binding (not a plain fetch to the workers.dev URL): worker-to-worker
// fetch over a public workers.dev URL is not supported by default. The binding
// is an internal, zero-latency link on the same account. See wrangler.toml.
export default {
  async fetch(request, env) {
    return env.HUB.fetch(request);
  },
};
