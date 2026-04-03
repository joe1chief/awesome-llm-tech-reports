#!/usr/bin/env python3
"""Discover latest model-release technical reports from monitored organizations."""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol
from urllib.parse import quote, urlencode, urljoin

import requests
from requests import exceptions as requests_exceptions

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "scripts" / "latest_models.json"
ALIASES_PATH = ROOT / "scripts" / "model_aliases.json"

LONGCAT_ARXIV_FEED_URL = (
    "https://export.arxiv.org/api/query?search_query=all:LongCat"
    "&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending"
)
LONGCAT_HF_MODELS_URL = "https://huggingface.co/api/models?author=meituan-longcat&limit=100"
ZHIPU_HF_MODELS_URL = "https://huggingface.co/api/models?author=zai-org&limit=200&full=true"
MINIMAX_NEWS_URL = "https://www.minimax.io/news"
MINIMAX_IR_URL = "https://ir.minimax.io/"
MINIMAX_SITEMAP_URL = "https://www.minimaxi.com/sitemap-0.xml"
GOOGLE_MODEL_CARDS_URL = "https://deepmind.google/models/model-cards/"
GOOGLE_GEMMA_URL = "https://deepmind.google/models/gemma/"
GOOGLE_GEMMA_DOCS_URL = "https://ai.google.dev/gemma/docs"
ZHIPU_DOCS_ROOT_URL = "https://docs.z.ai/"
BIGMODEL_DOCS_ROOT_URL = "https://docs.bigmodel.cn/cn/guide/models"
QWEN_GITHUB_REPOS_URL = "https://api.github.com/orgs/QwenLM/repos?per_page=100"
QWEN_PAGE_CONFIG_URL = "https://qwen.ai/api/page_config"
QWEN_PAGE_CONFIG_CODES = (
    "research.latest-advancements-list",
    "research.research-list",
    "home.latest-research-list",
    "news.news-list",
)
XAI_RELEASE_NOTES_URL = "https://docs.x.ai/docs/release-notes"
META_LLAMA4_BLOG_URL = "https://ai.meta.com/blog/llama-4-multimodal-intelligence/"
OPENAI_RELEASE_OVERRIDES: Dict[str, Dict[str, str]] = {
    "o3 / o4-mini": {
        "release_date": "2025-04",
        "evidence_url": "https://openai.com/index/introducing-o3-and-o4-mini/",
    }
}
ARXIV_QUERY_TEMPLATE = (
    "https://export.arxiv.org/api/query?search_query={query}"
    "&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending"
)
QWEN_REPO_ALLOWLIST = {
    "Qwen3",
    "Qwen3.5",
    "Qwen3-Coder",
    "Qwen3-Omni",
    "Qwen3-VL",
    "Qwen2.5-Omni",
    "Qwen-Image",
}

VENDOR_REGISTRY: Dict[str, Dict[str, object]] = {
    "openai": {
        "display_name": "OpenAI",
        "sources": [
            {"kind": "news", "url": "https://openai.com/news/"},
            {"kind": "system_cards", "url": "https://deploymentsafety.openai.com/"},
            {"kind": "sitemap", "url": "https://deploymentsafety.openai.com/sitemap.xml"},
            {"kind": "cdn_pdf", "url": "https://cdn.openai.com/pdf/"},
        ],
        "catalog_patterns": [r"GPT-5", r"gpt-oss", r"\bo3\b", r"o4-mini"],
    },
    "anthropic": {
        "display_name": "Anthropic",
        "sources": [
            {"kind": "news", "url": "https://www.anthropic.com/news"},
            {"kind": "sitemap", "url": "https://www.anthropic.com/sitemap.xml"},
            {"kind": "assets", "url": "https://assets.anthropic.com/"},
        ],
        "catalog_patterns": [r"Claude (?:Opus|Sonnet|Haiku) 4"],
    },
    "google": {
        "display_name": "Google",
        "sources": [
            {"kind": "model_cards", "url": GOOGLE_MODEL_CARDS_URL},
            {"kind": "gemma", "url": GOOGLE_GEMMA_URL},
            {"kind": "gemma_docs", "url": GOOGLE_GEMMA_DOCS_URL},
            {"kind": "developers_blog", "url": "https://developers.googleblog.com/"},
            {"kind": "research_blog", "url": "https://research.google/blog/"},
        ],
    },
    "xai": {
        "display_name": "xAI",
        "sources": [
            {"kind": "model_cards", "url": "https://data.x.ai/"},
            {"kind": "news", "url": "https://x.ai/news"},
            {"kind": "release_notes", "url": XAI_RELEASE_NOTES_URL},
        ],
        "catalog_patterns": [r"Grok 4(?:\.1(?: Fast)?| Fast)?\b"],
    },
    "meta": {
        "display_name": "Meta",
        "sources": [
            {"kind": "llama", "url": "https://www.llama.com/"},
            {"kind": "ai_blog", "url": "https://ai.meta.com/blog/"},
            {"kind": "llama4_blog", "url": META_LLAMA4_BLOG_URL},
            {"kind": "news_sitemap", "url": "https://about.fb.com/news-sitemap.xml"},
            {"kind": "meta_news", "url": "https://about.fb.com/news/"},
        ],
        "catalog_patterns": [r"Llama 4"],
    },
    "alibaba_qwen": {
        "display_name": "Alibaba",
        "sources": [
            {"kind": "qwen_home", "url": "https://qwen.ai/"},
            {"kind": "qwen_blog", "url": "https://qwenlm.github.io/blog/"},
            {"kind": "qwen_github", "url": "https://github.com/QwenLM"},
        ],
    },
    "quark": {
        "display_name": "Quark (Alibaba)",
        "sources": [
            {"kind": "quark_news", "url": "https://www.quark.cn/"},
            {"kind": "quark_search", "url": "https://www.quark.cn/s?q=QuarkMed"},
        ],
        "arxiv_queries": [
            {"query": 'ti:"QuarkMed"', "include_patterns": [r"^QuarkMed"]},
        ],
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "sources": [
            {"kind": "github", "url": "https://github.com/deepseek-ai"},
            {"kind": "platform", "url": "https://api-docs.deepseek.com/"},
            {"kind": "site", "url": "https://www.deepseek.com/"},
        ],
        "arxiv_queries": [
            {"query": 'ti:"DeepSeek"', "include_patterns": [r"^DeepSeek (?:V|R)\d"]},
        ],
    },
    "moonshot": {
        "display_name": "Moonshot AI",
        "sources": [
            {"kind": "kimi_site", "url": "https://www.kimi.com/"},
            {"kind": "moonshot_site", "url": "https://www.moonshot.ai/"},
            {"kind": "github", "url": "https://github.com/MoonshotAI"},
        ],
        "arxiv_queries": [
            {"query": 'ti:"Kimi K2"', "include_patterns": [r"^Kimi K2"]},
        ],
        "github_repos": [
            {"url": "https://github.com/MoonshotAI/Kimi-K2.5", "title_hint": "Kimi K2.5"},
        ],
    },
    "stepfun": {
        "display_name": "StepFun",
        "sources": [
            {"kind": "site", "url": "https://www.stepfun.com/"},
            {"kind": "open_platform", "url": "https://platform.stepfun.com/"},
            {"kind": "github", "url": "https://github.com/stepfun-ai"},
        ],
        "arxiv_queries": [
            {
                "query": 'ti:"Step-3.5-Flash" OR ti:"Step-DeepResearch"',
                "include_patterns": [r"^Step-3\.5-Flash", r"^Step-DeepResearch"],
            },
        ],
    },
    "tencent": {
        "display_name": "Tencent",
        "sources": [
            {"kind": "hunyuan", "url": "https://hunyuan.tencent.com/"},
            {"kind": "cloud", "url": "https://cloud.tencent.com/product/hunyuan"},
        ],
        "arxiv_queries": [
            {
                "query": 'ti:"Yuanbao" OR ti:"Hunyuan-TurboS"',
                "include_patterns": [r"^Yuanbao", r"Hunyuan-TurboS"],
            },
        ],
    },
    "baidu": {
        "display_name": "Baidu",
        "sources": [
            {"kind": "publication", "url": "https://yiyan.baidu.com/blog/publication"},
            {"kind": "wenxin", "url": "https://yiyan.baidu.com/"},
        ],
        "catalog_patterns": [r"ERNIE 4\.5", r"ERNIE 5(?:\.0)?"],
    },
    "bytedance": {
        "display_name": "ByteDance",
        "sources": [
            {"kind": "seed", "url": "https://seed.bytedance.com/"},
            {"kind": "github", "url": "https://github.com/bytedance"},
        ],
        "arxiv_queries": [
            {
                "query": 'ti:"MedXIAOHE" OR ti:"Seed1.5-VL" OR ti:"Seed 2.0"',
                "include_patterns": [r"^MedXIAOHE", r"^Seed1\.5-VL", r"^Seed 2\.0"],
            },
        ],
    },
    "baichuan": {
        "display_name": "Baichuan Intelligence",
        "sources": [
            {"kind": "site", "url": "https://www.baichuan-ai.com/"},
            {"kind": "github", "url": "https://github.com/baichuan-inc"},
        ],
        "arxiv_queries": [
            {"query": 'ti:"Baichuan-M"', "include_patterns": [r"^Baichuan-M\d"]},
        ],
    },
    "inclusionai": {
        "display_name": "InclusionAI (Ant Group)",
        "sources": [
            {"kind": "site", "url": "https://www.inclusionai.com/"},
            {"kind": "ant", "url": "https://www.antgroup.com/"},
        ],
        "github_repos": [
            {"url": "https://github.com/inclusionAI/Ling-V2.5", "title_hint": "Ling 2.5"},
        ],
    },
    "meituan": {
        "display_name": "Meituan",
        "sources": [
            {"kind": "arxiv", "url": LONGCAT_ARXIV_FEED_URL},
            {"kind": "hf", "url": LONGCAT_HF_MODELS_URL},
        ],
    },
    "minimax": {
        "display_name": "MiniMax",
        "sources": [
            {"kind": "news", "url": MINIMAX_NEWS_URL},
            {"kind": "ir", "url": MINIMAX_IR_URL},
            {"kind": "sitemap", "url": MINIMAX_SITEMAP_URL},
        ],
    },
    "zhipu": {
        "display_name": "Zhipu AI",
        "sources": [
            {"kind": "docs", "url": ZHIPU_DOCS_ROOT_URL},
            {"kind": "bigmodel_docs", "url": BIGMODEL_DOCS_ROOT_URL},
            {"kind": "hf", "url": ZHIPU_HF_MODELS_URL},
        ],
    },
    "mistral": {
        "display_name": "Mistral AI",
        "sources": [
            {"kind": "news", "url": "https://mistral.ai/news/"},
            {"kind": "docs", "url": "https://docs.mistral.ai/"},
        ],
        "catalog_patterns": [r"Magistral", r"Mistral (?:Medium|Small|Large)"],
    },
    "cohere": {
        "display_name": "Cohere",
        "sources": [
            {"kind": "news", "url": "https://cohere.com/blog"},
            {"kind": "docs", "url": "https://docs.cohere.com/"},
        ],
        "catalog_patterns": [r"Command A", r"Command R"],
    },
    "ai21": {
        "display_name": "AI21 Labs",
        "sources": [
            {"kind": "blog", "url": "https://www.ai21.com/blog"},
            {"kind": "docs", "url": "https://docs.ai21.com/"},
        ],
        "catalog_patterns": [r"Jamba"],
    },
    "amazon": {
        "display_name": "Amazon",
        "sources": [
            {"kind": "aws_blog", "url": "https://aws.amazon.com/blogs/aws/"},
            {"kind": "bedrock", "url": "https://docs.aws.amazon.com/bedrock/"},
        ],
        "catalog_patterns": [r"Nova (?:Premier|Pro|Lite|Micro|Sonic|Reel)"],
    },
    "ibm": {
        "display_name": "IBM",
        "sources": [
            {"kind": "granite_docs", "url": "https://www.ibm.com/granite/docs/"},
            {"kind": "research", "url": "https://research.ibm.com/blog"},
        ],
        "catalog_patterns": [r"Granite"],
    },
    "01ai": {
        "display_name": "01.AI",
        "sources": [
            {"kind": "site", "url": "https://www.lingyiwanwu.com/"},
            {"kind": "github", "url": "https://github.com/01-ai"},
        ],
        "catalog_patterns": [r"\bYi\b", r"Yi-Lightning"],
    },
    "naver": {
        "display_name": "NAVER",
        "sources": [
            {"kind": "hyperclova", "url": "https://www.ncloud.com/product/aiService/hyperclovaX"},
            {"kind": "blog", "url": "https://blog.naver.com/naver_ai"},
        ],
        "catalog_patterns": [r"HyperCLOVA X"],
    },
    "huawei": {
        "display_name": "Huawei",
        "sources": [
            {"kind": "pangu", "url": "https://www.huaweicloud.com/intl/en-us/product/pangu.html"},
            {"kind": "cloud_blog", "url": "https://www.huaweicloud.com/intl/en-us/news/"},
        ],
        "catalog_patterns": [r"Pangu"],
    },
    "sensetime": {
        "display_name": "SenseTime",
        "sources": [
            {"kind": "site", "url": "https://www.sensetime.com/"},
            {"kind": "sensenova", "url": "https://platform.sensenova.cn/"},
        ],
        "catalog_patterns": [r"SenseNova"],
    },
}

