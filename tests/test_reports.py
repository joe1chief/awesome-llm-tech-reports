from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError

import pytest

import report_sources
import report_watch
from parse_readme import parse_models
from report_catalog import ROOT, portal_models, read_catalog, validate
from report_parameters import configure_parameters, declared_total, total_parameters
from report_resolution import resolve_report
from report_store import Store
from report_visuals import build_visuals, frequencies

SETTINGS = {
    "org": "Alibaba",
    "hub": "Qwen",
    "official": "https://qwenlm.github.io/blog/",
    "hosts": ["qwenlm.github.io", "qwen.ai"],
    "model_pattern": r"Qwen\d+",
    "group_sizes": True,
}
DATES = ("2026-07-01", "2026-11-12")
PAPER = {
    "url": "https://arxiv.org/abs/2505.09388v2",
    "title": "Qwen3 Technical Report",
    "date": "2025-05-14",
    "summary": "The Qwen model uses a mixture of experts and long-context reasoning.",
    "affiliations": "Alibaba",
}


class ArxivFixture:
    def __init__(self, entries):
        self.entries = entries
        self.calls = []

    def query(self, **parameters):
        self.calls.append(parameters)
        return self.entries


def hub_row(name, revision="a"):
    return {
        "id": "Qwen/" + name,
        "sha": revision * 40,
        "createdAt": "2026-11-10T06:00:00Z",
        "lastModified": "2026-11-12T02:00:00Z",
        "modified": "2026-11-12",
    }


def release(name="Qwen3"):
    return {
        "key": "alibaba_qwen/qwen3",
        "id": "alibaba_qwen--qwen3",
        "org": "Alibaba",
        "model": name,
        "released_on": "2026-11-10",
        "release_url": "https://huggingface.co/Qwen/Qwen3-8B",
        "hub_revision": "a" * 40,
        "report": None,
    }


def test_historical_catalog_keeps_existing_portal_rows():
    rows = read_catalog()
    validate(rows, check_files=False)
    indexed = {model["id"]: model for model in portal_models(rows)["models"]}
    legacy = [row for row in rows if row.get("report") and row["report"]["kind"] == "archive"]
    assert legacy
    for row in legacy:
        assert indexed[row["id"]]["file"] == row["report"]["file"]
        assert indexed[row["id"]]["link"] == row["report"]["url"]
    assert len(parse_models(ROOT / "README.md")) == len(indexed)


def test_hub_pagination_and_cutoff(monkeypatch):
    current = hub_row("Qwen3-8B")
    older = dict(hub_row("Qwen2-8B"), lastModified="2026-01-01")
    replies = iter(
        [
            (
                json.dumps([current]).encode(),
                {"Link": '<https://huggingface.co/api/models?cursor=2>; rel="next"'},
            ),
            (json.dumps([older]).encode(), {}),
        ]
    )
    calls = []

    def fake_fetch(url, hosts):
        calls.append((url, hosts))
        return next(replies)

    monkeypatch.setattr(report_sources, "fetch", fake_fetch)
    assert list(report_sources.model_pages("Qwen", "2026-07-01")) == [current]
    assert len(calls) == 2
    assert "sort=lastModified" in calls[0][0]
    assert "expand%5B%5D=sha" in calls[0][0]


def test_direct_card_citation_prefers_the_matching_report():
    arxiv = ArxivFixture(
        [
            {**PAPER, "url": "https://arxiv.org/abs/2309.00071", "title": "YaRN: Context Window Extension"},
            PAPER,
        ]
    )
    card = "# Qwen3\n[Technical Report](https://arxiv.org/abs/2505.09388)\nhttps://arxiv.org/abs/2309.00071"
    report, errors = resolve_report(release(), card, SETTINGS, arxiv)
    assert report["id"] == "arxiv:2505.09388"
    assert report["revision"] == "2"
    assert report["rank"] == 0
    assert not errors
    assert "id_list" in arxiv.calls[0]


def test_arxiv_search_requires_affiliation():
    arxiv = ArxivFixture([{**PAPER, "affiliations": "Other Organization"}])
    report, _ = resolve_report(release(), "# Qwen3", SETTINGS, arxiv)
    assert report is None


