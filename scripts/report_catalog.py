from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from parse_readme import build_dataset, classify_camp, extract_tags, is_milestone, parse_models
from report_terms import term_index
from report_visuals import build_visuals

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("data/catalog.json")
README = Path("README.md")
MODELS = Path("docs/data/models.json")
PORTAL = "https://joe1chief.github.io/awesome-llm-tech-reports"
MONTH = re.compile(r"\d{4}-\d{2}")
PDF_PATH = re.compile(r"(?:20\d{2}/[a-z0-9_]+|pdf)/[A-Za-z0-9_.()-]+\.pdf")
MARKDOWN_CELL = re.compile(r"([\\|\[\]_*])")
REPORT_KINDS = {"archive", "technical report", "system card", "model card", "official technical page"}


def json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def put(path, content):
    if not path.is_file() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(path)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def https_url(value):
    try:
        url = urlsplit(value)
        return bool(
            url.scheme == "https"
            and url.hostname
            and not url.username
            and not url.password
            and url.port in (None, 443)
            and not re.search(r"[\s<>\"\\]", value)
        )
    except ValueError:
        return False


def parse_release_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value):
        raise ValueError(f"Invalid catalog date {value!r}")
    return date.fromisoformat(value + "-01" if MONTH.fullmatch(value) else value)


def read_catalog(root=ROOT):
    data = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    if data["version"] != 1:
        raise ValueError("Unsupported catalog version")
    return data["releases"]


def import_catalog(root=ROOT):
    baseline = parse_models(root / README)
    if not baseline:
        raise ValueError("No historical model rows found")
    rows = []
    for model in baseline:
        vendor = model["file"].split("/")[1]
        rows.append(
            {
                "id": model["id"],
                "key": f"{vendor}/{slug(model['model'])}",
                "model": model["model"],
                "org": model["org"],
                "released_on": model["date"],
                "release_url": model["link"],
                "report": {
                    "id": model["link"],
                    "kind": "archive",
                    "url": model["link"],
                    "file": model["file"],
                    "highlights": model["highlights"],
                },
            }
        )
    return rows


def save_catalog(rows, root=ROOT):
    put(root / CATALOG, json_text({"version": 1, "releases": rows}))


def validate(rows, root=ROOT, pdf_manifest=None, check_files=True):
    ids, keys = set(), set()
    for row in rows:
        key = row["key"]
        if not re.fullmatch(r"[a-z0-9_]+/[a-z0-9]+(?:-[a-z0-9]+)*", key):
            raise ValueError(f"Invalid release key {key}")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", row["id"]):
            raise ValueError(f"Invalid model ID for {key}")
        if key in keys or row["id"] in ids:
            raise ValueError(f"Duplicate release identity {key}")
        keys.add(key)
        ids.add(row["id"])
        parse_release_date(row["released_on"])
        if not https_url(row["release_url"]):
            raise ValueError(f"Invalid release URL for {key}")
        if "total_parameters" in row and (type(row["total_parameters"]) is not int or row["total_parameters"] <= 0):
            raise ValueError(f"Invalid total parameters for {key}")
        dates = {row["released_on"]}
        for event in row.get("release_events", []):
            day = event["released_on"]
            parse_release_date(day)
            if len(day) != 10 or day <= row["released_on"] or day in dates or not https_url(event["release_url"]):
                raise ValueError(f"Invalid follow-up release for {key}")
            dates.add(day)
        report = row.get("report")
        if report is None:
            continue
        if report["kind"] not in REPORT_KINDS:
            raise ValueError(f"Invalid report type for {key}")
        if not https_url(report["url"]):
            raise ValueError(f"Invalid report URL for {key}")
        file = report.get("file")
        if not file:
            continue
        if not PDF_PATH.fullmatch(file):
            raise ValueError(f"Invalid archive path for {key}")
        for path in (file, "pdf/" + Path(file).name):
            if check_files and not (
                (root / path).is_file() or pdf_manifest is not None and path in pdf_manifest
            ):
                raise ValueError(f"Missing PDF {path}")


def portal_models(rows):
    models = []
    for row in rows:
        report = row.get("report")
        if not report:
            continue
        released = row["released_on"]
        highlights = report.get("highlights", "")
        tags = extract_tags(row["model"], highlights, report["url"])
        has_weights = any("Open weights" in event.get("forms", []) for event in [row, *row.get("release_events", [])])
        if has_weights and "Open Weights" not in tags:
            tags.append("Open Weights")
        model = {
            "id": row["id"],
            "date": released[:7],
            "year": int(released[:4]),
            "month": int(released[5:7]),
            "org": row["org"],
            "model": row["model"],
            "highlights": highlights,
            "link": report["url"],
            "file": report.get("file", ""),
            "camp": classify_camp(row["org"]),
            "is_milestone": is_milestone(row["model"], highlights),
            "tags": tags,
        }
        if len(released) == 10:
            model["released_on"] = released
        if report["kind"] != "archive":
            model["report_kind"] = report["kind"]
        if row.get("total_parameters"):
            model["total_parameters"] = row["total_parameters"]
        if report.get("published_on"):
            model["document_published_on"] = report["published_on"]
        models.append(model)
    return build_dataset(models)


