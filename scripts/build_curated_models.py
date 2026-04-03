#!/usr/bin/env python3
"""Build a curated runtime model snapshot from the current README."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import discover_models, update_readme_incremental
DEFAULT_README = ROOT / "README.md"
DEFAULT_DISCOVERED_MODELS = ROOT / "scripts" / "latest_models.json"
DEFAULT_OUTPUT = ROOT / "scripts" / "latest_models_curated.json"
MAX_CANDIDATE_LINKS = 12
NOISE_HOSTS = {
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
    "https://www.gstatic.com",
}


def extract_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    match = re.search(r"\((https?://[^)]+)\)", text)
    if match:
        return match.group(1).strip()
    return text


def normalize_url(url: str) -> str:
    if "arxiv.org/abs/" in url:
        return url.replace("/abs/", "/pdf/")
    if "github.com" in url and "/blob/" in url and url.endswith(".pdf"):
        return url.replace("/blob/", "/raw/")
    return url


def is_noise_candidate_url(url: str) -> bool:
    lower = url.lower()
    if any(lower.startswith(host) for host in NOISE_HOSTS):
        return True
    if "#" in lower:
        return True
    if any(token in lower for token in ["/_next/", "/_astro/", "_server-islands", "favicon"]):
        return True
    if lower.endswith(
        (
            ".css",
            ".js",
            ".svg",
            ".ico",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".woff",
            ".woff2",
            ".xml",
        )
    ):
        return True
    return False


def candidate_priority(url: str) -> int:
    lower = url.lower()
    if lower.endswith(".pdf"):
        return 100
    if "arxiv.org/" in lower:
        return 95
    if "github.com/" in lower or "huggingface.co/" in lower or "modelscope.cn/" in lower:
        return 90
    if any(token in lower for token in ["/model-cards/", "/system-card", "/model_card", "/docs/", "/research/"]):
        return 85
    if any(token in lower for token in ["/news/", "/blog/", "/release-notes", "/guides/"]):
        return 75
    return 60


def candidate_host(url: str) -> str:
    return urlparse(url).netloc.casefold()


def is_allowed_cross_host(url: str) -> bool:
    lower = url.lower()
    return "arxiv.org/" in lower or lower.endswith(".pdf")


def limit_links(
    urls: Iterable[str],
    limit: int = MAX_CANDIDATE_LINKS,
    *,
    filter_noise: bool = False,
) -> List[str]:
    deduped: List[str] = []
    seen = set()
    ranked: List[Tuple[int, int, str]] = []
    for idx, url in enumerate(urls):
        cleaned = normalize_url(extract_url(url))
        if not cleaned or cleaned in seen:
            continue
        if filter_noise and is_noise_candidate_url(cleaned):
            continue
        seen.add(cleaned)
        ranked.append((candidate_priority(cleaned), -idx, cleaned))
    for _, _, cleaned in sorted(ranked, reverse=True):
        deduped.append(cleaned)
        if len(deduped) >= limit:
            break
    return deduped


def load_discovered_models(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("discovered models snapshot must be a list")
    results: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if str(item.get("release_classification", "model_release")).strip() not in {"", "model_release"}:
            continue
        if not item.get("org_slug") or not item.get("model"):
            continue
        results.append(dict(item))
    return results


def discovered_record_score(record: Dict[str, Any]) -> Tuple[float, int, int, int]:
    confidence = float(record.get("confidence") or 0)
    evidence_count = len(record.get("evidence_urls") or [])
    candidate_count = len(record.get("candidate_links") or [])
    has_pdf = 1 if str(record.get("official_link", "")).lower().endswith(".pdf") else 0
    return (confidence, evidence_count, candidate_count, has_pdf)


def build_discovered_index(
    records: Iterable[Dict[str, Any]],
    alias_config: Dict[str, Dict[str, List[str]]],
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    index: Dict[Tuple[str, str], Tuple[Tuple[float, int, int, int], Dict[str, Any]]] = {}
    for record in records:
        org_slug = str(record.get("org_slug", "")).strip()
        model = str(record.get("model", "")).strip()
        if not org_slug or not model:
            continue
        candidates = [model, *(record.get("aliases") or [])]
        resolution = discover_models.canonicalize_model_name(org_slug, model, alias_config=alias_config)
        candidates.extend(resolution.aliases)
        candidates.append(resolution.canonical_name)
        score = discovered_record_score(record)
        for candidate in candidates:
            token = discover_models.normalize_alias_token(candidate)
            if not token:
                continue
            key = (org_slug, token)
            if key not in index or score > index[key][0]:
                index[key] = (score, record)
    return {key: value[1] for key, value in index.items()}


def select_release_date(readme_date: str, discovered_date: str) -> str:
    if re.match(r"^20\d{2}-\d{2}$", (readme_date or "").strip()):
        return readme_date.strip()
    if re.match(r"^20\d{2}-\d{2}$", (discovered_date or "").strip()):
        return discovered_date.strip()
    return (readme_date or discovered_date or "").strip()


def build_curated_models(
    *,
    readme_path: Path = DEFAULT_README,
    discovered_models_path: Path = DEFAULT_DISCOVERED_MODELS,
) -> List[Dict[str, Any]]:
    alias_config = discover_models.load_alias_config()
    readme_rows = update_readme_incremental.parse_existing_rows(readme_path.read_text(encoding="utf-8"))
    discovered_index = build_discovered_index(load_discovered_models(discovered_models_path), alias_config)

    curated: List[Dict[str, Any]] = []
    for row in readme_rows:
        org_slug = update_readme_incremental.infer_org_slug(row)
        resolution = discover_models.canonicalize_model_name(org_slug, row["model"], alias_config=alias_config)
        match = discovered_index.get((org_slug, discover_models.normalize_alias_token(row["model"])))
        if match is None:
            match = discovered_index.get(
                (org_slug, discover_models.normalize_alias_token(resolution.canonical_name))
            )

        readme_official_link = extract_url(row["official_link"])
        official_link = extract_url(str(match.get("official_link", ""))) if match else ""
        if not official_link:
            official_link = readme_official_link
        extra_candidate_links: List[str] = []
        if org_slug == "xai":
            extra_candidate_links.append(discover_models.XAI_RELEASE_NOTES_URL)
        preferred_hosts = {
            candidate_host(url)
            for url in [
                official_link,
                readme_official_link,
                extract_url(str((match or {}).get("source_page", ""))),
                *extra_candidate_links,
            ]
            if url
        }

        aliases = [row["model"], resolution.canonical_name, *resolution.aliases]
        if match:
            aliases.extend(match.get("aliases") or [])

        candidate_links = limit_links(
            [
                official_link,
                readme_official_link,
                extract_url(str((match or {}).get("source_page", ""))),
                *extra_candidate_links,
                *((match or {}).get("candidate_links") or []),
            ],
            filter_noise=True,
        )
        candidate_links = [
            url
            for url in candidate_links
            if candidate_host(url) in preferred_hosts or is_allowed_cross_host(url)
        ][:MAX_CANDIDATE_LINKS]
        evidence_urls = limit_links(
            [
                *((match or {}).get("evidence_urls") or []),
                *((match or {}).get("candidate_links") or []),
                official_link,
                readme_official_link,
                extract_url(str((match or {}).get("source_page", ""))),
                *extra_candidate_links,
            ]
        )
        source_page = extract_url(str((match or {}).get("source_page", ""))) or official_link
        if org_slug == "xai":
            source_page = discover_models.XAI_RELEASE_NOTES_URL
        curated.append(
            {
                "release_date": select_release_date(
                    row["release_date"],
                    str((match or {}).get("release_date", "")),
                ),
                "org": update_readme_incremental.ORG_DISPLAY.get(org_slug, row["organization"]),
                "org_slug": org_slug,
                "model": row["model"],
                "canonical_model_id": discover_models.build_canonical_model_id(
                    org_slug, resolution.canonical_name
                ),
                "aliases": list(dict.fromkeys(alias for alias in aliases if alias)),
                "core_feature": row["core_highlights"],
                "official_link": official_link,
                "candidate_links": candidate_links,
                "source_page": source_page,
                "evidence_urls": evidence_urls,
                "evidence_type": str((match or {}).get("evidence_type", "curated_readme")),
                "release_classification": "model_release",
                "classification_reason": str(
                    (match or {}).get("classification_reason", "existing_repo_entry")
                ),
                "confidence": float((match or {}).get("confidence") or 0.55),
                "discovered_at": str((match or {}).get("discovered_at", "")),
            }
        )
    return curated


def write_curated_models_snapshot(
    *,
    readme_path: Path = DEFAULT_README,
    discovered_models_path: Path = DEFAULT_DISCOVERED_MODELS,
    output_path: Path = DEFAULT_OUTPUT,
) -> List[Dict[str, Any]]:
    curated = build_curated_models(
        readme_path=readme_path,
        discovered_models_path=discovered_models_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(curated, ensure_ascii=False, indent=2), encoding="utf-8")
    return curated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a curated runtime models snapshot from README + discovery metadata."
    )
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--discover-json", type=Path, default=DEFAULT_DISCOVERED_MODELS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    curated = write_curated_models_snapshot(
        readme_path=args.readme,
        discovered_models_path=args.discover_json,
        output_path=args.output,
    )
    print(f"curated_models={len(curated)} -> {args.output}")


if __name__ == "__main__":
    main()
