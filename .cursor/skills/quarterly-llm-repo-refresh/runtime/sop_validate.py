#!/usr/bin/env python3
"""SOP validation gates for awesome-llm-tech-reports."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

from runtime_paths import GENERATED_DIR, README, ROOT

MONTHLY_JSON = GENERATED_DIR / "monthly_density.json"
TIMELINE_JSON = GENERATED_DIR / "release_timeline.json"
MONTHLY_SVG = ROOT / "assets" / "diagrams" / "monthly-density.svg"
TIMELINE_SVG = ROOT / "assets" / "diagrams" / "release-timeline.svg"


def parse_readme_table_rows(text: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| Release Date") or line.startswith("| ---"):
            continue
        parts = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(parts) >= 6 and re.match(r"^20\d{2}-\d{2}$", parts[0]):
            rows.append(parts)
    return rows


def parse_readme_table_month_counts(text: str) -> Counter:
    return Counter(r[0] for r in parse_readme_table_rows(text))


def parse_readme_table_year_counts(text: str) -> Counter:
    return Counter(r[0][:4] for r in parse_readme_table_rows(text))


def parse_year_summary_counts(text: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for year, count in re.findall(r"<summary><b>(20\d{2}) \((\d+) models\)</b></summary>", text):
        out[year] = int(count)
    return out


def load_generated_monthly_counts() -> Dict[str, int]:
    payload = json.loads(MONTHLY_JSON.read_text(encoding="utf-8"))
    return {item["month"]: int(item["count"]) for item in payload.get("months", [])}


def load_generated_timeline_months() -> List[str]:
    payload = json.loads(TIMELINE_JSON.read_text(encoding="utf-8"))
    return list(payload.get("months", []))


def validate_release_prefix_accuracy(text: str) -> List[str]:
    errors: List[str] = []
    for release_date, _, model, _, _, local_file in parse_readme_table_rows(text):
        if local_file.lower() in {"download failed", "only online", "仅在线", "下载失败", "未发布"}:
            continue
        prefix_match = re.match(r"^\d{4}/[^/]+/(20\d{2}-\d{2})_.+\.pdf$", local_file)
        if not prefix_match:
            errors.append(f"unexpected local file path format: {model} -> {local_file}")
            continue
        if prefix_match.group(1) != release_date:
            errors.append(
                f"release_date mismatch: {model} table={release_date} file_prefix={prefix_match.group(1)}"
            )
            continue
        if not (ROOT / local_file).exists():
            errors.append(f"missing local PDF: {local_file}")
    return errors


def validate() -> int:
    errors: List[str] = []
    if not README.exists():
        print("ERROR: README.md not found")
        return 1

    text = README.read_text(encoding="utf-8")

    han_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    if han_count > 0:
        errors.append(f"README contains Chinese characters: {han_count}")

    errors.extend(validate_release_prefix_accuracy(text))

    table_counts = parse_readme_table_month_counts(text)
    table_year_counts = parse_readme_table_year_counts(text)
    summary_year_counts = parse_year_summary_counts(text)

    if not MONTHLY_SVG.exists():
        errors.append("missing assets/diagrams/monthly-density.svg")
    if not TIMELINE_SVG.exists():
        errors.append("missing assets/diagrams/release-timeline.svg")

    if MONTHLY_JSON.exists():
        generated_monthly_counts = load_generated_monthly_counts()
        if dict(sorted(table_counts.items())) != dict(sorted(generated_monthly_counts.items())):
            errors.append("monthly counts mismatch: README table vs monthly_density.json")

    if TIMELINE_JSON.exists():
        timeline_months = load_generated_timeline_months()
        if sorted(table_counts.keys()) != sorted(timeline_months):
            errors.append("month coverage mismatch: README table vs release_timeline.json")

    if dict(sorted(table_year_counts.items())) != dict(sorted(summary_year_counts.items())):
        errors.append("yearly counts mismatch: README table vs year summary headers")

    if "```mermaid" in text:
        errors.append("README still contains Mermaid diagrams")
    if "assets/diagrams/release-timeline.svg" not in text:
        errors.append("README missing release timeline SVG reference")
    if "assets/diagrams/monthly-density.svg" not in text:
        errors.append("README missing monthly density SVG reference")

    if MONTHLY_SVG.exists():
        monthly_svg = MONTHLY_SVG.read_text(encoding="utf-8")
        expected_monthly_counts = load_generated_monthly_counts() if MONTHLY_JSON.exists() else dict(table_counts)
        for month, count in expected_monthly_counts.items():
            if f'data-month="{month}"' not in monthly_svg:
                errors.append(f"monthly SVG missing month node: {month}")
            if f'data-count="{count}"' not in monthly_svg:
                errors.append(f"monthly SVG missing count marker: {month} -> {count}")

    if TIMELINE_SVG.exists():
        timeline_svg = TIMELINE_SVG.read_text(encoding="utf-8")
        for month in table_counts.keys():
            if month not in timeline_svg:
                errors.append(f"timeline SVG missing month label: {month}")

    if errors:
        print("SOP validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SOP validation passed")
    print(f"models={len(parse_readme_table_rows(text))}")
    print(f"months={len(table_counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
