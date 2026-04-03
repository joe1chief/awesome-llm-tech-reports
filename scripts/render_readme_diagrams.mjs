#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const DEFAULT_GENERATED_DIR = path.join(ROOT, "scripts", "generated");
const DEFAULT_ASSETS_DIR = path.join(ROOT, "assets", "diagrams");

function parseArgs(argv) {
  const out = {
    generatedDir: DEFAULT_GENERATED_DIR,
    assetsDir: DEFAULT_ASSETS_DIR,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--generated-dir") {
      out.generatedDir = argv[i + 1];
      i += 1;
    } else if (arg === "--assets-dir") {
      out.assetsDir = argv[i + 1];
      i += 1;
    }
  }
  return out;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function scribbleLine(x1, y1, x2, y2, color = "#1f2937", width = 2) {
  return [
    `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" stroke-linecap="round" />`,
    `<line x1="${x1 + 1.5}" y1="${y1 + 1.2}" x2="${x2 - 1.2}" y2="${y2 + 0.8}" stroke="${color}" stroke-width="${Math.max(
      1,
      width - 0.6,
    )}" stroke-linecap="round" opacity="0.75" />`,
  ].join("");
}

function scribbleRect(x, y, width, height, stroke, fill) {
  return `
    <rect x="${x}" y="${y}" width="${width}" height="${height}" rx="18" ry="18" fill="${fill}" stroke="${stroke}" stroke-width="2.4" />
    <rect x="${x + 1.5}" y="${y + 1.2}" width="${width - 2.6}" height="${height - 2.2}" rx="18" ry="18" fill="none" stroke="${stroke}" stroke-width="1.3" opacity="0.75" />
  `;
}

function scribbleEllipse(cx, cy, rx, ry, stroke, fill) {
  return `
    <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${fill}" stroke="${stroke}" stroke-width="2.4" />
    <ellipse cx="${cx + 1.1}" cy="${cy + 0.8}" rx="${Math.max(8, rx - 1.5)}" ry="${Math.max(8, ry - 1.1)}" fill="none" stroke="${stroke}" stroke-width="1.3" opacity="0.75" />
  `;
}

function textBlock(x, y, lines, opts = {}) {
  const {
    size = 20,
    weight = 500,
    color = "#111827",
    anchor = "start",
    lineHeight = size + 6,
  } = opts;
  const tspans = lines
    .map((line, idx) => `<tspan x="${x}" dy="${idx === 0 ? 0 : lineHeight}">${escapeXml(line)}</tspan>`)
    .join("");
  return `<text x="${x}" y="${y}" fill="${color}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" font-family="Virgil, Segoe Print, Comic Sans MS, cursive">${tspans}</text>`;
}

function tokenizeLabel(value) {
  return String(value || "")
    .trim()
    .split(/(?<=[-/])|\s+/)
    .filter(Boolean);
}

function wrapLabel(value, maxChars = 16) {
  const tokens = tokenizeLabel(value);
  if (!tokens.length) return [String(value || "").trim()];
  const lines = [];
  let current = "";
  for (const token of tokens) {
    const separator = current && !/[/-]$/.test(current) ? " " : "";
    const next = `${current}${separator}${token}`;
    if (next.length <= maxChars) {
      current = next;
      continue;
    }
    if (current) {
      lines.push(current.trim());
      current = "";
    }
    if (token.length <= maxChars) {
      current = token;
      continue;
    }
    for (let start = 0; start < token.length; start += maxChars) {
      lines.push(token.slice(start, start + maxChars));
    }
  }
  if (current) lines.push(current.trim());
  return lines.length ? lines : [String(value || "").trim()];
}

function monthlyColors(count) {
  if (count <= 1) return { fill: "#f8fafc", stroke: "#94a3b8" };
  if (count <= 2) return { fill: "#eef2ff", stroke: "#818cf8" };
  if (count <= 4) return { fill: "#dbeafe", stroke: "#2563eb" };
  if (count <= 8) return { fill: "#bfdbfe", stroke: "#1d4ed8" };
  return { fill: "#c7d2fe", stroke: "#312e81" };
}

