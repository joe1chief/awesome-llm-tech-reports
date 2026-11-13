import json

import pytest

from report_sources import Page, xml_entries
from report_watch import SOURCES, official_model


@pytest.mark.parametrize('name', [
    'Qwen3-235B-A22B',
    'Qwen3.8-2.4T-A95B',
    'Qwen3-Coder-480B-A35B-Instruct',
    'Qwen3-Next-80B-A3B-Thinking',
    'Qwen3.5-Plus',
    'Qwen4-Max-Preview',
    'Qwen4-Stage1',
])
def test_qwen_names_are_not_truncated(name):
    settings = json.loads(SOURCES.read_text())['alibaba_qwen']
    assert official_model(f'Introducing {name}: our new model', settings) == name


@pytest.mark.parametrize('suffix', ['-UnknownSuffix', '.Unknown'])
def test_unsupported_qwen_suffix_is_not_silently_a_different_model(suffix):
    settings = json.loads(SOURCES.read_text())['alibaba_qwen']
    assert official_model('Introducing Qwen3' + suffix, settings) == ''


@pytest.mark.parametrize('markup', [
    '<p>Updated November 10, 2026</p>',
    '<p>Last modified November 10, 2026</p>',
    '<p>Updated <span>November 10, 2026</span></p>',
    '<time itemprop="dateModified" datetime="2026-11-10">November 10, 2026</time>',
    '<time class="updated" datetime="2026-11-10">November 10, 2026</time>',
    '<div class="last-modified"><span>November 10, 2026</span></div>',
    '<time datetime="2026-11-10">Updated November 10, 2026</time>',
    '<p>更新于 2026-11-10</p>',
])
def test_update_date_is_not_a_release_date(markup):
    assert Page('<h1>Qwen4</h1>' + markup).date == ''
    assert Page('<h1>Qwen4</h1>' + markup + '<p>Published October 1, 2026</p>').date == '2026-10-01'


@pytest.mark.parametrize('markup', [
    '<time datetime="2026-10-01">October 1, 2026</time>',
    '<time itemprop="datePublished" datetime="2026-10-01">October 1, 2026</time>',
    '<p>October 1, 2026</p>',
    '<p>Published October 1, 2026</p>',
])
def test_publication_date_fallbacks_remain_supported(markup):
    assert Page('<h1>Qwen4</h1>' + markup).date == '2026-10-01'


def test_sitemap_modified_date_does_not_become_publication_date():
    entry, = xml_entries('<urlset><url><loc>https://qwen.ai/release</loc><lastmod>2026-11-10</lastmod></url></urlset>')
    assert entry['date'] == ''
    assert entry['lastmod'] == '2026-11-10'


def test_update_only_article_is_not_published_as_a_release(monkeypatch):
    import report_watch

    settings = json.loads(SOURCES.read_text())['alibaba_qwen']
    settings = {**settings, 'official': 'https://qwenlm.github.io/blog/'}
    url = 'https://qwenlm.github.io/blog/qwen3-coder/'
    monkeypatch.setattr(report_watch, 'official_entries', lambda *_: [
        {'url': url, 'title': 'Introducing Qwen3-Coder-480B-A35B', 'date': '', 'lastmod': '2026-11-10'},
    ])
    monkeypatch.setattr(report_watch, 'body_text', lambda *_:
        '<h1>Introducing Qwen3-Coder-480B-A35B</h1><p>Updated November 10, 2026</p>')
    monkeypatch.setattr(report_watch, 'try_report', lambda *_args, **_kwargs: [])
    rows, _, _, _ = report_watch.scan_official(
        'alibaba_qwen', settings, {}, {}, {}, '2026-07-01', '2026-11-13', 12, None,
    )
    assert rows == []


def test_time_outside_article_context_is_not_a_release_date():
    assert Page('<header><time datetime="2026-11-10">November 10, 2026</time></header><h1>Qwen4</h1>').date == ''


@pytest.mark.parametrize('punctuation', ['.', '. This is new.', ':', '!', '?'])
def test_qwen_sentence_punctuation_is_not_part_of_the_model(punctuation):
    settings = json.loads(SOURCES.read_text())['alibaba_qwen']
    assert official_model('Introducing Qwen4' + punctuation, settings) == 'Qwen4'
