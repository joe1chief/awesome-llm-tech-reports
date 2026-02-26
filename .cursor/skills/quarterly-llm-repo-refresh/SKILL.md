---
name: quarterly-llm-repo-refresh
description: Refresh awesome-llm-tech-reports quarterly by re-crawling model-release technical reports, selecting the best downloadable official source URL, downloading/rendering PDFs, and syncing README metrics.
argument-hint: "[models-json(optional)]"
---

# Quarterly LLM Repo Refresh

Use this skill to run the full quarterly refresh pipeline for `awesome-llm-tech-reports`.

## When To Use

Use this skill when you need to:
- add newly released model technical reports,
- regenerate download inputs from fresh crawl results,
- fix broken links by selecting better official sources,
- refresh README timeline/index/Monthly Density Snapshot consistently.

## Required Inputs

- Optional: `$ARGUMENTS[0]` as a crawler-generated `models.json` path.
- If no argument is provided, use in-file `MODELS` in [`download_papers.py`](../../../../download_papers.py).

## Core Workflow

1. Run preflight checks (proxy, Playwright, tests).
2. Re-crawl monitored organizations and rebuild model candidates.
3. Prefer running downloader with dynamic snapshot:
   - `python3 download_papers.py --models-json <path/to/models.json>`
4. Let downloader pick the best source URL at runtime from candidate links.
5. Download direct PDF or render official webpage to PDF.
6. Validate repository consistency before commit/push.

## Hard Requirements

- Include only model-release technical reports.
- Source URL selection must be dynamic and priority-driven each run.
- Filename prefix `YYYY-MM_` must match runtime-calibrated release month.
- `Core Highlights` must come from crawled PDF/blog-PDF content.
- Monthly snapshot rules:
  - no side tags;
  - bubble class name must be `b<count>` (dynamic, not fixed buckets).

## Additional Resources

- Detailed SOP and rules: [reference.md](reference.md)
- Command examples and `models.json` samples: [examples.md](examples.md)
- Skill verification script: [scripts/validate_skill.sh](scripts/validate_skill.sh)

## Completion Gate

Before claiming completion, run:

```bash
bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh
```

