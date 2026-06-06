import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box as rich_box
    from rich.text import Text
except ImportError:
    os.system("pip install -q rich")
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box as rich_box
    from rich.text import Text

from legion.config import Config
from legion.provider import Provider, ProviderError
from legion.agent import Agent, SYSTEM_PROMPT
from legion.planner import Planner
from legion.tools.__init__ import get_registry, execute_tool
from legion.cli import parse_args, validate_args, args_to_config
from legion.commands import dispatch
from legion.cost_tracker import CostTracker
from legion.memory import MemoryManager
from legion.permissions import PermissionChecker
from legion.hooks import HookManager, Hook
from legion.skills import SkillManager
from legion.mcp import McpManager
from legion.sessions import SessionManager
from legion.agent_teams import Team
from legion.encryption import Encryptor
from legion.obfuscator import Obfuscator
from legion.github_sync import GithubSync
from legion.workflow import Workflow, WorkflowStep
from legion.context_engine import ContextEngine
from legion.code_analyzers import CodeAnalyzer
from legion.auto_documenter import AutoDocumenter
from legion.benchmark import Benchmark
from legion.deployment import Deployer
from legion.prompt_engineer import PromptOptimizer, PromptTemplate, PromptLibrary

console = Console()

BANNER = """
[bold bright_cyan]██╗     ███████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗[/bold bright_cyan]
[bold bright_cyan]██║     ██╔════╝██╔════╝ ██║██╔═══██╗████╗  ██║[/bold bright_cyan]
[bold bright_cyan]██║     █████╗  ██║  ███╗██║██║   ██║██╔██╗ ██║[/bold bright_cyan]
[bold bright_cyan]██║     ██╔══╝  ██║   ██║██║██║   ██║██║╚██╗██║[/bold bright_cyan]
[bold bright_cyan]███████╗███████╗╚██████╔╝██║╚██████╔╝██║ ╚████║[/bold bright_cyan]
[bold bright_cyan]╚══════╝╚══════╝ ╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/bold bright_cyan]

[bold yellow]⚡ Autonomous Uncensored Coding Agent[/bold yellow]
[dim]Built by [bold]DeathLegionTeamLK[/bold] · Developed by [bold]DEMO X HEXA[/bold][/dim]
"""


def show_banner():
    console.clear()
    console.print(Panel(BANNER, box=rich_box.DOUBLE_EDGE, border_style="bright_cyan"))
    config = Config()
    console.print(f"   Model: {config.model}", style="dim")
    console.print(f"   API: {config.api_base}", style="dim")
    console.print(f"   Key: {'✓ Set' if config.api_key else '✗ Not set (free models only)'}", style="dim")
    console.print()


def save_session(session_data: dict, session_dir: str):
    os.makedirs(session_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(session_dir, f"session_{ts}.json")
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2)
    return path


def setup_components(config: Config):
    cost_tracker = CostTracker()
    memory_mgr = MemoryManager(config.session_dir)
    permission_checker = PermissionChecker(
        mode=config.permission_mode,
        allowed_tools=config.allowed_tools,
        denied_tools=config.denied_tools,
    )
    hook_mgr = HookManager()
    skill_mgr = SkillManager()
    mcp_mgr = McpManager()
    session_mgr = SessionManager(config.session_dir)
    for hook_cfg in config.hook_configs:
        if isinstance(hook_cfg, str):
            parts = hook_cfg.split(":", 2)
            if len(parts) >= 3:
                hook_mgr.register_from_config(parts[0], parts[1], {"command": parts[2], "name": f"hook_{parts[0]}_{parts[1]}"})
    for mcp_cfg in config.mcp_servers:
        if isinstance(mcp_cfg, str):
            parts = mcp_cfg.split(":", 1)
            if len(parts) >= 2:
                mcp_mgr.register_server(parts[0], parts[1])
    agent = Agent(config)
    agent.set_permission_checker(permission_checker)
    if config.effort_level:
        agent.set_effort(config.effort_level)
    return {
        "agent": agent,
        "cost_tracker": cost_tracker,
        "memory_mgr": memory_mgr,
        "permission_checker": permission_checker,
        "hook_mgr": hook_mgr,
        "skill_mgr": skill_mgr,
        "mcp_mgr": mcp_mgr,
        "session_mgr": session_mgr,
    }


