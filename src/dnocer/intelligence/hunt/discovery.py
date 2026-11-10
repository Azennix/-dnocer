from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".dnocer",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".swift",
    ".kt",
    ".kts",
}


def discover_project(root: Path) -> dict[str, Any]:
    root = root.resolve()

    if not root.is_dir():
        raise ValueError(f"Invalid project directory: {root}")

    files = []
    total_size = 0

    for current, dirs, names in __import__("os").walk(root):
        dirs[:] = sorted(directory for directory in dirs if directory not in SKIP_DIRS)

        for name in sorted(names):
            path = Path(current) / name

            if path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue

            try:
                if path.is_symlink() or not path.is_file():
                    continue

                size = path.stat().st_size

                files.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "extension": path.suffix.lower(),
                        "size": size,
                    }
                )

                total_size += size

            except OSError:
                continue

    return {
        "root": str(root),
        "file_count": len(files),
        "total_size": total_size,
        "files": files,
        "languages": sorted({item["extension"] for item in files}),
    }
