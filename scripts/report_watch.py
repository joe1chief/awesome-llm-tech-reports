from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, unquote, urldefrag, urlencode, urljoin, urlsplit
from zoneinfo import ZoneInfo

from report_catalog import ROOT, build, read_catalog, slug
from report_identity import collapse_distributions, document_priority, hub_relation, hub_repository
from report_parameters import below_parameter_floor, configure_parameters, declared_total, total_parameters
from report_resolution import (
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
    arxiv_key,
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
REPORT_RETRY_DAYS = 90
MODEL_RELEASE = re.compile(
    r"\b(?:introduc\w*|announc\w*|releas\w*|launch\w*|unveil\w*|available|availability|"
    r"preview|system.card|model.card|technical.report)\b|发布|上线|正式版|开放",
    re.I,
)
NOISE = re.compile(
    r"\b(?:pricing|deprecat\w*|discontinu\w*|retirement|sunset|incident|outage|benchmarking|cookbook|"
    r"migration|tutorial|end.of.life)\b|下线|退役|停服", re.I
)
MODEL_DASHES = str.maketrans({char: "-" for char in "‐‑‒–—−"})
HUB_REVISION = re.compile(r"[a-fA-F0-9]{40}")
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
    "image-text-to-video",
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
AUXILIARY_TAGS = AUXILIARY_HUB_TAGS | {"robotics-simulator"}
AUXILIARY_PURPOSES = (
    ("speculative-draft", re.compile(r"\bspeculative[- ]decoding (?:draft|drafter|checkpoint)\b", re.I)),
    ("user-simulator", re.compile(r"\buser simulator\b", re.I)),
    ("robotics-simulator", re.compile(r"\b(?:generative )?surgical world model\b", re.I)),
)
AUXILIARY_MODEL_NAME = re.compile(
    r"(?:^|[ ._/-])(?:embeddings?|rerank(?:er|ing)?|diarization|classifier|rewarder|reward[-_ ]model|"
    r"sae|auto[-_ ]?verifier|draft(?:er)?|dflash\d*|dspark|dspine|lora|adapter)(?=$|[ ._/-])",
    re.I,
)


def model_in_scope(name, settings, task=""):
    return (
        (not task or task == "other" or task in GENERATIVE_HUB_TASKS)
        and not AUXILIARY_MODEL_NAME.search(name)
        and not any(re.search(pattern, name, re.I) for pattern in settings.get("exclude_models", []))
    )


def auxiliary_purpose(model, description):
    name = r"[-_\s]+".join(re.escape(part) for part in re.split(r"[-_\s]+", model) if part)
    declaration = re.compile(
        rf"(?im)^(?:[>*-]\s+)?(?:the\s+)?{name}(?:\s+model)?\s+"
        r"(?:is|serves as)\s+([^\n]{1,260})"
    )
    for match in declaration.finditer(re.sub(r"[*\x60]", "", description[:10000])):
        purpose = re.split(r"(?<=[.!?])\s|,\s+which\b", match[1], maxsplit=1)[0]
        for tag, pattern in AUXILIARY_PURPOSES:
            if pattern.search(purpose):
                return tag
    return ""


def release_in_scope(row, settings):
    count = total_parameters(row["model"], settings, stored=row.get("total_parameters"))
    return (
        model_in_scope(row["model"], settings, row.get("hub_task", ""))
        and not set(row.get("hub_tags", [])) & AUXILIARY_TAGS
        and not row.get("hub_role")
        and not auxiliary_purpose(row["model"], (row.get("report") or {}).get("highlights", ""))
    ) and not below_parameter_floor(
        count, settings
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
    return min((current, new), key=lambda report: (document_priority(report), report_rank(report)))


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
    same_source = row["release_url"] == url and (
        not row.get("forms") or any(form in row["forms"] for form in forms)
    )
    follow_up = (
        not same_source and published > current and bool(forms) and bool(row.get("forms"))
        and set(forms) != set(row["forms"])
    )
    if (from_hub and not follow_up and not events) or (
        len(current) == 7 and current == published[:7]
    ) or published < current:
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
    events = {day: event for day, event in events.items() if day > row["released_on"]}
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
    row["report_checked_on"] = until
    age = (date.fromisoformat(until) - date.fromisoformat(row["first_seen"])).days
    if (not report or report["kind"] in {"model card", "official technical page"} or errors) and age < REPORT_RETRY_DAYS:
        row["retry_on"] = (date.fromisoformat(until) + timedelta(days=1 if age < 30 else 7)).isoformat()
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


def waiting_for_retry(seen, key, stamp, until):
    retry = seen.get(key)
    return isinstance(retry, dict) and retry.get("stamp") == stamp and retry.get("retry_on", "") > until


def defer_source_item(seen, key, stamp, until):
    seen[key] = {"stamp": stamp, "retry_on": (date.fromisoformat(until) + timedelta(days=1)).isoformat()}


def scan_hub(vendor, settings, aliases, existing, cursor, since, until, limit, arxiv):
    owner = settings["hub"]
    models = list(model_pages(owner, since))
    seen = cursor.get("seen", {}).copy()
    changed, errors = {}, []
    processed, deferred = 0, 0
    source_keys = {}
    for key, row in existing.items():
        if key.startswith(vendor + "/"):
            for source in {row.get("hub_url"), row["release_url"]} - {None}:
                source_keys.setdefault(source, set()).add(key)
    for model in models:
        model_id = model["id"]
        name = model_id.split("/", 1)[1]
        task = model.get("pipeline_tag") or ""
        tags = set(model.get("tags") or [])
        relation, base_model = hub_relation(tags)
        auxiliary = tags & AUXILIARY_HUB_TAGS
        if relation == "adapter":
            auxiliary.add(relation)
        if "simulation" in tags and tags & {"policy-evaluation", "surgical-robotics", "vla-evaluation"}:
            auxiliary.add("robotics-simulator")
        url = f"{HUB}/{model_id}"
        # Tags can change without a card revision. Reconcile only the exact
        # source, never a sibling normalized to the same family release key.
        if model["modified"] <= until:
            for key in sorted(source_keys.get(url, ())):
                prior = changed.get(key, existing[key])
                if url in (prior.get("hub_url"), prior["release_url"]):
                    updated = {**prior, "hub_task": task, "hub_tags": sorted(auxiliary)}
                    if updated != prior:
                        changed[key] = updated
        if not model_in_scope(name, settings, task) or auxiliary:
            continue
        if task not in GENERATIVE_HUB_TASKS and not official_model(name, settings):
            continue
        revision = model.get("sha") or ""
        published = date_value(model.get("createdAt"))
        if not published or published > until or model["modified"] > until:
            continue
        parameters = total_parameters(name, settings, safetensors=model.get("safetensors"))
        small = below_parameter_floor(parameters, settings)
        rejected_revision = f"{revision}:below-{settings.get('minimum_total_parameters', 0)}"
        cached = seen.get(model_id)
        # A rejection is not a successful observation. Reconsider it when
        # reliable parameter evidence is now available (notably verified totals).
        if (cached == revision or (cached == rejected_revision and parameters is None)) and not small:
            continue
        if not isinstance(revision, str) or not HUB_REVISION.fullmatch(revision):
            errors.append("Missing Hub revision")
            deferred += 1
            continue
        if not small and waiting_for_retry(seen, model_id, revision, until):
            deferred += 1
            continue
        forms = ["Gated"] if model.get("gated") else []
        if "preview" in name.casefold():
            forms.append("Preview")
        prior_rows = {**existing, **changed}
        row = record(
            vendor, name, published, url, settings, aliases, prior_rows, revision=revision, forms=forms,
        )
        if relation == "quantized":
            row["base_model"] = base_model
        elif row.get("hub_url") == url and name == row["model"]:
            row.pop("base_model", None)
        if small:
            save_small_variant(changed, prior_rows.get(row["key"]), name, url, parameters)
            continue
        row["hub_task"] = task
        row["hub_tags"] = []
        known = row["key"] in existing or row["key"] in changed
        if published < settings.get("release_since", since) and not known:
            seen[model_id] = revision
            continue
        if processed >= limit:
            deferred += 1
            continue
        processed += 1
        try:
            card = hf_card(url, revision, model.get("gated"))
        except (URLError, OSError, ValueError) as error:
            errors.append(source_error(error))
            deferred += 1
            defer_source_item(seen, model_id, revision, until)
            continue
        if not card.strip():
            if known or official_model(name, settings):
                if parameters is not None:
                    row.setdefault("total_parameters", parameters)
                row.setdefault("first_seen", until)
                if not row.get("report"):
                    row.setdefault("retry_on", (date.fromisoformat(until) + timedelta(days=1)).isoformat())
                changed[row["key"]] = row
                seen[model_id] = revision
            else:
                defer_source_item(seen, model_id, revision, until)
                deferred += 1
            continue
        if not (matches_model(row["model"], card[:18000]) or official_model(name, settings)):
            seen[model_id] = revision
            continue
        if purpose := auxiliary_purpose(name, card):
            if known:
                changed[row["key"]] = {**row, "hub_role": purpose}
            seen[model_id] = revision
            continue
        row.pop("hub_role", None)
        parameters = total_parameters(name, settings, stored=parameters, description=card)
        if below_parameter_floor(parameters, settings):
            save_small_variant(changed, prior_rows.get(row["key"]), name, url, parameters)
            seen[model_id] = rejected_revision
            continue
        if parameters is not None:
            if slug(name) != slug(row["model"]):
                parameters = max(row.get("total_parameters") or 0, parameters)
            row["total_parameters"] = parameters
        errors.extend(try_report(row, settings, arxiv, until, card=card))
        changed[row["key"]] = row
        seen[model_id] = revision
    return list(changed.values()), seen, errors, deferred


def save_small_variant(changed, prior, name, url, parameters):
    if (
        prior and slug(prior["model"]) == slug(name)
        and url in (prior.get("hub_url"), prior.get("official_url"), prior["release_url"])
        and prior.get("total_parameters") != parameters
    ):
        changed[prior["key"]] = {**prior, "total_parameters": parameters}


def source_error(error):
    return f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__


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
    path = urlsplit(url).path.strip("/")
    listing = not path or re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", path, re.I)
    if page.date and not listing:
        links.insert(0, {"url": url, "title": page.heading or page.title, "date": page.date, "body": text})
    return links


def official_entry_url(url):
    parsed = urlsplit(urldefrag(url)[0])
    query = [
        (key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.casefold() != "spm" and not key.casefold().startswith("utm_")
    ]
    return parsed._replace(query=urlencode(query)).geturl()


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
    matching = [name for name in names if f"-{slug(name)}-" in path_slug]
    return max(matching, key=len) if matching else names[0]


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
        link = official_entry_url(entry["url"])
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
        rejected_stamp = f"{stamp}:below-{settings.get('minimum_total_parameters', 0)}"
        if (hint and hint < since) or seen.get(link) in (stamp, rejected_stamp):
            continue
        if waiting_for_retry(seen, link, stamp, until):
            deferred += 1
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
            errors.append(source_error(error))
            deferred += 1
            defer_source_item(seen, link, stamp, until)
            if not (entry.get("date") and MODEL_RELEASE.search(label)):
                continue
            body = ""
        page = Page(body)
        published = entry.get("date") or page.date
        titles = [clean(value, 240) for value in (page.heading, page.title, label) if value]
        matches = [model for title in titles if (model := official_model(title, settings, path))]
        path_name = "-" + slug(path) + "-"
        aligned = [model for model in matches if f"-{slug(model)}-" in path_name]
        name = max(aligned, key=len) if aligned else next(iter(matches), "")
        subject = " ".join([*titles, path.replace("-", " ")])
        bare_title = any(words(name) == words(title) for title in titles) if name else False
        if (
            name and published and published <= until
            and not NOISE.search(" ".join(titles))
            and (bare_title or MODEL_RELEASE.search(subject))
            and model_in_scope(name, settings)
        ):
            description = "\n".join([page.summary, *page.paragraphs])
            parameters = total_parameters(name, settings, description=description)
            forms = [form for form, pattern in OFFICIAL_FORMS if pattern.search(subject)]
            prior_rows = {**existing, **changed}
            row = record(
                vendor, name, published, link, settings, aliases, prior_rows, forms=forms
            )
            if below_parameter_floor(parameters, settings):
                save_small_variant(changed, prior_rows.get(row["key"]), name, link, parameters)
                seen[link] = rejected_stamp
                continue
            if parameters is not None:
                if slug(name) != slug(row["model"]):
                    parameters = max(row.get("total_parameters") or 0, parameters)
                row["total_parameters"] = parameters
            if not release_in_scope(row, settings):
                if row["key"] in existing or row["key"] in changed:
                    changed[row["key"]] = row
                seen[link] = rejected_stamp
                continue
            if published >= since or row["key"] in existing or row["key"] in changed:
                if body:
                    errors.extend(try_report(row, settings, arxiv, until, official_body=body))
                elif not row.get("report") and not row.get("first_seen"):
                    row.update(first_seen=until, retry_on=until)
                changed[row["key"]] = row
        if body and (not published or published <= until):
            seen[link] = stamp
    return list(changed.values()), seen, errors, deferred


def verified_releases(vendor, settings, aliases, rows, entries, since, until):
    hosts = COMMON_HOSTS | set(settings["hosts"])
    changed = {}
    for evidence in entries:
        published, url = evidence["released_on"], evidence["release_url"]
        correction = evidence.get("correction", False)
        if published > until or (published < since and not correction):
            continue
        if date.fromisoformat(published).isoformat() != published:
            raise ValueError("Invalid verified release date")
        require_host(url, hosts)
        row = record(
            vendor, evidence["model"], published, url, settings, aliases, {**rows, **changed},
            forms=evidence.get("forms"),
        )
        if correction:
            invalid = set(evidence.get("invalid_event_dates", []))
            row.update(released_on=published, release_url=url)
            if "forms" in evidence:
                row["forms"] = evidence["forms"]
            events = [
                event for event in row.get("release_events", [])
                if event["released_on"] > published and event["released_on"] not in invalid
            ]
            if events:
                row["release_events"] = events
            else:
                row.pop("release_events", None)
        if urlsplit(url).hostname == "huggingface.co" and row["release_url"] != url:
            row["official_url"] = row["release_url"]
        if document := evidence.get("report"):
            require_host(document["url"], hosts)
            if document["kind"] not in {"system card", "technical report", "official technical page", "model card"}:
                raise ValueError("Invalid verified document kind")
            current = row.get("report") or {}
            if correction and current.get("kind") == "archive":
                row["report"] = {**current, "highlights": document.get("highlights", current.get("highlights", ""))}
            else:
                identity = arxiv_key(document["url"])
                report = {**document, "id": document["url"], "rank": 2}
                if identity:
                    report.update(id=f"arxiv:{identity[0]}", revision=str(identity[1]))
                row["report"] = newer_report(current, report)
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
        if archived and archived.get("file"):
            if archived["kind"] == "archive":
                saved["report"] = archived
            elif report and archived["id"] == report["id"] and archived.get("revision") == report.get("revision"):
                saved["report"] = {**report, "file": archived["file"]}
        rows[saved["key"]] = saved
    summaries = []
    for vendor in vendors:
        config = settings[vendor]
        scans = []
        if config.get("hub") and not backfill_only:
            scans.append(("hub", scan_hub, {**config, "release_since": since}))
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
                summaries.append({"source": name, "error": source_error(error)})
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
    visible = {row["key"] for row in publishable_releases(rows.values(), settings)}
    hidden = [rows[row["key"]] for row in baseline if row["key"] not in visible]
    if hidden:
        store.save(hidden)
    if backfill_only:
        return list(rows.values()), summaries
    due = []
    recent = (date.fromisoformat(until) - timedelta(days=REPORT_RETRY_DAYS)).isoformat()
    for row in rows.values():
        if row["key"] not in visible or row["key"].split("/", 1)[0] not in vendors:
            continue
        retry = row.get("retry_on")
        if not retry and not row.get("report_checked_on") and row["released_on"] >= recent and (
            (row.get("report") or {}).get("kind") in {None, "model card", "official technical page"}
        ):
            retry = row["released_on"]
        if retry and retry <= until:
            due.append((retry, row))
    deferred_retries = max(0, len(due) - limit)
    for _, pending in sorted(due, key=lambda item: (item[0], bool(item[1].get("report")), item[1]["key"]))[:limit]:
        row = pending.copy()
        config = settings[row["key"].split("/")[0]]
        card = official_body = None
        try:
            if row.get("hub_url") and HUB_REVISION.fullmatch(row.get("hub_revision", "")):
                card = hf_card(row["hub_url"], row["hub_revision"], True)
            elif (
                (url := row.get("hub_url") or row["release_url"])
                and (repo := hub_repository(url, casefold=False))
                and urlsplit(url).path.strip("/") == repo
            ):
                document = row.get("report") or {}
                revision = document.get("revision", "") if hub_repository(document.get("url")) == repo.casefold() else ""
                if not HUB_REVISION.fullmatch(revision):
                    info = json.loads(body_text(f"{HUB}/api/models/{repo}?expand%5B%5D=sha", {"huggingface.co"}))
                    revision = info.get("sha") or ""
                if HUB_REVISION.fullmatch(revision):
                    card = hf_card(url, revision, True)
                    row.update(hub_url=url, hub_revision=revision)
        except (URLError, OSError, ValueError, TypeError):
            summaries.append({"source": row["key"], "error": "Hub card unavailable for report retry"})
        try:
            official_url = row.get("official_url") or row["release_url"]
            if urlsplit(official_url).hostname != "huggingface.co":
                official_body = body_text(official_url, COMMON_HOSTS | set(config["hosts"]))
        except (URLError, OSError, ValueError):
            summaries.append({"source": row["key"], "error": "Official page unavailable for report retry"})
        declared = declared_total(row["model"], card or "")
        if declared is None and official_body:
            page = Page(official_body)
            declared = declared_total(row["model"], "\n".join([page.summary, *page.paragraphs]))
        if declared is not None:
            row["total_parameters"] = total_parameters(row["model"], config, stored=declared)
        if not release_in_scope(row, config):
            store.save([row])
            rows[row["key"]] = row
            continue
        if warnings := try_report(row, config, arxiv, until, card=card, official_body=official_body):
            summaries.append({"source": row["key"], "report_lookup_errors": len(warnings), "warnings": warnings})
        store.save([row])
        rows[row["key"]] = row
    if deferred_retries:
        summaries.append({"source": "report-retries", "deferred": deferred_retries})
    return list(rows.values()), summaries


def publishable_releases(rows, settings):
    eligible = [row for row in rows if release_in_scope(row, settings.get(row["key"].split("/", 1)[0], {}))]
    return collapse_distributions(eligible)


def project(rows, settings, root=ROOT, mirror=False):
    result = []
    for row in publishable_releases(rows, settings):
        vendor = row["key"].split("/", 1)[0]
        config = settings.get(vendor, {})
        output = {
            key: row[key] for key in ("id", "key", "model", "org", "released_on", "release_url", "report")
        }
        for field in ("forms", "release_events", "hub_task", "total_parameters", "base_model"):
            if row.get(field):
                output[field] = row[field]
        if count := config.get("verified_total_parameters", {}).get(slug(row["model"])):
            output["total_parameters"] = count
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
    parser.add_argument("--backfill-only", action="store_true", help="Rebuild the catalog from stored and verified evidence")
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
    configure_parameters(settings, SOURCES.with_name("report-parameters.json"))
    aliases = json.loads(ALIASES.read_text())
    backfill_file = SOURCES.with_name("report-backfill.json")
    backfill = json.loads(backfill_file.read_text()) if args.since and backfill_file.is_file() else None
    if args.backfill_only and not args.since:
        parser.error("--backfill-only requires --since")
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
        manifest = set(args.pdf_manifest.read_text().splitlines()) if args.pdf_manifest else None
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
        if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
            errors = sum(bool(item.get("error")) for item in summaries)
            deferred = sum(item.get("deferred", 0) for item in summaries)
            lookups = sum(item.get("report_lookup_errors", 0) for item in summaries)
            with Path(summary_path).open("a", encoding="utf-8") as summary:
                summary.write(
                    "### Model catalog refresh\n\n"
                    f"- Public models: {len(projection)}\n"
                    f"- Updated: {len(changed)}\n"
                    f"- Removed from the index: {len(removed)}\n"
                    f"- Releases awaiting documentation: {sum(not row['report'] for row in projection)}\n"
                    f"- Source or retry errors: {errors}\n"
                    f"- Deferred items: {deferred}\n"
                    f"- Document lookup warnings: {lookups}\n"
                )
        if not args.backfill_only and not any(
            "records" in item and "report_lookup_errors" in item for item in summaries
        ):
            return 1
        if args.strict and any(
            item.get("error") or item.get("deferred") or item.get("report_lookup_errors")
            for item in summaries
        ):
            return 1
        if args.publish:
            build(pdf_manifest=manifest, rows=projection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