ORG_DISPLAY = {
    slug: str(config["display_name"])
    for slug, config in VENDOR_REGISTRY.items()
}

EVIDENCE_SCORES = {
    "official_model_card": 1.0,
    "official_system_card": 1.0,
    "arxiv_report": 0.95,
    "official_model_page": 0.9,
    "official_hf_model_page": 0.82,
    "official_news_page": 0.78,
}

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class Fetcher(Protocol):
    def get_text(self, url: str) -> str: ...

    def get_json(self, url: str) -> Any: ...


class RequestsFetcher:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36"
                )
            }
        )
        self.fallback_user_agent = "Mozilla/5.0"

    def _request(self, url: str, *, parse_json: bool) -> Any:
        def perform(*, verify: bool, fallback_ua: bool) -> requests.Response:
            headers = {"User-Agent": self.fallback_user_agent} if fallback_ua else None
            return self.session.get(url, timeout=20, verify=verify, headers=headers)

        try:
            resp = perform(verify=True, fallback_ua=False)
        except requests_exceptions.SSLError:
            resp = perform(verify=False, fallback_ua=False)
        if resp.status_code in {400, 403} and any(host in url for host in ["meta.com", "llama.com", "fb.com"]):
            resp = perform(verify=False, fallback_ua=True)
        resp.raise_for_status()
        return resp.json() if parse_json else resp.text

    def get_text(self, url: str) -> str:
        return str(self._request(url, parse_json=False))

    def get_json(self, url: str) -> Any:
        return self._request(url, parse_json=True)


@dataclass(frozen=True)
class AliasResolution:
    canonical_name: str
    aliases: List[str]


def load_alias_config(path: Path = ALIASES_PATH) -> Dict[str, Dict[str, List[str]]]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_alias_token(text: str) -> str:
    text = html.unescape(unicodedata.normalize("NFKC", text or "")).replace("\xa0", " ").strip()
    text = text.replace("&nbsp;", " ").replace("&Nbsp;", " ")
    text = re.sub(r"(?i)\btechnical\s+report\b", "", text)
    text = re.sub(r"(?i)\bmodel\s+card\b", "", text)
    text = re.sub(r"(?i)\bsystem\s+card\b", "", text)
    text = re.sub(r"(?i)\breport\b", "", text)
    text = re.sub(r"(?i)\bpreview\b", "", text)
    text = re.sub(r"[()_:]+", " ", text)
    text = re.sub(r"[-–—]+", "-", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text.casefold()


def _generic_canonical_name(org_slug: str, name: str) -> str:
    raw = html.unescape(name or "").replace("\xa0", " ")
    raw = re.sub(r"(?i)\btechnical\s+report\b", "", raw).strip()
    raw = re.sub(r"(?i)\bmodel\s+card\b", "", raw).strip()
    raw = re.sub(r"(?i)\bsystem\s+card\b", "", raw).strip()
    raw = raw.replace("&nbsp;", " ").replace("&Nbsp;", " ")
    raw = re.sub(r"(?i)^introducing\s+", "", raw).strip()
    raw = re.sub(r"\s+", " ", raw).strip(" -")
    if org_slug == "meituan" and raw.lower().startswith("longcat"):
        raw = raw.split(":", 1)[0].strip()
        return re.sub(r"\s+", "-", raw)
    if org_slug == "zhipu" and raw.upper().startswith("GLM"):
        raw = raw.split(":", 1)[0].strip()
        canonical = raw.upper().replace(" ", "-")
        canonical = canonical.replace("--", "-")
        canonical = re.sub(r"GLM-(\d)(V)", r"GLM-\1\2", canonical)
        canonical = canonical.replace("-FLASH", "-Flash").replace("-TURBO", "-Turbo")
        return canonical.replace("GLM-", "GLM-", 1)
    if org_slug == "minimax" and raw.lower().startswith("minimax"):
        raw = raw.split(":", 1)[0].strip()
        pieces = raw.split()
        if len(pieces) >= 2 and pieces[0].lower() == "minimax":
            return f"MiniMax {pieces[1]}"
    if org_slug == "google":
        lowered = raw.casefold()
        if lowered.startswith("gemini"):
            cleaned = re.sub(r"(?i)\s*-\s*model card$", "", raw).strip()
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
            cleaned = cleaned.replace("Flash Lite", "Flash-Lite")
            return cleaned
        if "medgemma 1.5" in lowered:
            return "MedGemma 1.5"
        if "medgemma" in lowered:
            return "MedGemma"
        if "gemma 4" in lowered:
            return "Gemma 4"
        if "shieldgemma 2" in lowered:
            return "ShieldGemma 2"
        if "shieldgemma" in lowered:
            return "ShieldGemma"
        if "functiongemma" in lowered:
            return "FunctionGemma"
        if "embeddinggemma" in lowered:
            return "EmbeddingGemma"
        if "translategemma" in lowered:
            return "TranslateGemma"
        if "vaultgemma" in lowered:
            return "VaultGemma"
        if "t5gemma 2" in lowered:
            return "T5Gemma 2"
        if "t5gemma" in lowered:
            return "T5Gemma"
        raw = raw.replace("-", " ")
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw.title().replace("Medgemma", "MedGemma").replace("Shieldgemma", "ShieldGemma")
    if org_slug == "alibaba_qwen":
        raw = raw.split(":", 1)[0].strip()
        raw = re.sub(r"\s+", " ", raw).strip()
        return raw
    if org_slug == "openai":
        raw = re.sub(r"\s*-\s*OpenAI Deployment Safety Hub$", "", raw, flags=re.I).strip()
        raw = raw.replace("System Card", "").replace("Model Card", "").strip(" -")
        raw = re.sub(r"(?i)^openai\s+", "", raw).strip()
        if re.search(r"\bo3\b", raw, flags=re.I) and re.search(r"\bo4-mini\b", raw, flags=re.I):
            return "o3 / o4-mini"
        if raw.lower().startswith("gpt 5"):
            raw = raw.replace("GPT 5", "GPT-5")
        return re.sub(r"\s+", " ", raw).strip()
    if org_slug == "anthropic":
        return re.sub(r"\s+", " ", raw).strip()
    if org_slug == "xai":
        return re.sub(r"\s+", " ", raw).strip().replace("Model Card", "").strip()
    if org_slug == "meta":
        lowered = raw.casefold()
        if "llama 4" in lowered and any(token in lowered for token in ["scout", "maverick", "multimodal"]):
            return "Llama 4 Scout/Maverick"
        return re.sub(r"\s+", " ", raw).strip()
    if org_slug == "moonshot":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "deepseek":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "stepfun":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "tencent":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "baidu":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "bytedance":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "baichuan":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "quark":
        return re.sub(r"\s+", " ", raw).strip().replace("Technical Report", "").strip()
    if org_slug == "inclusionai":
        if "ling-v2.5" in raw.casefold():
            return "Ling 2.5"
        return re.sub(r"\s+", " ", raw).strip()
    return raw


def canonicalize_model_name(
    org_slug: str,
    name: str,
    alias_config: Optional[Dict[str, Dict[str, List[str]]]] = None,
) -> AliasResolution:
    alias_config = alias_config or load_alias_config()
    org_aliases = alias_config.get(org_slug, {})
    normalized = normalize_alias_token(name)
    aliases = [name.strip()]
    for canonical_name, known_aliases in org_aliases.items():
        candidates = [canonical_name, *known_aliases]
        if any(normalize_alias_token(candidate) == normalized for candidate in candidates):
            deduped = list(dict.fromkeys([canonical_name, *known_aliases, name.strip()]))
            return AliasResolution(canonical_name=canonical_name, aliases=deduped)

    canonical = _generic_canonical_name(org_slug, name)
    return AliasResolution(canonical_name=canonical, aliases=list(dict.fromkeys([canonical, name.strip()])))


def build_canonical_model_id(org_slug: str, model_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", model_name.lower()).strip("-")
    return f"{org_slug}/{slug}"


def parse_iso_month(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    match = re.search(r"(20\d{2})-(\d{2})", value)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None


def build_arxiv_query_url(query: str) -> str:
    return ARXIV_QUERY_TEMPLATE.format(query=quote(query, safe=':"()+'))


def build_qwen_page_config_url(code: str) -> str:
    return f"{QWEN_PAGE_CONFIG_URL}?{urlencode({'code': code})}"


def month_from_date_text(value: str) -> Optional[str]:
    match = re.search(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", value)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}"
    named_full = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2},\s*(20\d{2})",
        value,
        flags=re.I,
    )
    if named_full:
        month_names = {
            "january": "01",
            "jan": "01",
            "february": "02",
            "feb": "02",
            "march": "03",
            "mar": "03",
            "april": "04",
            "apr": "04",
            "may": "05",
            "june": "06",
            "jun": "06",
            "july": "07",
            "jul": "07",
            "august": "08",
            "aug": "08",
            "september": "09",
            "sep": "09",
            "sept": "09",
            "october": "10",
            "oct": "10",
            "november": "11",
            "nov": "11",
            "december": "12",
            "dec": "12",
        }
        return f"{named_full.group(2)}-{month_names[named_full.group(1).lower()]}"
    named = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})",
        value,
        flags=re.I,
    )
    if named:
        month_names = {
            "january": "01",
            "february": "02",
            "march": "03",
            "april": "04",
            "may": "05",
            "june": "06",
            "july": "07",
            "august": "08",
            "september": "09",
            "october": "10",
            "november": "11",
            "december": "12",
        }
        return f"{named.group(2)}-{month_names[named.group(1).lower()]}"
    return parse_iso_month(value)


