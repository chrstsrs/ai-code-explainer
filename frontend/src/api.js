const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

async function http(method, path, body) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* keep text if needed */ }
  if (!res.ok) {
    const msg = data?.error?.message || data?.detail || res.statusText;
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return data;
}

export async function listModels() {
  return http("GET", "/v1/models/");
}

export async function createSnippet({ language, code, options, title }) {
  return http("POST", "/v1/snippets/", { language, code, options_json: options ?? null, title: title ?? null });
}

export async function listSnippets(limit = 20) {
  const q = new URLSearchParams({ limit: String(limit) }).toString();
  return http("GET", `/v1/snippets/?${q}`);
}

export async function getSnippet(snippetId) {
  return http("GET", `/v1/snippets/${snippetId}/`);
}

export async function createRun({ snippetId, modelId }) {
  return http("POST", "/v1/runs/", { snippetId, modelId });
}

export async function upsertFeedback({ runId, score, comment }) {
  return http("POST", "/v1/feedback/", { run: runId, score, comment: comment ?? null });
}
