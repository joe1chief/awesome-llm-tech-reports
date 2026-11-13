from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

TERM_INDEX = Path("data/report-text-terms.json")
VERSION = 2
WORD = re.compile(r"[a-z][a-z0-9]*")
TERM_NORMALIZATION = re.compile(r"[^a-z0-9\u3400-\u9fff]+")
HEADS = set("""
alignment attention batching cache compression context decoding distillation embedding encoding
evaluation fusion generation gradients grounding inference optimization parallelism parsing
prediction quantization reasoning retrieval routing sampling scaling segmentation sparsity
tokenization training tuning
""".split())
MODIFIERS = set("""
activation adaptive agentic asynchronous autoregressive beam block blockwise cache chain chunked
contrastive context continuous cross curriculum data decoding deep dense diffusion distributed
dynamic elastic expert fine flash fp4 fp8 gated gradient group grouped hierarchical hybrid image
inference instruction int4 int8 iterative key latent layer linear long low masked memory mixed
modal model mixture multi multimodal native offload offline online parallel parameter pipeline
policy position positional post precision preference prefix prompt query recurrent reinforcement
reward rotary self sequence sliding sparse speculative streaming supervised tensor text token
tool value video vision weight window
""".split())
DISPLAY = {"fp4": "FP4", "fp8": "FP8", "int4": "INT4", "int8": "INT8", "kv": "KV", "moe": "MoE"}
BODY_SOURCES = {"archive PDF", "source PDF", "model card", "source page"}
GENERIC_MODIFIERS = {"data", "deep", "long", "low", "modal", "model", "multi", "native", "parameter"}
GENERIC_PAIRS = {("token", "context"), ("context", "reasoning")}


def text_key(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return TERM_NORMALIZATION.sub(" ", text).strip()


def terms_for_text(body, glossary):
    normalized = text_key(body)
    aliases = {text_key(alias): term for term, forms in glossary.items() for alias in [term, *forms]}
    terms = {
        term for alias, term in aliases.items()
        if alias and (
            alias in normalized if re.search(r"[\u3400-\u9fff]", alias)
            else re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized)
        )
    }
    for line in re.split(r"[.!?;:。；：！？\n]", body):
        tokens = WORD.findall(text_key(line))
        for index, token in enumerate(tokens):
            if token not in HEADS:
                continue
            for length in (2, 3):
                phrase = tokens[max(0, index + 1 - length):index + 1]
                if len(phrase) != length or not all(word in MODIFIERS for word in phrase[:-1]):
                    continue
                if phrase[-2] in GENERIC_MODIFIERS or tuple(phrase[-2:]) in GENERIC_PAIRS:
                    continue
                key = " ".join(phrase)
                terms.add(aliases.get(key, " ".join(DISPLAY.get(word, word.title()) for word in phrase)))
    return sorted(terms, key=str.casefold)


def document_key(report):
    return hashlib.sha256(document_id(report).encode()).hexdigest()


def document_id(report):
    url = urlsplit(report["url"])
    if url.hostname == "arxiv.org" and (match := re.fullmatch(r"/(?:abs|html|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?/?", url.path)):
        return f"arxiv:{match[1]}"
    return urlunsplit(url._replace(fragment=""))


def document_revision(report):
    return hashlib.sha256(json.dumps([
        report["url"], report.get("revision"), report.get("file"),
    ]).encode()).hexdigest()


def glossary_revision(glossary):
    return hashlib.sha256(json.dumps(glossary, sort_keys=True).encode()).hexdigest()


def latest_year(rows):
    return max(event["released_on"][:4] for row in rows for event in [row, *row.get("release_events", [])])


def yearly_documents(rows, year):
    documents = {}
    for row in rows:
        if row["released_on"].startswith(year) and (report := row.get("report")):
            key = document_key(report)
            previous = (documents.get(key) or {}).get("report", {})
            rank = (bool(report.get("file")), len(report.get("highlights", "")), report["url"])
            old_rank = (bool(previous.get("file")), len(previous.get("highlights", "")), previous.get("url", ""))
            if rank > old_rank:
                documents[key] = row
    return documents


def term_index(root, glossary):
    path = root / TERM_INDEX
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["version"] == VERSION and data.get("glossary") == glossary_revision(glossary):
            return data["documents"]
    return {}


def word_cloud_data(rows, glossary, index):
    counts = Counter()
    coverage = Counter()
    for key, row in yearly_documents(rows, latest_year(rows)).items():
        evidence = index.get(key, {})
        report = row["report"]
        if evidence.get("source") in BODY_SOURCES and evidence.get("revision") == document_revision(report):
            coverage[evidence["source"]] += 1
            counts.update(set(evidence["terms"]))
        elif summary := report.get("highlights"):
            coverage["catalog excerpt"] += 1
            counts.update(terms_for_text(summary, glossary))
        else:
            coverage["no text"] += 1
    counts = {term: count for term, count in counts.items() if count >= 2 or term in glossary}
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].casefold())), dict(sorted(coverage.items()))
