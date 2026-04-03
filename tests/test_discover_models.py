import unittest
import re
import base64
from pathlib import Path

from tests.runtime_imports import discover_models


LONGCAT_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2603.27538v1</id>
    <published>2026-03-29T12:00:00Z</published>
    <title>LongCat-Next Technical Report</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2603.21065v1</id>
    <published>2026-03-22T12:00:00Z</published>
    <title>LongCat-Flash-Prover Technical Report</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2601.16725v1</id>
    <published>2026-01-28T12:00:00Z</published>
    <title>LongCat-Flash-Thinking-2601 Technical Report</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2512.07584v1</id>
    <published>2025-12-08T12:00:00Z</published>
    <title>LongCat-Image Technical Report</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2510.22200v1</id>
    <published>2025-10-25T12:00:00Z</published>
    <title>LongCat-Video Technical Report</title>
  </entry>
</feed>
"""

MINIMAX_NEWS_HTML = """
<html>
  <body>
    <article>
      <a href="/news/minimax-m27">Introducing MiniMax M2.7</a>
      <time datetime="2026-03-20">March 20, 2026</time>
    </article>
  </body>
</html>
"""

MINIMAX_IR_HTML = """
<html>
  <body>
    <a href="/news/minimax-m27-en">MiniMax M2.7: Early Echoes of Self-Evolution</a>
  </body>
</html>
"""

MINIMAX_ARTICLE_HTML = """
<html>
  <head>
    <meta property="og:title" content="MiniMax M2.7: Early Echoes of Self-Evolution" />
  </head>
  <body>
    {"datePublished":"2026-03-20T12:00:00.000Z"}
  </body>
</html>
"""

GOOGLE_MODELS_HTML = """
<html>
  <body>
    <a href="https://storage.googleapis.com/deepmind-media/Model-Cards/Gemma-4-Model-Card.pdf">Gemma 4 Model Card</a>
    <a href="https://storage.googleapis.com/deepmind-media/Model-Cards/MedGemma-1-5-Model-Card.pdf">MedGemma 1.5 Model Card</a>
    <a href="https://storage.googleapis.com/deepmind-media/Model-Cards/ShieldGemma-2-Model-Card.pdf">ShieldGemma 2 Model Card</a>
    <table>
      <tr>
        <th scope="row">Gemini 3.1 Pro</th>
        <td>Updated 19 February 2026</td>
        <td class="table--right"><a aria-label="Gemini 3.1 Pro model card" href=/models/model-cards/gemini-3-1-pro/>View model card</a></td>
      </tr>
      <tr>
        <th scope="row">Gemini 3.1 Flash Live</th>
        <td>Updated 3 March 2026</td>
        <td class="table--right"><a aria-label="Gemini 3.1 Flash Live model card" href=/models/model-cards/gemini-3-1-flash-live/>View model card</a></td>
      </tr>
      <tr>
        <th scope="row">Imagen 4</th>
        <td>Updated 20 February 2026</td>
        <td class="table--right"><a aria-label="Imagen 4 model card" href=/models/model-cards/imagen-4/>View model card</a></td>
      </tr>
    </table>
  </body>
</html>
"""

GOOGLE_GEMMA_DOCS_HTML = """
<html>
  <body>
    <a href="/gemma/docs/core/model_card_4">Gemma 4 model card</a>
  </body>
</html>
"""

GOOGLE_GEMMA_MODEL_CARD_4 = """
<html>
  <head><title>Gemma 4 model card | Google AI for Developers</title></head>
  <body><p>Last updated 2026-04-02 UTC.</p></body>
</html>
"""

GOOGLE_GEMINI31_PRO_PAGE = """
<html>
  <head><title>Gemini 3.1 Pro - Model Card — Google DeepMind</title></head>
  <body>
    <span>Updated 19 February 2026</span>
    <a href=https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Pro-Model-Card.pdf target=_blank>View PDF version</a>
  </body>
</html>
"""

GOOGLE_GEMINI31_FLASH_LIVE_PAGE = """
<html>
  <head><title>Gemini 3.1 Flash Live - Model Card — Google DeepMind</title></head>
  <body>
    <span>Updated 3 March 2026</span>
    <a href=https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Live-Model-Card.pdf target=_blank>View PDF version</a>
  </body>
</html>
"""

OPENAI_HOME_HTML = """
<html>
  <body>
    <article>
      <a href="/gpt-5-4-thinking">GPT-5.4 Thinking</a>
      <time datetime="2026-03-12">March 12, 2026</time>
    </article>
  </body>
</html>
"""

OPENAI_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://localhost:4321/gpt-5-4-thinking/</loc></url>
  <url><loc>http://localhost:4321/gpt-5-3-instant/</loc></url>
  <url><loc>http://localhost:4321/gpt-5-sensitive-conversations/</loc></url>
  <url><loc>http://localhost:4321/o3/</loc></url>
</urlset>
"""

