from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from rich.console import Console

DEFAULT_CLOUD_URL = "https://dnocer-cloud.onrender.com"
console = Console()


def investigate(question: str, context: str) -> str:
    base_url = os.getenv(
        "DNOCER_CLOUD_URL",
        DEFAULT_CLOUD_URL,
    ).strip().rstrip("/")

    if not base_url:
        raise RuntimeError("DNOCER Cloud URL is not configured.")

    if len(question) > 5000:
        raise ValueError("Question exceeds the 5000-character limit.")

    if len(context) > 30000:
        raise ValueError(
            f"Project context exceeds the 30000-character limit "
            f"({len(context)} characters received)."
        )

    payload = json.dumps({
        "question": question,
        "context": context,
    }).encode("utf-8")

    request = Request(
        f"{base_url}/v1/ai/investigate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with console.status(
            "[bold white]Connecting to DNOCER Cloud...[/]\n"
            "[dim]If the server was idle, it may take "
            "up to 1 minute to wake up. Please wait...[/]",
            spinner="dots",
        ):
            with urlopen(request, timeout=65) as response:
                data = json.loads(response.read().decode("utf-8"))

    except HTTPError as exc:
        raise RuntimeError(
            f"DNOCER Cloud returned HTTP {exc.code}."
        ) from None

    except (URLError, TimeoutError, OSError):
        raise RuntimeError(
            "Could not connect to DNOCER Cloud. "
            "Check your internet connection and cloud URL."
        ) from None

    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError(
            "DNOCER Cloud returned an invalid response."
        ) from None

    result = data.get("result")

    if not isinstance(result, str) or not result.strip():
        raise RuntimeError("DNOCER Cloud returned an empty investigation.")

    return result.strip()