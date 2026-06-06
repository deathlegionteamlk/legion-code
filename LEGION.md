# Legion Code

**Autonomous Uncensored Coding Agent**

Built by **DeathLegionTeamLK** · Developed by **DEMO X HEXA**

## Overview
Legion Code is a fully autonomous AI coding agent framework matching Claude Code capabilities. It operates on uncensored models via OpenRouter, with read/write/edit file access, shell execution, internet search, git operations, multi-agent teams, slash commands, permission modes, MCP integration, hooks, skills, memory persistence, and cost tracking.

## Default Model
`cognitivecomputations/dolphin-mistral-24b-venice-edition:free` via OpenRouter

## Quick Start
```
python run.py --help
python run.py -P "hello world"
python run.py --interactive
python run.py "build a python calculator"
python run.py --plan "create a flask api"
python run.py --tools
```

## CLI Flags
| Flag | Description |
|------|-------------|
| --help, -h | Show help message |
| --version, -v | Show version and credits |
| --interactive, -i | Interactive chat mode (default) |
| --plan, -p <goal> | Plan and execute a goal |
| --print, -P <goal> | Print response and exit |
| --tools, -t | List available tools |
| --model <model> | Override model (e.g. openai/gpt-4o) |
| --output-format <fmt> | Output format: text/json/json-schema |
| --json-schema <file> | JSON schema file for structured output |
| --permission-mode <mode> | Permission mode: auto/default/plan |
| --allowedTools <list> | Comma-separated allowed tool list |
| --worktree <dir> | Git worktree directory |
| --bg, --background | Run agent in background |
| --agents <json> | Agent team JSON configuration |
| --resume, -r | Resume previous session |
| --max-turns <n> | Maximum conversation turns |
| --add-dir <dir> | Add directory to workspace |
| --system-prompt <text> | Additional system prompt |
| --effort <level> | Effort level: low/medium/high/max |
| --hook <cfg> | Register lifecycle hook |
| --skill <name> | Run a named skill |
| --mcp-add <cfg> | Add MCP server connection |
| --list | List background sessions |
| --compact | Compact conversation history |

## Slash Commands (interactive mode)
| Command | Description |
|---------|-------------|
| /help | List all slash commands |
| /init | Scan project, create LEGION.md |
| /plan | Read-only analysis mode |
| /review | Deep code review |
| /code-review | Diff-based code review |
| /test | Run tests and analyze results |
| /fix | Fix issues automatically |
| /cost | Show token and cost breakdown |
| /compact | Summarize conversation history |
| /model | Switch models mid-session |
| /effort | Set effort level (low/medium/high/max) |
| /mcp | Manage MCP servers |
| /doctor | Diagnose setup |
| /clear | Clear conversation |
| /summarize | Summarize session |
| /history | Show session history |
| /security-review | Security audit |
| /skills | List and run skills |

## Architecture
```
legion_code_0715/
├── run.py                    # CLI entrypoint
├── legion/
│   ├── __init__.py           # Package exports
│   ├── config.py             # All config fields
│   ├── provider.py           # Multi-backend provider (with retry)
│   ├── agent.py              # Enhanced agent loop
│   ├── cli.py                # CLI argument parser (25+ flags)
│   ├── commands.py           # 18 slash commands
│   ├── permissions.py        # 3 permission modes
│   ├── memory.py             # Session persistence, LEGION.md context
│   ├── cost_tracker.py       # Token/cost tracking
│   ├── hooks.py              # Lifecycle hooks system
│   ├── skills.py             # Skill loading from skills/ dir
│   ├── mcp.py                # MCP server registry + tool bridge
│   ├── sessions.py           # Background session daemon
│   ├── agent_teams.py        # Multi-agent orchestration (Team class)
│   ├── subagent.py           # Independent SubAgent class
│   ├── planner.py            # Goal decomposition
│   ├── researcher.py         # Internet search + synthesis
│   └── tools/
│       ├── __init__.py       # 17 tools registered
│       ├── files.py          # read_file, write_file, edit_file
│       ├── shell.py          # run_command
│       ├── search.py         # internet_search
│       ├── codebase.py       # explore_directory, grep_search
│       ├── jailbreak.py      # jailbreak_prompt
│       └── git_tools.py      # git_status, git_diff, git_commit, git_log, git_branch, git_pr, git_worktree
├── sessions/                 # Session storage
├── skills/                   # User-defined skills
├── plans/                    # Plan files
└── test_suite/
    ├── test_all_modules.py   # 275 comprehensive tests
    └── test_e2e_calculator.py # 124 E2E tests
```

## Permission System
- **auto**: All tool calls auto-approved
- **default**: Ask before destructive operations
- **plan**: Read-only mode (denies writes/commands)

Set with `--permission-mode <mode>` and restrict tools with `--allowedTools Read,Grep`

## Agent Teams
Spawn multi-agent teams with `--agents '{"planner":{"type":"planner"},"coder":{"type":"coder"}}'`

Agent types: planner, coder, reviewer, tester, researcher, security-reviewer

## Memory & Sessions
- LEGION.md provides project context
- `-r/--resume` resumes previous session
- Sessions stored in `sessions/` directory
- Auto memory persists notes across sessions

## MCP Integration
Connect external tools via MCP protocol:
- `/mcp add <name> <command>` — Register MCP server
- `/mcp remove <name>` — Remove server
- `/mcp list` — List connected servers

## Hooks System
Lifecycle hooks at: PreToolUse, PostToolUse, SessionStart, SessionEnd, TaskCompleted
Types: shell_command, http_webhook, llm_prompt

## Skills System
Markdown skills in `skills/` directory with YAML frontmatter.
Bundled skills: review, test, security-review, init

## Cost Tracking
Tracks input/output tokens per session, calculates API costs by model.
View with `/cost` slash command.

## Requirements
- Python 3.10+
- httpx
- rich
- pydantic

## Tools
17 tools available:

| Tool | Description |
|------|-------------|
| read_file | Read file contents |
| write_file | Create or overwrite files |
| edit_file | Search and replace in files |
| run_command | Execute shell commands |
| internet_search | Search the web |
| explore_directory | List directory structure |
| grep_search | Search text patterns in files |
| jailbreak_prompt | Generate prompt injection techniques |
| think | Internal reasoning and planning |
| finish | Signal task completion |
| git_status | Show working tree status |
| git_diff | Show file diffs |
| git_commit | Stage and commit changes |
| git_log | Show commit history |
| git_branch | Manage branches |
| git_pr | Create pull requests |
| git_worktree | Manage worktrees |

## Examples
```
# Interactive mode
python run.py

# Single command
python run.py "create a simple flask app"

# Plan mode
python run.py --plan "build a rest api"

# Custom model with auto permissions
python run.py --model openai/gpt-4o --permission-mode auto "list files"

# Background session
python run.py --bg "build a calculator"

# Resume previous session
python run.py --resume

# With agent team
python run.py --agents '{"planner":{"type":"planner"},"coder":{"type":"coder"},"reviewer":{"type":"reviewer"}}' "build a web app"

# Print mode (non-interactive)
python run.py -P "hello world"
```

## License
Apache 2.0