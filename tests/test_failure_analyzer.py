from dnocer.intelligence.failure_analyzer import (
    analyze_assertion,
    investigate_failure,
)


def test_detects_wrong_expected_value():
    result = analyze_assertion("assert (2 + 2) == 5")

    assert result is not None
    assert result["actual"] == 4
    assert result["expected"] == 5
    assert result["confidence"] == "HIGH"


def test_detects_subtraction():
    result = analyze_assertion("assert 10 - 3 == 8")

    assert result["actual"] == 7
    assert result["expected"] == 8


def test_ignores_unsupported_expression():
    result = analyze_assertion("assert calculate_total() == 100")

    assert result is None


def test_unclassified_failure_is_honest():
    result = investigate_failure(
        {"exception": "ModuleNotFoundError: No module named 'example'"}
    )

    assert result["type"] == "UNCLASSIFIED FAILURE"
    assert result["evidence_based"] is False
