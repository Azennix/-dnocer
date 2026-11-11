<div align="center">
  <img src="https://raw.githubusercontent.com/Azennix/dnocer/main/src/dnocer/assets/dnocer-logo.png" alt="DNOCER animal logo" width="150" />
  <h1>DNOCER</h1>
  <p><strong>Project Intelligence &amp; Safe Repair Companion</strong></p>
  <p>A developer tool by <strong>Azennix AI</strong></p>
  <p><em>Your Companion. Your Capability. Your Control.</em></p>
  <p><strong>Evidence before assumptions · Approval before action · Verification before success</strong></p>
</div>DNOCER is a command-line developer companion for inspecting software projects, understanding diagnostic findings, investigating selected risks, analyzing test results, and reviewing proposed code repairs.

It is designed to support developer judgment—not replace it. Developers remain responsible for reviewing changes and verifying results.
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
Software projects can contain confusing errors, fragile code, failing tests, and risks that are difficult to prioritize. Developers often move between multiple tools just to understand what happened and decide what to do next.

DNOCER brings selected developer workflows into one CLI:
- Inspect a project and surface useful findings.
- Investigate issues with supporting evidence.
- Review test results.
- Examine proposed repairs before applying them.
- Keep a record of previous activity and support undo workflows.
DNOCER is intended to help developers make informed decisions while keeping them in control.
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


The exact behavior available to each command depends on the installed release and project context. Use command help to review options before working on an important project.
Installation
DNOCER is distributed as a Python package.
python -m pip install dnocer
Verify the installation:
dnocer version
If the dnocer command is not found, reopen your terminal, confirm that your Python scripts directory is on PATH, and check the package installation:
python -m pip show dnocer
Quick start
Open a terminal in the root directory of the project you want to inspect.

Display the available commands:
dnocer --help
Inspect the project:
dnocer scan
Review the options for a command before using it:
dnocer hunt --help
Run DNOCER from the project directory you intend to work on so commands use the correct project context.
Commands
dnocer scan
Start with a project scan to gather diagnostic information and identify findings that may need attention.
dnocer scan
dnocer test
Use the test workflow to examine test execution and its results.
dnocer test
dnocer hunt
Investigate a selected issue or risk more closely. Review the available options first.
dnocer hunt --help
dnocer fix
Inspect the repair workflow and review proposed code changes before accepting them.
dnocer fix --help
dnocer auto
Review the supported automation workflow and its options.
dnocer auto --help
dnocer undo
Review the undo command options before reversing a supported previous action.
dnocer undo --help
dnocer history
Review activity recorded by DNOCER.
dnocer history
dnocer version
Display the installed DNOCER version.
dnocer version
Typical workflow
A cautious starting workflow for an unfamiliar project:
1. Open the project directory in your terminal.
2. Review the available commands.
3. Scan the project.
4. Examine the test workflow.
5. Investigate relevant findings.
6. Review proposed repairs.
7. Verify the project after any accepted change.
8. Review recorded activity if needed.
Start by checking the command list:
dnocer --help
Then scan the project:
dnocer scan
Run the test workflow:
dnocer test
Investigate a finding and review repair options:
dnocer hunt --help
dnocer fix --help
Do not treat a diagnostic finding or AI-generated suggestion as proof that a change is correct. Validate important changes with your own tests and review process.
Safety principles
DNOCER follows three guiding principles.
1. Evidence before assumptions
Findings should be grounded in observable project information. A suggestion should not be treated as a verified fact without supporting evidence.
2. Approval before action
Developers should understand proposed changes and retain control over consequential actions. Review what a command intends to do before allowing it to modify a project.
3. Verification before success
A proposed repair is not proof of a successful repair. Run relevant tests and inspect the resulting changes.
Technology
DNOCER is built with Python and uses a command-line interface designed for readable terminal output.
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
This is a high-level overview. Additional modules may be present and can change as the project develops.
Configuration
Some DNOCER features may require external service credentials. Keep credentials outside source control and configure them through environment variables as documented by the relevant feature.

Never commit API keys, passwords, access tokens, or other secrets to a public repository.
Current scope
DNOCER is an evolving developer tool. Available behavior depends on the installed version, configured integrations, and the project being inspected.
- Review dnocer --help for commands available in your installation.
- Review dnocer <command> --help before using command options.
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