OPENAI_GPT54_PAGE = """
<html>
  <head><title>GPT-5.4 Thinking System Card - OpenAI Deployment Safety Hub</title></head>
  <body>
    <div>March 12, 2026</div>
    <a href="/gpt-5-4-thinking/gpt-5-4-thinking.pdf">System card PDF</a>
  </body>
</html>
"""

OPENAI_GPT53_PAGE = """
<html>
  <head><title>GPT-5.3 Instant System Card - OpenAI Deployment Safety Hub</title></head>
  <body>
    <div>March 2, 2026</div>
    <a href=/gpt-5-3-instant/gpt-5-3-instant.pdf>System card PDF</a>
  </body>
</html>
"""

OPENAI_SENSITIVE_CONVERSATIONS_PAGE = """
<html>
  <head><title>Addendum to GPT-5 System Card: Sensitive Conversations - OpenAI Deployment Safety Hub</title></head>
  <body>
    <div>October 27, 2025</div>
    <a href="/gpt-5-sensitive-conversations/addendum-to-gpt-5-system-card-sensitive-conversations.pdf">Download addendum</a>
  </body>
</html>
"""

OPENAI_O3_PAGE = """
<html>
  <head><title>OpenAI o3 and o4-mini System Card - OpenAI Deployment Safety Hub</title></head>
  <body>
    <div>April 16, 2025</div>
    <a href="https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf">View PDF version</a>
  </body>
</html>
"""

ANTHROPIC_NEWS_HTML = """
<html>
  <body>
    <article>
      <a href="/news/claude-haiku-4-5">Claude Haiku 4.5</a>
      <time datetime="2026-03-07">March 7, 2026</time>
    </article>
  </body>
</html>
"""

ANTHROPIC_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.anthropic.com/news/claude-opus-4-6</loc>
    <lastmod>2026-02-05T18:13:29.000Z</lastmod>
  </url>
  <url>
    <loc>https://www.anthropic.com/news/claude-sonnet-4-6</loc>
    <lastmod>2026-03-11T17:28:36.000Z</lastmod>
  </url>
  <url>
    <loc>https://www.anthropic.com/news/claude-haiku-4-5</loc>
    <lastmod>2025-11-20T16:25:50.000Z</lastmod>
  </url>
</urlset>
"""

ANTHROPIC_HAIKU_PAGE = """
<html>
  <head><title>Claude Haiku 4.5 | Anthropic</title></head>
  <body>
    <a href="https://www-cdn.anthropic.com/system-cards/claude-haiku-4-5-system-card.pdf">Download system card</a>
  </body>
</html>
"""

ANTHROPIC_OPUS46_PAGE = """
<html>
  <head><title>Claude Opus 4.6 | Anthropic</title></head>
  <body>
    <div class="body-3 agate">Feb 5, 2026</div>
    <a href="https://www-cdn.anthropic.com/system-cards/claude-opus-4-6-system-card.pdf">Download system card</a>
  </body>
</html>
"""

ANTHROPIC_SONNET46_PAGE = """
<html>
  <head><title>Claude Sonnet 4.6 | Anthropic</title></head>
  <body>
    <div class="body-3 agate">Mar 11, 2026</div>
    <a href="https://www-cdn.anthropic.com/system-cards/claude-sonnet-4-6-system-card.pdf">Download system card</a>
  </body>
</html>
"""

XAI_DATA_HTML = """
<html>
  <body>
    <a href="https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf">Grok 4.1 model card</a>
  </body>
</html>
"""

XAI_RELEASE_NOTES_HTML = """
<html>
  <body>
    <h1><a>November 2025</a></h1>
    <div class="date-badge">Nov 19</div>
    <h3><a>Grok 4.1 Fast is available in Enterprise API</a></h3>
    <p>You can now use Grok 4.1 Fast in the <a href="https://x.ai/api">xAI Enterprise API</a>. For more details, check out <a href="https://x.ai/news/grok-4-1-fast">our blogpost</a>.</p>
    <h1><a>July 2025</a></h1>
    <div class="date-badge">Jul 9</div>
    <h3><a>Grok 4 is released</a></h3>
    <p>You can now use Grok 4 via our API or on <a href="https://grok.com">https://grok.com</a>.</p>
  </body>
</html>
"""

META_BLOG_HTML = """
<html>
  <body>
    <article>
    <a href="/blog/llama-4-multimodal-intelligence/">Llama 4 multimodal intelligence</a>
      <time datetime="2025-04-05">April 5, 2025</time>
    </article>
  </body>
</html>
"""

META_LLAMAS_PAGE = """
<html>
  <head><title>Llama 4 Scout/Maverick | Meta</title></head>
  <body>
    <span>April 5, 2025</span>
    <p>Introducing Llama 4 Scout and Maverick.</p>
  </body>
</html>
"""

INCLUSION_REPO_HTML = """
<html>
  <head><title>Ling-V2.5</title></head>
  <body>
    <article>
      <h1>Ling-V2.5</h1>
      <p>Released on 2026-02-18.</p>
    </article>
  </body>
