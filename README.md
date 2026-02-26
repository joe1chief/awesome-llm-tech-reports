# Awesome LLM Technical Reports (2025-01 ~ 2026-02)

> A curated, structured local archive of frontier LLM / multimodal / medical-vertical model documentation — papers, system cards, model cards, and official blog posts — organized by **year / company**.

<p align="center">
  <img src="https://img.shields.io/badge/Time%20Range-2025--01%20to%202026--02-4c1" alt="time range">
  <img src="https://img.shields.io/badge/Models-46-blue" alt="models">
  <img src="https://img.shields.io/badge/Local%20PDF-43-success" alt="local pdf">
  <img src="https://img.shields.io/badge/Failed-3-critical" alt="failed">
  <img src="https://img.shields.io/badge/Status-Continuously%20Maintained-orange" alt="status">
  <img src="https://img.shields.io/github/stars/joe1chief/awesome-llm-tech-reports-2025-2026?style=flat" alt="stars">
</p>

<div align="center">

### **46 Models · 18 Organizations · 43 Local PDFs**

</div>

<details>
<summary><b>View All 18 Organizations</b></summary>

<div align="center">

| | | |
|:---:|:---:|:---:|
| **OpenAI** (6) | **Anthropic** (5) | **Google** (6) |
| **Meta** (1) | **xAI** (3) | **DeepSeek** (4) |
| **Alibaba / Qwen** (3) | **Zhipu AI** (2) | **Moonshot AI** (2) |
| **MiniMax** (2) | **StepFun** (2) | **Baidu** (2) |
| **Baichuan** (2) | **InclusionAI** (1) | **ByteDance** (4) |
| **Tencent** (1) | **Meituan** (2) | **Quark** (1) |

</div>

</details>

---

## Table of Contents

