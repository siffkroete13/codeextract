import os
from typing import Dict, Set

from analyzers.python_analyzer import analyze_python_file
from analyzers.js_analyzer import analyze_js_file
from core.model import FileAnalysis


def scan_project(root: str, ignore_dirs: Set[str]) -> Dict[str, FileAnalysis]:
    root = os.path.abspath(root)
    result: Dict[str, FileAnalysis] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # Ignore-Verzeichnisse sauber entfernen
        dirnames[:] = [
            d for d in dirnames
            if d not in ignore_dirs and not d.startswith(".")
        ]

        for fname in filenames:
            full_path = os.path.join(dirpath, fname)

            analysis = None

            if fname.endswith(".py"):
                analysis = analyze_python_file(full_path)

            elif fname.endswith(".js"):
                analysis = analyze_js_file(full_path)

            # spaeter:
            # elif fname.endswith(".ts"):
            # elif fname.endswith(".wat"):

            if analysis:
                result[full_path] = analysis

    return result
