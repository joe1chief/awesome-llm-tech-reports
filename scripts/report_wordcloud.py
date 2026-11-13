from __future__ import annotations

import argparse
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from report_catalog import ROOT, json_text, put, read_catalog, validate
from report_resolution import ACCESS_CHALLENGE
from report_sources import COMMON_HOSTS, HUB_FILES, MAX_BODY, arxiv_key, fetch
from report_terms import (
    BODY_SOURCES, TERM_INDEX, VERSION, document_revision, glossary_revision, latest_year, term_index,
    terms_for_text, yearly_documents,
)

MAX_PDF = 80 * 1024 * 1024
MAX_TEXT = 350_000
SKIP_TAGS = {"aside", "footer", "form", "head", "nav", "noscript", "pre", "script", "style", "svg"}
BLOCK_TAGS = {"article", "div", "h1", "h2", "h3", "h4", "li", "main", "p", "section", "tr"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
REAR_SECTION = re.compile(
    r"(?im)^\s*(?:#{1,6}\s+)?(?:\d+\.?\s+)?(?:references|bibliography|citation|license|"
    r"terms of use|acknowledg(?:e)?ments?|参考文献)\s*[:：]?\s*$"
)


class Article(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.main = []
        self.other = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in VOID_TAGS:
            hidden = tag in SKIP_TAGS or attrs.get("aria-hidden") == "true"
            self.stack.append((tag, hidden))
        if tag in BLOCK_TAGS or tag == "br":
            self.handle_data("\n")

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self.handle_data("\n")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not any(hidden for _, hidden in self.stack):
            target = self.main if any(tag in {"article", "main"} for tag, _ in self.stack) else self.other
            target.append(data)

    def body(self):
        main = "".join(self.main)
        return main if has_body(main) else "".join([main, "\n", *self.other])


def plain_text(text, kind):
    if kind == "markdown":
        text = re.sub(r"\A\s*---\s*\n.*?\n---\s*(?:\n|$)", "", text, count=1, flags=re.S)
        text = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"<[^>\n]+>", "", text)
    elif kind == "html":
        text = Article(text).body()
    if (rear := REAR_SECTION.search(text, 350)) is not None:
        text = text[:rear.start()]
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=[a-z])", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return "\n".join(" ".join(line.split()) for line in text[:MAX_TEXT].splitlines() if line.strip())


def pdf_text(payload):
    pages, length = [], 0
    with PdfReader(payload) as reader:
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
            except (PyPdfError, ValueError, KeyError, UnicodeError):
                logging.warning("A PDF page had no readable text")
                continue
            pages.append(text)
            length += len(text)
            if length >= MAX_TEXT:
                break
    return plain_text("\n".join(pages), "pdf")


def remote_source(report):
    url = report["url"]
    parsed = urlsplit(url)
    if identity := arxiv_key(url):
        version = f"v{identity[1]}" if re.search(r"v\d+$", parsed.path) else ""
        return f"https://arxiv.org/pdf/{identity[0]}{version}", "source PDF"
    if parsed.hostname == "huggingface.co":
        path = parsed.path.strip("/").split("/")
        if len(path) == 2:
            return f"https://huggingface.co/{'/'.join(path)}/raw/main/README.md", "model card"
        if len(path) >= 5 and path[2] == "blob":
            path[2] = "resolve" if parsed.path.lower().endswith(".pdf") else "raw"
            return urlunsplit(parsed._replace(path="/" + "/".join(path))), (
                "source PDF" if path[2] == "resolve" else "model card"
            )
    return url, "source PDF" if parsed.path.lower().endswith(".pdf") else "source page"


