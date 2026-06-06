import os
import json

def read_file(filepath: str, max_lines: int = 500) -> str:
    if not os.path.exists(filepath):
        return f"Error: file not found: {filepath}"
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        total = len(lines)
        if total <= max_lines:
            content = "".join(lines)
        else:
            head = lines[:max_lines]
            tail = lines[-50:]
            content = "".join(head) + f"\n... [{total - max_lines} lines truncated] ...\n" + "".join(tail)
        return content
    except Exception as e:
        return f"Error reading {filepath}: {e}"

def write_file(filepath: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {filepath}"
    except Exception as e:
        return f"Error writing {filepath}: {e}"

def edit_file(filepath: str, search: str, replace: str) -> str:
    if not os.path.exists(filepath):
        return f"Error: file not found: {filepath}"
    try:
        with open(filepath, "r") as f:
            content = f.read()
        if search not in content:
            return f"Error: search text not found in {filepath}"
        new_content = content.replace(search, replace, 1)
        with open(filepath, "w") as f:
            f.write(new_content)
        return f"Replaced 1 occurrence in {filepath}"
    except Exception as e:
        return f"Error editing {filepath}: {e}"

def get_tool_definitions():
    return [
        {
            "name": "read_file",
            "description": "Read contents of a file. Specify max_lines to truncate large files.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path to the file to read"},
                    "max_lines": {"type": "integer", "description": "Maximum lines to return", "default": 500}
                },
                "required": ["filepath"]
            },
            "handler": lambda args: read_file(args.get("filepath", ""), args.get("max_lines", 500))
        },
        {
            "name": "write_file",
            "description": "Create or overwrite a file with content. Creates parent directories if needed.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path where file should be written"},
                    "content": {"type": "string", "description": "Complete file content to write"}
                },
                "required": ["filepath", "content"]
            },
            "handler": lambda args: write_file(args.get("filepath", ""), args.get("content", ""))
        },
        {
            "name": "edit_file",
            "description": "Search and replace text in an existing file. Only replaces first occurrence.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Absolute path to the file to edit"},
                    "search": {"type": "string", "description": "Exact text to find"},
                    "replace": {"type": "string", "description": "Text to replace it with"}
                },
                "required": ["filepath", "search", "replace"]
            },
            "handler": lambda args: edit_file(args.get("filepath", ""), args.get("search", ""), args.get("replace", ""))
        },
    ]