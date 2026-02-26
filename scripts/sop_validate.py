#!/usr/bin/env python3
"""SOP validation gates for awesome-llm-tech-reports."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import download_papers


def parse_readme_table_month_counts(text: str) -> Counter:
    rows: List[List[str]] = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| Release Date") or line.startswith("| ---"):
            continue
        parts = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(parts) >= 6 and re.match(r"^20\d{2}-\d{2}$", parts[0]):
            rows.append(parts)
    return Counter(r[0] for r in rows)


def parse_snapshot_counts(text: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for yy, mm, rr in re.findall(r'\("(\d\d)-(\d\d)<br/>R(\d\d)"\)', text):
        out[f"20{yy}-{mm}"] = int(rr)
    return out


def parse_snapshot_node_class_map(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for nodes, cls in re.findall(r"^\s*class\s+([A-Za-z0-9_,]+)\s+([a-z0-9]+);", text, flags=re.M):
        for node in nodes.split(","):
            out[node.strip()] = cls
    return out


def parse_snapshot_nodes(text: str) -> Dict[str, int]:
    # Example: M1(("25-01<br/>R02"))
    out: Dict[str, int] = {}
    for node, yy, mm, rr in re.findall(r'(M\d+)\(\("(\d\d)-(\d\d)<br/>R(\d\d)"\)\)', text):
        out[node] = int(rr)
    return out


def find_snapshot_block(text: str) -> str:
    m = re.search(
        r"<summary><b>Monthly Density Snapshot</b></summary>\s*```mermaid(.*?)```",
        text,
        flags=re.S,
    )
    return m.group(1) if m else ""


def validate_release_prefix_accuracy() -> List[str]:
    errors: List[str] = []
    session = download_papers.build_session()
    links = [download_papers.normalize_url(m["official_link"]) for m in download_papers.MODELS]
    link_frequency = Counter(links)
    cache: Dict[str, Tuple[str | None, str]] = {}

    for r in download_papers.MODELS:
        link = download_papers.normalize_url(r["official_link"])
        resolved, source = download_papers.resolve_release_month(
            session=session,
            declared_release_date=r["release_date"],
            url=link,
            link_frequency=link_frequency,
            cache=cache,
        )
        if resolved != r["release_date"]:
            errors.append(
                f"release_date mismatch: {r['model']} {r['release_date']} -> {resolved} ({source})"
            )
    return errors


def validate() -> int:
    errors: List[str] = []
    if not README.exists():
        print("ERROR: README.md not found")
        return 1

    text = README.read_text(encoding="utf-8")

    # Gate 1: README must remain English-only (no Han chars).
    han_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    if han_count > 0:
        errors.append(f"README contains Chinese characters: {han_count}")

    # Gate 2: release_date prefix must match runtime-calibrated result.
    errors.extend(validate_release_prefix_accuracy())

    # Gate 3: monthly counts consistency: MODELS == README table == snapshot.
    model_counts = Counter(m["release_date"] for m in download_papers.MODELS)
    table_counts = parse_readme_table_month_counts(text)
    snapshot_counts = parse_snapshot_counts(text)
    if dict(sorted(model_counts.items())) != dict(sorted(table_counts.items())):
        errors.append("monthly counts mismatch: MODELS vs README table")
    if dict(sorted(table_counts.items())) != dict(sorted(snapshot_counts.items())):
        errors.append("monthly counts mismatch: README table vs Monthly Density Snapshot")

    # Gate 4: monthly snapshot must remove side tags.
    snapshot_block = find_snapshot_block(text)
    if re.search(r"\bT\d+\[", snapshot_block) or "classDef tag" in snapshot_block:
        errors.append("Monthly Density Snapshot still contains side tags")

    # Gate 5: bubble size class must match count buckets.
    # Mapping frozen in README style.
    class_map = parse_snapshot_node_class_map(snapshot_block)
    node_counts = parse_snapshot_nodes(snapshot_block)
    expected = {1: "b1", 2: "b2", 3: "b3", 4: "b4", 5: "b5", 12: "b12"}
    for node, cnt in sorted(node_counts.items()):
        exp = expected.get(cnt)
        if not exp:
            continue
        got = class_map.get(node)
        if got != exp:
            errors.append(f"bubble class mismatch: {node} count={cnt} expected={exp} got={got}")

    if errors:
        print("SOP validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("SOP validation passed")
    print(f"models={len(download_papers.MODELS)}")
    print(f"months={len(table_counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
