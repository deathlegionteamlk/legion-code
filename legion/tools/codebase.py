import os

def explore_directory(path: str = ".", max_depth: int = 3) -> str:
    try:
        if not os.path.exists(path):
            return f"Error: path not found: {path}"
        lines = []
        base = os.path.abspath(path)
        for root, dirs, files in os.walk(base):
            rel = os.path.relpath(root, base)
            depth = len(rel.split(os.sep)) if rel != "." else 0
            if depth > max_depth:
                dirs.clear()
                continue
            indent = "  " * depth
            if rel == ".":
                lines.append(f"{os.path.basename(base)}/")
            else:
                lines.append(f"{indent}{os.path.basename(root)}/")
            for f in sorted(files):
                fpath = os.path.join(root, f)
                try:
                    size = os.path.getsize(fpath)
                except Exception:
                    size = 0
                lines.append(f"{indent}  {f} ({size} bytes)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error exploring directory: {e}"

def grep_search(pattern: str, path: str = ".", file_pattern: str = "*.py") -> str:
    try:
        cmd = f"grep -rn --include='{file_pattern}' '{pattern}' {path} 2>/dev/null | head -50"
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.stdout:
            return f"Matches for '{pattern}' in {file_pattern} files:\n{result.stdout.strip()}"
        elif result.returncode in (0, 1):
            return f"No matches found for '{pattern}' in {file_pattern} files"
        else:
            error = result.stderr.strip() if result.stderr else f"grep returned {result.returncode}"
            return f"Grep error: {error}"
    except Exception as e:
        return f"Error running grep: {e}"

def get_tool_definitions():
    return [
        {
            "name": "explore_directory",
            "description": "List files and directories in a tree format. Useful for understanding project structure.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to explore", "default": "."},
                    "max_depth": {"type": "integer", "description": "Maximum directory depth", "default": 3}
                },
                "required": []
            },
            "handler": lambda args: explore_directory(args.get("path", "."), args.get("max_depth", 3))
        },
        {
            "name": "grep_search",
            "description": "Search for text patterns in files using grep. Supports file pattern filtering.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text pattern to search for"},
                    "path": {"type": "string", "description": "Directory to search in", "default": "."},
                    "file_pattern": {"type": "string", "description": "File glob pattern (e.g. *.py, *.md)", "default": "*.py"}
                },
                "required": ["pattern"]
            },
            "handler": lambda args: grep_search(args.get("pattern", ""), args.get("path", "."), args.get("file_pattern", "*.py"))
        },
    ]