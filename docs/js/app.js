/**
 * Awesome LLM Technical Reports - LMSYS Org & Arena Controller
 */

window.App = (function() {
  let dataset = { metadata: {}, stats: {}, models: [] };
  let state = {
    category: "all",
    searchQuery: "",
    camp: "all",
    year: "all",
    onlyMilestones: false,
    view: "timeline", // timeline | table | grid | analytics
    currentModel: null,
    isDark: false
  };

  let charts = {};

  const ORG_EMOJIS = {
    "OpenAI": "🟢",
    "Anthropic": "🟠",
    "Google": "🔵",
    "DeepSeek": "🐳",
    "Alibaba": "🟠",
    "Zhipu AI": "🟣",
    "Meituan": "🟡",
    "Tencent": "🐧",
    "ByteDance": "🔴",
    "MiniMax": "🚀",
    "Moonshot AI": "🌙",
    "Meta": "🔷",
    "NVIDIA": "🟢",
    "Microsoft": "🟦",
    "xAI": "⚫",
    "StepFun": "⚡",
    "InternLM": "📘",
    "OpenBMB": "🐝",
    "InclusionAI (Ant Group)": "🐜",
    "Allen AI": "🔬",
    "Hugging Face": "🤗",
    "Snowflake": "❄️",
    "Quark (Alibaba)": "🔍"
  };

  async function init() {
    setupTheme();
    setupEventListeners();
    await loadData();
    parseUrlParams();
    renderHeroStats();
    renderCategoryTabs();
    applyFiltersAndRender();
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
      showToast("Error loading dataset. Please check console.", "error");
    }
  }

  function setupTheme() {
    const savedTheme = localStorage.getItem("lmsys_theme");
    state.isDark = savedTheme === "dark";
    updateThemeClass();
  }

  function toggleTheme() {
    state.isDark = !state.isDark;
    localStorage.setItem("lmsys_theme", state.isDark ? "dark" : "light");
    updateThemeClass();
    if (state.view === "analytics") {
      renderAnalytics(getFilteredModels());
    }
  }

  function updateThemeClass() {
    if (state.isDark) {
      document.documentElement.setAttribute("data-theme", "dark");
      const icon = document.getElementById("theme-toggle-icon");
      if (icon) icon.innerHTML = '<path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"></path>';
    } else {
      document.documentElement.removeAttribute("data-theme");
      const icon = document.getElementById("theme-toggle-icon");
      if (icon) icon.innerHTML = '<path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"></path>';
    }
  }

  function setupEventListeners() {
    const searchInput = document.getElementById("global-search-input");
    if (searchInput) {
      let timeout = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          state.searchQuery = e.target.value.trim().toLowerCase();
          applyFiltersAndRender();
        }, 150);
      });
    }

    // Keyboard shortcut (Cmd/Ctrl + K or /)
    window.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k" || (e.key === "/" && document.activeElement !== searchInput)) {
        e.preventDefault();
        searchInput?.focus();
      }
      if (e.key === "Escape") {
        closeDrawer();
        if (window.ArenaCompare) window.ArenaCompare.closeCompareModal();
      }
    });

    // Camp filter dropdown
    const campSelect = document.getElementById("camp-filter-select");
    if (campSelect) {
      campSelect.addEventListener("change", (e) => {
        state.camp = e.target.value;
        applyFiltersAndRender();
      });
    }

    // Year filter dropdown
    const yearSelect = document.getElementById("year-filter-select");
    if (yearSelect) {
      yearSelect.addEventListener("change", (e) => {
        state.year = e.target.value;
        applyFiltersAndRender();
      });
    }

    // Milestone toggle
    const milestoneCheckbox = document.getElementById("milestone-filter-checkbox");
    if (milestoneCheckbox) {
      milestoneCheckbox.addEventListener("change", (e) => {
        state.onlyMilestones = e.target.checked;
        applyFiltersAndRender();
      });
    }
  }

  function parseUrlParams() {
    const params = new URLSearchParams(window.location.search);
    if (params.has("view")) state.view = params.get("view");
    if (params.has("category")) state.category = params.get("category");
    if (params.has("search")) {
      state.searchQuery = params.get("search").toLowerCase();
      const input = document.getElementById("global-search-input");
      if (input) input.value = state.searchQuery;
    }
    if (params.has("camp")) {
      state.camp = params.get("camp");
      const campSelect = document.getElementById("camp-filter-select");
      if (campSelect) campSelect.value = state.camp;
    }
    updateViewButtons();
  }

  function updateUrlParams() {
    const params = new URLSearchParams();
    if (state.view !== "timeline") params.set("view", state.view);
    if (state.category !== "all") params.set("category", state.category);
    if (state.searchQuery) params.set("search", state.searchQuery);
    if (state.camp !== "all") params.set("camp", state.camp);
    
    const newQuery = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
    window.history.replaceState(null, '', newQuery);
  }

  function renderHeroStats() {
    const stats = dataset.stats;
    if (!stats) return;

    const elCount = document.getElementById("stat-total-models");
    const elOrgs = document.getElementById("stat-total-orgs");
    const elSpan = document.getElementById("stat-date-span");
    const elMilestones = document.getElementById("stat-milestones");

    if (elCount) elCount.textContent = `${stats.total_models || 112}+`;
    if (elOrgs) elOrgs.textContent = `${stats.total_orgs || 23}`;
    if (elSpan) elSpan.textContent = `19 Mos`;
    if (elMilestones) elMilestones.textContent = `${stats.milestones_count || 44}★`;
  }

  function renderCategoryTabs() {
    const container = document.getElementById("category-tabs-container");
    if (!container) return;

    const categories = [
      { id: "all", label: "Overall All", count: dataset.models.length },
      { id: "Reasoning / CoT", label: "Reasoning / CoT", count: dataset.stats.tag_breakdown?.["Reasoning / CoT"] || 49 },
      { id: "Agent & Coding", label: "Agent & Coding", count: dataset.stats.tag_breakdown?.["Agent & Coding"] || 47 },
      { id: "Vision & Multimodal", label: "Vision & Omni", count: dataset.stats.tag_breakdown?.["Vision & Multimodal"] || 51 },
      { id: "Audio & Speech", label: "Audio & Speech", count: dataset.stats.tag_breakdown?.["Audio & Speech"] || 18 },
      { id: "Video", label: "Video", count: dataset.stats.tag_breakdown?.["Video"] || 19 },
      { id: "Medical & Science", label: "Medical & Science", count: dataset.stats.tag_breakdown?.["Medical & Science"] || 33 },
      { id: "MoE", label: "MoE Architecture", count: dataset.stats.tag_breakdown?.["MoE"] || 19 },
      { id: "Open Weights", label: "Open Weights", count: dataset.stats.tag_breakdown?.["Open Weights"] || 44 }
    ];

    container.innerHTML = categories.map(cat => `
      <button onclick="window.App.setCategory('${cat.id}')" class="category-pill ${state.category === cat.id ? 'active' : ''}">
        <span>${cat.label}</span>
        <span class="category-count">${cat.count}</span>
      </button>
    `).join('');
  }

  function setCategory(catId) {
    state.category = catId;
    renderCategoryTabs();
    applyFiltersAndRender();
  }

  function switchView(viewName) {
    state.view = viewName;
    updateViewButtons();
    applyFiltersAndRender();
  }

  function updateViewButtons() {
    const views = ["timeline", "table", "grid", "analytics"];
    views.forEach(v => {
      const btn = document.getElementById(`view-btn-${v}`);
      if (btn) {
        if (state.view === v) btn.classList.add("active");
        else btn.classList.remove("active");
      }
    });
  }

  function filterByOrg(orgName) {
    state.searchQuery = orgName.toLowerCase();
    const input = document.getElementById("global-search-input");
    if (input) input.value = orgName;
    scrollToArchive();
    applyFiltersAndRender();
  }

  function scrollToArchive() {
    const el = document.getElementById("archive-section");
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }

  function getFilteredModels() {
    let list = [...(dataset.models || [])];

    if (state.category !== "all") {
      list = list.filter(m => m.tags.includes(state.category));
    }
    if (state.camp !== "all") {
      list = list.filter(m => m.camp === state.camp);
    }
    if (state.year !== "all") {
      list = list.filter(m => m.year === parseInt(state.year));
    }
    if (state.onlyMilestones) {
      list = list.filter(m => m.is_milestone);
    }
    if (state.searchQuery) {
      const q = state.searchQuery;
      list = list.filter(m =>
        m.model.toLowerCase().includes(q) ||
        m.org.toLowerCase().includes(q) ||
        m.highlights.toLowerCase().includes(q) ||
        m.date.toLowerCase().includes(q) ||
        m.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    list.sort((a, b) => b.date.localeCompare(a.date) || a.model.localeCompare(b.model));
    return list;
  }

  function applyFiltersAndRender() {
    updateUrlParams();
    const filtered = getFilteredModels();

    const countEl = document.getElementById("filtered-results-count");
    if (countEl) {
      countEl.textContent = `${filtered.length} of ${dataset.models.length} reports`;
    }

    const containers = {
      timeline: document.getElementById("view-container-timeline"),
      table: document.getElementById("view-container-table"),
      grid: document.getElementById("view-container-grid"),
      analytics: document.getElementById("view-container-analytics")
    };

    Object.keys(containers).forEach(k => {
      if (containers[k]) containers[k].style.display = (k === state.view) ? "block" : "none";
    });

    if (state.view === "timeline") renderTimeline(filtered);
    else if (state.view === "table") renderTable(filtered);
    else if (state.view === "grid") renderGrid(filtered);
    else if (state.view === "analytics") renderAnalytics(filtered);
  }

  function getOrgEmoji(org) {
    return ORG_EMOJIS[org] || "📄";
  }

  function getPdfUrl(filePath) {
    const base = dataset.metadata?.pdf_base_url || "https://raw.githubusercontent.com/joe1chief/awesome-llm-tech-reports/main/";
    return base + filePath;
  }

  /* ==========================================================================
     Render 1: LMSYS Alternating Timeline (.timeline, .tl-row, .tl-card)
     ========================================================================== */
  function renderTimeline(models) {
    const container = document.getElementById("timeline-flow-container");
    if (!container) return;

    if (models.length === 0) {
      container.innerHTML = `<div style="text-align: center; padding: 60px 0; color: var(--ink-lighter);">No technical reports matched your criteria.</div>`;
      return;
    }

    const monthGroups = {};
    models.forEach(m => {
      if (!monthGroups[m.date]) monthGroups[m.date] = [];
      monthGroups[m.date].push(m);
    });

    let html = '';
    let globalIndex = 0;

    Object.keys(monthGroups).forEach(month => {
      const monthModels = monthGroups[month];
      html += `
        <div class="tl-month-header">
          <span class="tl-month-tag font-mono">${month} · ${monthModels.length} ${monthModels.length === 1 ? 'Report' : 'Reports'}</span>
        </div>
      `;

      monthModels.forEach((m) => {
        const isLeft = globalIndex % 2 === 0;
        globalIndex++;

        const cardContent = `
          <div class="tl-card" onclick="window.App.openDrawer('${m.id}')">
            <div class="tl-name-row">
              <span class="tl-name">${m.model}</span>
              ${m.is_milestone ? '<span class="tl-badge">★ Milestone</span>' : `<span class="tl-badge" style="background: rgba(8,12,38,0.06); color: var(--ink-dim);">${m.org}</span>`}
            </div>
            <p class="tl-desc">${m.highlights}</p>
            <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;">
              ${m.tags.map(t => `<span class="table-tag">${t}</span>`).join('')}
            </div>
            <div class="tl-footer" onclick="event.stopPropagation()">
              <span>${m.org} · ${m.date}</span>
              <div class="tl-actions">
                <a href="${m.link}" target="_blank" rel="noopener noreferrer" class="tl-link">Paper &rarr;</a>
                <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" style="color: var(--ink-dim); text-decoration: none;">PDF</a>
                <button onclick="window.App.copyCitation('${m.id}')" style="background: none; border: none; color: var(--ink-lighter); cursor: pointer; font-size: 12px;">Cite</button>
              </div>
            </div>
          </div>
        `;

        if (isLeft) {
          html += `
            <div class="tl-row">
              <div class="tl-left">${cardContent}</div>
              <div class="tl-icon-col">
                <div class="tl-icon ${m.is_milestone ? 'milestone-icon' : ''}" title="${m.model} (${m.org})">
                  ${getOrgEmoji(m.org)}
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
                <div class="tl-icon ${m.is_milestone ? 'milestone-icon' : ''}" title="${m.model} (${m.org})">
                  ${getOrgEmoji(m.org)}
                </div>
              </div>
              <div class="tl-right">${cardContent}</div>
            </div>
          `;
        }
      });
    });

    container.innerHTML = html;
  }

  /* ==========================================================================
     Render 2: Leaderboard Table View (LMSYS Arena style)
     ========================================================================== */
  function renderTable(models) {
    const tbody = document.getElementById("arena-table-body");
    if (!tbody) return;

    if (models.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 48px 0; color: var(--ink-lighter);">No technical reports matched your criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = models.map((m, idx) => `
      <tr onclick="window.App.openDrawer('${m.id}')">
        <td class="table-rank">${idx + 1}</td>
        <td>
          <div class="table-model-name">
            <span>${m.model}</span>
            ${m.is_milestone ? '<span style="color: var(--orange); font-weight: bold;">★</span>' : ''}
          </div>
        </td>
        <td><span class="tl-badge" style="background: rgba(8,12,38,0.06); color: var(--ink);">${m.org}</span></td>
        <td style="font-family: var(--font-mono); font-size: 12px; color: var(--ink-lighter); white-space: nowrap;">${m.date}</td>
        <td style="max-width: 380px;">
          <p style="font-size: 13px; color: var(--ink-dim); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${m.highlights}</p>
        </td>
        <td style="max-width: 220px;">
          <div style="display: flex; flex-wrap: wrap; gap: 3px;">
            ${m.tags.slice(0, 3).map(t => `<span class="table-tag">${t}</span>`).join('')}
            ${m.tags.length > 3 ? `<span class="table-tag">+${m.tags.length - 3}</span>` : ''}
          </div>
        </td>
        <td style="text-align: right; white-space: nowrap;" onclick="event.stopPropagation()">
          <a href="${m.link}" target="_blank" rel="noopener noreferrer" style="color: var(--orange); text-decoration: none; font-weight: 500; margin-right: 10px;">Paper</a>
          <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" style="color: var(--ink-dim); text-decoration: none; margin-right: 10px;">PDF</a>
          <button onclick="window.App.copyCitation('${m.id}')" style="background: none; border: none; color: var(--ink-lighter); cursor: pointer;">Cite</button>
        </td>
      </tr>
    `).join('');
  }

  /* ==========================================================================
     Render 3: Grid Cards View
     ========================================================================== */
  function renderGrid(models) {
    const container = document.getElementById("grid-cards-container");
    if (!container) return;

    if (models.length === 0) {
      container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 60px 0; color: var(--ink-lighter);">No technical reports matched your criteria.</div>`;
      return;
    }

    container.innerHTML = models.map(m => `
      <div class="hero-blog-card" onclick="window.App.openDrawer('${m.id}')">
        <div class="hero-blog-card-body">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="tl-badge" style="background: rgba(8,12,38,0.06); color: var(--ink);">${m.org}</span>
            <span style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-lighter);">${m.date}</span>
          </div>
          <h3 class="hero-blog-card-title" style="margin-top: 4px;">${m.model} ${m.is_milestone ? '★' : ''}</h3>
          <p class="hero-blog-card-excerpt">${m.highlights}</p>
          <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;">
            ${m.tags.map(t => `<span class="table-tag">${t}</span>`).join('')}
          </div>
          <div class="hero-blog-card-meta" onclick="event.stopPropagation()">
            <a href="${m.link}" target="_blank" rel="noopener noreferrer" style="color: var(--orange); text-decoration: none; font-weight: 500;">Paper &rarr;</a>
            <div style="display: flex; gap: 10px;">
              <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" style="color: var(--ink-dim); text-decoration: none;">PDF</a>
              <button onclick="window.App.copyCitation('${m.id}')" style="background: none; border: none; color: var(--ink-lighter); cursor: pointer;">Cite</button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  }

  /* ==========================================================================
     Render 4: Analytics Dashboard
     ========================================================================== */
  function renderAnalytics(models) {
    if (typeof Chart === 'undefined') return;

    const textColor = state.isDark ? '#e2e8f0' : 'rgb(8,12,38)';
    const gridColor = state.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(8,12,38,0.06)';

    // Monthly Trends
    const monthlyCtx = document.getElementById("chart-monthly-trends")?.getContext("2d");
    if (monthlyCtx) {
      if (charts.monthly) charts.monthly.destroy();
      const monthCounts = {};
      models.forEach(m => {
        monthCounts[m.date] = (monthCounts[m.date] || 0) + 1;
      });
      const labels = Object.keys(monthCounts).sort();
      const data = labels.map(l => monthCounts[l]);

      charts.monthly = new Chart(monthlyCtx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Reports Released',
            data,
            backgroundColor: 'rgba(234, 106, 16, 0.85)',
            borderColor: '#ea6a10',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: 'Inter' } } },
            y: { grid: { color: gridColor }, ticks: { color: textColor, precision: 0 } }
          }
        }
      });
    }

    // Organization Share
    const orgCtx = document.getElementById("chart-org-share")?.getContext("2d");
    if (orgCtx) {
      if (charts.org) charts.org.destroy();
      const orgCounts = {};
      models.forEach(m => {
        orgCounts[m.org] = (orgCounts[m.org] || 0) + 1;
      });
      const sortedOrgs = Object.entries(orgCounts).sort((a, b) => b[1] - a[1]);
      const topOrgs = sortedOrgs.slice(0, 7);
      const otherCount = sortedOrgs.slice(7).reduce((sum, item) => sum + item[1], 0);
      if (otherCount > 0) topOrgs.push(["Other Labs", otherCount]);

      charts.org = new Chart(orgCtx, {
        type: 'doughnut',
        data: {
          labels: topOrgs.map(o => o[0]),
          datasets: [{
            data: topOrgs.map(o => o[1]),
            backgroundColor: [
              '#ea6a10', '#2563eb', '#10b981', '#a855f7', '#ec4899',
              '#eab308', '#0ea5e9', '#64687a'
            ],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { color: textColor, font: { family: 'Inter', size: 12 }, boxWidth: 12 } }
          }
        }
      });
    }

    // Modality Breakdown
    const tagCtx = document.getElementById("chart-tag-breakdown")?.getContext("2d");
    if (tagCtx) {
      if (charts.tag) charts.tag.destroy();
      const tagCounts = {};
      models.forEach(m => {
        m.tags.forEach(t => {
          tagCounts[t] = (tagCounts[t] || 0) + 1;
        });
      });
      const labels = Object.keys(tagCounts);
      const data = labels.map(l => tagCounts[l]);

      charts.tag = new Chart(tagCtx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Models by Capability',
            data,
            backgroundColor: 'rgba(37, 99, 235, 0.8)',
            borderColor: '#2563eb',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: gridColor }, ticks: { color: textColor, precision: 0 } },
            y: { grid: { color: gridColor }, ticks: { color: textColor, font: { family: 'Inter' } } }
          }
        }
      });
    }
  }

  /* ==========================================================================
     Model Detail Drawer (LMSYS Spec Sheet)
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
      tagsEl.innerHTML = model.tags.map(t => `<span class="table-tag">${t}</span>`).join('');
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
      showToast("Failed to copy citation to clipboard.", "error");
    });
  }

  function showToast(message) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = "toast-box";
    toast.innerHTML = `<span>📑 ${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 250);
    }, 2600);
  }

  return {
    init,
    setCategory,
    switchView,
    toggleTheme,
    filterByOrg,
    scrollToArchive,
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
