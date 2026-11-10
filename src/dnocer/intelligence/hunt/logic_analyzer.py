import ast
from pathlib import Path


def detect_logic_issues(
    root: Path,
    discovered_files: list[dict],
) -> list[dict]:

    findings = []

    def add_finding(file, node, code, message, recommendation):
        findings.append(
            {
                "code": code,
                "file": file,
                "line": getattr(node, "lineno", 1),
                "severity": "MEDIUM",
                "message": message,
                "recommendation": recommendation,
                "confidence": "MEDIUM",
                "category": "LOGIC_RISK",
                "confirmed_bug": False,
                "evidence": ast.get_source_segment(source, node) or "",
            }
        )

    def inspect_block(statements, file):
        terminal_seen = False

        for statement in statements:
            if terminal_seen:
                add_finding(
                    file,
                    statement,
                    "HUNT-UNREACHABLE-CODE",
                    "Statement appears after an unconditional return, raise, break or continue.",
                    "Check whether this statement is unreachable or incorrectly indented.",
                )
                break

            if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                terminal_seen = True

            # Inspect nested control-flow blocks.
            if isinstance(statement, (ast.If, ast.For, ast.AsyncFor, ast.While)):
                inspect_block(statement.body, file)
                inspect_block(statement.orelse, file)

            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                inspect_block(statement.body, file)

            elif isinstance(statement, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                inspect_block(statement.body, file)
                inspect_block(statement.orelse, file)
                inspect_block(statement.finalbody, file)

                for handler in statement.handlers:
                    inspect_block(handler.body, file)

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
            # Constant conditions
            if (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Constant)
                and isinstance(node.test.value, bool)
            ):
                add_finding(
                    file_info["path"],
                    node.test,
                    "HUNT-CONSTANT-CONDITION",
                    f"Condition is always {node.test.value}.",
                    "Check whether the condition was intended to be dynamic.",
                )

            # Literal division by zero
            if isinstance(node, ast.BinOp) and (
                isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod))
                and isinstance(node.right, ast.Constant)
                and node.right.value == 0
            ):
                add_finding(
                    file_info["path"],
                    node,
                    "HUNT-DIVISION-BY-ZERO",
                    "Arithmetic operation uses a literal zero divisor.",
                    "Check the calculation and ensure the divisor is non-zero.",
                )

        # Inspect module-level statements and function bodies.
        inspect_block(tree.body, file_info["path"])

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inspect_block(node.body, file_info["path"])

    return findings
