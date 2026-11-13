from __future__ import annotations

import hashlib
import re
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit

from report_sources import (
    ARXIV,
    COMMON_HOSTS,
    HUB_FILES,
    REPORT_WORDS,
    TECHNICAL_WORDS,
    Page,
    arxiv_key,
    digest,
    document_links,
    fetch,
)

MAX_PDF = 99 * 1024 * 1024
SIZE_VARIANT = re.compile(r"[- ]\d+(?:\.\d+)?[BM](?=[- ]|$)", re.I)
DISTRIBUTION = re.compile(
    r"(?:^|[._-])(GGUF|AWQ|GPTQ|MLX|EXL2|INT[48]|FP8|4bit|8bit|lora|adapter)(?:[._-]|$)", re.I
)
CARD_KIND = re.compile(r"\b(system|model)[-_ ]+card\b", re.I)


def words(value):
    return re.findall(r"[a-z]+|\d+(?:\.\d+)?", value.casefold())


def matches_model(model, title):
    offered = words(title)
    return all(
        part and any(offered[i : i + len(part)] == part for i in range(len(offered)))
        for part in map(words, model.split(" / "))
    )


def normalize_model(name, vendor, aliases, settings):
    key = tuple(words(name))
    for canonical, alternatives in aliases.get(vendor, {}).items():
        if any(key == tuple(words(variant)) for variant in [canonical, *alternatives]):
            return canonical
    if settings.get("group_sizes"):
        name = SIZE_VARIANT.sub("", name)
        name = re.sub(r"[- ](?:Base|Instruct|Chat)(?:[- ]\d{4})?$", "", name, flags=re.I)
    return name.strip(" -_.")


def clean(value, limit=560):
    return " ".join(re.sub(r"<[^>]{0,300}>", " ", value or "").split())[:limit]


def report_from_arxiv(entry, model, org, priority, affiliated):
    identity = arxiv_key(entry["url"])
    title = entry["title"]
    if not identity or not matches_model(model, title):
        return None
    affiliations = entry.get("affiliations", "").casefold()
    brand = org.casefold().split(" (")[0]
    report_title = REPORT_WORDS.search(title)
    if not report_title and not words(title)[: len(words(model))] == words(model):
        return None
    if affiliated and not (report_title and len(brand) > 2 and brand in affiliations):
        return None
    identifier, version = identity
    return {
        "id": "arxiv:" + identifier,
        "revision": str(version),
        "rank": priority,
        "kind": "technical report",
        "url": f"https://arxiv.org/abs/{identifier}v{version}",
        "pdf": f"https://arxiv.org/pdf/{identifier}v{version}",
        "published_on": entry.get("date", ""),
        "highlights": clean(entry.get("summary")),
    }


def technical_excerpt(body):
    for paragraph in re.split(r"\n\s*\n", body):
        sample = clean(paragraph)
        if len(sample) >= 100 and TECHNICAL_WORDS.search(sample):
            return sample
    return ""


def pdf_excerpt(payload):
    try:
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
    except ImportError:
        return ""

    try:
        document = PdfReader(BytesIO(payload))
        text = "\n\n".join(
            document.pages[index].extract_text() or "" for index in range(min(len(document.pages), 3))
        )
    except (PdfReadError, ValueError, OSError, KeyError):
        return ""
    abstract = re.search(
        r"\babstract\s+(.{100,1200}?)(?:\n\s*1[.\s]+introduction|\n\s*introduction|$)", text, re.I | re.S
    )
    return clean(abstract[1]) if abstract else technical_excerpt(text)


def vendor_document(url, title, model, hosts, *, explicit=False, provided=None):
    if urlsplit(url).hostname not in hosts:
        return None
    path = unquote(urlsplit(url).path)
    body = provided
    if body is None:
        if path.lower().endswith(".pdf") and not explicit:
            return None
        payload, _ = fetch(url, hosts, MAX_PDF if explicit else 2_000_000)
        if payload.startswith(b"%PDF-"):
            card = CARD_KIND.search(f"{title} {path}")
            return {
                "id": url,
                "revision": hashlib.sha256(payload).hexdigest(),
                "rank": 0,
                "kind": f"{card[1].lower()} card" if card else "technical report",
                "url": url,
                "pdf": url,
                "highlights": pdf_excerpt(payload),
            }
        if path.lower().endswith(".pdf"):
            raise ValueError("Official report did not return a PDF")
        body = payload.decode("utf-8", errors="replace")
    page = Page(body)
    summary = clean(page.summary)
    if not matches_model(model, f"{page.heading} {page.title} {path}"):
        return None
    excerpt = technical_excerpt("\n\n".join(page.paragraphs))
    if not explicit and not (TECHNICAL_WORDS.search(summary) or excerpt):
        return None
    highlights = summary if TECHNICAL_WORDS.search(summary) else excerpt
    return {
        "id": url,
        "revision": digest(clean(page.heading or page.title) + "\n" + highlights),
        "rank": 0 if explicit else 2,
        "kind": "system card"
        if re.search(r"system[- ]card", f"{page.heading} {page.title} {title} {path}", re.I)
        else "official technical page",
        "url": url,
        "published_on": page.date,
        "highlights": highlights,
    }


