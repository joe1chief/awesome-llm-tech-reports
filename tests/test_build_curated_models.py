import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import build_curated_models


class BuildCuratedModelsTests(unittest.TestCase):
    def test_curated_snapshot_preserves_readme_boundary_and_overlays_discovery(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            readme = root / "README.md"
            discover_json = root / "latest_models.json"
            readme.write_text(
                "\n".join(
                    [
                        "| Release Date | Organization | Model | Core Highlights | Official Link | Local File |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| 2025-04 | OpenAI | o3 / o4-mini | Existing summary. | https://old.example/o3 | 2025/openai/o3.pdf |",
                        "| 2026-02 | Google | Gemini 3.1 Pro | Existing gemini summary. | https://old.example/g31 | 2026/google/g31.pdf |",
                    ]
                ),
                encoding="utf-8",
            )
            discover_json.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2024-03",
                            "org": "OpenAI",
                            "org_slug": "openai",
                            "model": "o3 / o4-mini",
                            "aliases": ["OpenAI o3 and o4-mini"],
                            "core_feature": "",
                            "official_link": "https://cdn.openai.com/pdf/o3.pdf",
                            "candidate_links": [f"https://example.com/o3/{idx}" for idx in range(40)],
                            "source_page": "https://openai.com/index/introducing-o3-and-o4-mini/",
                            "evidence_urls": ["https://openai.com/index/introducing-o3-and-o4-mini/"],
                            "evidence_type": "official_pdf",
                            "release_classification": "model_release",
                            "classification_reason": "openai_reasoning_release",
                            "confidence": 0.95,
                            "discovered_at": "2026-04-03T12:00:00Z",
                        },
                        {
                            "release_date": "2026-02",
                            "org": "Google",
                            "org_slug": "google",
                            "model": "Gemini 3.1 Pro",
                            "aliases": ["Gemini 3.1 Pro model card"],
                            "core_feature": "",
                            "official_link": "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Pro-Model-Card.pdf",
                            "candidate_links": ["https://deepmind.google/models/model-cards/gemini-3-1-pro/"],
                            "source_page": "https://deepmind.google/models/model-cards/gemini-3-1-pro/",
                            "evidence_urls": ["https://deepmind.google/models/model-cards/"],
                            "evidence_type": "official_pdf",
                            "release_classification": "model_release",
                            "classification_reason": "google_frontier_release",
                            "confidence": 0.9,
                            "discovered_at": "2026-04-03T12:00:00Z",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            curated = build_curated_models.build_curated_models(
                readme_path=readme,
                discovered_models_path=discover_json,
            )

        self.assertEqual(len(curated), 2)
        by_model = {item["model"]: item for item in curated}
        self.assertEqual(by_model["o3 / o4-mini"]["release_date"], "2025-04")
        self.assertEqual(
            by_model["o3 / o4-mini"]["official_link"],
            "https://cdn.openai.com/pdf/o3.pdf",
        )
        self.assertLessEqual(len(by_model["o3 / o4-mini"]["candidate_links"]), 12)
        self.assertNotIn("https://example.com/o3/0", by_model["o3 / o4-mini"]["candidate_links"])
        self.assertEqual(
            by_model["Gemini 3.1 Pro"]["official_link"],
            "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Pro-Model-Card.pdf",
        )

    def test_curated_snapshot_matches_discovery_by_alias_but_keeps_readme_name(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            readme = root / "README.md"
            discover_json = root / "latest_models.json"
            readme.write_text(
                "\n".join(
                    [
                        "| Release Date | Organization | Model | Core Highlights | Official Link | Local File |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| 2026-02 | Alibaba | Qwen3-Coder-Next | Existing summary. | https://old.example/qwen | 2026/alibaba_qwen/qwen.pdf |",
                    ]
                ),
                encoding="utf-8",
            )
            discover_json.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2026-02",
                            "org": "Alibaba",
                            "org_slug": "alibaba_qwen",
                            "model": "Qwen3-Coder",
                            "aliases": ["Qwen3-Coder-Next"],
                            "core_feature": "",
                            "official_link": "https://github.com/QwenLM/Qwen3-Coder/blob/main/qwen3_coder_next_tech_report.pdf",
                            "candidate_links": ["https://github.com/QwenLM/Qwen3-Coder"],
                            "source_page": "https://github.com/QwenLM/Qwen3-Coder",
                            "evidence_urls": ["https://github.com/QwenLM/Qwen3-Coder"],
                            "evidence_type": "official_repo_pdf",
                            "release_classification": "model_release",
                            "classification_reason": "qwen_frontier_release",
                            "confidence": 0.92,
                            "discovered_at": "2026-04-03T12:00:00Z",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            curated = build_curated_models.build_curated_models(
                readme_path=readme,
                discovered_models_path=discover_json,
            )

        self.assertEqual(len(curated), 1)
        self.assertEqual(curated[0]["model"], "Qwen3-Coder-Next")
        self.assertEqual(
            curated[0]["official_link"],
            "https://github.com/QwenLM/Qwen3-Coder/blob/main/qwen3_coder_next_tech_report.pdf",
        )
        self.assertIn("Qwen3-Coder", curated[0]["aliases"])

    def test_curated_snapshot_adds_xai_release_notes_fallback(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            readme = root / "README.md"
            discover_json = root / "latest_models.json"
            readme.write_text(
                "\n".join(
                    [
                        "| Release Date | Organization | Model | Core Highlights | Official Link | Local File |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| 2025-11 | xAI | Grok 4.1 | Existing summary. | https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf | 2025/xai/grok41.pdf |",
                    ]
                ),
                encoding="utf-8",
            )
            discover_json.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2025-11",
                            "org": "xAI",
                            "org_slug": "xai",
                            "model": "Grok 4.1",
                            "aliases": [],
                            "core_feature": "",
                            "official_link": "https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf",
                            "candidate_links": ["https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf"],
                            "source_page": "https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf",
                            "evidence_urls": [],
                            "evidence_type": "official_pdf",
                            "release_classification": "model_release",
                            "classification_reason": "xai_frontier_release",
                            "confidence": 0.95,
                            "discovered_at": "2026-04-03T12:00:00Z",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            curated = build_curated_models.build_curated_models(
                readme_path=readme,
                discovered_models_path=discover_json,
            )

        self.assertIn("https://docs.x.ai/docs/release-notes", curated[0]["candidate_links"])
        self.assertEqual(curated[0]["source_page"], "https://docs.x.ai/docs/release-notes")

    def test_curated_snapshot_filters_static_asset_links(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            readme = root / "README.md"
            discover_json = root / "latest_models.json"
            readme.write_text(
                "\n".join(
                    [
                        "| Release Date | Organization | Model | Core Highlights | Official Link | Local File |",
                        "| --- | --- | --- | --- | --- | --- |",
                        "| 2026-03 | OpenAI | GPT-5.4 Thinking | Existing summary. | https://old.example/gpt54 | 2026/openai/gpt54.pdf |",
                    ]
                ),
                encoding="utf-8",
            )
            discover_json.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2026-03",
                            "org": "OpenAI",
                            "org_slug": "openai",
                            "model": "GPT-5.4 Thinking",
                            "aliases": [],
                            "core_feature": "",
                            "official_link": "https://deploymentsafety.openai.com/gpt-5-4-thinking/gpt-5-4-thinking.pdf",
                            "candidate_links": [
                                "https://deploymentsafety.openai.com/gpt-5-4-thinking",
                                "https://deploymentsafety.openai.com/favicon.svg",
                                "https://deploymentsafety.openai.com/posts.xml",
                                "https://fonts.googleapis.com/css2?family=Google+Sans",
                                "https://deploymentsafety.openai.com/_astro/app.css",
                            ],
                            "source_page": "https://deploymentsafety.openai.com/gpt-5-4-thinking",
                            "evidence_urls": ["https://deploymentsafety.openai.com/sitemap.xml"],
                            "evidence_type": "official_pdf",
                            "release_classification": "model_release",
                            "classification_reason": "openai_reasoning_release",
                            "confidence": 0.95,
                            "discovered_at": "2026-04-03T12:00:00Z",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            curated = build_curated_models.build_curated_models(
                readme_path=readme,
                discovered_models_path=discover_json,
            )

        self.assertEqual(
            curated[0]["candidate_links"],
            [
                "https://deploymentsafety.openai.com/gpt-5-4-thinking/gpt-5-4-thinking.pdf",
                "https://old.example/gpt54",
                "https://deploymentsafety.openai.com/gpt-5-4-thinking",
            ],
        )
