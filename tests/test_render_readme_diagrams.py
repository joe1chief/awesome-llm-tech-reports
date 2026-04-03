import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".cursor" / "skills" / "quarterly-llm-repo-refresh" / "runtime" / "render_readme_diagrams.mjs"


class RenderReadmeDiagramsTests(unittest.TestCase):
    def test_render_script_emits_wrapped_svg_assets_only(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            generated = tmp / "generated"
            assets = tmp / "assets"
            generated.mkdir()
            assets.mkdir()

            (generated / "monthly_density.json").write_text(
                json.dumps(
                    {
                        "months": [
                            {"month": "2026-02", "count": 2},
                            {"month": "2026-03", "count": 7},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (generated / "release_timeline.json").write_text(
                json.dumps(
                    {
                        "months": ["2026-02", "2026-03"],
                        "lanes": [
                            {
                                "id": "google",
                                "label": "Google",
                                "camp": "google",
                                "entries": [
                                    {
                                        "month": "2026-03",
                                        "models": ["LongCat-Flash-Thinking-2601", "MedGemma 1.5"],
                                        "highlighted_models": ["Gemma 4"],
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
                    str(SCRIPT),
                    "--generated-dir",
                    str(generated),
                    "--assets-dir",
                    str(assets),
                ],
                check=True,
                cwd=ROOT,
            )

            monthly_svg = (assets / "monthly-density.svg").read_text(encoding="utf-8")
            timeline_svg = (assets / "release-timeline.svg").read_text(encoding="utf-8")

            self.assertIn('data-count="7"', monthly_svg)
            self.assertIn("LongCat-", timeline_svg)
            self.assertIn("<tspan", timeline_svg)
            self.assertFalse((assets / "monthly-density.excalidraw").exists())
            self.assertFalse((assets / "release-timeline.excalidraw").exists())


if __name__ == "__main__":
    unittest.main()
