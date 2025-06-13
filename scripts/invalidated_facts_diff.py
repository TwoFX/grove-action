#!/usr/bin/env python3
"""Compare two invalidated-facts JSON files and output a Markdown summary.

Usage
-----
    python invalidated_facts_diff.py baseline.json latest.json

The script prints a Markdown-formatted report listing any new invalidated
facts—that is, (widgetId, factId) pairs that appear in latest.json but not
in baseline.json. Both files must conform to the JTD schema
`invalidatedFacts.jtd.json` (see Grove repository).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Set, Tuple, Iterable

Fact = Tuple[str, str]  # (widgetId, factId)


def _load_facts(path: str | Path) -> Set[Fact]:
    """Return a set of (widgetId, factId) pairs from *path*.

    Raises a SystemExit with a helpful message if the file cannot be read or is
    malformed.
    """
    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} does not contain valid JSON: {exc}") from exc

    try:
        items: Iterable[dict] = data["invalidatedFacts"]
    except (KeyError, TypeError):
        raise SystemExit(
            f"{path} is missing a top‑level 'invalidatedFacts' array as required by the schema."
        )

    facts: Set[Fact] = set()
    for idx, item in enumerate(items):
        try:
            facts.add((item["widgetId"], item["factId"]))
        except (KeyError, TypeError):
            raise SystemExit(
                f"Element #{idx} in {path} is missing 'widgetId' or 'factId'."
            )
    return facts


def _format_markdown(new_facts: Set[Fact]) -> str:
    """Return a nicely formatted Markdown message for *new_facts*."""
    if not new_facts:
        return "*Grove: no invalidated facts*"

    lines = ["### Grove invalidations", ""]
    for widget_id, fact_id in sorted(new_facts):
        lines.append(f"- `{widget_id}`/`{fact_id}`")
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python invalidated_facts_diff.py <baseline.json> <latest.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    baseline_path, latest_path = map(Path, sys.argv[1:3])
    baseline_facts = _load_facts(baseline_path)
    latest_facts = _load_facts(latest_path)

    new_facts = latest_facts - baseline_facts
    print(_format_markdown(new_facts))


if __name__ == "__main__":
    main()
