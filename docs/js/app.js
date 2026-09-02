/**
 * Awesome LLM Technical Reports - LMSYS Inspired Web Application Controller
 */

window.App = (function() {
  let dataset = { metadata: {}, stats: {}, models: [] };
  let state = {
    category: "all",
    searchQuery: "",
    camp: "all",
    year: "all",
    onlyMilestones: false,
    view: "table", // table | timeline | grid | analytics
    sortBy: "date_desc",
    currentModel: null,
    isDark: true
  };

  let charts = {};

  const ORG_CLASSES = {
    "OpenAI": "badge-openai",
    "Anthropic": "badge-anthropic",
    "Google": "badge-google",
    "DeepSeek": "badge-deepseek",
    "Alibaba": "badge-alibaba",
    "Zhipu AI": "badge-zhipu",
    "Meituan": "badge-meituan",
    "Tencent": "badge-tencent",
    "ByteDance": "badge-bytedance",
    "MiniMax": "badge-minimax",
    "Moonshot AI": "badge-moonshot",
    "Meta": "badge-meta",
    "NVIDIA": "badge-nvidia",
    "Microsoft": "badge-microsoft",
    "xAI": "badge-xai"
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
    const savedTheme = localStorage.getItem("theme");
    state.isDark = savedTheme ? savedTheme === "dark" : true;
    updateThemeClass();
  }

  function toggleTheme() {
    state.isDark = !state.isDark;
    localStorage.setItem("theme", state.isDark ? "dark" : "light");
    updateThemeClass();
    if (state.view === "analytics") {
      renderCharts();
    }
  }

  function updateThemeClass() {
    if (state.isDark) {
      document.documentElement.classList.remove("light-theme");
      const icon = document.getElementById("theme-toggle-icon");
      if (icon) icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>';
    } else {
      document.documentElement.classList.add("light-theme");
      const icon = document.getElementById("theme-toggle-icon");
      if (icon) icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>';
    }
  }

  function setupEventListeners() {
    // Search bar with debounce
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

    // Sort select
    const sortSelect = document.getElementById("sort-select");
    if (sortSelect) {
      sortSelect.addEventListener("change", (e) => {
        state.sortBy = e.target.value;
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
    if (state.view !== "table") params.set("view", state.view);
    if (state.category !== "all") params.set("category", state.category);
    if (state.searchQuery) params.set("search", state.searchQuery);
    if (state.camp !== "all") params.set("camp", state.camp);
    
    const newRelativePathQuery = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
    window.history.replaceState(null, '', newRelativePathQuery);
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
    if (elSpan) elSpan.textContent = `2025.01 - 2026.07`;
    if (elMilestones) elMilestones.textContent = `${stats.milestones_count || 44}★`;
  }

  function renderCategoryTabs() {
    const container = document.getElementById("category-tabs-container");
    if (!container) return;

    const categories = [
      { id: "all", label: "Overall All", count: dataset.models.length },
      { id: "Reasoning / CoT", label: "Reasoning / CoT", count: dataset.stats.tag_breakdown["Reasoning / CoT"] || 49 },
      { id: "Agent & Coding", label: "Agent & Coding", count: dataset.stats.tag_breakdown["Agent & Coding"] || 47 },
      { id: "Vision & Multimodal", label: "Vision & Omni", count: dataset.stats.tag_breakdown["Vision & Multimodal"] || 51 },
      { id: "Audio & Speech", label: "Audio & Speech", count: dataset.stats.tag_breakdown["Audio & Speech"] || 18 },
      { id: "Video", label: "Video", count: dataset.stats.tag_breakdown["Video"] || 19 },
      { id: "Medical & Science", label: "Medical & Science", count: dataset.stats.tag_breakdown["Medical & Science"] || 33 },
      { id: "MoE", label: "MoE Architecture", count: dataset.stats.tag_breakdown["MoE"] || 19 },
      { id: "Open Weights", label: "Open Weights", count: dataset.stats.tag_breakdown["Open Weights"] || 44 }
    ];

    container.innerHTML = categories.map(cat => `
      <button onclick="window.App.setCategory('${cat.id}')" class="category-tab px-4 py-2.5 text-sm font-medium flex items-center gap-2 cursor-pointer transition-colors ${state.category === cat.id ? 'active text-indigo-400' : 'text-gray-400 hover:text-gray-200'}">
        <span>${cat.label}</span>
        <span class="px-1.5 py-0.5 text-xs rounded-full ${state.category === cat.id ? 'bg-indigo-500/20 text-indigo-300' : 'bg-white/5 text-gray-400'} font-mono">${cat.count}</span>
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
    const views = ["table", "timeline", "grid", "analytics"];
    views.forEach(v => {
      const btn = document.getElementById(`view-btn-${v}`);
      if (btn) {
        if (state.view === v) {
          btn.classList.add("bg-indigo-600", "text-white");
          btn.classList.remove("text-gray-400", "hover:text-gray-200", "bg-transparent");
        } else {
          btn.classList.remove("bg-indigo-600", "text-white");
          btn.classList.add("text-gray-400", "hover:text-gray-200", "bg-transparent");
        }
      }
    });
  }

  function getFilteredModels() {
    let list = [...(dataset.models || [])];

    // Category filter
    if (state.category !== "all") {
      list = list.filter(m => m.tags.includes(state.category));
    }

    // Camp filter
    if (state.camp !== "all") {
      list = list.filter(m => m.camp === state.camp);
    }

    // Year filter
    if (state.year !== "all") {
      list = list.filter(m => m.year === parseInt(state.year));
    }

    // Milestone filter
    if (state.onlyMilestones) {
      list = list.filter(m => m.is_milestone);
    }

    // Search Query filter
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

    // Sorting
    list.sort((a, b) => {
      if (state.sortBy === "date_desc") return b.date.localeCompare(a.date) || a.model.localeCompare(b.model);
      if (state.sortBy === "date_asc") return a.date.localeCompare(b.date) || a.model.localeCompare(b.model);
      if (state.sortBy === "model") return a.model.localeCompare(b.model);
      if (state.sortBy === "org") return a.org.localeCompare(b.org) || b.date.localeCompare(a.date);
      return 0;
    });

    return list;
  }

  function applyFiltersAndRender() {
    updateUrlParams();
    const filtered = getFilteredModels();

    const resultCountEl = document.getElementById("filtered-results-count");
    if (resultCountEl) {
      resultCountEl.textContent = `Showing ${filtered.length} of ${dataset.models.length} reports`;
    }

    // Hide all view containers
    const containers = {
      table: document.getElementById("view-container-table"),
      timeline: document.getElementById("view-container-timeline"),
      grid: document.getElementById("view-container-grid"),
      analytics: document.getElementById("view-container-analytics")
    };

    Object.keys(containers).forEach(k => {
      if (containers[k]) containers[k].classList.add("hidden");
    });

    if (containers[state.view]) {
      containers[state.view].classList.remove("hidden");
    }

    if (state.view === "table") renderTable(filtered);
    else if (state.view === "timeline") renderTimeline(filtered);
    else if (state.view === "grid") renderGrid(filtered);
    else if (state.view === "analytics") renderAnalytics(filtered);
  }

  function getOrgBadgeClass(org) {
    return ORG_CLASSES[org] || "badge-default";
  }

  function getPdfUrl(filePath) {
    // Relative to repo raw URL on github
    const base = dataset.metadata.pdf_base_url || "https://raw.githubusercontent.com/joe1chief/awesome-llm-tech-reports/main/";
    return base + filePath;
  }

  /* Render 1: Arena Leaderboard Table */
  function renderTable(models) {
    const tbody = document.getElementById("arena-table-body");
    if (!tbody) return;

    if (models.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-12 text-gray-400">No technical reports matched your criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = models.map((m, idx) => `
      <tr class="arena-table-row border-b border-white/5 cursor-pointer" onclick="window.App.openDrawer('${m.id}')">
        <td class="px-4 py-3.5 text-xs text-gray-400 font-mono text-center">
          ${idx + 1}
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap">
          <div class="flex items-center gap-2">
            <span class="font-bold text-sm text-white group-hover:text-indigo-400 transition-colors">${m.model}</span>
            ${m.is_milestone ? '<span class="text-xs px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30" title="Milestone Breakthrough">★</span>' : ''}
          </div>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap">
          <span class="px-2.5 py-1 text-xs font-semibold rounded-md ${getOrgBadgeClass(m.org)}">${m.org}</span>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap text-xs text-gray-400 font-mono">
          ${m.date}
        </td>
        <td class="px-4 py-3.5 max-w-md">
          <p class="text-xs text-gray-300 line-clamp-2 leading-relaxed">${m.highlights}</p>
        </td>
        <td class="px-4 py-3.5">
          <div class="flex flex-wrap gap-1 max-w-xs">
            ${m.tags.slice(0, 3).map(t => `<span class="px-1.5 py-0.5 text-[10px] rounded bg-white/5 text-gray-300 border border-white/10">${t}</span>`).join('')}
            ${m.tags.length > 3 ? `<span class="px-1 py-0.5 text-[10px] text-gray-400">+${m.tags.length - 3}</span>` : ''}
          </div>
        </td>
        <td class="px-4 py-3.5 whitespace-nowrap text-right text-xs" onclick="event.stopPropagation()">
          <div class="flex items-center justify-end gap-1.5">
            <a href="${m.link}" target="_blank" rel="noopener noreferrer" title="Official Paper Link" class="p-1.5 rounded-lg bg-white/5 hover:bg-white/15 text-indigo-400 hover:text-indigo-300 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
            </a>
            <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" title="Download Local PDF" class="p-1.5 rounded-lg bg-white/5 hover:bg-white/15 text-red-400 hover:text-red-300 transition-colors">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
            </a>
            <button onclick="window.App.copyCitation('${m.id}')" title="Copy BibTeX Citation" class="p-1.5 rounded-lg bg-white/5 hover:bg-white/15 text-gray-400 hover:text-white transition-colors cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }

  /* Render 2: LMSYS Alternating Timeline */
  function renderTimeline(models) {
    const container = document.getElementById("timeline-flow-container");
    if (!container) return;

    if (models.length === 0) {
      container.innerHTML = `<div class="text-center py-16 text-gray-400">No technical reports matched your criteria.</div>`;
      return;
    }

    // Group by month
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
        <div class="tl-month-divider">
          <span class="tl-month-pill font-mono">${month} (${monthModels.length} ${monthModels.length === 1 ? 'Report' : 'Reports'})</span>
        </div>
      `;

      monthModels.forEach((m) => {
        const isLeft = globalIndex % 2 === 0;
        globalIndex++;

        html += `
          <div class="tl-item ${isLeft ? 'left' : 'right'}">
            <div class="tl-node-center ${m.is_milestone ? 'milestone-node' : ''}" title="${m.model} (${m.org})">
              ${m.is_milestone ? '★' : '<div class="w-2.5 h-2.5 rounded-full bg-indigo-500"></div>'}
            </div>
            <div class="tl-card-container">
              <div class="glass-panel p-4 rounded-xl shadow-lg border hover:border-indigo-500/50 transition-all cursor-pointer group" onclick="window.App.openDrawer('${m.id}')">
                <div class="flex items-center justify-between mb-2">
                  <span class="px-2 py-0.5 text-xs font-semibold rounded ${getOrgBadgeClass(m.org)}">${m.org}</span>
                  <span class="text-xs text-gray-400 font-mono">${m.date}</span>
                </div>
                <h4 class="text-base font-bold text-white group-hover:text-indigo-400 transition-colors mb-2">${m.model}</h4>
                <p class="text-xs text-gray-300 line-clamp-3 leading-relaxed mb-3">${m.highlights}</p>
                <div class="flex flex-wrap gap-1 mb-3">
                  ${m.tags.map(t => `<span class="px-1.5 py-0.5 text-[10px] rounded bg-white/5 text-gray-300 border border-white/10">${t}</span>`).join('')}
                </div>
                <div class="flex items-center justify-between pt-2 border-t border-white/10 text-xs" onclick="event.stopPropagation()">
                  <a href="${m.link}" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1">
                    Official Paper &rarr;
                  </a>
                  <div class="flex items-center gap-2">
                    <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" class="text-red-400 hover:text-red-300 font-medium">
                      PDF
                    </a>
                    <button onclick="window.App.copyCitation('${m.id}')" class="text-gray-400 hover:text-white cursor-pointer">
                      Cite
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
      });
    });

    container.innerHTML = html;
  }

  /* Render 3: Grid Cards */
  function renderGrid(models) {
    const container = document.getElementById("grid-cards-container");
    if (!container) return;

    if (models.length === 0) {
      container.innerHTML = `<div class="col-span-full text-center py-16 text-gray-400">No technical reports matched your criteria.</div>`;
      return;
    }

    container.innerHTML = models.map(m => `
      <div class="glass-panel p-5 rounded-xl border flex flex-col justify-between hover:border-indigo-500/50 transition-all cursor-pointer group" onclick="window.App.openDrawer('${m.id}')">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="px-2.5 py-1 text-xs font-semibold rounded-md ${getOrgBadgeClass(m.org)}">${m.org}</span>
            <div class="flex items-center gap-1.5">
              ${m.is_milestone ? '<span class="text-xs px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30">★</span>' : ''}
              <span class="text-xs text-gray-400 font-mono">${m.date}</span>
            </div>
          </div>
          <h4 class="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors mb-2">${m.model}</h4>
          <p class="text-xs text-gray-300 line-clamp-3 leading-relaxed mb-3">${m.highlights}</p>
        </div>

        <div>
          <div class="flex flex-wrap gap-1 mb-4">
            ${m.tags.map(t => `<span class="px-1.5 py-0.5 text-[10px] rounded bg-white/5 text-gray-300 border border-white/10">${t}</span>`).join('')}
          </div>
          <div class="flex items-center justify-between pt-3 border-t border-white/10 text-xs" onclick="event.stopPropagation()">
            <a href="${m.link}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded bg-indigo-600/80 hover:bg-indigo-600 text-white font-medium inline-flex items-center gap-1 transition-colors">
              Paper
            </a>
            <div class="flex items-center gap-2">
              <a href="${getPdfUrl(m.file)}" target="_blank" rel="noopener noreferrer" class="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-red-400 font-medium transition-colors">
                PDF
              </a>
              <button onclick="window.App.copyCitation('${m.id}')" class="px-2.5 py-1 rounded bg-white/5 hover:bg-white/15 text-gray-300 hover:text-white cursor-pointer transition-colors">
                Cite
              </button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  }

  /* Render 4: Analytics Dashboard */
  function renderAnalytics(models) {
    if (typeof Chart === 'undefined') return;

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
            label: 'Technical Reports Released',
            data,
            backgroundColor: 'rgba(99, 102, 241, 0.7)',
            borderColor: '#6366f1',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af', precision: 0 } }
          }
        }
      });
    }

    // Organization Market Share
    const orgCtx = document.getElementById("chart-org-share")?.getContext("2d");
    if (orgCtx) {
      if (charts.org) charts.org.destroy();
      const orgCounts = {};
      models.forEach(m => {
        orgCounts[m.org] = (orgCounts[m.org] || 0) + 1;
      });
      const sortedOrgs = Object.entries(orgCounts).sort((a, b) => b[1] - a[1]);
      const topOrgs = sortedOrgs.slice(0, 8);
      const otherCount = sortedOrgs.slice(8).reduce((sum, item) => sum + item[1], 0);
      if (otherCount > 0) topOrgs.push(["Other Labs", otherCount]);

      charts.org = new Chart(orgCtx, {
        type: 'doughnut',
        data: {
          labels: topOrgs.map(o => o[0]),
          datasets: [{
            data: topOrgs.map(o => o[1]),
            backgroundColor: [
              '#3b82f6', '#10b981', '#f97316', '#a855f7', '#ec4899',
              '#eab308', '#0ea5e9', '#ef4444', '#6b7280'
            ],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'right', labels: { color: '#9ca3af', boxWidth: 12 } }
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
            label: 'Capability Distribution',
            data,
            backgroundColor: 'rgba(168, 85, 247, 0.7)',
            borderColor: '#a855f7',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af', precision: 0 } },
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
          }
        }
      });
    }
  }

  /* Model Drawer */
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

    if (titleEl) titleEl.textContent = model.model;
    if (orgEl) {
      orgEl.textContent = model.org;
      orgEl.className = `px-2.5 py-1 text-xs font-semibold rounded-md ${getOrgBadgeClass(model.org)}`;
    }
    if (dateEl) dateEl.textContent = model.date;
    if (tagsEl) {
      tagsEl.innerHTML = model.tags.map(t => `<span class="px-2 py-0.5 text-xs rounded bg-white/5 text-gray-300 border border-white/10">${t}</span>`).join('');
    }
    if (highlightsEl) highlightsEl.textContent = model.highlights;
    if (officialLinkEl) officialLinkEl.href = model.link;
    if (pdfLinkEl) pdfLinkEl.href = getPdfUrl(model.file);
    if (bibtexEl) bibtexEl.textContent = generateBibtex(model);

    if (drawer) {
      drawer.classList.remove("hidden");
    }
  }

  function closeDrawer() {
    const drawer = document.getElementById("model-spec-drawer");
    if (drawer) {
      drawer.classList.add("hidden");
    }
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

  function copyMarkdown(modelId) {
    const model = dataset.models.find(m => m.id === modelId) || state.currentModel;
    if (!model) return;

    const md = `[${model.model} (${model.org}, ${model.date})](${model.link})`;
    navigator.clipboard.writeText(md).then(() => {
      showToast(`Copied Markdown link for ${model.model}!`);
    });
  }

  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast border ${type === 'error' ? 'border-red-500/50 text-red-200' : 'border-indigo-500/40 text-gray-100'}`;
    toast.innerHTML = `
      <svg class="w-4 h-4 text-indigo-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
      <span>${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 250);
    }, 2800);
  }

  return {
    init,
    setCategory,
    switchView,
    toggleTheme,
    openDrawer,
    closeDrawer,
    copyCitation,
    copyMarkdown,
    getPdfUrl,
    getOrgBadgeClass,
    showToast
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  window.App.init();
});
