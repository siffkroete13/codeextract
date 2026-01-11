import json
import os
from flask import Flask, render_template, request, jsonify

from analyzers.analyzer import scan_project, build_gpt_bundle

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

    ignore = default_ignore_dirs()
    analysis = scan_project(root, ignore_dirs=ignore)

    # Fuer UI: relative paths, damit es lesbar ist
    # (intern behalten wir absolute paths im analysis dict)
    ui_files = []
    for abs_path, info in analysis.items():
        rel = os.path.relpath(abs_path, root)
        ui_files.append({
            "abs": abs_path,
            "rel": rel,
            "items": info["items"],
        })

    ui_files.sort(key=lambda x: x["rel"].lower())

    return render_template("index.html", root=root, files=ui_files)

@app.post("/export")
def export_bundle():
    payload = request.get_json(force=True, silent=False)
    root = os.path.abspath(payload.get("root", "."))
    selection = payload.get("selection", {})

    ignore = default_ignore_dirs()
    analysis = scan_project(root, ignore_dirs=ignore)

    out_path = os.path.join(root, "gpt_bundle.txt")
    build_gpt_bundle(analysis, selection, out_path=out_path)

    return jsonify({"ok": True, "out_path": out_path})

@app.get("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    # Nur lokal!
    app.run(host="127.0.0.1", port=5000, debug=True)
