import ast
from pathlib import Path
from typing import List, Dict


def _node_name(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    return ""


def _node_type(node: ast.AST) -> str:
    if isinstance(node, ast.ClassDef):
        return "class"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "function"
    return "module"


def chunk_file(path: Path, content: str) -> List[Dict]:
    """Split a Python file into logical chunks using the AST.

    Returns chunks for:
    - imports and module-level statements
    - each top-level function
    - each top-level class
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    lines = content.splitlines()
    chunks: List[Dict] = []
    module_body: List[ast.AST] = []
    module_ranges: List[tuple] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if module_body:
                module_ranges.append((module_body[0].lineno, module_body[-1].end_lineno, module_body))
                module_body = []
            start = node.lineno - 1
            end = node.end_lineno
            chunk_lines = lines[start:end]
            chunks.append({
                "path": str(path),
                "name": node.name,
                "type": _node_type(node),
                "start_line": node.lineno,
                "end_line": node.end_lineno,
                "content": "\n".join(chunk_lines),
            })
        else:
            module_body.append(node)

    if module_body:
        module_ranges.append((module_body[0].lineno, module_body[-1].end_lineno, module_body))

    for start_line, end_line, _ in module_ranges:
        chunk_lines = lines[start_line - 1:end_line]
        chunks.append({
            "path": str(path),
            "name": "",
            "type": "module",
            "start_line": start_line,
            "end_line": end_line,
            "content": "\n".join(chunk_lines),
        })

    return chunks


def chunk_codebase(root: Path, glob: str = "**/*.py") -> List[Dict]:
    """Scan Python files and chunk them into logical units."""
    from retrieval.indexer import should_skip

    chunks: List[Dict] = []
    for path in root.rglob(glob):
        if should_skip(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if not content.strip():
            continue
        rel_path = path.relative_to(root)
        for chunk in chunk_file(path, content):
            chunk["path"] = str(rel_path)
            chunks.append(chunk)
    return chunks
