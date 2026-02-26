#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../" && pwd)"

SKILL_MD="$SKILL_DIR/SKILL.md"
REFERENCE_MD="$SKILL_DIR/reference.md"
EXAMPLES_MD="$SKILL_DIR/examples.md"

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: missing SKILL.md"
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
python3 scripts/sop_validate.py
python3 -m unittest tests/test_download_papers.py

python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    b.close()
print("playwright-ready")
PY

echo "skill-validation-ok"
