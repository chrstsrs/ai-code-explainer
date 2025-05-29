import React from "react";
import { createRoot } from "react-dom/client";

// Mock the API module used by App so no real network calls happen
jest.mock("../src/api", () => ({
  listModels: jest.fn().mockResolvedValue([{ id: 1, name: "mock:demo" }]),
  listSnippets: jest.fn().mockResolvedValue([]),
  createSnippet: jest.fn().mockResolvedValue({ id: 1, language: "python", code: "x=1", options_json: { tests: true }, title: "t1" }),
  getSnippet: jest.fn().mockResolvedValue({ id: 1, language: "python", code: "x=1", options_json: { tests: true }, title: "t1", runs: [] }),
  createRun: jest.fn().mockResolvedValue({ id: 99, snippet: 1 }),
  upsertFeedback: jest.fn().mockResolvedValue({ run: 99, score: 10 }),
}));

import App from "../src/App";

test("App renders without crashing", () => {
  const div = document.createElement("div");
  document.body.appendChild(div);
  const root = createRoot(div);
  expect(() => root.render(<App />)).not.toThrow();
  root.unmount();
});