def test_hub_scope_checks_task_and_auxiliary_role_before_fetching_cards(monkeypatch):
    def card(url, revision, gated):
        fetched.append(url.rsplit("/", 1)[-1])
        return "# " + fetched[-1]

    fetched = []
    monkeypatch.setattr(report_watch, "hf_card", card)
    monkeypatch.setattr(report_watch, "model_pages", lambda *_: [
        {**hub_row("Qwen4-Embed"), "pipeline_tag": "feature-extraction"},
        {**hub_row("Qwen4-Stage1"), "pipeline_tag": "text-generation", "tags": ["draft-model"]},
        {**hub_row("Qwen4-Embedding"), "pipeline_tag": "text-generation"},
        hub_row("UnknownExperiment"),
        hub_row("Qwen4-Max"),
        {**hub_row("NewImageGenerator"), "pipeline_tag": "text-to-image"},
    ])
    rows, _, _, _ = report_watch.scan_hub(
        "alibaba_qwen", SETTINGS, {}, {}, {}, *DATES, 12, ArxivFixture([])
    )
    assert fetched == ["Qwen4-Max", "NewImageGenerator"]
    assert {row["model"] for row in rows} == set(fetched)
    assert rows[1]["hub_task"] == "text-to-image"


def test_total_parameters_uses_verified_totals_and_ignores_active_sizes_and_context_lengths():
    settings = json.loads(report_watch.SOURCES.read_text())
    configure_parameters(settings, report_watch.SOURCES.with_name("report-parameters.json"))
    assert total_parameters("Gemma 3 270M", settings["google"]) == 270_000_000
    assert total_parameters("Ming-3.0-audio-tiny", settings["inclusionai"]) == 9_300_000_000
    assert total_parameters("Qwen2.5-1M", settings["alibaba_qwen"]) is None
    assert total_parameters("Example-600M", {}) == 600_000_000
    assert total_parameters("Example-128M-context", {}) is None
    assert total_parameters("Example-2B-Active", {}) is None
    assert total_parameters("Example-9B-A2B", {}) == 9_000_000_000
    assert total_parameters("Example-NVFP4", {}, safetensors={"total": 500_000_000}) is None
    assert total_parameters("JustRL-II-base-model", settings["openbmb"]) == 2_000_000_000


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("**VoiceFlow** is a 1.5B foundation model for speech generation.", 1_500_000_000),
        ("| Parameters | 9.3B total parameters, 2.7B activated per step |", 9_300_000_000),
        ("| Total Parameters | 9.3B |", 9_300_000_000),
        ("**Total Parameters:** 3B\n**Active Parameters:** 400M", 3_000_000_000),
        ("Total Parameters: 4.38B; the shared embedding is excluded.", 4_380_000_000),
        ("VoiceFlow is a 600M-parameter model.", 600_000_000),
        ("VoiceFlow is a 128K context model trained on 1.5B tokens.", None),
        ("The related model TinySpeech is a 1.5B foundation model.", None),
        ("VoiceFlow uses a 300M-parameter audio encoder.", None),
        ("VoiceFlow has 300M parameters in the audio encoder.", None),
        ("| Total parameters | 2B | 8B |", None),
        ("| Prior architecture | Denoiser (~675M parameters) |", None),
        ("Total parameters: 2B\nTotal parameters: 8B", None),
    ],
)
def test_card_parameter_count_requires_a_model_total(description, expected):
    assert declared_total("VoiceFlow", description) == expected


def test_hub_scan_rejects_unnamed_small_models_and_drafts_before_report_lookup(monkeypatch):
    config = {**SETTINGS, "minimum_total_parameters": 3_000_000_000}
    repo_names = ("VoiceFlow", "BigModel-50B-A2B-DFlash2", "AudioMoE")
    cards = {
        "VoiceFlow": "**VoiceFlow** is a 1.5B foundation model for speech generation.",
        "AudioMoE": "# AudioMoE\n\n| Parameters | 9.3B total parameters, 2.7B activated per step |",
    }
    fetched = []

    def card(url, revision, gated):
        name = url.rsplit("/", 1)[-1]
        fetched.append(name)
        return cards[name]

    monkeypatch.setattr(report_watch, "hf_card", card)
    monkeypatch.setattr(
        report_watch, "model_pages",
        lambda *_: [{**hub_row(name), "pipeline_tag": "text-to-speech"} for name in repo_names],
    )
    arxiv = ArxivFixture([])
    rows, _, errors, _ = report_watch.scan_hub("alibaba_qwen", config, {}, {}, {}, *DATES, 12, arxiv)
    assert fetched == ["VoiceFlow", "AudioMoE"]
    assert [row["model"] for row in rows] == ["AudioMoE"]
    assert rows[0]["total_parameters"] == 9_300_000_000
    assert len(arxiv.calls) == 1 and not errors


