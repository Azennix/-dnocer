from __future__ import annotations
from dnocer.cloud.client import investigate as cloud_investigate
import ast
import difflib
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".dnocer",
    "dist",
    "build",
}


def project_root(path: str) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    return root


def db_connect(root: Path):
    state = root / ".dnocer"
    (state / "backups").mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(state / "memory.db")
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS scans(id TEXT PRIMARY KEY, created_at TEXT, issue_count INTEGER);
    CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY, scan_id TEXT, fingerprint TEXT,
      code TEXT, file TEXT, line INTEGER, message TEXT, occurrences INTEGER, last_seen TEXT);
    CREATE TABLE IF NOT EXISTS changes(id TEXT PRIMARY KEY, created_at TEXT, file TEXT, code TEXT,
      backup_file TEXT, before_hash TEXT, after_hash TEXT, status TEXT, verification TEXT);
    """)
    db.commit()
    return db


def python_files(root: Path):
    found = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            p = Path(current) / name
            if p.suffix == ".py" and p.stat().st_size <= 1_000_000:
                found.append(p)
    return sorted(found)


def run_ruff(root: Path):
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(root), "--output-format=json"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], str(exc)
    if proc.returncode not in (0, 1):
        return [], proc.stderr.strip() or "Ruff failed."
    try:
        raw = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"Invalid Ruff JSON: {exc}"
    results = []
    for item in raw:
        filename = Path(item.get("filename", "")).resolve()
        try:
            rel = filename.relative_to(root).as_posix()
        except ValueError:
            rel = str(filename)
        loc, fix = item.get("location") or {}, item.get("fix") or {}
        results.append(
            {
                "code": item.get("code") or "RUFF",
                "file": rel,
                "line": int(loc.get("row") or 1),
                "message": item.get("message") or "Ruff diagnostic",
                "severity": "ERROR",
                "fixable": bool(fix) and fix.get("applicability") == "safe",
                "category": "ruff",
            }
        )
    return results, None


def custom_findings(root: Path):
    results = []
    for path in python_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (UnicodeDecodeError, SyntaxError) as exc:
            results.append(
                {
                    "code": "PY-SYNTAX",
                    "file": rel,
                    "line": getattr(exc, "lineno", 1) or 1,
                    "message": str(exc),
                    "severity": "ERROR",
                    "fixable": False,
                    "category": "dnocer",
                }
            )
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                results.append(
                    {
                        "code": "BARE_EXCEPT",
                        "file": rel,
                        "line": node.lineno,
                        "message": "This handler catches every exception, including unexpected failures.",
                        "severity": "WARNING",
                        "fixable": False,
                        "category": "dnocer",
                    }
                )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defaults = list(node.args.defaults) + [
                    d for d in node.args.kw_defaults if d is not None
                ]
                for default in defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        results.append(
                            {
                                "code": "MUTABLE_DEFAULT_ARGUMENT",
                                "file": rel,
                                "line": default.lineno,
                                "message": "A mutable default object is shared between function calls.",
                                "severity": "ERROR",
                                "fixable": False,
                                "category": "dnocer",
                            }
                        )
    return results


def merge_findings(items):
    """Merge known aliases while preserving detector sources."""
    aliases = {
        "BARE_EXCEPT": "E722",
    }

    severity_rank = {
        "CRITICAL": 0,
        "ERROR": 1,
        "WARNING": 2,
        "INFO": 3,
    }

    merged = {}

    for item in items:
        original_code = item.get("code", "UNKNOWN")
        canonical_code = aliases.get(original_code, original_code)

        normalized_file = str(item.get("file", "")).replace("\\", "/").casefold()
        key = (normalized_file, int(item.get("line") or 1), canonical_code)

        if key not in merged:
            merged[key] = {
                **item,
                "code": canonical_code,
                "sources": [],
                "related_codes": [],
                "detectors": [],
            }

        entry = merged[key]

        category = item.get("category", "unknown")

        if category not in entry["sources"]:
            entry["sources"].append(category)

        if original_code not in entry["related_codes"]:
            entry["related_codes"].append(original_code)

        detector = f"{category} ({original_code})"

        if detector not in entry["detectors"]:
            entry["detectors"].append(detector)

        incoming = item.get("severity", "INFO").upper()
        current = entry.get("severity", "INFO").upper()

        if severity_rank.get(incoming, 99) < severity_rank.get(current, 99):
            entry["severity"] = incoming

        if original_code == canonical_code and item.get("message"):
            entry["message"] = item["message"]
            entry["fixable"] = bool(item.get("fixable"))

    for entry in merged.values():
        entry["sources"].sort()
        entry["related_codes"].sort()
        entry["detectors"].sort()

    return sorted(
        merged.values(),
        key=lambda item: (
            severity_rank.get(item.get("severity", "INFO").upper(), 99),
            item["file"].casefold(),
            item["line"],
            item["code"],
        ),
    )


def remember_scan(root, findings):
    db = db_connect(root)
    scan_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    now = datetime.now(UTC).isoformat()
    db.execute("INSERT INTO scans VALUES(?,?,?)", (scan_id, now, len(findings)))
    for f in findings:
        fp = hashlib.sha256(
            f"{f['code']}|{f['file']}|{f['line']}|{f['message']}".encode()
        ).hexdigest()[:20]
        old = db.execute(
            "SELECT occurrences FROM findings WHERE fingerprint=? ORDER BY id DESC LIMIT 1",
            (fp,),
        ).fetchone()
        count = old["occurrences"] + 1 if old else 1
        db.execute(
            "INSERT INTO findings(scan_id,fingerprint,code,file,line,message,occurrences,last_seen) VALUES(?,?,?,?,?,?,?,?)",
            (scan_id, fp, f["code"], f["file"], f["line"], f["message"], count, now),
        )
    db.commit()
    db.close()
    return scan_id


def explain_local(f):
    """Return the stable four-field explanation structure."""

    data = {
        "E501": (
            "The line exceeds the configured length limit.",
            "Long lines are harder to read and maintain.",
            "Split the expression using parentheses or introduce a clearly named variable.",
            "Keep the configured line length in formatting and review checks.",
        ),
        "I001": (
            "The import block is not organized according to the project's lint rules.",
            "Inconsistent imports make dependencies harder to find and review.",
            "Use Ruff's import sorter and review the proposed changes.",
            "Run import sorting as part of the project's lint checks.",
        ),
        "E722": (
            "The code uses an exception handler without specifying an exception type.",
            "It can catch unexpected programming errors and interrupts, hiding the real failure.",
            "Catch only the exception types this operation is expected to handle.",
            "Test both expected exceptions and unexpected failures.",
        ),
        "B006": (
            "A mutable object is used as a function default.",
            "Separate function calls can unintentionally share the same object.",
            "Use None as the default and create a fresh object inside the function.",
            "Add a regression test that calls the function more than once.",
        ),
        "MUTABLE_DEFAULT_ARGUMENT": (
            "A mutable object is shared between function calls.",
            "Changes made during one call can affect later calls.",
            "Use None as the default and initialize a fresh object inside the function.",
            "Add a repeated-call regression test.",
        ),
        "PY-SYNTAX": (
            "Python could not parse this file.",
            "The interpreter cannot reliably load or execute the file until its syntax is corrected.",
            "Inspect the reported line and nearby brackets, indentation, quotes, and operators.",
            "Run a syntax check and the project's tests before committing.",
        ),
    }

    why, impact, fix, prevent = data.get(
        f.get("code"),
        (
            f.get("message", "The analyzer reported a code issue."),
            "This pattern may affect correctness, maintainability, or consistency.",
            "Review the exact code context and choose the smallest behavior-preserving correction.",
            "Add a focused regression test or project rule to prevent recurrence.",
        ),
    )

    return {
        "where": f"{f['file']}:{f['line']}",
        "why": why,
        "impact": impact,
        "fix": fix,
        "prevent": prevent,
    }


def project_context(root: Path, limit=24000):
    parts = []
    size = 0
    for p in python_files(root):
        try:
            body = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        chunk = f"\n--- {p.relative_to(root)} ---\n{body[:4500]}\n"
        if size + len(chunk) > limit:
            break
        parts.append(chunk)
        size += len(chunk)
    return "".join(parts)

def ask_ai(question, context):
    """Send user-approved project context to DNOCER Cloud."""
    return cloud_investigate(question, context)


def scan(root, use_ai=False):
    findings, error = run_ruff(root)
    if error:
        console.print(f"[yellow]Ruff unavailable or failed:[/] {error}")
    findings = merge_findings(findings + custom_findings(root))
    scan_id = remember_scan(root, findings)
    ai_text = (
        ask_ai(
            "Review these project excerpts. Summarize architecture clues, high-risk findings, root causes, and practical next steps. Do not invent findings.",
            project_context(root),
        )
        if use_ai
        else None
    )
    return findings, scan_id, ai_text


def display_findings(root, findings, scan_id, ai_text=None):
    console.print(
        Panel.fit(
            f"[bold white]DNOCER  /  PROJECT INTELLIGENCE[/]\n"
            f"[cyan]PROJECT[/]  {root}\n"
            f"[cyan]FILES[/]    {len(python_files(root))} Python files analyzed\n"
            f"[cyan]ISSUES[/]   {len(findings)} unique root causes\n"
            f"[dim]SCAN ID  {scan_id}[/]",
            border_style="cyan",
        )
    )

    if not findings:
        console.print(
            Panel(
                "[bold green]CLEAN SCAN[/]\nNo diagnostics were detected.",
                border_style="green",
            )
        )

    for index, finding in enumerate(findings, 1):
        explanation = explain_local(finding)
        titles = {
            "E501": "Line Too Long",
            "I001": "Import Organization",
            "E722": "Bare Exception Handler",
            "B006": "Mutable Default Argument",
            "MUTABLE_DEFAULT_ARGUMENT": "Mutable Default Argument",
            "PY-SYNTAX": "Python Syntax Error",
        }

        title = titles.get(finding["code"], "Code Diagnostic")
        what = finding.get("message", "The analyzer detected a code issue.")
        severity = finding.get("severity", "INFO").upper()
        style = {
            "CRITICAL": "bold red",
            "ERROR": "red",
            "WARNING": "yellow",
            "INFO": "blue",
        }.get(severity, "white")

        codes = ", ".join(finding.get("related_codes", [finding["code"]]))
        detectors = ", ".join(
            finding.get("detectors", [finding.get("category", "analyzer")])
        )
        fix_status = (
            "[green]SAFE FIX AVAILABLE[/]"
            if finding.get("fixable")
            else "[yellow]REVIEW REQUIRED[/]"
        )

        body = (
            f"[{style}]{severity}[/]  [bold white]{title}[/]\n"
            f"[dim]DIAGNOSTIC CODES[/]  {codes}\n"
            f"[cyan]WHERE[/]  {explanation['where']}\n"
            f"[cyan]WHAT HAPPENED[/]  {what}\n"
            f"[cyan]WHY IT MATTERS[/]  {explanation['why']}\n"
            f"[cyan]RECOMMENDED FIX[/]  {explanation['fix']}\n"
            f"[cyan]PREVENTION[/]  {explanation['prevent']}\n"
            f"[dim]DETECTED BY[/]  {detectors}\n"
            f"[dim]FIX STATUS[/]  {fix_status}"
        )
        console.print(
            Panel(
                body,
                title=f"ISSUE {index:02d}  /  {severity}",
                border_style=style,
                padding=(1, 2),
            )
        )

    if ai_text:
        console.print(
            Panel(
                ai_text,
                title="AI PROJECT REVIEW",
                border_style="magenta",
                padding=(1, 2),
            )
        )


def run_tests(root):
    """Run project tests and reject missing or empty test suites."""

    environment_candidates = [
        root / ".venv" / "Scripts" / "python.exe",
        root / "venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
        root / "venv" / "bin" / "python",
    ]

    project_python = next(
        (str(path) for path in environment_candidates if path.is_file()),
        sys.executable,
    )

    console.print(f"[cyan]Python environment:[/] {project_python}")

    def execute(command):
        try:
            return subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None
        except OSError as exc:
            return exc

    # First attempt: pytest with coverage.
    pytest_command = [
        project_python,
        "-m",
        "pytest",
        "-q",
        "--cov",
        "--cov-report=term-missing",
    ]

    result = execute(pytest_command)

    if result is None:
        return 124, "Test run timed out after 300 seconds."

    if isinstance(result, OSError):
        return 5, f"Could not start pytest: {result}"

    output = (result.stdout + "\n" + result.stderr).strip()

    # If pytest is missing, try unittest.
    if "No module named pytest" in output:
        result = execute(
            [
                project_python,
                "-m",
                "unittest",
                "discover",
                "-v",
            ]
        )

        if result is None:
            return 124, "Test run timed out after 300 seconds."

        if isinstance(result, OSError):
            return 5, f"Could not start unittest: {result}"

        output = (result.stdout + "\n" + result.stderr).strip()

        if re.search(r"\bRan\s+0\s+tests?\b", output, re.IGNORECASE):
            return 6, "NO TESTS FOUND: unittest discovered zero tests."

        if re.search(r"\bRan\s+\d+\s+tests?\b", output, re.IGNORECASE):
            return result.returncode, output or "Unittest completed."

        return 5, (
            "TEST RUNNER UNAVAILABLE: "
            "Could not confirm that unittest executed any tests.\n" + output
        )

    # Retry without coverage if pytest-cov is unavailable.
    if "unrecognized arguments: --cov" in output:
        console.print("[yellow]Coverage unavailable. Running normal pytest instead.[/]")

        result = execute([project_python, "-m", "pytest", "-q"])

        if result is None:
            return 124, "Test run timed out after 300 seconds."

        if isinstance(result, OSError):
            return 5, f"Could not start pytest: {result}"

        output = (result.stdout + "\n" + result.stderr).strip()

    # Pytest exit code 5 means no tests were collected.
    if result.returncode == 5 and "no tests ran" in output.lower():
        return 6, "NO TESTS FOUND: pytest collected zero tests.\n" + output

    return result.returncode, output or "Test command completed."


def propose_ai_fix(root: Path, finding: dict):
    """Generate one evidence-based, reviewable AI code repair."""

    root = root.resolve()
    target = (root / finding["file"]).resolve()

    # --------------------------------------------------
    # 1. TARGET FILE VALIDATION
    # --------------------------------------------------

    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Refusing to investigate files outside the project.")

    if not target.is_file():
        raise FileNotFoundError(f"Target file not found: {finding['file']}")

    if target.stat().st_size > 100_000:
        raise ValueError("AI repair refused: file exceeds 100 KB.")

    original_bytes = target.read_bytes()

    try:
        original = original_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("AI repair refused: target file is not valid UTF-8.")

    source_hash = hashlib.sha256(original_bytes).hexdigest()

    # --------------------------------------------------
    # 2. EXACT SOURCE LOCATION
    # --------------------------------------------------

    issue_line = finding.get("line")

    if not isinstance(issue_line, int) or issue_line < 1:
        raise ValueError("AI repair refused: invalid finding line number.")

    source_lines = original.splitlines()

    if issue_line > len(source_lines):
        raise ValueError("AI repair refused: reported line does not exist.")

    # Five lines before and after the reported location.
    start_line = max(1, issue_line - 5)
    end_line = min(len(source_lines), issue_line + 5)

    numbered_lines = []

    for number in range(start_line, end_line + 1):
        marker = ">>" if number == issue_line else "  "

        numbered_lines.append(f"{marker} {number:5}: {source_lines[number - 1]}")

    source_evidence = "\n".join(numbered_lines)

    exact_source_line = source_lines[issue_line - 1]

    # --------------------------------------------------
    # 3. FINDING EVIDENCE
    # --------------------------------------------------

    finding_evidence = {
        "file": finding.get("file"),
        "code": finding.get("code"),
        "line": issue_line,
        "column": finding.get("column"),
        "message": finding.get("message"),
    }

    context = f"""
