from __future__ import annotations

import hashlib
import re
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit

from report_identity import document_priority
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
CARD_KIND = re.compile(r"\b(system|model)[-_ ]+card\b", re.I)
PAPER_CITATION = re.compile(r"\b(?:paper|report)\s+(?:of|for|on)\s+|(?:技术报告|论文)\s*[：:]", re.I)
STRUCTURAL_EXCERPT = re.compile(r"^(?:---|\||!\[|[0-9]+\.\s|[+-]\s|\x60\x60\x60)")
ACCESS_CHALLENGE = re.compile(
    r"verif(?:y|ies|ying) you are (?:not a bot|human)|checking your browser|access denied|just a moment", re.I
)


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


def report_from_arxiv(entry, model, org, priority, affiliated, *, direct=False):
    identity = arxiv_key(entry["url"])
    title = entry["title"]
    if not identity or (not direct and not matches_model(model, title)):
        return None
    affiliations = entry.get("affiliations", "").casefold()
    brand = org.casefold().split(" (")[0]
    report_title = REPORT_WORDS.search(title)
    if not direct and not report_title and words(title)[: len(words(model))] != words(model):
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
    body = re.sub(r"\A\s*---[^\n]*\n.*?\n---[^\n]*(?:\n|$)", "", body, count=1, flags=re.S)
    body = re.sub(r"(?ms)^(\x60{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", body)
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = re.sub(r"(?m)^#{1,6}[ \t]+[^\n]*\n?", "", paragraph)
        if STRUCTURAL_EXCERPT.match(paragraph.lstrip()):
            continue
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
            if b"%%EOF" not in payload[-4096:]:
                raise ValueError("Source returned an incomplete PDF")
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
    if ACCESS_CHALLENGE.search(" ".join((page.title, page.heading, page.summary))):
        raise ValueError("Source returned an access challenge")
    summary = clean(page.summary)
    if not matches_model(model, f"{page.heading} {page.title} {path}"):
        return None
    excerpt = technical_excerpt("\n\n".join(page.paragraphs))
    if not explicit and not (TECHNICAL_WORDS.search(summary) or excerpt):
        return None
    highlights = summary if TECHNICAL_WORDS.search(summary) else excerpt
    card = CARD_KIND.search(f"{page.heading} {page.title} {title} {path}")
    return {
        "id": url,
        "revision": digest(clean(page.heading or page.title) + "\n" + highlights),
        "rank": 0 if explicit else 2,
        "kind": f"{card[1].lower()} card" if card else "official technical page",
        "url": url,
        "published_on": page.date,
        "highlights": highlights,
    }


def report_links(links, model, hosts, hub_url=""):
    result = []
    for link, label in links:
        path = unquote(urlsplit(link).path)
        host = urlsplit(link).hostname
        if not link.startswith("https://") or host not in hosts or arxiv_key(link):
            continue
        label_and_path = f"{label} {path}"
        pdf = path.lower().endswith(".pdf")
        named = matches_model(model, label_and_path)
        explicit = bool(REPORT_WORDS.search(label_and_path)) or (
            pdf and (named or label.strip().casefold() in {"paper", "report", "read the paper"})
        )
        if host == "huggingface.co" and (not hub_url or not link.startswith(hub_url + "/") or not pdf):
            continue
        if explicit or named:
            result.append((link, label, explicit, named))
    return [(link, label, explicit) for link, label, explicit, _ in sorted(
        result, key=lambda item: (not item[2], not item[3])
    )]


def cited_papers(model, card, official_body):
    citations = {}
    name = " ".join(words(model))
    for rank, body in enumerate((card, official_body)):
        for line in re.split(r"\n|</(?:p|li)>", body or "", flags=re.I):
            matches = ARXIV.findall(line)
            if not matches:
                continue
            text = " ".join(words(clean(line, 800)))
            direct = len(matches) == 1 and name and (
                bool(re.search(rf"(?<!\w){re.escape(name)} (?:technical report|system card|paper)\b", text))
                or any(
                    " ".join(words(clean(line[match.end():], 120))).startswith(name + " ")
                    for match in PAPER_CITATION.finditer(line)
                )
            )
            for identifier, _ in matches:
                evidence = (not direct, rank)
                citations[identifier] = min(citations.get(identifier, evidence), evidence)
    return dict(sorted(citations.items(), key=lambda item: item[1])[:12])


