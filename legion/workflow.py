import time
import json
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class WorkflowStep:
    id: str
    description: str = ""
    action: Callable = None
    depends_on: list = field(default_factory=list)
    condition: str = ""
    retry: int = 0
    timeout: int = 0


class Workflow:
    def __init__(self, name: str = ""):
        self.name = name or "default"
        self.steps = {}
        self.results = {}
        self.state = {}

    def add_step(self, step: WorkflowStep) -> str:
        self.steps[step.id] = step
        return step.id

    def validate(self) -> list:
        errors = []
        for sid, step in self.steps.items():
            for dep in step.depends_on:
                if dep not in self.steps:
                    errors.append(f"Step '{sid}' depends on unknown step '{dep}'")
        visited = set()
        path = set()

        def _dfs(node):
            if node in path:
                errors.append(f"Cycle detected involving step '{node}'")
                return
            if node in visited:
                return
            path.add(node)
            visited.add(node)
            step = self.steps.get(node)
            if step:
                for dep in step.depends_on:
                    _dfs(dep)
            path.remove(node)

        for sid in self.steps:
            _dfs(sid)
        return errors

    def run(self, context: dict = None) -> dict:
        errors = self.validate()
        if errors:
            return {"status": "validation_error", "errors": errors}
        if context is None:
            context = {}
        self.state = dict(context)
        self.results = {}
        completed = set()

        def _can_run(step):
            return all(dep in completed for dep in step.depends_on)

        while len(completed) < len(self.steps):
            progress = False
            for sid, step in sorted(self.steps.items()):
                if sid in completed:
                    continue
                if not _can_run(step):
                    continue
                if step.condition and step.condition not in self.state and step.condition not in self.results:
                    self.results[sid] = {"status": "skipped", "reason": f"condition '{step.condition}' not met"}
                    completed.add(sid)
                    progress = True
                    continue
                attempt = 0
                while attempt <= step.retry:
                    try:
                        result = step.action(self.state, self.results) if step.action else {"done": True}
                        self.results[sid] = {"status": "completed", "result": result}
                        break
                    except Exception as e:
                        attempt += 1
                        if attempt > step.retry:
                            self.results[sid] = {"status": "failed", "error": str(e)}
                            return {"status": "failed", "step": sid, "error": str(e), "results": self.results}
                completed.add(sid)
                progress = True
            if not progress:
                blocked = [sid for sid in self.steps if sid not in completed]
                return {"status": "deadlock", "blocked": blocked, "results": self.results}
        return {"status": "completed", "results": self.results}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "steps": {sid: {"id": s.id, "description": s.description, "depends_on": s.depends_on, "condition": s.condition, "retry": s.retry} for sid, s in self.steps.items()}
        }