TARGET FILE:
{finding["file"]}

STATIC ANALYSIS FINDING:
{json.dumps(finding_evidence, indent=2)}

EXACT REPORTED SOURCE LINE:
Line {issue_line}: {exact_source_line}

SOURCE LOCATION WITH SURROUNDING LINES:
{source_evidence}

COMPLETE TARGET FILE:
{original}

RELATED PROJECT CONTEXT:
{project_context(root, limit=12000)}
"""

    # --------------------------------------------------
    # 4. AI ROOT-CAUSE REPAIR INSTRUCTIONS
    # --------------------------------------------------

    question = """
You are DNOCER's AI code repair investigator.

Your responsibility is to identify and correct the actual
underlying problem, not simply silence static-analysis warnings.

You must investigate the supplied source evidence.

ROOT-CAUSE ANALYSIS:

1. Understand why the reported issue exists.
2. Identify intended behavior using the actual source code.
3. Examine relevant surrounding code and project context.
4. Distinguish confirmed facts from assumptions.
5. Correct the root cause whenever it can be established.

SEMANTIC CORRECTNESS:

1. Preserve intended application behavior.
2. Avoid introducing regressions.
3. Prefer precise exception handling.
4. Never replace bare except with except Exception merely
   to silence E722.
5. Handle only exceptions that the code is expected to handle.
6. Do not remove meaningful functionality to eliminate warnings.
7. Do not weaken tests merely to make them pass.

