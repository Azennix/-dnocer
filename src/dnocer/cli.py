import re

import typer
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from dnocer.core import (
    apply_ai_fix,
    apply_fix,
    ask_ai,
    console,
    display_findings,
    fix_preview,
    project_context,
    project_root,
    propose_ai_fix,
    read_history,
    run_tests,
    scan,
    undo,
)
from dnocer.intelligence.failure_analyzer import investigate_failure
from dnocer.intelligence.hunt.investigator import investigate_project

app = typer.Typer(
    name="dnocer",
    help="Scan, explain, test, safely repair, remember, and undo.",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        from dnocer.branding import print_banner

        print_banner(console)
        console.print("\n[dim]Use 'dnocer --help' to explore commands.[/]")


def consent():
    """Ask before sending selected project context to DNOCER Cloud."""
    console.print(
        Panel(
            "DNOCER Cloud AI Privacy Notice:\n\n"
            "Selected source-code excerpts and your question will be "
            "sent to DNOCER Cloud for AI investigation. The cloud "
            "service may process this information through its configured "
            "AI provider.\n\n"
            "Review the selected project context before continuing. "
            "Do not send secrets, credentials, personal information, "
            "customer data, or code you are not authorized to share.",
            border_style="magenta",
        )
    )
    return Confirm.ask(
        "Send selected project excerpts to DNOCER Cloud?",
        default=False,
    )


@app.command("scan")
def scan_cmd(
    path: str = typer.Argument("."),
    ai: bool = typer.Option(False, "--ai"),
):
    root = project_root(path)
    use_ai = ai and consent()

    findings, scan_id, review = scan(root, use_ai)
    display_findings(root, findings, scan_id, review)

    if ai and not use_ai:
        console.print("[yellow]AI skipped; local scan completed.[/]")


def analyze_test_result(code, output):
    """Extract test counts, pytest failure evidence, and warning evidence."""
    result = {
        "status": {
            0: "PASSED",
            5: "RUNNER UNAVAILABLE",
            6: "NO TESTS FOUND",
            124: "TIMEOUT",
        }.get(code, "FAILED"),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "warnings": 0,
        "warning_details": [],
        "failure_details": [],
    }

    summary_pattern = re.compile(
        r"(\d+)\s+(passed|failed|error|errors|skipped|warnings?|xfailed|xpassed)"
    )

    for count_text, label in summary_pattern.findall(output):
        count = int(count_text)
        label = label.lower()

        if label == "passed":
            result["passed"] += count
        elif label == "failed":
            result["failed"] += count
        elif label in ("error", "errors"):
            result["errors"] += count
        elif label == "skipped":
            result["skipped"] += count
        elif label.startswith("warning"):
            result["warnings"] += count

            # Parse unittest execution summaries.
    unittest_run = re.search(
        r"\bRan\s+(\d+)\s+tests?\b",
        output,
        re.IGNORECASE,
    )

    if unittest_run:
        total = int(unittest_run.group(1))

        unittest_failures = re.search(
            r"\bfailures=(\d+)",
            output,
            re.IGNORECASE,
        )
        unittest_errors = re.search(
            r"\berrors=(\d+)",
            output,
            re.IGNORECASE,
        )
        unittest_skipped = re.search(
            r"\bskipped=(\d+)",
            output,
            re.IGNORECASE,
        )

        result["failed"] = int(unittest_failures.group(1)) if unittest_failures else 0
        result["errors"] = int(unittest_errors.group(1)) if unittest_errors else 0
        result["skipped"] = int(unittest_skipped.group(1)) if unittest_skipped else 0

        result["passed"] = max(
            0,
            total - result["failed"] - result["errors"] - result["skipped"],
        )

    # Keep warning lines as evidence; do not infer a root cause from the text alone.
    warning_pattern = re.compile(
        r"(Warning|DeprecationWarning|PendingDeprecationWarning|"
        r"FutureWarning|ResourceWarning|UserWarning)",
        re.IGNORECASE,
    )
    for line in output.splitlines():
        if warning_pattern.search(line):
            cleaned = line.strip()
            if cleaned and cleaned not in result["warning_details"]:
                result["warning_details"].append(cleaned)

            # Successful test runs must not produce failure details.
    if code == 0:
        return result

    # Pytest's short summary contains the canonical test node IDs.
    failure_ids = re.findall(
        r"(?m)^FAILED\s+(.+?)(?:\s+-\s+.*)?$",
        output,
    )

    # Pytest failure sections begin with lines such as:
    # ______________________________ test_name ______________________________
    section_pattern = re.compile(r"(?m)^_{3,}.*?_{3,}\s*$")
    sections = section_pattern.split(output)

    failure_index = 0
    for section in sections:
        if not section.strip():
            continue

        lines = section.splitlines()
        location = None
        exception = None

        for line in lines:
            stripped = line.strip()

            # Handles both tests/file.py:12: and tests\\file.py:12: formats.
            location_match = re.search(
                r"([^\r\n]*?\.py):(\d+):(?:\s*(.*))?$",
                stripped,
            )
            if location_match and location is None:
                location = {
                    "file": location_match.group(1).strip(),
                    "line": int(location_match.group(2)),
                }

            if stripped.startswith("E   "):
                exception = stripped[4:].strip()

        # A section is a real failure block only when pytest supplied
        # source-location or assertion/error evidence.
        if location is None and exception is None:
            continue

        test_id = (
            failure_ids[failure_index]
            if failure_index < len(failure_ids)
            else "Unknown test"
        )

        result["failure_details"].append(
            {
                "test": test_id,
                "location": location,
                "exception": exception or "Failure details unavailable",
                "evidence": section.strip()[-3000:],
            }
        )
        failure_index += 1

    return result


def analyze_coverage(output):
    """Extract file-level and total coverage from pytest-cov output."""

    coverage = {
        "files": [],
        "total": None,
    }

    pattern = re.compile(r"^\s*(.+?)\s+(\d+)\s+(\d+)\s+(\d+)%\s*(.*)$")

    for line in output.splitlines():
        match = pattern.match(line)

        if not match:
            continue

        file_name, statements, missed, percent, missing = match.groups()

        item = {
            "file": file_name.strip(),
            "statements": int(statements),
            "missed": int(missed),
            "coverage": int(percent),
            "missing": missing.strip(),
        }

        if item["file"] == "TOTAL":
            continue

        file_path = item["file"].replace("\\", "/").lower()

        if (
            "/tests/" in f"/{file_path}"
            or file_path.startswith("tests/")
            or file_path.endswith("conftest.py")
            or "/test_" in file_path
        ):
            continue

        coverage["files"].append(item)

        if coverage["files"]:
            total_statements = sum(item["statements"] for item in coverage["files"])
            total_missed = sum(item["missed"] for item in coverage["files"])

            percentage = (
                round(((total_statements - total_missed) / total_statements) * 100)
                if total_statements
                else 100
            )

            coverage["total"] = {
                "file": "TOTAL",
                "statements": total_statements,
                "missed": total_missed,
                "coverage": percentage,
                "missing": "",
            }

    return coverage


@app.command("test")
def test_cmd(
    path: str = typer.Argument("."),
    ai: bool = typer.Option(False, "--ai"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    root = project_root(path)
    code, output = run_tests(root)
    analysis = analyze_test_result(code, output)
    coverage = analyze_coverage(output)

    table = Table(title="DNOCER TEST INTELLIGENCE")
    table.add_column("Metric", style="cyan")
    table.add_column("Result", style="white")

    table.add_row("Status", analysis["status"])
    table.add_row("Passed", str(analysis["passed"]))
    table.add_row("Failed", str(analysis["failed"]))
    table.add_row("Errors", str(analysis["errors"]))
    table.add_row("Skipped", str(analysis["skipped"]))
    table.add_row("Warnings", str(analysis["warnings"]))
    if coverage["files"]:
        coverage_table = Table(title="CODE COVERAGE INTELLIGENCE")

        coverage_table.add_column("File", style="cyan")
        coverage_table.add_column("Coverage", justify="right")
        coverage_table.add_column("Missed", justify="right")
        coverage_table.add_column("Uncovered Lines", style="yellow")

        for item in coverage["files"]:
            coverage_table.add_row(
                item["file"],
                f"{item['coverage']}%",
                str(item["missed"]),
                item["missing"] or "-",
            )

        if coverage["total"]:
            total = coverage["total"]

            coverage_table.add_section()
            coverage_table.add_row(
                "[bold]TOTAL[/]",
                f"[bold]{total['coverage']}%[/]",
                str(total["missed"]),
                "-",
            )

        console.print(
            Panel(
                coverage_table,
                title="COVERAGE ANALYSIS",
                border_style="cyan",
            )
        )

    console.print(
        Panel(
            table,
            title="PROJECT TEST ANALYSIS",
            border_style="green" if code == 0 else "red",
        )
    )

    if analysis["warning_details"]:
        console.print(
            Panel(
                "\n".join(analysis["warning_details"][:10]),
                title="WARNING ANALYSIS",
                border_style="yellow",
            )
        )

    if analysis["failure_details"]:
        console.print(
            Panel(
                f"Detected {len(analysis['failure_details'])} failure detail(s).",
                title="FAILURE INTELLIGENCE",
                border_style="red",
            )
        )

        for index, failure in enumerate(analysis["failure_details"], 1):
            location = failure["location"]
            investigation = investigate_failure(failure)

            location_text = (
                f"{location['file']}:{location['line']}"
                if location
                else "Location unavailable"
            )

            failure_body = (
                f"[cyan]TEST[/]  {failure['test']}\n"
                f"[cyan]LOCATION[/]  {location_text}\n"
                f"[red]EXCEPTION[/]  {failure['exception']}\n"
                f"[dim]EVIDENCE[/]\n{failure['evidence'][-1500:]}"
            )

            console.print(
                Panel(
                    failure_body,
                    title=f"FAILURE {index:02d}",
                    border_style="red",
                )
            )

            investigation_body = (
                f"[cyan]TYPE[/]  {investigation['type']}\n"
                f"[cyan]DIAGNOSIS[/]  {investigation['diagnosis']}\n"
                f"[cyan]REASON[/]  {investigation['reason']}\n"
                f"[cyan]RECOMMENDATION[/]  {investigation['recommendation']}\n"
                f"[cyan]CONFIDENCE[/]  {investigation['confidence']}"
            )

            if "actual" in investigation:
                investigation_body += (
                    f"\n[green]ACTUAL VALUE[/]  {investigation['actual']}"
                    f"\n[yellow]EXPECTED VALUE[/]  {investigation['expected']}"
                )

            console.print(
                Panel(
                    investigation_body,
                    title="ROOT CAUSE INVESTIGATION",
                    border_style=(
                        "green" if investigation["evidence_based"] else "yellow"
                    ),
                )
            )

    if verbose:
        console.print(
            Panel(
                output[-12000:] or "No test output available.",
                title="RAW TEST OUTPUT",
                border_style="cyan",
            )
        )

    if ai:
        if consent():
            review = ask_ai(
                "Analyze these test results. Separate confirmed facts "
                "from hypotheses. Explain warnings and failures, identify "
                "evidence-based likely causes, and recommend debugging steps. "
                "Do not invent root causes or modify files.\n\n" + output[-14000:],
                project_context(root),
            )
            console.print(
                Panel(
                    review,
                    title="AI TEST INVESTIGATION",
                    border_style="magenta",
                )
            )
        else:
            console.print("[yellow]AI analysis skipped.[/]")

    if analysis["status"] != "PASSED":
        raise typer.Exit(code=1)


def parse_hunt_findings(ai_report: str) -> list[dict]:
    if not ai_report:
        return []

    lines = ai_report.splitlines()
    findings = []
    current = None
    section = None

    for line in lines:
        clean = re.sub(r"^\s*#{1,6}\s*", "", line).strip()

        problem_match = re.match(r"^\d+\.\s*PROBLEM\s*$", clean, re.IGNORECASE)

        if problem_match:
            if current and current.get("problem"):
                findings.append(current)

            current = {
                "problem": "",
                "where": "",
                "why": "",
                "impact": "",
                "fix": "",
                "confidence": "Unknown",
            }
            section = "problem"
            continue

        if current is None:
            continue

        heading_match = re.match(
            r"^\d+\.\s*(WHERE|WHY|IMPACT|FIX)\s*$",
            clean,
            re.IGNORECASE,
        )

        if heading_match:
            section = heading_match.group(1).lower()
            continue

        confidence_match = re.match(
            r"^\*{0,2}CONFIDENCE\*{0,2}\s*:\s*(.*)",
            clean,
            re.IGNORECASE,
        )

        if confidence_match:
            current["confidence"] = confidence_match.group(1).strip()
            section = None
            continue

        if section and clean:
            current[section] += ("\n" if current[section] else "") + clean

    if current and current.get("problem"):
        findings.append(current)

    return findings


@app.command("hunt")
def hunt_cmd(
    path: str = typer.Argument("."),
    ai: bool = typer.Option(False, "--ai"),
):
    root = project_root(path)

    use_ai = ai and consent()

    console.print(
        Panel(
            "Starting DNOCER Deep Code Investigation...",
            title="HUNT INTELLIGENCE",
            border_style="cyan",
        )
    )

    try:
        report = investigate_project(root, use_ai=use_ai)
    except Exception as exc:  # noqa: BLE001
        # CLI boundary: report unexpected investigation failures cleanly.
        console.print(
            Panel(
                str(exc),
                title="HUNT INVESTIGATION ERROR",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    findings = parse_hunt_findings(report["ai_report"])

    # Use static findings when AI findings are unavailable.
    if not findings:
        for item in report["findings"]:
            findings.append(
                {
                    "problem": item["message"],
                    "where": f"{item['file']}:{item['line']}",
                    "why": item["evidence"],
                    "impact": item["severity"],
                    "fix": item["recommendation"],
                    "confidence": item["confidence"],
                }
            )

    if not findings:
        console.print(
            Panel(
                "No important problems were identified.",
                title="DNOCER HUNT REPORT",
                border_style="green",
            )
        )
        console.print("[dim]Hunt completed. No project files were modified.[/]")
        return

    console.print(
        Panel(
            f"[cyan]PROJECT FILES:[/] "
            f"{report['project']['file_count']}\n"
            f"[cyan]PROBLEMS FOUND:[/] {len(findings)}",
            title="DNOCER HUNT REPORT",
            border_style="cyan",
        )
    )

    while True:
        console.print("\n[bold cyan]PROBLEMS DETECTED[/]\n")

        for index, finding in enumerate(findings, 1):
            console.print(f"  [red]{index}.[/] [bold white]{finding['problem']}[/]")

        console.print("\n[dim]Enter a problem number to open it.[/]")
        console.print("[dim]Enter 0 to exit.[/]")

        choice = Prompt.ask(
            "Select problem",
            default="0",
        )

        if not choice.isdigit():
            console.print("[yellow]Enter a valid number.[/]")
            continue

        selected = int(choice)

        if selected == 0:
            break

        if selected < 1 or selected > len(findings):
            console.print("[yellow]Problem number not found.[/]")
            continue

        finding = findings[selected - 1]

        details = (
            f"[bold white]PROBLEM[/]\n"
            f"{finding['problem']}\n\n"
            f"[blue]WHERE[/]\n"
            f"{finding['where'] or 'Not available'}\n\n"
            f"[blue]WHY[/]\n"
            f"{finding['why'] or 'Not available'}\n\n"
            f"[yellow]IMPACT[/]\n"
            f"{finding['impact'] or 'Not available'}\n\n"
            f"[blue]FIX[/]\n"
            f"{finding['fix'] or 'Not available'}\n\n"
            f"[green]CONFIDENCE:[/] "
            f"{finding['confidence']}"
        )

        console.print(
            Panel(
                details,
                title=f"PROBLEM {selected:02d}",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        Prompt.ask(
            "[blue]Press Enter to return to problems[/]",
            default="",
        )

    console.print("[dim]Hunt completed. No project files were modified.[/]")


def offer_ai_repair(root, finding):
    """Generate, review and apply one AI repair."""

    try:
        proposal = propose_ai_fix(root, finding)

    except Exception as exc:  # noqa: BLE001
        # Skip this finding if AI investigation fails; continue the workflow.

        console.print(f"[yellow]AI REPAIR SKIPPED[/] {finding['file']} — {exc}")
        return "skipped"

    console.print(
        Panel(
            proposal["reason"],
            title="AI REPAIR REASON",
            border_style="cyan",
        )
    )

    console.print(
        Panel(
            Syntax(
                proposal["diff"],
                "diff",
                theme="monokai",
                line_numbers=False,
            ),
            title="PROPOSED CODE CHANGE",
            border_style="magenta",
        )
    )

    if not Confirm.ask(
        "Approve this exact AI repair?",
        default=False,
    ):
        console.print("[yellow]AI repair skipped.[/]")
        return "skipped"

    try:
        change_id = apply_ai_fix(root, finding, proposal)

        console.print(f"[green]AI FIXED[/] {finding['file']} | Change ID: {change_id}")
        return "applied"

    except Exception as exc:  # noqa: BLE001
        # Report this repair failure without terminating the CLI.
        console.print(f"[red]AI REPAIR FAILED[/] {finding['file']} — {exc}")
        return "failed"


@app.command("fix")
def fix_cmd(
    path: str = typer.Option(".", "--path", "-p"),
    issue: int | None = typer.Argument(None, min=1),
    all_fixes: bool = typer.Option(False, "--all"),
    ai: bool = typer.Option(False, "--ai"),
):
    if all_fixes and issue is not None:
        raise typer.BadParameter("Use either an issue number or --all, not both.")

    if not all_fixes and issue is None and not ai:
        raise typer.BadParameter("Select an issue number or use --all.")

    root = project_root(path)
    use_ai = ai and consent()

    if ai and not use_ai:
        console.print(
            "[yellow]AI repair cancelled. Only normal safe repairs are available.[/]"
        )
    findings, _, _ = scan(root)

    if not findings:
        console.print("[green]No issues found.[/]")
        return

    if issue is not None:
        if issue > len(findings):
            raise typer.BadParameter(f"Only {len(findings)} findings found.")

        candidates = [findings[issue - 1]]

    else:
        # Ruff applies a selected rule to the entire file.
        # Therefore, process each file/rule combination only once.
        candidates = []
        seen = set()

        for finding in findings:
            key = (finding["file"], finding["code"])

            if key not in seen:
                seen.add(key)
                candidates.append(finding)

    applied = 0
    skipped = 0
    failed = 0

    console.print(
        Panel(
            f"Repair candidates: {len(candidates)}",
            title="DNOCER FIX",
            border_style="cyan",
        )
    )

    for index, finding in enumerate(candidates, 1):
        if not finding.get("fixable"):
            if use_ai:
                result = offer_ai_repair(root, finding)

                if result == "applied":
                    applied += 1
                elif result == "failed":
                    failed += 1
                else:
                    skipped += 1

            else:
                console.print(
                    f"[yellow]SKIPPED[/] {finding['file']} "
                    f"— {finding['code']}: No safe automatic fix."
                )
                skipped += 1

            continue

        proposal, error = fix_preview(root, finding)

        if error:
            if use_ai:
                result = offer_ai_repair(root, finding)

                if result == "applied":
                    applied += 1
                elif result == "failed":
                    failed += 1
                else:
                    skipped += 1

            else:
                console.print(f"[yellow]SKIPPED[/] {finding['file']} — {error}")
                skipped += 1

            continue

        console.print(
            Panel(
                proposal["diff"],
                title=(f"PROPOSED FIX {index}: {finding['file']} / {finding['code']}"),
                border_style="cyan",
            )
        )

        if not Confirm.ask(
            "Approve this exact repair?",
            default=False,
        ):
            console.print("[yellow]Repair skipped.[/]")
            skipped += 1
            continue

        try:
            change_id = apply_fix(root, finding, proposal)

            console.print(f"[green]FIXED[/] {finding['file']} | Change ID: {change_id}")
            applied += 1

        except Exception as exc:  # noqa: BLE001
            # Record this failure and continue processing remaining findings.
            console.print(f"[red]FAILED[/] {finding['file']} | {exc}")
            failed += 1

    console.print(
        Panel(
            f"[green]Applied:[/] {applied}\n"
            f"[yellow]Skipped:[/] {skipped}\n"
            f"[red]Failed:[/] {failed}\n\n"
            "Run dnocer test to validate the project.\n"
            "Use dnocer undo to reverse the latest repair.",
            title="FIX SUMMARY",
            border_style="green" if failed == 0 else "yellow",
        )
    )


@app.command("auto")
def auto_cmd(
    path: str = typer.Argument("."),
    ai: bool = typer.Option(False, "--ai"),
):
    root = project_root(path)

    # AI privacy permission
    use_ai = ai and consent()

    if ai and not use_ai:
        console.print("[yellow]AI automation cancelled.[/]")
        raise typer.Exit()

    MAX_ROUNDS = 20
    MAX_REPAIRS = 50

    applied = 0
    skipped = 0
    failed = 0
    rolled_back = 0
    processed = set()

    console.print(
        Panel(
            "DNOCER iterative repair engine\n"
            f"Mode: {'AI + Ruff' if use_ai else 'Ruff only'}\n"
            "Every repair requires individual approval.\n"
            "Automatic test validation and rollback enabled.",
            title="DNOCER AUTO",
            border_style="cyan",
        )
    )

    # ----------------------------------------------
    # BASELINE TEST VALIDATION
    # ----------------------------------------------

    console.print("\n[bold cyan]Running baseline tests...[/]")

    baseline_code, baseline_output = run_tests(root)

    if baseline_code != 0:
        console.print(
            Panel(
                baseline_output[-5000:],
                title="BASELINE TEST VALIDATION FAILED",
                border_style="red",
            )
        )

        console.print(
            "[red]AUTO stopped.[/] Fix existing test failures "
            "before running automatic repair."
        )
        raise typer.Exit(code=1)

    console.print(
        "[green]Baseline tests passed. Automatic regression detection is active.[/]"
    )

    # ----------------------------------------------
    # VALIDATE AND ROLLBACK ONE REPAIR
    # ----------------------------------------------

    def validate_repair(change_id):

        nonlocal applied, rolled_back, failed

        console.print("\n[cyan]Running tests after repair...[/]")

        test_code, test_output = run_tests(root)

        if test_code == 0:
            console.print("[green]VALIDATION PASSED[/] Repair retained.")
            applied += 1
            return True

        console.print(
            Panel(
                test_output[-5000:],
                title="NEW TEST FAILURE DETECTED",
                border_style="red",
            )
        )

        console.print("[bold red]Automatically undoing the latest repair...[/]")

        rollback_result = undo(root, change_id)

        if rollback_result.startswith("Restored"):
            rolled_back += 1

            console.print(f"[green]AUTOMATIC ROLLBACK SUCCESSFUL[/]\n{rollback_result}")

            console.print("[cyan]Verifying project after rollback...[/]")

            verify_code, verify_output = run_tests(root)

            if verify_code == 0:
                console.print("[green]ROLLBACK VERIFIED. Baseline tests pass again.[/]")
            else:
                console.print(
                    Panel(
                        verify_output[-5000:],
                        title="ROLLBACK VERIFICATION FAILED",
                        border_style="red",
                    )
                )
                failed += 1

                console.print("[bold red]AUTO stopped for manual investigation.[/]")
                raise typer.Exit(code=1)

        else:
            failed += 1

            console.print(
                Panel(
                    rollback_result,
                    title="AUTOMATIC ROLLBACK FAILED",
                    border_style="red",
                )
            )

            console.print(
                "[bold red]AUTO stopped. Manual investigation is required.[/]"
            )
            raise typer.Exit(code=1)

        return False

    # ----------------------------------------------
    # ITERATIVE REPAIR ENGINE
    # ----------------------------------------------

    for round_number in range(1, MAX_ROUNDS + 1):
        if applied + rolled_back >= MAX_REPAIRS:
            console.print("[yellow]Maximum repair limit reached.[/]")
            break

        console.print(f"\n[bold cyan]Repair round {round_number}[/]")

        findings, _, _ = scan(root)

        if not findings:
            console.print("[green]No remaining findings detected.[/]")
            break

        repair_made = False

        for index, finding in enumerate(findings, 1):
            finding_key = (
                finding.get("file"),
                finding.get("code"),
                finding.get("line"),
                finding.get("message"),
            )

            if finding_key in processed:
                continue

            processed.add(finding_key)

            console.print(
                f"\n[bold]Finding #{index}[/] {finding['code']} — {finding['file']}"
            )

            change_id = None

            # --------------------------------------
            # RUFF REPAIR
            # --------------------------------------

            if finding.get("fixable"):
                proposal, error = fix_preview(root, finding)

                if not error:
                    console.print(
                        Panel(
                            Syntax(
                                proposal["diff"],
                                "diff",
                                theme="monokai",
                            ),
                            title="RUFF PROPOSED REPAIR",
                            border_style="green",
                        )
                    )

                    approved = Confirm.ask(
                        "Approve this exact repair?",
                        default=False,
                    )

                    if not approved:
                        skipped += 1
                        continue

                    try:
                        change_id = apply_fix(root, finding, proposal)

                        console.print(
                            f"[green]RUFF REPAIR APPLIED[/] Change ID: {change_id}"
                        )

                    except Exception as exc:  # noqa: BLE001
                        # Keep AUTO running when an individual repair fails.
                        console.print(f"[red]RUFF REPAIR FAILED:[/] {exc}")
                        failed += 1
                        continue

                else:
                    console.print(f"[yellow]Ruff preview unavailable:[/] {error}")

            # --------------------------------------
            # AI REPAIR
            # --------------------------------------

            if change_id is None and use_ai:
                result = offer_ai_repair(root, finding)

                if result == "failed":
                    failed += 1
                    continue

                if result != "applied":
                    skipped += 1
                    continue

                # Retrieve the change ID created by AI repair.
                history = read_history(root)

                if not history or history[0]["status"] != "APPLIED":
                    console.print(
                        "[red]Could not identify the AI repair "
                        "in history. AUTO stopped.[/]"
                    )
                    failed += 1
                    raise typer.Exit(code=1)

                change_id = history[0]["id"]

            elif change_id is None:
                skipped += 1
                continue

            # --------------------------------------
            # AUTOMATIC TEST VALIDATION
            # --------------------------------------

            repair_made = True

            passed = validate_repair(change_id)

            if passed:
                console.print("[cyan]Repair accepted. Rescanning project...[/]")
            else:
                console.print(
                    "[yellow]Repair rolled back. Continuing with remaining findings.[/]"
                )

            break

        # ------------------------------------------
        # ITERATIVE RESCAN
        # ------------------------------------------

        if repair_made:
            continue

        console.print("[yellow]No additional approved repairs in this round.[/]")
        break

    # ----------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------

    console.print(
        Panel(
            f"[green]Applied and validated:[/] {applied}\n"
            f"[yellow]Skipped:[/] {skipped}\n"
            f"[red]Failed:[/] {failed}\n"
            f"[magenta]Automatically rolled back:[/] {rolled_back}\n\n"
            "Run dnocer scan to inspect remaining findings.\n"
            "Use dnocer history to review repairs.\n"
            "Use dnocer undo to reverse retained changes.",
            title="DNOCER AUTO SUMMARY",
            border_style="cyan",
        )
    )


@app.command("undo")
def undo_cmd(
    path: str = typer.Argument("."),
    change_id: str | None = typer.Option(
        None, "--change-id", help="Undo a specific change by ID."
    ),
    last: bool = typer.Option(False, "--last", help="Undo the latest applied change."),
):
    root = project_root(path)

    # Prevent conflicting options.
    if last and change_id:
        console.print("[red]Use either --last or --change-id, not both.[/]")
        raise typer.Exit(code=1)

    # Retrieve repair history.
    history = read_history(root)

    if not history:
        console.print("[yellow]No DNOCER repair history found.[/]")
        raise typer.Exit()

    # --------------------------------------------------
    # SELECT CHANGE
    # --------------------------------------------------

    selected = None

    if change_id:
        selected = next(
            (item for item in history if item["id"] == change_id),
            None,
        )

        if selected is None:
            console.print("[red]Change ID not found.[/]")
            raise typer.Exit(code=1)

    elif last:
        selected = next(
            (item for item in history if item["status"] == "APPLIED"),
            None,
        )

        if selected is None:
            console.print("[yellow]No applied changes to undo.[/]")
            raise typer.Exit()

    else:
        # Interactive history.
        console.print(
            Panel(
                "Select a repair to undo.",
                title="DNOCER REPAIR HISTORY",
                border_style="yellow",
            )
        )

        available = []

        for item in history:
            status = item["status"]

            status_color = "green" if status == "APPLIED" else "dim"

            console.print(
                f"\n[{status_color}]{status}[/{status_color}]"
                f"\n  Number: {len(available) + 1 if status == 'APPLIED' else '-'}"
                f"\n  File: {item['file']}"
                f"\n  Issue: {item['code']}"
                f"\n  Change ID: {item['id']}"
                f"\n  Date: {item['created_at']}"
            )

            if status == "APPLIED":
                available.append(item)

        if not available:
            console.print("[yellow]No applied changes available to undo.[/]")
            raise typer.Exit()

        selection = typer.prompt(
            "\nEnter repair number to undo (0 to cancel)",
            type=int,
            default=0,
        )

        if selection == 0:
            console.print("[yellow]Undo cancelled.[/]")
            raise typer.Exit()

        if selection < 1 or selection > len(available):
            console.print("[red]Invalid selection.[/]")
            raise typer.Exit(code=1)

        selected = available[selection - 1]

    # --------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------

    console.print(
        Panel(
            f"[bold]File:[/] {selected['file']}\n"
            f"[bold]Issue:[/] {selected['code']}\n"
            f"[bold]Change ID:[/] {selected['id']}\n"
            f"[bold]Created:[/] {selected['created_at']}\n"
            f"[bold]Status:[/] {selected['status']}\n\n"
            "[yellow]The original file will be restored from backup.[/]",
            title="UNDO CONFIRMATION",
            border_style="yellow",
        )
    )

    if not Confirm.ask(
        "Are you sure you want to undo this change?",
        default=False,
    ):
        console.print("[yellow]Undo cancelled.[/]")
        raise typer.Exit()

    # --------------------------------------------------
    # EXECUTE EXISTING SAFE UNDO ENGINE
    # --------------------------------------------------

    result = undo(root, selected["id"])

    if "marked UNDONE" in result:
        console.print(
            Panel(
                result,
                title="UNDO SUCCESSFUL",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                result,
                title="UNDO REFUSED",
                border_style="red",
            )
        )


@app.command("history")
def history_cmd(
    path: str = typer.Argument("."),
    change_id: str | None = typer.Option(
        None,
        "--change-id",
        help="View details of a specific repair.",
    ),
):

    root = project_root(path)
    rows = read_history(root)

    if not rows:
        console.print("[dim]No repair history yet.[/]")
        raise typer.Exit()

    # --------------------------------------------------
    # DETAILED CHANGE VIEW
    # --------------------------------------------------

    if change_id:
        selected = next(
            (row for row in rows if row["id"] == change_id),
            None,
        )

        if selected is None:
            console.print("[red]Change ID not found.[/]")
            raise typer.Exit(code=1)

        backup_path = root / ".dnocer" / selected["backup_file"]

        backup_status = (
            "[green]AVAILABLE[/]" if backup_path.is_file() else "[red]MISSING[/]"
        )

        status_color = "green" if selected["status"] == "APPLIED" else "yellow"

        details = (
            f"[bold]Change ID:[/] {selected['id']}\n"
            f"[bold]File:[/] {selected['file']}\n"
            f"[bold]Issue:[/] {selected['code']}\n"
            f"[bold]Created:[/] {selected['created_at']}\n"
            f"[bold]Status:[/] "
            f"[{status_color}]{selected['status']}[/{status_color}]\n"
            f"[bold]Backup:[/] {backup_status}\n"
            f"[bold]Verification:[/] {selected['verification']}\n"
            f"[bold]Original SHA256:[/] {selected['before_hash']}\n"
            f"[bold]Modified SHA256:[/] {selected['after_hash']}"
        )

        console.print(
            Panel(
                details,
                title="DNOCER REPAIR DETAILS",
                border_style="cyan",
            )
        )

        return

    # --------------------------------------------------
    # COMPLETE REPAIR HISTORY
    # --------------------------------------------------

    table = Table(title="DNOCER LONG-TERM REPAIR MEMORY")

    table.add_column("No.", justify="right")
    table.add_column("Change ID")
    table.add_column("Timestamp UTC")
    table.add_column("File")
    table.add_column("Rule")
    table.add_column("Status")
    table.add_column("Backup")

    for index, row in enumerate(rows, start=1):
        backup_path = root / ".dnocer" / row["backup_file"]

        backup_status = (
            "[green]Available[/]" if backup_path.is_file() else "[red]Missing[/]"
        )

        status_color = "green" if row["status"] == "APPLIED" else "yellow"

        table.add_row(
            str(index),
            row["id"],
            row["created_at"],
            row["file"],
            row["code"],
            f"[{status_color}]{row['status']}[/{status_color}]",
            backup_status,
        )

    console.print(table)

    console.print(
        "\n[dim]Use dnocer history --change-id ID to inspect an individual repair.[/]"
    )


@app.command("version")
def version_cmd():
    from dnocer.branding import print_banner

    print_banner(console)