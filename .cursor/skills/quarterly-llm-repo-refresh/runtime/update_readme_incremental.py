#!/usr/bin/env python3
"""Incrementally update README metrics/model index while preserving style."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from runtime_paths import GENERATED_DIR, LATEST_RESULTS_JSON, README, ROOT

DEFAULT_README = README
DEFAULT_RESULTS_JSON = LATEST_RESULTS_JSON
DEFAULT_GENERATED_DIR = GENERATED_DIR

ASSET_RELEASE_TIMELINE = "assets/diagrams/release-timeline.svg"
ASSET_MONTHLY_DENSITY = "assets/diagrams/monthly-density.svg"

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
DISPLAY_TO_SLUG: Dict[str, str] = {value: key for key, value in ORG_DISPLAY.items()}
ORG_ANCHOR_LABELS: Dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "meta": "Meta",
    "xai": "xAI",
    "deepseek": "DeepSeek",
    "alibaba_qwen": "Alibaba / Qwen",
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
ORG_LINK_LABELS: Dict[str, str] = {
    "alibaba_qwen": "Alibaba",
    "quark": "Quark",
    **{k: v for k, v in ORG_DISPLAY.items() if k not in {"alibaba_qwen", "quark"}},
}
TIMELINE_LANES = [
    ("openai", "OpenAI", "openai"),
    ("anthropic", "Anthropic", "anthropic"),
    ("google", "Google", "google"),
    ("china", "China-based Labs", "china"),
    ("other", "Other Global", "other"),
]
ORG_TO_LANE = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "deepseek": "china",
    "alibaba_qwen": "china",
    "zhipu": "china",
    "moonshot": "china",
    "minimax": "china",
    "stepfun": "china",
    "baidu": "china",
    "baichuan": "china",
    "inclusionai": "china",
    "bytedance": "china",
    "tencent": "china",
    "meituan": "china",
    "quark": "china",
    "meta": "other",
    "xai": "other",
}
IMPACT_MODEL_NAMES = {
    "DeepSeek R1",
    "Qwen3",
    "Llama 4 Scout/Maverick",
    "GPT-5",
    "GPT-5.3-Codex",
    "Claude Opus 4.6",
    "Gemini 2.5 Pro",
    "GLM-5",
    "Kimi K2.5",
    "LongCat-Flash-Prover",
    "Gemma 4",
}

LOCAL_STATUS_MAP = {
    "下载失败": "Download failed",
    "仅在线": "Online only",
    "未发布": "Unreleased",
}
LOCAL_STATUS_VALUES = set(LOCAL_STATUS_MAP.values())


def contains_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def summary_quality_score(text: str) -> int:
    value = (text or "").strip()
    if not value:
        return -10_000
    if contains_han(value):
        return -5_000

    lower = value.casefold()
    score = 0
    if 40 <= len(value) <= 320:
        score += 10
    if len(value.split()) >= 8:
        score += 8
    score += sum(
        3
        for keyword in [
            "model",
            "multimodal",
            "reasoning",
            "agent",
            "agentic",
            "coding",
            "medical",
            "vision",
            "audio",
            "video",
            "proof",
            "benchmark",
        ]
        if keyword in lower
    )
    penalties = [
        "news",
        "who we are",
        "menu",
        "community",
        "discord",
        "log in",
        "sign up",
        "pricing",
        "search",
        "source:",
        "copy page",
    ]
    score -= sum(8 for marker in penalties if marker in lower)
    return score


def normalize_local_file(value: str) -> str:
    value = (value or "").strip()
    return LOCAL_STATUS_MAP.get(value, value)


def is_materialized_local_file(value: str) -> bool:
    value = (value or "").strip()
    return bool(value) and value not in LOCAL_STATUS_VALUES


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
    if row["local_file"]:
        if is_materialized_local_file(row["local_file"]) or not is_materialized_local_file(prev["local_file"]):
            out["local_file"] = row["local_file"]
    if row["core_highlights"]:
        if contains_han(prev["core_highlights"]):
            if not contains_han(row["core_highlights"]):
                out["core_highlights"] = row["core_highlights"]
        elif not contains_han(row["core_highlights"]) and (
            summary_quality_score(row["core_highlights"])
            > summary_quality_score(prev["core_highlights"]) + 2
        ):
            out["core_highlights"] = row["core_highlights"]
    return out


def _should_insert_new_row(row: Dict[str, str]) -> bool:
    return is_materialized_local_file(row["local_file"]) and not contains_han(row["core_highlights"])


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
            if not _should_insert_new_row(row):
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
        if not _should_insert_new_row(row):
            continue
        _insert_row_preserving_style(ordered_rows, row)
        index = {row_key(r): i for i, r in enumerate(ordered_rows)}
    return ordered_rows


def escape_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def infer_org_slug(row: Dict[str, str]) -> str:
    local_file = row.get("local_file", "").strip()
    parts = local_file.split("/")
    if len(parts) >= 2 and re.match(r"^20\d{2}$", parts[0]):
        return parts[1]
    return DISPLAY_TO_SLUG.get(row["organization"], slugify_org_name(row["organization"]))


def slugify_org_name(value: str) -> str:
    slug = value.lower().replace("&", "and")
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")
    return slug or "unknown"


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


def build_monthly_density_data(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, int]]]:
    counts = Counter(r["release_date"] for r in rows)
    return {
        "months": [
            {"month": month, "count": counts[month]}
            for month in sorted(counts.keys())
        ]
    }


def build_release_timeline_data(rows: List[Dict[str, str]]) -> Dict[str, object]:
    months = sorted({row["release_date"] for row in rows})
    lane_map: Dict[str, List[Dict[str, object]]] = {lane_id: [] for lane_id, _, _ in TIMELINE_LANES}
    grouped: Dict[tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        org_slug = infer_org_slug(row)
        lane_id = ORG_TO_LANE.get(org_slug, "other")
        grouped[(lane_id, row["release_date"])].append(row)

    for lane_id, _, _ in TIMELINE_LANES:
        for month in months:
            current = grouped.get((lane_id, month), [])
            if not current:
                continue
            models = [row["model"] for row in current]
            highlighted = [model for model in models if model in IMPACT_MODEL_NAMES]
            lane_map[lane_id].append(
                {
                    "month": month,
                    "models": models,
                    "highlighted_models": highlighted,
                }
            )

    lanes = []
    for lane_id, label, camp in TIMELINE_LANES:
        lanes.append(
            {
                "id": lane_id,
                "label": label,
                "camp": camp,
                "entries": lane_map[lane_id],
            }
        )
    return {"months": months, "lanes": lanes}


def write_generated_diagram_data(rows: List[Dict[str, str]], generated_dir: Path = DEFAULT_GENERATED_DIR) -> None:
    generated_dir.mkdir(parents=True, exist_ok=True)
    (generated_dir / "monthly_density.json").write_text(
        json.dumps(build_monthly_density_data(rows), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (generated_dir / "release_timeline.json").write_text(
        json.dumps(build_release_timeline_data(rows), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def generate_project_scope_section(rows: List[Dict[str, str]]) -> str:
    min_month = min(r["release_date"] for r in rows)
    max_month = max(r["release_date"] for r in rows)
    start_label = datetime_label(min_month)
    end_label = datetime_label(max_month)
    return "\n".join(
        [
            "## Project Scope",
            "",
            f"- Systematically archives major model releases from **{start_label}** to **{end_label}** across LLM, multimodal, and medical-vertical domains.",
            "- Downloads official papers, system cards, model cards as local PDFs; exports web-only blog pages to PDF via headless browser.",
            "- Provides a single searchable Markdown index sorted in reverse chronological order.",
        ]
    )


def datetime_label(month: str) -> str:
    year, mm = month.split("-")
    month_names = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
    return f"{month_names[mm]} {year}"


def generate_release_visual_section() -> str:
    return "\n".join(
        [
            "## Release Timeline",
            "",
            "**Legend (Camp Colors):** `OpenAI` · `Anthropic` · `Google` · `China-based Labs` · `Other Global`  ",
            "**Impact Highlight:** nodes with **★** are ecosystem-shaping releases (community discussion, benchmark influence, or deployment adoption).",
            "",
            f"![Release Timeline]({ASSET_RELEASE_TIMELINE})",
            "",
            "<details>",
            "<summary><b>Monthly Density Snapshot</b></summary>",
            "",
            f"![Monthly Density Snapshot]({ASSET_MONTHLY_DENSITY})",
            "",
            "> Bubble size follows the release count from the model index table.",
            "",
            "</details>",
        ]
    )


def generate_company_links_section(rows: List[Dict[str, str]]) -> str:
    year_to_orgs: Dict[str, List[str]] = defaultdict(list)
    org_years: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        year = row["release_date"][:4]
        org_slug = infer_org_slug(row)
        if org_slug not in year_to_orgs[year]:
            year_to_orgs[year].append(org_slug)
        org_years[org_slug].add(year)

    years = sorted(year_to_orgs.keys(), reverse=True)
    lines = ["## Company Quick Links", ""]
    for year in years:
        links = [
            f"[`{ORG_LINK_LABELS.get(org_slug, org_slug.title())}`](#company-{org_slug})"
            for org_slug in year_to_orgs[year]
        ]
        lines.append(f"`{year}`: " + " · ".join(links))
        lines.append("")

    lines.append("### Company Directory Index")
    lines.append("")
    ordered_orgs = sorted(org_years.keys(), key=lambda slug: (ORG_ANCHOR_LABELS.get(slug, slug), slug))
    for org_slug in ordered_orgs:
        years_for_org = sorted(org_years[org_slug])
        directories = ", ".join(f"`{year}/{org_slug}/`" for year in years_for_org)
        lines.append(f'<a id="company-{org_slug}"></a>')
        lines.append(f"- **{ORG_ANCHOR_LABELS.get(org_slug, org_slug.title())}**: {directories}")
    return "\n".join(lines)


def replace_or_insert_section(text: str, pattern: str, replacement: str, before_header: str) -> str:
    updated, count = re.subn(pattern, replacement.rstrip() + "\n", text, flags=re.S)
    if count:
        return updated
    marker = f"\n{before_header}"
    if marker in text:
        return text.replace(marker, "\n" + replacement.rstrip() + "\n\n" + before_header, 1)
    return text.rstrip() + "\n\n" + replacement.rstrip() + "\n"


def render_updated_readme(
    text: str,
    rows: List[Dict[str, str]],
) -> str:
    if not rows:
        return text

    text = replace_or_insert_section(
        text,
        r"## Project Scope.*?(?=\n## Release Timeline)",
        generate_project_scope_section(rows).rstrip() + "\n",
        "## Model Index (Folded by Year)",
    )
    text = replace_or_insert_section(
        text,
        r"## Release Timeline.*?(?=\n## Company Quick Links)",
        generate_release_visual_section().rstrip() + "\n",
        "## Model Index (Folded by Year)",
    )
    text = replace_or_insert_section(
        text,
        r"## Company Quick Links.*?(?=\n## Model Index \(Folded by Year\))",
        generate_company_links_section(rows).rstrip() + "\n",
        "## Model Index (Folded by Year)",
    )

    model_index = generate_model_index_section(rows)
    text = re.sub(
        r"## Model Index \(Folded by Year\).*?(?=\n## Star History)",
        model_index.rstrip() + "\n\n",
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
    write_generated_diagram_data(merged_rows)

    output = args.output or args.readme
    output.write_text(out_text, encoding="utf-8")
    print(f"README updated: {output}")
    print(f"rows_total={len(merged_rows)}")
    print(f"rows_from_run={len(run_rows)}")
    print(f"mode={'from-scratch' if args.from_scratch else 'incremental'}")


if __name__ == "__main__":
    main()