def test_official_release_recognizes_hydrogen_and_classifies_the_pdf_as_a_model_card(monkeypatch):
    import report_resolution

    google = json.loads(report_watch.SOURCES.read_text())["google"]
    title = "Introducing Gemini 4 Hydrogen for Agentic Workflows"
    link = "https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/"
    card = "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-4-Hydrogen-Model-Card.pdf"
    assert report_watch.official_model(title, google, link) == "Gemini 4 Hydrogen"
    assert not report_watch.model_in_scope("Gemini 4", google)
    monkeypatch.setattr(report_resolution, "fetch", lambda *_: (b"%PDF-1.7\n%%EOF", {}))
    report = report_resolution.vendor_document(card, "Model Card", "Gemini 4 Hydrogen", set(google["hosts"]), explicit=True)
    assert report["kind"] == "model card"


def test_official_only_release_retries_apply_new_parameter_evidence(monkeypatch):
    vendor = "alibaba_qwen"
    config = {**SETTINGS, "hub": "", "official": "", "minimum_total_parameters": 3_000_000_000}
    link = "https://qwen.ai/releases/voiceflow"
    pending = {
        **release("VoiceFlow"),
        "release_url": link,
        "official_url": link,
        "retry_on": DATES[1],
    }
    monkeypatch.setattr(
        report_watch, "body_text",
        lambda *_: "<p>VoiceFlow is a 1.5B foundation model for speech generation.</p>",
    )
    arxiv = ArxivFixture([])
    with Store(":memory:").lock() as store:
        rows, _ = report_watch.scan_reports(
            store, [pending], {vendor: config}, {}, [vendor], *DATES, 12, arxiv=arxiv,
        )
    assert rows[0]["total_parameters"] == 1_500_000_000
    assert report_watch.project(rows, {vendor: config}) == []
    assert arxiv.calls == []


def test_hub_size_filter_hides_a_known_release_even_when_its_revision_was_seen(monkeypatch):
    config = {**SETTINGS, "minimum_total_parameters": 3_000_000_000}
    url = "https://huggingface.co/Qwen/UnnamedSmall"
    old = {
        **release("UnnamedSmall"), "key": "alibaba_qwen/unnamedsmall",
        "release_url": url, "hub_url": url,
    }
    small = {
        **hub_row("UnnamedSmall"), "pipeline_tag": "text-generation",
        "safetensors": {"parameters": {"BF16": 900_000_000}, "total": 900_000_000},
    }
    large = {**hub_row("NewImageGenerator"), "pipeline_tag": "text-to-image",
             "safetensors": {"parameters": {"BF16": 3_000_000_000}, "total": 3_000_000_000}}
    fetched = []

    def card(url, revision, gated):
        name = url.rsplit("/", 1)[-1]
        fetched.append(name)
        return "# " + name

    monkeypatch.setattr(report_watch, "model_pages", lambda *_: [small, large])
    monkeypatch.setattr(report_watch, "hf_card", card)
    rows, _, _, _ = report_watch.scan_hub(
        "alibaba_qwen", config, {}, {old["key"]: old}, {"seen": {small["id"]: small["sha"]}},
        *DATES, 12, ArxivFixture([]),
    )
    assert fetched == ["NewImageGenerator"]
    assert rows[0]["total_parameters"] == 900_000_000
    assert [row["model"] for row in report_watch.project(rows, {"alibaba_qwen": config})] == fetched


def test_size_filtered_archive_can_be_restored_from_collection_state():
    vendor = "alibaba_qwen"
    config = {**SETTINGS, "minimum_total_parameters": 3_000_000_000}
    small = {
        **release("Qwen3-2B"),
        "report": {
            "id": PAPER["url"], "kind": "archive", "url": PAPER["url"],
            "file": "2026/alibaba_qwen/2026-11_qwen3-2b.pdf",
        },
    }
    with Store(":memory:").lock() as store:
        raw, _ = report_watch.scan_reports(
            store, [small], {vendor: config}, {}, [vendor], *DATES, 12, backfill_only=True,
        )
        assert report_watch.project(raw, {vendor: config}) == []
        config["minimum_total_parameters"] = 2_000_000_000
        raw, _ = report_watch.scan_reports(
            store, [], {vendor: config}, {}, [vendor], *DATES, 12, backfill_only=True,
        )
    assert report_watch.project(raw, {vendor: config})[0]["report"]["file"] == small["report"]["file"]


