from __future__ import annotations

import json
import re
from decimal import Decimal

from report_catalog import https_url, slug

TOTAL_IN_NAME = re.compile(
    r"(?<![A-Za-z0-9.])(\d+(?:\.\d+)?)([BT])(?![A-Za-z0-9]|[-_ ]+(?:active|activated)\b)",
    re.I,
)
PACKED_WEIGHTS = re.compile(
    r"(?:^|[-_. ])(?:awq|gptq|gguf|nvfp4|mxfp4|w\d+a\d+|int[248]|[248]bit|mlx)(?=$|[-_. ])",
    re.I,
)
FLOAT_DTYPES = {"F16", "BF16", "F32", "F64", "F8_E4M3", "F8_E5M2"}


def configure_parameters(settings, path):
    if not path.is_file():
        return
    policy = json.loads(path.read_text())
    minimum = policy["minimum_total_parameters"]
    if type(minimum) is not int or minimum < 0:
        raise ValueError("minimum_total_parameters must be a nonnegative integer")
    for config in settings.values():
        config["minimum_total_parameters"] = minimum
        config["verified_total_parameters"] = {}
    for key, evidence in policy.get("verified_models", {}).items():
        vendor, _, model = key.partition("/")
        count = evidence["total_parameters"]
        if (
            vendor not in settings or not model or slug(model) != model
            or type(count) is not int or count <= 0 or not https_url(evidence["source"])
        ):
            raise ValueError(f"Invalid total parameter evidence for {key}")
        settings[vendor]["verified_total_parameters"][model] = count


def total_parameters(name, settings, *, stored=None, safetensors=None):
    verified = settings.get("verified_total_parameters", {}).get(slug(name))
    if verified:
        return verified
    if type(stored) is int and stored > 0:
        return stored
    sizes = [
        int(Decimal(value) * (10**12 if unit.upper() == "T" else 10**9))
        for value, unit in TOTAL_IN_NAME.findall(name)
    ]
    if sizes:
        return max(sizes)
    if not isinstance(safetensors, dict) or PACKED_WEIGHTS.search(name):
        return None
    dtypes = safetensors.get("parameters") or {}
    if not isinstance(dtypes, dict) or dtypes.keys() - FLOAT_DTYPES:
        return None
    count = safetensors.get("total")
    return count if type(count) is int and count > 0 else None


def below_parameter_floor(count, settings):
    return count is not None and count < settings.get("minimum_total_parameters", 0)