SOURCE LOCATION VERIFICATION:

1. Use the exact file, line and column supplied by DNOCER.
2. The source excerpt is authoritative evidence.
3. Verify that the actual source matches the diagnostic.
4. Never invent or reconstruct source code.
5. Never guess which line contains the problem.
6. Do not confuse findings from different locations.
7. The old_text must be copied exactly from the supplied
   original source.
8. The old_text must include the reported issue location.
9. The old_text must identify exactly one occurrence.
10. Never return an entire file as a replacement.

SAFE REPAIR:

1. Make the smallest correction that solves the actual problem.
2. Preserve unrelated behavior and formatting.
3. Do not modify unrelated code.
4. Do not change public APIs unnecessarily.
5. Consider relevant callers and tests.
6. Do not claim tests passed unless they were actually executed.
7. If the correct behavior cannot be established, do not guess.

IMPORTANT EXAMPLES:

For E722:
Do not blindly replace:
    except:

with:
    except Exception:

Determine which specific exception should be handled.

For F841:

1. Inspect how the assigned variable is used or intended to be used.
2. Determine whether the code is incomplete.
3. If a test response is assigned but never checked, consider
   adding a meaningful assertion.
4. If the assignment is genuinely unnecessary, consider removing
   only that assignment.
5. Never delete meaningful test or application behavior.
6. The proposed old_text must include the exact reported line.
7. Preserve indentation and surrounding code.
For E501:
Use the exact reported source line.
Split long expressions without changing their behavior.

