from __future__ import annotations

import hashlib
import html
import json
import math
import re
import textwrap
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

PAPER = "#f8f7f2"
INK = "#201f1b"
MUTED = "#716b60"
RULE = "#dcd6c8"
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
        "<style>text:not([font-family]){font-family:Inter,system-ui,sans-serif}</style>",
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
    ]


def svg_text(x, y, value, size=14, color=INK, *, serif=False, weight=400):
    family = ' font-family="Georgia,serif"' if serif else ""
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


def timeline_svg(year, rows, first, last):
    width = 1120
    groups = [month_rows(rows, month) for month in range(first, last + 1)]
    top = 170
    row_heights = []
    for group in groups:
        row_heights.append(sum(29 + 17 * len(textwrap.wrap(row["model"], width=20)) for row in group))
    height = top + max(max(row_heights), 100) + 58
    desc = f"Monthly model release timeline for {MONTHS[first - 1]}–{MONTHS[last - 1]} {year}"
    parts = svg_start(width, height, f"{year} model releases", desc)
    parts.append(svg_text(29, 37, "MODEL RELEASE TIMELINE", 12, MUTED, weight=600))
    parts.append(svg_text(28, 88, f"{year}  Model releases", 46, serif=True))
    parts.append(
        svg_text(30, 117, f"{MONTHS[first - 1]}–{MONTHS[last - 1]}  /  Dates from the catalog", 13, MUTED)
    )
    for index, (value, label) in enumerate(year_stats(rows)):
        x = 664 + index * 107
        parts.extend([svg_text(x, 64, value, 27, serif=True), svg_text(x, 87, label, 11, MUTED)])
    parts.append(svg_line(28, 135, 1092, 135))
    for index, group in enumerate(groups):
        month = first + index
        x = 29 + index * 177
        parts.append(svg_text(x, 159, f"{month:02d}", 22, serif=True))
        parts.append(svg_text(x + 37, 158, f"{len(group)} releases", 10, MUTED))
        y = top + 14
        if group:
            parts.append(svg_line(x + 3, y, x + 3, top + row_heights[index] - 6))
        else:
            parts.append(svg_text(x, y + 6, "No catalog entries", 11, MUTED))
        for row in group:
            color = brand_color(row["org"])
            published = row["released_on"]
            label = published[5:].replace("-", ".") if len(published) == 10 else published[5:7]
            parts.append(
                f'<circle cx="{x + 3}" cy="{y}" r="3.5" fill="{color}" stroke="{PAPER}" stroke-width="1.5"/>'
            )
            parts.append(svg_text(x + 13, y + 4, f"{label}  {row['org']}", 10, color, weight=650))
            name_lines = textwrap.wrap(row["model"], width=20)
            for line_index, line in enumerate(name_lines):
                parts.append(svg_text(x + 13, y + 24 + line_index * 16, line, 14, weight=600))
            if badge := form_label(row):
                parts.append(svg_text(x + 13, y + 20 + len(name_lines) * 17, badge[:27], 9, MUTED))
            y += 29 + 17 * len(name_lines)
    parts.append(svg_line(29, height - 38, 1092, height - 38))
    parts.append(
        svg_text(
            30,
            height - 17,
            "Two-digit dates indicate month precision. The 72-day count uses day-level dates only.",
            11,
            MUTED,
        )
    )
    return "\n".join([*parts, "</svg>", ""])


def frequencies(rows, glossary):
    counts = Counter()
    for row in rows:
        if not row.get("report"):
            continue
        body = row["report"].get("highlights", "").casefold()
        for term, aliases in glossary.items():
            if any(
                re.search(r"(?<![a-z0-9])" + re.escape(alias.casefold()) + r"(?![a-z0-9])", body)
                for alias in aliases
            ):
                counts[term] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))


def position_word(term, size, placed, width, height):
    word_width = len(term) * size * 0.64 + 16
    word_height = size * 1.24 + 8
    for step in range(900):
        angle = step * 0.43
        radius = 5.6 * math.sqrt(step)
        x = round(width / 2 + math.cos(angle) * radius * 2.5 - word_width / 2)
        y = round(258 + math.sin(angle) * radius - word_height / 2)
        bounds = (x, y, x + word_width, y + word_height)
        if x < 28 or y < 95 or bounds[2] > width - 28 or bounds[3] > height - 45:
            continue
        if all(
            bounds[2] <= left or right <= x or bounds[3] <= top or bottom <= y
            for left, top, right, bottom in placed
        ):
            return bounds
    return None


def wordcloud_svg(year, counts):
    width, height = 1120, 460
    parts = svg_start(
        width,
        height,
        f"{year} technical word cloud",
        "Word size reflects the number of releases mentioning a technical term.",
    )
    parts.append(svg_text(30, 42, f"TECHNICAL WORD CLOUD  /  {year}", 12, MUTED, weight=600))
    parts.append(svg_text(29, 79, "Terms across model reports", 32, serif=True))
    parts.append(svg_line(29, 94, 1091, 94))
    placed = []
    for index, (term, count) in enumerate(counts[:25]):
        size = round(17 + 49 * math.sqrt(count / counts[0][1]))
        while size >= 15:
            if bounds := position_word(term, size, placed, width, height):
                placed.append(bounds)
                color = PALETTE[index % len(PALETTE)]
                parts.append(svg_text(bounds[0] + 8, bounds[1] + size, term, size, color, weight=700))
                break
            size -= 3
    if not placed:
        parts.append(svg_text(30, 160, "Terms appear when verified reports are added.", 15, MUTED))
    parts.append(svg_line(29, height - 41, 1091, height - 41))
    parts.append(
        svg_text(
            30, height - 17, "One mention per model release. Terms are normalized across reports.", 12, MUTED
        )
    )
    return "\n".join([*parts, "</svg>", ""])


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
            if not group:
                continue
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


def build_visuals(rows, glossary, portal):
    events = [*rows, *({**row, **event, "follow_up": True} for row in rows for event in row.get("release_events", []))]
    years = sorted({row["released_on"][:4] for row in events}, reverse=True)
    by_year = {year: [row for row in events if row["released_on"].startswith(year)] for year in years}
    year = years[0]
    latest = by_year[year]
    counts = frequencies([row for row in rows if row["released_on"].startswith(year)], glossary)
    diagrams = Path("assets/diagrams")
    h1, h2 = (diagrams / f"release-timeline-{year}-{half}.svg" for half in ("h1", "h2"))
    cloud = diagrams / f"technical-word-cloud-{year}.svg"
    terms = Path("docs/data/word-cloud.json")
    outputs = {
        h1: timeline_svg(year, latest, 1, 6),
        h2: timeline_svg(year, latest, 7, 12),
        cloud: wordcloud_svg(year, counts),
        terms: json.dumps({"year": int(year), "terms": dict(counts)}, indent=2) + "\n",
        Path("docs/timeline.html"): timeline_html(by_year),
    }
    sections = "\n".join(
        [
            "## Release Timeline",
            "",
            f"[Browse the full timeline and release sources]({portal}/timeline.html)",
            "",
            f"![{year} model releases, January to June]({h1})",
            "",
            f"![{year} model releases, July to December]({h2})",
            "",
            "## Technical Word Cloud",
            "",
            f"![{year} report terms sized by release count]({cloud})",
            "",
            f"[Word frequencies]({terms})",
        ]
    )
    return outputs, sections
