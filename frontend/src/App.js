import React, { useEffect, useMemo, useState } from "react";
import {
  listModels,
  listSnippets,
  createSnippet,
  getSnippet,
  createRun,
  upsertFeedback,
} from "./api";

const box = { maxWidth: 980, margin: "2rem auto", fontFamily: "system-ui, Arial, sans-serif", lineHeight: 1.4 };
const row = { display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" };
const label = { fontWeight: 600 };
const btn = { padding: "0.55rem 0.9rem", border: "1px solid #222", borderRadius: 6, background: "#111", color: "white", cursor: "pointer" };
const btnGhost = { ...btn, background: "white", color: "#111", borderColor: "#999" };
const codebox = { width: "100%", minHeight: 180, fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace", fontSize: 14, padding: 10 };
const card = { border: "1px solid #e5e7eb", borderRadius: 10, padding: 16, background: "#fff" };
const tag = { display: "inline-block", padding: "2px 8px", border: "1px solid #ddd", borderRadius: 999, fontSize: 12, background: "#fafafa" };

export default function App() {
  // models & selection
  const [models, setModels] = useState([]);
  const [modelId, setModelId] = useState(null);

  // snippet form
  const [language, setLanguage] = useState("python");
  const [title, setTitle] = useState("");
  const [code, setCode] = useState(`def add(a, b):\n    return a + b`);
  const [snippetId, setSnippetId] = useState(null);

  // loaded snippet details (with runs)
  const [snippet, setSnippet] = useState(null);

  // recent snippets list
  const [recent, setRecent] = useState([]);

  // ui state
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // local feedback draft per runId
  const [draftScores, setDraftScores] = useState({});    // { [runId]: number }
  const [draftComments, setDraftComments] = useState({}); // { [runId]: string }
  const [savingFeedback, setSavingFeedback] = useState({}); // { [runId]: boolean }

  // fetch models + recent on mount
  useEffect(() => {
    (async () => {
      try {
        const m = await listModels();
        setModels(m);
        if (m.length > 0) setModelId(m[0].id);
      } catch (e) {
        setErr(String(e.message || e));
      }
    })();
    (async () => {
      try {
        const items = await listSnippets(20);
        setRecent(items);
      } catch {
        /* non-fatal */
      }
    })();
  }, []);

  // helper: reload snippet detail and sync feedback drafts
  const reloadSnippet = async (id) => {
    const data = await getSnippet(id);
    setSnippet(data);
    const ds = {};
    const dc = {};
    (data.runs || []).forEach((r) => {
      if (r.feedback) {
        ds[r.id] = r.feedback.score;
        dc[r.id] = r.feedback.comment || "";
      }
    });
    setDraftScores(ds);
    setDraftComments(dc);
  };

  // refresh recent list
  const refreshRecent = async () => {
    try {
      const items = await listSnippets(20);
      setRecent(items);
    } catch {
      /* ignore */
    }
  };

  // open a snippet from the recent list
  const openSnippet = async (id) => {
    setErr("");
    setSnippetId(id);
    try {
      const data = await getSnippet(id);
      setSnippet(data);
      // sync form with loaded snippet (handy when revisiting)
      setLanguage(data.language || "python");
      setTitle(data.title || "");
      setCode(data.code || "");
      // sync drafts
      const ds = {};
      const dc = {};
      (data.runs || []).forEach((r) => {
        if (r.feedback) {
          ds[r.id] = r.feedback.score;
          dc[r.id] = r.feedback.comment || "";
        }
      });
      setDraftScores(ds);
      setDraftComments(dc);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const onCreateSnippet = async () => {
    setErr("");
    setLoading(true);
    try {
      const created = await createSnippet({
        language,
        code,
        options: { tests: true },
        title: title || null,
      });
      setSnippetId(created.id);
      await reloadSnippet(created.id);
      await refreshRecent();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onRunModel = async () => {
    if (!snippetId || !modelId) return;
    setErr("");
    setLoading(true);
    try {
      await createRun({ snippetId, modelId });
      await reloadSnippet(snippetId);
      await refreshRecent();
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const onSaveFeedback = async (runId) => {
    const score = draftScores[runId];
    const comment = draftComments[runId] ?? null;
    if (typeof score !== "number" || score < -100 || score > 100) {
      setErr("Score must be in [-100, 100].");
      return;
    }
    setSavingFeedback((s) => ({ ...s, [runId]: true }));
    setErr("");
    try {
      await upsertFeedback({ runId, score, comment });
      await reloadSnippet(snippetId);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setSavingFeedback((s) => ({ ...s, [runId]: false }));
    }
  };

  const selectedModel = useMemo(
    () => models.find((m) => m.id === modelId) || null,
    [models, modelId]
  );

  return (
    <div style={box}>
      <h1 style={{ marginBottom: 4 }}>AI Code Explainer & Evaluator</h1>
      <p style={{ color: "#555", marginTop: 0 }}>
        Send your code to a selected LLM, see explanation + complexity, then score it in <b>[-100, 100]</b>.
      </p>

      {err && (
        <div
          style={{
            ...card,
            borderColor: "#fecaca",
            background: "#fff1f2",
            color: "#7f1d1d",
            marginBottom: 16,
          }}
        >
          <strong>Error:</strong> {err}
        </div>
      )}

      {/* Create snippet */}
      <section style={{ ...card, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>1) Create or Update Snippet</h2>
        <div style={row}>
          <div>
            <span style={label}>Language:</span>{" "}
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="python">python</option>
              <option value="javascript">javascript</option>
            </select>
          </div>
          <div>
            <span style={label}>Title:</span>{" "}
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="optional"
            />
          </div>
          {snippetId && <div><span style={tag}>Snippet ID: {snippetId}</span></div>}
        </div>
        <textarea
          style={codebox}
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />
        <div style={{ display: "flex", gap: 8 }}>
          <button style={btn} onClick={onCreateSnippet} disabled={loading}>
            {snippetId ? "Save Changes" : "Create Snippet"}
          </button>
          {snippetId && (
            <button
              style={btnGhost}
              onClick={() => reloadSnippet(snippetId)}
              disabled={loading}
            >
              Reload History
            </button>
          )}
        </div>
      </section>

      {/* Select model & run */}
      <section style={{ ...card, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>2) Choose Model & Run</h2>
        <div style={row}>
          <div>
            <span style={label}>Model:</span>{" "}
            <select
              value={modelId || ""}
              onChange={(e) => setModelId(Number(e.target.value))}
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          {selectedModel && <span style={tag}>Active</span>}
        </div>
        <div style={{ marginTop: 8 }}>
          <button
            style={btn}
            onClick={onRunModel}
            disabled={!snippetId || !modelId || loading}
          >
            Run Selected Model
          </button>
        </div>
      </section>

      {/* Recent Snippets */}
      <section style={{ ...card, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>Recent Snippets</h2>
        {recent.length === 0 ? (
          <p style={{ color: "#666" }}>No snippets yet.</p>
        ) : (
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              display: "grid",
              gap: 8,
            }}
          >
            {recent.map((s) => (
              <li
                key={s.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  border: "1px solid #eee",
                  borderRadius: 8,
                  padding: "8px 12px",
                }}
              >
                <div>
                  <span style={{ ...tag, marginRight: 8 }}>#{s.id}</span>
                  <strong>{s.title || "(untitled)"}</strong>
                  <span style={{ ...tag, marginLeft: 8 }}>{s.language}</span>
                </div>
                <button style={btnGhost} onClick={() => openSnippet(s.id)}>
                  Open
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Runs & Scoring */}
      <section style={{ ...card }}>
        <h2 style={{ marginTop: 0 }}>3) Runs & Scoring</h2>
        {!snippet ? (
          <p style={{ color: "#666" }}>Create or open a snippet to see runs here.</p>
        ) : (
          <>
            {snippet.runs && snippet.runs.length > 0 ? (
              <div style={{ display: "grid", gap: 12 }}>
                {snippet.runs.map((run) => (
                  <div key={run.id} style={{ ...card, borderColor: "#ddd" }}>
                    <div style={{ ...row, justifyContent: "space-between" }}>
                      <div>
                        <span style={label}>Model:</span> {run.model?.name || "—"}{" "}
                        <span style={{ ...tag, marginLeft: 8 }}>Run #{run.id}</span>
                      </div>
                      <div>
                        <span
                          style={{
                            ...tag,
                            background: statusColor(run.status).bg,
                            borderColor: statusColor(run.status).bd,
                          }}
                        >
                          {run.status.toUpperCase()}
                        </span>
                        {typeof run.latency_ms === "number" && (
                          <span style={{ ...tag, marginLeft: 8 }}>
                            {run.latency_ms} ms
                          </span>
                        )}
                      </div>
                    </div>

                    {run.status === "ok" ? (
                      <>
                        <details open style={{ marginTop: 8 }}>
                          <summary style={{ cursor: "pointer" }}>
                            <b>Explanation</b>
                          </summary>
                          <pre style={{ whiteSpace: "pre-wrap" }}>
                            {run.response_text || "—"}
                          </pre>
                        </details>

                        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                          <div>
                            <span style={label}>Time:</span>{" "}
                            {run.complexity_time || "—"}
                          </div>
                          <div>
                            <span style={label}>Space:</span>{" "}
                            {run.complexity_space || "—"}
                          </div>
                          <div>
                            <span style={label}>Reasoning:</span>{" "}
                            {run.complexity_reasoning || "—"}
                          </div>
                        </div>

                        {/* Feedback */}
                        <div
                          style={{
                            marginTop: 12,
                            borderTop: "1px dashed #eee",
                            paddingTop: 12,
                          }}
                        >
                          <div style={{ ...row, alignItems: "stretch" }}>
                            <div style={{ flex: "1 1 280px" }}>
                              <div style={{ display: "flex", justifyContent: "space-between" }}>
                                <span style={label}>Score [-100, 100]</span>
                                <span style={{ fontVariantNumeric: "tabular-nums" }}>
                                  {draftScores[run.id] ?? (run.feedback?.score ?? 0)}
                                </span>
                              </div>
                              <input
                                type="range"
                                min={-100}
                                max={100}
                                step={5}
                                value={draftScores[run.id] ?? (run.feedback?.score ?? 0)}
                                onChange={(e) =>
                                  setDraftScores((s) => ({
                                    ...s,
                                    [run.id]: Number(e.target.value),
                                  }))
                                }
                                style={{ width: "100%" }}
                              />
                            </div>
                            <div style={{ flex: "1 1 280px" }}>
                              <textarea
                                placeholder="Optional comment"
                                value={draftComments[run.id] ?? (run.feedback?.comment ?? "")}
                                onChange={(e) =>
                                  setDraftComments((s) => ({
                                    ...s,
                                    [run.id]: e.target.value,
                                  }))
                                }
                                style={{ width: "100%", minHeight: 60 }}
                              />
                            </div>
                            <div style={{ alignSelf: "flex-end" }}>
                              <button
                                style={btn}
                                onClick={() => onSaveFeedback(run.id)}
                                disabled={!!savingFeedback[run.id]}
                              >
                                {savingFeedback[run.id]
                                  ? "Saving..."
                                  : run.feedback
                                  ? "Update Score"
                                  : "Save Score"}
                              </button>
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div style={{ marginTop: 8 }}>
                        {run.error_code && (
                          <div>
                            <b>Error:</b> {run.error_code}
                          </div>
                        )}
                        {run.error_message && (
                          <pre style={{ whiteSpace: "pre-wrap" }}>
                            {run.error_message}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "#666" }}>
                No runs yet. Pick a model and click “Run Selected Model”.
              </p>
            )}
          </>
        )}
      </section>

      <footer style={{ color: "#777", marginTop: 16, fontSize: 13 }}>
        API base:{" "}
        <code>{process.env.REACT_APP_API_URL || "http://localhost:8000/api"}</code>
      </footer>
    </div>
  );
}

function statusColor(status) {
  switch ((status || "").toLowerCase()) {
    case "ok":
      return { bg: "#ecfdf5", bd: "#d1fae5" };
    case "timeout":
      return { bg: "#fffbeb", bd: "#fde68a" };
    case "rate_limited":
      return { bg: "#eff6ff", bd: "#bfdbfe" };
    case "error":
    default:
      return { bg: "#fef2f2", bd: "#fecaca" };
  }
}