UNSAFE REPAIR:

If you cannot confidently establish a safe correction,
return empty old_text and new_text.

Explain exactly what evidence is missing.

OUTPUT FORMAT:

Return ONLY valid JSON.

{
    "old_text": "Exact existing source code",
    "new_text": "Corrected source code",
    "reason": "Root cause, evidence, correction, expected behavior and uncertainty"
}

If unsafe:

{
    "old_text": "",
    "new_text": "",
    "reason": "UNSAFE: Explain why a safe correction cannot be established."
}

Do not include Markdown fences.
Do not include text outside the JSON.
Never fabricate source code or line references.
Never claim tests passed without execution.
"""

    # --------------------------------------------------
    # 5. REQUEST AI PROPOSAL
    # --------------------------------------------------

    report = ask_ai(question, context).strip()

    if report.startswith("```"):
        report = re.sub(r"^```(?:json)?\s*", "", report)
        report = re.sub(r"\s*```$", "", report)

    try:
        proposal = json.loads(report)

    except json.JSONDecodeError as exc:
        raise TypeError(
            f"AI returned invalid JSON: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno}). "
            f"Response preview: {report[:500]!r}"
        )

    if not isinstance(proposal, dict):
        raise TypeError(
            f"AI returned {type(proposal).__name__} instead of a JSON object. "
            f"Response preview: {report[:500]!r}"
        )

    old_text = proposal.get("old_text", "")
    new_text = proposal.get("new_text", "")
    reason = proposal.get("reason", "")

    if not isinstance(old_text, str):
        raise TypeError("AI returned an invalid old_text.")

    if not isinstance(new_text, str):
        raise TypeError("AI returned an invalid new_text.")

    if not isinstance(reason, str):
        raise TypeError("AI returned an invalid explanation.")

    # --------------------------------------------------
    # 6. UNSAFE PROPOSAL HANDLING
    # --------------------------------------------------

    if not old_text or not new_text or old_text == new_text:
        raise ValueError(reason or "AI could not establish a safe correction.")

        # --------------------------------------------------
    # 7. EXACT ORIGINAL SOURCE VALIDATION
    # --------------------------------------------------

    occurrences = [
        match.start()
        for match in re.finditer(
            re.escape(old_text),
            original,
        )
    ]

    if len(occurrences) != 1:
        raise ValueError("AI repair refused: original code is missing or ambiguous.")

    occurrence = occurrences[0]
    occurrence_end = occurrence + len(old_text)

    # Calculate exact byte-independent character offsets
    # for the reported source line.
    source_lines_with_endings = original.splitlines(keepends=True)

    issue_line_start = sum(
        len(line) for line in source_lines_with_endings[: issue_line - 1]
    )

    issue_line_end = issue_line_start + len(source_lines_with_endings[issue_line - 1])

    # The proposed original text must overlap the actual
    # reported source line.
    covers_issue = occurrence < issue_line_end and occurrence_end > issue_line_start

    if not covers_issue:
        replacement_start_line = original.count("\n", 0, occurrence) + 1

        replacement_end_line = original.count("\n", 0, occurrence_end) + 1

        raise ValueError(
            "AI repair refused: proposed replacement does not "
            f"cover reported line {issue_line}. "
            f"Replacement spans lines "
            f"{replacement_start_line}-{replacement_end_line}."
        )
    # --------------------------------------------------
    # 8. GENERATE EXACT DIFF
    # --------------------------------------------------

    updated = original.replace(old_text, new_text, 1)

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=finding["file"],
            tofile=finding["file"] + " (AI proposal)",
        )
    )

    if not diff:
        raise ValueError("AI proposal contains no changes.")

    # --------------------------------------------------
    # 9. RETURN VERIFIED PROPOSAL
    # --------------------------------------------------

    return {
        "file": finding["file"],
        "old_text": old_text,
        "new_text": new_text,
        "reason": reason,
        "diff": diff,
        "source_hash": source_hash,
    }


def apply_ai_fix(root: Path, finding: dict, proposal: dict):
    """Apply an approved AI proposal with backup and verification."""

    target = (root / finding["file"]).resolve()

    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise ValueError("Refusing to modify files outside the project.")

    if not target.is_file():
        raise FileNotFoundError("Target file no longer exists.")

    before = target.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()

    if before_hash != proposal.get("source_hash"):
        raise RuntimeError(
            "File changed after the AI proposal. Generate a new proposal."
        )

    original = before.decode("utf-8")
    old_text = proposal["old_text"]
    new_text = proposal["new_text"]

    if original.count(old_text) != 1:
        raise RuntimeError("Original code no longer matches the AI proposal.")

    updated = original.replace(old_text, new_text, 1)
    change = uuid.uuid4().hex[:12]

    state = root / ".dnocer"
    backup = state / "backups" / f"{change}_{target.name}.bak"

    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(before)

    try:
        # Validate before modifying the actual file.
        ast.parse(updated, filename=str(target))

        target.write_text(updated, encoding="utf-8")

        after = target.read_bytes()
        after_hash = hashlib.sha256(after).hexdigest()

        db = db_connect(root)

        try:
            db.execute(
                "INSERT INTO changes VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    change,
                    datetime.now(UTC).isoformat(),
                    finding["file"],
                    f"AI:{finding['code']}",
                    str(backup.relative_to(state)),
                    before_hash,
                    after_hash,
                    "APPLIED",
                    "AI proposal approved; Python syntax check passed",
                ),
            )
            db.commit()
        finally:
            db.close()

    except Exception:
        target.write_bytes(before)
        raise

    return change


def fix_preview(root, finding):
    """Create an exact, in-memory Ruff repair proposal."""

    root = root.resolve()
    target = (root / finding["file"]).resolve()

    if not finding.get("fixable"):
        return None, "No safe machine-applicable Ruff fix is available."

    try:
        target.relative_to(root)
    except ValueError:
        return None, "Refusing to edit outside the selected project."

    if not target.is_file():
        return None, "Target file does not exist."

    before = target.read_bytes()

    try:
        original = before.decode("utf-8")
    except UnicodeDecodeError:
        return None, "Refusing to repair a non-UTF-8 file."

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--fix",
                "--select",
                finding["code"],
                "--stdin-filename",
                str(target),
                "-",
            ],
            input=before,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"Ruff preview failed: {exc}"

    if result.returncode not in (0, 1):
        return None, result.stderr.decode("utf-8", errors="replace")

    after = result.stdout

    if not after or after == before:
        return None, "Ruff produced no repair. Rescan before fixing."

    try:
        updated = after.decode("utf-8")
        ast.parse(updated, filename=str(target))
    except (UnicodeDecodeError, SyntaxError) as exc:
        return None, f"Proposed repair failed syntax validation: {exc}"

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=finding["file"],
            tofile=finding["file"] + " (proposed)",
        )
    )

    if not diff:
        return None, "No reviewable diff available."

    return {
        "diff": diff,
        "before": before,
        "after": after,
        "source_hash": hashlib.sha256(before).hexdigest(),
    }, None


def apply_fix(root, finding, proposal):
    """Apply only the exact bytes contained in the approved proposal."""

    root = root.resolve()
    target = (root / finding["file"]).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Refusing to edit outside project.")

    if not target.is_file():
        raise FileNotFoundError("Target file no longer exists.")

    before = target.read_bytes()
    before_hash = hashlib.sha256(before).hexdigest()

    if before_hash != proposal.get("source_hash"):
        raise RuntimeError(
            "File changed after preview. Generate a new repair proposal."
        )

    if before != proposal.get("before"):
        raise RuntimeError("Original file does not match the approved proposal.")

    after = proposal.get("after")

    if not isinstance(after, bytes) or not after or after == before:
        raise ValueError("Invalid or empty repair proposal.")

    try:
        ast.parse(after.decode("utf-8"), filename=str(target))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ValueError(f"Approved repair failed syntax validation: {exc}") from exc

    change = uuid.uuid4().hex[:12]
    state = root / ".dnocer"
    backup = state / "backups" / f"{change}_{target.name}.bak"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(before)

    db = None

    try:
        target.write_bytes(after)

        after_hash = hashlib.sha256(target.read_bytes()).hexdigest()

        if after_hash != hashlib.sha256(after).hexdigest():
            raise RuntimeError("Written file does not match approved repair.")

        db = db_connect(root)

        db.execute(
            "INSERT INTO changes VALUES(?,?,?,?,?,?,?,?,?)",
            (
                change,
                datetime.now(UTC).isoformat(),
                finding["file"],
                finding["code"],
                str(backup.relative_to(state)),
                before_hash,
                after_hash,
                "APPLIED",
                "Exact approved Ruff proposal applied; syntax check passed",
            ),
        )

        db.commit()

    except Exception as exc:
        if db is not None:
            db.rollback()

        try:
            target.write_bytes(before)
        except OSError as restore_exc:
            raise RuntimeError(
                f"Repair failed and restoration failed. Backup preserved at: {backup}"
            ) from restore_exc

        raise RuntimeError(f"Repair failed; original file restored: {exc}") from exc

    finally:
        if db is not None:
            db.close()

    return change


def undo(root, change_id=None):
    db = db_connect(root)
    row = db.execute(
        "SELECT * FROM changes WHERE "
        + ("id=? AND " if change_id else "")
        + "status='APPLIED' ORDER BY created_at DESC LIMIT 1",
        (change_id,) if change_id else (),
    ).fetchone()
    if not row:
        db.close()
        return "No applied DNOCER change to undo."
    target = (root / row["file"]).resolve()
    backup = root / ".dnocer" / row["backup_file"]
    if not target.is_file() or not backup.is_file():
        db.close()
        return "Undo refused: target or backup missing."
    if hashlib.sha256(target.read_bytes()).hexdigest() != row["after_hash"]:
        db.close()
        return "Undo refused: file changed after DNOCER's fix; manual review required."
    target.write_bytes(backup.read_bytes())
    db.execute("UPDATE changes SET status='UNDONE' WHERE id=?", (row["id"],))
    db.commit()
    db.close()
    return f"Restored {row['file']} from backup. Change {row['id']} marked UNDONE."


def read_history(root):
    db = db_connect(root)
    rows = [
        dict(r)
        for r in db.execute("SELECT * FROM changes ORDER BY created_at DESC LIMIT 40")
    ]
    db.close()
    return rows
