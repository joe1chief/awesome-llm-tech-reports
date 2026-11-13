# Model catalog maintenance

[data/catalog.json](data/catalog.json) is the public snapshot. The catalog builder generates the README index, the Pages catalog, the release timeline, and the technical word cloud. The timeline includes dated releases awaiting documentation. The README and website indexes list models with a source document.

## Discovery and inclusion

The refresh scans the Hugging Face organizations and vendor indexes in [configs/report-sources.json](configs/report-sources.json). Each source has its own cursor. Failed or deferred items can be retried without discarding work from other sources.

The resolver checks report links in revision-pinned Hugging Face model cards, then matches arXiv papers and checks official vendor sources. A model card or official technical page can serve as the source when a standalone report is unavailable. Releases that still need a stronger source are checked daily for their first 30 days and weekly through day 90.

The public catalog covers language, vision-language, and generative multimodal models. Task metadata, tags, and known model families help exclude releases such as embeddings, classifiers, robot controllers, and standalone draft models. Quantized packages are grouped with the base model when their relationship is known.

The [parameter policy](configs/report-parameters.json) currently requires at least 3 billion total parameters when the count can be established. MoE models use total parameters. Models with an unknown count remain eligible. The same rules apply when previously collected releases are published again.

Use [configs/report-backfill.json](configs/report-backfill.json) to add dated official evidence for missed releases or correct existing entries. Set `historical` to import an older release outside the replay window, or use `correction` to replace an incorrect date, source, or excerpt. Review redistribution rights before adding an exact PDF URL to a vendor's mirror list. Approved PDFs are stored under the release year and organization and in the flat `pdf/` archive.

## Local commands

Use Python 3.11 or later, Node.js, and uv. Run these commands from the repository root.

```sh
make check
uv run python scripts/report_watch.py --vendor meituan --strict
uv run python scripts/report_catalog.py build
```

The watcher previews changes by default. Pass `--since YYYY-MM-DD` to replay from a specific date. Use `--strict` to get a nonzero exit status for source errors, deferred items, or document lookup warnings. To inspect a local publication, use a full checkout with `REPORTS_DATABASE_URL` unset and pass `--publish --sqlite .report-state/watch.sqlite3`. Reuse the SQLite path when repeating a replay so completed work can be skipped.

For a sparse checkout, use a Git file manifest to validate the PDF paths.

```sh
git ls-tree -r --name-only HEAD > /tmp/llm-report-files.txt
make check CATALOG_CHECK_ARGS='--pdf-manifest /tmp/llm-report-files.txt'
```

## Technical word cloud

The word cloud uses documents from the latest catalog year. The extractor reads archived PDFs, source PDFs, model cards, and official technical pages. It skips references and navigation where possible and uses the catalog excerpt when it cannot extract readable source text. Terms count once per distinct document. The glossary in [configs/report-terms.json](configs/report-terms.json) normalizes English and Chinese aliases, and the extractor also recognizes recurring technical phrases.

Each scheduled run processes up to 30 new or due sources. To process a larger batch, dispatch the refresh workflow with `mode=publish` and `word_cloud_only=true`. For a local run using archived PDFs, run `uv run python scripts/report_wordcloud.py --local-only --limit 250` and rebuild the catalog. The repository stores extracted terms in [data/report-text-terms.json](data/report-text-terms.json). The site publishes [term counts, source coverage, and the displayed terms](docs/data/word-cloud.json).

## GitHub Actions and Supabase

[Refresh model technical reports](.github/workflows/refresh-reports.yml) runs every eight hours when the `REPORTS_AUTO_REFRESH` repository variable is `true`. Pushes to `main` on configured paths rebuild the snapshot from stored and verified evidence and deploy it. Use the workflow's `preview` mode to inspect source results, or `publish` to save and deploy a refresh. A failed Pages deployment can be rerun for the same published commit.

For a new deployment, apply the [Supabase migration](supabase/migrations/202611120001_llm_reports.sql) and provision a login for `reports_runtime` with access to the `llm_reports` schema. Store the session pooler connection in the `REPORTS_DATABASE_URL` Actions secret. Run a preview to confirm discovery, then publish and check the Pages deployment before enabling the schedule.

If the shared `ai-research-radar` repository is resumed, review its workflow states and existing delivery drafts there before enabling live delivery.