def interactive_mode(config_override=None):
    show_banner()
    config = config_override or Config()
    components = setup_components(config)
    agent = components["agent"]
    cost_tracker = components["cost_tracker"]
    memory_mgr = components["memory_mgr"]
    hook_mgr = components["hook_mgr"]
    skill_mgr = components["skill_mgr"]
    permission_checker = components["permission_checker"]
    mcp_mgr = components["mcp_mgr"]
    session_mgr = components["session_mgr"]

    ctx = {
        "agent": agent,
        "config": config,
        "cost_tracker": cost_tracker,
        "memory_mgr": memory_mgr,
        "hook_mgr": hook_mgr,
        "skill_mgr": skill_mgr,
        "mcp_mgr": mcp_mgr,
        "permission_checker": permission_checker,
        "session_mgr": session_mgr,
        "project_dir": os.getcwd(),
    }

    if config.resume_session:
        session_data = memory_mgr.load_session(config.resume_session)
        if session_data and "history" in session_data:
            agent.history = session_data["history"]
            console.print(f"[dim]Resumed session with {len(agent.history)} messages[/dim]")
        else:
            console.print(f"[yellow]Session '{config.resume_session}' not found[/yellow]")

    if config.skill_name:
        skill_prompt = skill_mgr.get_prompt(config.skill_name)
        if skill_prompt:
            console.print(f"[dim]Loaded skill: {config.skill_name}[/dim]")

    hook_mgr.fire("SessionStart", {"session_id": "interactive"})

    console.print("[bold green]Interactive Mode[/bold green] — Type your goals. Type [bold]exit[/bold], [bold]quit[/bold], or [bold]/bye[/bold] to quit.\n", style="dim")
    session_history = []
    try:
        while True:
            goal = Prompt.ask("[bold cyan]You")
            if goal.lower() in ("exit", "quit", "/bye"):
                break
            if not goal.strip():
                continue
            session_history.append({"role": "user", "content": goal})
            if goal.startswith("/"):
                result = dispatch(goal, ctx)
                if result:
                    console.print(result)
                session_history.append({"role": "assistant", "content": result or ""})
                continue
            if goal.lower().startswith("plan:"):
                planner = Planner(config)
                plan = planner.decompose(goal[5:].strip())
                console.print("\n[bold yellow]Plan:[/bold yellow]")
                for step in plan:
                    sid = step.get("id", "?")
                    desc = step.get("description", "")
                    deps = step.get("dependencies", [])
                    dep_str = f" (after: {deps})" if deps else ""
                    console.print(f"  [cyan]{sid}.[/cyan] {desc}[dim]{dep_str}[/dim]")
                session_history.append({"role": "assistant", "content": f"Plan: {plan}"})
                continue
            console.print(f"\n[bold green]Legion:[/bold green]")
            try:
                result = agent.run_streaming(goal)
                console.print(f"\n[dim]{result[:100]}...[/dim]" if len(result) > 100 else f"\n[dim]{result}[/dim]")
                session_history.append({"role": "assistant", "content": result})
            except ProviderError as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}")
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    finally:
        hook_mgr.fire("SessionEnd", {"session_id": "interactive"})
        if session_history and config.save_sessions:
            path = save_session({
                "timestamp": datetime.now().isoformat(),
                "history": session_history,
                "config": {"model": config.model, "permission_mode": config.permission_mode},
                "summary": cost_tracker.format_cost_table(),
            }, config.session_dir)
            console.print(f"\n[dim]Session saved: {path}[/dim]")
        agent.close()


def single_command_mode(goal: str, config_override=None):
    config = config_override or Config()
    agent = Agent(config)
    if config.allowed_tools:
        from legion.permissions import PermissionChecker
        agent.set_permission_checker(PermissionChecker(mode=config.permission_mode, allowed_tools=config.allowed_tools))
    try:
        result = agent.run(goal)
        console.print(result)
        if config.save_sessions:
            save_session({
                "timestamp": datetime.now().isoformat(),
                "mode": "single",
                "goal": goal,
                "result": result,
            }, config.session_dir)
    except ProviderError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
    finally:
        agent.close()