</html>
"""

DEEPSEEK_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2512.02556v1</id>
    <published>2025-12-04T12:00:00Z</published>
    <title>DeepSeek V3.2 Technical Report</title>
  </entry>
</feed>
"""

MOONSHOT_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2602.11912v1</id>
    <published>2026-02-19T12:00:00Z</published>
    <title>Kimi K2.5 Technical Report</title>
  </entry>
</feed>
"""

STEPFUN_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2602.10604v1</id>
    <published>2026-02-15T12:00:00Z</published>
    <title>Step-3.5-Flash Technical Report</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2512.20491v1</id>
    <published>2025-12-24T12:00:00Z</published>
    <title>Step-DeepResearch Technical Report</title>
  </entry>
</feed>
"""

TENCENT_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2505.15431v1</id>
    <published>2025-05-22T12:00:00Z</published>
    <title>Yuanbao (Hunyuan-TurboS) Technical Report</title>
  </entry>
</feed>
"""

BAICHUAN_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2602.06570v1</id>
    <published>2026-02-10T12:00:00Z</published>
    <title>Baichuan-M3 Technical Report</title>
  </entry>
</feed>
"""

QUARK_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2508.11894v1</id>
    <published>2025-08-18T12:00:00Z</published>
    <title>QuarkMed Technical Report</title>
  </entry>
</feed>
"""

BYTEDANCE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2602.12705v1</id>
    <published>2026-02-20T12:00:00Z</published>
    <title>MedXIAOHE Technical Report</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2505.07062v1</id>
    <published>2025-05-09T12:00:00Z</published>
    <title>Seed1.5-VL Technical Report</title>
  </entry>
</feed>
"""

BAIDU_PUBLICATION_HTML = """
<html>
  <body>
    <article>
      <a href="https://yiyan.baidu.com/blog/publication/ERNIE_Technical_Report.pdf">ERNIE 4.5 Technical Report</a>
      <time datetime="2025-06-30">June 30, 2025</time>
    </article>
  </body>
</html>
"""

ZHIPU_MODELS_JSON = [
    {
        "id": "zai-org/GLM-5V-Turbo",
        "createdAt": "2026-04-02T03:00:00.000Z",
        "cardData": {"license": "other"},
    },
    {
        "id": "zai-org/GLM-4.7",
        "createdAt": "2026-03-18T03:00:00.000Z",
        "cardData": {"license": "other"},
    },
    {
        "id": "zai-org/GLM-4.7-Flash",
        "createdAt": "2026-03-21T03:00:00.000Z",
        "cardData": {"license": "other"},
    },
]

ZHIPU_DOCS_ROOT_HTML = """
<html>
  <body>
    <a href="/guides/vlm/glm-5v-turbo">GLM-5V-Turbo</a>
    <a href="/guides/llm/glm-4.7">GLM-4.7</a>
  </body>
</html>
"""

BIGMODEL_DOCS_ROOT_HTML = """
<html>
  <body>
    <a href="/cn/guide/models/free/glm-4.7-flash">GLM-4.7-Flash</a>
  </body>
</html>
"""

ZHIPU_DOC_GLM_5V_TURBO = """
<html>
  <head><title>GLM-5V-Turbo - Overview - Z.AI DEVELOPER DOC</title></head>
  <body>Last updated 2026-04-02 UTC.</body>
</html>
"""

ZHIPU_DOC_GLM_47 = """
<html>
  <head><title>GLM-4.7 - Overview - Z.AI DEVELOPER DOC</title></head>
  <body>Last updated 2026-03-18 UTC.</body>
</html>
"""

ZHIPU_DOC_GLM_47_FLASH = """
<html>
  <head><title>GLM-4.7-Flash - Overview - BigModel Docs</title></head>
  <body>Last updated 2026-03-21 UTC.</body>
</html>
"""

QWEN_REPOS_JSON = [
    {
        "name": "Qwen3",
        "html_url": "https://github.com/QwenLM/Qwen3",
        "created_at": "2025-05-01T00:00:00Z",
    },
    {
        "name": "Qwen3-Coder",
        "html_url": "https://github.com/QwenLM/Qwen3-Coder",
        "created_at": "2026-03-28T00:00:00Z",
    },
]

QWEN_PAGE_CONFIG_LATEST = [
    {
        "date": "2025-09-24T04:00:00.000Z",
        "title": "Qwen3-Max: Just Scale it",
        "tokenLinks": "https://docs.qwenlm.ai/research/latest-advancements/qwen3-max/index.json",
        "tags": ["Release"],
    },
    {
        "date": "2025-09-10T20:00:00.000Z",
        "title": "Qwen3-Next: Towards Ultimate Training & Inference Efficiency",
        "tokenLinks": "https://docs.qwenlm.ai/research/latest-advancements/qwen3-next/index.json",
        "tags": ["Open-Source"],
    },
    {
        "date": "2025-07-22T13:00:00.000Z",
        "title": "Qwen3-Coder: Agentic Coding in the World",
        "tokenLinks": "https://docs.qwenlm.ai/research/latest-advancements/qwen3-coder/index.json",
        "tags": ["Research"],
    },
    {
        "date": "2025-04-28T20:00:00.000Z",
        "title": "Qwen3: Think Deeper, Act Faster",
        "tokenLinks": "https://docs.qwenlm.ai/research/latest-advancements/qwen3/index.json",
        "tags": ["Open-Source"],
    },
]

