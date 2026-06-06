import time
from dataclasses import dataclass, field


MODEL_PRICING = {
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free": {"input": 0.0, "output": 0.0, "input_cache": 0.0},
    "cognitivecomputations/dolphin-mixtral-8x22b": {"input": 0.90, "output": 0.90, "input_cache": 0.0},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00, "input_cache": 1.25},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60, "input_cache": 0.075},
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00, "input_cache": 0.30},
    "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25, "input_cache": 0.03},
    "meta-llama/llama-3.1-70b": {"input": 0.59, "output": 0.79, "input_cache": 0.0},
    "meta-llama/llama-3.1-8b": {"input": 0.07, "output": 0.29, "input_cache": 0.0},
    "google/gemini-pro-1.5": {"input": 1.25, "output": 5.00, "input_cache": 0.0},
    "mistralai/mistral-large": {"input": 2.00, "output": 6.00, "input_cache": 0.0},
}


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


class CostTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.session_usage = TokenUsage()
        self.total_usage = TokenUsage()
        self.model_usage = {}
        self.session_cost = 0.0
        self._initialized = True

    def record_usage(self, model: str, input_tokens: int = 0, output_tokens: int = 0, cache_read: int = 0, cache_write: int = 0):
        self.session_usage.input_tokens += input_tokens
        self.session_usage.output_tokens += output_tokens
        self.session_usage.cache_read_tokens += cache_read
        self.session_usage.cache_write_tokens += cache_write
        self.total_usage.input_tokens += input_tokens
        self.total_usage.output_tokens += output_tokens
        self.total_usage.cache_read_tokens += cache_read
        self.total_usage.cache_write_tokens += cache_write
        if model not in self.model_usage:
            self.model_usage[model] = TokenUsage()
        self.model_usage[model].input_tokens += input_tokens
        self.model_usage[model].output_tokens += output_tokens
        self.model_usage[model].cache_read_tokens += cache_read
        self.model_usage[model].cache_write_tokens += cache_write
        cost = self._calculate_cost(model, input_tokens, output_tokens, cache_read, cache_write)
        self.session_cost += cost
        return cost

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int, cache_read: int = 0, cache_write: int = 0) -> float:
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 2.0, "input_cache": 0.5})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        cache_cost = (cache_read / 1_000_000) * pricing.get("input_cache", pricing["input"] * 0.5)
        return input_cost + output_cost + cache_cost

    def get_session_summary(self) -> dict:
        return {
            "input_tokens": self.session_usage.input_tokens,
            "output_tokens": self.session_usage.output_tokens,
            "cache_read_tokens": self.session_usage.cache_read_tokens,
            "cache_write_tokens": self.session_usage.cache_write_tokens,
            "total_tokens": self.session_usage.input_tokens + self.session_usage.output_tokens + self.session_usage.cache_read_tokens,
            "estimated_cost": round(self.session_cost, 6),
            "model_breakdown": {m: {"input": u.input_tokens, "output": u.output_tokens} for m, u in self.model_usage.items()},
        }

    def format_cost_table(self) -> str:
        summary = self.get_session_summary()
        lines = []
        lines.append("Session Cost Summary")
        lines.append(f"  Input tokens: {summary['input_tokens']:,}")
        lines.append(f"  Output tokens: {summary['output_tokens']:,}")
        lines.append(f"  Cache tokens: {summary['cache_read_tokens']:,}")
        lines.append(f"  Total tokens: {summary['total_tokens']:,}")
        lines.append(f"  Estimated cost: ${summary['estimated_cost']:.6f}")
        if summary["model_breakdown"]:
            lines.append("  By model:")
            for m, u in summary["model_breakdown"].items():
                lines.append(f"    {m}: {u['input']:,} in / {u['output']:,} out")
        return "\n".join(lines)

    def reset_session(self):
        self.session_usage = TokenUsage()
        self.session_cost = 0.0
        self.model_usage = {}

    def to_dict(self) -> dict:
        return {
            "session_usage": {
                "input_tokens": self.session_usage.input_tokens,
                "output_tokens": self.session_usage.output_tokens,
                "cache_read_tokens": self.session_usage.cache_read_tokens,
            },
            "session_cost": self.session_cost,
            "model_usage": {m: {"input": u.input_tokens, "output": u.output_tokens} for m, u in self.model_usage.items()},
        }

    def from_dict(self, data: dict):
        if not data:
            return
        self.session_usage.input_tokens = data.get("session_usage", {}).get("input_tokens", 0)
        self.session_usage.output_tokens = data.get("session_usage", {}).get("output_tokens", 0)
        self.session_usage.cache_read_tokens = data.get("session_usage", {}).get("cache_read_tokens", 0)
        self.session_cost = data.get("session_cost", 0.0)
        for m, u in data.get("model_usage", {}).items():
            self.model_usage[m] = TokenUsage(input_tokens=u.get("input", 0), output_tokens=u.get("output", 0))