def test_public_projection_applies_scope_to_already_collected_models():
    settings = json.loads(report_watch.SOURCES.read_text())
    out_of_scope = {
        **release("SamudrACE-E3SMv3"),
        "key": "allenai/samudrace-e3smv3",
        "id": "allenai--samudrace-e3smv3",
        "org": "Allen AI",
        "release_url": "https://huggingface.co/allenai/SamudrACE-E3SMv3",
        "report": {
            "id": "samudrace",
            "kind": "technical report",
            "url": "https://huggingface.co/allenai/SamudrACE-E3SMv3",
        },
    }
    primary = {
        **release("Qwen3"),
        "report": {"id": PAPER["url"], "kind": "technical report", "url": PAPER["url"]},
    }
    published = report_watch.project([out_of_scope, primary], settings)
    assert [row["model"] for row in published] == ["Qwen3"]
    assert [model["model"] for model in portal_models(published)["models"]] == ["Qwen3"]
    visuals, _ = build_visuals(published, {}, "https://example.com")
    assert "SamudrACE" not in visuals[Path("docs/timeline.html")]


def test_repeat_poll_dedupes_variants_and_keeps_one_report(monkeypatch):
    vendor = "alibaba_qwen"
    settings = {vendor: {**SETTINGS, "official": ""}}
    arxiv = ArxivFixture([PAPER])
    monkeypatch.setattr(
        report_watch,
        "model_pages",
        lambda *_: [
            hub_row("Qwen3-8B"),
            hub_row("Qwen3-32B", "b"),
            hub_row("Qwen3-8B-AWQ", "c"),
        ],
    )
    monkeypatch.setattr(report_watch, "hf_card", lambda *_: "# Qwen3\nhttps://arxiv.org/abs/2505.09388")
    store = Store(":memory:")
    with store.lock():
        initial, logs = report_watch.scan_reports(store, [], settings, {}, [vendor], *DATES, 12, arxiv=arxiv)
        repeated, _ = report_watch.scan_reports(store, [], settings, {}, [vendor], *DATES, 12, arxiv=arxiv)
        reports = store.execute("SELECT count(*) FROM report_versions").fetchone()[0]
        assert len(initial) == len(repeated) == 2
        assert reports == 1
        assert len(report_watch.project(initial, settings)) == 1
        assert initial[0]["key"] == "alibaba_qwen/qwen3"
        assert initial == repeated
        assert logs[0]["report_lookup_errors"] == 0


def test_failed_page_leaves_cursor_unchanged(monkeypatch):
    vendor = "alibaba_qwen"
    settings = {vendor: {**SETTINGS, "official": ""}}

    def partial(*args):
        yield hub_row("Qwen3-8B")
        raise ValueError("truncated list")

    monkeypatch.setattr(report_watch, "model_pages", partial)
    store = Store(":memory:")
    with store.lock():
        store.save([], vendor + "/hub", {"watermark": "2026-10-10"})
        rows, logs = report_watch.scan_reports(store, [], settings, {}, [vendor], *DATES, 12)
        assert rows == []
        assert logs[0]["error"] == "ValueError"
        assert store.source(vendor + "/hub")["watermark"] == "2026-10-10"


def test_pending_release_can_receive_report_without_new_revision(monkeypatch):
    vendor = "alibaba_qwen"
    settings = {vendor: {**SETTINGS, "official": ""}}
    monkeypatch.setattr(report_watch, "model_pages", lambda *_: [hub_row("Qwen3-8B")])
    card = {"body": "# Qwen3\nhttps://arxiv.org/abs/2505.09388"}
    monkeypatch.setattr(report_watch, "hf_card", lambda *_: card["body"])
    arxiv = ArxivFixture([])
    store = Store(":memory:")
    with store.lock():
        pending, _ = report_watch.scan_reports(store, [], settings, {}, [vendor], *DATES, 12, arxiv=arxiv)
        assert pending[0]["report"] is None
        arxiv.entries = [PAPER]
        caught, _ = report_watch.scan_reports(
            store, [], settings, {}, [vendor], DATES[0], "2026-11-13", 12, arxiv=arxiv
        )
        assert caught[0]["report"]["id"] == "arxiv:2505.09388"
        assert pending[0]["key"] == caught[0]["key"]


