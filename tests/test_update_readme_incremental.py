import unittest

from scripts import update_readme_incremental as updater


class UpdateReadmeIncrementalTests(unittest.TestCase):
    def test_merge_rows_incremental_appends_new(self) -> None:
        existing = [
            {
                "release_date": "2025-01",
                "organization": "DeepSeek",
                "model": "DeepSeek R1",
                "core_highlights": "existing",
                "official_link": "https://arxiv.org/pdf/2501.12948",
                "local_file": "2025/deepseek/2025-01_deepseek-r1.pdf",
            }
        ]
        run_rows = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "GPT-5.3-Codex",
                "core_highlights": "new row",
                "official_link": "https://cdn.openai.com/pdf/example.pdf",
                "local_file": "2026/openai/2026-02_gpt-5.3-codex.pdf",
            }
        ]
        merged = updater.merge_rows(existing, run_rows, from_scratch=False)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["release_date"], "2026-02")

    def test_merge_rows_keeps_existing_order(self) -> None:
        existing = [
            {
                "release_date": "2026-02",
                "organization": "A",
                "model": "Model A",
                "core_highlights": "a",
                "official_link": "a",
                "local_file": "a.pdf",
            },
            {
                "release_date": "2026-02",
                "organization": "B",
                "model": "Model B",
                "core_highlights": "b",
                "official_link": "b",
                "local_file": "b.pdf",
            },
        ]
        run_rows = [
            {
                "release_date": "2026-02",
                "organization": "C",
                "model": "Model C",
                "core_highlights": "c",
                "official_link": "c",
                "local_file": "c.pdf",
            }
        ]
        merged = updater.merge_rows(existing, run_rows, from_scratch=False)
        self.assertEqual([r["model"] for r in merged], ["Model A", "Model B", "Model C"])

    def test_merge_rows_from_scratch_discards_existing(self) -> None:
        existing = [
            {
                "release_date": "2025-01",
                "organization": "DeepSeek",
                "model": "DeepSeek R1",
                "core_highlights": "existing",
                "official_link": "x",
                "local_file": "x",
            }
        ]
        run_rows = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "GPT-5.3-Codex",
                "core_highlights": "new row",
                "official_link": "y",
                "local_file": "y",
            }
        ]
        merged = updater.merge_rows(existing, run_rows, from_scratch=True)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["model"], "GPT-5.3-Codex")

    def test_merge_rows_from_scratch_reuses_existing_english_highlight(self) -> None:
        existing = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "GPT-X",
                "core_highlights": "english summary",
                "official_link": "a",
                "local_file": "a.pdf",
            }
        ]
        run_rows = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "GPT-X",
                "core_highlights": "中文摘要",
                "official_link": "a",
                "local_file": "a.pdf",
            }
        ]
        merged = updater.merge_rows(existing, run_rows, from_scratch=True)
        self.assertEqual(merged[0]["core_highlights"], "english summary")

    def test_snapshot_uses_dynamic_bubble_class(self) -> None:
        rows = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "A",
                "core_highlights": "a",
                "official_link": "a",
                "local_file": "a.pdf",
            }
            for _ in range(7)
        ]
        block = updater.build_snapshot_details(rows)
        self.assertIn("classDef b7", block)
        self.assertIn("R07", block)

    def test_snapshot_reuses_existing_class_def_style(self) -> None:
        text = """
<details>
<summary><b>Monthly Density Snapshot</b></summary>

```mermaid
flowchart LR
  classDef b7 fill:#111111,stroke:#222222,stroke-width:6px,color:#ffffff,font-size:24px;
```
</details>
"""
        defs = updater.parse_existing_snapshot_classdefs(text)
        block = updater.build_snapshot_details(
            [
                {
                    "release_date": "2026-02",
                    "organization": "OpenAI",
                    "model": "A",
                    "core_highlights": "a",
                    "official_link": "a",
                    "local_file": "a.pdf",
                }
                for _ in range(7)
            ],
            existing_defs=defs,
        )
        self.assertIn("classDef b7 fill:#111111,stroke:#222222,stroke-width:6px,color:#ffffff,font-size:24px;", block)

    def test_render_updated_readme_replaces_model_index(self) -> None:
        readme = """# Awesome LLM Technical Reports (2025-01 ~ 2026-02)

## Model Index (Folded by Year)

<details open>
<summary><b>2026 (0 models)</b></summary>

| Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File |
| --- | --- | --- | --- | --- | --- |

</details>

## Star History
"""
        rows = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "GPT-5.3-Codex",
                "core_highlights": "from pdf",
                "official_link": "https://cdn.openai.com/pdf/example.pdf",
                "local_file": "2026/openai/2026-02_gpt-5.3-codex.pdf",
            }
        ]
        out = updater.render_updated_readme(readme, rows)
        self.assertIn("2026 (1 models)", out)
        self.assertIn("GPT-5.3-Codex", out)
        self.assertIn("\n\n## Star History", out)

    def test_model_index_keeps_input_order_within_year(self) -> None:
        rows = [
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "Model B",
                "core_highlights": "b",
                "official_link": "b",
                "local_file": "b.pdf",
            },
            {
                "release_date": "2026-02",
                "organization": "OpenAI",
                "model": "Model A",
                "core_highlights": "a",
                "official_link": "a",
                "local_file": "a.pdf",
            },
        ]
        section = updater.generate_model_index_section(rows)
        self.assertLess(section.find("Model B"), section.find("Model A"))


if __name__ == "__main__":
    unittest.main()
