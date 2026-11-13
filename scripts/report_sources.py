from __future__ import annotations

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from report_catalog import https_url

HUB = "https://huggingface.co"
ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV = re.compile(r"(?:arxiv\.org/(?:abs|pdf|html)/|arxiv:)(\d{4}\.\d{4,5})(?:v(\d+))?", re.I)
COMMON_HOSTS = {"huggingface.co", "arxiv.org", "export.arxiv.org"}
HUB_FILES = {"cdn-lfs.huggingface.co", "cdn-lfs-us-1.hf.co", "cdn-lfs-eu-1.hf.co", "cas-bridge.xethub.hf.co"}
MAX_BODY = 2_000_000
REPORT_WORDS = re.compile(r"tech(?:nical)?[-_ ]report|system[-_ ]card|model[-_ ]card|white[-_ ]?paper", re.I)
TECHNICAL_WORDS = re.compile(
    r"\b(training|architecture|evaluation|benchmark|parameters|inference|reasoning)\b", re.I
)


class Redirects(HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_host(newurl, self.hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def require_host(url, hosts):
    if not https_url(url) or urlsplit(url).hostname not in hosts:
        raise ValueError("URL outside configured source hosts")


def fetch(url, hosts=COMMON_HOSTS, limit=MAX_BODY):
    require_host(url, hosts)
    opener = build_opener(Redirects(hosts))
    request = Request(url, headers={"User-Agent": "awesome-llm-tech-reports/1.0"})
    for attempt in range(3):
        try:
            with opener.open(request, timeout=18) as response:
                body = response.read(limit + 1)
                if len(body) > limit:
                    raise ValueError("Source response exceeds byte limit")
                return body, response.headers
        except HTTPError as error:
            if attempt == 2 or error.code not in {429, 500, 502, 503, 504}:
                raise
            retry_after = error.headers.get("Retry-After", "")
            if retry_after and (not retry_after.isdigit() or int(retry_after) > 12):
                raise
            time.sleep(int(retry_after) if retry_after else 2**attempt)
    raise AssertionError("Unreachable request retry")


def body_text(url, hosts=COMMON_HOSTS):
    return fetch(url, hosts)[0].decode("utf-8", errors="replace")


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


DATE_TEXT = re.compile(
    r"(?<!\d)20\d{2}(?:[./-]\d{1,2}[./-]\d{1,2}|年\s*\d{1,2}月\s*\d{1,2}日)"
    r"|\b(?:[a-z]{3,9}\.?\s+\d{1,2},?|\d{1,2}\s+[a-z]{3,9}\.?)\s+20\d{2}\b",
    re.I,
)


def date_value(value):
    if not isinstance(value, str) or not value:
        return ""
    value = value.strip()
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        pass
    parts = re.fullmatch(r"(\d{4})[年./-]\s*(\d{1,2})[月./-]\s*(\d{1,2})日?", value)
    if parts:
        try:
            return date(*map(int, parts.groups())).isoformat()
        except ValueError:
            return ""
    plain = value.replace(".", "").replace(",", "")
    for pattern in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(plain, pattern).date().isoformat()
        except ValueError:
            continue
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (ValueError, TypeError):
        return ""


def date_in(text):
    return next((value for found in DATE_TEXT.finditer(text) if (value := date_value(found[0]))), "")


def model_pages(owner, earliest):
    query = [
        ("author", owner),
        ("sort", "lastModified"),
        ("direction", -1),
        ("limit", 100),
        *[("expand[]", field) for field in ("sha", "createdAt", "lastModified", "gated", "pipeline_tag", "tags", "safetensors")],
    ]
    url = HUB + "/api/models?" + urlencode(query)
    visited = set()
    while url:
        if url in visited or len(visited) >= 25:
            raise ValueError("Hugging Face pagination was incomplete")
        visited.add(url)
        payload, headers = fetch(url, {"huggingface.co"})
        rows = json.loads(payload)
        if not isinstance(rows, list):
            raise ValueError("Expected a Hugging Face model list")
        older_page = False
        for row in rows:
            model = row.get("id") or row.get("modelId") or ""
            modified = date_value(row.get("lastModified")) or date_value(row.get("createdAt"))
            if (
                not re.fullmatch(r"[\w.-]+/[\w.-]+", model, re.ASCII)
                or model.split("/")[0].casefold() != owner.casefold()
            ):
                raise ValueError("Unexpected Hugging Face repository owner")
            if not modified:
                raise ValueError("Hugging Face model has no valid timestamp")
            if modified >= earliest:
                yield {**row, "id": model, "modified": modified}
            else:
                older_page = True
        if older_page:
            return
        next_link = re.search(r'<([^>]+)>;\s*rel="?next"?', headers.get("Link", ""))
        url = urljoin(url, next_link.group(1)) if next_link else ""
        if url and urlsplit(url).path != "/api/models":
            raise ValueError("Unexpected Hugging Face pagination path")


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.heading = ""
        self.date = ""
        self.summary = ""
        self.links = []
        self.paragraphs = []
        self.paragraph = None
        self.current = None
        self.in_title = False
        self.in_heading = False
        self.ignored = False
        self.heading_label = ""
        self.heading_context = None
        self.visible_date = ""
        self.date_context = []
        self.time_date = ""
        self.feed(text)
        if not self.date:
            found = re.search(r'"datePublished"\s*:\s*"([^"]+)"', text)
            self.date = (date_value(found[1]) if found else "") or self.visible_date

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        prop = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
        excluded_date = bool(re.search(
            r"updated|modified|更新|修改", " ".join((prop or "", attrs.get("class", ""))), re.I
        ))
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.date_context.append([tag, excluded_date])
        if tag == "meta" and prop in {"article:published_time", "datePublished", "pubdate", "date"}:
            self.date = self.date or date_value(attrs.get("content"))
        if tag == "meta" and prop in {"description", "og:description"}:
            self.summary = self.summary or attrs.get("content", "")
        if tag == "a":
            self.current = [attrs.get("href", ""), ""]
        if tag == "title":
            self.in_title = True
        if tag == "h1" and not self.heading:
            self.in_heading = True
            self.heading_label = attrs.get("aria-label", "")
        if tag in {"script", "style"}:
            self.ignored = True
        if tag == "time" and prop == "datePublished":
            self.date = self.date or date_value(attrs.get("datetime"))
        if tag == "time" and self.heading_context is not None:
            self.time_date = date_value(attrs.get("datetime"))
        if tag == "p":
            self.paragraph = []

    def handle_data(self, data):
        if self.ignored:
            return
        if re.search(r"\b(?:updated|modified)\b|更新|修改", data, re.I) and self.date_context:
            self.date_context[-1][1] = True
        excluded_date = any(excluded for _, excluded in self.date_context)
        in_time = any(tag == "time" for tag, _ in self.date_context)
        if in_time and not excluded_date:
            self.time_date = self.time_date or date_in(data)
        if self.current:
            self.current[1] += " " + data
        if self.in_title:
            self.title += data
        if self.in_heading:
            self.heading += data
        if self.heading_context is not None and not self.visible_date:
            self.heading_context += len(data.strip())
            if not excluded_date and not in_time and self.heading_context <= 350 and len(data.strip()) <= 100:
                self.visible_date = date_in(data)
            if self.heading_context > 350:
                self.heading_context = None
        if not self.visible_date and re.match(r"\s*(?:Published\b|发布日期)", data, re.I):
            self.visible_date = date_in(data)
        if self.paragraph is not None:
            self.paragraph.append(data)

    def handle_endtag(self, tag):
        if tag == "time":
            if self.heading_context is not None and not any(excluded for _, excluded in self.date_context):
                self.visible_date = self.visible_date or self.time_date
            self.time_date = ""
        for index in range(len(self.date_context) - 1, -1, -1):
            if self.date_context[index][0] == tag:
                del self.date_context[index:]
                break
        if tag == "a" and self.current:
            self.links.append(tuple(self.current))
            self.current = None
        if tag == "title":
            self.in_title = False
        if tag == "h1" and self.in_heading:
            self.heading = self.heading.strip() or self.heading_label
            self.in_heading = False
            self.heading_context = 0
        if tag in {"script", "style"}:
            self.ignored = False
        if tag == "p" and self.paragraph is not None:
            self.paragraphs.append("".join(self.paragraph))
            self.paragraph = None


def document_links(text, base):
    links = [(url, title) for title, url in re.findall(r"\[([^\]\n]+)\]\(([^)\s]+)\)", text)]
    if re.search(r"<a\b", text, re.I):
        links.extend(Page(text).links)
    links.extend((url, "") for url in re.findall(r"https://[^\s<>\]\"')]+", text))
    unique = {}
    for url, label in links:
        if url:
            url = urljoin(base, url.rstrip(".,"))
            unique[url] = unique.get(url) or label
    return list(unique.items())


def xml_entries(text):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise ValueError("Source returned malformed XML") from error
    for item in root.iter():
        kind = item.tag.split("}")[-1]
        if kind not in {"entry", "item", "url"}:
            continue
        fields = {child.tag.split("}")[-1]: child for child in item}
        link = next(
            (node for node in item if node.tag.split("}")[-1] == "link"
             and node.get("rel", "alternate") == "alternate"),
            fields.get("link"),
        )
        url = fields["loc"].text if "loc" in fields else ""
        if link is not None:
            url = link.get("href") or link.text or url
        published = next((fields[k].text for k in ("published", "pubDate") if k in fields), "")
        yield {
            "url": (url or "").strip(),
            "title": fields["title"].text or "" if "title" in fields else "",
            "date": date_value(published),
            "summary": fields["summary"].text or "" if "summary" in fields else "",
            "affiliations": " ".join(node.text or "" for node in item.findall(".//{*}affiliation")),
            "lastmod": date_value(fields["lastmod"].text) if "lastmod" in fields else "",
        }


def arxiv_key(url):
    parsed = urlsplit(url)
    match = ARXIV.search(url) if parsed.hostname in {"arxiv.org", "export.arxiv.org"} else None
    if not match:
        return None
    return match[1], int(match[2] or "1")


class Arxiv:
    def __init__(self):
        self.last_query = 0.0

    def query(self, **parameters):
        wait = 3 - (time.monotonic() - self.last_query)
        if wait > 0:
            time.sleep(wait)
        self.last_query = time.monotonic()
        return list(xml_entries(body_text(ARXIV_API + "?" + urlencode(parameters))))
