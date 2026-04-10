#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../" && pwd)"

SKILL_MD="$SKILL_DIR/SKILL.md"
REFERENCE_MD="$SKILL_DIR/reference.md"
EXAMPLES_MD="$SKILL_DIR/examples.md"
VENDOR_SOURCES_MD="$SKILL_DIR/vendor_sources.md"
RUNTIME_DIR="$SKILL_DIR/runtime"
STATE_DIR="$SKILL_DIR/state"
README_UPDATER="$RUNTIME_DIR/update_readme_incremental.py"
DISCOVER_SCRIPT="$RUNTIME_DIR/discover_models.py"
BUILD_CURATED_SCRIPT="$RUNTIME_DIR/build_curated_models.py"
DOWNLOAD_SCRIPT="$RUNTIME_DIR/download_papers.py"
RENDER_SCRIPT="$RUNTIME_DIR/render_readme_diagrams.mjs"
SOP_VALIDATE_SCRIPT="$RUNTIME_DIR/sop_validate.py"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: missing SKILL.md"
  exit 1
fi
if [[ ! -f "$README_UPDATER" ]]; then
  echo "ERROR: missing README updater script $README_UPDATER"
  exit 1
fi
if [[ ! -f "$DISCOVER_SCRIPT" ]]; then
  echo "ERROR: missing discover script $DISCOVER_SCRIPT"
  exit 1
fi
if [[ ! -f "$BUILD_CURATED_SCRIPT" ]]; then
  echo "ERROR: missing curated builder script $BUILD_CURATED_SCRIPT"
  exit 1
fi
if [[ ! -f "$DOWNLOAD_SCRIPT" ]]; then
  echo "ERROR: missing download script $DOWNLOAD_SCRIPT"
  exit 1
fi
if [[ ! -f "$RENDER_SCRIPT" ]]; then
  echo "ERROR: missing diagram renderer $RENDER_SCRIPT"
  exit 1
fi
if [[ ! -f "$SOP_VALIDATE_SCRIPT" ]]; then
  echo "ERROR: missing SOP validator $SOP_VALIDATE_SCRIPT"
  exit 1
fi

python3 - <<'PY' "$SKILL_MD" "$REFERENCE_MD" "$EXAMPLES_MD" "$VENDOR_SOURCES_MD" "$SCRIPT_DIR/validate_skill.sh"
from pathlib import Path
import re
import sys

skill_md = Path(sys.argv[1])
reference_md = Path(sys.argv[2])
examples_md = Path(sys.argv[3])
vendor_sources_md = Path(sys.argv[4])
script_path = Path(sys.argv[5])
text = skill_md.read_text(encoding="utf-8")

if len(text.splitlines()) > 500:
    raise SystemExit("ERROR: SKILL.md exceeds 500 lines")

m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
if not m:
    raise SystemExit("ERROR: SKILL.md missing YAML frontmatter")
frontmatter = m.group(1)
for field in ["name:", "description:"]:
    if field not in frontmatter:
        raise SystemExit(f"ERROR: missing frontmatter field {field}")

for p in [reference_md, examples_md, vendor_sources_md, script_path]:
    if not p.exists():
        raise SystemExit(f"ERROR: missing supporting file {p}")

required_links = [
    "[reference.md](reference.md)",
    "[examples.md](examples.md)",
    "[vendor_sources.md](vendor_sources.md)",
    "[scripts/validate_skill.sh](scripts/validate_skill.sh)",
]
for link in required_links:
    if link not in text:
        raise SystemExit(f"ERROR: SKILL.md missing link {link}")

print("skill-structure-ok")
PY

cd "$REPO_ROOT"
TMP_DIR="$(mktemp -d /tmp/quarterly-skill-validate.XXXXXX)"
BACKUP_DIR="$(mktemp -d /tmp/quarterly-skill-backup.XXXXXX)"
trap 'rm -rf "$TMP_DIR" "$BACKUP_DIR"' EXIT

mkdir -p "$BACKUP_DIR/assets" "$BACKUP_DIR/state"
if [[ -d assets/diagrams ]]; then
  cp -R assets/diagrams "$BACKUP_DIR/assets/diagrams"
fi
if [[ -d "$STATE_DIR/generated" ]]; then
  cp -R "$STATE_DIR/generated" "$BACKUP_DIR/state/generated"
fi

