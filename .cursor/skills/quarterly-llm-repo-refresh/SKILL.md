---
name: quarterly-llm-repo-refresh
description: Maintain the model release catalog and check the generated README, Pages timeline, and technical word cloud.
---

# Model catalog maintenance

Follow the [catalog maintenance guide](../../../REPORT_AUTOMATION.md).

Use `uv run python scripts/report_watch.py --vendor meituan --strict` for a preview. Update the source settings or verified backfill when a release is missing. Rebuild the generated files with `uv run python scripts/report_catalog.py build` and run `make check` from the repository root.
