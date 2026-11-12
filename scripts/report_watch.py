from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urldefrag, urljoin, urlsplit
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
    date_in,
    date_value,
    fetch,
    model_pages,
    require_host,
    xml_entries,
)
from report_store import Store

SOURCES = ROOT / "configs/report-sources.json"
ALIASES = ROOT / ".cursor/skills/quarterly-llm-repo-refresh/runtime/model_aliases.json"
BASELINE = "2026-07-01"
OVERLAP_DAYS = 3
MODEL_RELEASE = re.compile(
    r"\b(?:introduc\w*|announc\w*|releas\w*|launch\w*|unveil\w*|available|availability|"
    r"preview|system.card|model.card|technical.report)\b|发布|上线|正式版|开放",
    re.I,
)
NOISE = re.compile(
    r"\b(?:pricing|deprecat\w*|incident|outage|benchmarking|cookbook|migration|tutorial)\b", re.I
)
MODEL_DASHES = str.maketrans({char: "-" for char in "‐‑‒–—−"})
OFFICIAL_FORMS = (
    ("Preview", re.compile(r"\bpreview\b|预览", re.I)),
    ("Open weights", re.compile(r"\bopen[- ]weights?\b|权重开源|开放权重", re.I)),
    (
        "General availability",
        re.compile(r"\b(?:general availability|generally available|now available)\b|正式开放", re.I),
    ),
)
REPORT_RANKS = {"system card": 2, "official technical page": 2, "model card": 3}


GENERATIVE_HUB_TASKS = {
    "any-to-any",
    "audio-text-to-text",
    "audio-to-audio",
    "image-text-to-text",
    "image-to-3d",
    "image-to-image",
    "image-to-video",
    "text-generation",
    "text2text-generation",
    "text-to-3d",
    "text-to-audio",
    "text-to-image",
    "text-to-speech",
    "text-to-video",
    "translation",
    "video-text-to-text",
    "video-to-video",
}
AUXILIARY_HUB_TAGS = {"adapter", "draft-model", "lora", "reranker", "reward-model"}
AUXILIARY_MODEL_NAME = re.compile(
    r"(?:^|[ ._/-])(?:embeddings?|rerank(?:er|ing)?|diarization|classifier|rewarder|reward[-_ ]model|"
    r"sae|auto[-_ ]?verifier|draft(?:er)?|dspark|dspine|lora|adapter)(?=$|[ ._/-])",
    re.I,
)


def model_in_scope(name, settings, task=""):
    return (
        (not task or task == "other" or task in GENERATIVE_HUB_TASKS)
        and not AUXILIARY_MODEL_NAME.search(name)
        and not any(re.search(pattern, name, re.I) for pattern in settings.get("exclude_models", []))
    )


def report_rank(report):
    return report.get("rank", REPORT_RANKS.get(report["kind"], 1))


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
        if new["id"].startswith("arxiv:") and int(new["revision"]) < int(current.get("revision", "1")):
            return current
        if report_rank(new) > report_rank(current):
            return {**new, "rank": report_rank(current)}
        return new
    return new if report_rank(new) < report_rank(current) else current


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
    if revision:
        row["hub_revision"] = revision
        row["hub_url"] = url
        if forms and urlsplit(row["release_url"]).hostname == "huggingface.co":
            row["forms"] = list(dict.fromkeys([*row.get("forms", []), *forms]))
    else:
        row["official_url"] = url
        record_official_event(row, published, url, forms or [])
    return row


def record_official_event(row, published, url, forms):
    current = row["released_on"]
    from_hub = urlsplit(row["release_url"]).hostname == "huggingface.co"
    archive = (row.get("report") or {}).get("kind") == "archive"
    if archive and current[:7] != published[:7]:
        return
    events = {event["released_on"]: event for event in row.get("release_events", [])}
    follow_up = (
        published > current and bool(forms) and bool(row.get("forms"))
        and set(forms) != set(row["forms"])
    )
    if (from_hub and not follow_up and not events) or len(current) == 7 or published < current:
        if not from_hub and len(current) == 10 and row.get("forms"):
            events[current] = {key: row[key] for key in ("released_on", "release_url", "forms")}
        row["released_on"], row["release_url"] = published, url
        row.pop("forms", None)
    if published == row["released_on"]:
        if forms:
            row["forms"] = list(dict.fromkeys([*row.get("forms", []), *forms]))
        events.pop(published, None)
    elif forms and set(forms) != set(row.get("forms", [])):
        prior = events.get(published, {})
        events[published] = {
            "released_on": published,
            "release_url": prior.get("release_url", url),
            "forms": list(dict.fromkeys([*prior.get("forms", []), *forms])),
        }
    if events:
        row["release_events"] = [events[day] for day in sorted(events)]
    else:
        row.pop("release_events", None)


