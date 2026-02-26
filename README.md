# Awesome LLM Tech Reports

> 持续维护的 2025-01 至今 LLM/多模态技术报告归档仓库（季度更新）。

[![Update Cadence](https://img.shields.io/badge/update-quarterly-blue)](#更新策略) [![Coverage](https://img.shields.io/badge/coverage-2025--2026-success)](#模型总表)

## 项目亮点

- **高密度索引**：README 直接给出发布时间、机构、模型、技术亮点、官方链接、本地文件位置。
- **本地可复现**：已下载的 PDF 按 `年份/公司` 分层保存，便于检索与后续增量更新。
- **严格来源**：仅收录官方技术报告/论文/官方博客链接，不使用非官方镜像。

## 更新策略

- **更新频率**：每 3 个月更新一次（季度更新）。
- **收录范围**：重点覆盖国内外主流 LLM 与多模态模型，以及关键垂直模型。
- **目录规范**：一级目录为年份，二级目录为公司（示例：`2026/openai/...`）。

## 模型总表

| 发布时间 | 开发机构 | 模型名称 | 核心特性 | 官方链接 | 本地文件位置 |
| --- | --- | --- | --- | --- | --- |
| 2026-02 | 智谱AI | GLM-5 | MoE 744B/40B，异步强化学习与 Agent 工程能力。 | https://arxiv.org/pdf/2602.15763 | 2026/zhipu/2026-02_glm-5.pdf |
| 2026-02 | 阶跃星辰 | Step-3.5-Flash | MoE 196B/11B，混合注意力与多 token 预测。 | https://arxiv.org/pdf/2602.10604 | 2026/stepfun/2026-02_step-3.5-flash.pdf |
| 2026-02 | 百度 | ERNIE 5.0 | 统一自回归多模态，超稀疏 MoE，弹性训练。 | https://arxiv.org/pdf/2602.04705 | 2026/baidu/2026-02_ernie-5.0.pdf |
| 2026-02 | 百川智能 | Baichuan-M3 | 面向临床问诊的主动信息采集与长程推理。 | https://arxiv.org/pdf/2602.06570 | 2026/baichuan/2026-02_baichuan-m3.pdf |
| 2026-02 | 字节跳动 | MedXIAOHE | 医疗多模态基础模型，实体感知预训练与工具增强。 | https://arxiv.org/pdf/2602.12705 | 2026/bytedance/2026-02_medxiaohe.pdf |
| 2026-02 | OpenAI | GPT-5.3-Codex | 高能力 agentic 编码模型，面向长程工具任务。 | https://cdn.openai.com/pdf/8df7697b-c1b2-4222-be00-1fd3298f351d/codex_system_card.pdf | 2026/openai/2026-02_gpt-5.3-codex.pdf |
| 2026-02 | Anthropic | Claude Opus 4.6 | 系统卡覆盖高能力编码、长上下文与对齐评估。 | https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf | 2026/anthropic/2026-02_claude-opus-4.6.pdf |
| 2026-02 | 字节跳动 | Seed 2.0 | 面向真实复杂任务与企业工作流的 Seed 2.0 系列。 | https://lf3-static.bytednsdoc.com/obj/eden-cn/lapzild-tss/ljhwZthlaukjlkulzlp/seed2/0214/Seed2.0%20Model%20Card.pdf | 2026/bytedance/2026-02_seed-2.0.pdf |
| 2026-02 | 阿里巴巴 | Qwen 3.5 | 新一代通用模型系列，官方仅公开博客页。 | https://qwen.ai/blog?id=qwen3.5 | 2026/alibaba_qwen/2026-02_qwen-3.5.pdf |
| 2026-02 | MiniMax | MiniMax M2.5 | RL 大规模训练，强化编码/搜索/工具调用效率。 | https://www.minimax.io/news/minimax-m25 | 2026/minimax/2026-02_minimax-m2.5.pdf |
| 2026-02 | 月之暗面 | Kimi K2.5 | 多模态 1T MoE，Agent Swarm 并行子任务。 | https://github.com/MoonshotAI/Kimi-K2.5/raw/master/tech_report.pdf | 2026/moonshot/2026-02_kimi-k2.5.pdf |
| 2026-02 | inclusionAI | Ling 2.5 | 1T/63B 混合线性注意力，强调工具调用与效率。 | https://github.com/inclusionAI/Ling-V2.5 | 2026/inclusionai/2026-02_ling-2.5.pdf |
| 2025-12 | OpenAI | GPT-5.2 | 系统卡模型，强化推理与可靠性能力。 | https://cdn.openai.com/pdf/3a4153c8-c748-4b71-8e31-aecbde944f8d/oai_5_2_system-card.pdf | 2025/openai/2025-12_gpt-5.2.pdf |
| 2025-12 | DeepSeek | DeepSeek V3.2 | DSA 稀疏注意力与可扩展 RL 框架。 | https://arxiv.org/pdf/2512.02556 | 2025/deepseek/2025-12_deepseek-v3.2.pdf |
| 2025-12 | Google | Gemini 3 Flash | 高效率 MoE 多模态模型，支持长上下文。 | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Flash-Model-Card.pdf | 2025/google/2025-12_gemini-3-flash.pdf |
| 2025-12 | 阶跃星辰 | Step-DeepResearch | 面向深度研究任务的长流程 Agent 评测能力。 | https://arxiv.org/pdf/2512.20491 | 2025/stepfun/2025-12_step-deepresearch.pdf |
| 2025-11 | Google | Gemini 3 Pro | 强调复杂推理与 agentic 工作流。 | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf | 2025/google/2025-11_gemini-3-pro.pdf |
| 2025-11 | xAI | Grok 4.1 | Grok 4 系列迭代版，持续强化安全评测。 | https://data.x.ai/2025-11-17-grok-4-1-model-card.pdf | 下载失败 |
| 2025-11 | 阿里巴巴 | Qwen3-VL | Qwen 视觉语言技术报告，聚焦多模态推理。 | https://arxiv.org/pdf/2511.21631 | 2025/alibaba_qwen/2025-11_qwen3-vl.pdf |
| 2025-10 | MiniMax | MiniMax M2.0 | MoE 架构与 256K 上下文，开源仓库公开。 | https://github.com/MiniMax-AI/MiniMax-M2 | 2025/minimax/2025-10_minimax-m2.0.pdf |
| 2025-09 | xAI | Grok 4 Fast | 低时延推理版 Grok 4，覆盖安全评测。 | https://data.x.ai/2025-09-19-grok-4-fast-model-card.pdf | 下载失败 |
| 2025-09 | DeepSeek | DeepSeek V3.1-Terminus | V3.1 工程迭代版，强化稳定性与 agent 可靠性。 | https://arxiv.org/pdf/2412.19437 | 2025/deepseek/2025-09_deepseek-v3.1-terminus.pdf |
| 2025-09 | 百川智能 | Baichuan-M2 | 医疗验证系统驱动的 32B 医疗模型。 | https://arxiv.org/pdf/2509.02208 | 2025/baichuan/2025-09_baichuan-m2.pdf |
| 2025-09 | 美团 | LongCat-Flash | 560B MoE，零计算专家提升推理效率。 | https://arxiv.org/pdf/2509.01322 | 2025/meituan/2025-09_longcat-flash.pdf |
| 2025-09 | 美团 | LongCat-Flash-Thinking | 在 Flash 基础上强化形式推理与工具推理。 | https://arxiv.org/pdf/2509.18883 | 2025/meituan/2025-09_longcat-flash-thinking.pdf |
| 2025-08 | 智谱AI | GLM-4.5 | ARC 能力导向基础模型，重推理与编码。 | https://arxiv.org/pdf/2508.06471 | 2025/zhipu/2025-08_glm-4.5.pdf |
| 2025-08 | OpenAI | GPT-5 | 统一系统卡，覆盖多模型路由与安全评估。 | https://cdn.openai.com/pdf/8124a3ce-ab78-4f06-96eb-49ea29ffb52f/gpt5-system-card-aug7.pdf | 2025/openai/2025-08_gpt-5.pdf |
| 2025-08 | OpenAI | gpt-oss-120b/20b | Apache 2.0 开源权重，强调工具调用与推理。 | https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf | 2025/openai/2025-08_gpt-oss-120b-20b.pdf |
| 2025-08 | 夸克(阿里) | QuarkMed | 医疗 1T 数据与可验证 RL 流水线。 | https://arxiv.org/pdf/2508.11894 | 2025/quark/2025-08_quarkmed.pdf |
| 2025-07 | 月之暗面 | Kimi K2.0 | 1T MoE，MuonClip 优化器与 agentic 训练。 | https://arxiv.org/pdf/2507.20534 | 2025/moonshot/2025-07_kimi-k2.0.pdf |
| 2025-07 | xAI | Grok 4 | 高能力推理与工具使用，模型卡公开。 | https://data.x.ai/2025-08-20-grok-4-model-card.pdf | 下载失败 |
| 2025-07 | Google | Gemini 2.5 Pro | 原生多模态 MoE Transformer，1M 上下文。 | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Pro-Model-Card.pdf | 2025/google/2025-07_gemini-2.5-pro.pdf |
| 2025-07 | Google | Gemini 2.5 Flash | 高效推理模型，长上下文与低时延平衡。 | https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Flash-Model-Card.pdf | 2025/google/2025-07_gemini-2.5-flash.pdf |
| 2025-06 | Anthropic | Claude Opus 4.5 | 高能力系统卡版本，覆盖多项安全评估。 | https://assets.anthropic.com/m/64823ba7485345a7/Claude-Opus-4-5-System-Card.pdf | 2025/anthropic/2025-06_claude-opus-4.5.pdf |
| 2025-06 | Anthropic | Claude Sonnet 4.5 | Sonnet 4.5 系统卡，推理与工具能力增强。 | https://assets.anthropic.com/m/12f214efcc2f457a/original/Claude-Sonnet-4-5-System-Card.pdf | 2025/anthropic/2025-06_claude-sonnet-4.5.pdf |
| 2025-06 | 百度 | ERNIE 4.5 | 异构 MoE 多模态家族，工业级训练与部署。 | https://yiyan.baidu.com/blog/publication/ERNIE_Technical_Report.pdf | 2025/baidu/2025-06_ernie-4.5.pdf |
| 2025-05 | 阿里巴巴 | Qwen3 | 统一思考框架，覆盖思考/非思考双模式。 | https://arxiv.org/pdf/2505.09388 | 2025/alibaba_qwen/2025-05_qwen3.pdf |
| 2025-05 | 腾讯 | Yuanbao (Hunyuan-TurboS) | Mamba-Transformer 混合 MoE 与自适应 CoT。 | https://arxiv.org/pdf/2505.15431 | 2025/tencent/2025-05_yuanbao-hunyuan-turbos.pdf |
| 2025-05 | 字节跳动 | Seed1.5-VL | 20B 激活 MoE 多模态模型，视觉推理增强。 | https://arxiv.org/pdf/2505.07062 | 2025/bytedance/2025-05_seed1.5-vl.pdf |
| 2025-05 | Anthropic | Claude Opus 4 / Sonnet 4 | Claude 4 系列系统卡，混合推理能力。 | https://www-cdn.anthropic.com/4263b940cabb546aa0e3283f35b686f4f3b2ff47.pdf | 2025/anthropic/2025-05_claude-opus-4-sonnet-4.pdf |
| 2025-04 | OpenAI | o3 / o4-mini | 推理模型系统卡，覆盖安全与能力评估。 | https://cdn.openai.com/pdf/2221c875-02dc-4789-800b-e7758f3722c1/o3-and-o4-mini-system-card.pdf | 2025/openai/2025-04_o3-o4-mini.pdf |
| 2025-04 | Meta | Llama 4 Scout/Maverick | 原生多模态 MoE；Scout 支持超长上下文。 | https://ai.meta.com/blog/llama-4-multimodal-intelligence/ | 2025/meta/2025-04_llama-4-scout-maverick.pdf |
| 2025-04 | 字节跳动 | Seed1.5-Thinking | 强化学习驱动推理模型，20B 激活/200B 总参数。 | https://arxiv.org/pdf/2504.13914 | 2025/bytedance/2025-04_seed1.5-thinking.pdf |
| 2025-03 | Google | Gemma 3 | 开源多模态模型系列，强调可部署性。 | https://arxiv.org/pdf/2503.19786 | 2025/google/2025-03_gemma-3.pdf |
| 2025-01 | DeepSeek | DeepSeek R1 | 通过纯 RL 激发推理能力并开源蒸馏路线。 | https://arxiv.org/pdf/2501.12948 | 2025/deepseek/2025-01_deepseek-r1.pdf |
| 2025-01 | DeepSeek | DeepSeek V3 | MoE 671B/37B，MLA 与高效训练实践。 | https://arxiv.org/pdf/2412.19437 | 2025/deepseek/2025-01_deepseek-v3.pdf |