function renderMonthlyDensitySvg(data) {
  const months = data.months || [];
  const width = Math.max(900, 180 + months.length * 140);
  const height = 420;
  const baseY = 300;
  const gap = months.length > 1 ? (width - 160) / (months.length - 1) : 0;
  const circles = months
    .map((item, idx) => {
      const x = 80 + idx * gap;
      const radius = 20 + item.count * 4;
      const { fill, stroke } = monthlyColors(item.count);
      const monthLabel = item.month.slice(2);
      return `
        <g data-month="${item.month}" data-count="${item.count}">
          ${scribbleEllipse(x, baseY - 10, radius, radius, stroke, fill)}
          ${textBlock(x, baseY - 14, [monthLabel, `R${String(item.count).padStart(2, "0")}`], {
            size: 16,
            weight: 700,
            anchor: "middle",
            lineHeight: 18,
          })}
        </g>
      `;
    })
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title desc">
  <title id="title">Monthly Density Snapshot</title>
  <desc id="desc">Bubble size follows monthly release count.</desc>
  <rect width="${width}" height="${height}" fill="#fffdf8" />
  ${scribbleLine(60, baseY + 70, width - 50, baseY + 70, "#374151", 2.5)}
  ${textBlock(70, 60, ["Monthly Density Snapshot"], { size: 30, weight: 700 })}
  ${textBlock(70, 95, ["Bubble size follows the release count from the model index table."], {
    size: 16,
    color: "#4b5563",
  })}
  ${circles}
</svg>`;
}

function campPalette(camp) {
  const table = {
    openai: { fill: "#e8f2ff", stroke: "#2f6feb" },
    anthropic: { fill: "#fff4e8", stroke: "#b15f00" },
    google: { fill: "#e9fbe9", stroke: "#1a7f37" },
    china: { fill: "#fff0f6", stroke: "#bf3989" },
    other: { fill: "#f3f4f6", stroke: "#6b7280" },
  };
  return table[camp] || table.other;
}

function renderReleaseTimelineSvg(data) {
  const months = data.months || [];
  const lanes = data.lanes || [];
  const width = Math.max(1520, 260 + months.length * 150);
  const height = 220 + lanes.length * 160;
  const timelineY = 110;
  const startX = 140;
  const endX = width - 140;
  const gap = months.length > 1 ? (endX - startX) / (months.length - 1) : 0;
  const monthX = new Map(months.map((month, idx) => [month, startX + idx * gap]));
  const monthBoxWidth = 96;
  const cardWidth = Math.max(146, Math.min(170, gap - 16));

  const monthNodes = months
    .map((month) => {
      const x = monthX.get(month);
      return `
        ${scribbleRect(x - monthBoxWidth / 2, timelineY - 26, monthBoxWidth, 42, "#374151", "#ffffff")}
        ${textBlock(x, timelineY + 2, [month], { size: 15, weight: 700, anchor: "middle" })}
      `;
    })
    .join("\n");

  const laneBlocks = lanes
    .map((lane, idx) => {
      const top = 180 + idx * 150;
      const palette = campPalette(lane.camp);
      const cards = (lane.entries || [])
        .map((entry) => {
          const x = (monthX.get(entry.month) || startX) - cardWidth / 2;
          const modelLines = (entry.models || []).flatMap((model) =>
            wrapLabel(
              (entry.highlighted_models || []).includes(model) ? `★ ${model}` : model,
              16,
            ),
          );
          const cardHeight = 32 + modelLines.length * 18;
          return `
            ${scribbleLine(x + cardWidth / 2, timelineY + 18, x + cardWidth / 2, top + 12, "#9ca3af", 1.5)}
            ${scribbleRect(x, top + 12, cardWidth, cardHeight, palette.stroke, palette.fill)}
            ${textBlock(x + 12, top + 34, modelLines, {
              size: 14,
              weight: 600,
              lineHeight: 18,
            })}
          `;
        })
        .join("\n");
      return `
        ${textBlock(36, top + 50, [lane.label], { size: 18, weight: 700 })}
        ${cards}
      `;
    })
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title desc">
  <title id="title">Release Timeline</title>
  <desc id="desc">Release timeline grouped by ecosystem camp and organization lane.</desc>
  <rect width="${width}" height="${height}" fill="#fffdf8" />
  ${textBlock(70, 56, ["Release Timeline"], { size: 32, weight: 700 })}
  ${textBlock(70, 88, ["Camp colors stay aligned with the README legend. ★ marks impact releases."], {
    size: 16,
    color: "#4b5563",
  })}
  ${scribbleLine(startX, timelineY, endX, timelineY, "#1f2937", 3)}
  ${monthNodes}
  ${laneBlocks}
</svg>`;
}

function createBaseScene() {
  return {
    type: "excalidraw",
    version: 2,
    source: "https://excalidraw.com",
    elements: [],
    appState: {
      viewBackgroundColor: "#fffdf8",
      gridSize: null,
    },
    files: {},
  };
}