- [Project Scope](#project-scope)
- [Archive Rules](#archive-rules)
- [Snapshot Metrics](#snapshot-metrics)
- [Quick Refresh](#quick-refresh)
- [Company Quick Links](#company-quick-links)
- [Model Index (Folded by Year)](#model-index-folded-by-year)
- [Known Failed Downloads](#known-failed-downloads)
- [Star History](#star-history)

## Project Scope

- Systematically archives major model releases from **January 2025** to **February 2026** across LLM, multimodal, and medical-vertical domains.
- Downloads official papers, system cards, model cards as local PDFs; exports web-only blog pages to PDF via headless browser.
- Provides a single searchable Markdown index sorted in reverse chronological order.

## Archive Rules

- **Level-1 directory**: year (`2025/`, `2026/`)
- **Level-2 directory**: company slug (e.g. `openai/`, `google/`, `bytedance/`)
- **Filename pattern**: `YYYY-MM_model-name.pdf`

```text
llm_papers/
├── 2025/
│   ├── openai/
│   ├── google/
│   ├── bytedance/
│   └── ...
├── 2026/
│   ├── openai/
│   ├── zhipu/
│   └── ...
├── download_papers.py
└── README.md
```

## Snapshot Metrics

| Metric | Value |
| --- | ---: |
| Total models tracked | 46 |
| Local PDFs available | 43 |
| Failed source links | 3 |
| Online-only entries | 0 (exported to PDF) |

## Quick Refresh

```bash
python3 download_papers.py
```

> The script auto-normalizes arXiv links (`/abs/` → `/pdf/`), downloads direct PDF sources, and exports non-PDF technical webpages to local PDF via Playwright.

## Company Quick Links

`2026`: [`Zhipu AI`](#company-zhipu) · [`StepFun`](#company-stepfun) · [`Baidu`](#company-baidu) · [`Baichuan`](#company-baichuan) · [`ByteDance`](#company-bytedance) · [`OpenAI`](#company-openai) · [`Anthropic`](#company-anthropic) · [`Alibaba`](#company-alibaba_qwen) · [`MiniMax`](#company-minimax) · [`Moonshot AI`](#company-moonshot) · [`InclusionAI`](#company-inclusionai)

`2025`: [`DeepSeek`](#company-deepseek) · [`Google`](#company-google) · [`xAI`](#company-xai) · [`Meituan`](#company-meituan) · [`Meta`](#company-meta) · [`Quark`](#company-quark) · [`Tencent`](#company-tencent) (plus shared companies above)

### Company Directory Index

<a id="company-openai"></a>
- **OpenAI**: `2025/openai/`, `2026/openai/`
<a id="company-anthropic"></a>
- **Anthropic**: `2025/anthropic/`, `2026/anthropic/`
<a id="company-google"></a>
- **Google**: `2025/google/`
<a id="company-meta"></a>
- **Meta**: `2025/meta/`
<a id="company-xai"></a>
- **xAI**: `2025/xai/`
<a id="company-deepseek"></a>
- **DeepSeek**: `2025/deepseek/`
<a id="company-alibaba_qwen"></a>
- **Alibaba / Qwen**: `2025/alibaba_qwen/`, `2026/alibaba_qwen/`
<a id="company-zhipu"></a>
- **Zhipu AI**: `2025/zhipu/`, `2026/zhipu/`
<a id="company-moonshot"></a>
- **Moonshot AI**: `2025/moonshot/`, `2026/moonshot/`
<a id="company-minimax"></a>
- **MiniMax**: `2025/minimax/`, `2026/minimax/`
<a id="company-stepfun"></a>
- **StepFun**: `2025/stepfun/`, `2026/stepfun/`
<a id="company-baidu"></a>
- **Baidu**: `2025/baidu/`, `2026/baidu/`
<a id="company-baichuan"></a>
- **Baichuan Intelligence**: `2025/baichuan/`, `2026/baichuan/`
<a id="company-inclusionai"></a>
- **InclusionAI (Ant Group)**: `2026/inclusionai/`
<a id="company-bytedance"></a>
- **ByteDance**: `2025/bytedance/`, `2026/bytedance/`
<a id="company-tencent"></a>
- **Tencent**: `2025/tencent/`
<a id="company-meituan"></a>
- **Meituan**: `2025/meituan/`
<a id="company-quark"></a>
- **Quark (Alibaba)**: `2025/quark/`

## Model Index (Folded by Year)

<details open>
<summary><b>📅 2026 (12 models)</b></summary>

| Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File |
| --- | --- | --- | --- | --- | --- |
| 2026-02 | Zhipu AI | GLM-5 | We present GLM-5, a next-generation foundation model designed to transition the paradigm of vibe coding to agentic engineering. Building upon the agen- tic, reasoning, and coding (ARC) capabilities of its predecessor, GLM-5 adopts DSA to significantly reduce training and inferenc. | https://arxiv.org/pdf/2602.15763 | 2026/zhipu/2026-02_glm-5.pdf |
| 2026-02 | StepFun | Step-3.5-Flash | We introduceStep 3.5 Flash, a sparse Mixture-of-Experts (MoE) model that bridges the gap between frontier-level agentic intelligence and computational efficiency. We focus on what matters most when building agents: reasoning that’s sharp, and execution that’s fast and reliable. | https://arxiv.org/pdf/2602.10604 | 2026/stepfun/2026-02_step-3.5-flash.pdf |
| 2026-02 | Baidu | ERNIE 5.0 | In this report, we introduceERNIE 5.0, a natively autoregressive foundation model desinged for unified multimodal understanding and generation across text, image, video, and audio. All modalities are trained from scratch under a unified next-group- of-tokens prediction objective. | https://arxiv.org/pdf/2602.04705 | 2026/baidu/2026-02_ernie-5.0.pdf |
| 2026-02 | Baichuan Intelligence | Baichuan-M3 | We introduce Baichuan-M3, a medical-enhanced large language model engineered to shift the paradigm from passive question-answering to active, clinical-grade decision support. Addressing the limitations of existing systems in open-ended consultations, Baichuan-M3utilizesaspecializ. | https://arxiv.org/pdf/2602.06570 | 2026/baichuan/2026-02_baichuan-m3.pdf |
| 2026-02 | ByteDance | MedXIAOHE | We present MedXIAOHE, a medical vision-language foundation model designed to advance general- purpose medical understanding and reasoning in real-world clinical applications. MedXIAOHE achieves state-of-the-art performance across diverse medical benchmarks and surpasses leading c. | https://arxiv.org/pdf/2602.12705 | 2026/bytedance/2026-02_medxiaohe.pdf |
| 2026-02 | OpenAI | GPT-5.3-Codex | Addendum to o3 and o4-mini system card: Codex OpenAI May 16, 2025 Codex is a cloud-based coding agent. Codex is powered by codex-1, a version of OpenAI o3 optimized for software engineering. | https://cdn.openai.com/pdf/8df7697b-c1b2-4222-be00-1fd3298f351d/codex_system_card.pdf | 2026/openai/2026-02_gpt-5.3-codex.pdf |
| 2026-02 | Anthropic | Claude Opus 4.6 | This system card describes Claude Opus 4.6, a large language model from Anthropic. Claude Opus 4.6 is a frontier model with strong capabilities in software engineering, agentic tasks, and long context reasoning, as well as in knowledge work—including ﬁnancial analysis, document c. | https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf | 2026/anthropic/2026-02_claude-opus-4.6.pdf |
| 2026-02 | ByteDance | Seed 2.0 | Seed2.0 Model Card: Towards Intelligence Frontier for Real-World Complexity Bytedance Seed 1 Introduction Large Language Models (LLMs) now play a central role in modern digital infrastructure. Usage has grown dramatically across both professional and personal contexts [11]. | https://lf3-static.bytednsdoc.com/obj/eden-cn/lapzild-tss/ljhwZthlaukjlkulzlp/seed2/0214/Seed2.0%20Model%20Card.pdf | 2026/bytedance/2026-02_seed-2.0.pdf |
| 2026-02 | Alibaba | Qwen 3.5 |  Qwen3.5: Towards Native Mul Agents 2026/02/16 · 40 minute · 8049 words · QwenTeam ⼁ Translations:简体中⽂ We are delighted to announce the official release of Qwen3.5, introducing the open-weight of the first model i namely Qwen3.5-397B-A17B. As a native vision-language model, Qwen. | https://qwen.ai/blog?id=qwen3.5 | 2026/alibaba_qwen/2026-02_qwen-3.5.pdf |
| 2026-02 | MiniMax | MiniMax M2.5 | 2026.2.12 MiniMax M2.5: Built for Real- W orld Productivity. Access API Coding Plan Try Agent Now M o d e l s P r o d u c t A P I N e w s C o m p a n y L o g i n Today we're introducing our latest model, MiniMax-M2.5. | https://www.minimax.io/news/minimax-m25 | 2026/minimax/2026-02_minimax-m2.5.pdf |
| 2026-02 | Moonshot AI | Kimi K2.5 | We introduce Kimi K2.5, an open-source multimodal agentic model designed to advance general agentic intelligence. K2.5 emphasizes the joint optimization of text and vision so that two modali- ties enhance each other. | https://github.com/MoonshotAI/Kimi-K2.5/raw/master/tech_report.pdf | 2026/moonshot/2026-02_kimi-k2.5.pdf |
| 2026-02 | InclusionAI (Ant Group) | Ling 2.5 | inclusionAI/Ling-V2.5Public 1Branch 0Tags Go to file Go to file Code HanxiaoZhangupdate README eb1c3c7 · last week docs init repo last week examples/sft/llama_fact… init repo last week figures init repo last week models init repo last week LICENSE init repo last week README.md up. | https://github.com/inclusionAI/Ling-V2.5 | 2026/inclusionai/2026-02_ling-2.5.pdf |

</details>

<details>
<summary><b>📅 2025 (34 models)</b></summary>

| Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File |
| --- | --- | --- | --- | --- | --- |
| 2025-12 | OpenAI | GPT-5.2 | Update to GPT-5 System Card: GPT-5.2 OpenAI December 11, 2025 1 Contents 1 Introduction 3 2 Model Data and Training 3 3 Baseline Model Safety Evaluations 3 3.1 Disallowed Content Evaluations . 10 4 Preparedness Framework 11 4.1 Capabilities Assessment . | https://cdn.openai.com/pdf/3a4153c8-c748-4b71-8e31-aecbde944f8d/oai_5_2_system-card.pdf | 2025/openai/2025-12_gpt-5.2.pdf |
| 2025-12 | DeepSeek | DeepSeek V3.2 | We introduce DeepSeek-V3.2, a model that harmonizes high computational efficiency with supe- rior reasoning and agent performance. The key technical breakthroughs of DeepSeek-V3.2 are as follows:(1) DeepSeek Sparse Attention (DSA): We introduce DSA, an efficient attention mecha-. | https://arxiv.org/pdf/2512.02556 | 2025/deepseek/2025-12_deepseek-v3.2.pdf |
| 2025-12 | Google | Gemini 3 Flash | Model card published: December, 2025 Gemini 3 Flash Model Card Gemini 3 Flash - Model Card Model Cards are intended to provide essential information on Gemini models, including known limitations, mitigation approaches, and safety performance. Model cards may be updated from time-. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Flash-Model-Card.pdf | 2025/google/2025-12_gemini-3-flash.pdf |
| 2025-12 | StepFun | Step-DeepResearch | As Large Language Models (LLMs) shift toward autonomous agents, Deep Research has emerged as a pivotal metric for assessing the core competitiveness of agents. However, existing works primarily focus on academic multi-hop search tasks with ground truth, such as BrowseComp, which. | https://arxiv.org/pdf/2512.20491 | 2025/stepfun/2025-12_step-deepresearch.pdf |
| 2025-11 | Google | Gemini 3 Pro | Model card update: December, 2025 Gemini 3 Pro Model Card Gemini 3 Pro - Model Card Model Cards are intended to provide essential information on Gemini models, including known limitations, mitigation approaches, and safety performance. Model cards may be updated from time-to-time. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf | 2025/google/2025-11_gemini-3-pro.pdf |
| 2025-11 | xAI | Grok 4.1 | Source PDF could not be downloaded. | https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf | Download failed |
| 2025-11 | Alibaba | Qwen3-VL | We introduce Qwen3-VL, the most capable vision–language model in the Qwen series to date, achieving superior performance across a broad range of multimodal benchmarks. It natively supports interleaved contexts of up to 256K tokens, seamlessly integrat- ing text, images, and video. | https://arxiv.org/pdf/2511.21631 | 2025/alibaba_qwen/2025-11_qwen3-vl.pdf |
| 2025-10 | MiniMax | MiniMax M2.0 | MiniMax-AI/MiniMax-M2Public 2Branches 0Tags Go to file Go to file Code MiniMax-AI-DevMerge pull request#42from rogeryoungh/patch-2 2e575ef · 3 months ago .github/ISSUE_TEMPLATE update issue template 3 months ago docs update wechat 4 months ago figures update bench figure 4 months. | https://github.com/MiniMax-AI/MiniMax-M2 | 2025/minimax/2025-10_minimax-m2.0.pdf |
| 2025-09 | xAI | Grok 4 Fast | Source PDF could not be downloaded. | https://data.x.ai/2025-09-19-grok-4-fast-model-card.pdf | Download failed |
| 2025-09 | DeepSeek | DeepSeek V3.1-Terminus | We present DeepSeek-V3, a strong Mixture-of-Experts (MoE) language model with 671B total parameters with 37B activated for each token. To achieve efficient inference and cost-effective training, DeepSeek-V3 adopts Multi-head Latent Attention (MLA) and DeepSeekMoE architec- tures. | https://arxiv.org/pdf/2412.19437 | 2025/deepseek/2025-09_deepseek-v3.1-terminus.pdf |
| 2025-09 | Baichuan Intelligence | Baichuan-M2 | As large language models (LLMs) advance in conversational and reasoning capabil- ities, their practical application in healthcare has become a critical research focus. However, there is a notable gap between the performance of medical LLMs on static benchmarks such as USMLE and t. | https://arxiv.org/pdf/2509.02208 | 2025/baichuan/2025-09_baichuan-m2.pdf |
| 2025-09 | Meituan | LongCat-Flash | We introduce LongCat-Flash, a 560-billion-parameter Mixture-of-Experts (MoE) language model designed for both computational efficiency and advanced agentic capabilities. Stemming from the need for scalable efficiency, LongCat-Flash adopts two novel designs: (a) Zero-computation E. | https://arxiv.org/pdf/2509.01322 | 2025/meituan/2025-09_longcat-flash.pdf |
| 2025-09 | Meituan | LongCat-Flash-Thinking | We present LongCat-Flash-Thinking, an efficient 560-billion-parameter open-source Mixture-of- Experts (MoE) reasoning model. Its advanced capabilities are cultivated through a meticulously crafted training process, beginning with long Chain-of-Thought (CoT) data cold-start and cu. | https://arxiv.org/pdf/2509.18883 | 2025/meituan/2025-09_longcat-flash-thinking.pdf |
| 2025-08 | Zhipu AI | GLM-4.5 | We present GLM-4.5, an open-source Mixture-of-Experts (MoE) large language model with 355B total parameters and 32B activated parameters, featuring a hybrid reasoning method that supports both thinking and direct response modes. Through multi-stage training on 23T tokens and comp. | https://arxiv.org/pdf/2508.06471 | 2025/zhipu/2025-08_glm-4.5.pdf |
| 2025-08 | OpenAI | GPT-5 | The canonical version can be found at: https://cdn.openai.com/gpt-5-system-card.pdf August 13, 2025 1. | https://cdn.openai.com/pdf/8124a3ce-ab78-4f06-96eb-49ea29ffb52f/gpt5-system-card-aug7.pdf | 2025/openai/2025-08_gpt-5.pdf |
| 2025-08 | OpenAI | gpt-oss-120b/20b | gpt-oss-120b & gpt-oss-20b Model Card OpenAI August 5, 2025 1 Contents 1 Introduction 3 2 Model architecture, data, training and evaluations 3 2.1 Quantization . 5 2.5 Post-Training for Reasoning and Tool Use . | https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf | 2025/openai/2025-08_gpt-oss-120b-20b.pdf |
| 2025-08 | Quark (Alibaba) | QuarkMed | 2025-8-19 QuarkMed Medical Foundation Model Technical Report Ao Li1, Bin Yan1, Bingfeng Cai1, Chenxi Li1, Cunzhong Zhao1, Fugen Yao1, Gaoqiang Liu1, Guanjun Jiang1, Jian Xu1, Liang Dong1, Liansheng Sun1, Rongshen Zhang1, Xiaolei Gui1, Xin Liu1, Xin Shang1, Yao Wu1, Yu Cao1, Zhenx. | https://arxiv.org/pdf/2508.11894 | 2025/quark/2025-08_quarkmed.pdf |
| 2025-07 | Moonshot AI | Kimi K2.0 | We introduce Kimi K2, a Mixture-of-Experts (MoE) large language model with 32 billion activated parameters and 1 trillion total parameters. We propose the MuonClip optimizer, which improves upon Muon with a novel QK-clip technique to address training instability while enjoying th. | https://arxiv.org/pdf/2507.20534 | 2025/moonshot/2025-07_kimi-k2.0.pdf |
| 2025-07 | xAI | Grok 4 | Source PDF could not be downloaded. | https://data.x.ai/2025-08-20-grok-4-model-card.pdf | Download failed |
| 2025-07 | Google | Gemini 2.5 Pro | Model card updated June 27, 2025 Gemini 2.5 Pro Model Card Model Cards are intended to provide essential information on Gemini models, including known limitations, mitigation approaches, and safety performance. Model cards may be updated from time-to-time; for example, to include. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Pro-Model-Card.pdf | 2025/google/2025-07_gemini-2.5-pro.pdf |
| 2025-07 | Google | Gemini 2.5 Flash | Model card published/updated December, 2025 2.5 Flash and native capabilities –audio & image Model Card Gemini 2.5 Flash - Model Card Model Cards are intended to provide essential information on Gemini models, including known limitations, mitigation approaches, and safety perform. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Flash-Model-Card.pdf | 2025/google/2025-07_gemini-2.5-flash.pdf |
| 2025-06 | Anthropic | Claude Opus 4.5 | This system card describes our evaluations of Claude Opus 4.5, a large language model from Anthropic. Claude Opus 4.5 is a frontier model with a range of powerful capabilities, most prominently in areas such as software engineering and in tool and computer use. | https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf | 2025/anthropic/2025-06_claude-opus-4.5.pdf |
| 2025-06 | Anthropic | Claude Sonnet 4.5 | In this system card, we introduce Claude Sonnet 4.5, a new hybrid reasoning large language model from Anthropic with strengths in coding, agentic tasks, and computer use. We detail a very wide range of evaluations run to assess the model’s safety and alignment. | https://assets.anthropic.com/m/12f214efcc2f457a/original/Claude-Sonnet-4-5-System-Card.pdf | 2025/anthropic/2025-06_claude-sonnet-4.5.pdf |
| 2025-06 | Baidu | ERNIE 4.5 | In this report, we introduce ERNIE 4.5, a new family of large-scale foundation models comprising 10 distinct variants. The model family consists of Mixture-of-Experts (MoE) models with 47B and 3B active parameters (the largest containing 424B total parameters), as well as a dense. | https://yiyan.baidu.com/blog/publication/ERNIE_Technical_Report.pdf | 2025/baidu/2025-06_ernie-4.5.pdf |
| 2025-05 | Alibaba | Qwen3 | In this work, we present Qwen3, the latest version of the Qwen model family. Qwen3 comprises a series of large language models (LLMs) designed to advance performance, efficiency, and multilingual capabilities. | https://arxiv.org/pdf/2505.09388 | 2025/alibaba_qwen/2025-05_qwen3.pdf |
| 2025-05 | Tencent | Yuanbao (Hunyuan-TurboS) | As Large Language Models (LLMs) rapidly advance, we introduce Hunyuan-TurboS, a novel large hybrid Transformer-Mamba Mixture of Experts (MoE) model. It syner- gistically combines Mamba’s long-sequence processing efficiency with Transformer’s superior contextual understanding. | https://arxiv.org/pdf/2505.15431 | 2025/tencent/2025-05_yuanbao-hunyuan-turbos.pdf |
| 2025-05 | ByteDance | Seed1.5-VL | We present Seed1.5-VL, a vision-language foundation model designed to advance general-purpose multimodal understanding and reasoning. Seed1.5-VL is composed with a 532M-parameter vision encoder and a Mixture-of-Experts (MoE) LLM of 20B active parameters. | https://arxiv.org/pdf/2505.07062 | 2025/bytedance/2025-05_seed1.5-vl.pdf |
| 2025-05 | Anthropic | Claude Opus 4 / Sonnet 4 | This system card introduces Claude Opus 4 and Claude Sonnet 4, two new hybrid reasoning large language models from Anthropic. In the system card, we describe: a wide range of pre-deployment safety tests conducted in line with the commitments in our Responsible Scaling Policy; tes. | https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf | 2025/anthropic/2025-05_claude-opus-4-sonnet-4.pdf |
| 2025-04 | OpenAI | o3 / o4-mini | OpenAI o3 and o4-mini System Card OpenAI April 16, 2025 1 Introduction OpenAI o3 and OpenAI o4-mini combine state-of-the-art reasoning with full tool capabilities — web browsing, Python, image and file analysis, image generation, canvas, automations, file search, and memory. Thes. | https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf | 2025/openai/2025-04_o3-o4-mini.pdf |
| 2025-04 | Meta | Llama 4 Scout/Maverick | Large Language Model The Llama 4 herd: The beginning of a new era of natively multimodal AI innovation April 5, 2025 • 12 minute read Takeaways We’re sharing the first models in the Llama 4 herd, which will enable people to build more personalized multimodal experiences. Llama 4. | https://ai.meta.com/blog/llama-4-multimodal-intelligence/ | 2025/meta/2025-04_llama-4-scout-maverick.pdf |
| 2025-04 | ByteDance | Seed1.5-Thinking | We introduce Seed1.5-Thinking, capable of reasoning through thinking before responding, resulting in improved performance on a wide range of benchmarks. Seed1.5-Thinking achieves86.7 on AIME 2024, 55.0 on Codeforces and77.3 on GPQA, demonstrating excellent reasoning abilities in. | https://arxiv.org/pdf/2504.13914 | 2025/bytedance/2025-04_seed1.5-thinking.pdf |
| 2025-03 | Google | Gemma 3 | 2025-03-12 Gemma 3 Technical Report Gemma Team, Google DeepMind1 We introduce Gemma 3, a multimodal addition to the Gemma family of lightweight open models, ranging in scale from 1 to 27 billion parameters. This version introduces vision understanding abilities, a wider coverage. | https://arxiv.org/pdf/2503.19786 | 2025/google/2025-03_gemma-3.pdf |
| 2025-01 | DeepSeek | DeepSeek R1 | General reasoning represents a long-standing and formidable challenge in artificial intelli- gence. Recent breakthroughs, exemplified by large language models (LLMs) (Brown et al., 2020; OpenAI, 2023) and chain-of-thought prompting (Wei et al., 2022b), have achieved con- siderabl. | https://arxiv.org/pdf/2501.12948 | 2025/deepseek/2025-01_deepseek-r1.pdf |
| 2025-01 | DeepSeek | DeepSeek V3 | We present DeepSeek-V3, a strong Mixture-of-Experts (MoE) language model with 671B total parameters with 37B activated for each token. To achieve efficient inference and cost-effective training, DeepSeek-V3 adopts Multi-head Latent Attention (MLA) and DeepSeekMoE architec- tures. | https://arxiv.org/pdf/2412.19437 | 2025/deepseek/2025-01_deepseek-v3.pdf |

</details>

## Known Failed Downloads

> These source links could not be downloaded in the current environment (likely due to `data.x.ai` access restrictions). Retry manually or via VPN.

| Model | URL |
| --- | --- |
| Grok 4.1 | `https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf` |
| Grok 4 Fast | `https://data.x.ai/2025-09-19-grok-4-fast-model-card.pdf` |
| Grok 4 | `https://data.x.ai/2025-08-20-grok-4-model-card.pdf` |

## Star History

<a href="https://star-history.com/#joe1chief/awesome-llm-tech-reports-2025-2026&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=joe1chief/awesome-llm-tech-reports-2025-2026&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=joe1chief/awesome-llm-tech-reports-2025-2026&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=joe1chief/awesome-llm-tech-reports-2025-2026&type=Date" />
 </picture>
</a>
