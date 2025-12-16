#!/usr/bin/env python3
"""Compare two invalidated-facts JSON files and output a Markdown summary.

Usage
-----
    python invalidated_facts_diff.py upstream.json latest.json

The script prints a Markdown-formatted report listing any new invalidated
facts and need-attention facts—that is, (widgetId, factId) pairs that appear
in latest.json but not in upstream.json. Both files must conform to the JTD
schema `invalidatedFacts.jtd.json` (see Grove repository).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Set, Tuple, Iterable

Fact = Tuple[str, str]  # (widgetId, factId)


def _load_facts(path: str | Path, array_name: str) -> Set[Fact]:
    """Return a set of (widgetId, factId) pairs from *path* for the given *array_name*.

    Returns an empty set if the array doesn't exist (for backwards compatibility).
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

    # Return empty set if array doesn't exist (backwards compatibility)
    if not isinstance(data, dict) or array_name not in data:
        return set()

    items: Iterable[dict] = data[array_name]
    if not isinstance(items, list):
        raise SystemExit(
            f"{path}['{array_name}'] must be an array."
        )

    facts: Set[Fact] = set()
    for idx, item in enumerate(items):
        try:
            facts.add((item["widgetId"], item["factId"]))
        except (KeyError, TypeError):
            raise SystemExit(
                f"Element #{idx} in {path}['{array_name}'] is missing 'widgetId' or 'factId'."
            )
    return facts


def _format_markdown(new_invalidated: Set[Fact], new_need_attention: Set[Fact]) -> str:
    """Return a nicely formatted Markdown message for new facts."""
    if not new_invalidated and not new_need_attention:
        return "*Grove: no invalidated facts*"

    lines = []

    if new_invalidated:
        lines.append("### Grove invalidations")
        lines.append("")
        for widget_id, fact_id in sorted(new_invalidated):
            lines.append(f"- `{widget_id}`/`{fact_id}`")

    if new_need_attention:
        if lines:
            lines.append("")
        lines.append("### Grove needs attention")
        lines.append("")
        for widget_id, fact_id in sorted(new_need_attention):
            lines.append(f"- `{widget_id}`/`{fact_id}`")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python invalidated_facts_diff.py <upstream.json> <latest.json>",
            file=sys.stderr,
        )
        sys.exit(1)

    upstream_path, latest_path = map(Path, sys.argv[1:3])

    # Load invalidated facts
    upstream_invalidated = _load_facts(upstream_path, "invalidatedFacts")
    latest_invalidated = _load_facts(latest_path, "invalidatedFacts")
    new_invalidated = latest_invalidated - upstream_invalidated

    # Load need-attention facts
    upstream_need_attention = _load_facts(upstream_path, "needAttentionFacts")
    latest_need_attention = _load_facts(latest_path, "needAttentionFacts")
    new_need_attention = latest_need_attention - upstream_need_attention

    print(_format_markdown(new_invalidated, new_need_attention))


if __name__ == "__main__":
    main()
