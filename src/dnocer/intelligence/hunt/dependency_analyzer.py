import ast
from collections import defaultdict
from pathlib import Path


def analyze_dependencies(
    root: Path,
    discovered_files: list[dict],
) -> dict:

    root = root.resolve()

    module_map = {}
    imports = []
    functions = defaultdict(list)
    calls = []

    # Build Python module map.
    for item in discovered_files:
        if item["extension"] != ".py":
            continue

        relative = Path(item["path"])
        parts = relative.with_suffix("").parts

        if parts and parts[0] == "src":
            parts = parts[1:]

        module = ".".join(parts)

        module = module.removesuffix(".__init__")

        module_map[module] = item["path"]

    # Analyze Python files.
    for item in discovered_files:
        if item["extension"] != ".py":
            continue

        path = root / item["path"]

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        parts = Path(item["path"]).with_suffix("").parts

        if parts and parts[0] == "src":
            parts = parts[1:]

        current_module = ".".join(parts)

        for node in ast.walk(tree):
            # Import relationships.
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "source": current_module,
                            "target": alias.name,
                            "line": node.lineno,
                        }
                    )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(
                        {
                            "source": current_module,
                            "target": node.module,
                            "line": node.lineno,
                            "level": node.level,
                        }
                    )

            # Function definitions.
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name].append(
                    {
                        "module": current_module,
                        "file": item["path"],
                        "line": node.lineno,
                        "async": isinstance(node, ast.AsyncFunctionDef),
                    }
                )

            # Function calls.
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id

                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr

                else:
                    continue

                calls.append(
                    {
                        "caller_file": item["path"],
                        "caller_module": current_module,
                        "function": name,
                        "line": node.lineno,
                        "candidates": functions.get(name, []),
                    }
                )

    # Resolve imports to discovered local modules.
    resolved_imports = []

    for item in imports:
        target = item["target"]

        if target in module_map:
            resolved_imports.append(
                {
                    **item,
                    "resolved_file": module_map[target],
                    "resolved": True,
                }
            )
        else:
            resolved_imports.append(
                {
                    **item,
                    "resolved_file": None,
                    "resolved": False,
                }
            )

    return {
        "module_count": len(module_map),
        "function_count": sum(len(v) for v in functions.values()),
        "import_count": len(imports),
        "call_count": len(calls),
        "modules": module_map,
        "imports": resolved_imports,
        "functions": dict(functions),
        "calls": calls,
    }
