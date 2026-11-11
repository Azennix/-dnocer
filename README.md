<div align="center">
  <img src="src/dnocer/assets/dnocer-logo.png" alt="DNOCER monochrome animal logo" width="150" />
  <h1>DNOCER</h1>
  <p><strong>Project Intelligence &amp; Safe Repair Companion</strong></p>
  <p>A developer tool by <strong>Azennix AI</strong></p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
  <p><strong>Evidence before assumptions · Approval before action · Verification before success</strong></p>
</div>DNOCER is a command-line developer companion that helps developers inspect software projects, understand problems, investigate selected risks, review test results, and examine proposed code repairs.

It combines traditional development tools with optional AI-assisted investigation. Its goal is to help developers understand and resolve problems—not to make them blindly depend on generated code.
The DNOCER approach: Understand the problem before changing code. Review a change before applying it. Verify the result afterwards.

Table of contents
- Why DNOCER
- What DNOCER does
- Design principles
- Installation
- Quick start
- Commands
- How the workflows work
- AI integration
- Safety model
- Architecture
- Technology stack
- Limitations
- Relationship with IRABRAIN
- Development and contributions
- Release information
Why DNOCER
Software development involves more than writing code. Developers regularly face:
- Syntax and runtime errors.
- Unexpected application behavior.
- Dependency and configuration problems.
- Linting and code-quality issues.
- Test failures and unclear root causes.
- Repetitive debugging work.
- Risky code modifications.
Finding the cause of a problem can take time, especially when a developer is still learning.

DNOCER brings several useful development workflows into one terminal interface. It aims to make problems easier to inspect and proposed changes easier to review.
What DNOCER does
DNOCER provides these workflows:
1. Scan a project and collect diagnostic findings.
2. Present findings in a structured format.
3. Explain detected problems using available information.
4. Investigate selected risky code patterns.
5. Run supported tests and summarize their results.
6. Prepare code-repair proposals.
7. Ask for approval before consequential repair actions.
8. Keep repair records and support rollback of recorded repairs.
DNOCER works alongside existing development tools. It does not replace your editor, debugger, compiler, test framework, or your own code review.
Design principles
Evidence before explanation
A diagnosis should be based on information the tool can actually observe, such as source locations, diagnostic output, parser results, lint results, test output, and error messages.

If the evidence only suggests a possible cause, DNOCER should not present that possibility as a confirmed fact.
Deterministic checks before AI
Where possible, DNOCER uses conventional tools for checks such as Python syntax parsing, lint diagnostics, and test execution.

AI is an optional investigation layer. It does not replace these checks.
Human approval before consequential changes
A repair proposal should be shown before a consequential file modification. The developer should be able to review the proposed change and decide whether to approve it.
System safety remains separate
The application enforces technical boundaries such as permitted paths, file validation, repair restrictions, and execution limits. User approval does not bypass these restrictions.
Verify the outcome
Generating or applying a repair does not prove that the problem is fixed. Run the relevant tests and inspect the resulting changes.
Local-first operation
Core diagnostic workflows are designed to run locally. AI-assisted operations are optional and require consent before selected project context is sent to the configured provider.
Installation
DNOCER is distributed as a Python package.

Requirements
- Python 3.11 or newer.
- Windows PowerShell, Command Prompt, or a compatible terminal.
- Internet access for package installation.
- An Anthropic API key only if you want to use supported AI-assisted features.
Install DNOCER:
python -m pip install dnocer
Verify the installation:
dnocer version
Check the available commands:
dnocer --help
If Windows cannot find the dnocer command, check that the Python Scripts directory is on your PATH, then reopen your terminal.
Quick start
1. Open PowerShell or another terminal.
2. Change to the root folder of the project you want to inspect.
3. Check that DNOCER is installed.
4. Run a scan.
Example:
cd path\to\your-project
dnocer scan .
To see the options for a command, use its help option:
dnocer scan --help
Commands
The current command-line interface provides these eight commands:
Command	What it does
dnocer scan	Scans a project and displays diagnostic findings.
dnocer test	Runs supported tests and analyzes the results.
dnocer hunt	Investigates selected risky code patterns.
dnocer fix	Reviews and applies supported repairs through the approval workflow.
dnocer auto	Coordinates supported diagnostic and repair workflows.
dnocer undo	Reverses a recorded repair where rollback information is available.
dnocer history	Displays recorded repair history.
dnocer version	Displays the installed version.


See all commands
dnocer --help
Scan a project
dnocer scan .
Run project tests
dnocer test .
Show more test output:
dnocer test . --verbose
Request optional AI-assisted test investigation:
dnocer test . --ai
Investigate risky patterns
dnocer hunt .
Request optional AI-assisted investigation:
dnocer hunt . --ai
Review repair options
dnocer fix --help
Run the supported automated workflow
dnocer auto .
View repair history
dnocer history .
Undo a recorded repair
dnocer undo .
Check the installed version
dnocer version
Tip: Command options can vary by release. Run dnocer <command> --help to see the options available in the version you have installed.

How the workflows work
1. Project scanning
Run:
dnocer scan .
The scan checks the selected project using supported diagnostic rules and presents findings in a structured way.

A finding may include:
- Issue title and severity.
- Diagnostic rule or code.
- File and line location.
- Description and possible impact.
- Recommended action and prevention guidance.
- Detection source and repair availability.
Scanning is intended to identify and explain findings. It is not the same as automatically repairing them.
2. Test intelligence
Run:
dnocer test .
DNOCER runs the supported test workflow and analyzes the output. Depending on the test runner output, it can identify passed tests, failed tests, errors, skipped tests, warnings, failure locations, and exception information.