def plan_mode(goal: str, config_override=None):
    config = config_override or Config()
    planner = Planner(config)
    plan = planner.decompose(goal)
    console.print(f"\n[bold yellow]Plan for: {goal}[/bold yellow]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim")
    table.add_column("Step", style="white")
    table.add_column("Dependencies", style="dim")
    table.add_column("Expected Output", style="dim")
    for step in plan:
        table.add_row(
            str(step.get("id", "")),
            step.get("description", "")[:60],
            str(step.get("dependencies", [])),
            step.get("expected_output", "")[:30],
        )
    console.print(table)
    if config.save_sessions:
        save_session({
            "timestamp": datetime.now().isoformat(),
            "mode": "plan",
            "goal": goal,
            "plan": plan,
        }, config.session_dir)


def tools_mode():
    registry = get_registry()
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Tool", style="bright_cyan")
    table.add_column("Description", style="white")
    table.add_column("Required Params", style="dim")
    for name, tool in sorted(registry.items()):
        params = tool.get("input_schema", {}).get("required", [])
        table.add_row(name, tool.get("description", "")[:50], ", ".join(params) if params else "none")
    console.print(table)


def show_help():
    show_banner()
    console.print("[bold]Usage:[/bold]")
    console.print("  python run.py [options] [goal]")
    console.print()
    table = Table(show_header=True, header_style="bold cyan", box=rich_box.ROUNDED)
    table.add_column("Flag", style="bright_yellow")
    table.add_column("Description", style="white")
    table.add_row("--help, -h", "Show this help message and exit")
    table.add_row("--version, -v", "Show version information")
    table.add_row("--interactive, -i", "Start interactive chat mode (default)")
    table.add_row("--plan, -p <goal>", "Generate and execute a plan")
    table.add_row("--print, -P <goal>", "Print response and exit")
    table.add_row("--tools, -t", "List all available tools")
    table.add_row("--model <model>", "Override default model")
    table.add_row("--output-format <fmt>", "Output format: text/json/json-schema")
    table.add_row("--json-schema <file>", "JSON schema for structured output")
    table.add_row("--permission-mode <mode>", "Permission mode: auto/default/plan")
    table.add_row("--allowedTools <list>", "Comma-separated allowed tool list")
    table.add_row("--worktree <dir>", "Git worktree directory")
    table.add_row("--bg, --background", "Run agent in background")
    table.add_row("--agents <json>", "Agent team JSON configuration")
    table.add_row("--resume, -r [id]", "Resume previous session")
    table.add_row("--max-turns <n>", "Maximum conversation turns")
    table.add_row("--add-dir <dir>", "Add directory to workspace")
    table.add_row("--system-prompt <text>", "Additional system prompt")
    table.add_row("--effort <level>", "Effort level: low/medium/high/max")
    table.add_row("--hook <cfg>", "Register lifecycle hook")
    table.add_row("--skill <name>", "Run a named skill")
    table.add_row("--mcp-add <cfg>", "Add MCP server connection")
    table.add_row("--list", "List background sessions")
    table.add_row("--compact", "Compact conversation history")
    table.add_row("--github-push <patterns>", "Push code to GitHub")
    table.add_row("--encrypt <file>", "Encrypt a file with AES-256")
    table.add_row("--obfuscate", "Obfuscate Python files with PyArmor")
    table.add_row("--deploy <type>", "Generate deployment configs (docker/compose/service)")
    table.add_row("--docs", "Generate API documentation")
    table.add_row("--benchmark <module>", "Run performance benchmark")
    table.add_row("--protect", "Protect (obfuscate) source files")
    console.print(table)
    console.print()
    console.print("[bold]Examples:[/bold]")
    console.print("  python run.py --help")
    console.print('  python run.py -P "hello world"')
    console.print("  python run.py --interactive")
    console.print('  python run.py "build a python calculator"')
    console.print('  python run.py --plan "create a flask api"')
    console.print("  python run.py --tools")
    console.print('  python run.py --model "openai/gpt-4o" --permission-mode auto "list files"')
    console.print("  python run.py --encrypt myfile.txt")
    console.print("  python run.py --obfuscate")
    console.print("  python run.py --docs")
    console.print("  python run.py --benchmark mymodule")


def version_info():
    show_banner()
    console.print("Version: 1.0.0", style="dim")
    console.print("Platform: Legion Code", style="dim")
    console.print("Built by: DeathLegionTeamLK", style="dim")
    console.print("Developed by: DEMO X HEXA", style="dim")