def test_official_announcements_cover_closed_releases(monkeypatch):
    settings = {
        **SETTINGS,
        "org": "Anthropic",
        "hub": "",
        "hosts": ["www.anthropic.com"],
        "official": "https://www.anthropic.com/sitemap.xml",
        "model_pattern": r"Claude Sonnet \d+",
    }
    article = "https://www.anthropic.com/news/introducing-claude-sonnet-5"
    monkeypatch.setattr(
        report_watch,
        "official_entries",
        lambda *_: [
            {"url": article, "title": "Introducing Claude Sonnet 5", "date": "2026-11-10"},
        ],
    )
    body = (
        "<title>Introducing Claude Sonnet 5</title><p>The model uses a new reasoning architecture. "
        "We release evaluations of instruction following and agent capabilities across technical benchmarks.</p>"
    )
    monkeypatch.setattr(report_watch, "body_text", lambda *_: body)
    rows, _, errors, _ = report_watch.scan_official(
        "anthropic", settings, {}, {}, {}, *DATES, 12, ArxivFixture([])
    )
    assert not errors
    assert rows[0]["released_on"] == "2026-11-10"
    assert rows[0]["report"]["kind"] == "official technical page"


def test_official_sources_save_dated_cards_when_a_source_or_article_fails(monkeypatch):
    official = "https://deploymentsafety.openai.com"
    blocked = "https://openai.com/news/rss.xml"
    card = official + "/gpt-6-1-terra"
    cyber = official + "/gpt-6-cyber"
    config = json.loads(report_watch.SOURCES.read_text())["openai"]
    config = {**config, "hub": "", "official": [blocked, official]}
    pages = {
        official: (
            '<h1>Deployment safety</h1><a href="/gpt-6-cyber">Nov 05, 2026 <b>GPT‑6 Cyber</b></a>'
            '<a href="/gpt-6-1-terra"><time>Oct 26, 2026</time><b>GPT‑6.1 Terra</b></a>'
        ),
        card: (
            '<title>Deployment Safety Hub</title><h1>GPT‑6.1 Terra</h1>'
            '<p>Published October 26, 2026</p><p>The model card records training data, benchmark '
            'evaluations and limitations across supported modalities and model capabilities.</p>'
        ),
    }

    def fetch_page(url, hosts):
        if url in {blocked, cyber}:
            raise HTTPError(url, 403, "Forbidden", {}, None)
        return pages[url]

    monkeypatch.setattr(report_watch, "body_text", fetch_page)
    with Store(":memory:").lock() as store:
        rows, logs = report_watch.scan_reports(
            store, [], {"openai": config}, {}, ["openai"], *DATES, 12, arxiv=ArxivFixture([])
        )
        assert logs[0]["error"] == "HTTP 403"
        assert logs[1]["deferred"] == 1
        assert store.source(logs[1]["source"])["seen"] == {
            card: "2026-10-26", cyber: {"stamp": "2026-11-05", "retry_on": "2026-11-13"},
        }
    assert [(row["model"], row["released_on"]) for row in rows] == [("GPT-6.1 Terra", "2026-10-26")]
    assert rows[0]["report"]["url"] == card
    assert report_watch.official_model(
        "Addendum to GPT‑6 Astra System Card: GPT‑6.1 Terra", config, "/gpt-6-1-terra"
    ) == "GPT-6.1 Terra"


