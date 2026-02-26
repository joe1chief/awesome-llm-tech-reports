import re
import html
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency fallback
    PdfReader = None


ROOT = Path(__file__).resolve().parent

SOURCE_PRIORITY_RULES: List[Tuple[str, int]] = [
    ("arxiv.org/pdf/", 100),
    ("arxiv.org/abs/", 98),
    ("cdn.openai.com/pdf/", 95),
    ("assets.anthropic.com/", 94),
    ("www-cdn.anthropic.com/", 94),
    ("storage.googleapis.com/deepmind-media/model-cards/", 93),
    ("data.x.ai/", 92),
    ("yiyan.baidu.com/blog/publication/", 90),
    ("lf3-static.bytednsdoc.com/", 89),
    ("raw.githubusercontent.com/", 88),
]
_WEB_RENDER_READY: Optional[bool] = None

MODELS: List[Dict[str, Any]] = [
    # 2026-02
    {
        "release_date": "2026-02",
        "org": "智谱AI",
        "org_slug": "zhipu",
        "model": "GLM-5",
        "core_feature": "MoE 744B/40B，异步强化学习与 Agent 工程能力。",
        "official_link": "https://arxiv.org/abs/2602.15763",
    },
    {
        "release_date": "2026-02",
        "org": "阶跃星辰",
        "org_slug": "stepfun",
        "model": "Step-3.5-Flash",
        "core_feature": "MoE 196B/11B，混合注意力与多 token 预测。",
        "official_link": "https://arxiv.org/abs/2602.10604",
    },
    {
        "release_date": "2026-02",
        "org": "百度",
        "org_slug": "baidu",
        "model": "ERNIE 5.0",
        "core_feature": "统一自回归多模态，超稀疏 MoE，弹性训练。",
        "official_link": "https://arxiv.org/abs/2602.04705",
    },
    {
        "release_date": "2026-02",
        "org": "百川智能",
        "org_slug": "baichuan",
        "model": "Baichuan-M3",
        "core_feature": "面向临床问诊的主动信息采集与长程推理。",
        "official_link": "https://arxiv.org/abs/2602.06570",
    },
    {
        "release_date": "2026-02",
        "org": "字节跳动",
        "org_slug": "bytedance",
        "model": "MedXIAOHE",
        "core_feature": "医疗多模态基础模型，实体感知预训练与工具增强。",
        "official_link": "https://arxiv.org/abs/2602.12705",
    },
    {
        "release_date": "2026-02",
        "org": "OpenAI",
        "org_slug": "openai",
        "model": "GPT-5.3-Codex",
        "core_feature": "高能力 agentic 编码模型，面向长程工具任务。",
        "official_link": "https://cdn.openai.com/pdf/8df7697b-c1b2-4222-be00-1fd3298f351d/codex_system_card.pdf",
    },
    {
        "release_date": "2026-02",
        "org": "Anthropic",
        "org_slug": "anthropic",
        "model": "Claude Opus 4.6",
        "core_feature": "系统卡覆盖高能力编码、长上下文与对齐评估。",
        "official_link": "https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf",
    },
    {
        "release_date": "2026-02",
        "org": "字节跳动",
        "org_slug": "bytedance",
        "model": "Seed 2.0",
        "core_feature": "面向真实复杂任务与企业工作流的 Seed 2.0 系列。",
        "official_link": "https://lf3-static.bytednsdoc.com/obj/eden-cn/lapzild-tss/ljhwZthlaukjlkulzlp/seed2/0214/Seed2.0%20Model%20Card.pdf",
    },
    {
        "release_date": "2026-02",
        "org": "阿里巴巴",
        "org_slug": "alibaba_qwen",
        "model": "Qwen 3.5",
        "core_feature": "新一代通用模型系列，官方仅公开博客页。",
        "official_link": "https://qwen.ai/blog?id=qwen3.5",
    },
    {
        "release_date": "2026-02",
        "org": "MiniMax",
        "org_slug": "minimax",
        "model": "MiniMax M2.5",
        "core_feature": "RL 大规模训练，强化编码/搜索/工具调用效率。",
        "official_link": "https://www.minimax.io/news/minimax-m25",
    },
    {
        "release_date": "2026-02",
        "org": "月之暗面",
        "org_slug": "moonshot",
        "model": "Kimi K2.5",
        "core_feature": "多模态 1T MoE，Agent Swarm 并行子任务。",
        "official_link": "https://github.com/MoonshotAI/Kimi-K2.5/raw/master/tech_report.pdf",
    },
    {
        "release_date": "2026-02",
        "org": "inclusionAI",
        "org_slug": "inclusionai",
        "model": "Ling 2.5",
        "core_feature": "1T/63B 混合线性注意力，强调工具调用与效率。",
        "official_link": "https://github.com/inclusionAI/Ling-V2.5",
    },
    # 2025-12
    {
        "release_date": "2025-12",
        "org": "OpenAI",
        "org_slug": "openai",
        "model": "GPT-5.2",
        "core_feature": "系统卡模型，强化推理与可靠性能力。",
        "official_link": "https://cdn.openai.com/pdf/3a4153c8-c748-4b71-8e31-aecbde944f8d/oai_5_2_system-card.pdf",
    },
    {
        "release_date": "2025-12",
        "org": "DeepSeek",
        "org_slug": "deepseek",
        "model": "DeepSeek V3.2",
        "core_feature": "DSA 稀疏注意力与可扩展 RL 框架。",
        "official_link": "https://arxiv.org/abs/2512.02556",
    },
    {
        "release_date": "2025-12",
        "org": "Google",
        "org_slug": "google",
        "model": "Gemini 3 Flash",
        "core_feature": "高效率 MoE 多模态模型，支持长上下文。",
        "official_link": "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Flash-Model-Card.pdf",
    },
    {
        "release_date": "2025-12",
        "org": "阶跃星辰",
        "org_slug": "stepfun",
        "model": "Step-DeepResearch",
        "core_feature": "面向深度研究任务的长流程 Agent 评测能力。",
        "official_link": "https://arxiv.org/abs/2512.20491",
    },
    # 2025-11
    {
        "release_date": "2025-11",
        "org": "Google",
        "org_slug": "google",
        "model": "Gemini 3 Pro",
        "core_feature": "强调复杂推理与 agentic 工作流。",
        "official_link": "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf",
    },
    {
        "release_date": "2025-11",
        "org": "xAI",
        "org_slug": "xai",
        "model": "Grok 4.1",
        "core_feature": "Grok 4 系列迭代版，持续强化安全评测。",
        "official_link": "https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf",
    },
    {
        "release_date": "2025-11",
        "org": "阿里巴巴",
        "org_slug": "alibaba_qwen",
        "model": "Qwen3-VL",
        "core_feature": "Qwen 视觉语言技术报告，聚焦多模态推理。",
        "official_link": "https://arxiv.org/abs/2511.21631",
    },
    # 2025-10/09
    {
        "release_date": "2025-10",
        "org": "美团",
        "org_slug": "meituan",
        "model": "LongCat-Flash-Omni",
        "core_feature": "560B/27B 激活的开源全模态模型，课程式渐进训练实现低时延实时音视频交互。",
        "official_link": "https://arxiv.org/abs/2511.00279",
    },
    {
        "release_date": "2025-10",
        "org": "MiniMax",
        "org_slug": "minimax",
        "model": "MiniMax M2.0",
        "core_feature": "MoE 架构与 256K 上下文，开源仓库公开。",
        "official_link": "https://github.com/MiniMax-AI/MiniMax-M2",
    },
    {
        "release_date": "2025-09",
        "org": "xAI",
        "org_slug": "xai",
        "model": "Grok 4 Fast",
        "core_feature": "低时延推理版 Grok 4，覆盖安全评测。",
        "official_link": "https://data.x.ai/2025-09-19-grok-4-fast-model-card.pdf",
    },
    {
        "release_date": "2025-09",
        "org": "DeepSeek",
        "org_slug": "deepseek",
        "model": "DeepSeek V3.1-Terminus",
        "core_feature": "V3.1 工程迭代版，强化稳定性与 agent 可靠性。",
        "official_link": "https://arxiv.org/abs/2412.19437",
    },
    {
        "release_date": "2025-09",
        "org": "百川智能",
        "org_slug": "baichuan",
        "model": "Baichuan-M2",
        "core_feature": "医疗验证系统驱动的 32B 医疗模型。",
        "official_link": "https://arxiv.org/abs/2509.02208",
    },
    {
        "release_date": "2025-09",
        "org": "美团",
        "org_slug": "meituan",
        "model": "LongCat-Flash",
        "core_feature": "560B MoE，零计算专家提升推理效率。",
        "official_link": "https://arxiv.org/abs/2509.01322",
    },
    {
        "release_date": "2025-09",
        "org": "美团",
        "org_slug": "meituan",
        "model": "LongCat-Flash-Thinking",
        "core_feature": "在 Flash 基础上强化形式推理与工具推理。",
        "official_link": "https://arxiv.org/abs/2509.18883",
    },
    # 2025-08/07
    {
        "release_date": "2025-08",
        "org": "智谱AI",
        "org_slug": "zhipu",
        "model": "GLM-4.5",
        "core_feature": "ARC 能力导向基础模型，重推理与编码。",
        "official_link": "https://arxiv.org/abs/2508.06471",
    },
    {
        "release_date": "2025-08",
        "org": "OpenAI",
        "org_slug": "openai",
        "model": "GPT-5",
        "core_feature": "统一系统卡，覆盖多模型路由与安全评估。",
        "official_link": "https://cdn.openai.com/pdf/8124a3ce-ab78-4f06-96eb-49ea29ffb52f/gpt5-system-card-aug7.pdf",
    },
    {
        "release_date": "2025-08",
        "org": "OpenAI",
        "org_slug": "openai",
        "model": "gpt-oss-120b/20b",
        "core_feature": "Apache 2.0 开源权重，强调工具调用与推理。",
        "official_link": "https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf",
    },
    {
        "release_date": "2025-08",
        "org": "夸克(阿里)",
        "org_slug": "quark",
        "model": "QuarkMed",
        "core_feature": "医疗 1T 数据与可验证 RL 流水线。",
        "official_link": "https://arxiv.org/abs/2508.11894",
    },
    {
        "release_date": "2025-07",
        "org": "月之暗面",
        "org_slug": "moonshot",
        "model": "Kimi K2.0",
        "core_feature": "1T MoE，MuonClip 优化器与 agentic 训练。",
        "official_link": "https://arxiv.org/abs/2507.20534",
    },
    {
        "release_date": "2025-08",
        "org": "xAI",
        "org_slug": "xai",
        "model": "Grok 4",
        "core_feature": "高能力推理与工具使用，模型卡公开。",
        "official_link": "https://data.x.ai/2025-08-20-grok-4-model-card.pdf",
    },
    {
        "release_date": "2025-07",
        "org": "Google",
        "org_slug": "google",
        "model": "Gemini 2.5 Pro",
        "core_feature": "原生多模态 MoE Transformer，1M 上下文。",
        "official_link": "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Pro-Model-Card.pdf",
    },
    {
        "release_date": "2025-07",
        "org": "Google",
        "org_slug": "google",
        "model": "Gemini 2.5 Flash",
        "core_feature": "高效推理模型，长上下文与低时延平衡。",
        "official_link": "https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Flash-Model-Card.pdf",
    },
    # 2025-06/05
    {
        "release_date": "2025-06",
        "org": "Anthropic",
        "org_slug": "anthropic",
        "model": "Claude Opus 4.5",
        "core_feature": "高能力系统卡版本，覆盖多项安全评估。",
        "official_link": "https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf",
    },
    {
        "release_date": "2025-06",
        "org": "Anthropic",
        "org_slug": "anthropic",
        "model": "Claude Sonnet 4.5",
        "core_feature": "Sonnet 4.5 系统卡，推理与工具能力增强。",
        "official_link": "https://assets.anthropic.com/m/12f214efcc2f457a/original/Claude-Sonnet-4-5-System-Card.pdf",
    },
    {
        "release_date": "2025-05",
        "org": "阿里巴巴",
        "org_slug": "alibaba_qwen",
        "model": "Qwen3",
        "core_feature": "统一思考框架，覆盖思考/非思考双模式。",
        "official_link": "https://arxiv.org/abs/2505.09388",
    },
    {
        "release_date": "2025-05",
        "org": "腾讯",
        "org_slug": "tencent",
        "model": "Yuanbao (Hunyuan-TurboS)",
        "core_feature": "Mamba-Transformer 混合 MoE 与自适应 CoT。",
        "official_link": "https://arxiv.org/abs/2505.15431",
    },
    {
        "release_date": "2025-05",
        "org": "字节跳动",
        "org_slug": "bytedance",
        "model": "Seed1.5-VL",
        "core_feature": "20B 激活 MoE 多模态模型，视觉推理增强。",
        "official_link": "https://arxiv.org/abs/2505.07062",
    },
    {
        "release_date": "2025-06",
        "org": "百度",
        "org_slug": "baidu",
        "model": "ERNIE 4.5",
        "core_feature": "异构 MoE 多模态家族，工业级训练与部署。",
        "official_link": "https://yiyan.baidu.com/blog/publication/ERNIE_Technical_Report.pdf",
    },
    # 2025-04/03
    {
        "release_date": "2025-05",
        "org": "Anthropic",
        "org_slug": "anthropic",
        "model": "Claude Opus 4 / Sonnet 4",
        "core_feature": "Claude 4 系列系统卡，混合推理能力。",
        "official_link": "https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf",
    },
    {
        "release_date": "2025-04",
        "org": "OpenAI",
        "org_slug": "openai",
        "model": "o3 / o4-mini",
        "core_feature": "推理模型系统卡，覆盖安全与能力评估。",
        "official_link": "https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf",
    },
    {
        "release_date": "2025-04",
        "org": "Meta",
        "org_slug": "meta",
        "model": "Llama 4 Scout/Maverick",
        "core_feature": "原生多模态 MoE；Scout 支持超长上下文。",
        "official_link": "https://ai.meta.com/blog/llama-4-multimodal-intelligence/",
    },
    {
        "release_date": "2025-04",
        "org": "字节跳动",
        "org_slug": "bytedance",
        "model": "Seed1.5-Thinking",
        "core_feature": "强化学习驱动推理模型，20B 激活/200B 总参数。",
        "official_link": "https://arxiv.org/abs/2504.13914",
    },
    {
        "release_date": "2025-03",
        "org": "Google",
        "org_slug": "google",
        "model": "Gemma 3",
        "core_feature": "开源多模态模型系列，强调可部署性。",
        "official_link": "https://arxiv.org/abs/2503.19786",
    },
    # 2025-01/02
    {
        "release_date": "2025-01",
        "org": "DeepSeek",
        "org_slug": "deepseek",
        "model": "DeepSeek R1",
        "core_feature": "通过纯 RL 激发推理能力并开源蒸馏路线。",
        "official_link": "https://arxiv.org/abs/2501.12948",
    },
    {
        "release_date": "2025-01",
        "org": "DeepSeek",
        "org_slug": "deepseek",
        "model": "DeepSeek V3",
        "core_feature": "MoE 671B/37B，MLA 与高效训练实践。",
        "official_link": "https://arxiv.org/abs/2412.19437",
    },
]


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=1,
        connect=1,
        read=1,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def normalize_url(url: str) -> str:
    if "arxiv.org/abs/" in url:
        return url.replace("/abs/", "/pdf/")
    if "github.com" in url and "/blob/" in url and url.endswith(".pdf"):
        return url.replace("/blob/", "/raw/")
    return url


