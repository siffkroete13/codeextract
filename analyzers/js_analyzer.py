import re
from typing import Optional

from core.model import (
    FileAnalysis,
    FunctionItem,
    ClassItem,
    MethodItem,
)

# Einfache, robuste Patterns (Top-Level)
FUNC_RE = re.compile(r'^\s*function\s+([A-Za-z_$][\w$]*)\s*\(', re.M)
ARROW_RE = re.compile(r'^\s*const\s+([A-Za-z_$][\w$]*)\s*=\s*\(?.*?\)?\s*=>', re.M)
CLASS_RE = re.compile(r'^\s*class\s+([A-Za-z_$][\w$]*)\b', re.M)
METHOD_RE = re.compile(r'^\s*([A-Za-z_$][\w$]*)\s*\(', re.M)


def _line_no_from_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def analyze_js_file(path: str) -> Optional[FileAnalysis]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        lines = source.splitlines()

        analysis = FileAnalysis(
            path=path,
            language="javascript",
            source_lines=lines,
        )

        # functions: function foo() {}
        for m in FUNC_RE.finditer(source):
            ln = _line_no_from_pos(source, m.start())
            analysis.functions.append(
                FunctionItem(
                    name=m.group(1),
                    lineno_start=ln,
                    lineno_end=ln,
                    type="function",
                )
            )

        # functions: const foo = (...) => {}
        for m in ARROW_RE.finditer(source):
            ln = _line_no_from_pos(source, m.start())
            analysis.functions.append(
                FunctionItem(
                    name=m.group(1),
                    lineno_start=ln,
                    lineno_end=ln,
                    type="arrow",
                )
            )

        # classes + naive method scan inside class block
        for cm in CLASS_RE.finditer(source):
            cls_name = cm.group(1)
            start_ln = _line_no_from_pos(source, cm.start())

            # sehr einfache Block-Suche (reicht für Übersicht)
            brace_pos = source.find("{", cm.end())
            if brace_pos == -1:
                continue

            depth = 0
            end_pos = brace_pos
            for i in range(brace_pos, len(source)):
                if source[i] == "{":
                    depth += 1
                elif source[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end_pos = i
                        break

            end_ln = _line_no_from_pos(source, end_pos)

            cls = ClassItem(
                name=cls_name,
                lineno_start=start_ln,
                lineno_end=end_ln,
                methods=[],
            )

            class_body = source[brace_pos:end_pos]
            for mm in METHOD_RE.finditer(class_body):
                m_ln = _line_no_from_pos(source, brace_pos + mm.start())
                cls.methods.append(
                    MethodItem(
                        name=mm.group(1),
                        lineno_start=m_ln,
                        lineno_end=m_ln,
                        type="method",
                    )
                )

            analysis.classes.append(cls)

        if not analysis.functions and not analysis.classes:
            return None

        return analysis

    except Exception as e:
        print(f"JS analyzer error in {path}: {e}")
        return None
