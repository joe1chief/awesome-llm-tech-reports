#!/usr/bin/env python3
"""Incrementally update README metrics/model index while preserving style."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_README = ROOT / "README.md"
DEFAULT_RESULTS_JSON = ROOT / "scripts" / "latest_download_results.json"

ORG_DISPLAY: Dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "meta": "Meta",
    "xai": "xAI",
    "deepseek": "DeepSeek",
    "alibaba_qwen": "Alibaba",
    "zhipu": "Zhipu AI",
    "moonshot": "Moonshot AI",
    "minimax": "MiniMax",
    "stepfun": "StepFun",
    "baidu": "Baidu",
    "baichuan": "Baichuan Intelligence",
    "inclusionai": "InclusionAI (Ant Group)",
    "bytedance": "ByteDance",
    "tencent": "Tencent",
    "meituan": "Meituan",
    "quark": "Quark (Alibaba)",
}

LOCAL_STATUS_MAP = {
    "下载失败": "Download failed",
    "仅在线": "Online only",
    "未发布": "Unreleased",
}


def contains_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def normalize_local_file(value: str) -> str:
    value = (value or "").strip()
    return LOCAL_STATUS_MAP.get(value, value)


def row_key(row: Dict[str, str]) -> tuple[str, str]:
    return row["release_date"], row["model"].strip().lower()


def parse_existing_rows(text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| Release Date") or line.startswith("| ---"):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 6:
            continue
        if not re.match(r"^20\d{2}-\d{2}$", parts[0]):
            continue
        rows.append(
            {
                "release_date": parts[0],
                "organization": parts[1],
                "model": parts[2],
                "core_highlights": parts[3],
                "official_link": parts[4],
                "local_file": parts[5],
            }
        )
    return rows


def rows_from_results(results: Iterable[dict]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in results:
        release_date = str(r.get("release_date", "")).strip()
        model = str(r.get("model", "")).strip()
        if not re.match(r"^20\d{2}-\d{2}$", release_date) or not model:
            continue
        org_slug = str(r.get("org_slug", "")).strip()
        organization = ORG_DISPLAY.get(org_slug, str(r.get("org", "")).strip())
        rows.append(
            {
                "release_date": release_date,
                "organization": organization,
                "model": model,
                "core_highlights": str(r.get("core_feature", "")).strip(),
                "official_link": str(r.get("official_link", "")).strip(),
                "local_file": normalize_local_file(str(r.get("local_file_path", "")).strip()),
            }
        )
    return rows


def _merge_row_content(prev: Dict[str, str], row: Dict[str, str]) -> Dict[str, str]:
    out = dict(prev)
    out["organization"] = row["organization"] or prev["organization"]
    out["official_link"] = row["official_link"] or prev["official_link"]
    out["local_file"] = row["local_file"] or prev["local_file"]
    if row["core_highlights"]:
        if not contains_han(row["core_highlights"]) or contains_han(prev["core_highlights"]):
            out["core_highlights"] = row["core_highlights"]
    return out


def _insert_row_preserving_style(ordered_rows: List[Dict[str, str]], row: Dict[str, str]) -> None:
    # Keep existing visual order stable; only insert new rows by release month position.
    insert_idx = len(ordered_rows)
    for i, existing in enumerate(ordered_rows):
        if existing["release_date"] < row["release_date"]:
            insert_idx = i
            break
    ordered_rows.insert(insert_idx, dict(row))


def merge_rows(
    existing_rows: List[Dict[str, str]],
    run_rows: List[Dict[str, str]],
    from_scratch: bool,
) -> List[Dict[str, str]]:
    if from_scratch:
        # Rebuild from current run, but preserve existing ordering/style where keys already exist.
        existing_map = {row_key(r): r for r in existing_rows}
        run_map = {row_key(r): r for r in run_rows}
        ordered_rows: List[Dict[str, str]] = []
        used = set()
        for old in existing_rows:
            key = row_key(old)
            if key not in run_map:
                continue
            ordered_rows.append(_merge_row_content(old, run_map[key]))
            used.add(key)
        for row in run_rows:
            key = row_key(row)
            if key in used:
                continue
            _insert_row_preserving_style(ordered_rows, row)
            used.add(key)
        return ordered_rows

    ordered_rows = [dict(r) for r in existing_rows]
    index = {row_key(r): i for i, r in enumerate(ordered_rows)}

    for row in run_rows:
        key = row_key(row)
        if key in index:
            i = index[key]
            ordered_rows[i] = _merge_row_content(ordered_rows[i], row)
            continue
        _insert_row_preserving_style(ordered_rows, row)
        index = {row_key(r): i for i, r in enumerate(ordered_rows)}
    return ordered_rows


def escape_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def generate_model_index_section(rows: List[Dict[str, str]]) -> str:
    by_year: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_year[row["release_date"][:4]].append(row)

    years = sorted(by_year.keys(), reverse=True)
    lines: List[str] = ["## Model Index (Folded by Year)", ""]
    for i, year in enumerate(years):
        year_rows = by_year[year]
        details_tag = "<details open>" if i == 0 else "<details>"
        lines.append(details_tag)
        lines.append(f"<summary><b>{year} ({len(year_rows)} models)</b></summary>")
        lines.append("")
        lines.append(
            "| Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in year_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        escape_md_cell(row["release_date"]),
                        escape_md_cell(row["organization"]),
                        escape_md_cell(row["model"]),
                        escape_md_cell(row["core_highlights"]),
                        escape_md_cell(row["official_link"]),
                        escape_md_cell(row["local_file"]),
                    ]
                )
                + " |"
            )
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_existing_snapshot_classdefs(text: str) -> Dict[int, str]:
    m = re.search(
        r"<summary><b>Monthly Density Snapshot</b></summary>\s*```mermaid(.*?)```",
        text,
        flags=re.S,
    )
    if not m:
        return {}
    block = m.group(1)
    out: Dict[int, str] = {}
    for cnt, style in re.findall(r"^\s*classDef\s+b(\d+)\s+(.+);", block, flags=re.M):
        out[int(cnt)] = style.strip()
    return out


def build_snapshot_details(rows: List[Dict[str, str]], existing_defs: Dict[int, str] | None = None) -> str:
    counts = Counter(r["release_date"] for r in rows)
    months = sorted(counts.keys())
    if not months:
        return ""

    node_ids = [f"M{i + 1}" for i in range(len(months))]
    node_lines = []
    for node, month in zip(node_ids, months):
        yy, mm = month[2:4], month[5:7]
        node_lines.append(f'{node}(("{yy}-{mm}<br/>R{counts[month]:02d}"))')

    chain = " --> ".join(node_lines)

    unique_counts = sorted(set(counts.values()))
    existing_defs = existing_defs or {}
    class_defs: List[str] = []
    for cnt in unique_counts:
        if cnt in existing_defs:
            class_defs.append(f"  classDef b{cnt} {existing_defs[cnt]};")
            continue
        if cnt <= 1:
            fill, stroke = "#f8fafc", "#94a3b8"
        elif cnt <= 2:
            fill, stroke = "#eef2ff", "#818cf8"
        elif cnt <= 3:
            fill, stroke = "#dbeafe", "#3b82f6"
        elif cnt <= 5:
            fill, stroke = "#bfdbfe", "#2563eb"
        elif cnt <= 8:
            fill, stroke = "#a5b4fc", "#4f46e5"
        else:
            fill, stroke = "#6366f1", "#312e81"
        stroke_width = min(1 + cnt, 6)
        font_size = min(10 + cnt * 2, 24)
        class_defs.append(
            f"  classDef b{cnt} fill:{fill},stroke:{stroke},stroke-width:{stroke_width}px,color:#000000,font-size:{font_size}px;"
        )

    node_map: Dict[int, List[str]] = defaultdict(list)
    for node, month in zip(node_ids, months):
        node_map[counts[month]].append(node)

    class_assign = [
        f"  class {','.join(nodes)} b{cnt};" for cnt, nodes in sorted(node_map.items(), key=lambda x: x[0])
    ]

    lines = [
        "<details>",
        "<summary><b>Monthly Density Snapshot</b></summary>",
        "",
        "```mermaid",
        "%%{init: {",
        '  "theme": "base",',
        '  "themeVariables": {',
        '    "background": "#ffffff",',
        '    "primaryColor": "#f8fafc",',
        '    "primaryTextColor": "#000000",',
        '    "lineColor": "#64748b",',
        '    "fontFamily": "Segoe UI, Arial, sans-serif"',
        "  }",
        "}}%%",
        "flowchart LR",
        f"  {chain}",
        "",
    ]
    lines.extend(class_defs)
    lines.append("")
    lines.extend(class_assign)
    lines.extend(
        [
            "```",
            "",
            "> Bubbles show month + release count from the model index table.",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines)


def update_badges(text: str, rows: List[Dict[str, str]]) -> str:
    if not rows:
        return text

    models_count = len(rows)
    local_pdf_count = sum(
        1
        for r in rows
        if r["local_file"].endswith(".pdf") or re.match(r"^\d{4}/.+\.pdf$", r["local_file"])
    )
    min_month = min(r["release_date"] for r in rows)
    max_month = max(r["release_date"] for r in rows)
    time_range = f"{min_month.replace('-', '--')}%20to%20{max_month.replace('-', '--')}"

    text = re.sub(r"(badge/Models-)\d+(-blue)", rf"\g<1>{models_count}\2", text)
    text = re.sub(r"(badge/Local%20PDF-)\d+(-success)", rf"\g<1>{local_pdf_count}\2", text)
    text = re.sub(r"(badge/Time%20Range-)[^\"]+(-4c1)", rf"\g<1>{time_range}\2", text)
    title_range = f"{min_month} ~ {max_month}"
    text = re.sub(
        r"^# Awesome LLM Technical Reports \(\d{4}-\d{2}\s*~\s*\d{4}-\d{2}\)$",
        f"# Awesome LLM Technical Reports ({title_range})",
        text,
        flags=re.M,
    )
    return text


def render_updated_readme(
    text: str,
    rows: List[Dict[str, str]],
) -> str:
    if not rows:
        return text

    snapshot_defs = parse_existing_snapshot_classdefs(text)
    snapshot_block = build_snapshot_details(rows, existing_defs=snapshot_defs)
    if snapshot_block:
        text = re.sub(
            r"<details>\s*\n<summary><b>Monthly Density Snapshot</b></summary>.*?</details>",
            snapshot_block,
            text,
            flags=re.S,
        )

    model_index = generate_model_index_section(rows)
    text = re.sub(
        r"## Model Index \(Folded by Year\).*?(?=\n## Star History)",
        model_index.rstrip(),
        text,
        flags=re.S,
    )

    text = update_badges(text, rows)
    return text


def load_results(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("results json must be a list")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Incrementally update README sections from download results")
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--results-json", type=Path, default=DEFAULT_RESULTS_JSON)
    parser.add_argument("--output", type=Path, help="Optional output README path")
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="Rebuild model-index/snapshot from current results only (do not merge existing rows)",
    )
    args = parser.parse_args()

    readme_text = args.readme.read_text(encoding="utf-8")
    existing_rows = parse_existing_rows(readme_text)
    run_rows = rows_from_results(load_results(args.results_json))
    merged_rows = merge_rows(existing_rows, run_rows, from_scratch=args.from_scratch)
    out_text = render_updated_readme(readme_text, merged_rows)

    output = args.output or args.readme
    output.write_text(out_text, encoding="utf-8")
    print(f"README updated: {output}")
    print(f"rows_total={len(merged_rows)}")
    print(f"rows_from_run={len(run_rows)}")
    print(f"mode={'from-scratch' if args.from_scratch else 'incremental'}")


if __name__ == "__main__":
    main()
