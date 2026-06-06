import json
from legion.config import Config
from legion.provider import Provider

PLANNER_PROMPT = """You are a planning AI. Given a high-level goal, decompose it into an ordered list of subtasks.

For e provach subtask,ide:
1. id: numeric identifier
2. description: what to do
3. expected_output: what files or results should be produced
4. dependencies: list of subtask ids that must be completed first (can be empty)

Return ONLY a valid JSON array. No other text."""

class Planner:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.provider = Provider(self.config)

    def decompose(self, goal: str) -> list[dict]:
        messages = [
            {"role": "user", "content": f"Decompose this goal into subtasks: {goal}"}
        ]
        try:
            response = self.provider.chat(messages, system_prompt=PLANNER_PROMPT)
            message = self.provider.extract_assistant_message(response)
            content = message.get("content", "")
            plan = self._parse_plan(content)
            return plan
        except Exception as e:
            return [{"id": 1, "description": goal, "expected_output": "complete", "dependencies": []}]

    def _parse_plan(self, content: str) -> list[dict]:
        if not content:
            return []
        json_start = content.find("[")
        json_end = content.rfind("]")
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end+1]
            try:
                plan = json.loads(json_str)
                if isinstance(plan, list):
                    return plan
            except json.JSONDecodeError:
                pass
        try:
            plan = json.loads(content)
            if isinstance(plan, list):
                return plan
        except json.JSONDecodeError:
            pass
        lines = content.strip().split("\n")
        plan = []
        import re
        for line in lines:
            m = re.match(r"^\d+[.)]\s*(.*)", line)
            if m:
                plan.append({
                    "id": len(plan) + 1,
                    "description": m.group(1).strip(),
                    "expected_output": "",
                    "dependencies": []
                })
        return plan if plan else [{"id": 1, "description": content[:200], "expected_output": "", "dependencies": []}]

    def format_plan(self, plan: list[dict]) -> str:
        if not plan:
            return "No plan generated"
        lines = ["Plan:"]
        for step in plan:
            sid = step.get("id", "?")
            desc = step.get("description", "No description")
            out = step.get("expected_output", "")
            deps = step.get("dependencies", [])
            deps_str = f" (depends on: {deps})" if deps else ""
            lines.append(f"  {sid}. {desc}{deps_str}")
            if out:
                lines.append(f"     Output: {out}")
        return "\n".join(lines)

    def close(self):
        self.provider.close()