def month_from_url(value: str) -> Optional[str]:
    if not value:
        return None
    if (month := parse_iso_month(value)) is not None:
        return month
    return month_from_arxiv_url(value)


def month_distance(a: str, b: str) -> Optional[int]:
    match_a = re.match(r"^(20\d{2})-(\d{2})$", a)
    match_b = re.match(r"^(20\d{2})-(\d{2})$", b)
    if not match_a or not match_b:
        return None
    total_a = int(match_a.group(1)) * 12 + int(match_a.group(2))
    total_b = int(match_b.group(1)) * 12 + int(match_b.group(2))
    return abs(total_a - total_b)


def evidence_confidence(evidence_type: str) -> float:
    return EVIDENCE_SCORES.get(evidence_type, 0.6)


def safe_get_text(fetcher: Fetcher, url: str) -> str:
    try:
        return fetcher.get_text(url)
    except Exception:
        return ""


def safe_get_json(fetcher: Fetcher, url: str) -> Any:
    try:
        return fetcher.get_json(url)
    except Exception:
        return []


def strip_html_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_href_values(html_text: str) -> List[str]:
    values: List[str] = []
    for match in re.finditer(
        r"""href\s*=\s*(?:"([^"]+)"|'([^']+)'|([^>\s]+))""",
        html_text,
        flags=re.I,
    ):
        href = next((group for group in match.groups() if group), "")
        cleaned = clean_extracted_link(href)
        if cleaned:
            values.append(cleaned)
    return list(dict.fromkeys(values))


def explicit_release_month_from_html(html_text: str, *, allow_last_updated: bool) -> Optional[str]:
    for pattern in [
        r'"datePublished":"([^"]+)"',
        r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|publish-date|pubdate)["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
    ]:
        match = re.search(pattern, html_text, flags=re.I)
        if match and (month := parse_iso_month(match.group(1))):
            return month
    if published_match := re.search(r"Published\s+([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})", html_text):
        if month := month_from_date_text(published_match.group(1)):
            return month
    visible_text = strip_html_tags(html_text)
    visible_without_last_updated = re.sub(r"Last updated[^.]*\.?", " ", visible_text, flags=re.I)
    if month := month_from_date_text(visible_without_last_updated):
        return month
    if allow_last_updated:
        return parse_last_updated_month(html_text)
    return None


def parse_sitemap_entries(xml_text: str, base_url: str) -> List[Dict[str, str]]:
    if not xml_text.strip():
        return []
    root = ET.fromstring(xml_text)
    base_match = re.match(r"(https?://[^/]+)", base_url)
    base_origin = base_match.group(1) if base_match else ""
    entries: List[Dict[str, str]] = []
    for url_node in root.findall(".//{*}url"):
        loc_node = url_node.find("{*}loc")
        lastmod_node = url_node.find("{*}lastmod")
        if loc_node is None or not (loc_node.text and loc_node.text.strip()):
            continue
        loc = loc_node.text.strip()
        if "localhost" in loc and base_origin:
            path = re.sub(r"^https?://[^/]+", "", loc)
            loc = f"{base_origin}{path}"
        entries.append(
            {
                "url": clean_extracted_link(loc),
                "lastmod": (lastmod_node.text or "").strip() if lastmod_node is not None else "",
            }
        )
    return entries


def clean_extracted_link(url: str) -> str:
    cleaned = html.unescape(url or "").strip().strip("\"'<>")
    cleaned = cleaned.replace("\\u0026", "&").replace("\\/", "/").replace("&amp;", "&")
    cleaned = re.split(r"[\"'<>}]", cleaned, maxsplit=1)[0]
    cleaned = re.sub(r"\\+$", "", cleaned)
    return cleaned.rstrip(").,;")


def classify_release(org_slug: str, canonical_name: str) -> tuple[str, str]:
    if org_slug == "openai":
        lowered = canonical_name.casefold()
        if canonical_name.startswith("GPT-5") and not any(
            token in lowered for token in ["sensitive conversations", "addendum"]
        ):
            return "model_release", "openai_frontier_release"
        if canonical_name.startswith("gpt-oss"):
            return "model_release", "openai_frontier_release"
        if canonical_name == "o3 / o4-mini":
            return "model_release", "openai_frontier_release"
    if org_slug == "anthropic" and re.search(r"Claude (?:Opus|Sonnet|Haiku) 4", canonical_name):
        return "model_release", "anthropic_frontier_release"
    if org_slug == "xai" and canonical_name.startswith("Grok 4"):
        return "model_release", "xai_frontier_release"
    if org_slug == "meta" and canonical_name.startswith("Llama 4"):
        return "model_release", "meta_frontier_release"
    if org_slug == "alibaba_qwen":
        if canonical_name in {
            "Qwen3",
            "Qwen3.5",
            "Qwen3-Coder",
            "Qwen3-Next",
            "Qwen3-Max",
            "Qwen3-Omni",
            "Qwen3-VL",
            "Qwen2.5-Omni",
            "Qwen-Image",
        }:
            return "model_release", "qwen_frontier_release"
        if any(
            token in canonical_name
            for token in ["Embedding", "Guard", "ASR", "TTS", "VL-Embedding", "Image-Edit", "LiveTranslate", "DeepResearch", "VLo", "MT"]
        ):
            return "exclude_tool_model", "qwen_auxiliary_or_tool_release"
    if org_slug == "google":
        if canonical_name.startswith(("ShieldGemma", "EmbeddingGemma", "FunctionGemma")):
            return "exclude_tool_model", "tool_or_guard_gemma_variant"
        if canonical_name.startswith("Gemini "):
            return "model_release", "frontier_gemini_release"
        if re.match(r"^Gemma \d", canonical_name) or canonical_name.startswith("MedGemma "):
            return "model_release", "core_or_vertical_gemma_release"
    if org_slug == "meituan" and canonical_name.startswith("LongCat"):
        if canonical_name.startswith(
            (
                "LongCat-Flash",
                "LongCat-Next",
                "LongCat-Image",
                "LongCat-Video",
            )
        ):
            return "model_release", "longcat_frontier_release"
        return "exclude_method_paper", "longcat_non_frontier_or_component_release"
    if org_slug == "zhipu":
        if canonical_name in {"GLM-5", "GLM-5V-Turbo", "GLM-4.7", "GLM-4.7-Flash", "GLM-4.5"}:
            return "model_release", "glm_frontier_release"
        if canonical_name.startswith("GLM-"):
            return "exclude_tool_model", "glm_auxiliary_or_product_variant"
    if org_slug == "minimax" and re.match(r"^MiniMax M\d", canonical_name):
        return "model_release", "minimax_frontier_release"
    if org_slug == "deepseek" and canonical_name.startswith("DeepSeek "):
        return "model_release", "deepseek_frontier_release"
    if org_slug == "moonshot" and canonical_name.startswith("Kimi K2"):
        return "model_release", "moonshot_frontier_release"
    if org_slug == "stepfun" and canonical_name.startswith("Step-"):
        return "model_release", "stepfun_frontier_release"
    if org_slug == "tencent" and ("Hunyuan-TurboS" in canonical_name or canonical_name.startswith("Yuanbao")):
        return "model_release", "tencent_frontier_release"
    if org_slug == "baidu" and canonical_name.startswith("ERNIE "):
        return "model_release", "baidu_frontier_release"
    if org_slug == "bytedance" and (
        canonical_name.startswith("Seed") or canonical_name.startswith("MedXIAOHE")
    ):
        return "model_release", "bytedance_frontier_release"
    if org_slug == "baichuan" and canonical_name.startswith("Baichuan-"):
        return "model_release", "baichuan_frontier_release"
    if org_slug == "quark" and canonical_name.startswith("QuarkMed"):
        return "model_release", "quark_frontier_release"
    if org_slug == "inclusionai" and canonical_name.startswith("Ling "):
        return "model_release", "inclusionai_frontier_release"
    return "needs_review", "unmatched_release_rule"