def test_followup_availability_is_a_separate_dated_event(monkeypatch):
    home = "https://blog.google/releases/"
    initial = home + "introducing-gemini-4-carbon/"
    availability = home + "gemini-4-carbon-now-available/"
    pages = {
        home: (
            f'<a href="{availability}"><time>Nov 10, 2026</time>Gemini 4 Carbon is now available</a>'
            f'<a href="{initial}"><time>Oct 28, 2026</time>Introducing Gemini 4 Carbon</a>'
        ),
        availability: "<h1>Gemini 4 Carbon is now available</h1><p>Published November 10, 2026</p>",
        initial: "<h1>Introducing Gemini 4 Carbon</h1><time datetime='2026-10-28'>October 28, 2026</time>",
    }
    config = {
        **SETTINGS, "org": "Google", "hub": "", "official": home, "hosts": ["blog.google"],
        "model_pattern": r"Gemini 4 Carbon",
    }
    monkeypatch.setattr(report_watch, "body_text", lambda url, _: pages[url])
    rows, _, _, _ = report_watch.scan_official(
        "google", config, {}, {}, {}, *DATES, 12, ArxivFixture([])
    )
    rows = report_watch.project(rows, {"google": config})
    validate(rows, check_files=False)
    assert len(rows) == 1
    assert rows[0]["released_on"] == "2026-10-28"
    assert rows[0]["release_events"] == [{
        "released_on": "2026-11-10", "release_url": availability, "forms": ["General availability"],
    }]
    outputs, _ = build_visuals(rows, {}, "https://example.com")
    timeline = outputs[Path("docs/timeline.html")]
    assert initial in timeline and availability in timeline
    assert timeline.count(">Gemini 4 Carbon</a>") == 2


def test_verified_backfill_is_idempotent_without_polling(monkeypatch):
    def unexpected_fetch(*args):
        pytest.fail(f"Unexpected source fetch: {args}")

    monkeypatch.setattr(report_watch, "body_text", unexpected_fetch)
    monkeypatch.setattr(report_watch, "model_pages", unexpected_fetch)
    vendor = "alibaba_qwen"
    evidence = {
        vendor: [{
            "model": "Qwen4-Max Preview", "released_on": "2026-11-11",
            "release_url": "https://qwen.ai/blog?qwen4-max",
            "forms": ["Preview"],
        }],
    }
    settings = {vendor: SETTINGS}
    with Store(":memory:").lock() as store:
        rows, first = report_watch.scan_reports(
            store, [], settings, {}, [vendor], *DATES, 12, backfill=evidence, backfill_only=True
        )
        again, second = report_watch.scan_reports(
            store, [], settings, {}, [vendor], *DATES, 12, backfill=evidence, backfill_only=True
        )
    assert first[0]["records"] == 1 and second[0]["records"] == 0
    assert again == rows and rows[0]["report"] is None
    assert rows[0]["retry_on"] == DATES[1]


def test_configured_backfill_projects_a_valid_catalog():
    settings = json.loads(report_watch.SOURCES.read_text())
    backfill = json.loads(report_watch.SOURCES.with_name("report-backfill.json").read_text())
    aliases = json.loads(report_watch.ALIASES.read_text())
    with Store(":memory:").lock() as store:
        rows, _ = report_watch.scan_reports(
            store, read_catalog(), settings, aliases, list(settings), *DATES, 12,
            backfill=backfill, backfill_only=True,
        )
    releases = report_watch.project(rows, settings)
    validate(releases, check_files=False)
    by_key = {row["key"]: row for row in releases}
    assert by_key["openai/gpt-6-cyber"]["report"]["kind"] == "system card"
    assert by_key["google/gemini-4-carbon"]["release_events"][0]["released_on"] == "2026-11-10"
    assert by_key["stepfun/step-5-preview"]["released_on"] == "2026-09-20"


def test_public_assets_share_date_and_escape_external_text():
    row = release("Qwen3 <script> & Test")
    row["report"] = {
        "url": "https://arxiv.org/abs/2505.09388v2",
        "highlights": "MoE, mixture-of-experts, and MoE",
    }
    glossary = {"MoE": ["MoE", "mixture-of-experts"]}
    outputs, section = build_visuals([row], glossary, "https://example.com")
    assert frequencies([row], glossary) == [("MoE", 1)]
    assert "2026" in section
    for path, content in outputs.items():
        if path.suffix == ".svg":
            ET.fromstring(content)
        assert "<script>" not in content
    assert outputs[Path("docs/timeline.html")].count("2026-11-10") == 1
    assert build_visuals([row], glossary, "https://example.com") == (outputs, section)


def test_cross_host_pagination_rejected():
    with pytest.raises(ValueError, match="outside configured"):
        report_sources.require_host("https://huggingface.co.example.org/api/models", {"huggingface.co"})


