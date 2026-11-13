/**
 * LMSYS Head-to-Head Model Comparison Module (Arena Diff)
 */

window.ArenaCompare = (function() {
  let allModels = [];
  let modelA = null;
  let modelB = null;

  const PRESETS = [
    ["DeepSeek-R1", "Claude Sonnet 4.5"],
    ["GPT-5.4 Thinking", "Gemini 3 Pro"],
    ["GLM-5", "Qwen3-Max"],
    ["LongCat-2.0", "Kimi K2.5"],
    ["MiniMax M2.5", "GPT-5.3-Codex"]
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

    selectA.innerHTML = '<option value="">Select a model</option>';
    selectB.innerHTML = '<option value="">Select a model</option>';

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

    if (presetsContainer) {
      presetsContainer.innerHTML = "";
      PRESETS.forEach(([nameA, nameB]) => {
        const left = allModels.find(model => model.model.toLowerCase() === nameA.toLowerCase());
        const right = allModels.find(model => model.model.toLowerCase() === nameB.toLowerCase());
        if (!left || !right) return;
        const btn = document.createElement("button");
        btn.style.cssText = "padding: 4px 12px; font-size: 12px; border-radius: 100px; background: rgba(234, 106, 16, 0.08); color: var(--orange); border: 1px solid rgba(234, 106, 16, 0.25); cursor: pointer; white-space: nowrap; font-weight: 500;";
        btn.textContent = `${left.model} vs ${right.model}`;
        btn.onclick = () => openCompareModal(left.id, right.id);
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

  function openCompareModal(idA, idB) {
    const modal = document.getElementById("arena-compare-modal");
    if (!modal) return;

    modal.style.display = "flex";

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
    if (modal) modal.style.display = "none";
  }

  function renderComparison() {
    const container = document.getElementById("compare-content-matrix");
    if (!container) return;

    if (!modelA || !modelB) {
      container.innerHTML = `
        <div style="text-align: center; padding: 48px 0; color: var(--ink-lighter);">
          <p style="font-size: 15px; font-weight: 500;">Select two models to compare their highlights and sources.</p>
        </div>
      `;
      return;
    }

    const escapeHtml = window.App.escapeHtml;
    const renderCard = (m, label, accentColor) => `
      <div style="padding: 24px; border-radius: 12px; border: 1px solid var(--border); background: var(--card-bg); display: flex; flex-direction: column; gap: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); padding-bottom: 12px;">
          <span style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: ${accentColor};">${label}</span>
          ${m.is_milestone ? '<span class="tl-badge">★ Milestone</span>' : ''}
        </div>
        
        <div>
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span class="tl-badge" style="background: rgba(8,12,38,0.06); color: var(--ink);">${escapeHtml(m.org)}</span>
            <span style="font-family: var(--font-mono); font-size: 12px; color: var(--ink-lighter);">${escapeHtml(m.date)}</span>
          </div>
          <h4 style="font-size: 20px; font-weight: 700; color: var(--ink);">${escapeHtml(m.model)}</h4>
        </div>

        <div>
          <h5 style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ink-lighter); letter-spacing: 0.05em; margin-bottom: 6px;">Topics</h5>
          <div style="display: flex; flex-wrap: wrap; gap: 4px;">
            ${m.tags.map(t => `<span class="table-tag">${escapeHtml(t)}</span>`).join('')}
          </div>
        </div>

        <div>
          <h5 style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--ink-lighter); letter-spacing: 0.05em; margin-bottom: 6px;">Highlights</h5>
          <p style="font-size: 13.5px; color: var(--ink-dim); line-height: 1.6; background: var(--card-hover-bg); padding: 14px; border-radius: 8px; border: 1px solid var(--border);">${escapeHtml(m.highlights || "No catalog excerpt available.")}</p>
        </div>

        <div style="display: flex; gap: 10px; margin-top: auto; padding-top: 10px;">
          <a href="${escapeHtml(window.App.officialUrl(m.link))}" target="_blank" rel="noopener noreferrer" style="padding: 8px 14px; font-size: 12px; font-weight: 600; border-radius: 6px; background: var(--orange); color: #fff; text-decoration: none;">
            ${window.App.documentLabel(m)} &rarr;
          </a>
          <a href="${window.App.getPdfUrl(m.file)}" ${m.file ? "" : "hidden"} target="_blank" rel="noopener noreferrer" style="padding: 8px 14px; font-size: 12px; font-weight: 600; border-radius: 6px; background: var(--card-hover-bg); border: 1px solid var(--border); color: var(--ink); text-decoration: none;">
            Archived PDF
          </a>
          <button onclick="window.App && window.App.copyCitation('${m.id}')" style="padding: 8px 14px; font-size: 12px; font-weight: 600; border-radius: 6px; background: none; border: 1px solid var(--border); color: var(--ink-dim); cursor: pointer;">
            Cite
          </button>
        </div>
      </div>
    `;

    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        ${renderCard(modelA, "Model A", "var(--orange)")}
        ${renderCard(modelB, "Model B", "#6366f1")}
      </div>
    `;
  }

  return {
    init,
    openCompareModal,
    closeCompareModal
  };
})();
