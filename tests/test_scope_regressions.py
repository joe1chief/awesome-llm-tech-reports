import json
import sys

import pytest

import report_catalog
import report_watch
from report_store import Store
from test_reports import SETTINGS, DATES, ArxivFixture, hub_row, release


@pytest.mark.parametrize('metadata', [
    {'pipeline_tag': 'feature-extraction'},
    {'pipeline_tag': 'text-generation', 'tags': ['draft-model']},
])
def test_scope_state_survives_publish_and_recovers(monkeypatch, tmp_path, metadata):
    vendor = 'alibaba_qwen'
    settings = {vendor: {**SETTINGS, 'official': ''}}
    model = {**hub_row('Qwen4-Stage1'), **metadata}
    url = 'https://huggingface.co/' + model['id']
    old = {**release('Qwen4-Stage1'), 'key': vendor + '/qwen4-stage1', 'release_url': url}
    monkeypatch.setattr(report_watch, 'model_pages', lambda *_: [model])
    monkeypatch.setattr(report_watch, 'hf_card', lambda *_: pytest.fail('seen/rejected card fetched'))
    path = str(tmp_path / 'state.db')
    with Store(path).lock() as store:
        store.save([old], vendor + '/hub', {'seen': {model['id']: model['sha']}})
        rows, _ = report_watch.scan_reports(store, [old], settings, {}, [vendor], *DATES, 12, arxiv=ArxivFixture([]))
        assert report_watch.project(rows, settings) == []
    with Store(path).lock() as store:
        rows, _ = report_watch.scan_reports(store, [], settings, {}, [vendor], *DATES, 12, arxiv=ArxivFixture([]))
        assert report_watch.project(rows, settings) == []
        model.update(pipeline_tag='text-generation', tags=[])
        monkeypatch.setattr(report_watch, 'body_text', lambda *_: '{}')
        rows, _ = report_watch.scan_reports(store, [], settings, {}, [vendor], *DATES, 12, arxiv=ArxivFixture([]))
        assert [r['model'] for r in report_watch.project(rows, settings)] == [old['model']]


def test_rejected_derivative_does_not_hide_other_source(monkeypatch):
    old = release()
    model = {**hub_row('Qwen3-4B'), 'pipeline_tag': 'text-generation', 'tags': ['draft-model']}
    monkeypatch.setattr(report_watch, 'model_pages', lambda *_: [model])
    rows, *_ = report_watch.scan_hub('alibaba_qwen', SETTINGS, {}, {old['key']: old}, {}, *DATES, 12, ArxivFixture([]))
    assert rows == []
    assert report_watch.project([old], {'alibaba_qwen': SETTINGS})


@pytest.mark.parametrize('size', [1, 4])
def test_small_official_variant_preserves_larger_family(monkeypatch, size):
    settings = {**SETTINGS, 'minimum_total_parameters': 3_000_000_000,
                'model_pattern': r'Qwen\d+(?:-\d+B)?'}
    old = {**release(), 'total_parameters': 8_000_000_000}
    url = f'https://qwen.ai/releases/qwen3-{size}b'
    monkeypatch.setattr(report_watch, 'official_entries', lambda *_: [
        {'url': url, 'title': f'Introducing Qwen3-{size}B', 'date': '2026-11-11'}])
    monkeypatch.setattr(report_watch, 'body_text', lambda *_: f'<h1>Introducing Qwen3-{size}B</h1>')
    monkeypatch.setattr(report_watch, 'try_report', lambda *a, **kw: [])
    rows, *_ = report_watch.scan_official('alibaba_qwen', settings, {}, {old['key']: old}, {}, *DATES, 12, None)
    merged = {old['key']: old, **{r['key']: r for r in rows}}
    assert merged[old['key']]['total_parameters'] == 8_000_000_000
    assert report_watch.project(list(merged.values()), {'alibaba_qwen': settings})
    if size == 1:
        assert merged[old['key']] == old


def test_verified_total_reconsiders_cached_card_rejection(monkeypatch):
    config = {**SETTINGS, 'minimum_total_parameters': 3_000_000_000}
    model = {**hub_row('VoiceFlow'), 'pipeline_tag': 'text-to-speech'}
    monkeypatch.setattr(report_watch, 'model_pages', lambda *_: [model])
    monkeypatch.setattr(report_watch, 'hf_card', lambda *_: 'VoiceFlow is a 1.5B foundation model.')
    monkeypatch.setattr(report_watch, 'try_report', lambda *a, **kw: [])
    rows, seen, *_ = report_watch.scan_hub('alibaba_qwen', config, {}, {}, {}, *DATES, 12, None)
    assert rows == []
    assert seen[model['id']].endswith(':below-3000000000')
    config['verified_total_parameters'] = {'voiceflow': 4_000_000_000}
    rows, *_ = report_watch.scan_hub('alibaba_qwen', config, {}, {}, {'seen': seen}, *DATES, 12, None)
    assert len(rows) == 1
    assert rows[0]['total_parameters'] == 4_000_000_000


