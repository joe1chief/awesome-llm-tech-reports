---
name: quarterly-llm-repo-refresh
description: Use when performing a quarterly incremental update of the awesome-llm-tech-reports repository with mandatory re-crawl, model-release filtering, timestamp prefix calibration, and README synchronization.
---

# Quarterly LLM Repo Refresh SOP

## Scope

This skill standardizes quarterly incremental updates for `awesome-llm-tech-reports` while preserving:

- Directory structure: `<year>/<org_slug>/`
- Filename pattern: `YYYY-MM_slugified-model-name.pdf`
- README visual structure and Mermaid style
- Reverse-chronological model index

## Hard Rules (Non-Negotiable)

1. Only include **model-release technical reports**.
- Exclude standalone method papers / architectures / benchmarks / datasets unless explicitly tied to an official released model card/report.

2. Filename prefix timestamp (`YYYY-MM_`) must be accurate.
- `download_papers.py` must resolve release month from source evidence at runtime (arXiv published date, official URL date pattern, or webpage published metadata).

3. `README.md` must stay English-only.
- `Core Highlights` must be summarized from downloaded PDF content (or rendered blog PDF content), not guessed.

4. Monthly bubble chart rules:
- No side tags in `Monthly Density Snapshot`.
- Bubble size class must match release count (`b1/b2/b3/b4/b5/b12`).

## Monitored Organizations (Fixed)

Track these 18 organizations and channels every refresh cycle:

1. OpenAI (`cdn.openai.com`, `arxiv.org`)
2. Anthropic (`assets.anthropic.com`, `www-cdn.anthropic.com`)
3. Google (`storage.googleapis.com`, `arxiv.org`)
4. Meta (`ai.meta.com/blog`)
5. xAI (`data.x.ai`)
6. DeepSeek (`arxiv.org`)
7. Alibaba / Qwen (`qwen.ai/blog`, `arxiv.org`)
8. Zhipu AI (`arxiv.org`)
9. Moonshot AI (`github.com/MoonshotAI`, `arxiv.org`)
10. MiniMax (`minimax.io/news`, `github.com/MiniMax-AI`)
11. StepFun (`arxiv.org`)
12. Baidu (`yiyan.baidu.com`, `arxiv.org`)
13. Baichuan Intelligence (`arxiv.org`)
14. InclusionAI (`github.com/inclusionAI`)
15. ByteDance (`arxiv.org`, `bytednsdoc.com`)
16. Tencent (`arxiv.org`)
17. Meituan (`arxiv.org`)
18. Quark (`arxiv.org`)

## SOP

### Step 1 - Mandatory Re-Crawl (Every Run)

Do not run downloader first.

- Re-search all monitored organizations.
- Keep only model-release technical reports.
- Verify each candidate:
  - release month (`YYYY-MM`)
  - exact model name/version
  - official link (priority: arXiv PDF > official CDN PDF > official blog page)
- Exclude speculative/unreleased entries.

### Step 2 - Regenerate `MODELS` in `download_papers.py`

Do not treat in-file old links as source of truth.

- Rebuild `MODELS` snapshot with fields:
  - `release_date`
  - `org`
  - `org_slug`
  - `model`
  - `core_feature`
  - `official_link`
- Keep release-date sorting consistent with existing script behavior.

### Step 3 - Mandatory Code Gates Before Download

Run both commands in repo root:

```bash
python3 scripts/sop_validate.py
python3 -m unittest tests/test_download_papers.py
```

Both must pass before continuing.

### Step 4 - Download and Validate

```bash
python3 download_papers.py
```

Critical:

- Never use `--write-readme` in routine refresh.
- Confirm PDF signature (`%PDF-`) for newly downloaded files.
- Confirm text extraction threshold passes (avoid screenshot-only artifacts).

### Step 5 - Consolidate PDFs into `pdf/`

Run in repo root:

```bash
python3 - <<'PY'
from pathlib import Path
import shutil

root = Path(".").resolve()
out = root / "pdf"
out.mkdir(exist_ok=True)

for p in sorted(root.rglob("*.pdf")):
    if out in p.parents:
        continue
    top = p.parts[len(root.parts)]
    if top not in {"2025", "2026"}:
        continue
    dst = out / p.name
    if dst.exists():
        rel_tag = "_".join(p.relative_to(root).parts[:-1]).replace("/", "_")
        dst = out / f"{p.stem}__{rel_tag}{p.suffix}"
    if not dst.exists():
        shutil.copy2(p, dst)
PY
```

If duplicate `*__*.pdf` files appear after reruns:

```bash
find pdf -maxdepth 1 -name '*__*.pdf' -delete
```

### Step 6 - Incremental README Update

Do append/update only; do not regenerate from templates.

- Badges: update count values only.
- Release Timeline: append month/camp nodes only.
- Monthly Density Snapshot:
  - bubble format: `(("YY-MM<br/>Rxx"))`
  - no side tags
  - class mapping follows count (`1->b1, 2->b2, 3->b3, 4->b4, 5->b5, 12->b12`)
- Model Index:
  - keep columns unchanged
  - keep reverse chronological order
  - `Core Highlights` derived from crawled PDF/blog-PDF content

### Step 7 - Commit and Push

```bash
git add .
git commit -m "Quarterly update: add <N> models from <YYYY-MM> to <YYYY-MM>"
git push origin main
```

Use author identity:

- `joe1chief <joe1chief1993@gmail.com>`

## Debug Playbook

### Network / Proxy

```bash
export https_proxy=http://127.0.0.1:13659
export http_proxy=http://127.0.0.1:13659
```

Quick checks:

```bash
git ls-remote https://github.com/joe1chief/awesome-llm-tech-reports.git | head -n 3
curl -I -L --max-time 20 https://arxiv.org/pdf/2602.15763 | head -n 10
```

### Recovery for Accidental Deletions

If a failed run removed tracked PDFs:

```bash
git restore 2025 2026
```

## Completion Checklist

- Re-crawl completed and non-model papers excluded
- `scripts/sop_validate.py` passed
- unit tests passed
- PDFs downloaded and validated
- README updated (English-only, snapshot consistent)
- Git status clean after push