def read_source(report, root, hosts):
    archive = report.get("file")
    if archive and (root / archive).is_file():
        try:
            text = pdf_text(root / archive)
            if has_body(text):
                return text, "archive PDF"
        except (OSError, PyPdfError, ValueError, KeyError):
            logging.warning("Archived report had no readable text: %s", archive)
    url, kind = remote_source(report)
    payload, headers = fetch(url, hosts, MAX_BODY if kind == "model card" else MAX_PDF)
    if payload.startswith(b"%PDF-"):
        if b"%%EOF" not in payload[-4096:]:
            raise ValueError("Incomplete report PDF")
        return pdf_text(BytesIO(payload)), "source PDF"
    if kind == "source PDF" or "application/pdf" in headers.get("Content-Type", ""):
        raise ValueError("Source returned a page in place of a PDF")
    if len(payload) > MAX_BODY:
        raise ValueError("Source page exceeds the text input limit")
    body = payload.decode("utf-8", errors="replace")
    if ACCESS_CHALLENGE.search(body[:2000]):
        raise ValueError("Source returned an access challenge")
    if kind == "model card" and not re.search(r"<!doctype html|<html\b", body[:500], re.I):
        return plain_text(body, "markdown"), kind
    return plain_text(body, "html"), kind


def has_body(text):
    return len(re.findall(r"[A-Za-z]{3,}", text)) >= 45 or len(re.findall(r"[\u3400-\u9fff]", text)) >= 150


def refresh_terms(root, rows, *, limit=30, until=None, local_only=False):
    year = latest_year(rows)
    targets = yearly_documents(rows, year)
    glossary_path = root / "configs/report-terms.json"
    glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
    sources = json.loads((root / "configs/report-sources.json").read_text(encoding="utf-8"))
    today = until or date.today()
    entries = {
        key: value for key, value in term_index(root, glossary).items()
        if key in targets and value.get("revision") == document_revision(targets[key]["report"])
    }
    due = [
        (key, row) for key, row in targets.items()
        if (not local_only or (row["report"].get("file") and (root / row["report"]["file"]).is_file()))
        and (not (record := entries.get(key)) or record["check_on"] <= today.isoformat())
    ]
    due.sort(key=lambda item: (
        not bool(item[1]["report"].get("file")), bool(entries.get(item[0], {}).get("source")),
        item[0] in entries, item[0],
    ))

    def read(item):
        key, row = item
        hosts = COMMON_HOSTS | HUB_FILES | set(sources.get(row["key"].split("/")[0], {}).get("hosts", []))
        report = row["report"]
        previous = entries.get(key, {})
        state = {**previous, "revision": document_revision(report)}
        try:
            if local_only:
                body, kind = pdf_text(root / report["file"]), "archive PDF"
            else:
                body, kind = read_source(report, root, hosts)
            if not has_body(body):
                raise ValueError("No readable report body")
            pinned = kind == "archive PDF" or re.search(r"/blob/[a-f0-9]{40}/|arxiv\.org/abs/\d+\.\d+v\d+", report["url"])
            next_check = today + timedelta(days=3650 if pinned else 30)
            return key, {**state, "source": kind, "terms": terms_for_text(body, glossary), "check_on": next_check.isoformat()}
        except (URLError, OSError, PyPdfError, ValueError, KeyError, UnicodeError) as error:
            logging.warning("Word cloud source %s: %s", row["key"], type(error).__name__)
            return key, {**state, "check_on": (today + timedelta(days=7)).isoformat()}

    def save():
        put(root / TERM_INDEX, json_text({
            "version": VERSION, "year": int(year), "glossary": glossary_revision(glossary), "documents": entries,
        }))

    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = due[:limit]
        for offset in range(0, len(pending), 12):
            entries.update(pool.map(read, pending[offset:offset + 12]))
            save()
    if not pending:
        save()
    read_count = sum(entry.get("source") in BODY_SOURCES for entry in entries.values())
    print(f"Word cloud source text available for {read_count} of {len(targets)} distinct documents")
    return read_count


def main():
    parser = argparse.ArgumentParser(description="Extract terms from archived PDFs and model document sources")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--pdf-manifest", type=Path)
    parser.add_argument("--local-only", action="store_true", help="Index archived PDFs in this checkout")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    rows = read_catalog()
    manifest = set(args.pdf_manifest.read_text().splitlines()) if args.pdf_manifest else None
    validate(rows, pdf_manifest=manifest)
    refresh_terms(ROOT, rows, limit=args.limit, local_only=args.local_only)


if __name__ == "__main__":
    main()
