import json
import time
import requests
from typing import Optional
from ..client import BaseLLMClient, Complexity

# Non-streaming generate endpoint
_GEN_PATH = "/api/generate"

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
        return Complexity("O(n^2)", "O(1)", "Multiple loops; likely nested iteration.")
    if loops == 1:
        return Complexity("O(n)", "O(1)", "Single loop detected.")
    return Complexity("O(1)", "O(1)", "No obvious loops or recursion.")

class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str, timeout_ms: int = 12000, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_ms / 1000.0
        self.api_key = api_key
        # default model can be overridden by registry if desired
        self.model = "llama3:8b-instruct"

    def explain(self, language: str, snippet: str, want_tests: bool):
        url = self.base_url + _GEN_PATH
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "prompt": _PROMPT_TEMPLATE.format(language=language, snippet=snippet),
            "stream": False,
            "options": {"temperature": 0.2},
        }
        t0 = time.perf_counter()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code == 429:
                raise self.RateLimitedError("Ollama rate limit")
            resp.raise_for_status()
            data = resp.json()
            content = data.get("response", "") or ""
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
                    "explanation": content.strip() or "Ollama response (unparsed).",
                    "complexity": {"time": c.time, "space": c.space, "reasoning": c.reasoning},
                }
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama HTTP error: {e}") from e
        finally:
            _ = int((time.perf_counter() - t0) * 1000)
