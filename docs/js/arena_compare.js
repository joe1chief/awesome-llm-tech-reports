/**
 * LMSYS Head-to-Head Model Comparison Module (Arena Diff)
 * Enables side-by-side technical report and specification comparison.
 */

window.ArenaCompare = (function() {
  let allModels = [];
  let modelA = null;
  let modelB = null;

  const PRESETS = [
    { name: "DeepSeek-R1 vs Claude Sonnet 4.5", a: "DeepSeek-R1", b: "Claude Sonnet 4.5" },
    { name: "GPT-5.4 Thinking vs Gemini 3 Pro", a: "GPT-5.4 Thinking", b: "Gemini 3 Pro" },
    { name: "GLM-5 vs Qwen3-Max", a: "GLM-5", b: "Qwen3-Max" },
    { name: "LongCat-2.0 vs Kimi K2.5", a: "LongCat-2.0", b: "Kimi K2.5" },
    { name: "MiniMax M2.5 vs GPT-5.3-Codex", a: "MiniMax M2.5", b: "GPT-5.3-Codex" }
  ];

  function init(models) {
    allModels = models;
    setupCompareModal();
  }

  function setupCompareModal() {
    const selectA = document.getElementById("compare-select-a");
    const selectB = document.getElementById("compare-select-b");
    const presetsContainer = document.getElementById("compare-presets");

    if (!selectA || !selectB) return;

    // Populate dropdowns
    selectA.innerHTML = '<option value="">-- Select Model A --</option>';
    selectB.innerHTML = '<option value="">-- Select Model B --</option>';

    allModels.forEach(m => {
      const optA = document.createElement("option");
      optA.value = m.id;
      optA.textContent = `[${m.date}] ${m.org} - ${m.model}`;
      selectA.appendChild(optA);

      const optB = document.createElement("option");
      optB.value = m.id;
      optB.textContent = `[${m.date}] ${m.org} - ${m.model}`;
      selectB.appendChild(optB);
    });

    // Populate presets
    if (presetsContainer) {
      presetsContainer.innerHTML = "";
      PRESETS.forEach(p => {
        const btn = document.createElement("button");
        btn.className = "px-3 py-1 text-xs rounded-full bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 transition-all cursor-pointer";
        btn.textContent = p.name;
        btn.onclick = () => loadPreset(p.a, p.b);
        presetsContainer.appendChild(btn);
      });
    }

    selectA.onchange = (e) => {
      modelA = allModels.find(m => m.id === e.target.value) || null;
      renderComparison();
    };

    selectB.onchange = (e) => {
      modelB = allModels.find(m => m.id === e.target.value) || null;
      renderComparison();
    };
  }

  function loadPreset(nameA, nameB) {
    const mA = allModels.find(m => m.model.toLowerCase().includes(nameA.toLowerCase()));
    const mB = allModels.find(m => m.model.toLowerCase().includes(nameB.toLowerCase()));

    if (mA && mB) {
      openCompareModal(mA.id, mB.id);
    }
  }

  function openCompareModal(idA, idB) {
    const modal = document.getElementById("arena-compare-modal");
    if (!modal) return;

    modal.classList.remove("hidden");
    modal.classList.add("flex");

    const selectA = document.getElementById("compare-select-a");
    const selectB = document.getElementById("compare-select-b");

    if (idA) {
      modelA = allModels.find(m => m.id === idA) || null;
      if (selectA) selectA.value = idA;
    } else if (!modelA && allModels.length > 0) {
      modelA = allModels[0];
      if (selectA) selectA.value = modelA.id;
    }

    if (idB) {
      modelB = allModels.find(m => m.id === idB) || null;
      if (selectB) selectB.value = idB;
    } else if (!modelB && allModels.length > 1) {
      modelB = allModels[1];
      if (selectB) selectB.value = modelB.id;
    }

    renderComparison();
  }

  function closeCompareModal() {
    const modal = document.getElementById("arena-compare-modal");
    if (modal) {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }
  }

  function renderComparison() {
    const container = document.getElementById("compare-content-matrix");
    if (!container) return;

    if (!modelA || !modelB) {
      container.innerHTML = `
        <div class="text-center py-16 text-gray-400">
          <svg class="w-12 h-12 mx-auto mb-3 opacity-40 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
          <p class="text-base font-medium">Select both Model A and Model B above to compare their technical reports.</p>
        </div>
      `;
      return;
    }

    const getOrgBadge = (org) => {
      const cls = window.App ? window.App.getOrgBadgeClass(org) : "badge-default";
      return `<span class="px-2.5 py-1 text-xs font-semibold rounded-md ${cls}">${org}</span>`;
    };

    const renderCard = (m, label) => `
      <div class="glass-panel p-5 rounded-xl border flex-1 space-y-4">
        <div class="flex items-center justify-between border-b border-white/10 pb-3">
          <span class="text-xs font-bold uppercase tracking-wider text-indigo-400">${label}</span>
          ${m.is_milestone ? '<span class="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">★ Milestone</span>' : ''}
        </div>
        
        <div>
          <div class="flex items-center gap-2 mb-1.5">
            ${getOrgBadge(m.org)}
            <span class="text-xs text-gray-400 font-mono">${m.date}</span>
          </div>
          <h4 class="text-xl font-bold text-white">${m.model}</h4>
        </div>

        <div>
          <h5 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Capabilities & Modalities</h5>
          <div class="flex flex-wrap gap-1.5">
            ${m.tags.map(t => `<span class="px-2 py-0.5 text-xs rounded bg-white/5 text-gray-300 border border-white/10">${t}</span>`).join('')}
          </div>
        </div>

        <div>
          <h5 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Key Technical Highlights</h5>
          <p class="text-sm text-gray-300 leading-relaxed bg-black/30 p-3 rounded-lg border border-white/5 font-sans">${m.highlights}</p>
        </div>

        <div class="pt-2 flex flex-wrap gap-2">
          <a href="${m.link}" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors inline-flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
            Official Paper
          </a>
          <a href="${window.App ? window.App.getPdfUrl(m.file) : m.file}" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 text-gray-200 transition-colors inline-flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
            View Local PDF
          </a>
          <button onclick="window.App && window.App.copyCitation('${m.id}')" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white/5 hover:bg-white/15 text-gray-300 transition-colors inline-flex items-center gap-1.5 cursor-pointer">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
            Cite
          </button>
        </div>
      </div>
    `;

    container.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        ${renderCard(modelA, "Model A")}
        ${renderCard(modelB, "Model B")}
      </div>
    `;
  }

  return {
    init,
    openCompareModal,
    closeCompareModal,
    loadPreset
  };
})();
