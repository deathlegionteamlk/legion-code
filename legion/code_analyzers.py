import ast
import os
from collections import defaultdict


class CodeAnalyzer:
    def __init__(self):
        self.results = {}

    def analyze_file(self, filepath: str) -> dict:
        with open(filepath) as f:
            source = f.read()
        tree = ast.parse(source)
        result = {
            "filepath": filepath,
            "complexity": self._cyclomatic_complexity(tree),
            "functions": self._extract_functions(tree),
            "classes": self._extract_classes(tree),
            "imports": self._extract_imports(tree),
            "lines": len(source.splitlines()),
            "dead_code": self._detect_dead_code(tree),
        }
        self.results[filepath] = result
        return result

    def _cyclomatic_complexity(self, tree: ast.AST) -> dict:
        counts = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler,
                                          ast.Assert, ast.BoolOp)):
                        complexity += 1
                    elif isinstance(child, ast.Try):
                        complexity += len(child.handlers)
                counts[node.name] = complexity
            elif isinstance(node, ast.AsyncFunctionDef):
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler,
                                          ast.Assert, ast.BoolOp)):
                        complexity += 1
                counts[node.name] = complexity
        return counts

    def _extract_functions(self, tree: ast.AST) -> list:
        funcs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [d.id if hasattr(d, 'id') else (d.attr if hasattr(d, 'attr') else '') for d in node.decorator_list],
                    "docstring": ast.get_docstring(node) or "",
                })
        return funcs

    def _extract_classes(self, tree: ast.AST) -> list:
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "bases": [b.id if hasattr(b, 'id') else (b.attr if hasattr(b, 'attr') else '') for b in node.bases],
                    "methods": [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))],
                    "docstring": ast.get_docstring(node) or "",
                })
        return classes

    def _extract_imports(self, tree: ast.AST) -> list:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"module": alias.name, "alias": alias.asname or ""})
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append({"module": node.module or "", "name": alias.name, "alias": alias.asname or ""})
        return imports

    def _detect_dead_code(self, tree: ast.AST) -> list:
        dead = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_return_after = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is None:
                        pass
                body = node.body
                for i, stmt in enumerate(body):
                    if isinstance(stmt, ast.Return) and i < len(body) - 1:
                        for j in range(i + 1, len(body)):
                            dead.append({
                                "type": "unreachable",
                                "function": node.name,
                                "lineno": body[j].lineno,
                                "code": ast.unparse(body[j])[:80] if hasattr(ast, 'unparse') else ""
                            })
            if isinstance(node, ast.If):
                if isinstance(node.test, ast.Constant) and node.test.value is False:
                    dead.append({
                        "type": "dead_branch",
                        "lineno": node.lineno,
                        "code": ast.unparse(node.test)[:80] if hasattr(ast, 'unparse') else "if False"
                    })
        return dead

    def dependency_graph(self, filepath: str) -> dict:
        result = self.analyze_file(filepath)
        graph = {"file": filepath, "imports": [], "imported_by": []}
        for imp in result["imports"]:
            graph["imports"].append(imp["module"] or imp.get("name", ""))
        return graph

    def analyze_directory(self, path: str) -> dict:
        results = {}
        for root, dirs, files in os.walk(path):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    fpath = os.path.join(root, f)
                    try:
                        results[fpath] = self.analyze_file(fpath)
                    except Exception:
                        pass
        return results