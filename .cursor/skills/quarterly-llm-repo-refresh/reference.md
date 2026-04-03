# Quarterly Refresh Reference

## 1) Scope

Target repository: `awesome-llm-tech-reports`

Preserve:
- directory layout: `<year>/<org_slug>/`
- filename pattern: `YYYY-MM_slugified-model-name.pdf`
- reverse-chronological README table and folded year index
- existing README style and section order

Default update mode:
- incremental append from `2025-01` to the current run date
- bootstrap rebuild only when explicitly using `--from-scratch`

## 2) Discovery Rules

Discovery is the first-class source of truth. Do not start with the static `MODELS` list.

Run:

```bash
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/discover_models.py --until 2026-04-03 --output .cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/build_curated_models.py --discover-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json --output .cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json
```

Monitored ecosystems:
- `LongCat / Meituan`: arXiv `LongCat` family + `meituan-longcat`
- `Zhipu / Z.AI`: `docs.z.ai`, `docs.bigmodel.cn`, `huggingface.co/zai-org`
- `MiniMax`: official news pages and related official article sources
- `Google`: `deepmind.google/models/model-cards/`, `deepmind.google/models/gemma/`, `ai.google.dev/gemma/docs`
- `OpenAI`: `deploymentsafety.openai.com/sitemap.xml` + top-level model pages + official PDFs
- `xAI`: `data.x.ai`, `x.ai/news`, `docs.x.ai/docs/release-notes`
- `Anthropic`: `anthropic.com/sitemap.xml` + official news / PDF pages
- `Meta`: official Llama release pages such as `ai.meta.com/blog/llama-4-multimodal-intelligence/`

Discovery output must retain:
- `canonical_model_id`
- `aliases`
- `source_page`
- `evidence_urls`
- `evidence_type`
- `release_classification`
- `classification_reason`
- `confidence`
- `discovered_at`

## 3) Inclusion / Exclusion Rules

Include only:
- official model cards,
- official system cards,
- official model pages with released models,
- model-release technical reports on arXiv,
- official web pages that can be rendered to PDF and clearly correspond to a released model.

Exclude:
- standalone method papers,
- benchmark-only papers,
- product/tool variants that are not frontier model releases,
- pages without a released model context.

Examples:
- `LongCat-Flash-Prover` and `LongCat-Next`: include
- `GLM-5V-Turbo`: include
- `ShieldGemma 2` / `EmbeddingGemma` / `FunctionGemma`: discover but exclude

## 4) Alias And Canonical Naming

Canonical names must come from the strongest official source.

Alias mapping examples:
- `GLM 5V Flash` -> `GLM-5V-Turbo`
- `GLM-4.7 Flash` -> `GLM-4.7-Flash`
- `LongCat` paper title / repo title / README title variants -> one canonical model id

Rules:
- official docs/model card title wins,
- paper titles and repo titles remain in `aliases`,
- README display name should use the canonical model name unless backward compatibility requires the existing label.
- `o3 / o4-mini` remains the canonical README label even when the source page title is `OpenAI o3 and o4-mini`.

## 5) Source URL Prioritization

For each discovered record, probe `candidate_links` dynamically at runtime.
Do not feed the raw discovery superset directly into the downloader for incremental repo refreshes.

Curated runtime boundary:

```bash
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/build_curated_models.py --discover-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_models.json --output .cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json
```

The curated snapshot must:
- preserve the current README model boundary,
- overlay fresher official links / aliases / evidence from dynamic discovery,
- keep README model labels stable for backward-compatible incremental refreshes,
- filter static assets and unrelated external links out of `candidate_links`.
- add explicit official fallbacks when direct PDFs are known to be anti-bot blocked in the current environment.

Priority order:
1. official PDF / model card / system card
2. arXiv PDF
3. official model page
4. official Hugging Face / GitHub model page
5. other links only as supporting evidence, not primary download source

Downloader command:

```bash
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/download_papers.py --models-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json
```

