<div align="center">
  <img src="src/dnocer/assets/dnocer-logo.png" alt="DNOCER animal logo" width="150" />
  <h1>DNOCER</h1>
  <p><strong>Project Intelligence &amp; Safe Repair Companion</strong></p>
  <p>A developer tool by <strong>Azennix AI</strong></p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
  <p>
    <strong>Evidence before assumptions · Approval before action · Verification before success</strong>
  </p>
# DNOCER

### Project Intelligence & Safe Repair Companion

**A product by Azennix AI**

> Your Companion. Your Capability. Your Control.

DNOCER is a command-line developer companion designed to help developers understand software problems, investigate potential root causes, inspect test failures, review code improvements, and maintain control over changes made to their projects.

It combines deterministic development tools with optional AI-assisted investigation.

Its central principle is simple:

**Understand the problem before changing the code. Review the change before applying it. Verify the result after applying it.**

---

## 1. Why DNOCER Exists

Software development involves more than writing code.

Developers regularly encounter:

- Syntax and runtime errors.
- Unexpected application behavior.
- Dependency and configuration problems.
- Linting and code-quality issues.
- Test failures.
- Unclear root causes.
- Repeated debugging workflows.
- Risky code modifications.

For experienced developers, identifying these problems can still consume considerable time.

For beginners and students, understanding why something failed can be even more difficult.

DNOCER aims to reduce the gap between encountering a problem and understanding how to resolve it.

It is designed to make developers more capable, rather than encourage blind dependence on generated code.

## 2. What DNOCER Does

DNOCER provides a collection of developer workflows through a terminal interface.

Its capabilities include:

1. Project scanning and diagnostic collection.
2. Structured issue reporting.
3. Local explanations of detected problems.
4. Optional AI-assisted investigation.
5. Risk-pattern identification.
6. Test execution and result analysis.
7. Reviewable repair proposals.
8. Approval-controlled modifications.
9. Repair history and rollback.

DNOCER works alongside existing development tools rather than attempting to replace them.

## 3. Core Design Principles

### Evidence before explanation

A diagnosis should be grounded in available evidence.

Examples include:

- Source file locations.
- Diagnostic rule identifiers.
- Parser results.
- Linter output.
- Test execution results.
- Error messages.

An explanation should not be presented as a confirmed fact when the evidence only supports a hypothesis.

### Deterministic before generative

DNOCER uses conventional development tools for checks where possible.

Examples include:

- Python syntax parsing.
- Ruff diagnostics.
- Existing test frameworks.

AI is an optional additional investigation layer, not a replacement for deterministic checks.

### Human authorization

DNOCER is designed around user control.

A repair proposal should be visible before a consequential file modification.

The user must decide whether to approve the proposed change.

### System authorization

Technical safety boundaries are separate from human approval.

The system determines which operations are technically permitted, which paths are within scope, and which validations are required.

User approval must not bypass technical safety restrictions.

### Verifiable outcomes

A suggested repair is not automatically a successful repair.

DNOCER distinguishes between proposing a change, applying it, and validating its outcome.

### Local-first operation

The core diagnostic workflow is designed to operate locally.

AI-assisted operations are optional and require explicit consent before selected project context is sent to the configured provider.

---

## 4. Command-Line Interface

DNOCER uses Typer for command handling and Rich for terminal presentation.

The CLI provides structured output, interactive confirmations, tables, panels, and diagnostic summaries.

The implemented command interface includes the following workflows.

| Command | Responsibility |
|---|---|
| `dnocer scan` | Analyze a project and display findings |
| `dnocer test` | Execute tests and analyze results |
| `dnocer hunt` | Investigate selected risky code patterns |
| `dnocer fix` | Preview and apply approved repairs |
| `dnocer auto` | Coordinate supported diagnostic and repair workflows |
| `dnocer undo` | Reverse a recorded repair |
| `dnocer history` | Display repair history |
| `dnocer version` | Display the installed version |
Use:

```powershell
dnocer --help
```

to inspect the commands registered in your installed version.

---

## 5. How the Workflows Operate

### 5.1 Project Scanning

```powershell
dnocer scan .
```

The scan workflow examines the selected project using supported diagnostic checks.

Its purpose is to identify problems and present findings in a structured format.

A finding can contain:

- Issue title.
- Severity.
- Diagnostic code.
- File and line location.
- Description.
- Explanation of impact.
- Recommended action.
- Prevention guidance.
- Detection source.
- Repair availability.

