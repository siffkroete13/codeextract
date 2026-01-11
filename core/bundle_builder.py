from core.model import FileAnalysis

def extract_lines(lines, start, end):
    return "\n".join(lines[start - 1:end])

def build_bundle(analyses: list[FileAnalysis], selection, out_path):
    out = []

    for fa in analyses:
        sel = selection.get(fa.path)
        if not sel:
            continue

        out.append(f"# FILE {fa.path}")

        for fn in fa.functions:
            if fn.name in sel.get("functions", []):
                out.append(extract_lines(fa.source_lines, fn.lineno_start, fn.lineno_end))

        for cls in fa.classes:
            wanted = sel.get("classes", {}).get(cls.name)
            if wanted is None:
                continue

            if wanted == "*":
                out.append(extract_lines(fa.source_lines, cls.lineno_start, cls.lineno_end))
            else:
                for m in cls.methods:
                    if m.name in wanted:
                        out.append(extract_lines(fa.source_lines, m.lineno_start, m.lineno_end))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out))
