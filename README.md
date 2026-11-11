<div align="center">

<img src="src/dnocer/assets/dnocer-terminal-animal.png" alt="DNOCER animal logo" width="200" />

# 🛡️ DNOCER

### Project Intelligence & Safe Repair Companion

**🔎 Evidence before assumptions · ✅ Approval before action · 🧪 Verification before success**

![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11%2B-yellow?style=for-the-badge&logo=python&logoColor=white)
![Interface](https://img.shields.io/badge/interface-CLI-green?style=for-the-badge&logo=gnometerminal&logoColor=white)
![AI](https://img.shields.io/badge/AI-optional-purple?style=for-the-badge)
![Local First](https://img.shields.io/badge/local--first-yes-orange?style=for-the-badge)

**A product by Azennix AI**

*Your Companion. Your Capability. Your Control.*

</div>

---

DNOCER is a **command-line developer companion**. It helps you understand software problems, find likely root causes, inspect test failures, review code fixes, and **stay in control of every change** made to your project.

It combines **deterministic tools** (Ruff, pytest, Python parser) with **optional AI investigation**.

> [!IMPORTANT]
> **Understand the problem → Review the change → Verify the result.**
> That is the whole idea behind DNOCER.

---

## ⚡ Quick Start

```powershell
# 1. Install
python -m pip install dnocer-1.0.0-py3-none-any.whl

# 2. Check it works
dnocer version
dnocer --help

# 3. Scan your project
dnocer scan .
```

> [!TIP]
> Requirements: **Python 3.11+** and Windows PowerShell / CMD (or any compatible terminal). An Anthropic API key is **only** needed for AI features.

---

## 📑 Table of Contents

1. [Why DNOCER exists](#-why-dnocer-exists)
2. [What DNOCER does](#-what-dnocer-does)
3. [Core principles](#-core-principles)
4. [Commands](#-commands)
5. [How each workflow works](#-how-each-workflow-works)
6. [Architecture](#-architecture)
7. [AI integration](#-ai-integration)
8. [Safety model](#-safety-model)
9. [Tech stack](#-tech-stack)
10. [Installation](#-installation)
11. [Limitations](#-limitations)
12. [IRABRAIN](#-relationship-with-irabrain)
13. [Release info](#-release-info)

---

## 🤔 Why DNOCER Exists

Developers deal with these problems every day:

| 🐞 Problem | 😓 Pain |
|---|---|
| Syntax and runtime errors | Hard to find the real cause |
| Dependency and config issues | Time-consuming |
| Lint and code-quality issues | Easy to ignore |
| Test failures | Unclear why they fail |
| Risky code changes | Fear of breaking things |

For **beginners**, understanding *why* something failed is even harder.

DNOCER closes the gap between **"something broke"** and **"I understand how to fix it"**, and makes you a *more capable* developer instead of one who blindly depends on generated code.

---

## 🧰 What DNOCER Does

| # | Capability |
|---|---|
| 1 | 🔍 Project scanning and diagnostics |
| 2 | 📋 Structured issue reporting |
| 3 | 💡 Local explanations of problems |
| 4 | 🤖 Optional AI-assisted investigation |
| 5 | ⚠️ Risk-pattern identification |
| 6 | 🧪 Test execution and result analysis |
| 7 | 🛠️ Reviewable repair proposals |
| 8 | ✅ Approval-controlled modifications |
| 9 | ⏪ Repair history and rollback |

DNOCER works **alongside** your existing tools. It does not replace them.

---

## 🧭 Core Principles

### 🔎 Evidence before explanation
Every diagnosis should be backed by evidence: file locations, rule IDs, parser results, linter output, test results, error messages.

> [!NOTE]
> If the evidence only supports a *guess*, DNOCER must not present it as a *confirmed fact*.

### ⚙️ Deterministic before generative
Conventional tools do the checks first: **Python syntax parsing**, **Ruff**, **existing test frameworks**. AI is an extra layer, never a replacement.

### 🙋 Human authorization
You see a repair proposal **before** any file is changed, and **you** decide whether to approve it.

### 🔒 System authorization
Technical safety rules (allowed paths, validation, execution limits) are **separate** from your approval.

> [!WARNING]
> User approval can **never** bypass technical safety restrictions.

### ✅ Verifiable outcomes
Proposing a fix ≠ applying a fix ≠ a *successful* fix. DNOCER treats these as three different steps.

### 🏠 Local-first
Core diagnostics run **locally**. AI features are optional and ask for **explicit consent** before any project context is sent out.

---

## 💻 Commands

Built with **Typer** (commands) and **Rich** (colorful terminal output).

| Command | What it does |
|---|---|
| `dnocer scan` | 🔍 Analyze a project and show findings |
| `dnocer test` | 🧪 Run tests and analyze results |
| `dnocer hunt` | 🎯 Investigate risky code patterns |
| `dnocer fix` | 🛠️ Preview and apply approved repairs |
| `dnocer auto` | 🤝 Coordinate supported scan + repair workflows |
| `dnocer undo` | ⏪ Reverse a recorded repair |
| `dnocer history` | 📜 Show repair history |
| `dnocer version` | 🏷️ Show installed version |

```powershell
dnocer --help
```

---

## 🔬 How Each Workflow Works

<details open>
<summary><b>🔍 Project Scanning</b> — <code>dnocer scan .</code></summary>

<br>

Examines your project using supported diagnostic checks and shows findings in a structured format. It is **diagnostic only**, not an automatic repair.

Each finding can include: title, severity, diagnostic code, file and line, description, impact, recommended action, prevention tips, detection source, and whether a repair is available.

</details>

<details>
<summary><b>🧪 Test Intelligence</b> — <code>dnocer test .</code></summary>

<br>

Runs your project tests and analyzes the output: passed, failed, errors, skipped, warnings, failure locations, and exception info.

It also tells **different states apart** instead of calling everything a "failure":

| State | Meaning |
|---|---|
| 🟢 Tests passed | All good |
| 🔴 Tests failed | Real test failures |
| 🟡 Runner unavailable | pytest not found or not usable |
| 🟡 No tests found | Nothing to run |
| 🟠 Timed out | Execution took too long |

```powershell
dnocer test . --verbose   # more detail
dnocer test . --ai        # optional AI investigation
```

</details>

<details>
<summary><b>🎯 Risk Investigation</b> — <code>dnocer hunt .</code></summary>

<br>

Finds risky code patterns from the project's findings:

- Bare exception handling
- Broad exception handling
- Mutable default arguments
- Selected related patterns

```powershell
dnocer hunt . --ai   # optional AI-assisted review
```

> [!NOTE]
> AI output is **advisory**, not automatically confirmed.

</details>

<details>
<summary><b>🛠️ Controlled Repair</b> — <code>dnocer fix .</code></summary>

<br>

```text
 1. Identify a repairable finding
 2. Generate a repair proposal
 3. Show the proposed changes
 4. Ask for YOUR approval
 5. Apply the approved proposal
 6. Preserve the original file
 7. Record the operation
 8. Let you inspect or reverse it
```

> [!CAUTION]
> A repair is **never** "successful" just because a suggestion was generated.

</details>

<details>
<summary><b>🤝 Automated Repair</b> — <code>dnocer auto .</code></summary>

<br>

Coordinates supported scanning and repair steps. It does **not** mean unrestricted autonomous editing. **Each repair needs your individual approval.**

</details>

<details>
<summary><b>📜 History</b> — <code>dnocer history .</code></summary>

<br>

Records: change ID, timestamp, file, diagnostic rule, repair status, and verification info.

</details>

<details>
<summary><b>⏪ Rollback</b> — <code>dnocer undo .</code></summary>

<br>

Uses saved repair info and backups to reverse recorded changes.

> [!TIP]
> Rollback is a safety net, but still keep your **own project backups**.

</details>

---

## 🏗️ Architecture

| Layer | Responsibility | File |
|---|---|---|
| 🖥️ **CLI** | Commands, arguments, prompts, approvals, terminal output | `src/dnocer/cli.py` |
| ⚙️ **Core** | Scanning, context collection, test execution, repair proposal/apply, history, rollback | `src/dnocer/core.py` |
| 🧠 **Intelligence** | Failure investigation, root-cause explanations, optional AI analysis | — |
| 🔌 **External tools** | Ruff for lint/repair, pytest for tests (via subprocess) | — |
| 💾 **Local state** | Repair history and backups in the `.dnocer` folder | `.dnocer/` |

> [!IMPORTANT]
> Keep the `.dnocer` folder if you want to use rollback history later.

---

## 🤖 AI Integration

DNOCER can use the **Anthropic SDK** for extra explanations and investigation.

- ✅ AI is **optional**. Local diagnostics work without it.
- ✅ A normal local scan **never** sends project data automatically.
- ✅ AI commands show a **consent notice** first.
- ✅ You should inspect the information before agreeing to send it.
- ⚠️ AI output is **untrusted advice**.
- ⚠️ AI recommendations never replace technical validation or your approval.

Set your key with an environment variable:

```text
ANTHROPIC_API_KEY
```

> [!CAUTION]
> Never put API keys inside source files or publish them in documentation.

---

## 🔐 Safety Model

Two separate kinds of authorization:

| 🙋 Human Authorization | 🔒 System Authorization |
|---|---|
| Approving a repair | Project path boundaries |
| Allowing context to be sent to AI | File and syntax validation |
| Confirming consequential actions | Repair restrictions |
| | Execution limits |

> [!WARNING]
> Your confirmation does **not** make a prohibited operation safe, and automation must **not** silently replace your approval.

**Repair integrity:** DNOCER preserves the original file, the proposed change, your approval decision, the resulting file, and the recorded state. The bytes applied match the approved proposal, as long as the source file has not changed since preview.

> [!CAUTION]
> No tool can find every bug or guarantee every repair is correct. You are still responsible for reviewing changes and testing your app.

---

## 🧱 Tech Stack

| Technology | Purpose |
|---|---|
| 🐍 Python | Main language |
| ⌨️ Typer | CLI framework |
| 🎨 Rich | Terminal presentation |
| 🧹 Ruff | Python linting and repair |
| 🧪 pytest | Test execution |
| 🗄️ SQLite | Local repair-history storage |
| 🤖 Anthropic SDK | Optional AI analysis |
| 📦 setuptools | Package building |

---

## 📦 Installation

```powershell
pip install dnocer
dnocer version
dnocer --help
```

**Requirements**

- Python 3.11 or newer
- Windows PowerShell, CMD, or compatible terminal
- Required Python package dependencies
- *(Optional)* Anthropic API key for AI features

For development and testing, install the dev dependencies separately.

---

## 🚧 Limitations

DNOCER is **not**:

- ❌ A replacement for an IDE, debugger, compiler, or interpreter
- ❌ A guarantee of bug-free software
- ❌ An unrestricted autonomous coding agent
- ❌ A complete security scanner
- ❌ A guarantee that every AI explanation is correct
- ❌ A substitute for reviewing and testing code

What it can do depends on the implemented rules, supported tools, project setup, and available evidence.

---

## 🧠 Relationship with IRABRAIN

| | DNOCER | IRABRAIN |
|---|---|---|
| **What** | Independent developer tool | Broader personal AI and adaptability product |
| **Focus** | Software project intelligence and controlled workflows | Opportunities, capabilities, and personal or entrepreneurial goals |

Their responsibilities stay **separate**. Any future integration should be optional, documented, and consent-based.

---

## 🏷️ Release Info

| | |
|---|---|
| **Product** | DNOCER |
| **Organization** | Azennix AI |
| **Version** | 1.0.0 |
| **Release type** | Initial major release |
| **Interface** | Command-line application |
| **Implementation** | Python |

---

<div align="center">

## 🎯 Final Principle

**Evidence before assumptions.**
**Understanding before modification.**
**Approval before consequential action.**
**Verification before claiming success.**
**Recovery when something goes wrong.**

<br>

**DNOCER** · A developer tool by **Azennix AI**

*Your Companion. Your Capability. Your Control.*

</div>
