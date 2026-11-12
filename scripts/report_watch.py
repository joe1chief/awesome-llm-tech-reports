from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from report_catalog import ROOT, build, read_catalog, save_catalog, slug
from report_resolution import (
    DISTRIBUTION,
    MAX_PDF,
    clean,
    matches_model,
    normalize_model,
    resolve_report,
    words,
)
from report_sources import (
    COMMON_HOSTS,
    HUB_FILES,
    HUB,
    Arxiv,
    Page,
    body_text,
    date_value,
    document_links,
    fetch,
    model_pages,
    xml_entries,
)
from report_store import Store

SOURCES = ROOT / "configs/report-sources.json"
ALIASES = ROOT / ".cursor/skills/quarterly-llm-repo-refresh/runtime/model_aliases.json"
BASELINE = "2026-07-01"
OVERLAP_DAYS = 3
MODEL_RELEASE = re.compile(
    r"\b(?:introduc\w*|announc\w*|releas\w*|launch\w*|available|system.card|model.card)\b", re.I
)
NOISE = re.compile(
    r"\b(?:pricing|deprecat\w*|incident|outage|benchmarking|cookbook|migration|tutorial)\b", re.I
)


def newer_report(current, new):
    if not new:
        return current
    if not current:
        return new
    if current.get("kind") == "archive":
        return current
    if new["id"] == current["id"]:
        if not new.get("highlights"):
            new = {**new, "highlights": current.get("highlights", "")}
        if new["id"].startswith("arxiv:") and int(new["revision"]) < int(current["revision"]):
            return current
        if new["rank"] > current.get("rank", 1):
            return {**new, "rank": current.get("rank", 1)}
        return new
    return new if new["rank"] < current.get("rank", 1) else current


def record(vendor, name, published, url, settings, aliases, existing, *, revision="", forms=None):
    model = normalize_model(name, vendor, aliases, settings)
    model_key = slug(model)
    if not model_key:
        raise ValueError("Model name has no stable identifier")
    key = f"{vendor}/{model_key}"
    prior = existing.get(key)
    if prior is None:
        prior = next(
            (
                row
                for row in existing.values()
                if row["key"].startswith(vendor + "/")
                and words(normalize_model(row["model"], vendor, aliases, settings)) == words(model)
            ),
            None,
        )
    if prior:
        row = prior.copy()
    else:
        row = {
            "key": key,
            "id": f"{vendor}--{model_key}",
            "model": model,
            "org": settings["org"],
            "released_on": published,
            "release_url": url,
            "report": None,
        }
    if forms:
        row["forms"] = list(dict.fromkeys([*row.get("forms", []), *forms]))
    if revision:
        row["hub_revision"] = revision
        row["hub_url"] = url
    else:
        row["official_url"] = url
        if (
            row["released_on"][:7] == published[:7]
            or not prior
            or urlsplit(row["release_url"]).hostname == "huggingface.co"
        ):
            row["released_on"] = published
            row["release_url"] = url
    return row


def try_report(row, settings, arxiv, until, *, card=None, official_body=None):
    previous = row.get("report")
    if previous and previous["kind"] == "archive":
        return []
    hub_url = row.get("hub_url")
    lookup = {**row, "release_url": hub_url} if card and hub_url else row
    report, errors = resolve_report(lookup, card, settings, arxiv, official_body)
    row["report"] = newer_report(previous, report)
    report = row["report"]
    row.setdefault("first_seen", until)
    expiry = date.fromisoformat(row["first_seen"]) + timedelta(days=30)
    if (not report or report.get("rank", 1) >= 2 or errors) and date.fromisoformat(until) <= expiry:
        row["retry_on"] = (date.fromisoformat(until) + timedelta(days=1)).isoformat()
    else:
        row.pop("retry_on", None)
    return errors


def hf_card(url, revision, gated):
    try:
        return body_text(f"{url}/raw/{revision}/README.md", {"huggingface.co"})
    except HTTPError as error:
        if error.code == 404 or (gated and error.code in {401, 403}):
            return ""
        raise


def scan_hub(vendor, settings, aliases, existing, cursor, since, until, limit, arxiv):
    owner = settings["hub"]
    models = list(model_pages(owner, since))
    seen = cursor.get("seen", {}).copy()
    changed, errors = {}, []
    processed, deferred = 0, 0
    for model in models:
        model_id = model["id"]
        name = model_id.split("/", 1)[1]
        revision = model.get("sha") or ""
        published = date_value(model.get("createdAt"))
        if not published or published > until or model["modified"] > until or DISTRIBUTION.search(name):
            continue
        if not re.fullmatch(r"[a-fA-F0-9]{40}", revision):
            raise ValueError("Hub response lacks a pinned revision")
        if seen.get(model_id) == revision:
            continue
        url = f"{HUB}/{model_id}"
        forms = ["Gated"] if model.get("gated") else []
        if "preview" in name.casefold():
            forms.append("Preview")
        row = record(
            vendor,
            name,
            published,
            url,
            settings,
            aliases,
            {**existing, **changed},
            revision=revision,
            forms=forms,
        )
        known = row["key"] in existing or row["key"] in changed
        if published < since and not known:
            seen[model_id] = revision
            continue
        if processed >= limit:
            deferred += 1
            continue
        processed += 1
        card = hf_card(url, revision, model.get("gated"))
        if not card.strip():
            seen[model_id] = revision
            continue
        if not (matches_model(row["model"], card[:18000]) or official_model(name, settings)):
            seen[model_id] = revision
            continue
        errors.extend(try_report(row, settings, arxiv, until, card=card))
        changed[row["key"]] = row
        seen[model_id] = revision
    return list(changed.values()), seen, errors, deferred


