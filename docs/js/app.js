/**
 * Awesome LLM Technical Reports - LMSYS Exact Architecture & Controller
 */

window.App = (function() {
  let dataset = { metadata: {}, stats: {}, models: [] };
  let state = {
    archiveCategory: "all",
    archiveQuery: "",
    currentModel: null
  };

  const LAB_ICONS = {
    "DeepSeek": { bg: "#0284c7", text: "DS" },
    "OpenAI": { bg: "#10b981", text: "OA" },
    "Anthropic": { bg: "#ea580c", text: "AN" },
    "Google": { bg: "#2563eb", text: "GO" },
    "Alibaba": { bg: "#ea580c", text: "QW" },
    "Zhipu AI": { bg: "#9333ea", text: "GLM" },
    "Meituan": { bg: "#ca8a04", text: "LC" },
    "Tencent": { bg: "#1d4ed8", text: "HY" },
    "ByteDance": { bg: "#dc2626", text: "BD" },
    "MiniMax": { bg: "#db2777", text: "MM" },
    "Moonshot AI": { bg: "#4f46e5", text: "KM" },
    "Meta": { bg: "#2563eb", text: "LL" },
    "NVIDIA": { bg: "#65a30d", text: "NV" },
    "Microsoft": { bg: "#0284c7", text: "MS" },
    "StepFun": { bg: "#d97706", text: "ST" },
    "InternLM": { bg: "#0d9488", text: "IN" },
    "OpenBMB": { bg: "#f59e0b", text: "BMB" },
    "InclusionAI (Ant Group)": { bg: "#0284c7", text: "ANT" },
    "Allen AI": { bg: "#475569", text: "AI2" },
    "Hugging Face": { bg: "#d97706", text: "HF" },
    "Snowflake": { bg: "#0284c7", text: "SF" },
    "xAI": { bg: "#0f172a", text: "xAI" },
    "Quark (Alibaba)": { bg: "#ea580c", text: "QK" }
  };

  async function init() {
    setupEventListeners();
    await loadData();
    renderTimeline();
    renderCatalog();
    renderArchiveFilterTabs();
    renderArchiveList();
    renderLeaderboard();
    if (window.ArenaCompare) {
      window.ArenaCompare.init(dataset.models);
    }
  }

  async function loadData() {
    try {
      const res = await fetch("data/models.json");
      if (!res.ok) throw new Error("Failed to load models.json");
      dataset = await res.json();
    } catch (err) {
      console.error("Error loading models:", err);
    }
  }

  function setupEventListeners() {
    const searchInput = document.getElementById("archive-search-input");
    if (searchInput) {
      let timeout = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          state.archiveQuery = e.target.value.trim().toLowerCase();
          renderArchiveList();
        }, 150);
      });
    }

    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeDrawer();
        if (window.ArenaCompare) window.ArenaCompare.closeCompareModal();
      }
    });
  }

  function searchLab(labName) {
    state.archiveQuery = labName.toLowerCase();
    const searchInput = document.getElementById("archive-search-input");
    if (searchInput) searchInput.value = labName;
    renderArchiveList();
  }

  function getPdfUrl(filePath) {
    const base = dataset.metadata?.pdf_base_url || "https://raw.githubusercontent.com/joe1chief/awesome-llm-tech-reports/main/";
    return base + filePath;
  }

  function getLabIcon(org) {
    const info = LAB_ICONS[org] || { bg: "#475569", text: org.slice(0, 2).toUpperCase() };
    return `
      <div style="width:100%;height:100%;background:${info.bg};color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;letter-spacing:-0.02em;font-family:var(--font-inter),sans-serif;">
        ${info.text}
      </div>
    `;
  }

  /* ==========================================================================
     1. Milestone Alternating Timeline (LMSYS exact .timeline, .tl-row)
     ========================================================================== */
  function renderTimeline() {
    const container = document.getElementById("timeline-flow-container");
    if (!container) return;

    // Filter top milestone models across the timeline
    const timelineModels = dataset.models.filter(m => m.is_milestone).slice(0, 16);

    let html = '';
    timelineModels.forEach((m, idx) => {
      const isLeft = idx % 2 === 0;

      const cardHtml = `
        <a class="tl-card" onclick="window.App.openDrawer('${m.id}')">
          <div class="tl-name-row">
            <span class="tl-name">${m.model}</span>
            <span class="tl-graduated">${m.date}</span>
          </div>
          <p class="tl-desc">${m.highlights}</p>
          <div style="display:flex;align-items:center;justify-content:space-between;font-size:13px;color:var(--ink-lighter);margin-top:12px;padding-top:10px;border-top:1px solid var(--border);">
            <span style="font-weight:600;color:var(--ink);">${m.org}</span>
            <span style="color:var(--orange);font-weight:500;">View Spec &rarr;</span>
          </div>
        </a>
      `;

      if (isLeft) {
        html += `
          <div class="tl-row">
            <div class="tl-left">${cardHtml}</div>
            <div class="tl-icon-col">
              <div class="tl-icon">
                ${getLabIcon(m.org)}
              </div>
            </div>
            <div class="tl-right"><div class="tl-card tl-card-empty"></div></div>
          </div>
        `;
      } else {
        html += `
          <div class="tl-row">
            <div class="tl-left"><div class="tl-card tl-card-empty"></div></div>
            <div class="tl-icon-col">
              <div class="tl-icon">
                ${getLabIcon(m.org)}
              </div>
            </div>
            <div class="tl-right">${cardHtml}</div>
          </div>
        `;
      }
    });

    container.innerHTML = html;
  }

  /* ==========================================================================
     2. Categorized Catalog (LMSYS /projects exact .projects-grid, .project-card)
     ========================================================================== */
  function renderCatalog() {
    const categories = [
      { id: "catalog-grid-reasoning", tag: "Reasoning / CoT", limit: 6 },
      { id: "catalog-grid-agent", tag: "Agent & Coding", limit: 6 },
      { id: "catalog-grid-multimodal", tag: "Vision & Multimodal", limit: 6 },
      { id: "catalog-grid-medical", tag: "Medical & Science", limit: 6 }
    ];

    categories.forEach(cat => {
      const container = document.getElementById(cat.id);
      if (!container) return;

      const models = dataset.models.filter(m => m.tags.includes(cat.tag)).slice(0, cat.limit);

      container.innerHTML = models.map(m => `
        <a class="project-card" onclick="window.App.openDrawer('${m.id}')">
          <div class="project-card-top">
            <div class="project-card-icon">
              ${getLabIcon(m.org)}
            </div>
            <div class="project-card-info">
              <div class="project-card-name-row">
                <span class="project-card-name">${m.model}</span>
                ${m.is_milestone ? '<span class="project-card-badge">★ Milestone</span>' : ''}
              </div>
              <p class="project-card-desc">${m.highlights}</p>
            </div>
          </div>
          <div class="project-card-footer">
            <span class="project-card-model-info">${m.org} · ${m.date}</span>
          </div>
        </a>
      `).join('');
    });
  }

  /* ==========================================================================
     3. Searchable Reports Archive (LMSYS /blog exact .blog-item-full)
     ========================================================================== */
  function renderArchiveFilterTabs() {
    const container = document.getElementById("archive-filter-tabs");
    if (!container) return;

    const tabs = [
      { id: "all", label: "All" },
      { id: "Reasoning / CoT", label: "Reasoning" },
      { id: "Agent & Coding", label: "Coding & Agent" },
      { id: "Vision & Multimodal", label: "Multimodal" },
      { id: "Video", label: "Video" },
      { id: "Audio & Speech", label: "Audio" },
      { id: "Medical & Science", label: "Medical" },
      { id: "Open Weights", label: "Open Weights" }
    ];

    container.innerHTML = tabs.map(t => `
      <button onclick="window.App.setArchiveCategory('${t.id}')" class="blog-tab ${state.archiveCategory === t.id ? 'active' : ''}">
        ${t.label}
      </button>
    `).join('');
  }

  function setArchiveCategory(catId) {
    state.archiveCategory = catId;
    renderArchiveFilterTabs();
    renderArchiveList();
  }

  function renderArchiveList() {
    const container = document.getElementById("archive-list-container");
    if (!container) return;

    let list = [...(dataset.models || [])];

    if (state.archiveCategory !== "all") {
      list = list.filter(m => m.tags.includes(state.archiveCategory));
    }

    if (state.archiveQuery) {
      const q = state.archiveQuery;
      list = list.filter(m =>
        m.model.toLowerCase().includes(q) ||
        m.org.toLowerCase().includes(q) ||
        m.highlights.toLowerCase().includes(q) ||
        m.date.toLowerCase().includes(q) ||
        m.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    if (list.length === 0) {
      container.innerHTML = `<div style="text-align:center;padding:48px 0;color:var(--ink-lighter);">No technical reports matched your query.</div>`;
      return;
    }

    container.innerHTML = list.map(m => `
      <div class="blog-item-full" onclick="window.App.openDrawer('${m.id}')">
        <div class="blog-item-info">
          <div class="blog-item-tag-row">
            <span class="blog-item-tag ${m.is_milestone ? 'blog-item-tag--news' : 'blog-item-tag--tech'}">
              ${m.is_milestone ? '★ Milestone' : (m.tags[0] || 'Technical Report')}
            </span>
          </div>
          <h3 class="blog-item-title">${m.model}</h3>
          <p class="blog-item-excerpt" style="font-size:14px;color:var(--ink-dim);line-height:1.6;margin-top:6px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
            ${m.highlights}
          </p>
          <div class="blog-item-meta" style="font-size:12px;color:var(--ink-lighter);margin-top:10px;display:flex;align-items:center;justify-content:space-between;" onclick="event.stopPropagation()">
            <span>${m.org} · ${m.date}</span>
            <div style="display:flex;gap:12px;">
              <a href="${m.link}" target="_blank" rel="noopener noreferrer" style="color:var(--orange);font-weight:600;text-decoration:none;">Paper &rarr;</a>
              <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" style="color:var(--ink);text-decoration:none;">PDF</a>
              <button onclick="window.App.copyCitation('${m.id}')" style="background:none;border:none;color:var(--ink-lighter);cursor:pointer;font-size:12px;">Cite</button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  }

  /* ==========================================================================
     4. Leaderboard Table
     ========================================================================== */
  function renderLeaderboard() {
    const tbody = document.getElementById("leaderboard-table-body");
    const countEl = document.getElementById("table-results-count");
    if (!tbody) return;

    if (countEl) countEl.textContent = `${dataset.models.length} Reports`;

    tbody.innerHTML = dataset.models.map((m, idx) => `
      <tr onclick="window.App.openDrawer('${m.id}')">
        <td style="text-align:center;font-family:var(--font-mono);font-size:12px;color:var(--ink-lighter);">${idx + 1}</td>
        <td>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="font-weight:600;color:var(--ink);">${m.model}</span>
            ${m.is_milestone ? '<span style="color:var(--orange);font-weight:700;">★</span>' : ''}
          </div>
        </td>
        <td><span class="project-card-badge" style="background:rgba(8,12,38,0.06);color:var(--ink);">${m.org}</span></td>
        <td style="font-family:var(--font-mono);font-size:12px;color:var(--ink-lighter);white-space:nowrap;">${m.date}</td>
        <td style="max-width:380px;">
          <p style="font-size:13px;color:var(--ink-dim);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin:0;">
            ${m.highlights}
          </p>
        </td>
        <td style="max-width:200px;">
          <div style="display:flex;flex-wrap:wrap;gap:4px;">
            ${m.tags.slice(0, 2).map(t => `<span style="font-size:11px;padding:2px 6px;border-radius:4px;background:rgba(8,12,38,0.05);color:var(--ink-dim);border:1px solid var(--border);">${t}</span>`).join('')}
          </div>
        </td>
        <td style="text-align:right;white-space:nowrap;" onclick="event.stopPropagation()">
          <a href="${m.link}" target="_blank" rel="noopener noreferrer" style="color:var(--orange);text-decoration:none;font-weight:600;margin-right:10px;">Paper</a>
          <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" style="color:var(--ink-dim);text-decoration:none;margin-right:10px;">PDF</a>
          <button onclick="window.App.copyCitation('${m.id}')" style="background:none;border:none;color:var(--ink-lighter);cursor:pointer;font-size:12px;">Cite</button>
        </td>
      </tr>
    `).join('');
  }

  /* ==========================================================================
     5. Model Spec Sheet Drawer
     ========================================================================== */
  function openDrawer(modelId) {
    const model = dataset.models.find(m => m.id === modelId);
    if (!model) return;
    state.currentModel = model;

    const drawer = document.getElementById("model-spec-drawer");
    const titleEl = document.getElementById("drawer-title");
    const orgEl = document.getElementById("drawer-org");
    const dateEl = document.getElementById("drawer-date");
    const tagsEl = document.getElementById("drawer-tags");
    const highlightsEl = document.getElementById("drawer-highlights");
    const officialLinkEl = document.getElementById("drawer-official-link");
    const pdfLinkEl = document.getElementById("drawer-pdf-link");
    const bibtexEl = document.getElementById("drawer-bibtex");

    if (titleEl) titleEl.textContent = model.model + (model.is_milestone ? " ★" : "");
    if (orgEl) orgEl.textContent = model.org;
    if (dateEl) dateEl.textContent = model.date;
    if (tagsEl) {
      tagsEl.innerHTML = model.tags.map(t => `<span class="project-card-badge" style="background:rgba(8,12,38,0.06);color:var(--ink-dim);">${t}</span>`).join('');
    }
    if (highlightsEl) highlightsEl.textContent = model.highlights;
    if (officialLinkEl) officialLinkEl.href = model.link;
    if (pdfLinkEl) pdfLinkEl.href = getPdfUrl(model.file);
    if (bibtexEl) bibtexEl.textContent = generateBibtex(model);

    if (drawer) drawer.style.display = "flex";
  }

  function closeDrawer() {
    const drawer = document.getElementById("model-spec-drawer");
    if (drawer) drawer.style.display = "none";
  }

  function generateBibtex(model) {
    const citeKey = `${model.org.replace(/[^a-zA-Z]/g, '').toLowerCase()}${model.year}${model.model.replace(/[^a-zA-Z0-9]/g, '').toLowerCase()}`;
    return `@article{${citeKey},
  title={${model.model} Technical Report},
  author={${model.org}},
  year={${model.year}},
  month={${model.month}},
  url={${model.link}}
}`;
  }

  function copyCitation(modelId) {
    const model = dataset.models.find(m => m.id === modelId) || state.currentModel;
    if (!model) return;

    const bibtex = generateBibtex(model);
    navigator.clipboard.writeText(bibtex).then(() => {
      showToast(`Copied BibTeX citation for ${model.model}!`);
    }).catch(() => {
      showToast("Failed to copy citation to clipboard.");
    });
  }

  function showToast(message) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "lmsys-toast";
    toast.innerHTML = `<span>📑 ${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 250);
    }, 2600);
  }

  return {
    init,
    setArchiveCategory,
    searchLab,
    openDrawer,
    closeDrawer,
    copyCitation,
    getPdfUrl,
    showToast
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  window.App.init();
});
