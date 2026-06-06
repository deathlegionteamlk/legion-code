import argparse
import json
import sys


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="legion",
        description="Legion Code - Autonomous Uncensored Coding Agent",
        add_help=False,
    )
    parser.add_argument("--help", "-h", action="store_true", help="Show help message and exit")
    parser.add_argument("--version", "-v", action="store_true", help="Show version information")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive chat mode")
    parser.add_argument("--plan", "-p", type=str, nargs="?", const="", default=None, help="Generate and execute a plan")
    parser.add_argument("--print", "-P", type=str, nargs="?", const="", default=None, dest="print_mode", help="Print response and exit")
    parser.add_argument("--tools", "-t", action="store_true", help="List all available tools")
    parser.add_argument("--model", type=str, default=None, help="Override default model")
    parser.add_argument("--output-format", type=str, choices=["text", "json", "json-schema"], default=None, help="Output format")
    parser.add_argument("--json-schema", type=str, default=None, help="JSON schema file path for structured output")
    parser.add_argument("--permission-mode", type=str, choices=["auto", "default", "plan"], default=None, help="Permission approval mode")
    parser.add_argument("--allowedTools", type=str, default=None, help="Comma-separated list of allowed tool names")
    parser.add_argument("--worktree", type=str, default=None, help="Git worktree directory for isolated development")
    parser.add_argument("--bg", "--background", action="store_true", default=None, dest="bg_enabled", help="Run agent in background")
    parser.add_argument("--agents", type=str, default=None, help="JSON config for agent teams")
    parser.add_argument("--resume", "-r", type=str, nargs="?", const="latest", default=None, help="Resume previous session")
    parser.add_argument("--continue", "-c", action="store_true", default=None, dest="cont", help="Continue from last session")
    parser.add_argument("--max-turns", type=int, default=None, help="Maximum conversation turns")
    parser.add_argument("--add-dir", type=str, action="append", default=None, dest="add_dirs", help="Add directory to workspace")
    parser.add_argument("--system-prompt", type=str, default=None, help="Additional system prompt text")
    parser.add_argument("--effort", type=str, choices=["low", "medium", "high", "max"], default=None, help="Effort level")
    parser.add_argument("--hook", type=str, action="append", default=None, help="Register a lifecycle hook")
    parser.add_argument("--skill", type=str, default=None, help="Run a named skill")
    parser.add_argument("--mcp-add", type=str, action="append", default=None, help="Add MCP server connection")
    parser.add_argument("--list", action="store_true", default=None, dest="list_mode", help="List background sessions")
    parser.add_argument("--compact", action="store_true", default=None, help="Compact conversation history")
    # New flags for expanded framework
    parser.add_argument("--github-push", type=str, default=None, help="Push to GitHub with file patterns")
    parser.add_argument("--encrypt", type=str, default=None, help="Encrypt a file")
    parser.add_argument("--obfuscate", type=str, nargs="?", const=".", default=None, help="Obfuscate Python files")
    parser.add_argument("--deploy", type=str, default=None, help="Generate deployment configs: docker, compose, service")
    parser.add_argument("--docs", type=str, nargs="?", const=".", default=None, help="Generate API documentation")
    parser.add_argument("--benchmark", type=str, default=None, help="Run benchmark on a module")
    parser.add_argument("--protect", type=str, nargs="?", const=".", default=None, help="Protect (obfuscate) source files")
    parser.add_argument("goal", type=str, nargs="*", default=None, help="Goal or prompt to execute")
    return parser.parse_args(args)


def validate_args(ns: argparse.Namespace) -> argparse.Namespace:
    if ns.json_schema and ns.output_format != "json-schema":
        ns.output_format = "json-schema"
    if ns.json_schema:
        try:
            with open(ns.json_schema) as f:
                json.load(f)
        except Exception:
            print(f"Warning: could not load json schema from {ns.json_schema}", file=sys.stderr)
            ns.json_schema = None
    if ns.agents:
        try:
            ns.agents = json.loads(ns.agents) if isinstance(ns.agents, str) else ns.agents
        except json.JSONDecodeError:
            print("Warning: --agents value is not valid JSON, ignoring", file=sys.stderr)
            ns.agents = None
    if ns.allowedTools:
        ns.allowed_tools = [t.strip() for t in ns.allowedTools.split(",")]
    else:
        ns.allowed_tools = None
    if ns.mcp_add:
        ns.mcp_servers = ns.mcp_add
    else:
        ns.mcp_servers = None
    if ns.hook:
        ns.hook_configs = ns.hook
    else:
        ns.hook_configs = None
    if ns.add_dirs:
        ns.workspace_dirs = ns.add_dirs
    else:
        ns.workspace_dirs = None
    if ns.goal:
        ns.goal = " ".join(ns.goal)
    else:
        ns.goal = None
    return ns


def args_to_config(ns: argparse.Namespace, config_obj=None):
    if config_obj is None:
        from legion.config import Config
        config_obj = Config()
    if ns.model:
        config_obj.model = ns.model
    if ns.output_format:
        config_obj.output_format = ns.output_format
    if ns.json_schema:
        config_obj.json_schema = ns.json_schema
    if ns.permission_mode:
        config_obj.permission_mode = ns.permission_mode
    if ns.allowed_tools is not None:
        config_obj.allowed_tools = ns.allowed_tools
    if ns.worktree:
        config_obj.worktree_dir = ns.worktree
    if ns.bg_enabled:
        config_obj.bg_enabled = True
    if ns.agents:
        config_obj.agents_config = ns.agents
    if ns.resume:
        config_obj.resume_session = ns.resume
    if ns.cont:
        config_obj.resume_session = "latest"
    if ns.max_turns:
        config_obj.max_turns = ns.max_turns
    if ns.workspace_dirs:
        config_obj.add_dirs = ns.workspace_dirs
    if ns.system_prompt:
        config_obj.system_prompt_extra = ns.system_prompt
    if ns.effort:
        config_obj.effort_level = ns.effort
    if ns.hook_configs:
        config_obj.hook_configs = ns.hook_configs
    if ns.skill:
        config_obj.skill_name = ns.skill
    if ns.mcp_servers:
        config_obj.mcp_servers = ns.mcp_servers
    if ns.list_mode:
        config_obj.list_mode = True
    if ns.compact:
        config_obj.compact_mode = True
    if ns.github_push:
        config_obj.github_repo = ns.github_push
    return config_obj