import ast
import operator

# Only allow safe arithmetic operations.
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


def safe_evaluate(node):
    """Evaluate a restricted arithmetic expression without eval()."""

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("Unsupported constant")

    if isinstance(node, ast.UnaryOp):
        value = safe_evaluate(node.operand)

        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return value

        raise ValueError("Unsupported unary operator")

    if isinstance(node, ast.BinOp):
        operation = SAFE_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported arithmetic operator")

        left = safe_evaluate(node.left)
        right = safe_evaluate(node.right)

        if isinstance(node.op, ast.Mult) and abs(left) * abs(right) > 10**12:
            raise ValueError("Calculation limit exceeded")

        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ValueError("Division by zero")

        return operation(left, right)

    raise ValueError("Expression is not safely evaluable")


def analyze_assertion(exception):
    """Investigate simple pytest equality assertion failures."""

    if not exception:
        return None

    expression = exception.strip()

    expression = expression.removeprefix("assert ")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return None

    comparison = tree.body

    if not isinstance(comparison, ast.Compare):
        return None

    if len(comparison.ops) != 1 or not isinstance(comparison.ops[0], ast.Eq):
        return None

    try:
        actual = safe_evaluate(comparison.left)
        expected = safe_evaluate(comparison.comparators[0])
    except (ValueError, TypeError, ArithmeticError, OverflowError):
        return None

    if actual == expected:
        return None

    return {
        "diagnosis": "Assertion expected value does not match actual result.",
        "actual": actual,
        "expected": expected,
        "reason": (
            f"The expression evaluates to {actual}, but the test expects {expected}."
        ),
        "recommendation": (
            "Review the expected value in the test or investigate "
            "whether the implementation produces the intended result."
        ),
        "confidence": "HIGH",
        "evidence_based": True,
    }


def investigate_failure(failure):
    """Produce an evidence-based investigation for a test failure."""

    exception = failure.get("exception", "")

    assertion = analyze_assertion(exception)

    if assertion:
        return {
            "type": "ASSERTION FAILURE",
            **assertion,
        }

    return {
        "type": "UNCLASSIFIED FAILURE",
        "diagnosis": "The failure requires further investigation.",
        "reason": (
            "Available evidence is insufficient for a reliable root-cause conclusion."
        ),
        "recommendation": (
            "Inspect the test, traceback, and relevant application code."
        ),
        "confidence": "NOT ESTABLISHED",
        "evidence_based": False,
    }
