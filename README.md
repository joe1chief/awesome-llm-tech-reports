# Awesome LLM Technical Reports (2025-01 ~ 2026-04)

> A curated, structured local archive of frontier LLM / multimodal / medical-vertical model documentation — papers, system cards, model cards, and official blog posts — organized by **year / company**.

<p align="center">
  <img src="https://img.shields.io/badge/Time%20Range-2025--01%20to%202026--04-4c1" alt="time range">
  <img src="https://img.shields.io/badge/Models-73-blue" alt="models">
  <img src="https://img.shields.io/badge/Local%20PDF-73-success" alt="local pdf">
  <img src="https://img.shields.io/badge/Status-Continuously%20Maintained-orange" alt="status">
  <img src="https://img.shields.io/github/stars/joe1chief/awesome-llm-tech-reports?style=flat" alt="stars">
</p>

---

## Table of Contents

- [Project Scope](#project-scope)
- [Release Timeline](#release-timeline)
- [Company Quick Links](#company-quick-links)
- [Model Index (Folded by Year)](#model-index-folded-by-year)
- [Star History](#star-history)

## Project Scope

- Systematically archives major model releases from **January 2025** to **April 2026** across LLM, multimodal, and medical-vertical domains.
- Downloads official papers, system cards, model cards as local PDFs; exports web-only blog pages to PDF via headless browser.
- Provides a single searchable Markdown index sorted in reverse chronological order.

## Release Timeline

**Legend (Camp Colors):** `OpenAI` · `Anthropic` · `Google` · `China-based Labs` · `Other Global`  
**Impact Highlight:** nodes with **★** are ecosystem-shaping releases (community discussion, benchmark influence, or deployment adoption).

![Release Timeline](assets/diagrams/release-timeline.svg)

<details>
<summary><b>Monthly Density Snapshot</b></summary>

![Monthly Density Snapshot](assets/diagrams/monthly-density.svg)

> Bubble size follows the release count from the model index table.

</details>

## Company Quick Links

`2026`: [`Zhipu AI`](#company-zhipu) · [`Google`](#company-google) · [`OpenAI`](#company-openai) · [`MiniMax`](#company-minimax) · [`Meituan`](#company-meituan) · [`StepFun`](#company-stepfun) · [`Baidu`](#company-baidu) · [`Baichuan Intelligence`](#company-baichuan) · [`ByteDance`](#company-bytedance) · [`Anthropic`](#company-anthropic) · [`Alibaba`](#company-alibaba_qwen) · [`Moonshot AI`](#company-moonshot) · [`InclusionAI (Ant Group)`](#company-inclusionai)

`2025`: [`OpenAI`](#company-openai) · [`DeepSeek`](#company-deepseek) · [`Google`](#company-google) · [`StepFun`](#company-stepfun) · [`Zhipu AI`](#company-zhipu) · [`MiniMax`](#company-minimax) · [`Meituan`](#company-meituan) · [`xAI`](#company-xai) · [`Alibaba`](#company-alibaba_qwen) · [`Baichuan Intelligence`](#company-baichuan) · [`Quark`](#company-quark) · [`Moonshot AI`](#company-moonshot) · [`Anthropic`](#company-anthropic) · [`Baidu`](#company-baidu) · [`Tencent`](#company-tencent) · [`ByteDance`](#company-bytedance) · [`Meta`](#company-meta)

### Company Directory Index

<a id="company-alibaba_qwen"></a>
- **Alibaba / Qwen**: `2025/alibaba_qwen/`, `2026/alibaba_qwen/`
<a id="company-anthropic"></a>
- **Anthropic**: `2025/anthropic/`, `2026/anthropic/`
<a id="company-baichuan"></a>
- **Baichuan Intelligence**: `2025/baichuan/`, `2026/baichuan/`
<a id="company-baidu"></a>
- **Baidu**: `2025/baidu/`, `2026/baidu/`
<a id="company-bytedance"></a>
- **ByteDance**: `2025/bytedance/`, `2026/bytedance/`
<a id="company-deepseek"></a>
- **DeepSeek**: `2025/deepseek/`
<a id="company-google"></a>
- **Google**: `2025/google/`, `2026/google/`
<a id="company-inclusionai"></a>
- **InclusionAI (Ant Group)**: `2026/inclusionai/`
<a id="company-meituan"></a>
- **Meituan**: `2025/meituan/`, `2026/meituan/`
<a id="company-meta"></a>
- **Meta**: `2025/meta/`
<a id="company-minimax"></a>
- **MiniMax**: `2025/minimax/`, `2026/minimax/`
<a id="company-moonshot"></a>
- **Moonshot AI**: `2025/moonshot/`, `2026/moonshot/`
<a id="company-openai"></a>
- **OpenAI**: `2025/openai/`, `2026/openai/`
<a id="company-quark"></a>
- **Quark (Alibaba)**: `2025/quark/`
<a id="company-stepfun"></a>
- **StepFun**: `2025/stepfun/`, `2026/stepfun/`
<a id="company-tencent"></a>
- **Tencent**: `2025/tencent/`
<a id="company-zhipu"></a>
- **Zhipu AI**: `2025/zhipu/`, `2026/zhipu/`
<a id="company-xai"></a>
- **xAI**: `2025/xai/`

## Model Index (Folded by Year)

<details open>
<summary><b>2026 (27 models)</b></summary>

| Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File |
| --- | --- | --- | --- | --- | --- |
| 2026-04 | Zhipu AI | GLM-5V-Turbo | multimodal coding and agentic tasks, as well as pure-text coding, GLM-5V-Turbo delivers strong performance with a smaller model size 30+ Task Joint Reinforcement Learning : During RL, the model is jointly optimized across 30+ task types, spanning STEM, grounding, video, GUI agents, and coding agents, resulting in more robust gains in perception, reasoning, and agentic execution | https://docs.z.ai/guides/vlm/glm-5v-turbo | 2026/zhipu/2026-04_glm-5v-turbo.pdf |
| 2026-04 | Google | Gemma 4 | Featuring both Dense and Mixture-of-Experts (MoE) architectures, Gemma 4 is well-suited for tasks like text generation, coding, and reasoning They are well-suited for reasoning, agentic workflows, coding, and multimodal understanding | https://ai.google.dev/gemma/docs/core/model_card_4?utm_source=deepmind.google&utm_medium=referral&utm_campaign=gdm&utm_content | 2026/google/2026-04_gemma-4.pdf |
| 2026-03 | OpenAI | GPT-5.4 Thinking | Frontier reasoning model that unifies recent gains in coding, agentic workflows, and deep web research, while adding high-capability cybersecurity mitigations and stronger chain-of-thought monitoring. | https://deploymentsafety.openai.com/gpt-5-4-thinking/gpt-5-4-thinking.pdf | 2026/openai/2026-03_gpt-5.4-thinking.pdf |
| 2026-03 | OpenAI | GPT-5.3 Instant | General-purpose GPT-5 update tuned for richer web-grounded answers, smoother follow-up behavior, fewer dead ends and caveats, and improved everyday conversational usefulness. | https://deploymentsafety.openai.com/gpt-5-3-instant/gpt-5-3-instant.pdf | 2026/openai/2026-03_gpt-5.3-instant.pdf |
| 2026-03 | Google | Gemini 3.1 Flash-Lite | Cost-efficient multimodal reasoning model for high-volume, low-latency workloads, with 1M context, configurable reasoning depth, and strong coding and tool-use tradeoffs for production throughput. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Lite-Model-Card.pdf | 2026/google/2026-03_gemini-3.1-flash-lite.pdf |
| 2026-03 | Google | Gemini 3.1 Flash Live | Real-time multimodal model with native audio input/output, 128K context, and evaluation emphasis on low-latency voice and video interactions, conversational audio understanding, and multi-step function use. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Live-Model-Card.pdf | 2026/google/2026-03_gemini-3.1-flash-live.pdf |
| 2026-03 | MiniMax | MiniMax M2.7 | M2.7 is our first model deeply participating in its own evolution M2.7 is capable of building complex agent harnesses and completing highly elaborate productivity tasks, leveraging capabilities such as Agent Teams, complex Skills, and dynamic tool search | https://www.minimax.io/news/minimax-m27-en | 2026/minimax/2026-03_minimax-m2.7.pdf |
| 2026-03 | Meituan | LongCat-Next | Building on this foundation, we develop LongCat-Next, a native multimodal model that processes text, vision, and audio under a single autoregressive objective with minimal modality-specific design To transcend this limitation, we introduce Discrete Native Autoregressive (DiNA), a unified framework that represents multimodal information within a shared discrete space, enabling a consistent and principled autoregressive modeling across modalities | https://arxiv.org/pdf/2603.27538 | 2026/meituan/2026-03_longcat-next.pdf |
| 2026-03 | Meituan | LongCat-Flash-Prover | We introduce LongCat-Flash-Prover, a flagship 560-billion-parameter open-source Mixture-of-Experts (MoE) model that advances Native Formal Reasoning in Lean4 through agentic tool-integrated reasoning (TIR) The overview of the training process is shown in Figure 3, it begins with an initial checkpoint derived from the LongCat Mid-train Base model, an early-stage version of our previous LongCat-Flash-Thinking-2601 | https://arxiv.org/pdf/2603.21065 | 2026/meituan/2026-03_longcat-flash-prover.pdf |
| 2026-02 | Zhipu AI | GLM-5 | Next-generation foundation model designed for agentic engineering; adopts DSA (DeepSeek Sparse Attention) on top of MoE 744B/40B with async RL to strengthen reasoning, coding, and agent capabilities. | https://arxiv.org/pdf/2602.15763 | 2026/zhipu/2026-02_glm-5.pdf |
| 2026-02 | StepFun | Step-3.5-Flash | Sparse MoE model (196B/11B) bridging frontier agentic intelligence with computational efficiency; combines sliding-window and full attention for sharp reasoning and fast reliable execution. | https://arxiv.org/pdf/2602.10604 | 2026/stepfun/2026-02_step-3.5-flash.pdf |
| 2026-02 | Baidu | ERNIE 5.0 | Natively autoregressive foundation model for unified multimodal understanding and generation across text, image, video, and audio; trained under a next-group-of-tokens prediction objective with ultra-sparse MoE. | https://arxiv.org/pdf/2602.04705 | 2026/baidu/2026-02_ernie-5.0.pdf |
| 2026-02 | Baichuan Intelligence | Baichuan-M3 | Medical-enhanced LLM shifting from passive QA to active clinical-grade decision support; utilizes specialized active information acquisition for open-ended consultations with long-horizon reasoning. | https://arxiv.org/pdf/2602.06570 | 2026/baichuan/2026-02_baichuan-m3.pdf |
| 2026-02 | ByteDance | MedXIAOHE | Medical vision-language foundation model achieving SOTA across diverse medical benchmarks; features entity-aware pretraining, tool-augmented clinical reasoning, and surpasses leading commercial models. | https://arxiv.org/pdf/2602.12705 | 2026/bytedance/2026-02_medxiaohe.pdf |
| 2026-02 | OpenAI | GPT-5.3-Codex | Cloud-based agentic coding model powered by codex-1 (optimized o3); designed for long-horizon software engineering tasks with full tool capabilities in sandboxed environments. | https://deploymentsafety.openai.com/gpt-5-3-codex/gpt-5-3-codex.pdf | 2026/openai/2026-02_gpt-5.3-codex.pdf |
| 2026-02 | Anthropic | Claude Opus 4.6 | Frontier model with strong software engineering, agentic tasks, and long-context reasoning; system card covers financial analysis, document comprehension, and extensive safety evaluations. | https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf | 2026/anthropic/2026-02_claude-opus-4.6.pdf |
| 2026-02 | ByteDance | Seed 2.0 | LLM series targeting real-world complexity and enterprise workflows; model card describes capabilities across professional and personal contexts with emphasis on practical task completion. | https://lf3-static.bytednsdoc.com/obj/eden-cn/lapzild-tss/ljhwZthlaukjlkulzlp/seed2/0214/Seed2.0%20Model%20Card.pdf | 2026/bytedance/2026-02_seed-2.0.pdf |
| 2026-02 | Alibaba | Qwen 3.5 | Native vision-language model (397B-A17B) for multi-agent workflows; first open-weight model in the Qwen3.5 series with native multimodal capabilities and enhanced agent coordination. | https://qwen.ai/blog?id=qwen3.5 | 2026/alibaba_qwen/2026-02_qwen-3.5.pdf |
| 2026-02 | MiniMax | MiniMax M2.5 | Extensively RL-trained frontier model; SOTA in coding (80.2% SWE-Bench Verified), agentic tool use, and search; 37% faster than M2.1 at 100 tok/s with costs as low as $1/hour continuous operation. | https://www.minimax.io/news/minimax-m25 | 2026/minimax/2026-02_minimax-m2.5.pdf |
| 2026-02 | Moonshot AI | Kimi K2.5 | Open-source multimodal agentic model (1T MoE) jointly optimizing text and vision; features Agent Swarm for parallel sub-task execution and emphasizes mutual enhancement between modalities. | https://github.com/MoonshotAI/Kimi-K2.5/raw/master/tech_report.pdf | 2026/moonshot/2026-02_kimi-k2.5.pdf |
| 2026-02 | InclusionAI (Ant Group) | Ling 2.5 | 1T total / 63B active parameters with hybrid linear attention; supports up to 1M context via YaRN, features composite reward RL for efficiency-performance balance, and is compatible with mainstream agent platforms. | https://github.com/inclusionAI/Ling-V2.5 | 2026/inclusionai/2026-02_ling-2.5.pdf |
| 2026-02 | Google | Gemini 3.1 Pro | Advanced sparse-MoE multimodal reasoning model with 1M context, stronger agentic coding and long-context performance than Gemini 3 Pro, and published safety assessments under Google DeepMind's Frontier Safety Framework. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Pro-Model-Card.pdf | 2026/google/2026-02_gemini-3.1-pro.pdf |
| 2026-02 | Google | Gemini 3.1 Flash Image | Multimodal image generation and editing model with 1M context, text and image outputs, and reported gains on prompt following, edit preservation, and multi-turn image workflows. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-1-Flash-Image-Model-Card.pdf | 2026/google/2026-02_gemini-3.1-flash-image.pdf |
| 2026-02 | Alibaba | Qwen3-Coder-Next | Qwen3-Coder-Next is an 80-billion-parameter model that activates only 3 billion parameters during inference, enabling strong coding capability with efficient inference We present Qwen3-Coder-Next, an open-weight language model specialized for coding agents | https://raw.githubusercontent.com/QwenLM/Qwen3-Coder/main/qwen3_coder_next_tech_report.pdf | 2026/alibaba_qwen/2026-02_qwen3-coder-next.pdf |
| 2026-01 | Zhipu AI | GLM-4.7-Flash | Production-Ready Performance: Built for enterprise workloads with the reliability your applications demand Key Features 🎯 All-in-One API: A single API for text generation, image generation, document embeddings, NER, summarization, image classification, and more | https://huggingface.co/zai-org/GLM-4.7-Flash | 2026/zhipu/2026-01_glm-4.7-flash.pdf |
| 2026-01 | Google | MedGemma 1.5 | To our knowledge, MedGemma 1.5 is the first public release of an open multimodal large language model that can interpret high-dimensional medical data while also retaining the ability to interpret general 2D data and text MedGemma 1.5 4B improves at text-based tasks over MedGemma 1 4B, including on medical reasoning (Med QA) and electronic health record information retrieval (EHRQA) | https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/ | 2026/google/2026-01_medgemma-1.5.pdf |
| 2026-01 | Meituan | LongCat-Flash-Thinking-2601 | We introduce LongCat-Flash-Thinking-2601, a 560-billion-parameter open-source Mixture-of-Experts (MoE) reasoning model with superior agentic reasoning capability In this work, we introduce LongCat-Flash-Thinking-2601, a powerful and efficient Mixture-of-Experts (MoE) reasoning model with 560B total parameters and 27B activated parameters on average per token, featuring strong agentic reasoning capability | https://arxiv.org/pdf/2601.16725 | 2026/meituan/2026-01_longcat-flash-thinking-2601.pdf |

</details>

<details>
<summary><b>2025 (46 models)</b></summary>

| Release Date | Organization | Model | Core Highlights (from PDF) | Official Link | Local File |
| --- | --- | --- | --- | --- | --- |
| 2025-12 | OpenAI | GPT-5.2 | Iterative update to GPT-5 system card; covers enhanced safety evaluations, disallowed-content testing, and Preparedness Framework capability assessments for the GPT-5.2 release. | https://cdn.openai.com/pdf/3a4153c8-c748-4b71-8e31-aecbde944f8d/oai_5_2_system-card.pdf | 2025/openai/2025-12_gpt-5.2.pdf |
| 2025-12 | DeepSeek | DeepSeek V3.2 | Harmonizes high computational efficiency with superior reasoning and agent performance; introduces DeepSeek Sparse Attention (DSA) and scalable RL framework for improved long-context capabilities. | https://arxiv.org/pdf/2512.02556 | 2025/deepseek/2025-12_deepseek-v3.2.pdf |
| 2025-12 | Google | Gemini 3 Flash | High-efficiency multimodal model card; covers known limitations, mitigation approaches, and safety performance for the Gemini 3 Flash release with long-context support. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Flash-Model-Card.pdf | 2025/google/2025-12_gemini-3-flash.pdf |
| 2025-12 | StepFun | Step-DeepResearch | Autonomous deep-research agent; addresses limitations of academic multi-hop search benchmarks like BrowseComp by targeting real-world long-horizon research tasks with LLM-driven planning. | https://arxiv.org/pdf/2512.20491 | 2025/stepfun/2025-12_step-deepresearch.pdf |
| 2025-12 | Zhipu AI | GLM-4.7 | This reduces the time developers spend on style “fine-tuning.” GLM-4.7 delivers significant upgrades in layout and aesthetics for office creation Multimodal Interaction and Real-Time Application Development In scenarios requiring cameras, real-time input, and interactive controls, GLM-4.7 demonstrates superior system-level comprehension | https://docs.z.ai/guides/llm/glm-4.7 | 2025/zhipu/2025-12_glm-4.7.pdf |
| 2025-12 | MiniMax | MiniMax M2.1 | 2025.12.23 MiniMax M2.1: Significantly Enhanced Multi-Language Programming, Built for Real-World Complex Tasks Access API Coding Plan Try Agent Now MiniMax has been continuously transforming itself in a more AI-native way Today we are releasing updates to the model component, namely MiniMax M2.1, hoping to help more enterprises and individuals find more AI- native ways of working (and living) sooner | https://www.minimax.io/news/minimax-m21 | 2025/minimax/2025-12_minimax-m2.1.pdf |
| 2025-12 | Meituan | LongCat-Image | We are releasing not only multiple model versions for text-to-image and image editing, including checkpoints after mid-training and post-training stages, but also the entire toolchain of training procedure Beyond generation, LongCat-Image also excels in image editing, achieving SOTA results on standard benchmarks with superior editing consistency compared to other open-source works | https://arxiv.org/pdf/2512.07584 | 2025/meituan/2025-12_longcat-image.pdf |
| 2025-11 | Google | Gemini 3 Pro | Model card for Gemini 3 Pro covering complex reasoning and agentic workflow capabilities; includes known limitations, mitigation approaches, and safety performance documentation. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf | 2025/google/2025-11_gemini-3-pro.pdf |
| 2025-11 | xAI | Grok 4.1 | Iterative update to Grok 4 model card with continued safety evaluation coverage. | https://docs.x.ai/docs/release-notes | 2025/xai/2025-11_grok-4.1.pdf |
| 2025-11 | Alibaba | Qwen3-VL | Most capable vision-language model in the Qwen series; natively supports interleaved contexts up to 256K tokens, seamlessly integrating text, images, and video for multimodal reasoning. | https://arxiv.org/pdf/2511.21631 | 2025/alibaba_qwen/2025-11_qwen3-vl.pdf |
| 2025-10 | Meituan | LongCat-Flash-Omni | Open-source omni-modal 560B model (27B activated) optimized for low-latency real-time audio-visual interaction; uses curriculum-inspired progressive multimodal training with modality-decoupled parallelism sustaining over 90% of text-only training throughput. | https://arxiv.org/pdf/2511.00279 | 2025/meituan/2025-10_longcat-flash-omni.pdf |
| 2025-10 | MiniMax | MiniMax M2.0 | Compact MoE model (230B total / 10B active) built for elite coding and agentic workflows; ranks #1 among open-source models on Artificial Analysis composite score with strong tool-use performance. | https://www.minimax.io/news/minimax-m2 | 2025/minimax/2025-10_minimax-m2.0.pdf |
| 2025-10 | MiniMax | MiniMax M2 | 2025.10.27 MiniMax M2 & Agent: Ingenious in Sim plicity Access API Coding Plan Try Agent Now From Day 1 of our founding, we have been committed to the vision of " | https://www.minimax.io/news/minimax-m2 | 2025/minimax/2025-10_minimax-m2.pdf |
| 2025-10 | Meituan | LongCat-Video | Toward this end, we introduce LongCat-Video, a foundational video generation model with 13.6B parameters, delivering strong performance across multiple video generation tasks In this report, we introduce LongCat-Video, a foundational video generation model with 13.6B parameters that delivers strong performance across general video generation tasks, particularly excelling in efficient, high-quality long video generation | https://arxiv.org/pdf/2510.22200 | 2025/meituan/2025-10_longcat-video.pdf |
| 2025-09 | xAI | Grok 4 Fast | Low-latency inference variant of Grok 4 with safety evaluation coverage. | https://docs.x.ai/docs/release-notes | 2025/xai/2025-09_grok-4-fast.pdf |
| 2025-09 | DeepSeek | DeepSeek V3.1-Terminus | Engineering iteration of V3 (MoE 671B/37B); adopts Multi-head Latent Attention (MLA) and DeepSeekMoE architectures for efficient inference and cost-effective training. | https://arxiv.org/pdf/2412.19437 | 2025/deepseek/2025-09_deepseek-v3.1-terminus.pdf |
| 2025-09 | Baichuan Intelligence | Baichuan-M2 | Medical LLM addressing the gap between static benchmark performance and real-world clinical conversational reasoning; features a verification system for reliable healthcare applications. | https://arxiv.org/pdf/2509.02208 | 2025/baichuan/2025-09_baichuan-m2.pdf |
| 2025-09 | Meituan | LongCat-Flash | 560B MoE language model designed for computational efficiency and agentic capabilities; introduces Zero-computation Experts and novel routing for scalable inference. | https://arxiv.org/pdf/2509.01322 | 2025/meituan/2025-09_longcat-flash.pdf |
| 2025-09 | Meituan | LongCat-Flash-Thinking | Efficient 560B MoE reasoning model built on LongCat-Flash; cultivated through long CoT data cold-start and curriculum RL for formal and agentic reasoning. | https://arxiv.org/pdf/2509.18883 | 2025/meituan/2025-09_longcat-flash-thinking.pdf |
| 2025-09 | Alibaba | Qwen3-Omni | We present Qwen3-Omni, a single multimodal model that for the first time maintains state-of-the-art performance across text, image, audio, and video without any degra- dation relative to single-modal counterparts Based on these features, Qwen3-Omni supports a wide range of tasks, including but not limited to voice dialogue, video dialogue, and video reasoning | https://arxiv.org/pdf/2509.17765 | 2025/alibaba_qwen/2025-09_qwen3-omni.pdf |
| 2025-08 | Zhipu AI | GLM-4.5 | Open-source MoE LLM (355B total / 32B active) with hybrid reasoning supporting both thinking and direct response modes; trained on 23T tokens with comprehensive alignment. | https://arxiv.org/pdf/2508.06471 | 2025/zhipu/2025-08_glm-4.5.pdf |
| 2025-08 | OpenAI | GPT-5 | Unified system card covering multi-model routing architecture and comprehensive safety evaluations across the GPT-5 model family including reasoning and tool-use capabilities. | https://cdn.openai.com/gpt-5-system-card.pdf | 2025/openai/2025-08_gpt-5.pdf |
| 2025-08 | OpenAI | gpt-oss-120b/20b | Apache 2.0 open-weight MoE models (120B and 20B); model card covers architecture, quantization, and post-training for reasoning and tool use. | https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf | 2025/openai/2025-08_gpt-oss-120b-20b.pdf |
| 2025-08 | Quark (Alibaba) | QuarkMed | Medical foundation model trained on 1T healthcare tokens with verifiable RL pipeline; technical report covers clinical reasoning, safety, and multi-task medical benchmarks. | https://arxiv.org/pdf/2508.11894 | 2025/quark/2025-08_quarkmed.pdf |
| 2025-08 | xAI | Grok 4 | High-capability reasoning and tool-use model card with 256K context and comprehensive safety evaluation. | https://docs.x.ai/docs/release-notes | 2025/xai/2025-08_grok-4.pdf |
| 2025-08 | Google | Gemma 3 270M | Gemma 3 270M is its low power consumption For example, check out this Bedtime Story Generator web app : Link to Youtube Video (visible only when JS is disabled) Gemma 3 270M used to power a Bedtime Story Generator web app using Transformers.js | https://developers.googleblog.com/en/introducing-gemma-3-270m/ | 2025/google/2025-08_gemma-3-270m.pdf |
| 2025-08 | Alibaba | Qwen-Image | We present Qwen-Image, an image generation foundation model in the Qwen series that achieves significant advances in complex text rendering and precise image editing As a result, Qwen-Image not only performs exceptionally well in alphabetic languages such as English, but also achieves remarkable progress on more challenging logographic languages like Chinese | https://arxiv.org/pdf/2508.02324 | 2025/alibaba_qwen/2025-08_qwen-image.pdf |
| 2025-07 | Moonshot AI | Kimi K2.0 | MoE LLM with 1T total / 32B active parameters; proposes MuonClip optimizer with QK-clip technique to address training instability while enabling efficient large-scale agentic training. | https://arxiv.org/pdf/2507.20534 | 2025/moonshot/2025-07_kimi-k2.0.pdf |
| 2025-07 | Google | Gemini 2.5 Pro | Native multimodal MoE Transformer model card with 1M context; covers known limitations, mitigation approaches, and safety performance for the Gemini 2.5 Pro release. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Pro-Model-Card.pdf | 2025/google/2025-07_gemini-2.5-pro.pdf |
| 2025-07 | Google | Gemini 2.5 Flash | High-efficiency reasoning model card with 1M context and native audio/image capabilities; balances long-context performance with low-latency inference. | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Flash-Model-Card.pdf | 2025/google/2025-07_gemini-2.5-flash.pdf |
| 2025-06 | Anthropic | Claude Opus 4.5 | System card covering frontier capabilities in software engineering, tool use, and computer use; details a wide range of pre-deployment safety evaluations. | https://arxiv.org/pdf/2508.06600 | 2025/anthropic/2025-06_claude-opus-4.5.pdf |
| 2025-06 | Anthropic | Claude Sonnet 4.5 | Hybrid reasoning LLM system card with strengths in coding, agentic tasks, and computer use; details extensive evaluations for safety and alignment. | https://arxiv.org/pdf/2407.01489 | 2025/anthropic/2025-06_claude-sonnet-4.5.pdf |
| 2025-06 | Baidu | ERNIE 4.5 | Family of 10 large-scale foundation models including heterogeneous MoE variants (424B total / 47B active) and dense models; covers multimodal understanding and generation with industrial-scale training. | https://yiyan.baidu.com/blog/publication/ERNIE_Technical_Report.pdf | 2025/baidu/2025-06_ernie-4.5.pdf |
| 2025-06 | Google | Gemma 3N | They are capable of multimodal input, handling text, image, video, and audio input, and generating text outputs, with open weights for pre-trained and instruction-tuned variants For more information on Gemma 3n's efficient parameter management technology, see the Gemma 3n page | https://ai.google.dev/gemma/docs/gemma-3n/model_card | 2025/google/2025-06_gemma-3n.pdf |
| 2025-05 | Alibaba | Qwen3 | Latest Qwen LLM series with unified thinking framework supporting both thinking and non-thinking modes; designed for improved performance, efficiency, and multilingual capabilities. | https://raw.githubusercontent.com/QwenLM/Qwen3/main/Qwen3_Technical_Report.pdf | 2025/alibaba_qwen/2025-05_qwen3.pdf |
| 2025-05 | Tencent | Yuanbao (Hunyuan-TurboS) | Novel large hybrid Transformer-Mamba MoE model synergistically combining Mamba's long-sequence efficiency with Transformer's contextual understanding and adaptive CoT reasoning. | https://arxiv.org/pdf/2505.15431 | 2025/tencent/2025-05_yuanbao-hunyuan-turbos.pdf |
| 2025-05 | ByteDance | Seed1.5-VL | Vision-language foundation model (MoE 20B active / 532M vision encoder) designed for general-purpose multimodal understanding and reasoning with enhanced visual capabilities. | https://arxiv.org/pdf/2505.07062 | 2025/bytedance/2025-05_seed1.5-vl.pdf |
| 2025-05 | Anthropic | Claude Opus 4 / Sonnet 4 | System card introducing two hybrid reasoning LLMs; covers pre-deployment safety tests per Responsible Scaling Policy and comprehensive alignment evaluations. | https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf | 2025/anthropic/2025-05_claude-opus-4-sonnet-4.pdf |
| 2025-04 | OpenAI | o3 / o4-mini | Reasoning models combining state-of-the-art reasoning with full tool capabilities — web browsing, Python, image analysis, image generation, canvas, automations, file search, and memory. | https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf | 2025/openai/2025-04_o3-o4-mini.pdf |
| 2025-04 | Meta | Llama 4 Scout/Maverick | First natively multimodal models in the Llama 4 herd; Scout features 10M token context with MoE architecture, Maverick optimized for quality and speed, both distilled from Llama 4 Behemoth. | https://ai.meta.com/blog/llama-4-multimodal-intelligence/ | 2025/meta/2025-04_llama-4-scout-maverick.pdf |
| 2025-04 | ByteDance | Seed1.5-Thinking | RL-driven reasoning model (MoE 200B/20B active) achieving 86.7 on AIME 2024, 55.0 on Codeforces, and 77.3 on GPQA, demonstrating excellent reasoning through thinking before responding. | https://arxiv.org/pdf/2504.13914 | 2025/bytedance/2025-04_seed1.5-thinking.pdf |
| 2025-03 | Google | Gemma 3 | Open multimodal model family (1B–27B) introducing vision understanding, wider language coverage, and improved deployment efficiency for the Gemma series. | https://arxiv.org/pdf/2503.19786 | 2025/google/2025-03_gemma-3.pdf |
| 2025-03 | Alibaba | Qwen2.5-Omni | In this report, we present Qwen2.5-Omni, an end-to-end multimodal model designed to perceive diverse modalities, including text, images, audio, and video, while simultane- ously generating text and natural speech responses in a streaming manner Figure 1: Qwen2.5-Omni is a unified end-to-end model capable of processing multiple modalities, such as text, audio, image and video, and generating real-time text or speech response | https://github.com/QwenLM/Qwen2.5-Omni/raw/main/assets/Qwen2.5_Omni.pdf | 2025/alibaba_qwen/2025-03_qwen2.5-omni.pdf |
| 2025-02 | Google | Gemma 2 | The MoE Architecture (26B A4B): The 26B is a Mixture of Experts model This is why its baseline memory requirement is much closer to a dense 26B model than a 4B model | https://storage.googleapis.com/deepmind-media/gemma/gemma-2-report.pdf | 2025/google/2025-02_gemma-2.pdf |
| 2025-01 | DeepSeek | DeepSeek R1 | Pioneering pure RL approach to eliciting reasoning capabilities in LLMs; open-sources distillation recipes demonstrating that strong reasoning can emerge without supervised fine-tuning on CoT data. | https://arxiv.org/pdf/2501.12948 | 2025/deepseek/2025-01_deepseek-r1.pdf |
| 2025-01 | DeepSeek | DeepSeek V3 | Strong MoE language model (671B total / 37B active) adopting Multi-head Latent Attention (MLA) and DeepSeekMoE architectures for efficient inference and cost-effective training. | https://arxiv.org/pdf/2412.19437 | 2025/deepseek/2025-01_deepseek-v3.pdf |

</details>


## Star History

<a href="https://star-history.com/#joe1chief/awesome-llm-tech-reports&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=joe1chief/awesome-llm-tech-reports&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=joe1chief/awesome-llm-tech-reports&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=joe1chief/awesome-llm-tech-reports&type=Date" />
 </picture>
</a>