def build_record(
    *,
    org_slug: str,
    raw_name: str,
    release_date: str,
    official_link: str,
    candidate_links: Iterable[str],
    source_page: str,
    evidence_urls: Iterable[str],
    evidence_type: str,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> Dict[str, Any]:
    resolution = canonicalize_model_name(org_slug, raw_name, alias_config=alias_config)
    classification, reason = classify_release(org_slug, resolution.canonical_name)
    deduped_candidate_links = list(dict.fromkeys(link for link in candidate_links if link))
    deduped_evidence_urls = list(dict.fromkeys(link for link in evidence_urls if link))
    return {
        "release_date": release_date,
        "org": ORG_DISPLAY[org_slug],
        "org_slug": org_slug,
        "model": resolution.canonical_name,
        "canonical_model_id": build_canonical_model_id(org_slug, resolution.canonical_name),
        "aliases": resolution.aliases,
        "core_feature": "",
        "official_link": official_link,
        "candidate_links": deduped_candidate_links,
        "source_page": source_page,
        "evidence_urls": deduped_evidence_urls,
        "evidence_type": evidence_type,
        "release_classification": classification,
        "classification_reason": reason,
        "confidence": evidence_confidence(evidence_type),
        "discovered_at": discovered_at,
    }


def parse_longcat_arxiv(feed_text: str) -> List[Dict[str, str]]:
    root = ET.fromstring(feed_text)
    records: List[Dict[str, str]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        abs_url = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        if "longcat" not in title.lower():
            continue
        arxiv_match = re.search(r"/abs/([0-9]{4}\.[0-9]{4,5})", abs_url)
        if not arxiv_match:
            continue
        records.append(
            {
                "title": title,
                "release_date": parse_iso_month(published) or "1970-01",
                "abs_url": abs_url.replace("http://", "https://"),
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_match.group(1)}",
            }
        )
    return records


def parse_hf_models(items: Any, org_slug: str) -> List[Dict[str, str]]:
    if not isinstance(items, list):
        return []
    out: List[Dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        model_id = str(item.get("id", "")).strip()
        if "/" not in model_id:
            continue
        _, raw_name = model_id.split("/", 1)
        if org_slug == "zhipu" and not re.search(r"GLM-(?:5V-Turbo|5$|4\.7(?:-Flash)?$|4\.5$)", raw_name, flags=re.I):
            continue
        created_at = parse_iso_month(str(item.get("createdAt") or item.get("lastModified") or ""))
        out.append(
            {
                "title": raw_name,
                "release_date": created_at or "1970-01",
                "page_url": f"https://huggingface.co/{model_id}",
                "org_slug": org_slug,
            }
        )
    return out


def decode_github_readme(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    content = str(payload.get("content") or "")
    if not content:
        return ""
    try:
        return base64.b64decode(content).decode("utf-8", "ignore")
    except Exception:
        return ""


def extract_markdown_links(markdown: str) -> List[str]:
    links = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", markdown)
    links.extend(re.findall(r"(https?://[^\s)]+)", markdown))
    cleaned = []
    for link in links:
        cleaned.append(clean_extracted_link(link))
    return list(dict.fromkeys(cleaned))


def normalize_github_blob_url(url: str) -> str:
    if "raw.githubusercontent.com" in url:
        return url
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/blob/([^/]+)/(.*)", url)
    if match:
        return f"https://raw.githubusercontent.com/{match.group(1)}/{match.group(2)}/{match.group(3)}"
    if "github.com" not in url:
        return url
    return url


def extract_links_from_github_repo_html(html_text: str, repo_url: str) -> List[str]:
    links: List[str] = []
    repo_path = repo_url.replace("https://github.com/", "")
    for rel in re.findall(rf'/{re.escape(repo_path)}/(?:blob|raw)/main/[^"\' ]+\.pdf', html_text, flags=re.I):
        links.append(clean_extracted_link(normalize_github_blob_url(urljoin("https://github.com", rel))))
    for absolute in re.findall(r'https?://[^"\' ]+\.pdf', html_text, flags=re.I):
        links.append(clean_extracted_link(normalize_github_blob_url(absolute)))
    for absolute in re.findall(r'https?://arxiv\.org/(?:abs|pdf)/[0-9]{4}\.[0-9]{4,5}(?:v\d+)?', html_text, flags=re.I):
        pdf = arxiv_pdf_url(absolute)
        links.append(clean_extracted_link(pdf or absolute))
    for absolute in re.findall(r'https?://(?:qwen\.ai|qwenlm\.github\.io)/[^"\' <>]+', html_text, flags=re.I):
        links.append(clean_extracted_link(absolute))
    return list(dict.fromkeys(link for link in links if link))


def infer_month_from_github_repo_html(html_text: str) -> Optional[str]:
    for candidate in re.findall(r'(20\d{2}-\d{2}-\d{2})', html_text):
        month = parse_iso_month(candidate)
        if month:
            return month
    return None


def guess_qwen_repo_pdf_links(repo_name: str, html_text: str) -> List[str]:
    guesses: List[str] = []
    known_pdfs = {
        "Qwen3": "Qwen3_Technical_Report.pdf",
        "Qwen3-Coder": "qwen3_coder_next_tech_report.pdf",
    }
    filename = known_pdfs.get(repo_name)
    if filename and filename in html_text:
        guesses.append(f"https://raw.githubusercontent.com/QwenLM/{repo_name}/main/{filename}")
    return guesses


def arxiv_pdf_url(url: str) -> Optional[str]:
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})", url)
    if match:
        return f"https://arxiv.org/pdf/{match.group(1)}"
    return None


def month_from_arxiv_url(url: str) -> Optional[str]:
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{2})([0-9]{2})\.[0-9]{4,5}", url)
    if match:
        return f"20{match.group(1)}-{match.group(2)}"
    return None


def infer_month_from_blog_page(fetcher: Fetcher, url: str) -> Optional[str]:
    html_text = safe_get_text(fetcher, url)
    if not html_text:
        return None
    for pattern in [
        r'datePublished["\']?\s*[:=]\s*["\'](20\d{2}-\d{2}-\d{2})',
        r'<time[^>]+datetime=["\'](20\d{2}-\d{2}-\d{2})',
    ]:
        match = re.search(pattern, html_text, flags=re.I)
        if match:
            month = parse_iso_month(match.group(1))
            if month:
                return month
    plain = re.sub(r"<[^>]+>", " ", html_text)
    plain = re.sub(r"\s+", " ", plain)
    return month_from_date_text(plain)


def parse_markdown_heading(markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, flags=re.M)
    if match:
        heading = match.group(1).strip()
        if "qwen" in heading.casefold():
            return heading
    for candidate in [
        "Qwen3-Coder",
        "Qwen3-Next",
        "Qwen3-Max",
        "Qwen3-Omni",
        "Qwen3-VL",
        "Qwen2.5-Omni",
        "Qwen-Image",
        "Qwen3.5",
        "Qwen3",
    ]:
        if candidate.lower() in markdown.lower():
            return candidate
    return ""


def qwen_repo_tokens(repo_name: str) -> List[str]:
    mapping = {
        "Qwen3": ["qwen3"],
        "Qwen3.5": ["qwen3.5", "qwen3-5", "qwen3-next"],
        "Qwen3-Coder": ["qwen3-coder", "qwen3-coder-next"],
        "Qwen3-Next": ["qwen3-next"],
        "Qwen3-Max": ["qwen3-max"],
        "Qwen3-Omni": ["qwen3-omni"],
        "Qwen3-VL": ["qwen3-vl"],
        "Qwen2.5-Omni": ["qwen2.5-omni", "qwen25-omni"],
        "Qwen-Image": ["qwen-image"],
    }
    return mapping.get(repo_name, [repo_name.casefold().replace(".", "-")])


def parse_qwen_page_config_items(payload: Any) -> List[Dict[str, str]]:
    if not isinstance(payload, list):
        return []
    records: List[Dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        title = re.sub(r"\s+", " ", str(item.get("title") or "")).strip()
        if "qwen" not in title.casefold():
            continue
        token_links = clean_extracted_link(str(item.get("tokenLinks") or "").strip())
        records.append(
            {
                "title": title,
                "release_date": parse_iso_month(str(item.get("date") or "")) or "1970-01",
                "token_links_url": token_links,
            }
        )
    return records


def parse_qwen_token_links(payload: Any) -> Dict[str, Any]:
    links: List[str] = []
    headings: List[str] = []
    paragraphs: List[str] = []
    if not isinstance(payload, list):
        return {"links": [], "heading": "", "summary": ""}
    for item in payload:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type == "hugoButton":
            href = clean_extracted_link(str(item.get("href") or "").strip())
            if href:
                links.append(href)
        elif item_type == "heading":
            text = strip_html_tags(str(item.get("text") or ""))
            if text:
                headings.append(text)
        elif item_type == "paragraph":
            text = strip_html_tags(str(item.get("text") or ""))
            if text:
                paragraphs.append(text)
    return {
        "links": list(dict.fromkeys(links)),
        "heading": next((heading for heading in headings if "qwen" in heading.casefold()), headings[0] if headings else ""),
        "summary": " ".join(paragraphs[:2]).strip(),
    }


def qwen_raw_name_from_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.split(":", 1)[0]).strip().replace("\u2011", "-")


def should_override_qwen_raw_name(raw_name: str, heading: str) -> bool:
    if not heading or "qwen" not in heading.casefold():
        return False
    normalized_raw = normalize_alias_token(raw_name).replace(" ", "")
    normalized_heading = normalize_alias_token(heading).replace(" ", "")
    return bool(normalized_raw and normalized_heading and normalized_raw == normalized_heading)


def qwen_link_rank(url: str) -> tuple[int, int]:
    lowered = url.casefold()
    if "arxiv.org/pdf/" in lowered or lowered.endswith(".pdf") or "/tree/main/assets/" in lowered:
        return (0, len(url))
    if "github.com/qwenlm/" in lowered:
        return (1, len(url))
    if "docs.qwenlm.ai" in lowered:
        return (2, len(url))
    if "alibabacloud.com/help/en/model-studio" in lowered:
        return (3, len(url))
    if "huggingface.co/collections/qwen" in lowered:
        return (4, len(url))
    if "modelscope.cn/collections/" in lowered:
        return (5, len(url))
    if "chat.qwen" in lowered:
        return (8, len(url))
    if "discord.gg" in lowered:
        return (9, len(url))
    return (6, len(url))


def normalize_xai_release_title(title: str) -> Optional[str]:
    cleaned = re.sub(r"\s+", " ", title).strip()
    if cleaned.startswith("Grok 4.1 Fast"):
        return "Grok 4.1 Fast"
    if cleaned.startswith("Grok 4 is released") or cleaned == "Grok 4":
        return "Grok 4"
    return None


def default_xai_release_url(model_name: str) -> str:
    mapping = {
        "Grok 4": "https://x.ai/news/grok-4",
        "Grok 4.1 Fast": "https://x.ai/news/grok-4-1-fast",
    }
    return mapping.get(model_name, XAI_RELEASE_NOTES_URL)


def parse_xai_release_notes(html_text: str) -> List[Dict[str, str]]:
    month_map = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12",
    }
    current_year = ""
    current_month = ""
    records: List[Dict[str, str]] = []
    token_pattern = re.compile(
        r'<h1[^>]*><a[^>]*>([A-Za-z]+)\s+(20\d{2})</a></h1>|'
        r'>([A-Z][a-z]{2})\s+(\d{1,2})</div>.*?<h3[^>]*><a[^>]*>([^<]+)</a></h3>',
        flags=re.I | re.S,
    )
    abbr_map = {name[:3].lower(): number for name, number in month_map.items()}
    matches = list(token_pattern.finditer(html_text))
    for index, match in enumerate(matches):
        month_name, year, day_month_abbr, _day, title = match.groups()
        if month_name and year:
            current_year = year
            current_month = month_map.get(month_name.lower(), "")
            continue
        if not (day_month_abbr and title and current_year and current_month):
            continue
        normalized_title = normalize_xai_release_title(title)
        if not normalized_title:
            continue
        entry_month = abbr_map.get(day_month_abbr.lower())
        if not entry_month:
            continue
        snippet_end = matches[index + 1].start() if index + 1 < len(matches) else len(html_text)
        snippet = html_text[match.end():snippet_end]
        links = extract_generic_page_links(snippet, XAI_RELEASE_NOTES_URL)
        page_url = next((link for link in links if "x.ai/news/" in link), default_xai_release_url(normalized_title))
        records.append(
            {
                "title": normalized_title,
                "release_date": f"{current_year}-{entry_month}",
                "page_url": page_url,
            }
        )
    return records


