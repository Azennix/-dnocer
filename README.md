::: {align="center"}
`<img src="https://raw.githubusercontent.com/Azennix/dnocer/main/src/dnocer/assets/dnocer-logo.png" alt="DNOCER animal logo" width="150">`{=html}

# DNOCER

### Project Intelligence & Safe Repair Companion

**A product by Azennix AI**

*Your Companion. Your Capability. Your Control.*

**Evidence before assumptions · Approval before action · Verification
before success**
:::DNOCER is a command-line developer companion that helps developers
inspect software projects, understand diagnostic findings, investigate
selected risks, analyze test results, and review proposed code repairs.

It combines deterministic development tools with optional AI-assisted
investigation. DNOCER is designed to help developers understand and
control changes---not blindly accept generated code.
Core principle: Understand the problem before changing the code.
Review the change before applying it. Verify the result after applying
it.

Contents
- Why DNOCER exists
- What DNOCER does
- Design principles
- Installation
- Quick start
- Commands
- How the workflows operate
- Architecture
- AI integration
- Safety and authorization
- Technology stack
- Limitations
- Relationship with IRABRAIN
- Development
- Release information
Why DNOCER exists
Software developers regularly deal with:
- Syntax and runtime errors.
- Unexpected application behavior.
- Dependency and configuration problems.
- Linting and code-quality findings.
- Test failures and unclear failure locations.
- Repeated debugging workflows.
- Risky or difficult-to-review code modifications.
Finding the problem is only part of the work. Developers also need to
understand why it matters, decide what should change, and verify the
result.

DNOCER aims to make that workflow more structured and
understandable---especially for beginners and independent
developers---while keeping the developer in control.
What DNOCER does
DNOCER brings several project workflows into one terminal interface:
  Capability                          What it helps with
  Project scanning                    Collect supported diagnostics and
display findings

  Test intelligence                   Run supported tests and summarize
execution results

  Risk investigation                  Identify selected risky code
patterns

  AI-assisted investigation           Request additional analysis when
explicitly enabled

  Controlled repair                   Review proposed changes before
approving supported repairs

  Repair history                      Inspect recorded repair operations
Rollback                            Reverse recorded modifications when
retained recovery data is available
DNOCER works alongside existing development tools. It does not attempt
to replace an IDE, debugger, compiler, test framework, or developer
judgment.
Design principles
Evidence before explanation
A diagnosis should be grounded in available evidence, such as source
locations, diagnostic identifiers, parser results, linter output, test
results, and error messages.

A hypothesis should not be presented as a confirmed fact.
Deterministic before generative
DNOCER uses conventional development tools for supported checks wherever
possible. AI is an optional investigation layer, not a replacement for
deterministic diagnostics.
Human authorization
A repair proposal should be visible before a consequential file
modification. The user decides whether to approve the proposed change.
System authorization
Technical restrictions---such as permitted paths, validation rules, and
operation boundaries---remain separate from user approval. A user
confirmation must not bypass a technical safety restriction.
Verifiable outcomes
Generating a suggestion, applying a change, and validating the result
are different steps. A repair is not successful merely because a
proposal was generated or applied.
Local-first operation
Core diagnostic workflows are designed to run locally. AI-assisted
operations are optional and require consent before selected project
context is sent to the configured provider.
Installation
Requirements
- Python 3.11 or newer.
- Windows, Linux, or macOS.
- A compatible terminal.
Install from PyPI
python -m pip install dnocer
Verify the installation
dnocer version
dnocer --help
If the dnocer command is not found, check that the Python environment
in which you installed the package is active and that its scripts
directory is on your PATH.
Quick start
Open a terminal in the project you want to inspect.
1. See available commands
dnocer --help
2. Scan the current project
dnocer scan .
3. Run the supported test workflow
dnocer test .
4. Investigate selected risky patterns
dnocer hunt .
5. Review repair history
dnocer history .
6. Check the installed version
dnocer version
Start with dnocer --help for the options supported by your installed
release.
Commands
The current CLI registers these eight commands:
  Command                             Purpose
  dnocer scan                       Analyze a project and display