function pushElement(scene, element) {
  scene.elements.push({
    angle: 0,
    backgroundColor: "transparent",
    boundElements: null,
    fillStyle: "hachure",
    groupIds: [],
    height: element.height || 0,
    id: `el_${scene.elements.length + 1}`,
    isDeleted: false,
    link: null,
    locked: false,
    opacity: 100,
    roughness: 1,
    roundness: null,
    seed: 1000 + scene.elements.length,
    strokeColor: "#1f2937",
    strokeStyle: "solid",
    strokeWidth: 2,
    updated: 1,
    version: 1,
    versionNonce: 1 + scene.elements.length,
    width: element.width || 0,
    x: element.x || 0,
    y: element.y || 0,
    ...element,
  });
}

function buildMonthlyScene(data) {
  const scene = createBaseScene();
  pushElement(scene, { type: "text", x: 60, y: 40, text: "Monthly Density Snapshot", fontSize: 28, width: 360, height: 32, fontFamily: 4, textAlign: "left", verticalAlign: "top", originalText: "Monthly Density Snapshot", lineHeight: 1.25 });
  (data.months || []).forEach((item, idx) => {
    const x = 80 + idx * 140;
    const radius = 20 + item.count * 4;
    pushElement(scene, { type: "ellipse", x: x - radius, y: 200 - radius, width: radius * 2, height: radius * 2, backgroundColor: monthlyColors(item.count).fill, strokeColor: monthlyColors(item.count).stroke });
    pushElement(scene, { type: "text", x: x - 35, y: 192, text: `${item.month.slice(2)}\nR${String(item.count).padStart(2, "0")}`, fontSize: 16, width: 72, height: 40, fontFamily: 4, textAlign: "center", verticalAlign: "middle", originalText: `${item.month.slice(2)}\nR${String(item.count).padStart(2, "0")}`, lineHeight: 1.2 });
  });
  return scene;
}

function buildTimelineScene(data) {
  const scene = createBaseScene();
  pushElement(scene, { type: "text", x: 60, y: 32, text: "Release Timeline", fontSize: 30, width: 280, height: 36, fontFamily: 4, textAlign: "left", verticalAlign: "top", originalText: "Release Timeline", lineHeight: 1.25 });
  const months = data.months || [];
  const lanes = data.lanes || [];
  months.forEach((month, idx) => {
    const x = 120 + idx * 120;
    pushElement(scene, { type: "rectangle", x: x - 40, y: 92, width: 80, height: 42, backgroundColor: "#ffffff", strokeColor: "#374151" });
    pushElement(scene, { type: "text", x: x - 28, y: 105, text: month, fontSize: 14, width: 60, height: 18, fontFamily: 4, textAlign: "center", verticalAlign: "middle", originalText: month, lineHeight: 1.2 });
  });
  lanes.forEach((lane, laneIdx) => {
    const top = 180 + laneIdx * 150;
    pushElement(scene, { type: "text", x: 24, y: top + 20, text: lane.label, fontSize: 18, width: 120, height: 22, fontFamily: 4, textAlign: "left", verticalAlign: "top", originalText: lane.label, lineHeight: 1.2 });
    (lane.entries || []).forEach((entry) => {
      const monthIdx = months.indexOf(entry.month);
      const x = 120 + Math.max(0, monthIdx) * 120 - 60;
      const models = (entry.models || []).map((model) =>
        (entry.highlighted_models || []).includes(model) ? `★ ${model}` : model,
      );
      pushElement(scene, { type: "rectangle", x, y: top + 8, width: 120, height: 54 + models.length * 18, backgroundColor: campPalette(lane.camp).fill, strokeColor: campPalette(lane.camp).stroke });
      pushElement(scene, { type: "text", x: x + 10, y: top + 24, text: models.join("\n"), fontSize: 14, width: 98, height: 20 + models.length * 18, fontFamily: 4, textAlign: "left", verticalAlign: "top", originalText: models.join("\n"), lineHeight: 1.2 });
    });
  });
  return scene;
}

function writeOutputs({ generatedDir, assetsDir }) {
  ensureDir(assetsDir);
  const monthlyData = readJson(path.join(generatedDir, "monthly_density.json"));
  const timelineData = readJson(path.join(generatedDir, "release_timeline.json"));

  fs.writeFileSync(path.join(assetsDir, "monthly-density.svg"), renderMonthlyDensitySvg(monthlyData));
  fs.writeFileSync(path.join(assetsDir, "release-timeline.svg"), renderReleaseTimelineSvg(timelineData));
}

const args = parseArgs(process.argv.slice(2));
writeOutputs(args);
console.log(`assets=${args.assetsDir}`);