def parse_minimax_news(html: str) -> List[Dict[str, str]]:
    pattern = re.compile(
        r'<a[^>]+href="(?P<href>/news/[^"]+)"[^>]*>(?P<title>[^<]*MiniMax[^<]*)</a>.*?'
        r'<time[^>]+datetime="(?P<date>[^"]+)"',
        flags=re.I | re.S,
    )
    records: List[Dict[str, str]] = []
    for match in pattern.finditer(html):
        title = re.sub(r"\s+", " ", match.group("title")).strip()
        url = urljoin("https://www.minimax.io", match.group("href"))
        records.append(
            {
                "title": title.replace("Introducing ", "").strip(),
                "release_date": month_from_date_text(match.group("date")) or "1970-01",
                "page_url": url,
            }
        )
    return records


def parse_minimax_article_links(html: str) -> List[str]:
    links = sorted(
        {
            urljoin("https://www.minimax.io", match)
            for match in re.findall(r'/news/minimax-m[0-9a-z\-]+', html, flags=re.I)
        }
    )
    return links


def normalize_minimax_article_url(url: str) -> List[str]:
    normalized = url.replace("https://www.minimaxi.com", "https://www.minimax.io")
    candidates = [normalized]
    if normalized.endswith("-zh"):
        candidates.insert(0, normalized[:-3] + "-en")
    return list(dict.fromkeys(candidates))


def parse_minimax_article(html: str, url: str) -> Optional[Dict[str, str]]:
    title_match = re.search(
        r'<meta property="og:title" content="([^"]+)"',
        html,
        flags=re.I,
    ) or re.search(r"<title>([^<]+)</title>", html, flags=re.I)
    date_match = re.search(r'"datePublished":"([^"]+)"', html, flags=re.I)
    if not title_match:
        return None
    title = title_match.group(1).replace(" - MiniMax News | MiniMax", "").strip()
    return {
        "title": title,
        "release_date": (
            parse_iso_month(date_match.group(1))
            if date_match
            else explicit_release_month_from_html(html, allow_last_updated=False)
        )
        or "1970-01",
        "page_url": url,
    }


def parse_google_model_cards(html: str) -> List[Dict[str, str]]:
    pattern = re.compile(r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>[^<]+)</a>', flags=re.I)
    records: List[Dict[str, str]] = []
    for match in pattern.finditer(html):
        href = match.group("href").strip()
        title = re.sub(r"\s+", " ", match.group("title")).strip()
        if not any(key in title.lower() for key in ["gemma", "medgemma", "shieldgemma"]):
            continue
        records.append(
            {
                "title": title,
                "release_date": "1970-01",
                "pdf_url": href,
                "page_url": href,
            }
        )
    return records


def parse_google_model_card_rows(html: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    for row in re.findall(r"<tr\b.*?</tr>", html, flags=re.I | re.S):
        title_match = re.search(r"<th[^>]*>(.*?)</th>", row, flags=re.I | re.S)
        if not title_match:
            continue
        title = strip_html_tags(title_match.group(1))
        if not any(token in title.casefold() for token in ["gemma", "medgemma", "gemini"]):
            continue
        hrefs = [urljoin("https://deepmind.google", href) for href in extract_href_values(row)]
        if not hrefs:
            continue
        release_date = "1970-01"
        for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.I | re.S):
            if month := month_from_date_text(strip_html_tags(cell)):
                release_date = month
                break
        records.append(
            {
                "title": title,
                "release_date": release_date,
                "page_url": hrefs[0],
            }
        )
    return records


def parse_google_gemma_cards(html: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    article_pattern = re.compile(r'<article class="card card--general".*?</article>', flags=re.I | re.S)
    for article in article_pattern.findall(html):
        date_match = re.search(r'<span class=text-small>([^<]+)</span>', article, flags=re.I)
        title_match = re.search(r'<h3[^>]*>([^<]+)</h3>', article, flags=re.I)
        href_match = re.search(r'href=(https?://[^ >]+|/models/[^ >]+)', article, flags=re.I)
        if not title_match or not href_match:
            continue
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        if not any(token in title.lower() for token in ["gemma", "medgemma", "shieldgemma", "functiongemma", "translategemma"]):
            continue
        href = href_match.group(1).strip().rstrip('"').rstrip(">")
        records.append(
            {
                "title": title,
                "release_date": month_from_date_text(date_match.group(1)) if date_match else "1970-01",
                "page_url": urljoin("https://deepmind.google", href),
            }
        )
    return records


def parse_google_docs_model_cards(html: str) -> List[str]:
    return [
        urljoin("https://ai.google.dev", path.rstrip("\\"))
        for path in re.findall(r'/gemma/docs/[^"]*model_card[^"]*', html, flags=re.I)
    ]


def parse_last_updated_month(html: str) -> Optional[str]:
    match = re.search(r"Last updated (20\d{2}-\d{2}-\d{2})", html, flags=re.I)
    if match:
        return parse_iso_month(match.group(1))
    return parse_iso_month(next(iter(re.findall(r"(20\d{2}-\d{2}-\d{2})", html)), ""))


def parse_zhipu_doc_links(html: str, base_url: str) -> List[str]:
    matches = re.findall(
        r'href="([^"]*(?:glm-5v-turbo|glm-4\.7(?:-flash)?|glm-5)[^"]*)"',
        html,
        flags=re.I,
    )
    cleaned = []
    for href in matches:
        href = href.rstrip("\\")
        cleaned.append(urljoin(base_url, href))
    return sorted(set(cleaned))


def parse_zhipu_doc_page(html: str, url: str) -> Optional[Dict[str, str]]:
    title_match = re.search(r"<title>([^<]+)</title>", html, flags=re.I)
    if not title_match:
        return None
    title = title_match.group(1).split(" - ")[0].strip()
    title = title.replace("Overview", "").strip(" -")
    return {
        "title": title,
        "release_date": explicit_release_month_from_html(html, allow_last_updated=True) or "1970-01",
        "page_url": url,
    }


def parse_arxiv_feed(feed_text: str) -> List[Dict[str, str]]:
    if not feed_text.strip():
        return []
    root = ET.fromstring(feed_text)
    records: List[Dict[str, str]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        abs_url = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        arxiv_match = re.search(r"/abs/([0-9]{4}\.[0-9]{4,5})", abs_url)
        if not title or not arxiv_match:
            continue
        records.append(
            {
                "title": title,
                "release_date": parse_iso_month(published) or "1970-01",
                "abs_url": abs_url.replace("http://", "https://"),
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_match.group(1)}",
            }
        )
    return records


def parse_catalog_anchors(html_text: str, base_url: str) -> List[Dict[str, str]]:
    blocks = re.findall(r"<article\b.*?</article>", html_text, flags=re.I | re.S) or [html_text]
    seen = set()
    items: List[Dict[str, str]] = []
    for block in blocks:
        block_date = parse_iso_month(next(iter(re.findall(r'datetime="([^"]+)"', block, flags=re.I)), ""))
        if block_date is None:
            block_date = month_from_date_text(strip_html_tags(block))
        for href1, href2, href3, inner in re.findall(
            r"""<a[^>]+href\s*=\s*(?:"([^"]+)"|'([^']+)'|([^>\s]+))[^>]*>(.*?)</a>""",
            block,
            flags=re.I | re.S,
        ):
            href = next((group for group in (href1, href2, href3) if group), "")
            url = clean_extracted_link(urljoin(base_url, href))
            text = strip_html_tags(inner)
            if not url or not text:
                continue
            key = (url, text)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                {
                    "title": text,
                    "url": url,
                    "release_date": block_date or month_from_url(url) or "1970-01",
                }
            )
    return items


def parse_generic_page_title(html_text: str) -> str:
    title_match = re.search(r"<title>([^<]+)</title>", html_text, flags=re.I)
    if not title_match:
        return ""
    title = strip_html_tags(title_match.group(1))
    title = re.sub(r"\s+[|\\]\s+.+$", "", title).strip()
    return title


def parse_sitemap_urls(xml_text: str, base_url: str) -> List[str]:
    return list(dict.fromkeys(entry["url"] for entry in parse_sitemap_entries(xml_text, base_url) if entry["url"]))


def extract_generic_page_links(html_text: str, page_url: str) -> List[str]:
    links: List[str] = []
    for href in extract_href_values(html_text):
        cleaned = clean_extracted_link(urljoin(page_url, href))
        if cleaned.startswith("http"):
            links.append(cleaned)
    for absolute in re.findall(r'https?://[^\s"\'<>]+', html_text, flags=re.I):
        links.append(clean_extracted_link(absolute))
    return list(dict.fromkeys(link for link in links if link))


def clean_openai_title(title: str) -> str:
    cleaned = strip_html_tags(title)
    cleaned = re.sub(r"\s*-\s*OpenAI Deployment Safety Hub$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*System Card$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*Model Card$", "", cleaned, flags=re.I)
    return cleaned.strip()


def is_openai_model_slug(slug: str) -> bool:
    slug = slug.strip("/").casefold()
    if slug == "o3":
        return True
    if slug.startswith("gpt-oss"):
        return True
    if not slug.startswith("gpt-"):
        return False
    tokens = slug.split("-")
    if len(tokens) < 2 or not tokens[1].isdigit():
        return False
    suffix_tokens = tokens[2:]
    if suffix_tokens and suffix_tokens[0].isdigit():
        suffix_tokens = suffix_tokens[1:]
    allowed_suffixes = {"thinking", "instant", "codex", "max", "mini"}
    return all(token in allowed_suffixes for token in suffix_tokens)


def parse_openai_sitemap_model_urls(xml_text: str, base_url: str) -> List[str]:
    urls: List[str] = []
    for entry in parse_sitemap_entries(xml_text, base_url):
        page_url = clean_extracted_link(entry["url"]).rstrip("/")
        path = re.sub(r"^https?://[^/]+", "", page_url).strip("/")
        if not path or "/" in path:
            continue
        if is_openai_model_slug(path):
            urls.append(page_url)
    return list(dict.fromkeys(urls))


