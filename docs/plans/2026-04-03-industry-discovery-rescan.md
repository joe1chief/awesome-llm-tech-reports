# Industry Discovery Rescan Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current partial vendor discovery chain with an industry-wide official-source scan covering all major manufacturers already tracked by the repo.

**Architecture:** Move discovery from a few bespoke adapters to a vendor registry plus source-parser framework. Each vendor entry declares official discovery sources and evidence priorities, then discovery normalizes records into one shared schema before download and README generation. Existing vendor adapters stay only as implementation details under the new registry.

**Tech Stack:** Python 3, requests, stdlib HTML/XML parsing, repo unit tests, Node SVG renderer.

---

### Task 1: Add failing tests for vendor registry coverage

**Files:**
- Modify: `tests/test_discover_models.py`
- Test: `tests/test_discover_models.py`

**Step 1: Write the failing test**
- Add a test asserting the vendor registry contains every manufacturer already present in `README.md`.
- Add a test asserting the registry includes at least: `openai`, `anthropic`, `google`, `xai`, `meta`, `alibaba_qwen`, `quark`, `deepseek`, `moonshot`, `stepfun`, `tencent`, `baidu`, `bytedance`, `baichuan`, `inclusion`, `meituan`, `minimax`, `zhipu`.

**Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_discover_models.py -v`
Expected: FAIL because registry does not exist yet.

**Step 3: Write minimal implementation**
- Add a registry constant and mapping helpers in `scripts/discover_models.py`.

**Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_discover_models.py -v`
Expected: PASS for registry coverage tests.

### Task 2: Add failing tests for generic source parsing

**Files:**
- Modify: `tests/test_discover_models.py`
- Modify: `scripts/discover_models.py`

**Step 1: Write the failing test**
- Add tests for parsing vendor feed snippets from generic official sources:
  - JSON-LD article blocks
  - official GitHub README / repo pages with tech report PDF links
  - arXiv feeds
  - official doc/model card pages

**Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_discover_models.py -v`
Expected: FAIL because parser helpers are missing.

**Step 3: Write minimal implementation**
- Implement generic parsing helpers and integrate them into discovery.

**Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_discover_models.py -v`
Expected: PASS.

### Task 3: Refactor discovery into registry-driven execution

**Files:**
- Modify: `scripts/discover_models.py`
- Modify: `scripts/model_aliases.json`
- Modify: `tests/test_model_aliases.py`

**Step 1: Write the failing test**
- Add tests asserting vendor-specific alias normalization under the new registry names, especially for Qwen and legacy org slugs.

**Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_model_aliases.py -v`
Expected: FAIL until registry/aliases are aligned.

**Step 3: Write minimal implementation**
- Introduce vendor registry metadata.
- Route per-vendor discovery through the registry.
- Keep shared output schema unchanged.

**Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_model_aliases.py tests/test_discover_models.py -v`
Expected: PASS.

### Task 4: Add Qwen and remaining official vendor sources

**Files:**
- Modify: `scripts/discover_models.py`
- Modify: `scripts/model_aliases.json`
- Modify: `tests/test_discover_models.py`

**Step 1: Write the failing test**
- Add explicit discovery tests for recent Qwen releases and at least one record for each currently tracked org family.

**Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_discover_models.py -v`
Expected: FAIL until new vendor sources are wired in.

**Step 3: Write minimal implementation**
- Add official sources for: OpenAI, Anthropic, xAI, Meta, Alibaba/Qwen, Quark, DeepSeek, Moonshot, StepFun, Tencent, Baidu, ByteDance, Baichuan, Inclusion.
- Normalize names and evidence links.

**Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_discover_models.py -v`
Expected: PASS.

### Task 5: Rebuild runtime discovery and incremental refresh flow

**Files:**
- Modify: `download_papers.py`
- Modify: `scripts/update_readme_incremental.py`
- Modify: `README.md`

**Step 1: Write the failing test**
- Add/update tests to confirm runtime models are built from the new industry-wide discovery snapshot.

**Step 2: Run test to verify it fails**
Run: `python3 -m unittest tests/test_download_papers.py tests/test_update_readme_incremental.py -v`
Expected: FAIL if assumptions no longer match.

**Step 3: Write minimal implementation**
- Ensure discovery snapshot drives downloader input.
- Refresh README using the new discovery outputs.

**Step 4: Run test to verify it passes**
Run: `python3 -m unittest tests/test_download_papers.py tests/test_update_readme_incremental.py -v`
Expected: PASS.

### Task 6: Validate end-to-end rescan

**Files:**
- Modify if needed: `scripts/sop_validate.py`
- Modify if needed: `.cursor/skills/quarterly-llm-repo-refresh/reference.md`
- Modify if needed: `.cursor/skills/quarterly-llm-repo-refresh/examples.md`

**Step 1: Run full discovery**
Run: `python3 scripts/discover_models.py --until 2026-04-03 --output scripts/latest_models.json`
Expected: writes an industry-wide snapshot.

**Step 2: Run downloader and README refresh**
Run:
- `python3 download_papers.py --models-json scripts/latest_models.json --results-json scripts/latest_download_results.json`
- `python3 scripts/update_readme_incremental.py --results-json scripts/latest_download_results.json`
- `node scripts/render_readme_diagrams.mjs`

**Step 3: Run verification**
Run:
- `python3 -m unittest tests/test_download_papers.py tests/test_update_readme_incremental.py tests/test_discover_models.py tests/test_model_aliases.py tests/test_render_readme_diagrams.py`
- `python3 scripts/sop_validate.py`
- `bash .cursor/skills/quarterly-llm-repo-refresh/scripts/validate_skill.sh`

**Step 4: Review diff and commit intentionally**
Run: `git status --short && git diff -- README.md scripts/discover_models.py download_papers.py`
Expected: only intended discovery, README, test, and asset changes.
