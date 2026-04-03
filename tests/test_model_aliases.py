import unittest

from scripts import discover_models


class ModelAliasTests(unittest.TestCase):
    def test_glm_5v_flash_alias_resolves_to_glm_5v_turbo(self) -> None:
        resolved = discover_models.canonicalize_model_name("zhipu", "GLM 5V Flash")
        self.assertEqual(resolved.canonical_name, "GLM-5V-Turbo")
        self.assertIn("GLM 5V Flash", resolved.aliases)

    def test_qwen3_coder_next_alias_resolves_to_qwen3_coder(self) -> None:
        resolved = discover_models.canonicalize_model_name("alibaba_qwen", "Qwen3-Coder-Next")
        self.assertEqual(resolved.canonical_name, "Qwen3-Coder")
        self.assertIn("Qwen3-Coder-Next", resolved.aliases)

    def test_qwen3_max_alias_normalizes_spacing(self) -> None:
        resolved = discover_models.canonicalize_model_name("alibaba_qwen", "Qwen 3 Max")
        self.assertEqual(resolved.canonical_name, "Qwen3-Max")
        self.assertIn("Qwen 3 Max", resolved.aliases)

    def test_longcat_aliases_normalize_to_single_canonical_name(self) -> None:
        resolved = discover_models.canonicalize_model_name(
            "meituan",
            "LongCat Flash Prover",
        )
        self.assertEqual(resolved.canonical_name, "LongCat-Flash-Prover")
        self.assertIn("LongCat Flash Prover", resolved.aliases)

    def test_minimax_m2_alias_resolves_to_existing_m2_0_name(self) -> None:
        resolved = discover_models.canonicalize_model_name("minimax", "MiniMax M2")
        self.assertEqual(resolved.canonical_name, "MiniMax M2.0")
        self.assertIn("MiniMax M2", resolved.aliases)

    def test_google_gemma_nbsp_alias_normalizes_cleanly(self) -> None:
        resolved = discover_models.canonicalize_model_name("google", "Gemma 3 &Nbsp;")
        self.assertEqual(resolved.canonical_name, "Gemma 3")
        self.assertIn("Gemma 3 &Nbsp;", resolved.aliases)


if __name__ == "__main__":
    unittest.main()
