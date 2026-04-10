---
name: quarterly-llm-repo-refresh
description: Refresh awesome-llm-tech-reports by dynamically discovering latest model-release technical reports, downloading or rendering official PDFs, regenerating README sections, and validating the full SOP before push.
argument-hint: "[latest_models_curated.json(optional)]"
---

# Quarterly LLM Repo Refresh

Use this skill to update `awesome-llm-tech-reports` without breaking the existing README style. The default behavior is incremental append from `2025-01` to the latest run date. Bootstrap rebuilds are allowed only with `--from-scratch`.

## When To Use

Use this skill when you need to:
- discover newly released frontier models from monitored organizations,
- repair stale or missing report links with better official sources,
- regenerate local PDFs and English `Core Highlights`,
- refresh README tables, year summaries, and SVG diagrams consistently.

## Required Inputs

- Optional: `$ARGUMENTS[0]` as a pre-generated curated runtime snapshot.
- If no argument is provided, run dynamic discovery first, then build the curated runtime snapshot from the current `README.md` boundary.
- Do not blindly execute the static `MODELS` list and do not feed raw `.cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json` directly into incremental refreshes.

## Core Workflow

1. Run preflight:
   - export proxy if the environment cannot reach the internet,
   - ensure Playwright Chromium is installed,
   - confirm the repo is clean enough to update safely.
2. Discover model candidates:
   - `python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/discover_models.py --until <today> --output .cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json`
3. Build the curated runtime snapshot from the current README boundary:
   - `python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/build_curated_models.py --discover-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json --output .cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json`
4. Download/render from the curated snapshot:
   - `python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/download_papers.py --models-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json`
5. Update README incrementally:
   - `python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/update_readme_incremental.py --results-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_download_results.json`
6. Regenerate Excalidraw-style SVG assets:
   - `node .cursor/skills/quarterly-llm-repo-refresh/runtime/render_readme_diagrams.mjs`
7. Run the validation gate before commit/push.

## Hard Requirements

- Discovery must be organization-driven:
  - `LongCat / Meituan`: arXiv + `meituan-longcat`
  - `Zhipu / Z.AI`: `docs.z.ai`, `docs.bigmodel.cn`, `zai-org`
  - `MiniMax`: official news pages and related official article sources
  - `Google`: DeepMind model cards, Gemma pages, AI docs
  - `OpenAI`: Deployment Safety Hub sitemap + model pages + official PDFs
  - `xAI`: `data.x.ai`, `x.ai/news`, and `docs.x.ai/docs/release-notes` fallback
  - `Anthropic`: sitemap-first discovery with official PDF fallback
  - `Meta`: direct official Llama release pages
- Discovery output must include:
  - `canonical_model_id`
  - `aliases`
  - `source_page`
  - `evidence_urls`
  - `evidence_type`
  - `release_classification`
  - `classification_reason`
  - `confidence`
  - `discovered_at`
- Alias merging is mandatory:
  - `GLM 5V Flash` -> `GLM-5V-Turbo`
  - `LongCat` paper title / repo title / README title variants -> one canonical name
  - `OpenAI o3 and o4-mini` -> `o3 / o4-mini`
- Include only model-release records. Keep excluded findings with machine-readable reasons.
- Source URL selection must be dynamic and priority-driven per run.
- `.cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json` is a discovery superset, not a safe direct download input.
- `.cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json` is the required runtime boundary for incremental repo refreshes.
- `YYYY-MM_` filename prefixes must match runtime-calibrated release months.
- `o3 / o4-mini` must stay pinned to the corrected `2025-04` release month at runtime.
- If xAI PDF/news endpoints are anti-bot blocked, fall back to `docs.x.ai/docs/release-notes` for materialization but keep the model's declared release month.
- `Core Highlights` must be regenerated from downloaded PDF text or webpage-rendered PDF text, in English only.
- README diagrams must be SVG assets generated from structured JSON, not Mermaid blocks.
- Monthly Density Snapshot must keep bubble size proportional to release count and must not render side tags.
- `Star History` remains the external chart; do not rewrite it.

## Preflight And Debug

If network access fails, try:

```bash
export https_proxy=http://127.0.0.1:13659
export http_proxy=http://127.0.0.1:13659
```

Playwright preflight:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()
print("playwright-ready")
PY
```

## Completion Gate

Before claiming completion, run:

```bash
bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh
```

## Additional Resources

- SOP details: [reference.md](reference.md)
- Example commands and input/output shapes: [examples.md](examples.md)
- ATOM-aligned vendor source map: [vendor_sources.md](vendor_sources.md)
- Validation script: [scripts/validate_skill.sh](scripts/validate_skill.sh)
