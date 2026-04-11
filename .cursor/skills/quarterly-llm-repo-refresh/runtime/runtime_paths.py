from pathlib import Path


RUNTIME_DIR = Path(__file__).resolve().parent
SKILL_DIR = RUNTIME_DIR.parent
ROOT = SKILL_DIR.parents[2]

STATE_DIR = SKILL_DIR / "state"
GENERATED_DIR = STATE_DIR / "generated"

README = ROOT / "README.md"
ALIASES_JSON = RUNTIME_DIR / "model_aliases.json"
LATEST_MODELS_JSON = STATE_DIR / "latest_models.json"
LATEST_CURATED_MODELS_JSON = STATE_DIR / "latest_models_curated.json"
LATEST_RESULTS_JSON = STATE_DIR / "latest_download_results.json"

ASSETS_DIR = ROOT / "assets" / "diagrams"
PDF_DIR = ROOT / "pdf"
