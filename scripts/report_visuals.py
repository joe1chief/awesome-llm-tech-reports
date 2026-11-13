from __future__ import annotations

import hashlib
import html
import json
import math
import textwrap
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from report_terms import BODY_SOURCES, word_cloud_data

PAPER = "#f8f7f2"
INK = "#201f1b"
MUTED = "#716b60"
RULE = "#dcd6c8"
PREVIEW_LIMIT = 10
CLOUD_LIMIT = 64
CLOUD_WIDTH, CLOUD_HEIGHT = 1120, 600
PALETTE = ["#b6472f", "#137f72", "#7545b7", "#2555bd", "#946410", "#c23966", "#086f96", "#3f7550"]
BRANDS = {
    "Anthropic": "#b6472f",
    "OpenAI": "#137f72",
    "Google": "#2555bd",
    "Meta": "#7545b7",
    "DeepSeek": "#086f96",
    "Zhipu AI": "#893fbd",
    "MiniMax": "#c23966",
    "Alibaba": "#c35216",
    "Meituan": "#946410",
    "Moonshot AI": "#a130a1",
    "xAI": "#20212b",
    "Tencent": "#247553",
    "ByteDance": "#1984bf",
    "StepFun": "#a8720a",
    "Baidu": "#453eb4",
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def escape(value):
    return html.escape(str(value), quote=True)


def brand_color(org):
    digest = hashlib.sha256(org.encode()).digest()
    return BRANDS.get(org, PALETTE[digest[0] % len(PALETTE)])


def svg_start(width, height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        f"<title>{escape(title)}</title><desc>{escape(description)}</desc>",
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
    ]


def svg_text(x, y, value, size=14, color=INK, *, serif=False, weight=400):
    family = ' font-family="Georgia,serif"' if serif else ' font-family="Inter,Arial,sans-serif"'
    return (
        f'<text{family} x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}">{escape(value)}</text>'
    )


def svg_line(x1, y1, x2, y2):
    return f'<path d="M{x1} {y1}H{x2}V{y2}" stroke="{RULE}" fill="none"/>'


def year_stats(rows):
    latest = max(row["released_on"] for row in rows)
    days = [date.fromisoformat(row["released_on"]) for row in rows if len(row["released_on"]) == 10]
    recent = "—"
    if len(latest) == 10 and days:
        end = date.fromisoformat(latest)
        recent = str(sum(end - timedelta(days=71) <= item <= end for item in days))
    return [
        (str(len(rows)), "Releases"),
        (str(len({row["org"] for row in rows})), "Organizations"),
        (f"{len(rows) / int(latest[5:7]):.1f}", "Per month"),
        (recent, "Last 72 days"),
    ]


def month_rows(rows, month):
    return sorted(
        (row for row in rows if int(row["released_on"][5:7]) == month),
        key=lambda row: (len(row["released_on"]) == 7, row["released_on"], row["org"], row["model"]),
    )


def form_label(row):
    badges = list(row.get("forms", []))
    if not row.get("report"):
        badges.append("Report pending")
    return " · ".join(badges)


def preview_events(rows):
    def priority(row):
        report = row.get("report") or {}
        return (
            not row.get("featured"),
            row.get("follow_up", False),
            not any(notice in row.get("forms", []) for notice in ("Preview", "General availability", "Open weights")),
            report.get("kind") not in {"technical report", "system card", "archive"},
        )

    return sorted(sorted(rows, key=lambda row: row["released_on"], reverse=True), key=priority)[:PREVIEW_LIMIT]


def timeline_svg(year, rows):
    width, left, right = 2000, 50, 1950
    columns = (right - left) / 12
    groups = [month_rows(rows, month) for month in range(1, 13)]
    vendors = Counter(row["org"] for row in rows)
    legend = sorted(vendors, key=lambda org: (-vendors[org], org))
    legend_y = 176
    legend_x = left
    legend_items = []
    for org in legend:
        span = max(60, len(org) * 7 + len(str(vendors[org])) * 7 + 31)
        if legend_x + span > right:
            legend_x, legend_y = left, legend_y + 20
        legend_items.append(f'<circle cx="{legend_x + 3}" cy="{legend_y - 4}" r="3.5" fill="{brand_color(org)}"/>')
        legend_items.append(svg_text(legend_x + 14, legend_y, f"{org}  {vendors[org]}", 11))
        legend_x += span

    month_y = legend_y + 43
    content_top = month_y + 29
    max_bottom = content_top
    body = []
    for index, group in enumerate(groups):
        x = round(left + index * columns)
        shown = sorted(preview_events(group), key=lambda row: (row["released_on"], row["model"]))
        body.append(svg_text(x, month_y, f"{index + 1:02d}", 23, serif=True))
        body.append(svg_text(x + 35, month_y - 1, f"{len(group)} releases", 10, MUTED))
        y = content_top
        if not group:
            body.append(svg_text(x, y + 5, "No releases", 10, MUTED))
            continue
        for row in shown:
            color = brand_color(row["org"])
            published = row["released_on"]
            day = published[5:].replace("-", ".") if len(published) == 10 else published[5:7]
            name_lines = textwrap.wrap(row["model"], width=21)
            body.append(svg_line(x + 3, y, x + 3, y + 26 + 13 * (len(name_lines) - 1)))
            body.append(f'<circle cx="{x + 3}" cy="{y}" r="3.5" fill="{color}" stroke="{PAPER}" stroke-width="1"/>')
            org = textwrap.shorten(row["org"], width=19, placeholder="…")
            badge = next((item for item in row.get("forms", []) if item), "")
            body.append(svg_text(x + 13, y + 3, f"{day}  {org}", 9, color, weight=600))
            for line_index, line in enumerate(name_lines):
                body.append(svg_text(x + 13, y + 17 + line_index * 13, line, 13, weight=600))
            y += 29 + (len(name_lines) - 1) * 13
            if badge:
                body.append(svg_text(x + 13, y - 1, badge, 8, MUTED))
                y += 9
        if extra := len(group) - len(shown):
            body.append(svg_text(x + 13, y + 4, f"+{extra} on the full timeline", 9, MUTED))
            y += 16
        max_bottom = max(max_bottom, y)

    notes_y = max(max_bottom + 29, 573)
    height = notes_y + 89
    parts = svg_start(width, height, f"{year} model releases", "Annual overview with up to ten releases per month.")
    parts.extend([
        svg_text(left, 42, f"AI MODEL RELEASE TIMELINE  /  {year}", 12, MUTED, weight=600),
        svg_text(left, 99, f"{year}  Model releases", 53, serif=True),
        svg_text(left, 130, "January–December  ·  One dot per release event  ·  Color by organization", 13, MUTED),
        svg_line(left, 153, right, 153),
        *legend_items,
        svg_line(left, month_y + 12, right, month_y + 12),
        *body,
    ])
    for index, (value, label) in enumerate(year_stats(rows)):
        x = 1430 + index * 131
        parts.extend([svg_text(x, 78, value, 32, serif=True), svg_text(x, 101, label, 11, MUTED)])
    busiest = max(range(12), key=lambda index: len(groups[index]))
    pending = sum(not row.get("report") for row in rows)
    parts.extend([
        svg_line(left, notes_y, right, notes_y),
        svg_text(left, notes_y + 21, f"{year} RELEASE NOTES", 10, MUTED, weight=600),
        svg_text(left, notes_y + 42, f"Busiest month: {MONTHS[busiest]} ({len(groups[busiest])} releases)", 13, weight=600),
        svg_text(570, notes_y + 42, f"{pending} release events awaiting documentation", 13, weight=600),
        svg_text(1060, notes_y + 42, "Preview · Open weights · General availability", 12, MUTED),
        svg_text(left, notes_y + 67,
                 "Each month shows up to 10 events. Counts cover the complete catalog. Month-only dates are shown as MM.",
                 11, MUTED),
    ])
    return "\n".join([*parts, "</svg>", ""])



def frequencies(rows, glossary):
    return word_cloud_data(rows, glossary, {})[0] if rows else []


def cloud_position(term, size, placed):
    width, height = CLOUD_WIDTH, CLOUD_HEIGHT
    word_width = round(sum(0.9 if c in "MWmw" else 0.43 if c in "Iiljt- " else 0.65 for c in term) * size) + 13
    word_height = math.ceil(size * 1.16) + 7
    x_positions = range(28, width - 27 - word_width, 6)
    y_positions = range(108, height - 44 - word_height, 6)
    positions = sorted(
        ((x, y) for y in y_positions for x in x_positions),
        key=lambda point: (
            ((point[0] + word_width / 2 - width / 2) / 2.2) ** 2
            + (point[1] + word_height / 2 - (height + 57) / 2) ** 2
        ),
    )
    for x, y in positions:
        right, bottom = x + word_width, y + word_height
        if all(right <= a or b <= x or bottom <= c or d <= y for a, c, b, d in placed):
            return x, y, right, bottom
    return None


def wordcloud_svg(year, counts, coverage):
    width, height = CLOUD_WIDTH, CLOUD_HEIGHT
    body_count = sum(coverage.get(source, 0) for source in BODY_SOURCES)
    document_count = sum(coverage.values())
    parts = svg_start(
        width,
        height,
        f"{year} technical word cloud",
        "Word size reflects the number of distinct documents mentioning a technical term.",
    )
    parts.append(svg_text(30, 42, f"TECHNICAL WORD CLOUD  /  {year}", 12, MUTED, weight=600))
    parts.append(svg_text(29, 79, "Terms across model reports", 32, serif=True))
    parts.append(svg_line(29, 94, 1091, 94))
    placed = []
    displayed = []
    for index, (term, count) in enumerate(counts[:CLOUD_LIMIT]):
        size = round(14 + 35 * math.sqrt(count / counts[0][1]))
        size = max(14, min(size, 48 - round(32 * index / (CLOUD_LIMIT - 1))))
        for candidate in range(size, 13, -2):
            if bounds := cloud_position(term, candidate, placed):
                placed.append(bounds)
                displayed.append(term)
                color = PALETTE[index % len(PALETTE)]
                parts.append(svg_text(bounds[0] + 6, bounds[1] + candidate, term, candidate, color, weight=700))
                break
            size -= 3
    if not placed:
        parts.append(svg_text(30, 160, "Terms appear when verified reports are added.", 15, MUTED))
    parts.append(svg_line(29, height - 41, 1091, height - 41))
    parts.append(
        svg_text(30, height - 17, (
            f"{body_count} of {document_count} documents with source text  ·  "
            f"{len(displayed)} terms shown  ·  One count per document"
        ), 12, MUTED)
    )
    return "\n".join([*parts, "</svg>", ""]), displayed


def timeline_html(by_year):
    parts = [
        """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Model release timeline</title>
<style>
:root{color:#201f1b;background:#f8f7f2;font:15px/1.5 Inter,system-ui,sans-serif}
body{max-width:1680px;margin:0 auto;padding:clamp(18px,4vw,52px)}
a{color:inherit;text-decoration-thickness:1px;text-underline-offset:3px}
header a{color:#716b60} h1,h2,h3{font-family:Georgia,serif;font-weight:400}
h1{font-size:clamp(2.6rem,6vw,4.8rem);line-height:1;margin:.45em 0 .2em}
h2{font-size:2rem;margin:.3em 0} h3{margin:0 0 14px}
.year{margin:42px 0;border-top:1px solid #dcd6c8;padding-top:16px}
.stats{display:flex;gap:26px;flex-wrap:wrap;margin:0 0 16px;color:#716b60}
.stats strong{font:1.5rem Georgia,serif;color:#201f1b}
.months{display:grid;grid-template-columns:repeat(12,minmax(142px,1fr));overflow:auto;padding-bottom:14px}
.month{min-width:0;padding:10px 12px;border-left:1px solid #dcd6c8}
article{border-left:2px solid var(--brand);padding:0 0 0 8px;margin:0 0 15px}
article a{font-weight:650;overflow-wrap:anywhere}
.kicker{display:block;color:var(--brand);font-size:.74rem}
.note{font-size:.83rem;color:#716b60;margin:4px 0}
@media(max-width:650px){.months{grid-template-columns:repeat(2,minmax(0,1fr));overflow:visible}.month{border-top:1px solid #dcd6c8}}
</style>
<header><a href="./">Technical reports</a><h1>Model release timeline</h1>
<p class="note">Dates reflect the precision available in the catalog. The 72-day count uses day-level dates.</p></header>
<main>"""
    ]
    for year, rows in by_year.items():
        parts.append(f'<section class="year"><h2>{year}</h2><div class="stats">')
        for value, label in year_stats(rows):
            parts.append(f"<span><strong>{value}</strong> {label}</span>")
        parts.append('</div><div class="months">')
        for month in range(1, 13):
            group = month_rows(rows, month)
            parts.append(f'<section class="month"><h3>{MONTHS[month - 1]} <small>{len(group)}</small></h3>')
            for row in group:
                report = row.get("report")
                url = report["url"] if report and not row.get("follow_up") else row["release_url"]
                color = brand_color(row["org"])
                parts.append(
                    f'<article style="--brand:{color}"><span class="kicker">'
                    f"{escape(row['released_on'])} · {escape(row['org'])}</span>"
                    f'<a href="{escape(url)}">{escape(row["model"])}</a>'
                )
                if badge := form_label(row):
                    parts.append(f'<div class="note">{escape(badge)}</div>')
                parts.append("</article>")
            parts.append("</section>")
        parts.append("</div></section>")
    return "\n".join([*parts, "</main>", "</html>", ""])


def build_visuals(rows, glossary, portal, *, featured=(), text_index=None):
    events = [*rows, *({**row, **event, "follow_up": True} for row in rows for event in row.get("release_events", []))]
    events = [
        {**row, "featured": (row.get("key"), row["released_on"]) in featured}
        for row in events
    ]
    years = sorted({row["released_on"][:4] for row in events}, reverse=True)
    by_year = {year: [row for row in events if row["released_on"].startswith(year)] for year in years}
    year = years[0]
    latest = by_year[year]
    counts, coverage = word_cloud_data(rows, glossary, text_index or {})
    diagrams = Path("assets/diagrams")
    overview = diagrams / f"release-timeline-{year}.svg"
    cloud = diagrams / f"technical-word-cloud-{year}.svg"
    terms = Path("docs/data/word-cloud.json")
    cloud_svg, displayed = wordcloud_svg(year, counts, coverage)
    outputs = {
        overview: timeline_svg(year, latest),
        cloud: cloud_svg,
        Path("docs/assets/diagrams/technical-word-cloud.svg"): cloud_svg,
        terms: json.dumps({
            "year": int(year), "coverage": coverage, "displayed_terms": displayed, "terms": dict(counts),
        }, indent=2) + "\n",
        Path("docs/timeline.html"): timeline_html(by_year),
    }
    sections = "\n".join(
        [
            "## Release Timeline",
            "",
            f"[Browse the full timeline and release sources]({portal}/timeline.html)",
            "",
            f"![{year} model release overview]({overview})",
            "",
            "## Technical Word Cloud",
            "",
            f"![{year} technical terms sized by document frequency]({cloud})",
            "",
            f"[Word frequencies]({terms})",
        ]
    )
    return outputs, sections
