from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import urlsplit

from report_catalog import slug

FORMAT = r"(?:bf16|fp(?:4|8|16|32)(?:[-_]?e[45]m[23])?|nvfp4|mxfp[48]|int[248]|w\d+a\d+|[248]bit|gguf|awq|gptq|mlx|exl2|bnb[48]bit)"
FORMAT_SUFFIX = re.compile(rf"(?:[-_. ]+(?:ascend[-_. ]+)?{FORMAT})+(?:[-_. ]+local)?$", re.I)
QUANTIZED = re.compile(
    rf"[-_. ]+(?:ascend[-_. ]+)?(?!bf16\b|fp16\b|fp32\b){FORMAT}(?:[-_. ]+local)?$", re.I
)
BASE_MODEL = re.compile(r"base_model:(adapter|quantized):([\w.-]+/[\w.-]+)$", re.I)
HUB_REPO = re.compile(r"[\w.-]+/[\w.-]+$", re.ASCII)
DOCUMENT_ORDER = {
    "archive": 0, "technical report": 1, "system card": 2, "model card": 3, "official technical page": 4,
}


def hub_relation(tags):
    for tag in sorted(tags):
        if match := BASE_MODEL.fullmatch(tag):
            return match[1].lower(), match[2].casefold()
    return "", ""


def hub_repository(url, *, casefold=True):
    parsed = urlsplit(url or "")
    path = "/".join(parsed.path.strip("/").split("/")[:2])
    if parsed.hostname != "huggingface.co" or not HUB_REPO.fullmatch(path):
        return ""
    return path.casefold() if casefold else path


def document_priority(report):
    if not report:
        return len(DOCUMENT_ORDER)
    return DOCUMENT_ORDER.get(report["kind"], len(DOCUMENT_ORDER))


def collapse_distributions(rows):
    primary = {}
    original_names = defaultdict(list)
    repositories = {}
    packages = []
    for row in rows:
        model, key = row["model"], row["key"]
        stem = FORMAT_SUFFIX.sub("", model)
        if stem != model or row.get("base_model"):
            if not (row.get("report") or {}).get("file"):
                packages.append((row, slug(stem)))
                continue
        primary[key] = row
        original_names[slug(model)].append(key)
        for url in (row.get("hub_url"), row["release_url"]):
            if repo := hub_repository(url):
                repositories[repo] = key

    groups = defaultdict(list)
    for row, name in packages:
        vendor = row["key"].split("/", 1)[0]
        targets = original_names[name]
        local = [key for key in targets if key.startswith(vendor + "/")]
        base_model = row.get("base_model")
        target = repositories.get(base_model)
        if not target and len(local) == 1:
            target = local[0]
        if not target and not row.get("base_model") and not local and len(targets) == 1:
            target = targets[0]
        group = target or base_model or (vendor, name)
        groups[group].append(row)

    removed = set()
    for target, variants in groups.items():
        canonical = primary.get(target)
        if not canonical:
            canonical = min(variants, key=lambda row: (
                bool(row.get("base_model")) and row.get("base_model", "").split("/")[0]
                != hub_repository(row.get("hub_url") or row["release_url"]).split("/")[0],
                bool(QUANTIZED.search(row["model"])), row["released_on"], row["key"],
            ))
        chosen = canonical.copy()
        for variant in sorted(variants, key=lambda row: row["key"]):
            report = variant.get("report")
            if report and report["kind"] in {"technical report", "system card"}:
                if document_priority(report) < document_priority(chosen.get("report")):
                    chosen["report"] = report
        primary[canonical["key"]] = chosen
        removed.update(row["key"] for row in variants if row["key"] != canonical["key"])
    return [primary[row["key"]] for row in rows if row["key"] not in removed]