def main():
    ns = parse_args()
    ns = validate_args(ns)

    if ns.help:
        show_help()
        return
    if ns.version:
        version_info()
        return

    config = Config()
    config = args_to_config(ns, config)

    if ns.list_mode:
        from legion.sessions import SessionManager
        sm = SessionManager(config.session_dir)
        sessions = sm.list_sessions()
        if not sessions:
            console.print("No background sessions.")
            return
        console.print("[bold]Background Sessions:[/bold]")
        for s in sessions:
            status = "running" if s.get("status") == "running" else "stopped"
            console.print(f"  {s['id']}: {status} (PID: {s.get('pid', '?')})")
        return

    if ns.bg_enabled:
        from legion.sessions import SessionManager
        sm = SessionManager(config.session_dir)
        goal = ns.goal or "interactive"
        sid = sm.start_background(f"cd {os.getcwd()} && python run.py -P '{goal}'", config.session_dir)
        console.print(f"[green]Background session started: {sid}[/green]")
        console.print(f"[dim]Log: {config.session_dir}/{sid}.log[/dim]")
        return

    if ns.github_push:
        try:
            gs = GithubSync(token=config.github_token)
            patterns = ns.github_push.split(",")
            result = gs.push_code(patterns)
            console.print(f"[green]{result}[/green]")
        except Exception as e:
            console.print(f"[red]GitHub push error: {e}[/red]")
        return

    if ns.encrypt:
        try:
            enc = Encryptor()
            key = enc.generate_key()
            enc.encrypt_file(ns.encrypt, ns.encrypt + ".enc", key)
            console.print(f"[green]Encrypted {ns.encrypt} -> {ns.encrypt}.enc (key: {key.hex()})[/green]")
        except Exception as e:
            console.print(f"[red]Encryption error: {e}[/red]")
        return

    if ns.obfuscate is not None:
        try:
            ob = Obfuscator()
            path = ns.obfuscate if ns.obfuscate else "."
            ob.protect_all(path)
            console.print(f"[green]Obfuscation completed for {path}[/green]")
        except Exception as e:
            console.print(f"[red]Obfuscation error: {e}[/red]")
        return

    if ns.protect is not None:
        try:
            ob = Obfuscator()
            path = ns.protect if ns.protect else "."
            ob.protect_all(path)
            console.print(f"[green]Protection (obfuscation) completed for {path}[/green]")
        except Exception as e:
            console.print(f"[red]Protection error: {e}[/red]")
        return

    if ns.deploy:
        try:
            dp = Deployer()
            if ns.deploy == "docker":
                path = dp.generate_dockerfile()
            elif ns.deploy == "compose":
                path = dp.generate_docker_compose()
            elif ns.deploy == "service":
                path = dp.generate_systemd_service()
            else:
                console.print(f"[yellow]Unknown deploy type: {ns.deploy}. Use docker, compose, or service.[/yellow]")
                return
            console.print(f"[green]Deployment config generated: {path}[/green]")
        except Exception as e:
            console.print(f"[red]Deployment error: {e}[/red]")
        return

    if ns.docs is not None:
        try:
            ad = AutoDocumenter()
            path = ns.docs if ns.docs else "."
            ad.scan_project(path)
            output_dir = os.path.join(path, "docs") if path == "." else os.path.join(path, "docs")
            os.makedirs(output_dir, exist_ok=True)
            result = ad.generate_api_docs(output_dir)
            console.print(f"[green]Documentation generated in {output_dir}: {len(result)} files[/green]")
        except Exception as e:
            console.print(f"[red]Documentation error: {e}[/red]")
        return

    if ns.benchmark:
        try:
            bm = Benchmark()
            mod_name = ns.benchmark
            console.print(f"[green]Benchmarking module: {mod_name}[/green]")
            console.print(bm.generate_report())
        except Exception as e:
            console.print(f"[red]Benchmark error: {e}[/red]")
        return

    if ns.tools:
        show_banner()
        tools_mode()
        return

    if ns.print_mode:
        goal_to_run = ns.goal or ns.print_mode if isinstance(ns.print_mode, str) and ns.print_mode else ns.goal or "interactive"
        single_command_mode(goal_to_run, config)
        return

    if ns.goal and ns.print_mode is None and not ns.interactive:
        if ns.plan is not None:
            show_banner()
            plan_mode(ns.goal, config)
        else:
            show_banner()
            single_command_mode(ns.goal, config)
        return

    interactive_mode(config)


if __name__ == "__main__":
    main()