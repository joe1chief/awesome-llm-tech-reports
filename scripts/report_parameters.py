from __future__ import annotations

import json
import re
from decimal import Decimal

from report_catalog import https_url, slug

TOTAL_IN_NAME = re.compile(
    r"(?<![A-Za-z0-9.])(?:\d+(?:\.\d+)?[BT]|\d{2,}(?:\.\d+)?M)"
    r"(?![A-Za-z0-9]|[-_ ]+(?:active|activated|context)\b)",
    re.I,
)
PACKED_WEIGHTS = re.compile(
    r"(?:^|[-_. ])(?:awq|gptq|gguf|nvfp4|mxfp4|w\d+a\d+|int[248]|[248]bit|mlx)(?=$|[-_. ])",
    re.I,
)
FLOAT_DTYPES = {"F16", "BF16", "F32", "F64", "F8_E4M3", "F8_E5M2"}
AMOUNT = r"(\d+(?:\.\d+)?)\s*(trillion|billion|million|[TBM])"
PARAMETER_UNITS = {"T": 10**12, "B": 10**9, "M": 10**6}
TOTAL_FIELD = re.compile(
    rf"^\s*(?:[-*]\s+)?total\s+(?:model\s+)?parameters?\s*[:=]\s*{AMOUNT}(?=\s*(?:$|[.;(]))",
    re.I,
)
PARAMETER_TABLE_ROW = re.compile(r"^\s*\|\s*(total\s+)?(?:model\s+)?parameters?\s*\|\s*([^|]+)\|\s*$", re.I)
PARAMETER_AMOUNT = re.compile(rf"{AMOUNT}\s*", re.I)
EXPLICIT_TOTAL = re.compile(rf"{AMOUNT}\s+total\s+(?:model\s+)?parameters?\b", re.I)


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


def declared_total(name, description):
    text = re.sub(r"[*\x60]", "", description[:16000])
    text = re.sub(r"https?://\S+", "", text)
    model = r"[-_\s]+".join(re.escape(word) for word in re.split(r"[-_\s]+", name) if word)
    if not model:
        return None
    subject = re.compile(
        rf"(?im)^[ \t]*(?:>\s*)?{model}\s+(?:is|has)\s+(?:an?\s+)?"
        rf"(?:approximately\s+|about\s+|~\s*)?{AMOUNT}\s*"
        r"(?:total\s+parameters\b|parameters(?=[ \t]*[.!?]|[ \t]*$)|(?:[- ]parameter\s+)?"
        r"(?:(?:foundation|language|multimodal|vision-language|MoE)\s+)*model\b)"
    )
    amounts = []
    for line in text.splitlines():
        if match := TOTAL_FIELD.match(line):
            amounts.append(match.groups())
        elif row := PARAMETER_TABLE_ROW.fullmatch(line):
            if row[1] and (match := PARAMETER_AMOUNT.fullmatch(row[2].strip())):
                amounts.append(match.groups())
            else:
                amounts.extend(EXPLICIT_TOTAL.findall(row[2]))
        elif re.match(r"\s*(?:total\s+)?(?:model\s+)?parameters?\s*:", line, re.I):
            amounts.extend(EXPLICIT_TOTAL.findall(line))
    if not amounts:
        amounts = subject.findall(text)
    totals = {int(Decimal(value) * PARAMETER_UNITS[unit[0].upper()]) for value, unit in amounts}
    return totals.pop() if len(totals) == 1 else None


def total_parameters(name, settings, *, stored=None, safetensors=None, description=""):
    verified = settings.get("verified_total_parameters", {}).get(slug(name))
    if verified:
        return verified
    if described := declared_total(name, description):
        return described
    if type(stored) is int and stored > 0:
        return stored
    sizes = [
        int(Decimal(size[:-1]) * PARAMETER_UNITS[size[-1].upper()])
        for size in TOTAL_IN_NAME.findall(name)
    ]
    if not isinstance(safetensors, dict) or PACKED_WEIGHTS.search(name):
        return max(sizes, default=None)
    dtypes = safetensors.get("parameters") or {}
    if not isinstance(dtypes, dict) or not dtypes or dtypes.keys() - FLOAT_DTYPES:
        return max(sizes, default=None)
    count = safetensors.get("total")
    if type(count) is int and count > 0:
        return count
    return max(sizes, default=None)


def below_parameter_floor(count, settings):
    return count is not None and count < settings.get("minimum_total_parameters", 0)
