import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / ".cursor" / "skills" / "quarterly-llm-repo-refresh" / "runtime"

if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

import build_curated_models  # noqa: E402
import discover_models  # noqa: E402
import download_papers  # noqa: E402
import update_readme_incremental  # noqa: E402
