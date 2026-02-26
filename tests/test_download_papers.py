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


if __name__ == "__main__":
    unittest.main()
