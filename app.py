import os
from flask import Flask, render_template, request, jsonify

from core.scanner import scan_project
from core.bundle_builder import build_bundle
from core.project_tree import build_project_tree

app = Flask(__name__)


def build_project_tree(root: str, ignore_dirs: set[str]) -> str:
    lines = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in ignore_dirs and not d.startswith(".")
        ]

        rel = os.path.relpath(dirpath, root)
        indent = "  " * (0 if rel == "." else rel.count(os.sep) + 1)

        if rel != ".":
            lines.append(f"{indent}{os.path.basename(dirpath)}/")

        for f in sorted(filenames):
            lines.append(f"{indent}  {f}")

    return "\n".join(lines)

def default_ignore_dirs() -> set[str]:
    return {
        ".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
        "node_modules", "dist", "build", ".idea", ".vscode"
    }

@app.get("/")
def index():

    # DEFAULT_ROOT = "C:/Homepage/math-education-v3"
    # DEFAULT_ROOT = "C:/Homepage/codeextract"
    DEFAULT_ROOT = "C:/Homepage/math-education-v4"

    root = os.path.abspath(request.args.get("root") or DEFAULT_ROOT)

    analysis = scan_project(root, ignore_dirs=default_ignore_dirs())

    ui_files = []

    for abs_path, fa in analysis.items():
        rel = os.path.relpath(abs_path, root)

        # WICHTIG: items als LIST, nicht als dict
        items = []
        items.extend(fa.functions)
        items.extend(fa.classes)

        ui_files.append({
            "abs": abs_path,
            "rel": rel,
            "items": items,
        })

    ui_files.sort(key=lambda x: x["rel"].lower())

    return render_template(
        "index.html",
        root=root,
        files=ui_files
    )


@app.post("/export")
def export_bundle():
    payload = request.get_json(force=True)
    root = os.path.abspath(payload.get("root", "."))
    selection = payload.get("selection", {})

    analysis = scan_project(root, ignore_dirs=default_ignore_dirs())
    out_path = os.path.join(root, "gpt_bundle.txt")

    build_bundle(list(analysis.values()), selection, out_path)

    tree = build_project_tree(root, default_ignore_dirs())

    with open(out_path, "a", encoding="utf-8") as f:
        f.write("\n\n# PROJECT STRUCTURE\n\n")
        f.write(tree)

    return jsonify({"ok": True, "out_path": out_path})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
