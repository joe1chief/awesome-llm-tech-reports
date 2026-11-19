import pytest

from parse_readme import extract_tags


@pytest.mark.parametrize("summary", [
    "The post-trained preview has 280B total and 14B active parameters, with a 1M-token context.",
    "It has 280B total parameters with 14B active and a 1M-token context.",
    "ERNIE 5.5 Flash Preview has 280B total parameters, 14B active and a 1M-token context.",
])
def test_moe_tag_survives_parameter_summary_rewording(summary):
    assert "MoE" in extract_tags("ERNIE 5.5 Flash Preview", summary, "https://ernie.baidu.com/")


@pytest.mark.parametrize("summary", [
    "A dense 14B model with an active community.",
    "280B total tokens and 14B active users.",
    "Trained on 280B total tokens, with 14B active at launch.",
    "280B total parameters and 14B active users.",
])
def test_moe_tag_does_not_infer_from_unrelated_counts(summary):
    assert "MoE" not in extract_tags("Example model", summary, "https://example.com/")