supported findings

  dnocer test                       Execute the supported test workflow
and analyze its output

  dnocer hunt                       Investigate selected risky code
patterns

  dnocer fix                        Preview and apply supported repairs
with approval

  dnocer auto                       Coordinate supported diagnostic and
repair workflows

  dnocer undo                       Reverse a recorded repair when
recovery data is available

  dnocer history                    Display recorded repair history
dnocer version                    Display the installed version
Use dnocer <command> --help to inspect the options for an individual
command.
How the workflows operate
Project scanning
dnocer scan .
The scan workflow examines the selected project using supported
diagnostic checks and presents findings in a structured format.

A finding may include:
- Issue title and severity.
- Diagnostic code.
- File and line location.
- Description and potential impact.
- Recommended action and prevention guidance.
- Detection source.
- Repair availability.
Scanning is intended to collect and report diagnostics rather than
silently modify project files.
Test intelligence
dnocer test .
The test workflow runs the supported project test process and analyzes
its output. Depending on the test runner and available output, analysis
may identify passed tests, failures, errors, skipped tests, warnings,
failure locations, and exception information.

The workflow distinguishes different execution outcomes, including a
successful run, failed tests, an unavailable test runner, no tests
found, and a timed-out execution.

Verbose output and optional AI investigation are available where
supported:
dnocer test . --verbose
dnocer test . --ai
Risk investigation
dnocer hunt .
Hunt examines selected risky patterns represented in the project's
findings. Implemented candidates include bare or broad exception
handling, mutable default arguments, and selected related diagnostic
patterns.

Optional AI-assisted review:
dnocer hunt . --ai
AI analysis is advisory. Review its reasoning against the actual source
and diagnostic evidence.
Controlled repair
The repair workflow is designed around review and approval:
1. Identify a repairable finding.
2. Generate a repair proposal.
3. Display the proposed change.
4. Ask the user for approval.
5. Apply the approved proposal.
6. Preserve the original file where supported.
7. Record the operation.
8. Make the recorded operation available for inspection or rollback
   where supported.
The exact behavior depends on the diagnostic rule and repair mechanism.
Review the proposal before approving it.
Automated workflow
dnocer auto .
AUTO coordinates supported scanning and repair operations. It does not
mean unrestricted autonomous modification. Proposed repairs require
individual user approval.
Repair history
dnocer history .
The history workflow displays recorded repair information, which may
include a change identifier, timestamp, file, diagnostic rule, repair
status, and verification information.
Rollback
dnocer undo .
Rollback uses retained repair information and backups to reverse
recorded modifications. Availability depends on the recorded state and
retained recovery data. Keep your own project backups as well.
Version
dnocer version
Displays the installed DNOCER version.
Architecture
DNOCER separates its terminal interface from reusable diagnostic and
repair functionality.
DNOCER
├── CLI layer
│   └── Commands, arguments, prompts, and terminal output
├── Core layer
│   └── Project operations, diagnostics, tests, and repair workflows
├── Intelligence layer
│   └── Failure investigation and optional AI-assisted analysis
├── External tool integration
│   └── Ruff and supported project test runners
└── Local repair state
    └── .dnocer records and retained backup information
CLI layer
Responsible for command registration, argument handling, user
interaction, approval prompts, terminal output, and workflow
coordination.

Primary implementation: src/dnocer/cli.py
Core layer
Provides shared project operations used by scanning, test execution,
repair proposal generation, repair application, history, and rollback.

Primary implementation: src/dnocer/core.py
Intelligence layer
Provides additional analysis beyond basic diagnostic collection,
including failure investigation and optional AI-assisted analysis. It
should distinguish evidence from possible explanations.
External tool integration
DNOCER uses existing development tools where appropriate. For example,
Ruff provides supported Python diagnostics, while test execution is
delegated to supported project test runners.
Local repair state
Repair history and retained backups are maintained in project-local
DNOCER state. The .dnocer directory contains repair-related records
and backup information. Preserve it if you need the associated rollback
history.
AI integration
DNOCER includes optional AI-assisted analysis through the Anthropic SDK.
AI may provide additional explanations or investigation of selected
project information.

