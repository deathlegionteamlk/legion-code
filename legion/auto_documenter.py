import os
import ast
import json


class AutoDocumenter:
    def __init__(self):
        self.structure = {}

    def scan_project(self, path: str) -> dict:
        self.structure = {"project": os.path.basename(path), "modules": []}
        for root, dirs, files in os.walk(path):
            if "__pycache__" in root or ".git" in root or "dist" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    fpath = os.path.join(root, f)
                    rel_path = os.path.relpath(fpath, path)
                    module_info = self._extract_module_info(fpath)
                    module_info["path"] = rel_path
                    self.structure["modules"].append(module_info)
        return self.structure

    def _extract_module_info(self, filepath: str) -> dict:
        with open(filepath) as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {"file": os.path.basename(filepath), "error": "syntax_error", "classes": [], "functions": []}
        info = {
            "file": os.path.basename(filepath),
            "docstring": ast.get_docstring(tree) or "",
            "classes": [],
            "functions": [],
            "exports": [],
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                    "methods": [],
                }
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        cls_info["methods"].append({
                            "name": item.name,
                            "lineno": item.lineno,
                            "args": [arg.arg for arg in item.args.args],
                            "docstring": ast.get_docstring(item) or "",
                        })
                info["classes"].append(cls_info)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree)) or not self._is_method(node, tree):
                    info["functions"].append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node) or "",
                    })
        return info

    def _is_method(self, node, tree):
        for c in ast.walk(tree):
            if isinstance(c, ast.ClassDef) and node in c.body:
                return True
        return False

    def generate_markdown(self, path: str = "") -> str:
        if not self.structure:
            self.scan_project(path or ".")
        lines = [f"# {self.structure['project']} API Documentation", "", "## Modules", ""]
        for mod in self.structure["modules"]:
            lines.append(f"### {mod['file']}")
            lines.append(f"**Path:** `{mod['path']}`")
            if mod.get("docstring"):
                lines.append(f"**Description:** {mod['docstring']}")
            lines.append("")
            if mod.get("classes"):
                lines.append("#### Classes")
                for cls in mod["classes"]:
                    lines.append(f"- **{cls['name']}** (line {cls['lineno']})")
                    if cls.get("docstring"):
                        lines.append(f"  - {cls['docstring']}")
                    for m in cls.get("methods", []):
                        args_str = ", ".join(m.get("args", []))
                        lines.append(f"  - `{m['name']}({args_str})`")
                        if m.get("docstring"):
                            lines.append(f"    - {m['docstring'].split(chr(10))[0]}")
                lines.append("")
            if mod.get("functions"):
                lines.append("#### Functions")
                for func in mod["functions"]:
                    args_str = ", ".join(func.get("args", []))
                    lines.append(f"- `{func['name']}({args_str})` (line {func['lineno']})")
                    if func.get("docstring"):
                        lines.append(f"  - {func['docstring'].split(chr(10))[0]}")
                lines.append("")
        return "\n".join(lines)

    def generate_api_docs(self, output_path: str = "API.md") -> str:
        md = self.generate_markdown()
        with open(output_path, "w") as f:
            f.write(md)
        return output_path