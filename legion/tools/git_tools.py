import os
import subprocess


def _git_run(args: list, workdir: str = "") -> str:
    cwd = workdir or os.getcwd()
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=30,
            cwd=cwd,
        )
        output = result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        return output.strip() if output.strip() else f"(git command completed with no output, exit {result.returncode})"
    except FileNotFoundError:
        return "Error: git not found. Install git first."
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"
    except Exception as e:
        return f"Error: {e}"


def git_status(workdir: str = "") -> str:
    return _git_run(["status"], workdir)


def git_diff(workdir: str = "", staged: bool = False) -> str:
    args = ["diff"]
    if staged:
        args.append("--cached")
    return _git_run(args, workdir)


def git_log(workdir: str = "", max_count: int = 10) -> str:
    return _git_run(["log", f"--max-count={max_count}", "--oneline"], workdir)


def git_commit(message: str, workdir: str = "", add_all: bool = True) -> str:
    if add_all:
        add_result = _git_run(["add", "-A"], workdir)
        if add_result and "Error" in add_result:
            return add_result
    return _git_run(["commit", "-m", message], workdir)


def git_branch(action: str = "", name: str = "", workdir: str = "") -> str:
    if action == "create":
        return _git_run(["checkout", "-b", name], workdir)
    elif action == "switch":
        return _git_run(["checkout", name], workdir)
    elif action == "delete":
        return _git_run(["branch", "-d", name], workdir)
    else:
        return _git_run(["branch"], workdir)


def git_pr(title: str = "", body: str = "", workdir: str = "") -> str:
    try:
        result = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body],
            capture_output=True, text=True, timeout=30,
            cwd=workdir or os.getcwd(),
        )
        output = result.stdout or result.stderr
        return output.strip() or f"PR created (exit {result.returncode})" if result.returncode == 0 else f"gh error: {result.stderr}"
    except FileNotFoundError:
        return "Error: gh CLI not found. Install gh to create PRs."
    except Exception as e:
        return f"Error creating PR: {e}"


def git_worktree(action: str = "", path: str = "", branch: str = "", workdir: str = "") -> str:
    if action == "add":
        return _git_run(["worktree", "add", path, branch], workdir)
    elif action == "remove":
        return _git_run(["worktree", "remove", path], workdir)
    else:
        return _git_run(["worktree", "list"], workdir)


def get_tool_definitions():
    return [
        {
            "name": "git_status",
            "description": "Show the working tree status: staged, unstaged, and untracked changes",
            "input_schema": {
                "type": "object",
                "properties": {
                    "workdir": {"type": "string", "description": "Working directory", "default": ""}
                },
                "required": []
            },
            "handler": lambda args: git_status(args.get("workdir", ""))
        },
        {
            "name": "git_diff",
            "description": "Show diff of unstaged or staged changes in the working tree",
            "input_schema": {
                "type": "object",
                "properties": {
                    "workdir": {"type": "string", "description": "Working directory", "default": ""},
                    "staged": {"type": "boolean", "description": "Show staged changes only", "default": False}
                },
                "required": []
            },
            "handler": lambda args: git_diff(args.get("workdir", ""), args.get("staged", False))
        },
        {
            "name": "git_log",
            "description": "Show recent commit history",
            "input_schema": {
                "type": "object",
                "properties": {
                    "workdir": {"type": "string", "description": "Working directory", "default": ""},
                    "max_count": {"type": "integer", "description": "Number of commits to show", "default": 10}
                },
                "required": []
            },
            "handler": lambda args: git_log(args.get("workdir", ""), args.get("max_count", 10))
        },
        {
            "name": "git_commit",
            "description": "Stage all changes and commit with a message",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "workdir": {"type": "string", "description": "Working directory", "default": ""}
                },
                "required": ["message"]
            },
            "handler": lambda args: git_commit(args.get("message", ""), args.get("workdir", ""), True)
        },
        {
            "name": "git_branch",
            "description": "List, create, switch, or delete branches",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: create, switch, delete, or leave empty to list", "default": ""},
                    "name": {"type": "string", "description": "Branch name for create/switch/delete", "default": ""},
                    "workdir": {"type": "string", "description": "Working directory", "default": ""}
                },
                "required": []
            },
            "handler": lambda args: git_branch(args.get("action", ""), args.get("name", ""), args.get("workdir", ""))
        },
        {
            "name": "git_pr",
            "description": "Create a GitHub Pull Request (requires gh CLI)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "PR title"},
                    "body": {"type": "string", "description": "PR body/description", "default": ""},
                    "workdir": {"type": "string", "description": "Working directory", "default": ""}
                },
                "required": ["title"]
            },
            "handler": lambda args: git_pr(args.get("title", ""), args.get("body", ""), args.get("workdir", ""))
        },
        {
            "name": "git_worktree",
            "description": "Manage git worktrees for parallel development",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: add, remove, or leave empty to list", "default": ""},
                    "path": {"type": "string", "description": "Path for add/remove", "default": ""},
                    "branch": {"type": "string", "description": "Branch for worktree add", "default": ""},
                    "workdir": {"type": "string", "description": "Working directory", "default": ""}
                },
                "required": []
            },
            "handler": lambda args: git_worktree(args.get("action", ""), args.get("path", ""), args.get("branch", ""), args.get("workdir", ""))
        },
    ]