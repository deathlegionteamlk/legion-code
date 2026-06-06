import fnmatch
from enum import Enum


class PermissionMode(Enum):
    DEFAULT = "default"
    AUTO = "auto"
    PLAN = "plan"


class PermissionAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


WRITE_TOOLS = {"write_file", "edit_file", "run_command"}
DESTRUCTIVE_COMMANDS = {"rm", "rmdir", "chmod -R", "dd", "mkfs", "format", ">", "|"}


class PermissionChecker:
    def __init__(self, mode: str = "default", allowed_tools: list = None, denied_tools: list = None):
        self.mode = PermissionMode(mode)
        self.allowed_tools = allowed_tools or []
        self.denied_tools = denied_tools or []
        self.rules = []

    def add_rule(self, tool_pattern: str, action: str):
        self.rules.append((tool_pattern, PermissionAction(action)))

    def check_tool(self, tool_name: str, tool_args: dict = None) -> tuple:
        if self.mode == PermissionMode.PLAN:
            if tool_name in WRITE_TOOLS:
                return False, "plan mode: write operations not allowed"
            if tool_name == "run_command":
                cmd = tool_args.get("command", "") if tool_args else ""
                for dc in DESTRUCTIVE_COMMANDS:
                    if cmd.strip().startswith(dc):
                        return False, f"plan mode: destructive command '{dc}' not allowed"
            return True, ""
        if self.allowed_tools:
            if tool_name not in self.allowed_tools and tool_name not in ("think", "finish"):
                return False, f"tool '{tool_name}' not in allowed tools list"
        if tool_name in self.denied_tools:
            return False, f"tool '{tool_name}' is denied"
        for pattern, action in self.rules:
            if fnmatch.fnmatch(tool_name, pattern):
                if action == PermissionAction.DENY:
                    return False, f"tool '{tool_name}' denied by rule"
                if action == PermissionAction.ALLOW:
                    return True, ""
                if action == PermissionAction.ASK:
                    return None, f"tool '{tool_name}' requires approval"
        if self.mode == PermissionMode.AUTO:
            return True, ""
        if tool_name in WRITE_TOOLS:
            return None, f"tool '{tool_name}' requires approval in default mode"
        if tool_name == "run_command":
            cmd = tool_args.get("command", "") if tool_args else ""
            for dc in DESTRUCTIVE_COMMANDS:
                if cmd.strip().startswith(dc):
                    return None, f"destructive command '{dc}' requires approval"
            return True, ""
        return True, ""

    def to_config_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "allowed_tools": self.allowed_tools,
            "denied_tools": self.denied_tools,
            "rules": [(p, a.value) for p, a in self.rules],
        }