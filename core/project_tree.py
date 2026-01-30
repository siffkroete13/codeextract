import os

def build_project_tree(root: str, ignore_dirs: set[str]) -> str:
    lines = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in ignore_dirs and not d.startswith(".")
        ]

        rel = os.path.relpath(dirpath, root)
        level = 0 if rel == "." else rel.count(os.sep) + 1
        indent = "  " * level

        if rel != ".":
            lines.append(f"{indent}{os.path.basename(dirpath)}/")

        for f in sorted(filenames):
            lines.append(f"{indent}  {f}")

    return "\n".join(lines)