def select_openai_pdf_link(page_url: str, candidate_links: Iterable[str], raw_name: str) -> Optional[str]:
    slug = page_url.rstrip("/").split("/")[-1].casefold()
    raw_lower = raw_name.casefold()

    def score(link: str) -> int:
        lowered = link.casefold()
        value = 0
        if not lowered.endswith(".pdf"):
            return -10_000
        if lowered.startswith(f"{page_url.casefold()}/"):
            value += 500
        if "cdn.openai.com" in lowered:
            value += 250
        if slug and slug in lowered:
            value += 160
        if any(token in lowered for token in ["system-card", "system_card", "model-card", "model_card"]):
            value += 120
        if "card" in lowered:
            value += 40
        if any(token in lowered for token in ["preparedness", "healthbench", "paperbench", "controllability", "/data/eval-sets/", "fig%3a"]):
            value -= 300
        if "sensitive-conversations" in lowered and "sensitive conversations" not in raw_lower:
            value -= 500
        if "addendum" in lowered and "addendum" not in raw_lower:
            value -= 300
        return value

    ranked = sorted(
        ((score(link), link) for link in dict.fromkeys(candidate_links)),
        reverse=True,
    )
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    return None


def select_google_pdf_link(page_url: str, candidate_links: Iterable[str], raw_name: str) -> Optional[str]:
    slug = page_url.rstrip("/").split("/")[-1].casefold()
    normalized_name = re.sub(r"[^a-z0-9]+", "-", raw_name.casefold()).strip("-")

    def score(link: str) -> int:
        lowered = link.casefold()
        value = 0
        matched_model_identity = False
        if not lowered.endswith(".pdf"):
            return -10_000
        if "storage.googleapis.com/deepmind-media/model-cards/" in lowered:
            value += 250
        if slug and slug in lowered:
            value += 220
            matched_model_identity = True
        if normalized_name and normalized_name in lowered:
            value += 160
            matched_model_identity = True
        if "model-card" in lowered or "model_card" in lowered:
            value += 80
        if any(token in lowered for token in ["ai-responsibility-update", "frontier-safety-framework", "technical_agi_safety", "gemini_v1_5_report", "gemini_v2_5_report"]):
            value -= 250
        if not matched_model_identity:
            value -= 500
        return value

    ranked = sorted(
        ((score(link), link) for link in dict.fromkeys(candidate_links)),
        reverse=True,
    )
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    return None


def maybe_apply_openai_release_override(record: Dict[str, Any]) -> Dict[str, Any]:
    override = OPENAI_RELEASE_OVERRIDES.get(str(record.get("model") or ""))
    if not override:
        return record
    release_date = str(override.get("release_date") or "")
    if release_date:
        current = str(record.get("release_date") or "")
        if current == "1970-01" or (month_distance(current, release_date) or 0) >= 6:
            record["release_date"] = release_date
    evidence_url = str(override.get("evidence_url") or "")
    if evidence_url:
        record["evidence_urls"] = list(dict.fromkeys([*record.get("evidence_urls", []), evidence_url]))
    return record


def evidence_type_for_link(url: str, title: str) -> str:
    lowered = f"{title} {url}".casefold()
    if "arxiv.org" in lowered:
        return "arxiv_report"
    if ".pdf" in lowered and ("system card" in lowered or "system-card" in lowered):
        return "official_system_card"
    if ".pdf" in lowered and ("model card" in lowered or "model-card" in lowered):
        return "official_model_card"
    if ".pdf" in lowered:
        return "official_model_card"
    return "official_model_page"


def github_commit_month_for_url(fetcher: Fetcher, url: str) -> Optional[str]:
    raw_match = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/[^/]+/(.+)", url)
    blob_match = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/[^/]+/(.+)", url)
    match = raw_match or blob_match
    if not match:
        return None
    owner, repo, path = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits?path={path}&per_page=1"
    payload = safe_get_json(fetcher, api_url)
    if not isinstance(payload, list) or not payload:
        return None
    commit = payload[0] if isinstance(payload[0], dict) else {}
    commit_info = commit.get("commit") if isinstance(commit, dict) else {}
    author = commit_info.get("author") if isinstance(commit_info, dict) else {}
    if isinstance(author, dict):
        return parse_iso_month(str(author.get("date") or ""))
    return None


def merge_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for record in records:
        key = record["canonical_model_id"]
        existing = merged.get(key)
        if existing is None:
            merged[key] = dict(record)
            continue
        existing["aliases"] = list(dict.fromkeys([*existing["aliases"], *record["aliases"]]))
        existing["candidate_links"] = list(
            dict.fromkeys([*existing["candidate_links"], *record["candidate_links"]])
        )
        existing["evidence_urls"] = list(
            dict.fromkeys([*existing["evidence_urls"], *record["evidence_urls"]])
        )
        if record["confidence"] > existing["confidence"]:
            for field in ["official_link", "source_page", "evidence_type", "confidence"]:
                existing[field] = record[field]
        if existing["release_date"] == "1970-01" and record["release_date"] != "1970-01":
            existing["release_date"] = record["release_date"]
        elif record["release_date"] != "1970-01" and record["release_date"] < existing["release_date"]:
            existing["release_date"] = record["release_date"]
        if record["release_classification"] != "needs_review":
            existing["release_classification"] = record["release_classification"]
            existing["classification_reason"] = record["classification_reason"]
    return sorted(
        merged.values(),
        key=lambda item: (
            str(item.get("release_date") or ""),
            str(item.get("org_slug") or ""),
            str(item.get("model") or ""),
        ),
        reverse=True,
    )