If `--models-json` is omitted, `.cursor/skills/quarterly-llm-repo-refresh/runtime/download_papers.py` should try dynamic discovery first and only then fall back to static `MODELS`.
When `README.md` is present, the default runtime path should prefer `.cursor/skills/quarterly-llm-repo-refresh/state/latest_models_curated.json`.

Special cases:
- `o3 / o4-mini`: keep the corrected `2025-04` month even if a source page exposes stale or conflicting metadata.
- `xAI`: if `data.x.ai` and `x.ai/news` both return anti-bot `403`, allow `docs.x.ai/docs/release-notes` as the materialization source, but do not let that page override the model's declared month.

## 6) Release Month Accuracy

Filename prefixes must be calibrated at runtime from source evidence:
- arXiv published date,
- date pattern in URL,
- HTTP `Last-Modified`,
- webpage published metadata,
- visible date text near the page title when available.

The final saved filename must use the resolved `YYYY-MM`.

## 7) Webpage To PDF Rules

If the selected URL is a webpage:
- prefer the best official model page/news page,
- render to PDF with Playwright,
- if the page is hostile to stable browser printing, fall back to visible-text PDF generation,
- enforce `%PDF-` signature and usable text extraction.

Playwright preflight:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

## 8) Core Highlights Rules

`Core Highlights` must be English only and regenerated from:
- downloaded PDF text,
- or webpage-rendered PDF / visible webpage text when no raw PDF exists.

Do not keep Chinese summaries in README.
Do not let navigation text, section headings, or marketing boilerplate overwrite a good existing English summary.

## 9) README And Diagram Rules

Update README incrementally:

```bash
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/update_readme_incremental.py --results-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_download_results.json
```

Bootstrap rebuild:

```bash
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/update_readme_incremental.py \
  --results-json .cursor/skills/quarterly-llm-repo-refresh/state/latest_download_results.json \
  --from-scratch
```

Render diagrams:

```bash
node .cursor/skills/quarterly-llm-repo-refresh/runtime/render_readme_diagrams.mjs
```

Generated assets:
- `.cursor/skills/quarterly-llm-repo-refresh/state/generated/monthly_density.json`
- `.cursor/skills/quarterly-llm-repo-refresh/state/generated/release_timeline.json`
- `assets/diagrams/monthly-density.svg`
- `assets/diagrams/release-timeline.svg`

Notes:
- `.cursor/skills/quarterly-llm-repo-refresh/state/generated/*` is a local intermediate cache used during refresh and validation; it should not be committed to `main`.
- The repository only keeps the final SVG diagrams in `assets/diagrams/`.

Rules:
- README must remain English-only
- README must reference SVG assets, not Mermaid
- `Star History` stays external
- bubble size must scale with actual monthly release count

## 10) Validation

Run in repo root:

```bash
python3 -m unittest \
  tests/test_build_curated_models.py \
  tests/test_download_papers.py \
  tests/test_update_readme_incremental.py \
  tests/test_discover_models.py \
  tests/test_model_aliases.py \
  tests/test_render_readme_diagrams.py
python3 .cursor/skills/quarterly-llm-repo-refresh/runtime/sop_validate.py
bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh
```

All must pass before commit/push.

## 11) Network Debug

If internet access is blocked:

```bash
export https_proxy=http://127.0.0.1:13659
export http_proxy=http://127.0.0.1:13659
```

Quick checks:

```bash
git ls-remote https://github.com/joe1chief/awesome-llm-tech-reports.git | head -n 3
curl -I -L --max-time 20 https://arxiv.org/pdf/2603.21065 | head -n 10
```

xAI anti-bot check:

```bash
curl -I -L --max-time 20 https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf
python3 - <<'PY'
import requests
for url in [
    "https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf",
    "https://x.ai/news/grok-4",
    "https://docs.x.ai/docs/release-notes",
]:
    r = requests.get(url, timeout=20, verify=False)
    print(url, r.status_code, r.headers.get("content-type"))
PY
```
