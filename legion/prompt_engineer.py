import re
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PromptTemplate:
    name: str
    template: str
    variables: list = field(default_factory=list)
    description: str = ""

    def render(self, **kwargs) -> str:
        result = self.template
        for var in self.variables:
            if var in kwargs:
                result = result.replace(f"{{{var}}}", str(kwargs[var]))
        return result


class PromptLibrary:
    def __init__(self):
        self.templates = {}

    def add(self, template: PromptTemplate):
        self.templates[template.name] = template

    def get(self, name: str) -> Optional[PromptTemplate]:
        return self.templates.get(name)

    def list_templates(self) -> list:
        return [{"name": t.name, "description": t.description, "variables": t.variables} for t in self.templates.values()]

    def remove(self, name: str):
        self.templates.pop(name, None)


class PromptOptimizer:
    def __init__(self):
        self.library = PromptLibrary()

    def optimize_tokens(self, prompt: str, target_tokens: int = 0) -> str:
        if target_tokens <= 0:
            return prompt
        current = len(prompt)
        if current <= target_tokens:
            return prompt
        lines = prompt.split("\n")
        optimized = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if len(stripped) > 200:
                stripped = self._compress_line(stripped)
            optimized.append(stripped)
        result = "\n".join(optimized)
        while len(result) > target_tokens and len(optimized) > 1:
            optimized.pop(0)
            result = "\n".join(optimized)
        return result

    def _compress_line(self, line: str) -> str:
        line = re.sub(r'\s+', ' ', line)
        line = re.sub(r'#.*$', '', line, flags=re.MULTILINE)
        line = re.sub(r'"{2,}', '', line)
        line = re.sub(r"'{2,}", '', line)
        if len(line) > 100:
            line = line[:97] + "..."
        return line.strip()

    def score_prompt(self, prompt: str) -> dict:
        score = 100
        issues = []
        if len(prompt) < 10:
            score -= 30
            issues.append("Too short (less than 10 characters)")
        if not prompt.strip():
            score -= 50
            issues.append("Empty prompt")
        has_instructions = any(word in prompt.lower() for word in ["you are", "your task", "do this", "please", "should"])
        if not has_instructions:
            score -= 15
            issues.append("No clear instruction phrase detected")
        has_context = len(prompt) > 50
        if not has_context:
            score -= 10
            issues.append("Very little context provided")
        has_format = any(word in prompt.lower() for word in ["output", "return", "format", "json", "list"])
        if not has_format:
            score -= 5
            issues.append("No output format specified")
        return {"score": max(0, score), "issues": issues, "length": len(prompt)}

    def suggest_improvements(self, prompt: str) -> list:
        suggestions = []
        if "example" not in prompt.lower():
            suggestions.append("Add examples for clarity")
        if not any(word in prompt.lower() for word in ["step", "first", "then", "finally"]):
            suggestions.append("Add step-by-step instructions for complex tasks")
        if not any(word in prompt.lower() for word in ["avoid", "don't", "should not", "not"]):
            suggestions.append("Specify what to avoid or negative constraints")
        if not prompt.strip().endswith((".", "?", "!", ":", ";", "}")):
            suggestions.append("End the prompt with proper punctuation")
        return suggestions

    def ab_test(self, prompts: list, scorer: callable = None) -> dict:
        if scorer is None:
            scorer = self.score_prompt
        results = []
        for i, prompt in enumerate(prompts):
            score = scorer(prompt)
            results.append({"index": i, "prompt": prompt[:100], "score": score["score"]})
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"results": results, "winner": results[0]["index"] if results else -1}