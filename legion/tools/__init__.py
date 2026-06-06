import os
import json
from legion.tools.files import get_tool_definitions as get_file_tools
from legion.tools.shell import get_tool_definitions as get_shell_tools
from legion.tools.search import get_tool_definitions as get_search_tools
from legion.tools.codebase import get_tool_definitions as get_codebase_tools
from legion.tools.jailbreak import get_tool_definitions as get_jailbreak_tools
from legion.tools.git_tools import get_tool_definitions as get_git_tools
from legion.tools.database_tools import get_tool_definitions as get_database_tools
from legion.tools.network_tools import get_tool_definitions as get_network_tools
from legion.tools.file_advanced import get_tool_definitions as get_file_advanced_tools
from legion.tools.ai_tools import get_tool_definitions as get_ai_tools

_tool_registry = {}
_initialized = False


def _init():
    global _initialized, _tool_registry
    if _initialized:
        return
    all_tool_defs = []
    all_tool_defs.extend(get_file_tools())
    all_tool_defs.extend(get_shell_tools())
    all_tool_defs.extend(get_search_tools())
    all_tool_defs.extend(get_codebase_tools())
    all_tool_defs.extend(get_jailbreak_tools())
    all_tool_defs.extend(get_git_tools())
    all_tool_defs.extend(get_database_tools())
    all_tool_defs.extend(get_network_tools())
    all_tool_defs.extend(get_file_advanced_tools())
    all_tool_defs.extend(get_ai_tools())
    all_tool_defs.append({
        "name": "think",
        "description": "Use this for internal reasoning, planning next steps, and analysis. Records your thought process without changing any state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "thought": {"type": "string", "description": "Your internal reasoning and analysis"}
            },
            "required": ["thought"]
        },
        "handler": lambda args: f"Thought recorded: {args.get('thought', '')[:500]}"
    })
    all_tool_defs.append({
        "name": "finish",
        "description": "Call this when the task is complete. Provide a summary of what was accomplished.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Summary of what was accomplished"},
                "files_changed": {"type": "array", "items": {"type": "string"}, "description": "List of files created or modified"}
            },
            "required": ["summary"]
        },
        "handler": lambda args: f"Task complete: {args.get('summary', '')}"
    })
    for t in all_tool_defs:
        _tool_registry[t["name"]] = t
    _initialized = True


def get_registry():
    _init()
    return _tool_registry


def get_tool(name: str) -> dict:
    _init()
    return _tool_registry.get(name)


def get_all_tools():
    _init()
    return list(_tool_registry.values())


def get_tool_schemas():
    _init()
    schemas = []
    for t in _tool_registry.values():
        schemas.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            }
        })
    return schemas


def execute_tool(name: str, args: dict) -> str:
    _init()
    tool = _tool_registry.get(name)
    if not tool:
        return f"Error: unknown tool '{name}'"
    try:
        result = tool["handler"](args)
        return str(result)
    except Exception as e:
        return f"Error executing {name}: {e}"