def test_hub_pdf_uses_pinned_resolve_url(monkeypatch):
    import report_resolution

    expected = "https://huggingface.co/Qwen/Qwen3-8B/resolve/" + "a" * 40 + "/Qwen_Tech_Report.pdf"
    requested = []

    def fetch_pdf(url, hosts, limit):
        requested.append(url)
        return b"%PDF-1.7\n%%EOF", {}

    monkeypatch.setattr(report_resolution, "fetch", fetch_pdf)
    card = '<a href="https://qwen.ai">Home</a>\n[Technical Report](Qwen_Tech_Report.pdf)'
    report, errors = resolve_report(release(), card, SETTINGS, ArxivFixture([]))
    assert not errors
    assert requested == [expected]
    assert report["pdf"] == expected
    assert "/blob/" + "a" * 40 in report["url"]


def test_own_arxiv_citation_can_have_a_different_title():
    model = "Unlimited-OCR-2"
    row = {**release(model), "release_url": "https://huggingface.co/baidu/Unlimited-OCR-2"}
    original = {**PAPER, "url": "https://arxiv.org/abs/2606.23050", "title": "Unlimited OCR Works"}
    paper = {**PAPER, "url": "https://arxiv.org/abs/2610.39308v2", "title": "Unlimited OCR Works 2"}
    body = (
        "The paper of **Unlimited OCR 2** is now available on [arXiv](https://arxiv.org/abs/2610.39308).\n"
        "Unlimited OCR 2 builds on the paper of [Unlimited OCR](https://arxiv.org/abs/2606.23050)."
    )
    arxiv = ArxivFixture([original, paper])
    report, _ = resolve_report(row, body, SETTINGS, arxiv)
    assert report["id"] == "arxiv:2610.39308"
    arxiv.entries = [original]
    report, _ = resolve_report(row, body, SETTINGS, arxiv)
    assert report is None


def test_atom_keeps_alternate_link_and_malformed_xml_is_recoverable():
    atom = (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Qwen3 Technical Report</title>'
        '<link href="https://arxiv.org/abs/2505.09388v2" rel="alternate"/>'
        '<link href="https://arxiv.org/pdf/2505.09388" rel="related"/>'
        '</entry></feed>'
    )
    entry, = report_sources.xml_entries(atom)
    assert entry["url"] == PAPER["url"]
    with pytest.raises(ValueError, match="malformed XML"):
        list(report_sources.xml_entries("<feed>"))


def test_hub_card_failure_does_not_block_the_next_repo(monkeypatch):
    blocked, good = hub_row("Qwen3-8B"), hub_row("Qwen4-8B")
    good.update(createdAt="2026-08-05", pipeline_tag="text-generation")
    calls = []

    def card(url, *_):
        calls.append(url)
        if url.endswith("Qwen3-8B"):
            raise HTTPError(url, 403, "Forbidden", None, None)
        return "# Qwen4"

    monkeypatch.setattr(report_watch, "model_pages", lambda *_: [blocked, good])
    monkeypatch.setattr(report_watch, "hf_card", card)
    settings = {**SETTINGS, "release_since": DATES[0]}
    rows, seen, errors, deferred = report_watch.scan_hub(
        "alibaba_qwen", settings, {}, {}, {}, "2026-11-10", DATES[1], 2, ArxivFixture([]),
    )
    assert [(row["model"], row["released_on"]) for row in rows] == [("Qwen4", "2026-08-05")]
    assert errors == ["HTTP 403"] and deferred == 1
    assert seen[blocked["id"]]["retry_on"] == "2026-11-13"
    rows, _, errors, deferred = report_watch.scan_hub(
        "alibaba_qwen", settings, {}, {}, {"seen": seen}, *DATES, 2, ArxivFixture([]),
    )
    assert len(calls) == 2 and not rows and not errors and deferred == 1


def test_weight_packages_share_one_release_and_keep_better_report():
    canonical = {**release("Example-27B"), "key": "example/example-27b",
                 "release_url": "https://huggingface.co/example/Example-27B"}
    quantized = {**canonical, "key": "other/example-27b-nvfp4", "model": "Example-27B-NVFP4",
                 "base_model": "example/example-27b"}
    report = {"kind": "technical report", "id": PAPER["url"], "url": PAPER["url"]}
    quantized["report"] = report
    bf16 = {**canonical, "key": "example/example-27b-bf16", "model": "Example-27B-BF16"}
    rows = report_watch.publishable_releases([bf16, quantized, canonical], {})
    assert rows == [{**canonical, "report": report}]
    assert report_watch.publishable_releases([quantized], {}) == [quantized]