def try_report(row, settings, arxiv, until, *, card=None, official_body=None):
    previous = row.get("report")
    if previous and previous["kind"] == "archive":
        return []
    source = row.get("hub_url") if card else row.get("official_url") if official_body else None
    lookup = {**row, "release_url": source} if source else row
    report, errors = resolve_report(lookup, card, settings, arxiv, official_body)
    row["report"] = newer_report(previous, report)
    report = row["report"]
    row.setdefault("first_seen", until)
    expiry = date.fromisoformat(row["first_seen"]) + timedelta(days=30)
    if (not report or report_rank(report) >= 2 or errors) and date.fromisoformat(until) <= expiry:
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
        task = model.get("pipeline_tag") or ""
        tags = set(model.get("tags") or [])
        if not model_in_scope(name, settings, task) or tags & AUXILIARY_HUB_TAGS:
            continue
        if task not in GENERATIVE_HUB_TASKS and not official_model(name, settings):
            continue
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
        if task in GENERATIVE_HUB_TASKS:
            row["hub_task"] = task
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
        {"url": urljoin(url, link), "title": label, "date": date_in(label), "lastmod": ""}
        for link, label in page.links
        if link and not link.startswith("#")
    ]
    if page.date:
        links.insert(0, {"url": url, "title": page.heading or page.title, "date": page.date, "body": text})
    return links


def official_model(text, settings, path=""):
    names = [
        clean(re.split(
            r"\s+(?:is|are|now|for|with|delivers|and|launches|available|technical|system|model card)\b",
            match[0], maxsplit=1, flags=re.I,
        )[0], 90).strip(" -./")
        for match in re.finditer(settings["model_pattern"], text.translate(MODEL_DASHES), re.I)
    ]
    if not names:
        return ""
    path_slug = "-" + slug(path) + "-"
    return next((name for name in names if f"-{slug(name)}-" in path_slug), names[0])


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
        link = urldefrag(entry["url"])[0]
        label = clean(entry["title"], 240)
        path = unquote(urlsplit(link).path)
        if urlsplit(link).hostname not in hosts or link in eligible or path.lower().endswith(".pdf"):
            continue
        topic = f"{label} {path}"
        candidate = official_model(topic, settings, path)
        if NOISE.search(topic) or not candidate or not model_in_scope(candidate, settings):
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
            body = entry.get("body") or body_text(link, hosts)
        except (URLError, OSError, ValueError) as error:
            if isinstance(error, HTTPError) and error.code == 404:
                seen[link] = stamp
                continue
            errors.append(f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__)
            if not (entry.get("date") and MODEL_RELEASE.search(label)):
                deferred += 1
                continue
            body = ""
        page = Page(body)
        published = entry.get("date") or page.date
        titles = [clean(value, 240) for value in (page.heading, page.title, label) if value]
        name = next((model for title in titles if (model := official_model(title, settings, path))), "")
        subject = " ".join([*titles, path.replace("-", " ")])
        bare_title = any(words(name) == words(title) for title in titles) if name else False
        if (
            name and published and published <= until
            and (bare_title or MODEL_RELEASE.search(subject))
            and model_in_scope(name, settings)
        ):
            forms = [form for form, pattern in OFFICIAL_FORMS if pattern.search(subject)]
            row = record(
                vendor, name, published, link, settings, aliases, {**existing, **changed}, forms=forms
            )
            if published >= since or row["key"] in existing or row["key"] in changed:
                if body:
                    errors.extend(try_report(row, settings, arxiv, until, official_body=body))
                elif not row.get("report") and not row.get("first_seen"):
                    row.update(first_seen=until, retry_on=until)
                changed[row["key"]] = row
        if not published or published <= until:
            seen[link] = stamp
    return list(changed.values()), seen, errors, deferred


def verified_releases(vendor, settings, aliases, rows, entries, since, until):
    hosts = COMMON_HOSTS | set(settings["hosts"])
    changed = {}
    for evidence in entries:
        published, url = evidence["released_on"], evidence["release_url"]
        if not since <= published <= until:
            continue
        if date.fromisoformat(published).isoformat() != published:
            raise ValueError("Invalid verified release date")
        require_host(url, hosts)
        row = record(
            vendor, evidence["model"], published, url, settings, aliases, {**rows, **changed},
            forms=evidence.get("forms"),
        )
        if urlsplit(url).hostname == "huggingface.co" and row["release_url"] != url:
            row["official_url"] = row["release_url"]
        if document := evidence.get("report"):
            require_host(document["url"], hosts)
            if document["kind"] not in {"system card", "technical report", "official technical page", "model card"}:
                raise ValueError("Invalid verified document kind")
            current = row.get("report")
            if not current or report_rank(current) > 2:
                row["report"] = {**document, "id": document["url"], "rank": 2}
        if not row.get("report") and not row.get("first_seen"):
            row.update(first_seen=until, retry_on=until)
        changed[row["key"]] = row
    return [row for key, row in changed.items() if rows.get(key) != row]


