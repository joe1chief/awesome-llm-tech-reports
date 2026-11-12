.PHONY: check
check:
	uv run ruff check
	uv run pytest
	node --check docs/js/app.js
	node --check docs/js/arena_compare.js
	uv run python scripts/report_catalog.py check $(CATALOG_CHECK_ARGS)
