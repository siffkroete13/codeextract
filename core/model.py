from dataclasses import dataclass, field
from typing import List, Optional, Literal

ItemType = Literal[
    "function",
    "async_function",
    "class",
    "method",
    "async_method",
    "wasm_export"
]

Language = Literal[
    "python",
    "javascript",
    "typescript",
    "wasm"
]

@dataclass
class MethodItem:
    name: str
    lineno_start: int
    lineno_end: int
    type: ItemType = "method"

@dataclass
class ClassItem:
    name: str
    lineno_start: int
    lineno_end: int
    methods: List[MethodItem] = field(default_factory=list)
    type: ItemType = "class"

@dataclass
class FunctionItem:
    name: str
    lineno_start: int
    lineno_end: int
    type: ItemType = "function"

@dataclass
class FileAnalysis:
    path: str                 # absolut
    language: Language
    source_lines: List[str]
    functions: List[FunctionItem] = field(default_factory=list)
    classes: List[ClassItem] = field(default_factory=list)