cp README.md "$TMP_DIR/README.md"
cat > "$TMP_DIR/results.json" <<'JSON'
[
  {
    "release_date": "2026-02",
    "org": "OpenAI",
    "org_slug": "openai",
    "model": "GPT-5.3-Codex",
    "core_feature": "agentic coding model",
    "official_link": "https://cdn.openai.com/pdf/example.pdf",
    "local_file_path": "2026/openai/2026-02_gpt-5.3-codex.pdf"
  }
]
JSON
python3 "$README_UPDATER" \
  --readme "$TMP_DIR/README.md" \
  --results-json "$TMP_DIR/results.json"
python3 "$README_UPDATER" \
  --readme "$TMP_DIR/README.md" \
  --results-json "$TMP_DIR/results.json" \
  --from-scratch
node "$RENDER_SCRIPT"

rm -rf assets/diagrams "$STATE_DIR/generated"
if [[ -d "$BACKUP_DIR/assets/diagrams" ]]; then
  mkdir -p assets
  cp -R "$BACKUP_DIR/assets/diagrams" assets/diagrams
fi
if [[ -d "$BACKUP_DIR/state/generated" ]]; then
  mkdir -p "$STATE_DIR"
  cp -R "$BACKUP_DIR/state/generated" "$STATE_DIR/generated"
fi

python3 - <<'PY' "$RUNTIME_DIR" "$STATE_DIR" "$REPO_ROOT"
import json
import subprocess
import sys
import tempfile
from pathlib import Path

runtime_dir = Path(sys.argv[1])
state_dir = Path(sys.argv[2])
repo_root = Path(sys.argv[3])
sys.path.insert(0, str(runtime_dir))

import build_curated_models
import discover_models
import download_papers
import update_readme_incremental

required_vendor_slugs = {
    "meta",
    "google",
    "microsoft",
    "nvidia",
    "openai",
    "allenai",
    "ibm",
    "snowflake",
    "ai21",
    "alibaba_qwen",
    "deepseek",
    "bytedance",
    "baidu",
    "internlm",
    "zhipu",
    "openbmb",
    "inclusionai",
    "skywork",
    "tencent",
    "xiaomi",
    "moonshot",
    "minimax",
    "mistral",
    "huggingface",
}
missing_vendor_slugs = sorted(required_vendor_slugs - set(discover_models.VENDOR_REGISTRY))
if missing_vendor_slugs:
    raise SystemExit(f"ERROR: ATOM-backed vendor coverage regressed: {missing_vendor_slugs}")

resolved = discover_models.canonicalize_model_name("zhipu", "GLM 5V Flash")
if resolved.canonical_name != "GLM-5V-Turbo":
    raise SystemExit("ERROR: alias canonicalization regressed")

if not download_papers.should_render_webpage_to_pdf("https://qwen.ai/blog?id=qwen3.5"):
    raise SystemExit("ERROR: webpage-to-pdf rule regressed")

limited = build_curated_models.limit_links(
    [
        "https://fonts.googleapis.com/css2?family=Virgil",
        "https://qwen.ai/blog?id=qwen3.5",
        "https://arxiv.org/abs/2603.21065",
    ],
    filter_noise=True,
)
if any("fonts.googleapis.com" in url for url in limited):
    raise SystemExit("ERROR: noisy candidate-link filtering regressed")

with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    generated = tmp / "generated"
    assets = tmp / "assets"
    generated.mkdir()
    assets.mkdir()
    (generated / "monthly_density.json").write_text(
        json.dumps({"months": [{"month": "2026-02", "count": 2}, {"month": "2026-03", "count": 7}]}),
        encoding="utf-8",
    )
    (generated / "release_timeline.json").write_text(
        json.dumps(
            {
                "months": ["2026-02", "2026-03"],
                "lanes": [
                    {
                        "id": "china",
                        "label": "China-based Labs",
                        "camp": "china",
                        "entries": [
                            {
                                "month": "2026-02",
                                "models": ["GLM-5", "Qwen 3.5", "Qwen3-Coder-Next", "LongCat-Flash-Thinking-2601"],
                                "highlighted_models": ["GLM-5"],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "node",
            str(runtime_dir / "render_readme_diagrams.mjs"),
            "--generated-dir",
            str(generated),
            "--assets-dir",
            str(assets),
        ],
        check=True,
        cwd=repo_root,
    )
    svg = (assets / "release-timeline.svg").read_text(encoding="utf-8")
    if 'data-card-width="' not in svg or 'data-max-line-width="' not in svg:
        raise SystemExit("ERROR: timeline SVG metadata missing")

print("skill-smoke-ok")
PY
python3 "$SOP_VALIDATE_SCRIPT"

python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    b.close()
print("playwright-ready")
PY

echo "skill-validation-ok"
