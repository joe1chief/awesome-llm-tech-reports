#!/usr/bin/env python3
"""
Awesome LLM Technical Reports - README Parser & Data Generator
Parses README.md tables and outputs enriched, structured JSON data for the web UI.
"""

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
OUTPUT_PATH = REPO_ROOT / "docs" / "data" / "models.json"

CHINA_LABS = {
    "alibaba", "deepseek", "zhipu", "moonshot", "tencent", "bytedance",
    "minimax", "stepfun", "internlm", "meituan", "openbmb", "inclusionai",
    "quark", "baidu", "baichuan"
}

MILESTONE_KEYWORDS = [
    "deepseek-r1", "deepseek-v3", "gpt-5", "gpt-5.5", "gpt-5.4 thinking",
    "claude sonnet 4.5", "claude sonnet 5", "claude opus 4.6", "claude opus 4.7", "claude opus 4.8",
    "gemini 3 pro", "gemini 3.1 pro", "gemini 3.5", "gemini 2.5 pro", "gemini 2.5 deep think",
    "glm-5", "glm-5.2", "qwen3", "qwen3-vl", "qwen3-max", "qwen2.5-vl", "qwen2.5-max",
    "kimi k2", "kimi k2.5", "longcat-2.0", "longcat-flash-thinking", "nemotron 3 super",
    "llama 4", "minicpm-o 4.5", "medgemma 1.5", "medxiaohe"
]


def classify_camp(org: str) -> str:
    org_lower = org.lower()
    if "openai" in org_lower:
        return "OpenAI"
    elif "anthropic" in org_lower:
        return "Anthropic"
    elif "google" in org_lower:
        return "Google"
    elif any(lab in org_lower for lab in CHINA_LABS):
        return "China-based Labs"
    else:
        return "Other Global"


def is_milestone(model_name: str, highlights: str) -> bool:
    name_lower = model_name.lower()
    for kw in MILESTONE_KEYWORDS:
        if kw in name_lower:
            return True
    return False


def extract_tags(model_name: str, highlights: str, link: str) -> list:
    combined = f"{model_name} {highlights} {link}".lower()
    tags = []

    # Reasoning / Thinking
    if any(k in combined for k in ["reasoning", "thinking", "think", "cot", "chain-of-thought", "r1", "prover", "formal", "math-500", "aime"]):
        tags.append("Reasoning / CoT")

    # Agentic & Coding
    if any(k in combined for k in ["agent", "agentic", "coding", "swe-bench", "codex", "tool use", "tool-use", "function-calling", "computer use", "claw"]):
        tags.append("Agent & Coding")

    # Multimodal & Vision
    if any(k in combined for k in ["multimodal", "multi-modal", "vision", "vlm", "image", "omni", "visual", "gui"]):
        tags.append("Vision & Multimodal")

    # Audio & Speech
    if any(k in combined for k in ["audio", "speech", "voice", "tts", "translate", "whisper", "live translate"]):
        tags.append("Audio & Speech")

    # Video Generation & Understanding
    if any(k in combined for k in ["video", "avatar", "motion", "hunyuanvideo"]):
        tags.append("Video")

    # Medical & Science Vertical
    if any(k in combined for k in ["med", "medical", "clinical", "health", "science", "scientific", "quarkmed", "xiaohe", "biology"]):
        tags.append("Medical & Science")

    # MoE Architecture
    if any(k in combined for k in ["moe", "mixture-of-experts", "mixture of experts", "sparse", "active parameter", "activated parameter"]):
        tags.append("MoE")

    # Open Weights / Open Source
    if any(k in combined for k in ["open-source", "open source", "open-weight", "open weight", "apache", "github.com", "huggingface.co", "arxiv.org", "weights"]):
        tags.append("Open Weights")

    # Deduplicate while preserving order
    return list(dict.fromkeys(tags))


def parse_readme(readme_path: Path):
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find table blocks
    table_pattern = re.compile(
        r"\| Release Date \| Organization \| Model \| Core Highlights \(from PDF\) \| Official Link \| Local File \|\s*\n\|(?: --- \|)+\s*\n((?:\|[^\n]+\n)+)",
        re.MULTILINE
    )

    matches = table_pattern.findall(content)
    models = []

    for match in matches:
        lines = match.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) < 6:
                continue

            date, org, model_name, highlights, link, local_file = cells[:6]

            camp = classify_camp(org)
            milestone = is_milestone(model_name, highlights)
            tags = extract_tags(model_name, highlights, link)

            year, month = date.split("-") if "-" in date else (date, "01")

            models.append({
                "id": f"{date}_{re.sub(r'[^a-zA-Z0-9]', '_', model_name.lower())}".strip("_"),
                "date": date,
                "year": int(year),
                "month": int(month),
                "org": org,
                "model": model_name,
                "highlights": highlights,
                "link": link,
                "file": local_file,
                "camp": camp,
                "is_milestone": milestone,
                "tags": tags
            })

    # Sort descending by date, then model name
    models.sort(key=lambda m: (m["date"], m["model"]), reverse=True)

    # Compute overall statistics
    org_counts = {}
    camp_counts = {}
    tag_counts = {}
    month_counts = {}

    for m in models:
        org_counts[m["org"]] = org_counts.get(m["org"], 0) + 1
        camp_counts[m["camp"]] = camp_counts.get(m["camp"], 0) + 1
        month_counts[m["date"]] = month_counts.get(m["date"], 0) + 1
        for t in m["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1

    stats = {
        "total_models": len(models),
        "total_orgs": len(org_counts),
        "milestones_count": sum(1 for m in models if m["is_milestone"]),
        "date_range": {
            "start": min(m["date"] for m in models) if models else "2025-01",
            "end": max(m["date"] for m in models) if models else "2026-07"
        },
        "camp_breakdown": camp_counts,
        "org_breakdown": org_counts,
        "tag_breakdown": tag_counts,
        "monthly_trend": [{"month": k, "count": month_counts[k]} for k in sorted(month_counts.keys())]
    }

    return {
        "metadata": {
            "title": "Awesome LLM Technical Reports",
            "description": "Curated Archive of Frontier LLM, Multimodal & Reasoning Technical Reports (2025-01 to 2026-07)",
            "repo_url": "https://github.com/joe1chief/awesome-llm-tech-reports",
            "pdf_base_url": "https://raw.githubusercontent.com/joe1chief/awesome-llm-tech-reports/main/"
        },
        "stats": stats,
        "models": models
    }


def main():
    print(f"Reading README from: {README_PATH}")
    data = parse_readme(README_PATH)
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Successfully parsed {data['stats']['total_models']} models from {data['stats']['total_orgs']} organizations!")
    print(f"📁 Output saved to: {OUTPUT_PATH}")
    print(f"✨ Milestones detected: {data['stats']['milestones_count']}")
    print(f"🏷️ Top Tags: {list(data['stats']['tag_breakdown'].items())[:5]}")


if __name__ == "__main__":
    main()