QWEN_PAGE_CONFIG_RESEARCH = [
    {
        "date": "2025-09-21T21:00:00.000Z",
        "title": "Qwen3-Omni: Natively Omni-Modal Foundation Models!",
        "tokenLinks": "https://docs.qwenlm.ai/home/latest-research/qwen3-omni/index.json",
        "tags": ["Release"],
    },
    {
        "date": "2025-08-04T14:08:30.000Z",
        "title": "Qwen-Image: Crafting with Native Text Rendering",
        "tokenLinks": "https://docs.qwenlm.ai/research/latest-advancements/qwen-image/index.json",
        "tags": ["Research"],
    },
    {
        "date": "2025-03-26T16:00:45.000Z",
        "title": "Qwen2.5 Omni: See, Hear, Talk, Write, Do It All!",
        "tokenLinks": "https://docs.qwenlm.ai/research/qwen2.5-omni/index.json",
        "tags": ["Research"],
    },
]

QWEN3_TOKEN_LINKS = [
    {"type": "hugoButton", "label": "PAPER", "href": "https://arxiv.org/pdf/2505.09388"},
    {"type": "hugoButton", "label": "GITHUB", "href": "https://github.com/QwenLM/Qwen3"},
]

QWEN3_CODER_TOKEN_LINKS = [
    {"type": "hugoButton", "label": "GITHUB", "href": "https://github.com/QwenLM/Qwen3-Coder"},
    {
        "type": "paragraph",
        "text": "Today, we're announcing Qwen3-Coder, our most agentic code model to date.",
    },
    {"type": "heading", "text": "Qwen3-Coder"},
]

QWEN3_NEXT_TOKEN_LINKS = [
    {
        "type": "hugoButton",
        "label": "Hugging Face",
        "href": "https://huggingface.co/collections/Qwen/qwen3-next-68c25fd6838e585db8eeea9d",
    },
    {
        "type": "paragraph",
        "text": "Qwen3-Next is an open-weight release focused on training and inference efficiency.",
    },
    {"type": "heading", "text": "Qwen3-Next"},
]

QWEN3_MAX_TOKEN_LINKS = [
    {
        "type": "hugoButton",
        "label": "API",
        "href": "https://www.alibabacloud.com/help/en/model-studio/models#c2d5833ae4jmo",
    },
    {
        "type": "paragraph",
        "text": "Qwen3-Max is the flagship proprietary model in the Qwen3 family.",
    },
    {"type": "heading", "text": "Qwen3-Max"},
]

QWEN3_OMNI_TOKEN_LINKS = [
    {"type": "hugoButton", "label": "PAPER", "href": "https://github.com/QwenLM/Qwen3-Omni/tree/main/assets/Qwen3_Omni.pdf"},
    {"type": "hugoButton", "label": "GITHUB", "href": "https://github.com/QwenLM/Qwen3-Omni"},
]

QWEN_IMAGE_TOKEN_LINKS = [
    {"type": "hugoButton", "label": "PAPER", "href": "https://arxiv.org/pdf/2508.02324"},
]

QWEN25_OMNI_TOKEN_LINKS = [
    {"type": "hugoButton", "label": "PAPER", "href": "https://arxiv.org/pdf/2503.20215"},
]

QWEN3_README = """# Qwen3

[Paper](https://arxiv.org/abs/2505.09388)
[Blog](https://qwenlm.github.io/blog/qwen3/)
"""

QWEN3_CODER_README = """Qwen3-Coder:

[Blog](https://qwenlm.github.io/blog/qwen3-coder/)
"""

QWEN3_BLOG_HTML = """
<html><head><title>Qwen3</title></head><body><time datetime="2025-05-01">May 1, 2025</time></body></html>
"""

QWEN3_CODER_BLOG_HTML = """
<html><head><title>Qwen3-Coder-Next</title></head><body><time datetime="2026-03-28">March 28, 2026</time></body></html>
"""