def md_cell(value):
    safe = html.escape(" ".join(value.split()), quote=False)
    return MARKDOWN_CELL.sub(r"\\\1", safe)


def update_readme(text, dataset, visual_sections, rows):
    models = sorted(
        (row for row in rows if row.get("report")), key=lambda row: row["released_on"], reverse=True
    )
    date_range = dataset["stats"]["date_range"]
    first, last = date_range["start"], date_range["end"]
    text = re.sub(
        r"(?m)^# Awesome LLM Technical Reports.*$",
        f"# Awesome LLM Technical Reports ({first} ~ {last})",
        text,
        count=1,
    )
    time_badge = f"Time%20Range-{first.replace('-', '--')}%20to%20{last.replace('-', '--')}-4c1"
    text = re.sub(r"Time%20Range-[^\" ]+", time_badge, text, count=1)
    text = re.sub(r"Models-\d+-blue", f"Models-{len(models)}-blue", text, count=1)
    pdf_count = sum(bool(model["report"].get("file")) for model in models)
    text = re.sub(r"Local%20PDF-\d+-success", f"Local%20PDF-{pdf_count}-success", text, count=1)
    text = re.sub(
        r"(?m)^- (?:Systematically archives major model releases from|Archives model reports from) .*$",
        f"- Archives model reports from **{first}** through **{last}** across LLM, multimodal and medical domains.",
        text,
        count=1,
    )
    toc = "- [Release Timeline](#release-timeline)\n"
    word_cloud = "- [Technical Word Cloud](#technical-word-cloud)\n"
    if word_cloud not in text:
        text = text.replace(toc, toc + word_cloud, 1)
    start, stop = text.index("## Release Timeline\n"), text.index("## Company Quick Links\n")
    text = text[:start] + visual_sections + "\n\n" + text[stop:]
    start, stop = text.index("## Model Index (Folded by Year)\n"), text.index("## Star History\n")
    sections = ["## Model Index (Folded by Year)", ""]
    years = sorted({m["released_on"][:4] for m in models}, reverse=True)
    for index, year in enumerate(years):
        year_models = [m for m in models if m["released_on"].startswith(year)]
        sections.extend(
            [
                "<details open>" if index == 0 else "<details>",
                f"<summary><b>{year} ({len(year_models)} models)</b></summary>",
                "",
                "| Release Date | Organization | Model | Core Highlights | Official Link | Local File |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for model in year_models:
            report = model["report"]
            source = report["url"]
            cells = (
                model["released_on"],
                model["org"],
                model["model"],
                report.get("highlights", ""),
                source.replace("|", "%7C"),
                report.get("file") or report["kind"].capitalize(),
            )
            safe = [cell if i == 4 else md_cell(cell) for i, cell in enumerate(cells)]
            sections.append("| " + " | ".join(safe) + " |")
        sections.extend(["", "</details>", "", "---", ""])
    return text[:start] + "\n".join(sections) + "\n" + text[stop:]


def build(root=ROOT, check=False, pdf_manifest=None, *, rows=None):
    publishing = rows is not None
    if rows is None:
        rows = read_catalog(root)
    if not rows:
        raise ValueError("The model catalog is empty")
    validate(rows, root, pdf_manifest=pdf_manifest)
    dataset = portal_models(rows)
    terms = json.loads((root / "configs/report-terms.json").read_text(encoding="utf-8"))
    backfill_path = root / "configs/report-backfill.json"
    featured = set()
    if backfill_path.is_file():
        backfill = json.loads(backfill_path.read_text(encoding="utf-8"))
        featured = {
            (f"{vendor}/{slug(item['model'])}", item["released_on"])
            for vendor, items in backfill.items() for item in items
        }
    visuals, readme_sections = build_visuals(rows, terms, PORTAL, featured=featured, text_index=term_index(root, terms))
    outputs = {MODELS: json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", **visuals}
    outputs[README] = update_readme(
        (root / README).read_text(encoding="utf-8"), dataset, readme_sections, rows
    )
    if publishing:
        outputs[CATALOG] = json_text({"version": 1, "releases": rows})
    mismatches = []
    for file, content in outputs.items():
        path = root / file
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                mismatches.append(str(file))
        else:
            put(path, content)
    if mismatches:
        raise ValueError("Generated files are stale: " + ", ".join(mismatches))
    print(f"{len(rows)} releases and {len(dataset['models'])} reports validated")
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Build the technical reports catalog")
    parser.add_argument("command", choices=["import", "build", "check"])
    parser.add_argument("--pdf-manifest", type=Path)
    args = parser.parse_args()
    if args.command == "import":
        if (ROOT / CATALOG).exists():
            parser.error(f"{CATALOG} already exists")
        save_catalog(import_catalog())
    else:
        manifest = set(args.pdf_manifest.read_text().splitlines()) if args.pdf_manifest else None
        build(check=args.command == "check", pdf_manifest=manifest)


if __name__ == "__main__":
    main()
