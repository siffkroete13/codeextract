from typing import Optional
from tree_sitter import Parser
from tree_sitter_javascript import javascript

from core.model import (
    FileAnalysis,
    FunctionItem,
    ClassItem,
    MethodItem,
)


def analyze_js_file(path: str) -> Optional[FileAnalysis]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        lines = source.splitlines()
        parser = Parser()
        parser.set_language(javascript)

        tree = parser.parse(bytes(source, "utf8"))
        root = tree.root_node

        analysis = FileAnalysis(
            path=path,
            language="javascript",
            source_lines=lines,
        )

        for node in root.children:
            # function foo() {}
            if node.type == "function_declaration":
                name_node = node.child_by_field_name("name")
                if name_node:
                    analysis.functions.append(
                        FunctionItem(
                            name=source[name_node.start_byte:name_node.end_byte],
                            lineno_start=node.start_point[0] + 1,
                            lineno_end=node.end_point[0] + 1,
                            type="function",
                        )
                    )

            # class Foo { ... }
            elif node.type == "class_declaration":
                name_node = node.child_by_field_name("name")
                if not name_node:
                    continue

                cls = ClassItem(
                    name=source[name_node.start_byte:name_node.end_byte],
                    lineno_start=node.start_point[0] + 1,
                    lineno_end=node.end_point[0] + 1,
                    methods=[],
                )

                body = node.child_by_field_name("body")
                if body:
                    for item in body.children:
                        # method() {}
                        if item.type == "method_definition":
                            name_node = item.child_by_field_name("name")
                            if name_node:
                                cls.methods.append(
                                    MethodItem(
                                        name=source[name_node.start_byte:name_node.end_byte],
                                        lineno_start=item.start_point[0] + 1,
                                        lineno_end=item.end_point[0] + 1,
                                        type="method",
                                    )
                                )

                analysis.classes.append(cls)

        if not analysis.functions and not analysis.classes:
            return None

        return analysis

    except Exception:
        return None
