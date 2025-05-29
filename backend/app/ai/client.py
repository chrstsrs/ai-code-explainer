# backend/app/ai/client.py
from dataclasses import dataclass


@dataclass
class Complexity:
    time: str
    space: str
    reasoning: str


class BaseLLMClient:
    class RateLimitedError(Exception):
        pass

    def explain(self, language: str, snippet: str, want_tests: bool):
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    Deterministic, no-key client that "analyzes" code with simple heuristics.
    Produces fields required by the API without external calls.
    """

    def explain(self, language: str, snippet: str, want_tests: bool):
        loops = snippet.count("for ") + snippet.count("while ")
        recursion = any(tok in snippet for tok in ["def ", "function "]) and ("(" in snippet and ")" in snippet and snippet.split("(")[0].strip() in snippet)

        if loops >= 2:
            time_c = "O(n^2)"
            reason = "Multiple loops; likely nested iteration."
        elif loops == 1:
            time_c = "O(n)"
            reason = "Single loop detected."
        elif recursion:
            time_c = "O(n)"
            reason = "Possible recursion."
        else:
            time_c = "O(1)"
            reason = "No obvious loops or recursion."

        comp = Complexity(time=time_c, space="O(1)", reasoning=reason)

        return {
            "explanation": f"Mock analysis of {language} code. Heuristic Big-O guess included.",
            "complexity": comp.__dict__,
        }
