from pathlib import Path

from dnocer.core import ask_ai
from dnocer.intelligence.hunt.context_builder import build_hunt_context
from dnocer.intelligence.hunt.dependency_analyzer import analyze_dependencies
from dnocer.intelligence.hunt.discovery import discover_project
from dnocer.intelligence.hunt.logic_analyzer import detect_logic_issues
from dnocer.intelligence.hunt.risk_detector import detect_risks


def investigate_project(root: Path, use_ai: bool = False) -> dict:
    root = root.resolve()

    # 1. Discover project
    project = discover_project(root)
    files = project["files"]

    # 2. Detect risks and logic issues
    risks = detect_risks(root, files)
    logic = detect_logic_issues(root, files)

    findings = risks + logic

    # 3. Analyze dependencies
    dependencies = analyze_dependencies(root, files)

    # 4. Build selected source context
    context = build_hunt_context(
        root,
        files,
        findings,
        dependencies,
    )

    # 5. AI investigation
    ai_report = None

    if use_ai:
        question = """
You are DNOCER, an expert software bug investigator.

Carefully investigate the supplied project source.

Find genuine:
- Logic bugs
- Hidden bugs
- Authentication and validation problems
- Runtime errors
- Edge cases
- Cross-file problems

IMPORTANT:
Do not depend only on static analyzer findings.
Investigate the source code independently.

REPORT FORMAT:

DNOCER HUNT REPORT

For EVERY important finding, use exactly this structure:

1. PROBLEM
Explain what is wrong in simple English.

2. WHERE
Give the exact file path and line number.

3. WHY
Explain why the code causes this problem.

4. IMPACT
Explain what can happen because of this problem.

5. FIX
Give a practical solution.

CONFIDENCE: High / Medium / Low

RULES:
- Never invent bugs or line numbers.
- Use actual source-code evidence.
- Do not hide important findings just to keep the report short.
- Do not report harmless style issues.
- Avoid duplicate findings.
- Clearly distinguish confirmed bugs from possible risks.
- If no genuine problems are found, say so.
- Use simple English.
- Keep each explanation short and understandable.
- Prioritize the most important problems.
"""

        if not context["context"]:
            raise ValueError("No source context available for AI investigation.")

        ai_report = ask_ai(question, context["context"])

    return {
        "project": project,
        "risks": risks,
        "logic": logic,
        "findings": findings,
        "dependencies": dependencies,
        "context": context,
        "ai_report": ai_report,
    }
