# Quarterly Refresh Reference

## 1) Scope

Target repository: `awesome-llm-tech-reports`

Preserve:
- directory layout: `<year>/<org_slug>/`
- filename pattern: `YYYY-MM_slugified-model-name.pdf`
- reverse-chronological model index in README.

## 2) Model Inclusion Rules

Include only model-release technical reports.

Exclude:
- standalone method papers,
- generic benchmark papers,
- unrelated architecture-only papers,
- pages without a released model context.

## 3) Source URL Prioritization (Runtime)

For each model entry, build `candidate_links` and select source dynamically per run.

Priority order:
1. arXiv PDF
2. official CDN model card/report PDF
3. official repo raw PDF
4. official blog/news page (render to PDF)

Do not keep a lower-priority URL if a higher-priority URL is downloadable.

## 4) Dynamic Input Contract

Preferred run input is crawler output JSON:

- required fields:
  - `release_date`
  - `org`
  - `org_slug`
  - `model`
  - `core_feature`
  - `official_link`
- optional field:
  - `candidate_links` (recommended)

Run:

```bash
python3 download_papers.py --models-json <path/to/models.json>
```

Downloader writes structured run output by default:

```bash
scripts/latest_download_results.json
```

## 5) Release Month Accuracy

Downloader must calibrate `release_date` by source evidence at runtime:
- arXiv published date,
- date pattern in official URL,
- webpage published metadata/content.

Prefix `YYYY-MM_` in filename must match calibrated month.

## 6) Webpage To PDF Rules

If selected URL is a webpage:
- use Playwright to render PDF,
- enforce `%PDF-` signature check,
- enforce minimum extractable text threshold.

Preflight:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    b.close()
print("playwright-ready")
PY
```

## 7) README Rules

- README must remain English-only.
- `Core Highlights` must come from downloaded PDF/blog-PDF content.
- Monthly Density Snapshot:
  - no side tags,
  - bubble class is dynamic: `b<count>`.

Example:
- release count `7` -> class `b7`
- release count `12` -> class `b12`

README update command (incremental append mode):

```bash
python3 scripts/update_readme_incremental.py --results-json scripts/latest_download_results.json
```

From-scratch bootstrap mode:

```bash
python3 scripts/update_readme_incremental.py \
  --results-json scripts/latest_download_results.json \
  --from-scratch
```

## 8) Mandatory Validation

Run in repo root:

```bash
python3 scripts/sop_validate.py
python3 -m unittest tests/test_download_papers.py
python3 -m unittest tests/test_update_readme_incremental.py
bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh
```

All must pass before commit/push.

## 9) Network Debug

```bash
export https_proxy=http://127.0.0.1:13659
export http_proxy=http://127.0.0.1:13659
```

Quick checks:

```bash
git ls-remote https://github.com/joe1chief/awesome-llm-tech-reports.git | head -n 3
curl -I -L --max-time 20 https://arxiv.org/pdf/2602.15763 | head -n 10
```
