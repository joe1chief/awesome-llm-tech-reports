import json
import xml.etree.ElementTree as ET
from datetime import date
from urllib.error import URLError

import report_wordcloud
from report_terms import document_key, terms_for_text, word_cloud_data
from report_visuals import CLOUD_LIMIT, wordcloud_svg


def test_extract_technical_terms_beyond_glossary():
    text = "采用混合专家架构。The report studies blockwise attention and speculative decoding. It uses blockwise attention."
    assert set(terms_for_text(text, {"MoE": ["混合专家"]})) >= {"MoE", "Blockwise Attention", "Speculative Decoding"}


def test_pdf_reader_includes_pages_after_the_abstract(monkeypatch):
    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class Reader:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        pages = [
            Page("Abstract\n" + "Some model evaluation results. " * 13),
            Page("Introduction"), Page("Architecture"), Page("Hierarchical attention improves long contexts."),
            Page("References\nSynthetic data is used by an unrelated paper."),
        ]

    monkeypatch.setattr(report_wordcloud, "PdfReader", lambda _: Reader())
    text = report_wordcloud.pdf_text(b"placeholder")
    assert "Hierarchical Attention" in terms_for_text(text, {})
    assert "Synthetic data" not in text


def test_model_card_and_html_readers_skip_non_document_text(monkeypatch, tmp_path):
    markdown = "---\ntags: cache compression\n---\n# Model card\nSliding window attention.\n"
    html = "<nav>Cache compression</nav><article><h2>Architecture</h2><p>Sliding window attention.</p></article>"
    report = {"url": "https://huggingface.co/org/model/blob/" + "a" * 40 + "/README.md"}
    calls = []

    def fetch(url, *_):
        calls.append(url)
        return markdown.encode(), {}

    monkeypatch.setattr(report_wordcloud, "fetch", fetch)
    body, source = report_wordcloud.read_source(report, tmp_path, {"huggingface.co"})
    assert "/raw/" in calls[0] and source == "model card"
    assert "cache compression" not in body.lower()
    assert "Sliding window attention" in body
    assert "Cache compression" not in report_wordcloud.plain_text(html, "html")


def test_revisions_deduplicate_documents_and_retry_with_excerpt(monkeypatch, tmp_path):
    configs = tmp_path / "configs"
    configs.mkdir()
    glossary = {"MoE": ["mixture of experts"]}
    (configs / "report-terms.json").write_text(json.dumps(glossary))
    (configs / "report-sources.json").write_text("{}")
    report = {"url": "https://arxiv.org/abs/2610.00000v1", "highlights": "Mixture of experts"}
    rows = [
        {"key": "example/model-a", "released_on": "2026-10-02", "report": report},
        {"key": "example/model-b", "released_on": "2026-10-03", "report": report},
    ]
    calls = []

    def read(*_):
        calls.append(True)
        return "Mixture of experts and low precision inference. " * 12, "source PDF"

    monkeypatch.setattr(report_wordcloud, "read_source", read)
    assert report_wordcloud.refresh_terms(tmp_path, rows, until=date(2026, 11, 12)) == 1
    assert report_wordcloud.refresh_terms(tmp_path, rows, until=date(2026, 11, 13)) == 1
    assert len(calls) == 1
    index = report_wordcloud.term_index(tmp_path, glossary)
    assert word_cloud_data(rows, glossary, index) == ([("MoE", 1)], {"source PDF": 1})
    report["url"] = report["url"].replace("v1", "v2")
    assert word_cloud_data(rows, glossary, index) == ([("MoE", 1)], {"catalog excerpt": 1})

    def unavailable(*_):
        raise URLError("unavailable")

    monkeypatch.setattr(report_wordcloud, "read_source", unavailable)
    assert report_wordcloud.refresh_terms(tmp_path, rows, until=date(2026, 11, 13)) == 0
    updated = report_wordcloud.term_index(tmp_path, glossary)
    assert updated[document_key(report)]["check_on"] == "2026-11-20"


def test_cloud_displays_more_than_the_old_layout_limit():
    counts = [(f"Technical phrase {index}", CLOUD_LIMIT - index) for index in range(CLOUD_LIMIT)]
    svg, displayed = wordcloud_svg("2026", counts, {"archive PDF": 20, "catalog excerpt": 3})
    assert len(displayed) == CLOUD_LIMIT
    assert displayed == wordcloud_svg("2026", counts, {"archive PDF": 20, "catalog excerpt": 3})[1]
    texts = {element.text for element in ET.fromstring(svg).iter("{http://www.w3.org/2000/svg}text")}
    assert set(displayed) <= texts
    assert any(text and "20 of 23 documents" in text for text in texts)