def discover_longcat(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    feed_text = safe_get_text(fetcher, LONGCAT_ARXIV_FEED_URL)
    if not feed_text:
        return records
    for item in parse_longcat_arxiv(feed_text):
        records.append(
            build_record(
                org_slug="meituan",
                raw_name=item["title"],
                release_date=item["release_date"],
                official_link=item["pdf_url"],
                candidate_links=[item["pdf_url"], item["abs_url"]],
                source_page=item["abs_url"],
                evidence_urls=[item["abs_url"], item["pdf_url"]],
                evidence_type="arxiv_report",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_zhipu(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for root_url in [ZHIPU_DOCS_ROOT_URL, BIGMODEL_DOCS_ROOT_URL]:
        root_html = safe_get_text(fetcher, root_url)
        if not root_html:
            continue
        for page_url in parse_zhipu_doc_links(root_html, root_url):
            page_html = safe_get_text(fetcher, page_url)
            if not page_html:
                continue
            page = parse_zhipu_doc_page(page_html, page_url)
            if not page:
                continue
            records.append(
                build_record(
                    org_slug="zhipu",
                    raw_name=page["title"],
                    release_date=page["release_date"],
                    official_link=page["page_url"],
                    candidate_links=[page["page_url"]],
                    source_page=root_url,
                    evidence_urls=[root_url, page["page_url"]],
                    evidence_type="official_model_page",
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )

    for item in parse_hf_models(safe_get_json(fetcher, ZHIPU_HF_MODELS_URL), "zhipu"):
        records.append(
            build_record(
                org_slug="zhipu",
                raw_name=item["title"],
                release_date=item["release_date"],
                official_link=item["page_url"],
                candidate_links=[item["page_url"]],
                source_page=item["page_url"],
                evidence_urls=[item["page_url"]],
                evidence_type="official_hf_model_page",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_minimax(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    news_html = safe_get_text(fetcher, MINIMAX_NEWS_URL)
    if news_html:
        for item in parse_minimax_news(news_html):
            records.append(
                build_record(
                    org_slug="minimax",
                    raw_name=item["title"],
                    release_date=item["release_date"],
                    official_link=item["page_url"],
                    candidate_links=[item["page_url"]],
                    source_page=item["page_url"],
                    evidence_urls=[item["page_url"]],
                    evidence_type="official_news_page",
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )

    article_roots = [MINIMAX_IR_URL, MINIMAX_SITEMAP_URL]
    discovered_pages = set()
    for root_url in article_roots:
        root_html = safe_get_text(fetcher, root_url)
        if not root_html:
            continue
        for page_url in parse_minimax_article_links(root_html):
            for candidate_url in normalize_minimax_article_url(page_url):
                if candidate_url in discovered_pages:
                    continue
                page_html = safe_get_text(fetcher, candidate_url)
                if not page_html:
                    continue
                discovered_pages.add(candidate_url)
                item = parse_minimax_article(page_html, candidate_url)
                if not item:
                    continue
                records.append(
                    build_record(
                        org_slug="minimax",
                        raw_name=item["title"],
                        release_date=item["release_date"],
                        official_link=item["page_url"],
                        candidate_links=[item["page_url"]],
                        source_page=candidate_url,
                        evidence_urls=[candidate_url],
                        evidence_type="official_news_page",
                        discovered_at=discovered_at,
                        alias_config=alias_config,
                    )
                )
    return records


def discover_google(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    seen_links = set()
    model_cards_html = safe_get_text(fetcher, GOOGLE_MODEL_CARDS_URL)
    if model_cards_html:
        for item in parse_google_model_cards(model_cards_html):
            key = item["pdf_url"]
            if key in seen_links:
                continue
            seen_links.add(key)
            records.append(
                build_record(
                    org_slug="google",
                    raw_name=item["title"],
                    release_date=item["release_date"],
                    official_link=item["pdf_url"],
                    candidate_links=[item["pdf_url"]],
                    source_page=GOOGLE_MODEL_CARDS_URL,
                    evidence_urls=[item["pdf_url"], GOOGLE_MODEL_CARDS_URL],
                    evidence_type="official_model_card",
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )
        for item in parse_google_model_card_rows(model_cards_html):
            page_url = item["page_url"]
            if page_url in seen_links:
                continue
            candidate_links = [page_url]
            evidence_urls = [GOOGLE_MODEL_CARDS_URL, page_url]
            official_link = page_url
            evidence_type = "official_model_page"
            if not page_url.lower().endswith(".pdf"):
                page_html = safe_get_text(fetcher, page_url)
                if page_html:
                    extra_links = extract_generic_page_links(page_html, page_url)
                    if pdf_link := select_google_pdf_link(page_url, extra_links, item["title"]):
                        official_link = pdf_link
                        evidence_type = "official_model_card"
            candidate_links = list(dict.fromkeys([page_url, official_link]))
            evidence_urls = list(dict.fromkeys([GOOGLE_MODEL_CARDS_URL, page_url, official_link]))
            seen_links.add(page_url)
            records.append(
                build_record(
                    org_slug="google",
                    raw_name=item["title"],
                    release_date=item["release_date"],
                    official_link=official_link,
                    candidate_links=candidate_links,
                    source_page=GOOGLE_MODEL_CARDS_URL,
                    evidence_urls=evidence_urls,
                    evidence_type=evidence_type,
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )
    gemma_html = safe_get_text(fetcher, GOOGLE_GEMMA_URL)
    for item in parse_google_gemma_cards(gemma_html) if gemma_html else []:
        records.append(
            build_record(
                org_slug="google",
                raw_name=item["title"],
                release_date=item["release_date"],
                official_link=item["page_url"],
                candidate_links=[item["page_url"]],
                source_page=GOOGLE_GEMMA_URL,
                evidence_urls=[GOOGLE_GEMMA_URL, item["page_url"]],
                evidence_type="official_model_page",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    docs_root_html = safe_get_text(fetcher, GOOGLE_GEMMA_DOCS_URL)
    for page_url in parse_google_docs_model_cards(docs_root_html) if docs_root_html else []:
        page_html = safe_get_text(fetcher, page_url)
        if not page_html:
            continue
        title_match = re.search(r"<title>([^<]+)</title>", page_html, flags=re.I)
        if not title_match:
            continue
        raw_name = title_match.group(1).split("|")[0].strip()
        if "shieldgemma/model_card_2" in page_url:
            raw_name = "ShieldGemma 2"
        elif "shieldgemma/model_card" in page_url:
            raw_name = "ShieldGemma"
        elif "model_card_4" in page_url:
            raw_name = "Gemma 4 model card"
        records.append(
            build_record(
                org_slug="google",
                raw_name=raw_name,
                release_date=parse_last_updated_month(page_html) or "1970-01",
                official_link=page_url,
                candidate_links=[page_url],
                source_page=GOOGLE_GEMMA_DOCS_URL,
                evidence_urls=[GOOGLE_GEMMA_DOCS_URL, page_url],
                evidence_type="official_model_page",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_alibaba_qwen(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    official_qwen_models = set()
    for code in QWEN_PAGE_CONFIG_CODES:
        page_config_url = build_qwen_page_config_url(code)
        payload = safe_get_json(fetcher, page_config_url)
        for item in parse_qwen_page_config_items(payload):
            raw_name = qwen_raw_name_from_title(item["title"])
            token_links_url = item["token_links_url"]
            token_links_payload = safe_get_json(fetcher, token_links_url) if token_links_url else []
            token_links = parse_qwen_token_links(token_links_payload)
            token_heading = token_links.get("heading") or ""
            if should_override_qwen_raw_name(raw_name, token_heading):
                raw_name = token_heading
            candidate_links = [
                *token_links.get("links", []),
                token_links_url,
            ]
            ranked_links = [link for link in candidate_links if link]
            official_link = min(ranked_links, key=qwen_link_rank) if ranked_links else (token_links_url or page_config_url)
            evidence_type = evidence_type_for_link(official_link, raw_name)
            official_qwen_models.add(
                canonicalize_model_name("alibaba_qwen", raw_name, alias_config=alias_config).canonical_name
            )
            records.append(
                build_record(
                    org_slug="alibaba_qwen",
                    raw_name=raw_name,
                    release_date=item["release_date"],
                    official_link=official_link,
                    candidate_links=candidate_links,
                    source_page=token_links_url or page_config_url,
                    evidence_urls=[page_config_url, token_links_url, *candidate_links],
                    evidence_type=evidence_type,
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )

    repos = safe_get_json(fetcher, QWEN_GITHUB_REPOS_URL)
    if not isinstance(repos, list) or not repos:
        repos = [
            {
                "name": repo_name,
                "html_url": f"https://github.com/QwenLM/{repo_name}",
                "created_at": "",
            }
            for repo_name in sorted(QWEN_REPO_ALLOWLIST)
        ]

    for repo in repos:
        if not isinstance(repo, dict):
            continue
        repo_name = str(repo.get("name") or "").strip()
        if repo_name not in QWEN_REPO_ALLOWLIST:
            continue
        repo_url = str(repo.get("html_url") or "").strip()
        release_date = parse_iso_month(str(repo.get("created_at") or repo.get("updated_at") or "")) or "1970-01"
        contents_url = f"https://api.github.com/repos/QwenLM/{repo_name}/contents"
        readme_url = f"https://api.github.com/repos/QwenLM/{repo_name}/readme"
        contents = safe_get_json(fetcher, contents_url)
        readme_text = decode_github_readme(safe_get_json(fetcher, readme_url))
        repo_html = safe_get_text(fetcher, repo_url)
        if release_date == "1970-01":
            release_date = infer_month_from_github_repo_html(repo_html) or release_date
        raw_name = parse_markdown_heading(readme_text) or repo_name
        if "qwen" not in raw_name.casefold():
            raw_name = repo_name
        canonical_name = canonicalize_model_name("alibaba_qwen", raw_name, alias_config=alias_config).canonical_name

        pdf_links = []
        if isinstance(contents, list):
            for item in contents:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "")
                if ".pdf" in name.lower():
                    download_url = str(item.get("download_url") or item.get("html_url") or "").strip()
                    if download_url:
                        pdf_links.append(download_url)
        pdf_links.extend(guess_qwen_repo_pdf_links(repo_name, repo_html))
        pdf_commit_month = github_commit_month_for_url(fetcher, pdf_links[0]) if pdf_links else None

        markdown_links = extract_markdown_links(readme_text)
        html_links = extract_links_from_github_repo_html(repo_html, repo_url)
        repo_tokens = qwen_repo_tokens(repo_name)
        arxiv_links = [arxiv_pdf_url(link) for link in markdown_links if "arxiv.org" in link]
        arxiv_links.extend(arxiv_pdf_url(link) for link in html_links if "arxiv.org" in link)
        blog_links = [
            link for link in markdown_links if any(host in link for host in ["qwen.ai", "qwenlm.github.io"])
        ]
        blog_links.extend(
            link for link in html_links if any(host in link for host in ["qwen.ai", "qwenlm.github.io"])
        )
        preferred_blog_links = [
            link
            for link in blog_links
            if any(token in link.casefold() for token in repo_tokens)
        ]
        if preferred_blog_links:
            blog_links = preferred_blog_links
        arxiv_pdfs = [link for link in arxiv_links if link]
        if pdf_commit_month:
            arxiv_pdfs = [
                link
                for link in arxiv_pdfs
                if (arxiv_month := month_from_arxiv_url(link)) is not None
                and (distance := month_distance(pdf_commit_month, arxiv_month)) is not None
                and distance <= 6
            ]
        candidate_links = [
            *pdf_links,
            *arxiv_pdfs,
            *blog_links,
            *[link for link in html_links if link.endswith(".pdf")],
            repo_url,
        ]
        evidence_type = "official_model_page"
        official_link = repo_url
        if pdf_links:
            official_link = pdf_links[0]
            evidence_type = "official_model_card"
        elif arxiv_pdfs:
            official_link = arxiv_pdfs[0]
            evidence_type = "arxiv_report"
        elif blog_links:
            official_link = blog_links[0]

        if pdf_links and blog_links:
            release_date = infer_month_from_blog_page(fetcher, blog_links[0]) or release_date
        elif arxiv_pdfs:
            release_date = month_from_arxiv_url(arxiv_pdfs[0]) or release_date
        elif blog_links:
            release_date = infer_month_from_blog_page(fetcher, blog_links[0]) or release_date
        if pdf_links and pdf_commit_month:
            if release_date == "1970-01":
                release_date = pdf_commit_month
            else:
                distance = month_distance(release_date, pdf_commit_month)
                if distance is not None and distance <= 2:
                    release_date = min(release_date, pdf_commit_month)
        if canonical_name in official_qwen_models:
            release_date = "1970-01"

        records.append(
            build_record(
                org_slug="alibaba_qwen",
                raw_name=raw_name,
                release_date=release_date,
                official_link=official_link,
                candidate_links=candidate_links,
                source_page=repo_url,
                evidence_urls=[repo_url, *candidate_links],
                evidence_type=evidence_type,
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_vendor_arxiv(
    org_slug: str,
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    vendor = VENDOR_REGISTRY[org_slug]
    for query_config in vendor.get("arxiv_queries", []):
        if not isinstance(query_config, dict):
            continue
        query = str(query_config.get("query") or "").strip()
        if not query:
            continue
        include_patterns = [re.compile(pattern, re.I) for pattern in query_config.get("include_patterns", [])]
        feed_text = safe_get_text(fetcher, build_arxiv_query_url(query))
        if not feed_text:
            continue
        for item in parse_arxiv_feed(feed_text):
            title = item["title"]
            if include_patterns and not any(pattern.search(title) for pattern in include_patterns):
                continue
            records.append(
                build_record(
                    org_slug=org_slug,
                    raw_name=title,
                    release_date=item["release_date"],
                    official_link=item["pdf_url"],
                    candidate_links=[item["pdf_url"], item["abs_url"]],
                    source_page=item["abs_url"],
                    evidence_urls=[item["abs_url"], item["pdf_url"]],
                    evidence_type="arxiv_report",
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )
    return records


def discover_vendor_catalog(
    org_slug: str,
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    vendor = VENDOR_REGISTRY[org_slug]
    raw_patterns = [re.compile(pattern, re.I) for pattern in vendor.get("catalog_patterns", [])]
    if not raw_patterns:
        return []
    records: List[Dict[str, Any]] = []
    seen_pages = set()
    for source in vendor.get("sources", []):
        if not isinstance(source, dict):
            continue
        source_url = str(source.get("url") or "").strip()
        if not source_url:
            continue
        source_html = safe_get_text(fetcher, source_url)
        if not source_html:
            continue
        source_kind = str(source.get("kind") or "")
        if "sitemap" in source_kind:
            items = [
                {
                    "title": url.rstrip("/").split("/")[-1].replace("-", " "),
                    "url": url,
                    "release_date": month_from_url(url) or "1970-01",
                }
                for url in parse_sitemap_urls(source_html, source_url)
            ]
        else:
            items = parse_catalog_anchors(source_html, source_url)
        for item in items:
            haystack = f"{item['title']} {item['url']}"
            if not any(pattern.search(haystack) for pattern in raw_patterns):
                continue
            page_url = item["url"]
            page_html = ""
            candidate_links = [page_url]
            if not page_url.lower().endswith(".pdf") and page_url not in seen_pages:
                seen_pages.add(page_url)
                page_html = safe_get_text(fetcher, page_url)
                candidate_links.extend(extract_generic_page_links(page_html, page_url))
            page_title = parse_generic_page_title(page_html) if page_html else ""
            raw_name = page_title or item["title"]
            pdf_links = [link for link in candidate_links if link.lower().endswith(".pdf")]
            arxiv_links = [arxiv_pdf_url(link) or link for link in candidate_links if "arxiv.org" in link]
            official_link = page_url
            evidence_type = evidence_type_for_link(page_url, raw_name)
            if pdf_links:
                official_link = pdf_links[0]
                evidence_type = evidence_type_for_link(official_link, raw_name)
            elif arxiv_links:
                official_link = arxiv_links[0]
                evidence_type = "arxiv_report"
            release_date = (
                item["release_date"]
                if item["release_date"] != "1970-01"
                else parse_last_updated_month(page_html)
                or month_from_date_text(strip_html_tags(page_html))
                or month_from_url(official_link)
                or "1970-01"
            )
            records.append(
                build_record(
                    org_slug=org_slug,
                    raw_name=raw_name,
                    release_date=release_date,
                    official_link=official_link,
                    candidate_links=candidate_links,
                    source_page=source_url,
                    evidence_urls=[source_url, *candidate_links],
                    evidence_type=evidence_type,
                    discovered_at=discovered_at,
                    alias_config=alias_config,
                )
            )
    return records


def discover_vendor_github_repos(
    org_slug: str,
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    vendor = VENDOR_REGISTRY[org_slug]
    records: List[Dict[str, Any]] = []
    for repo in vendor.get("github_repos", []):
        if not isinstance(repo, dict):
            continue
        repo_url = str(repo.get("url") or "").strip()
        if not repo_url:
            continue
        repo_html = safe_get_text(fetcher, repo_url)
        if not repo_html:
            continue
        title_hint = str(repo.get("title_hint") or "").strip()
        raw_name = title_hint or parse_generic_page_title(repo_html) or repo_url.rstrip("/").split("/")[-1]
        candidate_links = extract_links_from_github_repo_html(repo_html, repo_url)
        official_link = next((link for link in candidate_links if link.lower().endswith(".pdf")), repo_url)
        evidence_type = evidence_type_for_link(official_link, raw_name)
        release_date = (
            github_commit_month_for_url(fetcher, official_link)
            or month_from_date_text(strip_html_tags(repo_html))
            or month_from_url(official_link)
            or "1970-01"
        )
        records.append(
            build_record(
                org_slug=org_slug,
                raw_name=raw_name,
                release_date=release_date,
                official_link=official_link,
                candidate_links=[official_link, *candidate_links, repo_url],
                source_page=repo_url,
                evidence_urls=[repo_url, *candidate_links],
                evidence_type=evidence_type,
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_openai(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    sitemap_url = "https://deploymentsafety.openai.com/sitemap.xml"
    sitemap_xml = safe_get_text(fetcher, sitemap_url)
    for page_url in parse_openai_sitemap_model_urls(sitemap_xml, sitemap_url):
        page_html = safe_get_text(fetcher, page_url)
        if not page_html:
            continue
        title_match = re.search(r"<title>([^<]+)</title>", page_html, flags=re.I)
        raw_name = clean_openai_title(title_match.group(1)) if title_match else page_url.rstrip("/").split("/")[-1]
        page_links = extract_generic_page_links(page_html, page_url)
        official_link = select_openai_pdf_link(page_url, [page_url, *page_links], raw_name) or page_url
        candidate_links = list(dict.fromkeys([page_url, official_link]))
        release_date = (
            month_from_date_text(strip_html_tags(page_html[:5000]))
            or explicit_release_month_from_html(page_html, allow_last_updated=False)
            or "1970-01"
        )
        record = build_record(
            org_slug="openai",
            raw_name=raw_name,
            release_date=release_date,
            official_link=official_link,
            candidate_links=candidate_links,
            source_page=sitemap_url,
            evidence_urls=[sitemap_url, page_url, official_link],
            evidence_type=evidence_type_for_link(official_link, raw_name),
            discovered_at=discovered_at,
            alias_config=alias_config,
        )
        records.append(maybe_apply_openai_release_override(record))
    return [record for record in merge_records(records) if record["release_classification"] == "model_release"]


def discover_anthropic(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    sitemap_xml = safe_get_text(fetcher, "https://www.anthropic.com/sitemap.xml")
    for entry in parse_sitemap_entries(sitemap_xml, "https://www.anthropic.com/sitemap.xml"):
        page_url = entry["url"]
        if not re.search(r"/news/claude-(?:opus|sonnet|haiku)-", page_url):
            continue
        page_html = safe_get_text(fetcher, page_url)
        if not page_html:
            continue
        candidate_links = [page_url, *extract_generic_page_links(page_html, page_url)]
        page_title = parse_generic_page_title(page_html) or page_url.rstrip("/").split("/")[-1].replace("-", " ")
        pdf_links = [
            link
            for link in candidate_links
            if link.lower().endswith(".pdf") and "anthropic.com" in link
        ]
        official_link = pdf_links[0] if pdf_links else page_url
        release_date = (
            explicit_release_month_from_html(page_html, allow_last_updated=False)
            or parse_iso_month(entry["lastmod"])
            or "1970-01"
        )
        records.append(
            build_record(
                org_slug="anthropic",
                raw_name=page_title,
                release_date=release_date,
                official_link=official_link,
                candidate_links=candidate_links,
                source_page="https://www.anthropic.com/sitemap.xml",
                evidence_urls=["https://www.anthropic.com/sitemap.xml", *candidate_links],
                evidence_type=evidence_type_for_link(official_link, page_title),
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_xai(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records = discover_vendor_catalog("xai", fetcher, discovered_at, alias_config)
    release_notes_html = safe_get_text(fetcher, XAI_RELEASE_NOTES_URL)
    for item in parse_xai_release_notes(release_notes_html):
        records.append(
            build_record(
                org_slug="xai",
                raw_name=item["title"],
                release_date=item["release_date"],
                official_link=item["page_url"],
                candidate_links=[item["page_url"], XAI_RELEASE_NOTES_URL],
                source_page=XAI_RELEASE_NOTES_URL,
                evidence_urls=[XAI_RELEASE_NOTES_URL, item["page_url"]],
                evidence_type="official_model_page",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_meta(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    direct_page_html = safe_get_text(fetcher, META_LLAMA4_BLOG_URL)
    if direct_page_html and "llama 4" in direct_page_html.casefold():
        records.append(
            build_record(
                org_slug="meta",
                raw_name="Llama 4 Scout/Maverick",
                release_date=explicit_release_month_from_html(direct_page_html, allow_last_updated=False) or "1970-01",
                official_link=META_LLAMA4_BLOG_URL,
                candidate_links=[META_LLAMA4_BLOG_URL, "https://www.llama.com/"],
                source_page=META_LLAMA4_BLOG_URL,
                evidence_urls=[META_LLAMA4_BLOG_URL, "https://www.llama.com/"],
                evidence_type="official_model_page",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
        return records
    llama_home_html = safe_get_text(fetcher, "https://www.llama.com/")
    if llama_home_html and all(token in llama_home_html.casefold() for token in ["llama 4", "scout", "maverick"]):
        records.append(
            build_record(
                org_slug="meta",
                raw_name="Llama 4 Scout/Maverick",
                release_date=explicit_release_month_from_html(llama_home_html, allow_last_updated=False) or "1970-01",
                official_link="https://www.llama.com/",
                candidate_links=["https://www.llama.com/"],
                source_page="https://www.llama.com/",
                evidence_urls=["https://www.llama.com/"],
                evidence_type="official_model_page",
                discovered_at=discovered_at,
                alias_config=alias_config,
            )
        )
    return records


def discover_baidu(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_catalog("baidu", fetcher, discovered_at, alias_config)


def discover_deepseek(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_arxiv("deepseek", fetcher, discovered_at, alias_config)


def discover_moonshot(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return [
        *discover_vendor_arxiv("moonshot", fetcher, discovered_at, alias_config),
        *discover_vendor_github_repos("moonshot", fetcher, discovered_at, alias_config),
    ]


def discover_stepfun(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_arxiv("stepfun", fetcher, discovered_at, alias_config)


def discover_tencent(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_arxiv("tencent", fetcher, discovered_at, alias_config)


def discover_baichuan(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_arxiv("baichuan", fetcher, discovered_at, alias_config)


def discover_quark(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_arxiv("quark", fetcher, discovered_at, alias_config)


def discover_bytedance(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_arxiv("bytedance", fetcher, discovered_at, alias_config)


def discover_inclusionai(
    fetcher: Fetcher,
    discovered_at: str,
    alias_config: Dict[str, Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    return discover_vendor_github_repos("inclusionai", fetcher, discovered_at, alias_config)


DISCOVERY_DISPATCH = {
    "openai": discover_openai,
    "anthropic": discover_anthropic,
    "xai": discover_xai,
    "meta": discover_meta,
    "alibaba_qwen": discover_alibaba_qwen,
    "quark": discover_quark,
    "deepseek": discover_deepseek,
    "moonshot": discover_moonshot,
    "stepfun": discover_stepfun,
    "tencent": discover_tencent,
    "baidu": discover_baidu,
    "bytedance": discover_bytedance,
    "baichuan": discover_baichuan,
    "inclusionai": discover_inclusionai,
    "google": discover_google,
    "meituan": discover_longcat,
    "minimax": discover_minimax,
    "zhipu": discover_zhipu,
}


def discover_all_models(
    *,
    until: str,
    fetcher: Optional[Fetcher] = None,
    discovered_at: Optional[str] = None,
) -> List[Dict[str, Any]]:
    del until  # current sources already yield latest-first results; retained for CLI contract
    fetcher = fetcher or RequestsFetcher()
    discovered_at = discovered_at or datetime.now(timezone.utc).isoformat()
    alias_config = load_alias_config()
    records: List[Dict[str, Any]] = []
    for vendor_slug in VENDOR_REGISTRY:
        discoverer = DISCOVERY_DISPATCH.get(vendor_slug)
        if discoverer is not None:
            records.extend(discoverer(fetcher, discovered_at, alias_config))
            continue
        vendor = VENDOR_REGISTRY[vendor_slug]
        if vendor.get("arxiv_queries"):
            records.extend(discover_vendor_arxiv(vendor_slug, fetcher, discovered_at, alias_config))
        elif vendor.get("github_repos"):
            records.extend(discover_vendor_github_repos(vendor_slug, fetcher, discovered_at, alias_config))
        elif vendor.get("catalog_patterns"):
            records.extend(discover_vendor_catalog(vendor_slug, fetcher, discovered_at, alias_config))
    return merge_records(records)


def downloadable_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [record for record in records if record.get("release_classification") == "model_release"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover latest official model-release records")
    parser.add_argument("--until", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--downloadable-only",
        action="store_true",
        help="Only write model_release records suitable for download_papers.py",
    )
    args = parser.parse_args()

    records = discover_all_models(until=args.until)
    if args.downloadable_only:
        records = downloadable_records(records)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"records={len(records)}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
