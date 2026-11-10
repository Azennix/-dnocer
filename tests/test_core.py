from dnocer.core import custom_findings, explain_local, merge_findings


def test_merge_keeps_sources():
    rows = [
        {
            "code": "E722",
            "file": "x.py",
            "line": 4,
            "message": "bare",
            "category": "ruff",
        },
        {
            "code": "E722",
            "file": "x.py",
            "line": 4,
            "message": "bare",
            "category": "dnocer",
        },
    ]
    result = merge_findings(rows)
    assert len(result) == 1
    assert set(result[0]["sources"]) == {"ruff", "dnocer"}


def test_explanation_has_where_why_fix_prevent():
    assert set(explain_local({"code": "E722", "file": "x.py", "line": 4})) == {
        "where",
        "why",
        "impact",
        "fix",
        "prevent",
    }


def test_mutable_default_detected(tmp_path):
    (tmp_path / "sample.py").write_text(
        "def f(x=[]):\n    return x\n", encoding="utf-8"
    )
    assert any(
        x["code"] == "MUTABLE_DEFAULT_ARGUMENT" for x in custom_findings(tmp_path)
    )