def official_entries(url, hosts):
    text = body_text(url, hosts)
    if re.search(r"<(?:rss|feed|urlset|sitemapindex)\b", text[:600], re.I):
        if re.search(r"<sitemapindex\b", text[:600], re.I):
            indexes = re.findall(r"<loc>\s*(https://[^<]+)</loc>", text)
            entries = []
            for child in [item for item in indexes if urlsplit(item).hostname in hosts][:4]:
                entries.extend(xml_entries(body_text(child, hosts)))
            if len(indexes) > 4:
                raise ValueError("Official sitemap index exceeds scan budget")
            return entries
        return list(xml_entries(text))
    page = Page(text)
    links = [
        {"url": link, "title": label, "date": "", "lastmod": ""} for link, label in document_links(text, url)
    ]
    if page.date:
        links.insert(0, {"url": url, "title": page.title, "date": page.date, "lastmod": ""})
    return links


def official_model(text, settings):
    match = re.search(settings["model_pattern"], text, re.I)
    if not match:
        return ""
    value = re.split(
        r"\s+(?:is|are|now|for|with|delivers|and|launches|available|technical|system)\b",
        match.group(0),
        maxsplit=1,
        flags=re.I,
    )[0]
    return clean(value, 90).strip(" -./")


def scan_official(vendor, settings, aliases, existing, cursor, since, until, limit, arxiv):
    url = settings["official"]
    hosts = set(settings["hosts"]) | COMMON_HOSTS
    entries = official_entries(url, hosts)
    seen = cursor.get("seen", {}).copy()
    changed, errors = {}, []
    processed, deferred = 0, 0
    eligible = set()
    for entry in sorted(
        entries, key=lambda item: item.get("date") or item.get("lastmod") or "", reverse=True
    ):
        link = entry["url"]
        label = clean(entry["title"], 240)
        if urlsplit(link).hostname not in hosts or link in eligible:
            continue
        topic = label + " " + unquote(urlsplit(link).path).replace("-", " ")
        if NOISE.search(topic) or not official_model(topic, settings) or not MODEL_RELEASE.search(topic):
            continue
        eligible.add(link)
        hint = entry.get("lastmod") or entry.get("date") or ""
        stamp = hint or until[:7]
        if (hint and hint < since) or seen.get(link) == stamp:
            continue
        if processed >= limit:
            deferred += 1
            continue
        processed += 1
        try:
            body = body_text(link, hosts)
        except HTTPError as error:
            if error.code != 404:
                raise
            seen[link] = stamp
            continue
        page = Page(body)
        published = entry.get("date") or page.date
        title = page.title or label
        name = official_model(title, settings) or official_model(label, settings)
        if name and published and published <= until:
            forms = ["Preview"] if "preview" in title.casefold() else []
            row = record(
                vendor, name, published, link, settings, aliases, {**existing, **changed}, forms=forms
            )
            if published >= since or row["key"] in existing or row["key"] in changed:
                errors.extend(try_report(row, settings, arxiv, until, official_body=body))
                changed[row["key"]] = row
        if not published or published <= until:
            seen[link] = stamp
    return list(changed.values()), seen, errors, deferred


def scan_reports(store, baseline, settings, aliases, vendors, since, until, limit, replay=False, arxiv=None):
    arxiv = arxiv or Arxiv()
    rows = {row["key"]: row for row in baseline}
    for saved in store.releases():
        prior = rows.get(saved["key"])
        report = saved.get("report")
        archived = prior.get("report") if prior else None
        if archived and archived.get("file") and report and archived["id"] == report["id"]:
            if archived.get("revision") == report.get("revision"):
                saved["report"] = {**report, "file": archived["file"]}
        rows[saved["key"]] = saved
    summaries = []
    for vendor in vendors:
        config = settings[vendor]
        scans = []
        if config.get("hub"):
            scans.append(("hub", scan_hub))
        if config.get("official"):
            scans.append(("official", scan_official))
        for label, scan in scans:
            name = f"{vendor}/{label}"
            cursor = store.source(name)
            watermark = cursor.get("watermark", "")
            earliest = since
            if watermark and not replay:
                overlap = (date.fromisoformat(watermark) - timedelta(days=OVERLAP_DAYS)).isoformat()
                earliest = max(since, overlap)
            try:
                collected, seen, warnings, deferred = scan(
                    vendor, config, aliases, rows, cursor, earliest, until, limit, arxiv
                )
            except (URLError, OSError, ValueError, KeyError, TypeError) as error:
                issue = f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__
                summaries.append({"source": name, "error": issue})
                continue
            next_state = {"watermark": watermark if deferred else max(watermark, until), "seen": seen}
            store.save(collected, name, next_state)
            rows.update((row["key"], row) for row in collected)
            summaries.append(
                {
                    "source": name,
                    "records": len(collected),
                    "report_lookup_errors": len(warnings),
                    "deferred": deferred,
                }
            )
    due = [
        row
        for row in rows.values()
        if row.get("retry_on") and row["retry_on"] <= until and row["key"].split("/")[0] in vendors
    ]
    for pending in sorted(due, key=lambda row: row["retry_on"])[:limit]:
        row = pending.copy()
        config = settings[row["key"].split("/")[0]]
        try:
            if row.get("hub_url"):
                card = hf_card(row["hub_url"], row["hub_revision"], True)
                try_report(row, config, arxiv, until, card=card)
            elif row.get("official_url"):
                page = body_text(row["official_url"], COMMON_HOSTS | set(config["hosts"]))
                try_report(row, config, arxiv, until, official_body=page)
        except (URLError, OSError, ValueError):
            summaries.append({"source": row["key"], "error": "report retry unavailable"})
            continue
        store.save([row])
        rows[row["key"]] = row
    return list(rows.values()), summaries


