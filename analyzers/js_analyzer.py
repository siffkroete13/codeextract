from typing import Optional
from core.model import FileAnalysis


def analyze_js_file(path: str) -> Optional[FileAnalysis]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        return FileAnalysis(
            path=path,
            language="javascript",
            source_lines=source.splitlines(),
            functions=[],
            classes=[],
        )

    except OSError:
        return None
