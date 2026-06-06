import os
import json
import subprocess
import threading
import urllib.request
import urllib.parse
from enum import Enum


class HookEvent(Enum):
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    TASK_COMPLETED = "TaskCompleted"


HOOK_EVENTS = list(HookEvent)


class HookType(Enum):
    SHELL_COMMAND = "shell_command"
    HTTP_WEBHOOK = "http_webhook"
    LLM_PROMPT = "llm_prompt"


class Hook:
    def __init__(self, event: str, hook_type: str, config: dict):
        self.event = HookEvent(event)
        self.hook_type = HookType(hook_type)
        self.config = config
        self.name = config.get("name", f"hook_{event}_{hook_type}")

    def get_env(self, event_data: dict) -> dict:
        env = os.environ.copy()
        env["HOOK_EVENT"] = self.event.value
        for k, v in event_data.items():
            env[f"HOOK_{k.upper()}"] = str(v)
        return env

    def execute(self, event_data: dict) -> str:
        if self.hook_type == HookType.SHELL_COMMAND:
            return self._run_shell(event_data)
        elif self.hook_type == HookType.HTTP_WEBHOOK:
            return self._run_http(event_data)
        elif self.hook_type == HookType.LLM_PROMPT:
            return self._run_llm(event_data)
        return ""

    def _run_shell(self, event_data: dict) -> str:
        command = self.config.get("command", "")
        if not command:
            return ""
        env = self.get_env(event_data)
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=self.config.get("timeout", 30), env=env,
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return output.strip()
        except subprocess.TimeoutExpired:
            return f"Hook timeout: {command}"
        except Exception as e:
            return f"Hook error: {e}"

    def _run_http(self, event_data: dict) -> str:
        url = self.config.get("url", "")
        if not url:
            return ""
        try:
            data = json.dumps(event_data).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.config.get("timeout", 10)) as resp:
                return resp.read().decode()
        except Exception as e:
            return f"HTTP hook error: {e}"

    def _run_llm(self, event_data: dict) -> str:
        prompt = self.config.get("prompt", "")
        return prompt.format(**event_data) if prompt else ""


class HookManager:
    def __init__(self):
        self.hooks = {event: [] for event in HOOK_EVENTS}

    def register(self, hook: Hook):
        if hook.event in self.hooks:
            self.hooks[hook.event].append(hook)
        else:
            self.hooks[hook.event] = [hook]

    def register_from_config(self, event: str, hook_type: str, config: dict):
        hook = Hook(event, hook_type, config)
        self.register(hook)
        return hook

    def unregister(self, event: str, name: str):
        event_enum = HookEvent(event)
        if event_enum in self.hooks:
            self.hooks[event_enum] = [h for h in self.hooks[event_enum] if h.name != name]

    def fire(self, event: str, event_data: dict = None) -> list:
        event_enum = HookEvent(event)
        hooks = self.hooks.get(event_enum, [])
        results = []
        for hook in hooks:
            try:
                result = hook.execute(event_data or {})
                results.append({"hook": hook.name, "event": event, "result": result})
            except Exception as e:
                results.append({"hook": hook.name, "event": event, "error": str(e)})
        return results

    def fire_async(self, event: str, event_data: dict = None):
        t = threading.Thread(target=self.fire, args=(event, event_data or {}))
        t.daemon = True
        t.start()

    def get_registered_events(self) -> dict:
        return {event.value: [h.name for h in hooks] for event, hooks in self.hooks.items() if hooks}