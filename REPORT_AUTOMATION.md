# Model report refresh

The versioned public snapshot is [data/catalog.json](data/catalog.json). The catalog builder updates the README, timeline, technical word cloud and Pages JSON from that snapshot. Releases may appear on the timeline while their reports are being located. The report index lists entries with verified technical documentation.

## Local development

Use Python 3.11 or later, Node.js and uv.

~~~sh
make check
uv run python scripts/report_watch.py --vendor meituan --vendor zhipu --vendor alibaba_qwen --since 2026-07-01 --strict
uv run python scripts/report_catalog.py build
~~~

A watch run prints a preview by default. With a full checkout, add --publish --sqlite .report-state/watch.sqlite3 to save a local refresh for inspection. The state file is ignored by Git. For a sparse checkout, pass --pdf-manifest with the output of git ls-tree -r --name-only HEAD to the catalog checker.

Sources are configured in [configs/report-sources.json](configs/report-sources.json). Each official index has its own cursor. A blocked article can still leave a pending release when the vendor index gives its name and date. A successful source pass saves observed revisions with its cursor. The report resolver follows fixed Hugging Face model card links, then checks arXiv and official vendor sources. The --strict option returns nonzero when a source fails, reaches its processing limit, or encounters a report lookup error. Repeat a dated backfill with persistent state to work through deferred records. Dates in the catalog distinguish day-level release evidence from month-level historical records.

The [verified backfill](configs/report-backfill.json) records dated vendor evidence for historical gaps. A change to the file on `main` imports those releases immediately when auto-refresh is enabled. Dated manual replays also import matching entries. Regular polls continue report lookup for pending releases and publish each documented release phase on the timeline.

The public catalog covers language models, vision-language models, and generative multimodal models. Hub discovery checks the reported task and tags, and uses a known model family when the task is missing. Vendor exclusions cover families with specialized roles, including embedding and classification, simulation, robot control, and standalone draft models. Publishing applies the same exclusions to previously collected entries. Changes to source settings on `main` rebuild the public catalog, timeline, and word cloud when auto-refresh is enabled.

[The parameter policy](configs/report-parameters.json) sets a 3-billion total-parameter floor for published models. It uses verified totals, declared model sizes and supported Hub Safetensors metadata. The floor applies to total parameters for MoE models. Models with no reliable total remain eligible. Previously collected entries below the floor are retained in collection state so a lower floor can restore them. Updating the policy on `main` rebuilds the public archive.

PDFs can be mirrored after the exact download URL has been reviewed for redistribution and added to the vendor's mirror list. Each mirrored PDF is written under its year and vendor and into the existing flat PDF directory.

## Shared Supabase and GitHub Actions

1. Review and apply [the reports migration](supabase/migrations/202611120001_llm_reports.sql) through the shared project's existing migration process. Provision a login for the reports_runtime role and verify its access to llm_reports and separation from the Radar tables.
2. Configure the target repository's REPORTS_DATABASE_URL Actions secret with the reports runtime session pooler connection. Leave the hosted connection and raw state out of published assets.
3. Run the Refresh model technical reports workflow in preview mode. Inspect each source's result. Verify the real Hub API and an official release page, then run a publish to check the Git commit and the Pages deployment reference.
4. Set REPORTS_AUTO_REFRESH to true to run every eight hours. GitHub Actions then writes only changed catalog artifacts. The Pages workflow receives the exact published commit. A failed Pages deploy can be rerun for the same snapshot.

## Radar pause and restore

The six production workflows are collect-alert.yml, paper-sweep.yml, daily-digest.yml, delivery-reconcile.yml, maintenance.yml and pages.yml. GitHub can re-enable those workflows individually. Check AgentMail's existing scheduled drafts before restoring live delivery. Resume collection in shadow mode when replaying the pause window.
