import ast
from pathlib import Path
from typing import Any


def detect_risks(root: Path, discovered_files: list[dict]) -> list[dict[str, Any]]:
    """
    Detect potentially risky Python code patterns.

    Findings are risk candidates, not automatically confirmed bugs.
    """

    findings = []

    for file_info in discovered_files:
        if file_info["extension"] != ".py":
            continue

        path = root / file_info["path"]

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for node in ast.walk(tree):
            code = None
            message = None
            severity = "MEDIUM"
            recommendation = None

            # 1. Bare exception handling
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                code = "HUNT-BARE-EXCEPT"
                message = "Bare exception handler catches every exception."
                recommendation = "Catch specific exception types."

            # 2. Dangerous dynamic execution
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    code = "HUNT-DYNAMIC-EXECUTION"
                    message = f"Dynamic execution through {node.func.id}()."
                    severity = "HIGH"
                    recommendation = (
                        "Avoid dynamic execution of untrusted input. "
                        "Use a safer alternative."
                    )

            # 3. Mutable default arguments
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defaults = node.args.defaults + [
                    item for item in node.args.kw_defaults if item is not None
                ]

                for default in defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        code = "HUNT-MUTABLE-DEFAULT"
                        message = f"Mutable default argument in function '{node.name}'."
                        recommendation = (
                            "Use None as the default and create "
                            "the mutable object inside the function."
                        )
                        break

            # 4. Subprocess with shell=True
            elif isinstance(node, ast.Call):
                function = node.func

                is_subprocess = (
                    isinstance(function, ast.Attribute)
                    and isinstance(function.value, ast.Name)
                    and function.value.id == "subprocess"
                )

                if is_subprocess:
                    for keyword in node.keywords:
                        if (
                            keyword.arg == "shell"
                            and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is True
                        ):
                            code = "HUNT-SHELL-EXECUTION"
                            message = "Subprocess command uses shell=True."
                            severity = "HIGH"
                            recommendation = (
                                "Avoid shell execution with untrusted input. "
                                "Prefer argument lists and shell=False."
                            )
                            break

            # 5. Unsafe deserialization candidate
            elif isinstance(node, ast.Call):
                function = node.func

                if (
                    isinstance(function, ast.Attribute)
                    and function.attr == "loads"
                    and isinstance(function.value, ast.Name)
                    and function.value.id == "pickle"
                ):
                    code = "HUNT-UNSAFE-DESERIALIZATION"
                    message = "pickle.loads() can execute malicious payloads."
                    severity = "HIGH"
                    recommendation = "Never deserialize untrusted pickle data."

            if code:
                findings.append(
                    {
                        "code": code,
                        "file": file_info["path"],
                        "line": getattr(node, "lineno", 1),
                        "severity": severity,
                        "message": message,
                        "recommendation": recommendation,
                        "confidence": "HIGH",
                        "category": "STATIC_RISK",
                        "confirmed_bug": False,
                        "evidence": ast.get_source_segment(source, node) or "",
                    }
                )

    return findings