def resolve_report(release, card, settings, arxiv, official_body=None):
    url = release["release_url"]
    model, org = release["model"], release["org"]
    hosts = COMMON_HOSTS | set(settings["hosts"])
    body = card or official_body or ""
    hub_page = urlsplit(url).hostname == "huggingface.co"
    links = document_links(body, url + "/" if hub_page else url)

    identifiers = list(dict.fromkeys(match[1] for match in ARXIV.finditer(body)))[:12]
    explicit_documents = []
    for link, label in links:
        if not arxiv_key(link) and REPORT_WORDS.search(f"{label} {unquote(urlsplit(link).path)}"):
            if urlsplit(link).hostname == "huggingface.co" and not link.startswith(url + "/"):
                continue
            if link.startswith("https://") and urlsplit(link).hostname in hosts:
                explicit_documents.append((link, label))

    errors = []
    if hub_page:
        for link, label in list(dict.fromkeys(explicit_documents))[:4]:
            try:
                target = link
                if urlsplit(link).hostname == "huggingface.co":
                    suffix = urlsplit(link).path[len(urlsplit(url).path) + 1 :]
                    suffix = re.sub(r"^(?:blob|raw|resolve)/[^/]+/", "", suffix)
                    if not suffix.lower().endswith(".pdf") or ".." in unquote(suffix).split("/"):
                        continue
                    target = f"{url}/resolve/{release['hub_revision']}/{suffix}"
                if report := vendor_document(target, label, model, hosts | HUB_FILES, explicit=True):
                    if target != link:
                        report["id"] = f"{url}/{suffix}"
                        report["url"] = f"{url}/blob/{release['hub_revision']}/{suffix}"
                    report["highlights"] = report["highlights"] or technical_excerpt(body)
                    return report, errors
            except (URLError, OSError, ValueError) as error:
                errors.append(type(error).__name__)

    if identifiers:
        try:
            for entry in arxiv.query(id_list=",".join(identifiers), max_results=len(identifiers)):
                if report := report_from_arxiv(entry, model, org, 0 if hub_page else 1, affiliated=False):
                    return report, errors
        except (URLError, OSError, ValueError) as error:
            errors.append(type(error).__name__)

    try:
        for entry in arxiv.query(search_query=f'ti:"{model}"', max_results=6):
            if report := report_from_arxiv(entry, model, org, 1, affiliated=True):
                return report, errors
    except (URLError, OSError, ValueError) as error:
        errors.append(type(error).__name__)

    fallback = list(dict.fromkeys(explicit_documents))[:4] if not hub_page else []
    official_url = release.get("official_url", url)
    if official_body:
        page = Page(official_body)
        fallback.append((official_url, page.heading or page.title))
    fallback += [
        (link, label)
        for link, label in links
        if urlsplit(link).hostname in settings["hosts"] and matches_model(model, label + " " + unquote(link))
    ]
    for link, label in list(dict.fromkeys(fallback))[:6]:
        try:
            explicit = bool(REPORT_WORDS.search(f"{label} {unquote(urlsplit(link).path)}"))
            if report := vendor_document(
                link, label, model, hosts, explicit=explicit, provided=official_body if link == official_url else None
            ):
                report["rank"] = 2
                return report, errors
        except HTTPError as error:
            if error.code not in {403, 404}:
                errors.append(f"HTTP {error.code}")
        except (URLError, OSError, ValueError) as error:
            errors.append(type(error).__name__)

    if hub_page and (excerpt := technical_excerpt(card or "")):
        revision = release["hub_revision"]
        return {
            "id": url + "/README.md",
            "revision": revision,
            "rank": 3,
            "kind": "model card",
            "url": f"{url}/blob/{revision}/README.md",
            "highlights": excerpt,
        }, errors
    return None, errors
