import { listModels, listSnippets, createSnippet, getSnippet, createRun, upsertFeedback } from "../src/api";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

beforeEach(() => { global.fetch = jest.fn(); });
afterEach(() => { jest.resetAllMocks(); });

test("listModels calls correct URL", async () => {
  fetch.mockResolvedValueOnce({ ok: true, text: async () => JSON.stringify([{ id: 1, name: "mock:demo" }]) });
  const data = await listModels();
  expect(fetch).toHaveBeenCalledWith(`${API}/v1/models/`, expect.any(Object));
  expect(data[0].name).toBe("mock:demo");
});

test("listSnippets uses limit param", async () => {
  fetch.mockResolvedValueOnce({ ok: true, text: async () => JSON.stringify([{ id: 123, language: "python" }]) });
  await listSnippets(20);
  expect(fetch).toHaveBeenCalledWith(`${API}/v1/snippets/?limit=20`, expect.any(Object));
});

test("createSnippet posts payload", async () => {
  const payload = { language: "python", code: "print(1)", options: { tests: true }, title: "t" };
  fetch.mockResolvedValueOnce({ ok: true, text: async () => JSON.stringify({ id: 10, ...payload, options_json: payload.options }) });
  await createSnippet(payload);
  const [url, opts] = fetch.mock.calls[0];
  expect(url).toBe(`${API}/v1/snippets/`);
  expect(opts.method).toBe("POST");
  expect(JSON.parse(opts.body).language).toBe("python");
});

test("getSnippet hits correct URL", async () => {
  fetch.mockResolvedValueOnce({ ok: true, text: async () => JSON.stringify({ id: 55, runs: [] }) });
  await getSnippet(55);
  expect(fetch).toHaveBeenCalledWith(`${API}/v1/snippets/55/`, expect.any(Object));
});

test("createRun posts IDs", async () => {
  fetch.mockResolvedValueOnce({ ok: true, text: async () => JSON.stringify({ id: 77, snippet: 1 }) });
  await createRun({ snippetId: 1, modelId: 2 });
  const [, opts] = fetch.mock.calls[0];
  const body = JSON.parse(opts.body);
  expect(body.snippetId).toBe(1);
  expect(body.modelId).toBe(2);
});

test("upsertFeedback posts run, score, comment", async () => {
  fetch.mockResolvedValueOnce({ ok: true, text: async () => JSON.stringify({ run: 5, score: 10, comment: "ok" }) });
  await upsertFeedback({ runId: 5, score: 10, comment: "ok" });
  const [, opts] = fetch.mock.calls[0];
  const body = JSON.parse(opts.body);
  expect(body.run).toBe(5);
  expect(body.score).toBe(10);
  expect(body.comment).toBe("ok");
});
