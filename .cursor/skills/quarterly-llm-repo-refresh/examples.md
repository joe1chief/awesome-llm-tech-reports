# Usage Examples

## Example 1: Full Quarterly Refresh With Crawler Output

```bash
export https_proxy=http://127.0.0.1:13659
export http_proxy=http://127.0.0.1:13659

python3 scripts/sop_validate.py
python3 -m unittest tests/test_download_papers.py

python3 download_papers.py --models-json /path/to/models.json
```

## Example 2: Fallback Run With In-File MODELS

```bash
python3 download_papers.py
```

## Example 3: `models.json` With Candidate Links

```json
[
  {
    "release_date": "2026-02",
    "org": "Alibaba",
    "org_slug": "alibaba_qwen",
    "model": "Qwen 3.5",
    "core_feature": "Reasoning + coding improvements.",
    "official_link": "https://qwen.ai/blog?id=qwen3.5",
    "candidate_links": [
      "https://qwen.ai/blog?id=qwen3.5",
      "https://arxiv.org/abs/2505.09388"
    ]
  }
]
```

Expected behavior:
- downloader probes candidates,
- chooses highest-priority downloadable official source,
- downloads PDF (or renders webpage if needed).

## Example 4: Skill Verification

```bash
bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh
```

