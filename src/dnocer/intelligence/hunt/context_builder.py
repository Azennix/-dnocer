from pathlib import Path


def build_hunt_context(
    root: Path,
    discovered_files: list[dict],
    findings: list[dict],
    dependencies: dict,
    max_chars: int = 27000,
    radius: int = 25,
) -> dict:

    root = root.resolve()

    priorities = {}

    # Priority 1: Files with detected findings.
    for finding in findings:
        file_path = finding.get("file")
        if file_path:
            priorities[file_path] = 1

    # Priority 2: Files connected through imports.
    for imported in dependencies.get("imports", []):
        source = imported.get("source", "").replace(".", "/")
        target = imported.get("resolved_file")

        if not target:
            continue

        source_path = source + ".py"

        if source_path in priorities:
            priorities.setdefault(target, 2)

    # Priority 3: Remaining discovered files.
    for item in discovered_files:
        priorities.setdefault(item["path"], 3)

    ordered_files = sorted(
        discovered_files,
        key=lambda item: (
            priorities.get(item["path"], 3),
            item["path"].casefold(),
        ),
    )

    finding_lines = {}

    for finding in findings:
        file_path = finding.get("file")
        line = finding.get("line", 1)

        if file_path:
            finding_lines.setdefault(file_path, set()).add(line)

    sections = []
    total_size = 0
    omitted = []
    included = []

    for item in ordered_files:
        file_path = item["path"]
        path = (root / file_path).resolve()

        try:
            path.relative_to(root)

            if path.is_symlink() or not path.is_file():
                continue

            source = path.read_text(encoding="utf-8")

        except (OSError, UnicodeDecodeError, ValueError):
            omitted.append(file_path)
            continue

        lines = source.splitlines()

        important_lines = finding_lines.get(file_path, set())

        if important_lines:
            selected_lines = set()

            for line in important_lines:
                start = max(1, line - radius)
                end = min(len(lines), line + radius)

                selected_lines.update(
                    range(start, end + 1)
                )

            excerpt_lines = [
                f"{number}: {lines[number - 1]}"
                for number in sorted(selected_lines)
            ]

        else:
            excerpt_lines = [
                f"{number}: {line}"
                for number, line in enumerate(lines, 1)
            ]

        header = f"\n--- FILE: {file_path} ---\n"
        footer = "\n"

        available = max_chars - total_size - len(header) - len(footer)

        if available <= 0:
            omitted.append(file_path)
            continue

        excerpt = "\n".join(excerpt_lines)

        # Keep a partial excerpt when the entire file doesn't fit.
        if len(excerpt) > available:
            excerpt = excerpt[:available]
            excerpt += "\n[TRUNCATED: remaining source excluded]"

        section = header + excerpt + footer

        if total_size + len(section) > max_chars:
            omitted.append(file_path)
            continue

        sections.append(section)
        total_size += len(section)
        included.append(file_path)

    return {
        "context": "".join(sections),
        "files_included": len(included),
        "characters": total_size,
        "included_files": included,
        "omitted_files": omitted,
    }