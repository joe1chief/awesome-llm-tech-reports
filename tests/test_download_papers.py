import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from llm_papers import download_papers


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


if __name__ == "__main__":
    unittest.main()