def linked_report(candidates, release, hosts, errors, *, hub_url="", rank=0, provided=None):
    best = None
    for link, label, explicit in candidates:
        target = link
        suffix = ""
        if hub_url and urlsplit(link).hostname == "huggingface.co":
            suffix = urlsplit(link).path[len(urlsplit(hub_url).path) + 1 :]
            suffix = re.sub(r"^(?:blob|raw|resolve)/[^/]+/", "", suffix)
            if ".." in unquote(suffix).split("/"):
                continue
            target = f"{hub_url}/resolve/{release['hub_revision']}/{suffix}"
        try:
            report = vendor_document(
                target, label, release["model"], hosts, explicit=explicit, provided=(provided or {}).get(target)
            )
        except (URLError, OSError, ValueError) as error:
            errors.append(f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__)
            continue
        if not report:
            continue
        report["rank"] = rank
        if suffix:
            report["id"] = f"{hub_url}/{suffix}"
            report["url"] = f"{hub_url}/blob/{release['hub_revision']}/{suffix}"
        if not best or document_priority(report) < document_priority(best):
            best = report
        if report["kind"] == "technical report":
            break
    return best


def resolve_report(release, card, settings, arxiv, official_body=None):
    url = release["release_url"]
    model, org = release["model"], release["org"]
    hosts = COMMON_HOSTS | set(settings["hosts"])
    hub_url = release.get("hub_url") or (url if urlsplit(url).hostname == "huggingface.co" else "")
    if not release.get("hub_revision"):
        hub_url = ""
    official_url = release.get("official_url", url)
    hub_links = document_links(card or "", hub_url + "/") if hub_url else []
    official_links = document_links(official_body or "", official_url)
    candidates = report_links(hub_links, model, hosts, hub_url)
    errors = []
    best = linked_report([item for item in candidates if item[2]][:4], release, hosts | HUB_FILES, errors, hub_url=hub_url)
    if best and best["kind"] == "technical report":
        best["highlights"] = best["highlights"] or technical_excerpt(card or "")
        return best, errors

    citations = cited_papers(model, card, official_body)
    if citations:
        try:
            entries = {
                identity[0]: entry
                for entry in arxiv.query(id_list=",".join(citations), max_results=len(citations))
                if (identity := arxiv_key(entry["url"]))
            }
            for identifier, (implicit, rank) in citations.items():
                if identifier in entries:
                    report = report_from_arxiv(entries[identifier], model, org, rank, affiliated=False, direct=not implicit)
                    if report:
                        return report, errors
        except (URLError, OSError, ValueError) as error:
            errors.append(type(error).__name__)

    try:
        for entry in arxiv.query(search_query=f'ti:"{model}"', max_results=6):
            if report := report_from_arxiv(entry, model, org, 1, affiliated=True):
                return report, errors
    except (URLError, OSError, ValueError) as error:
        errors.append(type(error).__name__)

    fallback = report_links(official_links, model, hosts)
    fallback.extend(item for item in candidates if not item[2])
    linked = linked_report(
        list(dict.fromkeys(fallback))[:6], release, hosts | HUB_FILES, errors, rank=2,
        provided={official_url: official_body},
    )
    choices = [report for report in (best, linked) if report]
    if official_body:
        page = Page(official_body)
        try:
            if report := vendor_document(official_url, page.heading or page.title, model, hosts, provided=official_body):
                choices.append(report)
        except ValueError as error:
            errors.append(str(error))

    if card and hub_url and (excerpt := technical_excerpt(card)):
        revision = release["hub_revision"]
        choices.append({
            "id": hub_url + "/README.md",
            "revision": revision,
            "rank": 3,
            "kind": "model card",
            "url": f"{hub_url}/blob/{revision}/README.md",
            "highlights": excerpt,
        })
    return min(choices, key=lambda report: (document_priority(report), report["rank"]), default=None), errors