class StaticFetcher:
    def __init__(self) -> None:
        self.text_map = {
            discover_models.LONGCAT_ARXIV_FEED_URL: LONGCAT_FEED,
            discover_models.MINIMAX_NEWS_URL: MINIMAX_NEWS_HTML,
            discover_models.MINIMAX_IR_URL: MINIMAX_IR_HTML,
            "https://www.minimax.io/news/minimax-m27-en": MINIMAX_ARTICLE_HTML,
            "https://deploymentsafety.openai.com/": OPENAI_HOME_HTML,
            "https://deploymentsafety.openai.com/sitemap.xml": OPENAI_SITEMAP_XML,
            "https://deploymentsafety.openai.com/gpt-5-4-thinking": OPENAI_GPT54_PAGE,
            "https://deploymentsafety.openai.com/gpt-5-3-instant": OPENAI_GPT53_PAGE,
            "https://deploymentsafety.openai.com/gpt-5-sensitive-conversations": OPENAI_SENSITIVE_CONVERSATIONS_PAGE,
            "https://deploymentsafety.openai.com/o3": OPENAI_O3_PAGE,
            "https://www.anthropic.com/news": ANTHROPIC_NEWS_HTML,
            "https://www.anthropic.com/sitemap.xml": ANTHROPIC_SITEMAP_XML,
            "https://www.anthropic.com/news/claude-haiku-4-5": ANTHROPIC_HAIKU_PAGE,
            "https://www.anthropic.com/news/claude-opus-4-6": ANTHROPIC_OPUS46_PAGE,
            "https://www.anthropic.com/news/claude-sonnet-4-6": ANTHROPIC_SONNET46_PAGE,
            "https://data.x.ai/": XAI_DATA_HTML,
            "https://docs.x.ai/docs/release-notes": XAI_RELEASE_NOTES_HTML,
            "https://ai.meta.com/blog/": META_BLOG_HTML,
            "https://ai.meta.com/blog/llama-4-multimodal-intelligence/": META_LLAMAS_PAGE,
            "https://yiyan.baidu.com/blog/publication": BAIDU_PUBLICATION_HTML,
            "https://github.com/inclusionAI/Ling-V2.5": INCLUSION_REPO_HTML,
            discover_models.GOOGLE_MODEL_CARDS_URL: GOOGLE_MODELS_HTML,
            discover_models.GOOGLE_GEMMA_URL: GOOGLE_MODELS_HTML,
            discover_models.GOOGLE_GEMMA_DOCS_URL: GOOGLE_GEMMA_DOCS_HTML,
            "https://ai.google.dev/gemma/docs/core/model_card_4": GOOGLE_GEMMA_MODEL_CARD_4,
            "https://deepmind.google/models/model-cards/gemini-3-1-pro/": GOOGLE_GEMINI31_PRO_PAGE,
            "https://deepmind.google/models/model-cards/gemini-3-1-flash-live/": GOOGLE_GEMINI31_FLASH_LIVE_PAGE,
            "https://github.com/QwenLM/Qwen3": "<html>Qwen3_Technical_Report.pdf</html>",
            "https://github.com/QwenLM/Qwen3-Coder": "<html>qwen3_coder_next_tech_report.pdf</html>",
            "https://qwenlm.github.io/blog/qwen3/": QWEN3_BLOG_HTML,
            "https://qwenlm.github.io/blog/qwen3-coder/": QWEN3_CODER_BLOG_HTML,
            discover_models.ZHIPU_DOCS_ROOT_URL: ZHIPU_DOCS_ROOT_HTML,
            discover_models.BIGMODEL_DOCS_ROOT_URL: BIGMODEL_DOCS_ROOT_HTML,
            "https://docs.z.ai/guides/vlm/glm-5v-turbo": ZHIPU_DOC_GLM_5V_TURBO,
            "https://docs.z.ai/guides/llm/glm-4.7": ZHIPU_DOC_GLM_47,
            "https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash": ZHIPU_DOC_GLM_47_FLASH,
            discover_models.build_arxiv_query_url('ti:"DeepSeek"'): DEEPSEEK_FEED,
            discover_models.build_arxiv_query_url('ti:"Kimi K2"'): MOONSHOT_FEED,
            discover_models.build_arxiv_query_url('ti:"Step-3.5-Flash" OR ti:"Step-DeepResearch"'): STEPFUN_FEED,
            discover_models.build_arxiv_query_url('ti:"Yuanbao" OR ti:"Hunyuan-TurboS"'): TENCENT_FEED,
            discover_models.build_arxiv_query_url('ti:"Baichuan-M"'): BAICHUAN_FEED,
            discover_models.build_arxiv_query_url('ti:"QuarkMed"'): QUARK_FEED,
            discover_models.build_arxiv_query_url('ti:"MedXIAOHE" OR ti:"Seed1.5-VL" OR ti:"Seed 2.0"'): BYTEDANCE_FEED,
        }
        self.json_map = {
            discover_models.build_qwen_page_config_url("research.latest-advancements-list"): QWEN_PAGE_CONFIG_LATEST,
            discover_models.build_qwen_page_config_url("home.latest-research-list"): QWEN_PAGE_CONFIG_LATEST,
            discover_models.build_qwen_page_config_url("research.research-list"): QWEN_PAGE_CONFIG_RESEARCH,
            discover_models.build_qwen_page_config_url("news.news-list"): QWEN_PAGE_CONFIG_RESEARCH,
            "https://docs.qwenlm.ai/research/latest-advancements/qwen3/index.json": QWEN3_TOKEN_LINKS,
            "https://docs.qwenlm.ai/research/latest-advancements/qwen3-coder/index.json": QWEN3_CODER_TOKEN_LINKS,
            "https://docs.qwenlm.ai/research/latest-advancements/qwen3-next/index.json": QWEN3_NEXT_TOKEN_LINKS,
            "https://docs.qwenlm.ai/research/latest-advancements/qwen3-max/index.json": QWEN3_MAX_TOKEN_LINKS,
            "https://docs.qwenlm.ai/home/latest-research/qwen3-omni/index.json": QWEN3_OMNI_TOKEN_LINKS,
            "https://docs.qwenlm.ai/research/latest-advancements/qwen-image/index.json": QWEN_IMAGE_TOKEN_LINKS,
            "https://docs.qwenlm.ai/research/qwen2.5-omni/index.json": QWEN25_OMNI_TOKEN_LINKS,
            discover_models.ZHIPU_HF_MODELS_URL: ZHIPU_MODELS_JSON,
            discover_models.QWEN_GITHUB_REPOS_URL: QWEN_REPOS_JSON,
            "https://api.github.com/repos/QwenLM/Qwen3/contents": [
                {
                    "name": "Qwen3_Technical_Report.pdf",
                    "download_url": "https://raw.githubusercontent.com/QwenLM/Qwen3/main/Qwen3_Technical_Report.pdf",
                }
            ],
            "https://api.github.com/repos/QwenLM/Qwen3/readme": {
                "content": base64.b64encode(QWEN3_README.encode("utf-8")).decode("ascii")
            },
            "https://api.github.com/repos/QwenLM/Qwen3-Coder/contents": [
                {
                    "name": "qwen3_coder_next_tech_report.pdf",
                    "download_url": "https://raw.githubusercontent.com/QwenLM/Qwen3-Coder/main/qwen3_coder_next_tech_report.pdf",
                }
            ],
            "https://api.github.com/repos/QwenLM/Qwen3-Coder/readme": {
                "content": base64.b64encode(QWEN3_CODER_README.encode("utf-8")).decode("ascii")
            },
        }

    def get_text(self, url: str) -> str:
        return self.text_map[url]

    def get_json(self, url: str):
        return self.json_map[url]


