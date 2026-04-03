#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../" && pwd)"

SKILL_MD="$SKILL_DIR/SKILL.md"
REFERENCE_MD="$SKILL_DIR/reference.md"
EXAMPLES_MD="$SKILL_DIR/examples.md"
README_UPDATER="$REPO_ROOT/scripts/update_readme_incremental.py"
DISCOVER_SCRIPT="$REPO_ROOT/scripts/discover_models.py"
BUILD_CURATED_SCRIPT="$REPO_ROOT/scripts/build_curated_models.py"
RENDER_SCRIPT="$REPO_ROOT/scripts/render_readme_diagrams.mjs"

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
if [[ ! -f "$RENDER_SCRIPT" ]]; then
  echo "ERROR: missing diagram renderer $RENDER_SCRIPT"
  exit 1
fi

python3 - <<'PY' "$SKILL_MD" "$REFERENCE_MD" "$EXAMPLES_MD" "$SCRIPT_DIR/validate_skill.sh"
from pathlib import Path
import re
import sys

skill_md = Path(sys.argv[1])
reference_md = Path(sys.argv[2])
examples_md = Path(sys.argv[3])
script_path = Path(sys.argv[4])
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

for p in [reference_md, examples_md, script_path]:
    if not p.exists():
        raise SystemExit(f"ERROR: missing supporting file {p}")

required_links = [
    "[reference.md](reference.md)",
    "[examples.md](examples.md)",
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

mkdir -p "$BACKUP_DIR/assets" "$BACKUP_DIR/scripts"
if [[ -d assets/diagrams ]]; then
  cp -R assets/diagrams "$BACKUP_DIR/assets/diagrams"
fi
if [[ -d scripts/generated ]]; then
  cp -R scripts/generated "$BACKUP_DIR/scripts/generated"
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
python3 scripts/update_readme_incremental.py \
  --readme "$TMP_DIR/README.md" \
  --results-json "$TMP_DIR/results.json"
python3 scripts/update_readme_incremental.py \
  --readme "$TMP_DIR/README.md" \
  --results-json "$TMP_DIR/results.json" \
  --from-scratch
node scripts/render_readme_diagrams.mjs

rm -rf assets/diagrams scripts/generated
if [[ -d "$BACKUP_DIR/assets/diagrams" ]]; then
  mkdir -p assets
  cp -R "$BACKUP_DIR/assets/diagrams" assets/diagrams
fi
if [[ -d "$BACKUP_DIR/scripts/generated" ]]; then
  mkdir -p scripts
  cp -R "$BACKUP_DIR/scripts/generated" scripts/generated
fi

python3 -m unittest \
  tests/test_build_curated_models.py \
  tests/test_download_papers.py \
  tests/test_update_readme_incremental.py \
  tests/test_discover_models.py \
  tests/test_model_aliases.py \
  tests/test_render_readme_diagrams.py
python3 scripts/sop_validate.py

python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    b.close()
print("playwright-ready")
PY

echo "skill-validation-ok"
