import json
import time
import requests
from typing import Any, Dict
from ..client import BaseLLMClient, Complexity

_OPENAI_CHAT_PATH = "/chat/completions"

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

class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, base_url: str, timeout_ms: int = 12000):
      self.api_key = api_key
      self.base_url = base_url.rstrip("/")
      self.timeout = timeout_ms / 1000.0

    def explain(self, language: str, snippet: str, want_tests: bool):
      url = self.base_url + _OPENAI_CHAT_PATH
      model = "gpt-4o-mini"  # actual model is selected via LLMModel.name; prompt content is model-agnostic
      # Let caller set the exact model by prefix; we override via header param not available -> so we pass in body:
      payload = {
          "model": model,
          "messages": [
              {"role": "system", "content": "You return only strict JSON; never include backticks."},
              {"role": "user", "content": _PROMPT_TEMPLATE.format(language=language, snippet=snippet)}
          ],
          "temperature": 0.2,
      }
      headers = {
          "Authorization": f"Bearer {self.api_key}",
          "Content-Type": "application/json",
      }
      t0 = time.perf_counter()
      try:
          resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
          if resp.status_code == 429:
              raise self.RateLimitedError("OpenAI rate limit")
          resp.raise_for_status()
          data = resp.json()
          content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
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
              # fallback: heuristic
              c = _heuristic_complexity(snippet)
              return {
                  "explanation": content.strip() or "OpenAI response (unparsed).",
                  "complexity": {"time": c.time, "space": c.space, "reasoning": c.reasoning},
              }
      except requests.RequestException as e:
          raise RuntimeError(f"OpenAI HTTP error: {e}") from e
      finally:
          _ = int((time.perf_counter() - t0) * 1000)
