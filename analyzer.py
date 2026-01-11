import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."

FUNC_RE = re.compile(r"^(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.M)

def scan_py_files(root):
    result = {}
    for r, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(r, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        code = fh.read()
                except Exception:
                    continue

                funcs = []
                for m in FUNC_RE.finditer(code):
                    funcs.append({
                        "name": m.group(1),
                        "pos": m.start()
                    })

                if funcs:
                    result[path] = {
                        "code": code,
                        "funcs": funcs
                    }
    return result

def choose(items, label):
    print(f"\n{label}")
    for i, it in enumerate(items):
        print(f"[{i}] {it}")
    raw = input("Auswahl (z.B. 0,2 oder leer=alle): ").strip()
    if not raw:
        return items
    idx = {int(x) for x in raw.split(",") if x.isdigit()}
    return [it for i, it in enumerate(items) if i in idx]

def main():
    data = scan_py_files(ROOT)
    if not data:
        print("Keine Python-Dateien mit Funktionen gefunden.")
        return

    files = list(data.keys())
    sel_files = choose(files, "Dateien:")

    out = []

    for f in sel_files:
        entry = data[f]
        fnames = [x["name"] for x in entry["funcs"]]
        sel_funcs = choose(fnames, f"Funktionen in {f}:")

        out.append(f"\n# FILE {f}")

        for func in entry["funcs"]:
            if func["name"] in sel_funcs:
                out.append(f"\n# FUNC {func['name']}")
                out.append(entry["code"][func["pos"]:])

    with open("gpt_bundle.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))

    print("\n✅ gpt_bundle.txt erstellt")

if __name__ == "__main__":
    main()