def collect_candidate_links(record: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []
    raw_candidates = record.get("candidate_links")
    if isinstance(raw_candidates, list):
        for c in raw_candidates:
            if isinstance(c, str) and c.strip():
                candidates.append(normalize_url(c.strip()))
    official = record.get("official_link")
    if isinstance(official, str) and official.strip():
        candidates.append(normalize_url(official.strip()))

    deduped: List[str] = []
    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        deduped.append(c)
    return deduped


def source_priority_score(url: str) -> int:
    u = url.lower()
    for pattern, score in SOURCE_PRIORITY_RULES:
        if pattern in u:
            return score
    if is_pdf_url(url):
        return 75
    if should_render_webpage_to_pdf(url):
        if "github.com/" in u and "/raw/" not in u:
            return 35
        return 45
    return 10


def can_render_webpage_to_pdf() -> bool:
    global _WEB_RENDER_READY
    if _WEB_RENDER_READY is not None:
        return _WEB_RENDER_READY
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        _WEB_RENDER_READY = True
    except Exception:
        _WEB_RENDER_READY = False
    return _WEB_RENDER_READY


def probe_source_url(session: requests.Session, url: str) -> Tuple[bool, str]:
    try:
        if is_pdf_url(url):
            with session.get(url, timeout=20, stream=True) as resp:
                if resp.status_code >= 400:
                    return False, f"http_{resp.status_code}"
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if "pdf" in content_type:
                    return True, "pdf_content_type"
                first_chunk = b""
                for chunk in resp.iter_content(chunk_size=16):
                    if chunk:
                        first_chunk = chunk
                        break
                if first_chunk.startswith(b"%PDF-"):
                    return True, "pdf_signature"
                return False, f"not_pdf:{content_type or 'unknown'}"

        if should_render_webpage_to_pdf(url):
            resp = session.get(url, timeout=20)
            if resp.status_code >= 400:
                return False, f"http_{resp.status_code}"
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "html" not in content_type and "text" not in content_type:
                return False, f"non_html:{content_type or 'unknown'}"
            if not can_render_webpage_to_pdf():
                return False, "renderer_unavailable"
            return True, "html_renderable"

        return False, "unsupported_scheme"
    except Exception as e:
        return False, f"probe_error:{type(e).__name__}"


def choose_best_source_url(
    session: requests.Session,
    record: Dict[str, Any],
    probe_cache: Dict[str, Tuple[bool, str]],
) -> Tuple[str, str]:
    candidates = collect_candidate_links(record)
    if not candidates:
        return "", "no_candidate_url"

    available: List[Tuple[int, int, str, str]] = []
    unavailable: List[Tuple[int, int, str, str]] = []
    for idx, url in enumerate(candidates):
        base = source_priority_score(url)
        if url in probe_cache:
            ok, reason = probe_cache[url]
        else:
            ok, reason = probe_source_url(session, url)
            probe_cache[url] = (ok, reason)
        bucket = available if ok else unavailable
        bucket.append((base, -idx, url, reason))

    if available:
        base, _, url, reason = max(available)
        return url, f"probe_ok:{reason}|priority={base}"

    base, _, url, reason = max(unavailable)
    return url, f"probe_fail_fallback:{reason}|priority={base}"


def extract_arxiv_id(url: str) -> Optional[str]:
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", url)
    if not m:
        return None
    return m.group(1)


def extract_year_month_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    patterns = [
        # YYYY-MM-DD / YYYY/MM/DD / YYYY.MM.DD
        r"(20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])",
        # YYYY-MM / YYYY/MM / YYYY.MM
        r"(20\d{2})[-/\.](0?[1-9]|1[0-2])",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}"
    return None


def extract_year_month_from_url(url: str) -> Optional[str]:
    return extract_year_month_from_text(url)


def fetch_arxiv_published_month(session: requests.Session, arxiv_id: str) -> Optional[str]:
    try:
        resp = session.get(
            "https://export.arxiv.org/api/query",
            params={"id_list": arxiv_id},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception:
        return None
    m = re.search(r"<published>(\d{4})-(\d{2})-\d{2}T", resp.text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def fetch_webpage_published_month(session: requests.Session, url: str) -> Optional[str]:
    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
    except Exception:
        return None

    body = resp.text[:300000]
    patterns = [
        # OpenGraph / metadata published date
        r'(?i)article:published_time[^>]*content=["\'](20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])',
        r'(?i)datePublished["\']?\s*[:=]\s*["\'](20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])',
        # Common inline date blocks like 2026/02/16 · ...
        r"(20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\s*[·|\\-]",
        # Keyword-near-date fallback
        r'(?i)(published|release(?:d)?|date)\D{0,30}(20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])',
    ]
    for p in patterns:
        m = re.search(p, body)
        if not m:
            continue
        if len(m.groups()) == 3:
            year, month = m.group(1), m.group(2)
        else:
            year, month = m.group(2), m.group(3)
        return f"{year}-{int(month):02d}"
    return None


def infer_release_month_from_source(
    session: requests.Session,
    url: str,
) -> Tuple[Optional[str], str]:
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id:
        published = fetch_arxiv_published_month(session, arxiv_id)
        if published:
            return published, "arxiv_published"

    url_month = extract_year_month_from_url(url)
    if url_month:
        return url_month, "url_pattern"

    if should_render_webpage_to_pdf(url):
        web_month = fetch_webpage_published_month(session, url)
        if web_month:
            return web_month, "webpage_published"

    return None, "manual_fallback"


def resolve_release_month(
    session: requests.Session,
    declared_release_date: str,
    url: str,
    link_frequency: Dict[str, int],
    cache: Dict[str, Tuple[Optional[str], str]],
) -> Tuple[str, str]:
    # If one source link maps to multiple model entries, preserve manual release dates.
    if link_frequency.get(url, 0) > 1:
        return declared_release_date, "manual_shared_link"

    if url in cache:
        inferred, source = cache[url]
    else:
        inferred, source = infer_release_month_from_source(session, url)
        cache[url] = (inferred, source)

    if inferred and re.match(r"^20\d{2}-\d{2}$", inferred):
        return inferred, source
    return declared_release_date, "manual_fallback"


def is_pdf_url(url: str) -> bool:
    url_l = url.lower()
    return (
        url_l.endswith(".pdf")
        or "arxiv.org/pdf/" in url_l
        or "raw/" in url_l and url_l.endswith(".pdf")
    )


def should_render_webpage_to_pdf(url: str) -> bool:
    return url.lower().startswith(("http://", "https://")) and not is_pdf_url(url)


def slugify_model(name: str) -> str:
    s = name.lower().replace("/", "-")
    s = re.sub(r"[^a-z0-9\-_\.]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def has_pdf_signature(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(5).startswith(b"%PDF-")
    except Exception:
        return False


def extract_text_length_from_pdf(path: Path, max_pages: int = 5) -> int:
    if not path.exists() or PdfReader is None:
        return 0
    try:
        reader = PdfReader(str(path))
        total = 0
        for page in reader.pages[:max_pages]:
            total += len((page.extract_text() or "").strip())
        return total
    except Exception:
        return 0


def looks_like_text_pdf(path: Path, min_chars: int) -> bool:
    return extract_text_length_from_pdf(path) >= min_chars


def download_file(session: requests.Session, url: str, output: Path) -> Tuple[bool, str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        content_type = ""
        with session.get(url, timeout=20, stream=True) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            with output.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        success = output.exists() and output.stat().st_size > 0
        return success, content_type
    except Exception:
        if output.exists():
            output.unlink(missing_ok=True)
        return False, ""


def _expand_common_read_more(page) -> None:
    page.evaluate(
        """
        () => {
            const keys = [
                "read more", "show more", "more", "expand",
                "展开", "更多", "阅读全文", "查看全部"
            ];
            const nodes = document.querySelectorAll("button, a, summary, [role='button']");
            for (const el of nodes) {
                const txt = (el.innerText || el.textContent || "").trim().toLowerCase();
                if (!txt) continue;
                if (keys.some(k => txt.includes(k))) {
                    try { el.click(); } catch (_) {}
                }
            }
        }
        """
    )


def _scroll_until_stable(page, max_rounds: int = 30) -> None:
    stable = 0
    last_height = 0
    for _ in range(max_rounds):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(900)
        height = page.evaluate(
            "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
        )
        if height <= last_height + 8:
            stable += 1
        else:
            stable = 0
        last_height = height
        if stable >= 3:
            break


def _render_text_fallback_pdf(page, url: str, output: Path) -> bool:
    title = (page.title() or url).strip()
    body_text = (page.evaluate("document.body.innerText || ''") or "").strip()
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)
    if len(body_text) < 500:
        return False

    fallback_html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>{html.escape(title)}</title>
        <style>
          body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            margin: 28px;
            color: #111827;
            line-height: 1.55;
          }}
          h1 {{
            margin: 0 0 8px 0;
            font-size: 24px;
          }}
          .meta {{
            color: #4b5563;
            font-size: 12px;
            margin-bottom: 16px;
          }}
          pre {{
            white-space: pre-wrap;
            word-break: break-word;
            margin: 0;
            font-size: 12px;
          }}
        </style>
      </head>
      <body>
        <h1>{html.escape(title)}</h1>
        <div class="meta">Source: {html.escape(url)}</div>
        <pre>{html.escape(body_text)}</pre>
      </body>
    </html>
    """

    page.set_content(fallback_html, wait_until="load")
    page.pdf(
        path=str(output),
        format="A4",
        print_background=True,
        margin={"top": "12mm", "right": "10mm", "bottom": "12mm", "left": "10mm"},
    )
    return has_pdf_signature(output) and looks_like_text_pdf(output, min_chars=800)


def render_webpage_to_pdf(url: str, output: Path) -> bool:
    output.parent.mkdir(parents=True, exist_ok=True)
    if not can_render_webpage_to_pdf():
        return False
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 2200})
            min_chars_for_webpage_pdf = 800
            for attempt in range(2):
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1800 + attempt * 1400)
                _expand_common_read_more(page)
                _scroll_until_stable(page)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(600)
                raw_text_len = len((page.evaluate("document.body.innerText || ''") or "").strip())
                page.emulate_media(media="screen")
                page.pdf(
                    path=str(output),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    margin={"top": "12mm", "right": "10mm", "bottom": "12mm", "left": "10mm"},
                )
                if has_pdf_signature(output) and looks_like_text_pdf(
                    output, min_chars=min_chars_for_webpage_pdf
                ):
                    browser.close()
                    return True
                output.unlink(missing_ok=True)

                # Some blogs hide core content in print CSS. Fall back to text-first export.
                if raw_text_len >= min_chars_for_webpage_pdf and _render_text_fallback_pdf(
                    page, url, output
                ):
                    browser.close()
                    return True
                output.unlink(missing_ok=True)
            browser.close()
        return False
    except Exception:
        if output.exists():
            output.unlink(missing_ok=True)
        return False


def generate_markdown(records: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    lines.append("# LLM 技术报告汇总（2025-01 至 2026-02）")
    lines.append("")
    lines.append("- 目录规则：一级目录为年份，二级目录为公司。")
    lines.append("- 说明：未发布模型标注为“未发布”；已发布但无公开技术报告则保留官方页面链接并将本地位置标注为“仅在线”。")
    lines.append("")
    lines.append("| 发布时间 | 开发机构 | 模型名称 | 核心特性 | 官方链接 | 本地文件位置 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in records:
        lines.append(
            f"| {r['release_date']} | {r['org']} | {r['model']} | {r['core_feature']} | "
            f"{r['official_link']} | {r['local_file_path']} |"
        )
    lines.append("")
    return "\n".join(lines)


def load_models_from_json(models_json_path: Path) -> List[Dict[str, Any]]:
    import json

    raw = json.loads(models_json_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("models_json must be a list")

    required = {"release_date", "org", "org_slug", "model", "core_feature", "official_link"}
    models: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"models_json item #{idx} must be an object")
        missing = required - set(item.keys())
        if missing:
            raise ValueError(f"models_json item #{idx} missing fields: {sorted(missing)}")
        models.append(dict(item))
    return models


def main(
    write_readme: bool = False,
    models: Optional[List[Dict[str, Any]]] = None,
    results_json: Optional[Path] = None,
) -> None:
    session = build_session()
    results: List[Dict[str, str]] = []
    ok, fail, skip = 0, 0, 0

    active_models = models if models is not None else MODELS
    sorted_models = sorted(active_models, key=lambda x: x["release_date"], reverse=True)

    probe_cache: Dict[str, Tuple[bool, str]] = {}
    selected_links: List[str] = []
    selected_reasons: List[str] = []
    for item in sorted_models:
        selected_link, select_reason = choose_best_source_url(session, item, probe_cache)
        if not selected_link:
            selected_link = normalize_url(str(item.get("official_link", "")))
            select_reason = "single_source_fallback"
        selected_links.append(selected_link)
        selected_reasons.append(select_reason)

    normalized_links = [normalize_url(x) for x in selected_links if x]
    link_frequency = Counter(normalized_links)
    release_month_cache: Dict[str, Tuple[Optional[str], str]] = {}

    for idx, item in enumerate(sorted_models, start=1):
        record = dict(item)
        declared_link = normalize_url(str(record["official_link"]))
        link = normalize_url(selected_links[idx - 1])
        source_reason = selected_reasons[idx - 1]
        record["declared_official_link"] = declared_link
        record["source_selection_reason"] = source_reason
        if link != declared_link:
            print(f"  URL优选: {declared_link} -> {link} ({source_reason})", flush=True)
        record["official_link"] = link
        declared_release_date = str(record["release_date"])
        release_date, release_source = resolve_release_month(
            session=session,
            declared_release_date=declared_release_date,
            url=link,
            link_frequency=link_frequency,
            cache=release_month_cache,
        )
        if release_date != declared_release_date:
            print(
                f"  时间前缀校正: {declared_release_date} -> {release_date} ({release_source})",
                flush=True,
            )
        record["release_date"] = release_date
        year = release_date.split("-")[0]
        print(f"[{idx}/{len(sorted_models)}] {record['model']} -> {year}/{record['org_slug']}", flush=True)

        if record["model"].lower() == "grok 4.5":
            record["official_link"] = "未发布"
            record["local_file_path"] = "未发布"
            skip += 1
            results.append(record)
            continue

        filename = f"{release_date}_{slugify_model(record['model'])}.pdf"
        output = ROOT / year / record["org_slug"] / filename

        if is_pdf_url(link):
            success, content_type = download_file(session, link, output)
            if success:
                is_pdf = has_pdf_signature(output)
                is_original_pdf = is_pdf and (
                    "pdf" in content_type.lower()
                    or link.lower().endswith(".pdf")
                    or "arxiv.org/pdf/" in link.lower()
                )
                text_len = extract_text_length_from_pdf(output)
                if not is_original_pdf:
                    output.unlink(missing_ok=True)
                    record["local_file_path"] = "下载失败"
                    fail += 1
                    print(f"  下载失败: 非原始 PDF 响应 ({content_type})", flush=True)
                else:
                    record["local_file_path"] = str(output.relative_to(ROOT))
                    ok += 1
                    print(
                        f"  下载成功: {record['local_file_path']} | 原始PDF=是 | 可提取文本={text_len}",
                        flush=True,
                    )
            else:
                record["local_file_path"] = "下载失败"
                fail += 1
                print(f"  下载失败: {link}", flush=True)
        elif should_render_webpage_to_pdf(link):
            success = render_webpage_to_pdf(link, output)
            if success:
                record["local_file_path"] = str(output.relative_to(ROOT))
                ok += 1
                print(f"  网页转 PDF 成功: {record['local_file_path']}", flush=True)
            else:
                record["local_file_path"] = "下载失败"
                fail += 1
                print(f"  网页转 PDF 失败: {link}", flush=True)
        else:
            record["local_file_path"] = "仅在线"
            skip += 1
            print("  跳过下载: 非 HTTP(s) 资源", flush=True)

        results.append(record)

    if results_json:
        results_json.parent.mkdir(parents=True, exist_ok=True)
        results_json.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Results JSON: {results_json}")

    if write_readme:
        readme = ROOT / "README.md"
        readme.write_text(generate_markdown(results), encoding="utf-8")
        print(f"README: {readme}")
    else:
        print("README: skipped (preserving existing curated README.md)")

    print("=== 下载完成 ===")
    print(f"成功: {ok}")
    print(f"失败: {fail}")
    print(f"跳过(仅在线/未发布): {skip}")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download model papers and optionally regenerate README")
    parser.add_argument(
        "--write-readme",
        action="store_true",
        help="Regenerate README.md from raw records (disabled by default)",
    )
    parser.add_argument(
        "--models-json",
        type=Path,
        help="Optional JSON list regenerated by crawler to override in-file MODELS snapshot",
    )
    parser.add_argument(
        "--results-json",
        type=Path,
        default=ROOT / "scripts" / "latest_download_results.json",
        help="Path to write structured download results for downstream README update",
    )
    args = parser.parse_args()
    runtime_models = None
    if args.models_json:
        runtime_models = load_models_from_json(args.models_json)
    main(write_readme=args.write_readme, models=runtime_models, results_json=args.results_json)