def project(rows, settings, root=ROOT, mirror=False):
    result = []
    for row in rows:
        output = {
            key: row[key] for key in ("id", "key", "model", "org", "released_on", "release_url", "report")
        }
        if row.get("forms"):
            output["forms"] = row["forms"]
        if row.get("report"):
            report = row["report"]
            public = {
                key: report[key]
                for key in ("id", "kind", "url", "highlights", "file", "published_on", "revision")
                if report.get(key)
            }
            vendor = row["key"].split("/")[0]
            mirror_urls = settings.get(vendor, {}).get("mirror", [])
            if mirror and not public.get("file") and report.get("pdf") in mirror_urls:
                hosts = COMMON_HOSTS | set(settings[vendor]["hosts"])
                content = fetch(report["pdf"], hosts | HUB_FILES, MAX_PDF)[0]
                if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-4096:]:
                    raise ValueError("Incomplete PDF")
                month = row["released_on"][:7]
                filename = f"{month}_{slug(row['model'])}.pdf"
                paths = [Path(month[:4]) / vendor / filename, Path("pdf") / filename]
                for path in paths:
                    if (root / path).is_file() and (root / path).read_bytes() != content:
                        raise ValueError(f"PDF archive collision at {path}")
                for path in paths:
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_suffix(".tmp")
                    temporary.write_bytes(content)
                    temporary.replace(target)
                public["file"] = str(paths[0])
            output["report"] = public
        result.append(output)
    return result


def main():
    parser = argparse.ArgumentParser(description="Discover model releases and technical reports")
    parser.add_argument("--vendor", action="append")
    parser.add_argument("--since")
    parser.add_argument("--until", default=datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat())
    parser.add_argument("--limit", type=int, default=12, help="New revisions or pages to inspect per source")
    parser.add_argument("--sqlite", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--publish", action="store_true", help="Write the catalog and regenerate the public archive"
    )
    parser.add_argument("--pdf-manifest", type=Path)
    args = parser.parse_args()
    since = args.since or BASELINE
    if date.fromisoformat(since) > date.fromisoformat(args.until) or args.limit < 1:
        parser.error("Expected a valid collection window and a positive limit")
    settings = json.loads(SOURCES.read_text())
    aliases = json.loads(ALIASES.read_text())
    vendors = list(dict.fromkeys(args.vendor or settings))
    if unknown := set(vendors) - settings.keys():
        parser.error("Unknown vendor: " + ", ".join(sorted(unknown)))
    baseline = read_catalog()
    db_url = os.environ.get("REPORTS_DATABASE_URL") if args.publish else None
    if args.sqlite:
        args.sqlite.parent.mkdir(parents=True, exist_ok=True)
    if args.publish and not (db_url or args.sqlite):
        parser.error("Publishing requires REPORTS_DATABASE_URL or an explicit --sqlite state path")
    store = Store(str(args.sqlite) if args.sqlite else ":memory:", db_url)
    with store.lock():
        rows, summaries = scan_reports(
            store,
            baseline,
            settings,
            aliases,
            vendors,
            since,
            args.until,
            args.limit,
            replay=bool(args.since),
        )
        original = {row["key"]: row for row in baseline}
        projection = project(rows, settings, mirror=args.publish)
        changed = [row for row in projection if original.get(row["key"]) != row]
        print(json.dumps({"changes": changed, "sources": summaries}, ensure_ascii=False, indent=2))
        if not summaries or all(item.get("error") for item in summaries):
            return 1
        if args.strict and any(
            item.get("error") or item.get("deferred") or item.get("report_lookup_errors")
            for item in summaries
        ):
            return 1
        if args.publish:
            manifest = set(args.pdf_manifest.read_text().splitlines()) if args.pdf_manifest else None
            save_catalog(projection)
            build(pdf_manifest=manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