A test run can have different outcomes, including tests passed, tests failed, test runner unavailable, no tests found, or execution timed out. These outcomes should not all be treated as the same kind of failure.

For additional output:
dnocer test . --verbose
AI-assisted investigation is optional:
dnocer test . --ai
3. Risk investigation
Run:
dnocer hunt .
HUNT investigates selected risky code patterns. The documented candidates include bare or broad exception handling, mutable default arguments, and related supported diagnostic patterns.

Optional AI-assisted review:
dnocer hunt . --ai
Treat AI-generated analysis as advice to review, not as a confirmed security or correctness finding.
4. Controlled repair
The repair workflow is designed to make changes reviewable.

The intended process is:
1. Identify a finding that has a supported repair.
2. Prepare a repair proposal.
3. Show the proposed change.
4. Ask the developer to approve it.
5. Apply the approved proposal.
6. Preserve the original file where supported.
7. Record the repair operation.
8. Make the recorded operation available for review or rollback.
The exact repair behavior depends on the diagnostic rule and supported repair mechanism. A generated proposal is not proof that the repair is correct.

Review the available options:
dnocer fix --help
5. Automated workflow
Run:
dnocer auto .
AUTO coordinates supported scanning and repair workflows. It does not mean unrestricted autonomous modification. Proposed repairs remain subject to the approval workflow.
6. Repair history and rollback
View recorded repair activity:
dnocer history .
Where rollback information is available, use:
dnocer undo .
Repair records can include information such as the change identifier, timestamp, file, diagnostic rule, repair status, and verification information.

Rollback is a recovery aid, not a replacement for source control or independent backups. Preserve the project's .dnocer state directory if you need its associated repair records and backups.
AI integration
DNOCER supports optional AI-assisted analysis through the Anthropic SDK.

AI may help provide additional explanations or investigate selected project information. It is not the authority on whether a file modification is safe or correct.

Important points:
- AI features are optional.
- Local diagnostic workflows can be used independently of AI.
- Ordinary local scans do not automatically mean project context is sent to an AI provider.
- AI-assisted operations require consent before selected project context is sent.
- Review the information being shared before approving it.
- Treat AI output as untrusted advice.
- Validate recommendations with appropriate tools and tests.
API key configuration
For supported AI features, configure the ANTHROPIC_API_KEY environment variable in your environment. Do not put API keys directly in source files or commit them to the repository.
Safety model
DNOCER separates two kinds of authorization.
Human authorization
This is the developer's decision to approve an action, such as:
- Approving a proposed repair.
- Allowing selected project context to be sent to an AI provider.
- Confirming a consequential operation.
System authorization
These are technical restrictions enforced by the application, such as:
- Project path boundaries.
- File validation.
- Syntax validation.
- Repair restrictions.
- Execution limits.
These two concepts must remain independent. User approval does not make a technically prohibited operation safe. Likewise, automation must not silently replace user approval where approval is required.
Important limitation
No diagnostic tool can guarantee that every bug will be found or every suggested repair will be correct. Developers remain responsible for reviewing changes and validating their applications.
Architecture
DNOCER separates its terminal interface from reusable diagnostic and repair functionality.
- CLI layer: Registers commands, handles arguments and user interaction, displays results, and coordinates workflows.
- Core layer: Provides shared project operations used by scanning, testing, repair, history, and rollback workflows.
- Intelligence layer: Adds structured investigation and optional AI-assisted analysis.
- External tool integration: Runs supported development tools and test runners where required.
- Local repair state: Stores repair-related records and backup information in the project-local .dnocer directory.
The CLI entry point is src/dnocer/cli.py. The exact internal module layout may evolve as the project develops.
Technology stack
Technology	Role
Python	Main implementation language
Typer	CLI command framework
Rich	Terminal presentation
Ruff	Supported Python linting and repair operations
pytest	Supported project test execution
SQLite	Local repair-history storage
Anthropic SDK	Optional AI-assisted analysis
setuptools	Python package building


The availability of optional tools depends on the project and local environment.
Limitations
DNOCER is not intended to be:
- A replacement for an IDE or debugger.
- A replacement for compilers or interpreters.
- A guarantee of bug-free or secure software.
- An unrestricted autonomous coding agent.
- A complete security scanner.
- A guarantee that every AI explanation is correct.
- A substitute for code review and testing.
Its capabilities depend on the implemented diagnostic rules, supported tools, project configuration, and available evidence.
Relationship with IRABRAIN
DNOCER and IRABRAIN are separate products under Azennix AI.
- DNOCER focuses on software project intelligence and controlled developer workflows.
- IRABRAIN focuses on helping people understand opportunities, develop capabilities, and execute broader personal or entrepreneurial goals.
Any future integration should be optional, documented, and consent-based. DNOCER should remain independent of IRABRAIN's core and self-development foundation.
Development and contributions
Contributions, bug reports, and practical feedback are welcome.

When reporting an issue, include:
- Your operating system and Python version.
- Your DNOCER version (dnocer version).
- The command you ran.
- The complete error output, with secrets removed.
- A short description of the project context.
Never include API keys, passwords, access tokens, or private project information in a public issue.
Release information
Field	Value
Product	DNOCER
Organization	Azennix AI
Version	1.0.0
Release	Initial major release
Interface	Command-line application
Primary language	Python


<div align="center">
  <p><strong>DNOCER</strong> · A developer tool by Azennix AI</p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
</div>