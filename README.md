<div align="center">
  <img src="src/dnocer/assets/dnocer-logo.png" alt="DNOCER animal logo" width="150" />
  <h1>DNOCER</h1>
  <p><strong>Project Intelligence &amp; Safe Repair Companion</strong></p>
  <p>A developer tool by <strong>Azennix AI</strong></p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
  <p>
    <strong>Evidence before assumptions · Approval before action · Verification before success</strong>
  </p>
</div>DNOCER is a command-line developer companion for inspecting software projects, understanding diagnostic findings, investigating selected risks, analyzing test results, and reviewing proposed code repairs.

It is designed to help developers make better-informed decisions while keeping the developer in control of important actions.
Table of contents
- Why DNOCER
- Core capabilities
- Installation
- Quick start
- Commands
- Typical workflow
- Safety principles
- Technology
- Project structure
- Configuration
- Current scope
- Contributing
- License
Why DNOCER
Software projects can contain confusing errors, fragile code, failing tests, and risks that are difficult to prioritize. Developers often have to move between multiple tools just to understand what happened and decide what to do next.

DNOCER brings selected developer workflows into one CLI:
- Inspect a project and surface useful findings.
- Investigate issues with supporting evidence.
- Review test results.
- Examine proposed repairs before applying them.
- Keep a record of previous activity and support undo workflows.
DNOCER is intended to support developer judgment—not replace it.
Core capabilities
Capability	Command	Purpose
Project scan	scan	Inspect a project and report findings.
Test analysis	test	Run or analyze the project's test workflow.
Investigation	hunt	Investigate a selected issue or risk.
Repair review	fix	Review and work with proposed code repairs.
Automation	auto	Run the supported automated workflow.
Undo	undo	Reverse a supported previous change.
History	history	Review recorded DNOCER activity.
Version	version	Display the installed DNOCER version.


The exact behavior available to each command depends on the installed release and project context. Review command help before using a command on an important project.
Installation
DNOCER is distributed as a Python package.
python -m pip install dnocer
Verify the installation:
dnocer version
If the dnocer command is not found, close and reopen your terminal, confirm that your Python scripts directory is on PATH, and try:
python -m pip show dnocer
Quick start
Open a terminal in the root directory of the project you want to inspect.

Display the available commands:
dnocer --help
Inspect the project:
dnocer scan
Review the available options for a command before running it:
dnocer hunt --help
DNOCER should be run from the project you intend to work on so that its commands operate in the correct context.
Commands
dnocer scan
Start with a project scan to gather diagnostic information and identify findings that may need attention.
dnocer scan
dnocer test
Use the test workflow to examine test execution and its results.
dnocer test
dnocer hunt
Use investigation when you want to examine a particular issue or risk more closely.
dnocer hunt --help
dnocer fix
Use the repair workflow to inspect proposed code changes. Review the proposal and understand its impact before accepting a change.
dnocer fix --help
dnocer auto
Use the supported automation workflow when you want DNOCER to coordinate available steps.
dnocer auto --help
dnocer undo
Use undo to reverse a supported previous action when appropriate.
dnocer undo --help
dnocer history
Review the activity recorded by DNOCER.
dnocer history
dnocer version
Display the installed version.
dnocer version
Typical workflow
A cautious starting workflow for an unfamiliar project is:
1. Open the project directory in your terminal.
2. Run dnocer --help and review the available commands.
3. Run dnocer scan to collect initial findings.
4. Use dnocer test to examine the test workflow.
5. Investigate relevant findings with dnocer hunt.
6. Review proposed changes with dnocer fix.
7. Verify the project after any accepted change.
8. Use dnocer history to review recorded activity.
Do not treat a diagnostic finding or AI-generated suggestion as proof that a change is correct. Validate important changes with your own tests and review process.
Safety principles
DNOCER follows three guiding principles:
1. Evidence before assumptions
Findings should be grounded in observable project information. A suggestion should not be treated as a verified fact without supporting evidence.
2. Approval before action
Developers should understand proposed changes and retain control over consequential actions. Review what a command intends to do before allowing it to modify a project.
3. Verification before success
A proposed repair is not proof of a successful repair. Run relevant tests and inspect the resulting changes.
Technology
DNOCER is built with Python and uses a command-line interface designed for readable terminal output. Its implementation includes:
- Python
- Typer for CLI command handling
- Rich for terminal presentation
- Anthropic SDK for supported AI integration
Project structure
The repository is organized around the DNOCER Python package, its command-line interface, supporting modules, assets, and tests.
dnocer/
├── src/
│   └── dnocer/
│       ├── assets/
│       │   ├── dnocer-logo.png
│       │   └── dnocer-logo.txt
│       ├── cli.py
│       └── branding.py
├── tests/
├── pyproject.toml
└── README.md
This is a high-level overview. Additional modules may be present in the repository and can change as the project develops.
Configuration
Some DNOCER features may require external service credentials. Keep credentials outside source control and configure them through environment variables as documented by the relevant feature.

Never commit API keys, passwords, access tokens, or other secrets to a public repository.
Current scope
DNOCER is an evolving developer tool. Available behavior depends on the installed version, configured integrations, and the project being inspected.
- Review dnocer --help for the commands available in your installation.
- Review dnocer <command> --help before using a command with options.
- Back up important work and use version control before applying code changes.
- Verify results independently, especially before deploying or releasing software.
Contributing
Contributions, bug reports, and practical feedback are welcome.

When reporting an issue, include:
- Your operating system and Python version.
- The DNOCER version (dnocer version).
- The command you ran.
- The complete error output, with secrets removed.
- A minimal description of the project context.
License
See the repository's license file for the terms that apply to this project.
<div align="center">
  <p><strong>DNOCER</strong> · A developer tool by Azennix AI</p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
</div>