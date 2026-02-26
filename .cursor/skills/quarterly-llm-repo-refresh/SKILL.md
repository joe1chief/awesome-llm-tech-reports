---
name: quarterly-llm-repo-refresh
description: Use when performing a quarterly incremental update of the awesome-llm-tech-reports repository -- search new model releases, download/verify PDFs, and update README with frozen visual style conventions.
---

# Quarterly LLM Repo Refresh SOP

## Scope

This skill standardizes quarterly incremental updates for `awesome-llm-tech-reports` while preserving:

- Directory structure: `<year>/<org_slug>/`
- Filename pattern: `YYYY-MM_slugified-model-name.pdf`
- README visual structure and Mermaid style
- Reverse-chronological model index

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

### Step 1 - Research New Releases

- Use official channels first, then reputable secondary references.
- For each candidate release, verify:
  - release month (`YYYY-MM`)
  - exact model name/version
  - official URL (priority: arXiv PDF > official CDN PDF > official blog page)
- Exclude speculative or unreleased versions.

### Step 2 - Update `download_papers.py`

Append only new entries into `MODELS` with this schema:

- `release_date`
- `org`
- `org_slug`
- `model`
- `core_feature`
- `official_link`

Rules:

- `org_slug` must match existing directory conventions.
- Keep release-date sorting compatible with current script behavior.
- Do not alter prior validated entries unless source links are broken.

### Step 3 - Run Download and Validation

Run in repo root:

```bash
python3 download_papers.py
```

Critical:

- Never add `--write-readme` during routine refresh.
- Confirm newly downloaded files are true PDFs (header `%PDF-`).
- Confirm extracted text length passes threshold (avoid screenshot-only artifacts).
- For blog URLs, ensure rendered PDFs include complete page content.

### Step 4 - Consolidate PDFs into `pdf/`

After download validation, aggregate all technical-report PDFs from year directories
into a single flat directory for easy bulk access.

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

Checks:

- Ensure `pdf/` exists and file count matches current year-tree PDFs.
- Keep original `2025/` and `2026/` files untouched (copy, not move).

### Step 5 - Incrementally Update `README.md`

Do append/update only; do not regenerate from templates.

- **Badges**: update only count values.
- **Release Timeline** (`mermaid flowchart TB`):
  - append month backbone nodes
  - append entries in camp subgraphs:
    - OpenAI
    - Anthropic
    - Google
    - China-based Labs
    - Other Global
  - use `★` for high-impact releases.
- **Monthly Density Snapshot** (`mermaid flowchart LR`):
  - use bubble node format: `(("YY-MM<br/>Rxx"))`
  - keep side tags for representative companies
  - split overly long tags into left/right labels.
- **Company Quick Links**: add anchors only if new org appears.
- **Model Index**:
  - columns must remain:
    - `Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File`
  - append rows into correct year `<details>` block
  - keep reverse chronological order.
- **Core Highlights source rule**:
  - arXiv PDF links: summarize from PDF abstract/body
  - non-arXiv links: summarize from webpage content (not OCR-garbled fragments).
- **Star History**: keep static section unchanged.

### Step 6 - Commit and Push

```bash
git add .
git commit -m "Quarterly update: add <N> models from <YYYY-MM> to <YYYY-MM>"
git push origin main
```

Use author identity:

- `joe1chief <joe1chief1993@gmail.com>`

## Frozen Style Reference Snippets

### Timeline Camp Colors

```text
openai:    fill:#e8f2ff, stroke:#2f6feb, color:#0b1f44
anthropic: fill:#fff4e8, stroke:#b15f00, color:#4a2800
google:    fill:#e9fbe9, stroke:#1a7f37, color:#083b1e
china:     fill:#fff0f6, stroke:#bf3989, color:#4a0d2f
other:     fill:#f4f4f4, stroke:#6e7781, color:#24292f
impact:    fill:#fff8c5, stroke:#d4a72c, color:#3d2f00
```

### Bubble Size Classes

```text
b1,b2,b3,b4,b5,b12 + tag
Keep existing class-to-count mapping from README and extend conservatively.
```

## Common Mistakes (Do Not Repeat)

- Never run `python3 download_papers.py --write-readme` for incremental updates.
- Never use `_rebuild_readme.py` (deprecated overwrite script).
- Never regenerate Mermaid diagrams from scratch; append into existing structure.
- Never replace curated README sections with auto-generated templates.
- Never skip PDF signature/text checks for new files.

## Completion Checklist

- New releases verified and non-speculative
- PDFs downloaded and validated
- README updated with frozen style
- Model index sorted correctly
- Git status clean after push