class DiscoverModelsTests(unittest.TestCase):
    def test_vendor_registry_covers_current_repo_manufacturers(self) -> None:
        text = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        organizations = set()
        for line in text.splitlines():
            if not line.startswith("| ") or line.startswith("| Release Date") or line.startswith("| ---"):
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 6 and re.match(r"^20\d{2}-\d{2}$", parts[0]):
                organizations.add(parts[1])

        expected_slugs = {
            "Alibaba": "alibaba_qwen",
            "Anthropic": "anthropic",
            "Baichuan Intelligence": "baichuan",
            "Baidu": "baidu",
            "ByteDance": "bytedance",
            "DeepSeek": "deepseek",
            "Google": "google",
            "InclusionAI (Ant Group)": "inclusionai",
            "Meituan": "meituan",
            "Meta": "meta",
            "MiniMax": "minimax",
            "Moonshot AI": "moonshot",
            "OpenAI": "openai",
            "Quark (Alibaba)": "quark",
            "StepFun": "stepfun",
            "Tencent": "tencent",
            "Zhipu AI": "zhipu",
            "xAI": "xai",
        }

        self.assertEqual(organizations, set(expected_slugs))
        registered = set(discover_models.VENDOR_REGISTRY)
        self.assertTrue(set(expected_slugs.values()).issubset(registered))

    def test_vendor_registry_contains_source_metadata_for_major_manufacturers(self) -> None:
        for slug in [
            "openai",
            "anthropic",
            "google",
            "xai",
            "meta",
            "alibaba_qwen",
            "quark",
            "deepseek",
            "moonshot",
            "stepfun",
            "tencent",
            "baidu",
            "bytedance",
            "baichuan",
            "inclusionai",
            "meituan",
            "minimax",
            "zhipu",
            "mistral",
            "cohere",
            "ai21",
            "amazon",
            "ibm",
            "01ai",
            "naver",
            "huawei",
            "sensetime",
        ]:
            vendor = discover_models.VENDOR_REGISTRY[slug]
            self.assertTrue(vendor["display_name"])
            self.assertTrue(vendor["sources"])

    def test_discover_all_models_finds_required_latest_releases(self) -> None:
        records = discover_models.discover_all_models(
            until="2026-04-03",
            fetcher=StaticFetcher(),
            discovered_at="2026-04-03T10:00:00Z",
        )

        by_model = {record["model"]: record for record in records}
        for model_name in [
            "LongCat-Flash-Prover",
            "LongCat-Next",
            "LongCat-Flash-Thinking-2601",
            "LongCat-Image",
            "LongCat-Video",
            "GLM-5V-Turbo",
            "GLM-4.7",
            "GLM-4.7-Flash",
            "MiniMax M2.7",
            "Gemma 4",
            "MedGemma 1.5",
            "Gemini 3.1 Pro",
            "GPT-5.3 Instant",
        ]:
            self.assertIn(model_name, by_model)
            self.assertEqual(by_model[model_name]["release_classification"], "model_release")

    def test_discovery_keeps_excluded_records_with_machine_readable_reason(self) -> None:
        records = discover_models.discover_all_models(
            until="2026-04-03",
            fetcher=StaticFetcher(),
            discovered_at="2026-04-03T10:00:00Z",
        )
        shield = next(record for record in records if record["model"] == "ShieldGemma 2")
        self.assertEqual(shield["release_classification"], "exclude_tool_model")
        self.assertTrue(shield["classification_reason"])

    def test_discovered_records_include_alias_and_evidence_fields(self) -> None:
        records = discover_models.discover_all_models(
            until="2026-04-03",
            fetcher=StaticFetcher(),
            discovered_at="2026-04-03T10:00:00Z",
        )
        record = next(r for r in records if r["model"] == "GLM-5V-Turbo")
        self.assertEqual(record["canonical_model_id"], "zhipu/glm-5v-turbo")
        self.assertIn("GLM 5V Flash", record["aliases"])
        self.assertTrue(record["evidence_urls"])
        self.assertEqual(record["discovered_at"], "2026-04-03T10:00:00Z")

    def test_discover_all_models_includes_qwen_official_api_releases(self) -> None:
        records = discover_models.discover_all_models(
            until="2026-04-03",
            fetcher=StaticFetcher(),
            discovered_at="2026-04-03T10:00:00Z",
        )
        by_model = {record["model"]: record for record in records}
        self.assertIn("Qwen3", by_model)
        self.assertIn("Qwen3-Coder", by_model)
        self.assertIn("Qwen3-Next", by_model)
        self.assertIn("Qwen3-Max", by_model)
        self.assertEqual(by_model["Qwen3"]["release_classification"], "model_release")
        self.assertEqual(by_model["Qwen3-Coder"]["release_classification"], "model_release")
        self.assertEqual(by_model["Qwen3-Next"]["release_classification"], "model_release")
        self.assertEqual(by_model["Qwen3-Max"]["release_classification"], "model_release")
        self.assertEqual(by_model["Qwen3"]["release_date"], "2025-04")
        self.assertEqual(by_model["Qwen3-Coder"]["release_date"], "2025-07")
        self.assertEqual(by_model["Qwen3-Next"]["release_date"], "2025-09")
        self.assertEqual(by_model["Qwen3-Max"]["release_date"], "2025-09")
        self.assertIn(
            "qwen3_coder_next_tech_report.pdf",
            " ".join(by_model["Qwen3-Coder"]["candidate_links"]),
        )

    def test_guess_qwen_repo_pdf_links_supports_html_fallback(self) -> None:
        guessed = discover_models.guess_qwen_repo_pdf_links(
            "Qwen3-Coder",
            '<html>qwen3_coder_next_tech_report.pdf</html>',
        )
        self.assertEqual(
            guessed,
            ["https://raw.githubusercontent.com/QwenLM/Qwen3-Coder/main/qwen3_coder_next_tech_report.pdf"],
        )

    def test_discover_all_models_does_not_invent_qwen36_without_official_source(self) -> None:
        records = discover_models.discover_all_models(
            until="2026-04-03",
            fetcher=StaticFetcher(),
            discovered_at="2026-04-03T10:00:00Z",
        )
        models = {record["model"] for record in records}
        self.assertNotIn("Qwen3.6", models)
        self.assertNotIn("Qwen 3.6", models)
        self.assertNotIn("Qwen3.6-Plus", models)

    def test_discover_anthropic_uses_sitemap_when_news_index_unavailable(self) -> None:
        fetcher = StaticFetcher()
        fetcher.text_map["https://www.anthropic.com/news"] = ""
        records = discover_models.discover_anthropic(
            fetcher,
            "2026-04-03T10:00:00Z",
            discover_models.load_alias_config(),
        )
        by_model = {record["model"]: record for record in records}
        self.assertEqual(by_model["Claude Opus 4.6"]["release_date"], "2026-02")
        self.assertEqual(by_model["Claude Sonnet 4.6"]["release_date"], "2026-03")
        self.assertEqual(by_model["Claude Haiku 4.5"]["release_date"], "2025-11")
        self.assertTrue(by_model["Claude Opus 4.6"]["official_link"].endswith(".pdf"))

    def test_discover_openai_uses_sitemap_top_level_model_routes(self) -> None:
        records = discover_models.discover_openai(
            StaticFetcher(),
            "2026-04-03T10:00:00Z",
            discover_models.load_alias_config(),
        )
        by_model = {record["model"]: record for record in records}
        self.assertEqual(by_model["GPT-5.4 Thinking"]["release_date"], "2026-03")
        self.assertEqual(by_model["GPT-5.3 Instant"]["release_date"], "2026-03")
        self.assertEqual(by_model["o3 / o4-mini"]["release_date"], "2025-04")
        self.assertTrue(by_model["GPT-5.4 Thinking"]["official_link"].endswith("gpt-5-4-thinking.pdf"))
        self.assertTrue(by_model["GPT-5.3 Instant"]["official_link"].endswith("gpt-5-3-instant.pdf"))
        self.assertTrue(by_model["o3 / o4-mini"]["official_link"].endswith("o3-and-o4-mini-system-card.pdf"))
        self.assertIn(
            "https://openai.com/index/introducing-o3-and-o4-mini/",
            by_model["o3 / o4-mini"]["evidence_urls"],
        )
        self.assertLessEqual(len(by_model["o3 / o4-mini"]["candidate_links"]), 3)
        self.assertNotIn("GPT-5 Sensitive Conversations", by_model)

    def test_discover_google_reads_gemini_rows_from_model_card_catalog(self) -> None:
        records = discover_models.discover_google(
            StaticFetcher(),
            "2026-04-03T10:00:00Z",
            discover_models.load_alias_config(),
        )
        by_model = {record["model"]: record for record in records}
        self.assertEqual(by_model["Gemini 3.1 Pro"]["release_date"], "2026-02")
        self.assertEqual(by_model["Gemini 3.1 Flash Live"]["release_date"], "2026-03")
        self.assertTrue(by_model["Gemini 3.1 Pro"]["official_link"].endswith("Gemini-3-1-Pro-Model-Card.pdf"))
        self.assertTrue(
            by_model["Gemini 3.1 Flash Live"]["official_link"].endswith("Gemini-3-1-Flash-Live-Model-Card.pdf")
        )
        self.assertLessEqual(len(by_model["Gemini 3.1 Pro"]["candidate_links"]), 2)

    def test_discover_xai_uses_release_notes_when_primary_sources_are_blocked(self) -> None:
        fetcher = StaticFetcher()
        fetcher.text_map["https://data.x.ai/"] = ""
        fetcher.text_map["https://x.ai/news"] = ""
        records = discover_models.discover_xai(
            fetcher,
            "2026-04-03T10:00:00Z",
            discover_models.load_alias_config(),
        )
        by_model = {record["model"]: record for record in records}
        self.assertEqual(by_model["Grok 4"]["release_date"], "2025-07")
        self.assertEqual(by_model["Grok 4.1 Fast"]["release_date"], "2025-11")
        self.assertEqual(by_model["Grok 4"]["official_link"], "https://x.ai/news/grok-4")
        self.assertEqual(by_model["Grok 4.1 Fast"]["official_link"], "https://x.ai/news/grok-4-1-fast")

    def test_discover_meta_uses_direct_official_article_when_index_has_no_llama_link(self) -> None:
        fetcher = StaticFetcher()
        fetcher.text_map["https://ai.meta.com/blog/"] = "<html><body>No index entries</body></html>"
        records = discover_models.discover_meta(
            fetcher,
            "2026-04-03T10:00:00Z",
            discover_models.load_alias_config(),
        )
        by_model = {record["model"]: record for record in records}
        self.assertEqual(by_model["Llama 4 Scout/Maverick"]["release_date"], "2025-04")
        self.assertEqual(
            by_model["Llama 4 Scout/Maverick"]["official_link"],
            "https://ai.meta.com/blog/llama-4-multimodal-intelligence/",
        )

    def test_month_distance_rejects_stale_arxiv_backfill_links(self) -> None:
        self.assertEqual(discover_models.month_distance("2025-05", "2025-05"), 0)
        self.assertGreater(discover_models.month_distance("2026-02", "2022-07") or 0, 6)

    def test_discover_all_models_covers_industry_wide_major_manufacturers(self) -> None:
        records = discover_models.discover_all_models(
            until="2026-04-03",
            fetcher=StaticFetcher(),
            discovered_at="2026-04-03T10:00:00Z",
        )
        by_org = {}
        for record in records:
            if record["release_classification"] != "model_release":
                continue
            by_org.setdefault(record["org_slug"], set()).add(record["model"])

        expected = {
            "openai": {"GPT-5.4 Thinking", "GPT-5.3 Instant", "o3 / o4-mini"},
            "anthropic": {"Claude Haiku 4.5"},
            "google": {"Gemma 4", "Gemini 3.1 Pro"},
            "xai": {"Grok 4.1"},
            "meta": {"Llama 4 Scout/Maverick"},
            "alibaba_qwen": {"Qwen3", "Qwen3-Coder", "Qwen3-Next", "Qwen3-Max"},
            "quark": {"QuarkMed"},
            "deepseek": {"DeepSeek V3.2"},
            "moonshot": {"Kimi K2.5"},
            "stepfun": {"Step-3.5-Flash"},
            "tencent": {"Yuanbao (Hunyuan-TurboS)"},
            "baidu": {"ERNIE 4.5"},
            "bytedance": {"MedXIAOHE", "Seed1.5-VL"},
            "baichuan": {"Baichuan-M3"},
            "inclusionai": {"Ling 2.5"},
            "meituan": {"LongCat-Next"},
            "minimax": {"MiniMax M2.7"},
            "zhipu": {"GLM-5V-Turbo"},
        }
        for slug, expected_models in expected.items():
            self.assertTrue(expected_models.issubset(by_org.get(slug, set())), slug)


if __name__ == "__main__":
    unittest.main()