Scanning is intended to be diagnostic rather than an automatic repair operation.

### 5.2 Test Intelligence

```powershell
dnocer test .
```

DNOCER runs the supported project test workflow and analyzes the resulting output.

Its test analysis can extract:

- Passed tests.
- Failed tests.
- Errors.
- Skipped tests.
- Warnings.
- Available failure locations.
- Exception information.

The test workflow distinguishes execution outcomes rather than treating every unsuccessful run as an ordinary test failure.

Examples of important states include:

- Tests passed.
- Tests failed.
- Test runner unavailable.
- No tests found.
- Execution timed out.

Use verbose output when more execution detail is needed:

```powershell
dnocer test . --verbose
```

Optional AI investigation:

```powershell
dnocer test . --ai
```

### 5.3 Risk Investigation

```powershell
dnocer hunt .
```

Hunt identifies selected risky code patterns from the project's findings.

The implemented risk candidates include:

- Bare exception handling.
- Broad exception handling.
- Mutable default arguments.
- Selected related diagnostic patterns.

Optional AI-assisted review:

```powershell
dnocer hunt . --ai
```

AI investigation provides additional analysis. Its output should be treated as advisory rather than automatically confirmed.

### 5.4 Finding Explanation

```powershell
dnocer why . 1
```

This explains a finding using its position in the current scan results.

The local explanation presents:

- Where the issue occurs.
- Why it matters.
- Recommended correction.
- Prevention guidance.

Optional AI explanation:

```powershell
dnocer why . 1 --ai
```

### 5.5 Controlled Repair

DNOCER's repair workflow is designed around review and approval.

The intended sequence is:

1. Identify a repairable finding.
2. Generate a repair proposal.
3. Display the proposed changes.
4. Ask the user for approval.
5. Apply the approved proposal.
6. Preserve the original file.
7. Record the operation.
8. Allow the user to inspect or reverse the change.

The exact repair implementation depends on the diagnostic rule and supported repair mechanism.

A repair should never be considered successful merely because a suggestion was generated.

### 5.6 Automated Repair Workflow

```powershell
dnocer auto .
```

AUTO coordinates supported scanning and repair operations.

It is not intended to mean unrestricted autonomous modification.

Each proposed repair requires individual user approval.

The workflow is designed to preserve user control and make repair outcomes reviewable.

### 5.7 Repair History

```powershell
dnocer history .
```

DNOCER records repair information, including:

- Change identifier.
- Timestamp.
- File.
- Diagnostic rule.
- Repair status.
- Verification information.

This allows developers to review previously recorded repair operations.

### 5.8 Rollback

```powershell
dnocer undo .
```

Rollback uses retained repair information and backups to reverse recorded modifications.

Rollback is an important recovery mechanism, but users should still maintain their own project backups.

### 5.9 Version

```powershell
dnocer version
```

Displays the installed DNOCER version.

---

## 6. Internal Architecture

DNOCER separates its terminal interface from reusable diagnostic and repair functionality.

### CLI Layer

Responsible for:

- Command registration.
- Argument handling.
- User interaction.
- Approval prompts.
- Terminal output.
- Workflow coordination.

Primary implementation:

`src/dnocer/cli.py`

### Core Layer

Responsible for shared project operations and reusable functionality.

The core provides functionality used by workflows such as:

- Project scanning.
- Project context collection.
- Test execution.
- Repair proposal generation.
- Repair application.
- Repair history.
- Rollback.

Primary implementation:

`src/dnocer/core.py`

### Intelligence Layer

The intelligence components provide additional analysis beyond basic diagnostic collection.

Examples include:

- Failure investigation.
- Root-cause-oriented explanations.
- Optional AI-assisted analysis.

These components should distinguish available evidence from possible explanations.

### External Tool Integration

DNOCER integrates with development tools through Python subprocess execution where required.

For example, Ruff is used for supported Python diagnostics and repair operations.

Test execution is delegated to supported project test runners.

DNOCER does not replace those underlying tools.

### Local Repair State

Repair history and retained backups are maintained in project-local DNOCER state.

The `.dnocer` directory is used for repair-related records and backup information.

Users should preserve this directory when they need the associated rollback history.

---

## 7. AI Integration

DNOCER includes optional AI-assisted analysis through the Anthropic SDK.

AI may be used to provide additional explanations and investigation of project information.

The AI layer is not the authority for whether a file modification is safe.

Important principles:

- AI functionality is optional.
- Local diagnostic operations remain available independently of AI.
- Project context is not sent automatically merely because the user runs an ordinary local scan.
- AI-assisted commands display a consent notice.
- The user should inspect the information before agreeing to send it.
- AI output must be treated as untrusted advice.
- AI recommendations do not replace technical validation or user approval.

### API configuration

Set the provider key through the environment variable:

```text
ANTHROPIC_API_KEY
```

Never place API credentials directly inside source files or publish them in documentation.

---

## 8. Safety Model

DNOCER distinguishes two separate authorization concepts.

### Human Authorization

Human authorization represents the user's decision to approve an action.

Examples:

- Approving a repair.
- Authorizing selected project context to be sent to AI.
- Confirming a consequential operation.

### System Authorization

System authorization represents the technical restrictions enforced by the application.

Examples:

- Project path boundaries.
- File validation.
- Syntax validation.
- Repair restrictions.
- Execution limits.

These concepts must remain independent.

A user confirmation does not make an otherwise prohibited operation safe.

Similarly, system automation must not silently replace user approval where approval is required.

### Repair Integrity

A repair workflow should preserve:

- The original file.
- The proposed change.
- The approval decision.
- The resulting file.
- The recorded repair state.

DNOCER's exact-proposal repair mechanism is designed so that the bytes applied match the approved proposal, provided the source file has not changed since preview.

### Important limitation

No diagnostic tool can guarantee that every bug will be discovered or that every suggested repair is correct.

Developers remain responsible for reviewing changes and validating their applications.

---

## 9. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main implementation language |
| Typer | CLI command framework |
| Rich | Terminal presentation |
| Ruff | Supported Python linting and repair operations |
| pytest | Supported project test execution |
| SQLite | Local repair-history storage |
| Anthropic SDK | Optional AI-assisted analysis |
| setuptools | Python package building |

The exact behavior of optional development tools depends on their availability in the environment.

---

## 10. Installation

DNOCER is distributed as a Python package.

Requirements:

- Python 3.11 or newer.
- Windows PowerShell, CMD, or a compatible terminal.
- Required Python package dependencies.
- An optional Anthropic API key for AI-assisted operations.

Install from a built wheel:

```powershell
python -m pip install dnocer-1.0.0-py3-none-any.whl
```

Verify:

```powershell
dnocer version
dnocer --help
```

For development and testing, install the development dependencies separately.

---

## 11. Development Philosophy

DNOCER is intended to support developers at different experience levels.

For beginners, it should help explain what happened and where to investigate.

For independent developers, it should reduce repetitive diagnostic work.

For experienced developers, it should provide a structured workflow for examining findings and reviewing changes.

Its purpose is not to make developers dependent on automation.

Its purpose is to improve their ability to understand, diagnose, and maintain software.

---

## 12. Product Boundaries and Limitations

DNOCER should not be understood as:

- A replacement for an IDE.
- A replacement for a debugger.
- A replacement for compilers or interpreters.
- A guarantee of bug-free software.
- An unrestricted autonomous coding agent.
- A complete security scanner.
- A guarantee that every AI explanation is correct.
- A substitute for reviewing and testing code.

Its capabilities depend on the implemented diagnostic rules, supported tools, project configuration, and available evidence.

---

## 13. Relationship with IRABRAIN

DNOCER is an independent developer tool under Azennix AI.

IRABRAIN is a broader personal AI and adaptability product.

Their responsibilities should remain separate.

DNOCER focuses on software project intelligence and controlled development workflows.

IRABRAIN focuses on helping people understand opportunities, develop capabilities, and execute broader personal or entrepreneurial goals.

Any future integration should be optional, documented, and consent-based.

DNOCER should not duplicate IRABRAIN's core or self-development foundation.

---

## 14. Release Information

**Product:** DNOCER  
**Organization:** Azennix AI  
**Version:** 1.0.0  
**Release type:** Initial major release  
**Interface:** Command-line application  
**Primary implementation:** Python  

For detailed installation, command usage, safety policies, and release changes, refer to the accompanying documentation.

---

## 15. Final Principle

DNOCER is built around a simple development philosophy:

**Evidence before assumptions.  
Understanding before modification.  
Approval before consequential action.  
Verification before claiming success.  
Recovery when something goes wrong.**

DNOCER — Your Companion. Your Capability. Your Control.
<div align="center">
  <p><strong>DNOCER</strong> · A developer tool by Azennix AI</p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
</div>