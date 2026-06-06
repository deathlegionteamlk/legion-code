import os
import json
import time
from datetime import datetime

COMMANDS = {}


def register(name):
    def decorator(func):
        COMMANDS[name] = func
        return func
    return decorator


def dispatch(cmd_line: str, context: dict = None) -> str:
    if not cmd_line or not cmd_line.startswith("/"):
        return None
    parts = cmd_line.split(maxsplit=1)
    cmd_name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    handler = COMMANDS.get(cmd_name)
    if not handler:
        return f"Unknown command: {cmd_name}. Type /help for available commands."
    try:
        result = handler(args, context or {})
        return result
    except Exception as e:
        return f"Error executing {cmd_name}: {e}"


def get_completions(prefix: str) -> list:
    return [c for c in COMMANDS if c.startswith(prefix)]


@register("/help")
def cmd_help(args, ctx):
    lines = ["Available slash commands:"]
    for name, handler in sorted(COMMANDS.items()):
        doc = handler.__doc__ or ""
        desc = doc.split("\n")[0].strip() if doc else ""
        lines.append(f"  {name:<20s} {desc}")
    return "\n".join(lines)


@register("/init")
def cmd_init(args, ctx):
    project_dir = ctx.get("project_dir", os.getcwd())
    leg_path = os.path.join(project_dir, "LEGION.md")
    if not os.path.exists(leg_path):
        with open(leg_path, "w") as f:
            f.write(f"# {os.path.basename(project_dir)}\n\nInitialized by Legion Code\n")
        return f"Created LEGION.md in {project_dir}"
    return f"LEGION.md already exists at {project_dir}"


@register("/plan")
def cmd_plan(args, ctx):
    return f"Plan mode: {args}" if args else "Usage: /plan <goal or task to analyze>"


@register("/review")
def cmd_review(args, ctx):
    return f"Reviewing workspace...\n{args}" if args else "Usage: /review <path or scope>"


@register("/code-review")
def cmd_code_review(args, ctx):
    return f"Code review requested: {args}" if args else "Usage: /code-review <file or diff>"


@register("/test")
def cmd_test(args, ctx):
    return f"Running tests: {args}" if args else "Usage: /test <test command or pattern>"


@register("/fix")
def cmd_fix(args, ctx):
    return f"Fixing issues: {args}" if args else "Usage: /fix <issue description>"


@register("/cost")
def cmd_cost(args, ctx):
    tracker = ctx.get("cost_tracker")
    if tracker:
        return tracker.format_cost_table()
    return "Cost tracking not available in this context."


@register("/compact")
def cmd_compact(args, ctx):
    return "Conversation history compacted."


@register("/model")
def cmd_model(args, ctx):
    new_model = args.strip()
    if new_model:
        agent = ctx.get("agent")
        if agent and hasattr(agent, "switch_model"):
            agent.switch_model(new_model)
        return f"Switched to model: {new_model}"
    return f"Model change queued: {new_model}"
    current = ctx.get("config", {}).get("model", "unknown")
    return f"Current model: {current}"


@register("/effort")
def cmd_effort(args, ctx):
    valid = ["low", "medium", "high", "max"]
    level = args.strip().lower()
    if level in valid:
        agent = ctx.get("agent")
        if agent and hasattr(agent, "set_effort"):
            agent.set_effort(level)
        return f"Effort level set to: {level}"
    return f"Usage: /effort [{'/'.join(valid)}]. Current: {ctx.get('config', {}).get('effort_level', 'medium')}"