Important principles:
- AI functionality is optional.
- Local diagnostic operations are available independently of AI.
- An ordinary local scan does not, by itself, mean project context is
  sent to an AI provider.
- AI-assisted workflows display a consent notice.
- Inspect the information before agreeing to send it.
- Treat AI output as untrusted advice.
- AI recommendations do not replace technical validation or user
  approval.
API key configuration
Set the ANTHROPIC_API_KEY environment variable in your terminal. For
PowerShell:
$env:ANTHROPIC_API_KEY = "your-api-key"
This sets the variable for the current PowerShell session. Use your
operating system's environment-variable settings or a secrets manager
for persistent configuration.

Never hard-code API credentials in source files or commit them to
version control.
Safety and authorization
DNOCER distinguishes two authorization concepts that must remain
independent.
Human authorization
Human authorization represents the user's decision to approve an action,
such as:
- Approving a repair.
- Authorizing selected project context to be sent to an AI provider.
- Confirming a consequential operation.
System authorization
System authorization represents technical restrictions enforced by the
application, such as:
- Project path boundaries.
- File validation.
- Syntax validation.
- Repair restrictions.
- Execution limits.
A user confirmation does not make a technically prohibited operation
safe. Similarly, system automation must not silently replace user
approval where approval is required.
Repair integrity
A repair workflow should preserve the original file, proposed change,
approval decision, resulting file, and recorded repair state.

DNOCER's exact-proposal repair mechanism is designed so that the bytes
applied match the approved proposal, provided the source file has not
changed since preview.
Technology stack
  Technology      Role
  Python          Main implementation language
Typer           CLI command framework
Rich            Terminal presentation
Ruff            Supported Python linting and repair operations
pytest          Supported project test execution
SQLite          Local repair-history storage
Anthropic SDK   Optional AI-assisted analysis
setuptools      Python package building

The exact behavior of optional development tools depends on their
availability and configuration in the environment.
Limitations
DNOCER should not be understood as:
- A replacement for an IDE or debugger.
- A replacement for compilers or interpreters.
- A guarantee that every bug will be detected.
- A guarantee that every suggested repair is correct.
- An unrestricted autonomous coding agent.
- A complete security scanner.
- A substitute for reviewing and testing code.
Its capabilities depend on implemented diagnostic rules, supported
tools, project configuration, and available evidence. Developers remain
responsible for reviewing changes and validating their applications.
Relationship with IRABRAIN
DNOCER is an independent developer tool under Azennix AI.

IRABRAIN is a broader personal AI and adaptability product. Their
responsibilities remain separate:
- DNOCER focuses on software project intelligence and controlled
  development workflows.
- IRABRAIN focuses on helping people understand opportunities,
  develop capabilities, and execute broader personal or
  entrepreneurial goals.
Any future integration should be optional, documented, and
consent-based. DNOCER does not duplicate IRABRAIN's core or
self-development foundation.
Development
To work with the source code:
git clone https://github.com/Azennix/dnocer.git
cd dnocer
python -m venv .venv
Activate the virtual environment.

PowerShell:
.venv\Scripts\Activate.ps1
Command Prompt:
.venv\Scripts\activate.bat
Install the package in editable mode with development dependencies:
python -m pip install -e ".[dev]"
Run the test suite:
python -m pytest
The available tests and development checks depend on the current
repository state.
Release information
  Field              Value
  Product            DNOCER
Organization       Azennix AI
Version            1.0.0
Release            Initial major release
Interface          Command-line application
Primary language   Python
Final principle
::: {align="center"}
**Evidence before assumptions.**\
**Understanding before modification.**\
**Approval before consequential action.**\
**Verification before claiming success.**\
**Recovery when something goes wrong.**

### DNOCER --- Your Companion. Your Capability. Your Control.
:::