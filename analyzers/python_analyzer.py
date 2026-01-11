import ast
from typing import Optional
from core.model import (
    FileAnalysis,
    FunctionItem,
    ClassItem,
    MethodItem,
)


def analyze_python_file(path: str) -> Optional[FileAnalysis]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        tree = ast.parse(source)
        lines = source.splitlines()

        analysis = FileAnalysis(
            path=path,
            language="python",
            source_lines=lines,
        )

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                analysis.functions.append(
                    FunctionItem(
                        name=node.name,
                        lineno_start=node.lineno,
                        lineno_end=node.end_lineno,
                        type="function",
                    )
                )

            elif isinstance(node, ast.AsyncFunctionDef):
                analysis.functions.append(
                    FunctionItem(
                        name=node.name,
                        lineno_start=node.lineno,
                        lineno_end=node.end_lineno,
                        type="async_function",
                    )
                )

            elif isinstance(node, ast.ClassDef):
                cls = ClassItem(
                    name=node.name,
                    lineno_start=node.lineno,
                    lineno_end=node.end_lineno,
                    methods=[],
                )

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        cls.methods.append(
                            MethodItem(
                                name=item.name,
                                lineno_start=item.lineno,
                                lineno_end=item.end_lineno,
                                type="method",
                            )
                        )
                    elif isinstance(item, ast.AsyncFunctionDef):
                        cls.methods.append(
                            MethodItem(
                                name=item.name,
                                lineno_start=item.lineno,
                                lineno_end=item.end_lineno,
                                type="async_method",
                            )
                        )

                analysis.classes.append(cls)

        if not analysis.functions and not analysis.classes:
            return None

        return analysis

    except (SyntaxError, OSError, UnicodeError):
        return None
