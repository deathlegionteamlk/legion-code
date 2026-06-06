import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    priority: int = 0
    tokens: int = 0


class ContextEngine:
    def __init__(self, budget: int = 4096):
        self.budget = budget
        self.messages = []
        self.system_messages = []
        self._token_cache = {}

    def count_tokens(self, text: str) -> int:
        if text in self._token_cache:
            return self._token_cache[text]
        tokens = len(text) // 4 + len(re.findall(r'\b\w+\b', text)) // 2
        tokens = max(1, tokens)
        self._token_cache[text] = tokens
        return tokens

    def add_message(self, role: str, content: str, priority: int = 0):
        tokens = self.count_tokens(content)
        msg = Message(role=role, content=content, priority=priority, tokens=tokens)
        if role == "system":
            self.system_messages.append(msg)
        else:
            self.messages.append(msg)

    def total_tokens(self) -> int:
        return sum(m.tokens for m in self.system_messages) + sum(m.tokens for m in self.messages)

    def usage(self) -> dict:
        return {
            "budget": self.budget,
            "system_tokens": sum(m.tokens for m in self.system_messages),
            "message_tokens": sum(m.tokens for m in self.messages),
            "total_tokens": self.total_tokens(),
            "percent_used": (self.total_tokens() / self.budget * 100) if self.budget > 0 else 0,
            "message_count": len(self.messages),
        }

    def prune_to_fit(self) -> list:
        while self.total_tokens() > self.budget and len(self.messages) > 1:
            lowest = min(self.messages, key=lambda m: (m.priority, m.tokens))
            self.messages.remove(lowest)
        return self.messages

    def sliding_window(self, window_size: int = 10) -> list:
        if len(self.messages) <= window_size:
            return self.system_messages + self.messages
        return self.system_messages + self.messages[-window_size:]

    def summarize_oldest(self, ratio: float = 0.3) -> str:
        if len(self.messages) < 3:
            return ""
        keep_count = max(1, int(len(self.messages) * (1 - ratio)))
        old = self.messages[:-keep_count]
        summary_parts = []
        for m in old:
            text = m.content[:100].replace("\n", " ")
            summary_parts.append(f"[{m.role}] {text}")
        summary = "\n".join(summary_parts)
        self.messages = self.messages[-keep_count:]
        self.add_message("system", f"[Summarized earlier conversation]\n{summary}", priority=10)
        return summary

    def get_context(self) -> list:
        return [{"role": m.role, "content": m.content} for m in (self.system_messages + self.messages)]

    def get_budget(self) -> int:
        return self.budget

    def clear(self):
        self.messages = []
        self.system_messages = []
        self._token_cache.clear()