def test_float_parameter_count_takes_precedence_over_nominal_name():
    tensors = {"total": 2_800_000_000, "parameters": {"BF16": 2_800_000_000}}
    assert total_parameters("Example-3B", {}, safetensors=tensors) == 2_800_000_000
    assert total_parameters("Example-3B-NVFP4", {}, safetensors=tensors) == 3_000_000_000
    assert total_parameters("Example-3B", {}, safetensors={"total": 2_800_000_000}) == 3_000_000_000


def test_monthly_overview_caps_display_without_dropping_events():
    rows = [{**release(f"Example {day}"), "released_on": f"2026-11-{day:02d}"} for day in range(1, 12)]
    outputs, section = build_visuals(rows, {}, "https://example.com")
    svg = outputs[Path("assets/diagrams/release-timeline-2026.svg")]
    full = outputs[Path("docs/timeline.html")]
    assert section.count("model release overview") == 1
    assert "+1 on the full timeline" in svg
    assert full.count('class="month"') == 12 and full.count("<article ") == 11
    assert outputs[Path("docs/assets/diagrams/technical-word-cloud.svg")] == outputs[
        Path("assets/diagrams/technical-word-cloud-2026.svg")
    ]


def test_official_system_card_can_redirect_to_pdf(monkeypatch):
    import report_resolution

    settings = {**SETTINGS, "hosts": ["www.anthropic.com"]}
    announcement = "https://www.anthropic.com/claude-sonnet"
    pdf = "https://www.anthropic.com/document/claude-sonnet-system-card"
    monkeypatch.setattr(report_resolution, "fetch", lambda *_: (b"%PDF-1.7\n%%EOF", {}))
    row = {**release("Claude Sonnet 5.5"), "release_url": announcement}
    report, _ = resolve_report(
        row,
        None,
        settings,
        ArxivFixture([]),
        official_body=f'<a href="{pdf}">System Card</a>',
    )
    assert report["kind"] == "system card"
    assert report["url"] == pdf


def test_cli_refresh_rebuilds_all_outputs_and_replays_idempotently(monkeypatch, tmp_path, capsys):
    import sys

    from report_catalog import CATALOG, build, save_catalog

    vendor = "alibaba_qwen"
    baseline = read_catalog()[:1]
    baseline[0]["report"].pop("file", None)
    save_catalog(baseline, tmp_path)
    (tmp_path / "README.md").write_text((ROOT / "README.md").read_text())
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "report-terms.json").write_text('{"MoE": ["mixture of experts"]}')
    sources = config_dir / "report-sources.json"
    sources.write_text(json.dumps({vendor: {**SETTINGS, "official": ""}}))
    monkeypatch.setattr(report_watch, "SOURCES", sources)
    monkeypatch.setattr(report_watch, "read_catalog", lambda: read_catalog(tmp_path))
    monkeypatch.setattr(report_watch, "build", lambda **kwargs: build(tmp_path, **kwargs))
    monkeypatch.setattr(report_watch, "Arxiv", lambda: ArxivFixture([PAPER]))
    monkeypatch.setattr(report_watch, "model_pages", lambda *_: [hub_row("Qwen3-8B")])
    monkeypatch.setattr(report_watch, "hf_card", lambda *_: "# Qwen3\nhttps://arxiv.org/abs/2505.09388")
    monkeypatch.delenv("REPORTS_DATABASE_URL", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report_watch.py",
            "--publish",
            "--sqlite",
            str(tmp_path / "watch.sqlite3"),
            "--since",
            DATES[0],
            "--until",
            DATES[1],
        ],
    )
    assert report_watch.main() == 0
    outputs = build(tmp_path, check=True)
    assert "Qwen3" in outputs[Path("README.md")]
    assert "Qwen3" in outputs[Path("docs/timeline.html")]
    assert json.loads(outputs[Path("docs/data/word-cloud.json")])["terms"]["MoE"] >= 1
    first_catalog = (tmp_path / CATALOG).read_bytes()
    capsys.readouterr()
    assert report_watch.main() == 0
    assert '"changes": []' in capsys.readouterr().out
    assert first_catalog == (tmp_path / CATALOG).read_bytes()
    assert build(tmp_path, check=True) == outputs