def scan_reports(
    store, baseline, settings, aliases, vendors, since, until, limit,
    replay=False, arxiv=None, backfill=None, backfill_only=False,
):
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
        if config.get("hub") and not backfill_only:
            scans.append(("hub", scan_hub, config))
        official = [] if backfill_only else config.get("official") or []
        if isinstance(official, str):
            official = [official]
        for url in dict.fromkeys(official):
            scans.append((f"official:{url}", scan_official, {**config, "official": url}))
        for label, scan, source_config in scans:
            name = f"{vendor}/{label}"
            cursor = store.source(name)
            watermark = cursor.get("watermark", "")
            earliest = since
            if watermark and not replay:
                overlap = (date.fromisoformat(watermark) - timedelta(days=OVERLAP_DAYS)).isoformat()
                earliest = max(since, overlap)
            try:
                collected, seen, warnings, deferred = scan(
                    vendor, source_config, aliases, rows, cursor, earliest, until, limit, arxiv
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
                    **({"warnings": list(dict.fromkeys(warnings))} if warnings else {}),
                }
            )
        if backfill and (entries := backfill.get(vendor)):
            collected = verified_releases(vendor, config, aliases, rows, entries, since, until)
            store.save(collected)
            rows.update((row["key"], row) for row in collected)
            summaries.append({"source": f"{vendor}/verified-backfill", "records": len(collected)})
    if backfill_only:
        return list(rows.values()), summaries
    due = [
        row
        for row in rows.values()
        if row.get("retry_on") and row["retry_on"] <= until
        and (vendor := row["key"].split("/", 1)[0]) in vendors
        and model_in_scope(row["model"], settings[vendor], row.get("hub_task", ""))
    ]
    for pending in sorted(due, key=lambda row: row["retry_on"])[:limit]:
        row = pending.copy()
        config = settings[row["key"].split("/")[0]]
        card = official_body = None
        try:
            if row.get("hub_url"):
                card = hf_card(row["hub_url"], row["hub_revision"], True)
        except (URLError, OSError, ValueError):
            summaries.append({"source": row["key"], "error": "Hub card unavailable for report retry"})
        try:
            if row.get("official_url"):
                official_body = body_text(row["official_url"], COMMON_HOSTS | set(config["hosts"]))
        except (URLError, OSError, ValueError):
            summaries.append({"source": row["key"], "error": "Official page unavailable for report retry"})
        try_report(row, config, arxiv, until, card=card, official_body=official_body)
        store.save([row])
        rows[row["key"]] = row
    return list(rows.values()), summaries


def project(rows, settings, root=ROOT, mirror=False):
    result = []
    for row in rows:
        vendor = row["key"].split("/", 1)[0]
        config = settings.get(vendor, {})
        if not model_in_scope(row["model"], config, row.get("hub_task", "")):
            continue
        output = {
            key: row[key] for key in ("id", "key", "model", "org", "released_on", "release_url", "report")
        }
        for field in ("forms", "release_events", "hub_task"):
            if row.get(field):
                output[field] = row[field]
        if row.get("report"):
            report = row["report"]
            public = {
                key: report[key]
                for key in ("id", "kind", "url", "highlights", "file", "published_on", "revision")
                if report.get(key)
            }
            mirror_urls = config.get("mirror", [])
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
    parser.add_argument("--backfill-only", action="store_true", help="Import verified release evidence without polling")
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
    backfill_file = SOURCES.with_name("report-backfill.json")
    backfill = json.loads(backfill_file.read_text()) if args.since and backfill_file.is_file() else None
    if args.backfill_only and not backfill:
        parser.error("--backfill-only requires --since and verified release evidence")
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
            backfill=backfill,
            backfill_only=args.backfill_only,
        )
        original = {row["key"]: row for row in baseline}
        projection = project(rows, settings, mirror=args.publish)
        changed = [row for row in projection if original.get(row["key"]) != row]
        removed = sorted(original.keys() - {row["key"] for row in projection})
        print(json.dumps({"changes": changed, "removed": removed, "sources": summaries}, ensure_ascii=False, indent=2))
        if os.environ.get("GITHUB_ACTIONS") == "true":
            for summary in summaries:
                issue = summary.get("error") or ", ".join(summary.get("warnings", []))
                if issue or summary.get("deferred"):
                    print(
                        f"::warning::{summary['source']}: {issue or 'scan limit reached'}, "
                        f"{summary.get('deferred', 0)} deferred",
                        file=sys.stderr,
                    )
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