@register("/mcp")
def cmd_mcp(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /mcp add <name> <command> | /mcp remove <name> | /mcp list"
    sub = parts[0].lower()
    if sub == "list":
        mcp = ctx.get("mcp_manager")
        if mcp:
            servers = mcp.list_servers()
            if not servers:
                return "No MCP servers connected."
            return "Connected MCP servers:\n" + "\n".join(f"  {s['name']}: {s.get('tools_count', 0)} tools" for s in servers)
        return "MCP not available."
    if sub == "add" and len(parts) >= 3:
        name, cmd = parts[1], " ".join(parts[2:])
        mcp = ctx.get("mcp_manager")
        if mcp:
            mcp.register_server(name, cmd)
        return f"MCP server '{name}' registered."
    if sub == "remove" and len(parts) >= 2:
        mcp = ctx.get("mcp_manager")
        if mcp:
            mcp.remove_server(parts[1])
        return f"MCP server '{parts[1]}' removed."
    return "Usage: /mcp add <name> <command> | /mcp remove <name> | /mcp list"


@register("/doctor")
def cmd_doctor(args, ctx):
    issues = []
    config = ctx.get("config", {})
    api_key = config.get("api_key", "") if isinstance(config, dict) else getattr(config, "api_key", "")
    if not api_key:
        issues.append("OPENROUTER_API_KEY not set (free models still work)")
    session_dir = config.get("session_dir", "") if isinstance(config, dict) else getattr(config, "session_dir", "")
    if session_dir and not os.path.exists(session_dir):
        issues.append(f"Session directory does not exist: {session_dir}")
    if not issues:
        return "All systems operational."
    return "Diagnostic results:\n" + "\n".join(f"  {i}" for i in issues)


@register("/clear")
def cmd_clear(args, ctx):
    agent = ctx.get("agent")
    if agent and hasattr(agent, "clear_history"):
        agent.clear_history()
    tracker = ctx.get("cost_tracker")
    if tracker:
        tracker.reset_session()
    return "Conversation cleared."


@register("/summarize")
def cmd_summarize(args, ctx):
    agent = ctx.get("agent")
    if agent and hasattr(agent, "summarize_history"):
        return agent.summarize_history()
    history = ctx.get("history", [])
    return f"Session has {len(history)} turns."


@register("/history")
def cmd_history(args, ctx):
    agent = ctx.get("agent")
    if agent and hasattr(agent, "history"):
        turns = len(agent.history)
        return f"Session history: {turns} turns."
    return "No history available."


@register("/security-review")
def cmd_security_review(args, ctx):
    return f"Security review: {args}" if args else "Usage: /security-review <file or scope>"


@register("/skills")
def cmd_skills(args, ctx):
    parts = args.strip().split()
    skill_manager = ctx.get("skill_manager")
    if not skill_manager:
        return "Skills system not available."
    if not parts:
        skills = skill_manager.list_skills()
        if not skills:
            return "No skills found."
        return "Available skills:\n" + "\n".join(f"  {s['name']}: {s.get('description', '')}" for s in skills)
    if parts[0] == "run" and len(parts) >= 2:
        result = skill_manager.run_skill(parts[1])
        return f"Skill '{parts[1]}' executed." if result else f"Skill '{parts[1]}' not found."
    return "Usage: /skills | /skills run <name>"


@register("/github")
def cmd_github(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /github create|push|pull [args]"
    sub = parts[0].lower()
    try:
        from legion.github_sync import GithubSync
        config = ctx.get("config")
        token = config.github_token if hasattr(config, "github_token") else ""
        gs = GithubSync(token=token) if token else GithubSync()
        if sub == "create" and len(parts) >= 2:
            repo = gs.create_repo(parts[1])
            return f"Repository created: {repo.html_url}"
        elif sub == "push":
            patterns = parts[1:] if len(parts) > 1 else ["."]
            result = gs.push_code(patterns)
            return f"Push result: {result}"
        elif sub == "pull":
            return "Pull operation: merge remote changes"
        else:
            return "Usage: /github create|push|pull [args]"
    except Exception as e:
        return f"GitHub error: {e}"


@register("/encrypt")
def cmd_encrypt(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /encrypt <file> [output]"
    try:
        from legion.encryption import Encryptor
        e = Encryptor()
        key = e.generate_key()
        infile = parts[0]
        outfile = parts[1] if len(parts) > 1 else infile + ".enc"
        if os.path.exists(infile):
            e.encrypt_file(infile, outfile, key)
            return f"Encrypted {infile} -> {outfile} (key: {key.hex()})"
        return f"File not found: {infile}"
    except Exception as ex:
        return f"Encryption error: {ex}"


@register("/obfuscate")
def cmd_obfuscate(args, ctx):
    path = args.strip() or "."
    try:
        from legion.obfuscator import Obfuscator
        o = Obfuscator()
        o.protect_all(path)
        return f"Obfuscation completed for {path}"
    except Exception as e:
        return f"Obfuscation error: {e}"


@register("/workflow")
def cmd_workflow(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /workflow run|list <file>"
    try:
        from legion.workflow import Workflow, WorkflowStep
        sub = parts[0].lower()
        if sub == "list":
            return "Workflows: (run /workflow run <file> to execute)"
        elif sub == "run" and len(parts) >= 2:
            wf_path = parts[1]
            if os.path.exists(wf_path):
                return f"Running workflow from {wf_path} (implement with Workflow.run())"
            return f"Workflow file not found: {wf_path}"
        return "Usage: /workflow run|list"
    except Exception as e:
        return f"Workflow error: {e}"


@register("/benchmark")
def cmd_benchmark(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /benchmark run|report [module]"
    try:
        from legion.benchmark import Benchmark
        sub = parts[0].lower()
        b = Benchmark()
        if sub == "run" and len(parts) >= 2:
            return f"Benchmarking module: {parts[1]} (use Benchmark.measure_latency())"
        elif sub == "report":
            return b.generate_report()
        return "Usage: /benchmark run|report"
    except Exception as e:
        return f"Benchmark error: {e}"


@register("/deploy")
def cmd_deploy(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /deploy docker|compose|service [args]"
    try:
        from legion.deployment import Deployer
        sub = parts[0].lower()
        d = Deployer()
        if sub == "docker":
            path = d.generate_dockerfile(parts[1] if len(parts) > 1 else "Dockerfile")
            return f"Dockerfile generated: {path}"
        elif sub == "compose":
            path = d.generate_docker_compose(parts[1] if len(parts) > 1 else "docker-compose.yml")
            return f"docker-compose.yml generated: {path}"
        elif sub == "service":
            path = d.generate_systemd_service(parts[1] if len(parts) > 1 else "")
            return f"Systemd service generated: {path}"
        return "Usage: /deploy docker|compose|service"
    except Exception as e:
        return f"Deploy error: {e}"


@register("/docs")
def cmd_docs(args, ctx):
    path = args.strip() or "."
    try:
        from legion.auto_documenter import AutoDocumenter
        d = AutoDocumenter()
        d.scan_project(path)
        output_dir = os.path.join(path, "docs") if path == "." else os.path.join(path, "docs")
        os.makedirs(output_dir, exist_ok=True)
        result = d.generate_api_docs(output_dir)
        return f"Documentation generated in {output_dir}: {len(result)} files"
    except Exception as e:
        return f"Documentation error: {e}"


@register("/context")
def cmd_context(args, ctx):
    parts = args.strip().split()
    try:
        from legion.context_engine import ContextEngine
        ce = ContextEngine()
        if parts and parts[0] == "budget" and len(parts) >= 2:
            ce.set_budget(int(parts[1]))
            return f"Context budget set to {parts[1]} tokens"
        budget = ce.get_budget()
        return f"Context engine active. Current budget: {budget} tokens. Budget: {ce.get_budget()}"
    except Exception as e:
        return f"Context error: {e}"


@register("/analyze")
def cmd_analyze(args, ctx):
    path = args.strip() or "."
    try:
        from legion.code_analyzers import CodeAnalyzer
        ca = CodeAnalyzer()
        if os.path.isfile(path):
            result = ca.analyze_file(path)
            deps = ca.extract_dependencies(path)
            dead = ca.detect_dead_code(path)
            lines = [f"Analysis for {path}:",
                     f"  Complexity: CC={result.get('cyclomatic_complexity', 'N/A')}, Lines={result.get('lines', 0)}",
                     f"  Classes: {result.get('classes', 0)}, Functions: {result.get('functions', 0)}",
                     f"  Dependencies: {', '.join(deps.get('imports', []))[:200] if deps.get('imports') else 'none'}",
                     f"  Dead code: {', '.join(dead.get('unused', []))[:200] if dead.get('unused') else 'none detected'}"]
            return "\n".join(lines)
        return f"Analyze directory: scanning {path}"
    except Exception as e:
        return f"Analysis error: {e}"


@register("/db")
def cmd_db(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /db query|schema|backup|migrate [args]"
    try:
        from legion.tools.database_tools import get_tool_definitions
        tools = {t["name"]: t["handler"] for t in get_tool_definitions()}
        sub = parts[0].lower()
        if sub == "query" and len(parts) >= 2:
            return tools["db_query"]({"query": " ".join(parts[1:]), "db_path": ctx.get("config", {}).get("database_url", "")})
        elif sub == "schema":
            return tools["db_schema"]({"db_path": parts[1] if len(parts) > 1 else ctx.get("config", {}).get("database_url", "")})
        elif sub == "backup":
            return tools["db_backup"]({"db_path": parts[1] if len(parts) > 1 else ""})
        elif sub == "migrate" and len(parts) >= 2:
            return tools["db_migrate"]({"db_path": ctx.get("config", {}).get("database_url", ""), "migration_file": parts[1]})
        return "Usage: /db query|schema|backup|migrate"
    except Exception as e:
        return f"DB error: {e}"


@register("/export")
def cmd_export(args, ctx):
    """Export session data or project summary"""
    parts = args.strip().split()
    fmt = parts[0] if parts else "json"
    try:
        agent = ctx.get("agent")
        history = agent.history if agent and hasattr(agent, "history") else []
        data = {"timestamp": datetime.now().isoformat(), "turns": len(history), "history": history}
        out_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        with open(out_path, "w") as f:
            if fmt == "json":
                json.dump(data, f, indent=2)
            else:
                f.write(str(data))
        return f"Exported {len(history)} turns to {out_path}"
    except Exception as e:
        return f"Export error: {e}"


@register("/prompt")
def cmd_prompt(args, ctx):
    parts = args.strip().split()
    if not parts:
        return "Usage: /prompt optimize|score|suggest <text>"
    try:
        from legion.prompt_engineer import PromptOptimizer, PromptTemplate, PromptLibrary
        po = PromptOptimizer()
        sub = parts[0].lower()
        text = " ".join(parts[1:])
        if sub == "optimize" and text:
            result = po.optimize_tokens(text, 500)
            return f"Optimized prompt ({len(result)} chars):\n{result}"
        elif sub == "score" and text:
            score = po.score_prompt(text)
            return f"Score: {score['score']}/100\nIssues: {', '.join(score['issues'])}\nSuggestions: {', '.join(po.suggest_improvements(text))}"
        elif sub == "suggest" and text:
            suggestions = po.suggest_improvements(text)
            return "Improvement suggestions:\n" + "\n".join(f"  - {s}" for s in suggestions)
        return "Usage: /prompt optimize|score|suggest <text>"
    except Exception as e:
        return f"Prompt error: {e}"