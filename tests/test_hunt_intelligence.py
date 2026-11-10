from pathlib import Path

from dnocer.intelligence.hunt.discovery import discover_project
from dnocer.intelligence.hunt.logic_analyzer import detect_logic_issues
from dnocer.intelligence.hunt.risk_detector import detect_risks


def create_project(tmp_path: Path, code: str):
    (tmp_path / "sample.py").write_text(code, encoding="utf-8")
    return discover_project(tmp_path)


def test_detects_eval(tmp_path):
    project = create_project(
        tmp_path,
        """
def calculate(value):
    return eval(value)
""",
    )

    findings = detect_risks(tmp_path, project["files"])

    assert any(finding["code"] == "HUNT-DYNAMIC-EXECUTION" for finding in findings)


def test_detects_mutable_default(tmp_path):
    project = create_project(
        tmp_path,
        """
def add_item(item, items=[]):
    items.append(item)
    return items
""",
    )

    findings = detect_risks(tmp_path, project["files"])

    assert any(finding["code"] == "HUNT-MUTABLE-DEFAULT" for finding in findings)


def test_detects_shell_execution(tmp_path):
    project = create_project(
        tmp_path,
        """
import subprocess

subprocess.run("echo hello", shell=True)
""",
    )

    findings = detect_risks(tmp_path, project["files"])

    assert any(finding["code"] == "HUNT-SHELL-EXECUTION" for finding in findings)


def test_detects_constant_condition(tmp_path):
    project = create_project(
        tmp_path,
        """
def check():
    if True:
        return "yes"
""",
    )

    findings = detect_logic_issues(tmp_path, project["files"])

    assert any(finding["code"] == "HUNT-CONSTANT-CONDITION" for finding in findings)


def test_detects_division_by_zero(tmp_path):
    project = create_project(
        tmp_path,
        """
def calculate():
    return 100 / 0
""",
    )

    findings = detect_logic_issues(tmp_path, project["files"])

    assert any(finding["code"] == "HUNT-DIVISION-BY-ZERO" for finding in findings)


def test_detects_unreachable_code(tmp_path):
    project = create_project(
        tmp_path,
        """
def calculate():
    return 10
    print("unreachable")
""",
    )

    findings = detect_logic_issues(tmp_path, project["files"])

    assert any(finding["code"] == "HUNT-UNREACHABLE-CODE" for finding in findings)
