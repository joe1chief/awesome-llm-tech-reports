import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json

try:
    from llm_papers import download_papers
except ModuleNotFoundError:  # pragma: no cover - local fallback
    import download_papers


class DownloadPapersTests(unittest.TestCase):
    def test_runtime_models_prefer_curated_snapshot_when_present(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            curated_models = root / "scripts" / "latest_models_curated.json"
            discovered_models = root / "scripts" / "latest_models.json"
            curated_models.parent.mkdir(parents=True, exist_ok=True)
            curated_models.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2025-04",
                            "org": "OpenAI",
                            "org_slug": "openai",
                            "model": "o3 / o4-mini",
                            "core_feature": "",
                            "official_link": "https://cdn.openai.com/pdf/o3.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            discovered_models.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2026-04",
                            "org": "Zhipu AI",
                            "org_slug": "zhipu",
                            "model": "GLM-5V-Turbo",
                            "core_feature": "",
                            "official_link": "https://docs.z.ai/guides/vlm/glm-5v-turbo",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            models = download_papers.load_runtime_models(root=root)

        self.assertEqual([item["model"] for item in models], ["o3 / o4-mini"])

    def test_runtime_models_attempt_discovery_when_snapshot_missing(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with patch.object(
                download_papers,
                "refresh_discovered_models_snapshot",
                return_value=[
                    {
                        "release_date": "2026-04",
                        "org": "Zhipu AI",
                        "org_slug": "zhipu",
                        "model": "GLM-5V-Turbo",
                        "core_feature": "",
                        "official_link": "https://docs.z.ai/guides/vlm/glm-5v-turbo",
                    }
                ],
            ) as mocked_refresh:
                models = download_papers.load_runtime_models(root=root)
            mocked_refresh.assert_called_once()
            self.assertIn("GLM-5V-Turbo", [item["model"] for item in models])

    def test_runtime_models_prefer_discovered_snapshot_when_present(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            latest_models = root / "scripts" / "latest_models.json"
            latest_models.parent.mkdir(parents=True, exist_ok=True)
            latest_models.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2026-03",
                            "org": "Meituan",
                            "org_slug": "meituan",
                            "model": "LongCat-Flash-Prover",
                            "core_feature": "",
                            "official_link": "https://arxiv.org/pdf/2603.21065",
                            "release_classification": "model_release",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            models = download_papers.load_runtime_models(root=root)
            self.assertIn("LongCat-Flash-Prover", [item["model"] for item in models])

    def test_should_render_webpage_to_pdf_for_blog_links(self) -> None:
        self.assertTrue(
            download_papers.should_render_webpage_to_pdf("https://qwen.ai/blog?id=qwen3.5")
        )
        self.assertTrue(
            download_papers.should_render_webpage_to_pdf("https://github.com/MiniMax-AI/MiniMax-M2")
        )

    def test_should_not_render_pdf_links_as_webpage(self) -> None:
        self.assertFalse(
            download_papers.should_render_webpage_to_pdf("https://arxiv.org/pdf/2505.09388")
        )
        self.assertFalse(
            download_papers.should_render_webpage_to_pdf(
                "https://cdn.openai.com/pdf/8124a3ce-ab78-4f06-96eb-49ea29ffb52f/gpt5-system-card-aug7.pdf"
            )
        )

    def test_has_pdf_signature_detects_magic_header(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ok.pdf"
            path.write_bytes(b"%PDF-1.7\nfoo")
            self.assertTrue(download_papers.has_pdf_signature(path))

    def test_has_pdf_signature_rejects_non_pdf(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.bin"
            path.write_bytes(b"not-a-pdf")
            self.assertFalse(download_papers.has_pdf_signature(path))

    def test_extract_text_length_from_pdf_returns_zero_for_missing_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.pdf"
            self.assertEqual(download_papers.extract_text_length_from_pdf(path), 0)

    def test_extract_arxiv_id_from_abs_and_pdf_links(self) -> None:
        self.assertEqual(
            download_papers.extract_arxiv_id("https://arxiv.org/abs/2511.00279"),
            "2511.00279",
        )
        self.assertEqual(
            download_papers.extract_arxiv_id("https://arxiv.org/pdf/2510.26692v2"),
            "2510.26692",
        )
        self.assertIsNone(download_papers.extract_arxiv_id("https://example.com/a.pdf"))

    def test_extract_year_month_from_url_supports_multiple_formats(self) -> None:
        self.assertEqual(
            download_papers.extract_year_month_from_url(
                "https://data.x.ai/2025-08-20-grok-4-model-card.pdf"
            ),
            "2025-08",
        )
        self.assertEqual(
            download_papers.extract_year_month_from_url("https://foo.bar/release/2026/2/16"),
            "2026-02",
        )
        self.assertIsNone(download_papers.extract_year_month_from_url("https://foo.bar/no-date"))

    def test_resolve_release_month_keeps_manual_for_shared_link(self) -> None:
        with patch.object(
            download_papers,
            "infer_release_month_from_source",
            return_value=("2025-08", "url_pattern"),
        ):
            month, source = download_papers.resolve_release_month(
                session=download_papers.build_session(),
                declared_release_date="2025-07",
                url="https://arxiv.org/pdf/2412.19437",
                link_frequency={"https://arxiv.org/pdf/2412.19437": 2},
                cache={},
            )
        self.assertEqual(month, "2025-07")
        self.assertEqual(source, "manual_shared_link")

    def test_resolve_release_month_keeps_declared_for_xai_release_notes(self) -> None:
        month, source = download_papers.resolve_release_month(
            session=download_papers.build_session(),
            declared_release_date="2025-08",
            url="https://docs.x.ai/docs/release-notes",
            link_frequency={},
            cache={},
        )
        self.assertEqual(month, "2025-08")
        self.assertEqual(source, "manual_xai_release_notes")

    def test_fetch_webpage_published_month_prefers_visible_header_date(self) -> None:
        class FakeResponse:
            text = """
            <html>
              <head>
                <script type="application/ld+json">
                  {"datePublished":"2026-04-01"}
                </script>
              </head>
              <body>
                <nav>Models News Company</nav>
                <div>2026.2.12</div>
                <h1>MiniMax M2.5: Built for Real-World Productivity.</h1>
              </body>
            </html>
            """

            def raise_for_status(self) -> None:
                return None

        class FakeSession:
            def get(self, url: str, timeout: int = 20) -> FakeResponse:
                return FakeResponse()

        self.assertEqual(
            download_papers.fetch_webpage_published_month(
                FakeSession(), "https://www.minimax.io/news/minimax-m25"
            ),
            "2026-02",
        )

    def test_source_priority_prefers_pdf_over_blog(self) -> None:
        self.assertGreater(
            download_papers.source_priority_score("https://arxiv.org/pdf/2505.09388"),
            download_papers.source_priority_score("https://qwen.ai/blog?id=qwen3.5"),
        )

    def test_choose_best_source_url_prefers_available_candidate(self) -> None:
        record = {
            "official_link": "https://qwen.ai/blog?id=qwen3.5",
            "candidate_links": [
                "https://qwen.ai/blog?id=qwen3.5",
                "https://arxiv.org/abs/2505.09388",
            ],
        }
        with patch.object(
            download_papers,
            "probe_source_url",
            side_effect=[(False, "renderer_unavailable"), (True, "pdf_content_type")],
        ):
            url, reason = download_papers.choose_best_source_url(
                download_papers.build_session(), record, {}
            )
        self.assertEqual(url, "https://arxiv.org/pdf/2505.09388")
        self.assertIn("probe_ok", reason)

    def test_choose_best_source_url_short_circuits_on_valid_official_pdf(self) -> None:
        record = {
            "official_link": "https://cdn.openai.com/pdf/example.pdf",
            "candidate_links": [
                "https://cdn.openai.com/pdf/example.pdf",
                "https://example.com/fallback",
            ],
        }
        with patch.object(
            download_papers,
            "probe_source_url",
            return_value=(True, "pdf_content_type"),
        ) as mocked_probe:
            url, reason = download_papers.choose_best_source_url(
                download_papers.build_session(), record, {}
            )
        self.assertEqual(url, "https://cdn.openai.com/pdf/example.pdf")
        self.assertIn("|early", reason)
        mocked_probe.assert_called_once()

    def test_collect_candidate_links_caps_noisy_candidate_lists(self) -> None:
        record = {
            "official_link": "https://cdn.openai.com/pdf/example.pdf",
            "candidate_links": [f"https://example.com/{idx}" for idx in range(30)],
        }
        candidates = download_papers.collect_candidate_links(record)
        self.assertEqual(candidates, ["https://cdn.openai.com/pdf/example.pdf"])

    def test_collect_candidate_links_filters_static_assets(self) -> None:
        record = {
            "official_link": "https://cdn.openai.com/pdf/example.pdf",
            "source_page": "https://deploymentsafety.openai.com/gpt-5-4-thinking",
            "candidate_links": [
                "https://deploymentsafety.openai.com/gpt-5-4-thinking",
                "https://deploymentsafety.openai.com/favicon.svg",
                "https://fonts.googleapis.com/css2?family=Google+Sans",
                "https://deploymentsafety.openai.com/_astro/app.css",
                "https://deploymentsafety.openai.com/gpt-5-4-thinking#main",
            ],
        }
        candidates = download_papers.collect_candidate_links(record)
        self.assertEqual(
            candidates,
            [
                "https://cdn.openai.com/pdf/example.pdf",
                "https://deploymentsafety.openai.com/gpt-5-4-thinking",
            ],
        )

    def test_load_models_from_json_accepts_runtime_snapshot(self) -> None:
        with TemporaryDirectory() as tmpdir:
            models_path = Path(tmpdir) / "models.json"
            models_path.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2026-02",
                            "org": "OpenAI",
                            "org_slug": "openai",
                            "model": "GPT-X",
                            "core_feature": "runtime generated",
                            "official_link": "https://cdn.openai.com/pdf/example.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            models = download_papers.load_models_from_json(models_path)
            self.assertEqual(len(models), 1)
            self.assertEqual(models[0]["model"], "GPT-X")

    def test_load_models_from_json_filters_non_release_records(self) -> None:
        with TemporaryDirectory() as tmpdir:
            models_path = Path(tmpdir) / "models.json"
            models_path.write_text(
                json.dumps(
                    [
                        {
                            "release_date": "2026-03",
                            "org": "Google",
                            "org_slug": "google",
                            "model": "Gemma 4",
                            "core_feature": "",
                            "official_link": "https://example.com/gemma4.pdf",
                            "release_classification": "model_release",
                        },
                        {
                            "release_date": "2026-03",
                            "org": "Google",
                            "org_slug": "google",
                            "model": "ShieldGemma 2",
                            "core_feature": "",
                            "official_link": "https://example.com/shieldgemma2.pdf",
                            "release_classification": "exclude_tool_model",
                        },
                    ]
                ),
                encoding="utf-8",
            )
            models = download_papers.load_models_from_json(models_path)
            self.assertEqual([item["model"] for item in models], ["Gemma 4"])

    def test_summarize_core_feature_from_text_extracts_english_highlights(self) -> None:
        summary = download_papers.summarize_core_feature_from_text(
            """
            Abstract
            LongCat-Flash-Prover is a formal-reasoning model built for theorem proving.
            It introduces verifier-guided reinforcement learning, specialized proof search,
            and stronger tool use for mathematical reasoning across long trajectories.
            """,
            model_name="LongCat-Flash-Prover",
        )
        self.assertIn("formal-reasoning model", summary)
        self.assertIn("verifier-guided reinforcement learning", summary)

    def test_choose_best_generated_summary_prefers_technical_summary_over_page_title(self) -> None:
        summary = download_papers.choose_best_generated_summary(
            "MiniMax M2.7: Early Echoes of Self-Evolution - MiniMax News",
            (
                "M2.7 is our first model deeply participating in its own evolution. "
                "M2.7 is capable of building complex agent harnesses and completing "
                "highly elaborate productivity tasks."
            ),
            model_name="MiniMax M2.7",
        )
        self.assertIn("participating in its own evolution", summary)
        self.assertNotIn("News", summary)


if __name__ == "__main__":
    unittest.main()
