import ast
import os
from typing import Dict, List, Any, Optional, Set


class FileAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.items.append({
            "type": "function",
            "name": node.name,
            "lineno_start": node.lineno,
            "lineno_end": node.end_lineno,
        })

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.items.append({
            "type": "async_function",
            "name": node.name,
            "lineno_start": node.lineno,
            "lineno_end": node.end_lineno,
        })

    def visit_ClassDef(self, node: ast.ClassDef):
        cls = {
            "type": "class",
            "name": node.name,
            "lineno_start": node.lineno,
            "lineno_end": node.end_lineno,
            "methods": []
        }
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                cls["methods"].append({
                    "type": "method",
                    "name": item.name,
                    "lineno_start": item.lineno,
                    "lineno_end": item.end_lineno,
                })
            elif isinstance(item, ast.AsyncFunctionDef):
                cls["methods"].append({
                    "type": "async_method",
                    "name": item.name,
                    "lineno_start": item.lineno,
                    "lineno_end": item.end_lineno,
                })
        self.items.append(cls)


def analyze_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source)
        analyzer = FileAnalyzer()
        for node in tree.body:
            # Nur top-level sammeln, nicht rekursiv alles doppelt.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                analyzer.visit(node)

        if not analyzer.items:
            return None

        return {
            "path": path,
            "items": analyzer.items,
            "source_lines": source.splitlines()
        }
    except (SyntaxError, OSError, UnicodeError):
        return None


def scan_project(root: str, ignore_dirs: Optional[Set[str]] = None) -> Dict[str, Any]:
    root = os.path.abspath(root)
    ignore_dirs = ignore_dirs or set()

    result: Dict[str, Any] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored dirs in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".git")]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            full_path = os.path.join(dirpath, fname)
            analysis = analyze_file(full_path)
            if analysis:
                result[full_path] = analysis

    return result


def extract_lines(source_lines: List[str], start: int, end: int) -> str:
    # lineno is 1-based inclusive
    if start < 1:
        start = 1
    if end < start:
        end = start
    return "\n".join(source_lines[start - 1:end])


def build_gpt_bundle(analysis: Dict[str, Any], selection: Dict[str, Any], out_path: str = "gpt_bundle.txt") -> None:
    """
    selection format (from UI):
    {
      "/abs/path/file.py": {
        "functions": ["foo", ...],
        "classes": {
          "MyClass": null,            # whole class
          "OtherClass": ["m1","m2"]   # only these methods (but we will include class header + those method defs)
        }
      }
    }
    """

    out: List[str] = []

    for file_path, sel in selection.items():
        file_data = analysis.get(file_path)
        if not file_data:
            continue

        funcs_wanted = set(sel.get("functions", []) or [])
        classes_wanted = sel.get("classes", {}) or {}

        if not funcs_wanted and not classes_wanted:
            continue

        out.append("\n# ===============================")
        out.append(f"# FILE: {file_path}")
        out.append("# ===============================\n")

        items = file_data["items"]
        lines = file_data["source_lines"]

        for item in items:
            if item["type"] in ("function", "async_function"):
                if item["name"] in funcs_wanted:
                    out.append(f"# {item['type'].upper()} {item['name']}")
                    out.append(extract_lines(lines, item["lineno_start"], item["lineno_end"]))
                    out.append("")

            elif item["type"] == "class":
                cls = item["name"]
                if cls not in classes_wanted:
                    continue

                wanted_methods = classes_wanted[cls]  # None or list[str]

                if wanted_methods is None:
                    # Whole class
                    out.append(f"# CLASS {cls}")
                    out.append(extract_lines(lines, item["lineno_start"], item["lineno_end"]))
                    out.append("")
                else:
                    # Only selected methods: include class signature line + selected method blocks
                    # We include class line through the line right before first method (best-effort),
                    # then include chosen methods blocks.
                    out.append(f"# CLASS {cls} (selected methods)")

                    methods = item.get("methods", [])
                    methods_sorted = sorted(methods, key=lambda m: m["lineno_start"])
                    if methods_sorted:
                        class_header_end = methods_sorted[0]["lineno_start"] - 1
                        out.append(extract_lines(lines, item["lineno_start"], class_header_end))
                    else:
                        # Class without methods: just include whole class (nothing else to do)
                        out.append(extract_lines(lines, item["lineno_start"], item["lineno_end"]))
                        out.append("")
                        continue

                    wanted_set = set(wanted_methods)
                    for m in methods_sorted:
                        if m["name"] in wanted_set:
                            out.append(f"\n# {m['type'].upper()} {cls}.{m['name']}")
                            out.append(extract_lines(lines, m["lineno_start"], m["lineno_end"]))

                    out.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
