import os
from flask import Flask, render_template, request, jsonify

from core.scanner import scan_project
from core.bundle_builder import build_bundle

app = Flask(__name__)

def default_ignore_dirs() -> set[str]:
    return {
        ".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
        "node_modules", "dist", "build", ".idea", ".vscode"
    }

@app.get("/")
def index():
    root = request.args.get("root", ".").strip() or "."
    root = os.path.abspath(root)

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

    return jsonify({"ok": True, "out_path": out_path})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