def test_publish_removes_rejected_from_all_generated_outputs(monkeypatch, tmp_path):
    vendor = 'alibaba_qwen'
    model = {**hub_row('Qwen4-Stage1'), 'pipeline_tag': 'text-generation', 'tags': ['draft-model']}
    old = {**release('Qwen4-Stage1'), 'key': vendor + '/qwen4-stage1',
           'release_url': 'https://huggingface.co/' + model['id']}
    keeper = {**release('Qwen4-Max'), 'key': vendor + '/qwen4-max', 'id': 'keeper'}
    report_catalog.save_catalog([old, keeper], tmp_path)
    (tmp_path / 'README.md').write_text((report_catalog.ROOT / 'README.md').read_text())
    config = tmp_path / 'configs'
    config.mkdir()
    (config / 'report-terms.json').write_text((report_catalog.ROOT / 'configs/report-terms.json').read_text())
    sources = config / 'report-sources.json'
    sources.write_text(json.dumps({vendor: {**SETTINGS, 'official': ''}}))
    aliases = config / 'aliases.json'
    aliases.write_text('{}')
    monkeypatch.setattr(report_watch, 'SOURCES', sources)
    monkeypatch.setattr(report_watch, 'ALIASES', aliases)
    monkeypatch.setattr(report_watch, 'read_catalog', lambda: report_catalog.read_catalog(tmp_path))
    monkeypatch.setattr(report_watch, 'build', lambda **kw: report_catalog.build(tmp_path, **kw))
    monkeypatch.setattr(report_watch, 'model_pages', lambda *_: [model])
    monkeypatch.setattr(report_watch, 'Arxiv', lambda: ArxivFixture([]))
    monkeypatch.setattr(report_watch, 'body_text', lambda *_: '{}')
    monkeypatch.delenv('REPORTS_DATABASE_URL', raising=False)
    monkeypatch.setattr(sys, 'argv', ['report_watch', '--publish', '--sqlite', str(tmp_path / 'state.db'), '--until', DATES[1]])
    assert report_watch.main() == 0
    assert [r['model'] for r in report_catalog.read_catalog(tmp_path)] == ['Qwen4-Max']
    for pattern in ('*.md', '*.html', '*.svg', '*.json'):
        for path in tmp_path.rglob(pattern):
            assert 'Qwen4-Stage1' not in path.read_text(), path
    report_catalog.build(tmp_path, check=True)


def test_unchanged_card_rejection_is_cached_but_lower_floor_can_restore(monkeypatch):
    config = {**SETTINGS, 'minimum_total_parameters': 3_000_000_000}
    model = {**hub_row('VoiceFlow'), 'pipeline_tag': 'text-to-speech'}
    calls = []
    monkeypatch.setattr(report_watch, 'model_pages', lambda *_: [model])

    def card(*_):
        calls.append(True)
        return 'VoiceFlow is a 1.5B foundation model.'

    monkeypatch.setattr(report_watch, 'hf_card', card)
    monkeypatch.setattr(report_watch, 'try_report', lambda *a, **kw: [])
    rows, seen, *_ = report_watch.scan_hub('alibaba_qwen', config, {}, {}, {}, *DATES, 12, None)
    assert rows == [] and len(calls) == 1
    rows, *_ = report_watch.scan_hub('alibaba_qwen', config, {}, {}, {'seen': seen}, *DATES, 12, None)
    assert rows == [] and len(calls) == 1
    config['minimum_total_parameters'] = 1_000_000_000
    rows, *_ = report_watch.scan_hub('alibaba_qwen', config, {}, {}, {'seen': seen}, *DATES, 12, None)
    assert rows[0]['total_parameters'] == 1_500_000_000
    assert len(calls) == 2


@pytest.mark.parametrize("separate_launch", [False, True])
def test_exact_small_official_release_is_still_hidden(monkeypatch, separate_launch):
    config = {**SETTINGS, 'minimum_total_parameters': 3_000_000_000}
    url = 'https://qwen.ai/releases/qwen4'
    old = {**release('Qwen4'), 'key': 'alibaba_qwen/qwen4', 'release_url': url}
    if separate_launch:
        old.update(release_url='https://qwen.ai/releases/qwen4-launch', official_url=url,
                   total_parameters=4_000_000_000)
    monkeypatch.setattr(report_watch, 'official_entries', lambda *_: [
        {'url': url, 'title': 'Introducing Qwen4', 'date': '2026-11-10'}])
    monkeypatch.setattr(report_watch, 'body_text', lambda *_:
                        '<h1>Introducing Qwen4</h1><p>Qwen4 is a 1.5B foundation model.</p>')
    rows, *_ = report_watch.scan_official('alibaba_qwen', config, {}, {old['key']: old}, {}, *DATES, 12, None)
    assert rows[0]['total_parameters'] == 1_500_000_000
    assert report_watch.project(rows, {'alibaba_qwen': config}) == []
