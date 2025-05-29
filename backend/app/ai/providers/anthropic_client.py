import json
import time
import requests
from typing import Any, Dict
from ..client import BaseLLMClient, Complexity

_ANTHROPIC_MESSAGES_PATH = "/v1/messages"

_PROMPT_TEMPLATE = """You are a senior software engineer.
Analyze the following {language} code and respond STRICTLY as JSON with this shape:
{{
  "explanation": "clear, concise explanation",
  "complexity": {{"time": "O(...)", "space": "O(...)", "reasoning": "short why"}}
}}
Code:
---
{snippet}
---
Return ONLY JSON. No prose outside JSON.
"""


def _heuristic_complexity(snippet: str) -> Complexity:
    loops = snippet.count("for ") + snippet.count("while ")
    if loops >= 2:
        return Complexity("O(n^2)", "O(1)",
                          "Multiple loops; likely nested iteration.")
    if loops == 1:
        return Complexity("O(n)", "O(1)", "Single loop detected.")
    return Complexity("O(1)", "O(1)", "No obvious loops or recursion.")


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, base_url: str, api_version: str,
                 timeout_ms: int = 12000):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.timeout = timeout_ms / 1000.0
        # default model can be overridden by mapping name in registry call site
        self.model = "claude-3-haiku-20240307"

    def explain(self, language: str, snippet: str, want_tests: bool):
        url = self.base_url + _ANTHROPIC_MESSAGES_PATH
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 800,
            "temperature": 0.2,
            "messages": [
                {"role": "user",
                 "content": _PROMPT_TEMPLATE.format(language=language,
                                                    snippet=snippet)}
            ]
        }
        t0 = time.perf_counter()
        try:
            resp = requests.post(url, headers=headers, json=payload,
                                 timeout=self.timeout)
            if resp.status_code == 429:
                raise self.RateLimitedError("Anthropic rate limit")
            resp.raise_for_status()
            data = resp.json()
            content = ""
            blocks = data.get("content") or []
            if blocks and isinstance(blocks, list):
                # Take first text block
                content = (blocks[0].get("text") or "") if isinstance(blocks[0],
                                                                      dict) else str(
                    blocks[0])

            try:
                doc = json.loads(content)
                comp = doc.get("complexity") or {}
                return {
                    "explanation": doc.get("explanation", "") or "",
                    "complexity": {
                        "time": comp.get("time", "") or "",
                        "space": comp.get("space", "") or "",
                        "reasoning": comp.get("reasoning", "") or "",
                    },
                }
            except json.JSONDecodeError:
                c = _heuristic_complexity(snippet)
                return {
                    "explanation": content.strip() or "Anthropic response (unparsed).",
                    "complexity": {"time": c.time, "space": c.space,
                                   "reasoning": c.reasoning},
                }
        except requests.RequestException as e:
            raise RuntimeError(f"Anthropic HTTP error: {e}") from e
        finally:
            _ = int((time.perf_counter() - t0) * 1000)
