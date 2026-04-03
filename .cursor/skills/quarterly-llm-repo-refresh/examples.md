# Usage Examples

## Example 1: Full Incremental Refresh From Discovery

```bash
export https_proxy=http://127.0.0.1:13659
export http_proxy=http://127.0.0.1:13659

python3 -m pip install playwright
python3 -m playwright install chromium

python3 scripts/discover_models.py --until 2026-04-03 --output scripts/latest_models.json
python3 scripts/build_curated_models.py --discover-json scripts/latest_models.json --output scripts/latest_models_curated.json
python3 download_papers.py --models-json scripts/latest_models_curated.json
python3 scripts/update_readme_incremental.py --results-json scripts/latest_download_results.json
node scripts/render_readme_diagrams.mjs
python3 scripts/sop_validate.py
```

## Example 2: No Argument Run With Automatic Discovery

```bash
python3 download_papers.py
python3 scripts/update_readme_incremental.py --results-json scripts/latest_download_results.json
node scripts/render_readme_diagrams.mjs
```

Behavior:
- tries dynamic discovery first,
- writes `scripts/latest_models.json`,
- builds `scripts/latest_models_curated.json` when `README.md` is present,
- falls back to static `MODELS` only if discovery fails.

## Example 3: Bootstrap Rebuild

```bash
python3 scripts/discover_models.py --until 2026-04-03 --output scripts/latest_models.json
python3 scripts/build_curated_models.py --discover-json scripts/latest_models.json --output scripts/latest_models_curated.json
python3 download_papers.py --models-json scripts/latest_models_curated.json
python3 scripts/update_readme_incremental.py \
  --results-json scripts/latest_download_results.json \
  --from-scratch
node scripts/render_readme_diagrams.mjs
```

## Example 4: Discovery Output Shape

```json
[
  {
    "release_date": "2026-04",
    "org": "Zhipu AI",
    "org_slug": "zhipu",
    "model": "GLM-5V-Turbo",
    "canonical_model_id": "zhipu/glm-5v-turbo",
    "aliases": ["GLM-5V-Turbo", "GLM 5V Flash"],
    "core_feature": "",
    "official_link": "https://docs.z.ai/guides/vlm/glm-5v-turbo",
    "candidate_links": ["https://docs.z.ai/guides/vlm/glm-5v-turbo"],
    "source_page": "https://docs.z.ai/",
    "evidence_urls": [
      "https://docs.z.ai/",
      "https://docs.z.ai/guides/vlm/glm-5v-turbo"
    ],
    "evidence_type": "official_model_page",
    "release_classification": "model_release",
    "classification_reason": "glm_frontier_release",
    "confidence": 0.9,
    "discovered_at": "2026-04-03T10:00:00Z"
  }
]
```

## Example 5: Curated Incremental Catch-Up

Use this when you only want to backfill a known missing subset before the next full run.

```bash
python3 scripts/discover_models.py --until 2026-04-03 --output scripts/latest_models.json
python3 scripts/build_curated_models.py --discover-json scripts/latest_models.json --output /tmp/latest_models_curated.json
python3 - <<'PY'
import json
from pathlib import Path

wanted = {
    "LongCat-Flash-Prover",
    "LongCat-Next",
    "GLM-5V-Turbo",
    "GLM-4.7",
    "GLM-4.7-Flash",
    "MiniMax M2.7",
    "Gemma 4",
    "MedGemma 1.5",
}
records = json.loads(Path("/tmp/latest_models_curated.json").read_text())
subset = [item for item in records if item["model"] in wanted]
Path("/tmp/latest_models_curated_subset.json").write_text(
    json.dumps(subset, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
PY

python3 download_papers.py --models-json /tmp/latest_models_curated_subset.json
python3 scripts/update_readme_incremental.py --results-json scripts/latest_download_results.json
node scripts/render_readme_diagrams.mjs
```

## Example 6: xAI Fallback Check

```bash
python3 scripts/discover_models.py --until 2026-04-03 --output scripts/latest_models.json
python3 scripts/build_curated_models.py --discover-json scripts/latest_models.json --output scripts/latest_models_curated.json
python3 - <<'PY'
import json
from pathlib import Path
rows = json.loads(Path("scripts/latest_models_curated.json").read_text())
for row in rows:
    if row["org_slug"] == "xai":
        print(row["model"], row["release_date"], row["candidate_links"])
PY
```

## Example 7: Skill Verification

```bash
bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh
```
