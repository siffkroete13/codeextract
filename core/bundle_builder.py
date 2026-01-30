# core/bundle_builder.py

def extract_lines(lines, start, end):
    return "\n".join(lines[start - 1:end])


def build_bundle(analyses, selection, out_path):
    out = []

    for fa in analyses:
        sel = selection.get(fa.path)
        if not sel:
            continue

        out.append(f"# FILE {fa.path}")

        # === SPRACHUNTERSCHEIDUNG ===
        if fa.language in ("javascript", "typescript", "wasm"):
            # JS/TS/WASM: IMMER ganzes File
            out.append("\n".join(fa.source_lines))
            continue

        # === PYTHON ===
        if sel is True:
            out.append("\n".join(fa.source_lines))
            continue

        for fn in fa.functions:
            if fn.name in sel.get("functions", []):
                out.append(
                    extract_lines(
                        fa.source_lines,
                        fn.lineno_start,
                        fn.lineno_end
                    )
                )

        for cls in fa.classes:
            wanted = sel.get("classes", {}).get(cls.name)
            if wanted is None:
                continue

            if wanted == "*":
                out.append(
                    extract_lines(
                        fa.source_lines,
                        cls.lineno_start,
                        cls.lineno_end
                    )
                )
            else:
                for m in cls.methods:
                    if m.name in wanted:
                        out.append(
                            extract_lines(
                                fa.source_lines,
                                m.lineno_start,
                                m.lineno_end
                            )
                        )

    # with open(out_path, "w", encoding="utf-8") as f:
        # f.write("\n\n".join(out))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(normalize("\n\n".join(out)))



def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines()]
    out = []
    empty = False
    for ln in lines:
        if ln == "":
            if not empty:
                out.append("")
            empty = True
        else:
            out.append(ln)
            empty = False
    return "\n".join(out).strip()
