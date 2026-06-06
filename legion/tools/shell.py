import subprocess
import shlex
import os

def run_command(command: str, workdir: str = "", timeout: int = 120) -> str:
    try:
        cwd = workdir if workdir else os.getcwd()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        return output.strip() if output.strip() else f"(command completed with no output, exit code {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error running command: {e}"

def get_tool_definitions():
    return [
        {
            "name": "run_command",
            "description": "Execute a shell command in the sandbox. Returns stdout and stderr.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "workdir": {"type": "string", "description": "Working directory (default: current dir)", "default": ""},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 120}
                },
                "required": ["command"]
            },
            "handler": lambda args: run_command(args.get("command", ""), args.get("workdir", ""), args.get("timeout", 120))
        },
    ]