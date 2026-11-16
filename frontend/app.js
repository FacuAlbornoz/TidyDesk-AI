// TidyDesk AI - Frontend Controller (v1.1)

let currentFolderType = "desktop";
let currentCustomFolderPath = "";
let guardianCustomFolderPath = "";
let currentTargetFolder = "";
let scannedFiles = [];
let currentPlan = [];
let currentRules = [];
let defaultFolders = {};

// Inicialización al cargar la página
document.addEventListener("DOMContentLoaded", async () => {
  loadSavedGeminiKey();
  await checkHealth();
  await loadRules();
  await loadHistory();
  await loadGuardianStatus();
  await loadOllamaSetupStatus();
  setInterval(loadGuardianStatus, 3000);
});

// Guardar y cargar Gemini API Key en LocalStorage
function loadSavedGeminiKey() {
  const savedKey = localStorage.getItem("tidydesk_gemini_key");
  if (savedKey) {
    const input = document.getElementById("input-gemini-key");
    if (input) input.value = savedKey;
  }
}

function saveGeminiKey() {
  const input = document.getElementById("input-gemini-key");
  if (input) {
    localStorage.setItem("tidydesk_gemini_key", input.value.trim());
    showToast("Clave guardada", "La API Key de Gemini se guardó localmente en tu navegador.");
  }
}

// 1. Verificación de Salud y Detección de Proveedores
async function checkHealth() {
  const statusPill = document.getElementById("ollama-status-pill");
  const dot = document.getElementById("ollama-dot");
  const text = document.getElementById("ollama-text");
  const selectModels = document.getElementById("select-ollama-model");

  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error("Backend inaccesible");
    const data = await res.json();

    defaultFolders = data.default_folders || {};
    document.getElementById("path-preview-desktop").innerText = defaultFolders.desktop || "Escritorio";
    document.getElementById("path-preview-downloads").innerText = defaultFolders.downloads || "Descargas";
    currentTargetFolder = defaultFolders.desktop;

    // Estado de Ollama
    statusPill.classList.remove("hidden");
    if (data.providers?.ollama?.available) {
      dot.className = "w-2 h-2 rounded-full bg-emerald-400";
      text.innerText = "Ollama: Conectado";

      // Poblar modelos de Ollama si hay
      if (selectModels && data.providers.ollama.models?.length > 0) {
        selectModels.innerHTML = "";
        data.providers.ollama.models.forEach((model) => {
          const opt = document.createElement("option");
          opt.value = model;
          opt.textContent = model;
          selectModels.appendChild(opt);
        });
      }
    } else {
      dot.className = "w-2 h-2 rounded-full bg-amber-400";
      text.innerText = "Ollama: Inactivo (usará Reglas o Gemini)";
    }
  } catch (err) {
    console.error("Error al conectar con backend:", err);
    if (dot) dot.className = "w-2 h-2 rounded-full bg-rose-500";
    if (text) text.innerText = "Backend desconectado";
  }
}

// 2. Navegación por Pestañas (Organizador / Guardián / Limpiador / Reglas / Historial)
function switchTab(tab) {
  const viewOrganizer = document.getElementById("view-organizer");
  const viewGuardian = document.getElementById("view-guardian");
  const viewCleaner = document.getElementById("view-cleaner");
  const viewRules = document.getElementById("view-rules");
  const viewHistory = document.getElementById("view-history");
  
  const btnOrganizer = document.getElementById("tab-organizer-btn");
  const btnGuardian = document.getElementById("tab-guardian-btn");
  const btnCleaner = document.getElementById("tab-cleaner-btn");
  const btnRules = document.getElementById("tab-rules-btn");
  const btnHistory = document.getElementById("tab-history-btn");

  // Ocultar todas las vistas
  viewOrganizer.classList.add("hidden");
  if (viewGuardian) viewGuardian.classList.add("hidden");
  if (viewCleaner) viewCleaner.classList.add("hidden");
  viewRules.classList.add("hidden");
  viewHistory.classList.add("hidden");

  // Estilos inactivos
  btnOrganizer.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all";
  if (btnGuardian) btnGuardian.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all flex items-center gap-1.5";
  if (btnCleaner) btnCleaner.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all flex items-center gap-1.5";
  btnRules.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all flex items-center gap-1.5";
  btnHistory.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all flex items-center gap-1.5";

  if (tab === "organizer") {
    viewOrganizer.classList.remove("hidden");
    btnOrganizer.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all";
  } else if (tab === "guardian") {
    if (viewGuardian) viewGuardian.classList.remove("hidden");
    if (btnGuardian) btnGuardian.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all flex items-center gap-1.5";
    loadGuardianStatus();
  } else if (tab === "cleaner") {
    if (viewCleaner) viewCleaner.classList.remove("hidden");
    if (btnCleaner) btnCleaner.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all flex items-center gap-1.5";
  } else if (tab === "rules") {
    viewRules.classList.remove("hidden");
    btnRules.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all flex items-center gap-1.5";
    loadRules();
  } else if (tab === "history") {
    viewHistory.classList.remove("hidden");
    btnHistory.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all flex items-center gap-1.5";
    loadHistory();
  }
}

// 3. Selección de Carpeta (Escritorio / Descargas / Otra Carpeta Personalizada)
function selectFolder(type) {
  currentFolderType = type;
  const btnDesktop = document.getElementById("btn-folder-desktop");
  const btnDownloads = document.getElementById("btn-folder-downloads");
  const btnCustom = document.getElementById("btn-folder-custom");

  const inactiveCard = "folder-select-btn p-4 rounded-xl border border-gray-800 bg-gray-800/40 text-left hover:border-gray-700 transition-all";
  const activeCard = "folder-select-btn active p-4 rounded-xl border-2 border-brand-500 bg-brand-500/10 text-left transition-all";

  if (btnDesktop) btnDesktop.className = type === "desktop" ? activeCard : inactiveCard;
  if (btnDownloads) btnDownloads.className = type === "downloads" ? activeCard : inactiveCard;
  if (btnCustom) {
    btnCustom.className =
      type === "custom"
        ? "folder-select-btn active w-full p-3.5 rounded-xl border-2 border-brand-500 bg-brand-500/10 text-left transition-all flex items-center justify-between gap-2"
        : "folder-select-btn w-full p-3.5 rounded-xl border border-gray-800 bg-gray-800/40 hover:border-brand-500/50 text-left transition-all flex items-center justify-between gap-2";
  }

  if (type === "desktop") {
    currentTargetFolder = defaultFolders.desktop || "";
  } else if (type === "downloads") {
    currentTargetFolder = defaultFolders.downloads || "";
  } else if (type === "custom" && currentCustomFolderPath) {
    currentTargetFolder = currentCustomFolderPath;
  }

  hideAllStates();
}

async function pickCustomFolderToOrganize() {
  try {
    const res = await fetch("/api/system/pick-folder?title=Seleccionar+carpeta+a+organizar");
    if (!res.ok) throw new Error("No se pudo abrir el selector de carpetas");
    const data = await res.json();
    if (data.selected && data.path) {
      currentCustomFolderPath = data.path;
      const previewEl = document.getElementById("path-preview-custom");
      if (previewEl) {
        previewEl.innerText = data.path;
        previewEl.className = "text-[11px] text-brand-300 font-mono truncate block";
      }
      selectFolder("custom");
      showToast("Carpeta Seleccionada", `Listo para auditar: ${data.path}`);
    }
  } catch (err) {
    showToast("Error al elegir carpeta", err.message, "error");
  }
}

function onShortcutsToggleChange() {
  hideAllStates();
}

// 4. Cambio de Proveedor de IA
function onProviderChange() {
  const provider = document.getElementById("select-ai-provider").value;
  const ollamaOpts = document.getElementById("ollama-options");
  const geminiOpts = document.getElementById("gemini-options");

  if (provider === "ollama") {
    ollamaOpts.classList.remove("hidden");
    geminiOpts.classList.add("hidden");
  } else if (provider === "gemini") {
    ollamaOpts.classList.add("hidden");
    geminiOpts.classList.remove("hidden");
  } else {
    ollamaOpts.classList.add("hidden");
    geminiOpts.classList.add("hidden");
  }
}

// 5. Gestión de los 4 Estados UI
function hideAllStates() {
  document.getElementById("state-loading").classList.add("hidden");
  document.getElementById("state-empty").classList.add("hidden");
  document.getElementById("state-error").classList.add("hidden");
  document.getElementById("state-plan").classList.add("hidden");
}

function showLoading(title, subtitle) {
  hideAllStates();
  document.getElementById("loading-title").innerText = title;
  document.getElementById("loading-subtitle").innerText = subtitle;
  document.getElementById("state-loading").classList.remove("hidden");
}

function showError(title, message) {
  hideAllStates();
  document.getElementById("error-title").innerText = title;
  document.getElementById("error-message").innerText = message;
  document.getElementById("state-error").classList.remove("hidden");
}

function showEmpty() {
  hideAllStates();
  document.getElementById("state-empty").classList.remove("hidden");
}

// 6. Proceso Principal: Escaneo + Plan de IA y Reglas (Dry-Run)
async function startScanAndPlan() {
  showLoading("Escaneando archivos...", "Revisando elementos y aplicando guardas de seguridad.");

  try {
    const includeShortcuts = document.getElementById("toggle-include-shortcuts")?.checked || false;

    // Paso A: Escanear directorio
    const scanRes = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        folder_type: currentFolderType,
        custom_path: currentFolderType === "custom" ? currentCustomFolderPath : null,
        include_shortcuts: includeShortcuts
      }),
    });

    if (!scanRes.ok) {
      const err = await scanRes.json();
      throw new Error(err.detail || "Fallo en el escaneo");
    }

    const scanData = await scanRes.json();
    currentTargetFolder = scanData.target_folder;
    scannedFiles = scanData.files || [];

    if (scannedFiles.length === 0) {
      showEmpty();
      return;
    }

    // Paso B: Generar Plan
    showLoading(
      "Analizando archivos...",
      `Evaluando ${scannedFiles.length} archivos con tus Reglas Personalizadas y el motor de IA.`
    );

    const provider = document.getElementById("select-ai-provider").value;
    const model = provider === "ollama" ? document.getElementById("select-ollama-model").value : null;
    const apiKey = provider === "gemini" ? document.getElementById("input-gemini-key").value : null;
    const enableSmartRename = document.getElementById("toggle-smart-rename")?.checked ?? true;

    const planRes = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_folder: currentTargetFolder,
        provider: provider,
        model: model,
        api_key: apiKey,
        files: scannedFiles,
        enable_smart_rename: enableSmartRename,
      }),
    });

    if (!planRes.ok) {
      const err = await planRes.json();
      throw new Error(err.detail || "Error al clasificar archivos");
    }

    const planData = await planRes.json();
    currentPlan = planData.items || [];

    // Renderizar la tabla de Dry-Run
    renderPlanTable();
    hideAllStates();
    document.getElementById("state-plan").classList.remove("hidden");
    updateSelectionCounter();

  } catch (err) {
    showError("Inconveniente en la auditoría", err.message);
  }
}

// 7. Renderizado de la Tabla de Dry-Run
function renderPlanTable() {
  const tbody = document.getElementById("plan-table-body");
  tbody.innerHTML = "";

  const fileMap = new Map(scannedFiles.map((f) => [f.id, f]));

  currentPlan.forEach((item, index) => {
    const file = fileMap.get(item.file_id) || {};
    const tr = document.createElement("tr");
    tr.className = "hover:bg-gray-800/40 transition-colors";

    // Icono contextual
    let fileIcon = "📄";
    const nameLower = item.original_name.toLowerCase();
    const isCustomRule = item.reason.includes("⭐");

    if (nameLower.endsWith(".lnk") || nameLower.endsWith(".url")) {
      if (item.suggested_folder.includes("Juegos")) fileIcon = "🎮";
      else if (item.suggested_folder.includes("Desarrollo")) fileIcon = "💻";
      else if (item.suggested_folder.includes("Diseno") || item.suggested_folder.includes("Diseño")) fileIcon = "🎨";
      else if (item.suggested_folder.includes("Navegadores")) fileIcon = "🌐";
      else if (item.suggested_folder.includes("Multimedia")) fileIcon = "🎧";
      else fileIcon = "🔗";
    } else if (nameLower.endsWith(".stl") || nameLower.endsWith(".gcode") || nameLower.endsWith(".3mf")) {
      fileIcon = "🖨️";
    } else if (nameLower.endsWith(".exe")) {
      fileIcon = "⚙️";
    } else if (nameLower.endsWith(".pdf")) {
      fileIcon = "📕";
    } else if (isCustomRule) {
      fileIcon = "⭐";
    }

    const isRenamed = item.suggested_name && item.suggested_name.toLowerCase() !== item.original_name.toLowerCase();

    tr.innerHTML = `
      <td class="py-3 px-4 text-center">
        <input type="checkbox" ${item.selected ? "checked" : ""} 
               onchange="toggleItemSelection(${index}, this.checked)"
               class="rounded bg-gray-700 border-gray-600 text-brand-600 focus:ring-0 cursor-pointer" />
      </td>
      <td class="py-3 px-4">
        <div class="font-medium text-white break-all flex items-center gap-2">
          <span>${fileIcon}</span>
          <span>${item.original_name}</span>
        </div>
        <div class="text-[10px] text-gray-500">${file.modified_at || ""}</div>
      </td>
      <td class="py-3 px-4">
        <div class="flex items-center gap-1.5">
          <span class="text-xs ${isCustomRule ? 'text-amber-400' : 'text-brand-400'}">📁</span>
          <input type="text" value="${item.suggested_folder}" 
                 onchange="updateSuggestedFolder(${index}, this.value)"
                 class="bg-gray-800/80 border ${isCustomRule ? 'border-amber-500/50 text-amber-200' : 'border-gray-700 text-white'} rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-brand-500 w-44 sm:w-56" />
        </div>
      </td>
      <td class="py-3 px-4">
        <div class="space-y-1">
          <div class="flex items-center gap-1.5">
            <span class="text-xs ${isRenamed ? 'text-purple-400' : 'text-gray-500'}">✏️</span>
            <input type="text" value="${item.suggested_name}" 
                   onchange="updateSuggestedName(${index}, this.value)"
                   class="bg-gray-800/80 border ${isRenamed ? 'border-purple-500/60 text-purple-200 font-medium' : 'border-gray-700 text-gray-300'} rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-brand-500 w-48 sm:w-60" />
          </div>
          ${isRenamed ? '<div class="text-[10px] text-purple-300 flex items-center gap-1"><span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span> Renombrado por IA</div>' : ''}
        </div>
      </td>
      <td class="py-3 px-4">
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md ${isCustomRule ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 font-semibold' : 'bg-gray-800 border border-gray-700 text-gray-300'} text-[11px]">
          ${isCustomRule ? item.reason : '💡 ' + item.reason}
        </span>
      </td>
      <td class="py-3 px-4 text-right font-mono text-[11px] text-gray-400">
        ${file.size_formatted || "-"}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateSuggestedName(index, newName) {
  if (currentPlan[index]) {
    currentPlan[index].suggested_name = newName.trim();
  }
}

function toggleItemSelection(index, selected) {
  if (currentPlan[index]) {
    currentPlan[index].selected = selected;
    updateSelectionCounter();
  }
}

function toggleSelectAll(checked) {
  currentPlan.forEach((item) => (item.selected = checked));
  renderPlanTable();
  updateSelectionCounter();
}

function updateSuggestedFolder(index, folder) {
  if (currentPlan[index]) {
    currentPlan[index].suggested_folder = folder.trim();
  }
}

function updateSelectionCounter() {
  const selectedCount = currentPlan.filter((p) => p.selected).length;
  const countLabel = document.getElementById("plan-selection-count");
  if (countLabel) {
    countLabel.innerText = `${selectedCount} de ${currentPlan.length} seleccionados`;
  }
  const btnExecute = document.getElementById("btn-execute");
  if (btnExecute) {
    btnExecute.disabled = selectedCount === 0;
    btnExecute.style.opacity = selectedCount === 0 ? "0.5" : "1";
  }
}

// 8. Confirmación y Ejecución de Movimientos
async function executeCurrentPlan() {
  const selectedItems = currentPlan.filter((p) => p.selected);
  if (selectedItems.length === 0) {
    showToast("Aviso", "No hay archivos seleccionados para organizar.", "warning");
    return;
  }

  const confirmed = confirm(
    `¿Deseas organizar ${selectedItems.length} archivos ahora?\n\nTranquilo: Todo queda registrado y podrás deshacer los cambios en cualquier momento desde la pestaña de Historial.`
  );
  if (!confirmed) return;

  showLoading("Organizando tus archivos...", "Moviendo elementos a sus carpetas de destino.");

  try {
    const res = await fetch("/api/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_folder: currentTargetFolder,
        items: selectedItems,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error al ejecutar organización");
    }

    const data = await res.json();
    if (data.errors && data.errors.length > 0) {
      showToast(
        "Atención con algunos archivos",
        `Se movieron ${data.moved_count} archivos, pero ${data.errors.length} no pudieron moverse (ej: archivo en uso o bloqueado).`,
        "warning"
      );
    } else {
      showToast(
        "¡Organización Completada!",
        `Se movieron ${data.moved_count} archivos con éxito. Guardado en transacción ${data.transaction_id.slice(-6)}.`
      );
    }

    await loadHistory();
    await startScanAndPlan();

  } catch (err) {
    showError("Fallo al organizar", err.message);
  }
}

// 9. Gestión de Reglas Personalizadas (V1.1)
async function loadRules() {
  try {
    const res = await fetch("/api/rules");
    if (!res.ok) return;
    currentRules = await res.json();
    
    const badge = document.getElementById("rules-badge");
    if (badge) {
      badge.innerText = currentRules.length;
    }
    renderRulesList();
  } catch (err) {
    console.error("Error al cargar reglas:", err);
  }
}

function renderRulesList() {
  const container = document.getElementById("rules-list");
  const empty = document.getElementById("rules-empty");
  if (!container) return;
  container.innerHTML = "";

  if (currentRules.length === 0) {
    if (empty) empty.classList.remove("hidden");
    return;
  }
  if (empty) empty.classList.add("hidden");

  currentRules.forEach((rule) => {
    const card = document.createElement("div");
    card.className = "bg-gray-900/90 border border-gray-800 rounded-2xl p-5 shadow-lg space-y-3";
    
    card.innerHTML = `
      <div class="flex items-center justify-between border-b border-gray-800 pb-3">
        <div class="flex items-center gap-2">
          <span class="text-sm">⭐</span>
          <h4 class="text-sm font-bold text-white">${rule.name}</h4>
          <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${rule.enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-gray-700 text-gray-400'}">
            ${rule.enabled ? 'Activa' : 'Pausada'}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="p-1.5 rounded-lg text-xs ${rule.enabled ? 'text-amber-400 hover:bg-amber-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'}" title="${rule.enabled ? 'Pausar regla' : 'Activar regla'}" onclick="toggleCustomRule('${rule.id}')">
            ${rule.enabled ? '⏸' : '▶'}
          </button>
          <button type="button" class="p-1.5 rounded-lg text-xs text-rose-400 hover:bg-rose-500/10" title="Eliminar regla" onclick="deleteCustomRule('${rule.id}')">
            🗑
          </button>
        </div>
      </div>

      <div class="space-y-2 text-xs">
        <div>
          <span class="text-gray-400 text-[11px] block">Patrones (${rule.pattern_type === 'extension' ? 'Extensiones' : 'Palabras clave'}):</span>
          <div class="flex flex-wrap gap-1 mt-1">
            ${rule.patterns.map(p => `<span class="bg-gray-800 border border-gray-700 px-2 py-0.5 rounded font-mono text-[11px] text-brand-300">${p}</span>`).join('')}
          </div>
        </div>
        <div>
          <span class="text-gray-400 text-[11px] block">Destino de la regla:</span>
          <span class="font-mono text-white text-[11px] bg-gray-800/60 px-2 py-1 rounded block truncate mt-0.5 border border-gray-700/60">
            📁 ${rule.destination_path}
          </span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function toggleNewRuleModal(show) {
  const card = document.getElementById("new-rule-card");
  if (card) {
    card.classList.toggle("hidden", !show);
  }
}

function setQuickDest(path) {
  const input = document.getElementById("rule-input-dest");
  if (input) input.value = path;
}

async function saveNewRule() {
  const name = document.getElementById("rule-input-name").value.trim();
  const type = document.getElementById("rule-input-type").value;
  const rawPatterns = document.getElementById("rule-input-patterns").value;
  const dest = document.getElementById("rule-input-dest").value.trim();

  if (!name || !rawPatterns || !dest) {
    showToast("Faltan datos", "Completa el nombre, patrones y carpeta de destino.", "warning");
    return;
  }

  const patterns = rawPatterns.split(",").map(p => p.trim()).filter(Boolean);

  try {
    const res = await fetch("/api/rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        pattern_type: type,
        patterns: patterns,
        destination_path: dest,
        enabled: true
      })
    });

    if (!res.ok) throw new Error("Error al guardar regla");
    showToast("Regla creada", `Se guardó la regla "${name}" con éxito.`);
    toggleNewRuleModal(false);
    
    // Limpiar campos
    document.getElementById("rule-input-name").value = "";
    document.getElementById("rule-input-patterns").value = "";
    document.getElementById("rule-input-dest").value = "";

    await loadRules();
  } catch (err) {
    showToast("Error", err.message, "error");
  }
}

async function deleteCustomRule(ruleId) {
  if (!confirm("¿Deseas eliminar esta regla personalizada?")) return;
  try {
    const res = await fetch(`/api/rules/${ruleId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("No se pudo eliminar la regla");
    showToast("Regla eliminada", "La regla fue quitada con éxito.");
    await loadRules();
  } catch (err) {
    showToast("Error", err.message, "error");
  }
}

async function toggleCustomRule(ruleId) {
  try {
    const res = await fetch(`/api/rules/${ruleId}/toggle`, { method: "POST" });
    if (!res.ok) throw new Error("No se pudo cambiar estado");
    await loadRules();
  } catch (err) {
    showToast("Error", err.message, "error");
  }
}

// 10. Historial y Rollback (Undo)
async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) return;
    const data = await res.json();
    const transactions = data.transactions || [];

    const badge = document.getElementById("history-badge");
    if (badge) {
      badge.innerText = transactions.length;
      badge.classList.toggle("hidden", transactions.length === 0);
    }

    const list = document.getElementById("history-list");
    const emptyState = document.getElementById("history-empty");

    if (!list) return;
    list.innerHTML = "";

    if (transactions.length === 0) {
      if (emptyState) emptyState.classList.remove("hidden");
      return;
    }
    if (emptyState) emptyState.classList.add("hidden");

    transactions.forEach((tx) => {
      const card = document.createElement("div");
      card.className = "bg-gray-900/90 border border-gray-800 rounded-2xl p-5 shadow-lg space-y-3";

      const isReverted = tx.reverted;
      card.innerHTML = `
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-gray-800 pb-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono bg-gray-800 text-gray-300 px-2 py-0.5 rounded border border-gray-700">${tx.transaction_id}</span>
              ${isReverted ? '<span class="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full font-bold">REVERTIDO (DESHECHO)</span>' : '<span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full font-bold">ACTIVO</span>'}
            </div>
            <p class="text-xs text-gray-400 mt-1">${tx.timestamp} • ${tx.moves?.length || 0} archivos organizados</p>
          </div>
          ${
            !isReverted
              ? `<button type="button" class="px-4 py-2 rounded-xl bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/30 text-xs font-bold transition-all flex items-center gap-1.5" onclick="triggerRollback('${tx.transaction_id}')">
                  <span>↩ Deshacer Lote</span>
                 </button>`
              : '<span class="text-xs text-gray-500 italic">Cambios ya restaurados</span>'
          }
        </div>
        <div class="text-xs text-gray-400 space-y-1">
          <p class="font-semibold text-gray-300 text-[11px] uppercase tracking-wider">Detalle de movimientos:</p>
          <ul class="list-disc list-inside space-y-0.5 max-h-32 overflow-y-auto pr-2">
            ${(tx.moves || [])
              .map(
                (m) =>
                  `<li class="truncate"><span class="text-white">${m.file_name}</span> &rarr; <span class="text-brand-300">${m.new_path}</span></li>`
              )
              .join("")}
          </ul>
        </div>
      `;
      list.appendChild(card);
    });

  } catch (err) {
    console.error("Error al cargar historial:", err);
  }
}

async function triggerRollback(txId) {
  const confirmed = confirm("¿Estás seguro de deshacer esta organización?\nTodos los archivos volverán exactamente a donde estaban.");
  if (!confirmed) return;

  try {
    const res = await fetch("/api/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transaction_id: txId }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error al revertir");
    }

    const data = await res.json();
    showToast("Reversión exitosa", `Se restauraron ${data.restored_count} archivos a su ubicación original.`);
    await loadHistory();

  } catch (err) {
    showToast("Error en reversión", err.message, "error");
  }
}

// 11. Sistema de Toast Notifications
function showToast(title, message, type = "success") {
  const toast = document.getElementById("toast");
  const tTitle = document.getElementById("toast-title");
  const tMessage = document.getElementById("toast-message");
  const tIcon = document.getElementById("toast-icon");

  if (!toast) return;

  tTitle.innerText = title;
  tMessage.innerText = message;

  if (type === "warning") {
    tIcon.className = "w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0";
    tIcon.innerText = "⚠";
  } else if (type === "error") {
    tIcon.className = "w-8 h-8 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0";
    tIcon.innerText = "✕";
  } else {
    tIcon.className = "w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0";
    tIcon.innerText = "✓";
  }

  toast.classList.remove("translate-y-20", "opacity-0");
  toast.classList.add("translate-y-0", "opacity-100");

  setTimeout(() => {
    toast.classList.add("translate-y-20", "opacity-0");
    toast.classList.remove("translate-y-0", "opacity-100");
  }, 4000);
}

// ==========================================
// 12. LIMPIADOR INTELIGENTE & DUPLICADOS (V1.2)
// ==========================================
let cleanerAuditData = null;
let selectedCleanerIds = new Set();

async function startCleanerAudit() {
  const btn = document.getElementById("btn-audit-cleaner");
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="animate-spin inline-block mr-1">🌀</span> Auditando...`;

  try {
    const res = await fetch("/api/cleaner/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_type: currentFolderType,
        custom_path: currentFolderType === "custom" ? currentCustomFolderPath : null,
      }),
    });

    if (!res.ok) throw new Error("Fallo en la auditoría de limpieza");
    cleanerAuditData = await res.json();
    renderCleanerResults();
    showToast(
      "Auditoría Completa",
      `Se encontraron ${cleanerAuditData.total_duplicates_count} duplicados y ${cleanerAuditData.old_installers.length} instaladores antiguos.`
    );
  } catch (err) {
    showToast("Error en Limpiador", err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

function renderCleanerResults() {
  if (!cleanerAuditData) return;

  selectedCleanerIds.clear();

  // Actualizar Métricas
  document.getElementById("cleaner-metrics").classList.remove("hidden");
  document.getElementById("cleaner-empty").classList.add("hidden");
  document.getElementById("cleaner-results").classList.remove("hidden");
  document.getElementById("cleaner-action-bar").classList.remove("hidden");

  document.getElementById("metric-recoverable-space").innerText = cleanerAuditData.total_recoverable_formatted;
  document.getElementById("metric-duplicates-count").innerText = cleanerAuditData.total_duplicates_count;
  document.getElementById("metric-duplicates-waste").innerText = `Desperdicio: ${cleanerAuditData.duplicates_waste_formatted}`;
  document.getElementById("metric-installers-count").innerText = cleanerAuditData.old_installers.length;
  document.getElementById("metric-installers-waste").innerText = `Ocupación: ${cleanerAuditData.total_old_installers_formatted}`;

  // Renderizar Duplicados
  const dupContainer = document.getElementById("cleaner-duplicates-list");
  dupContainer.innerHTML = "";
  if (cleanerAuditData.duplicate_groups.length === 0) {
    dupContainer.innerHTML = `<div class="p-4 rounded-xl bg-gray-900 border border-gray-800 text-xs text-emerald-400">✨ No se detectaron archivos duplicados idénticos por SHA-256.</div>`;
  } else {
    cleanerAuditData.duplicate_groups.forEach((group) => {
      const div = document.createElement("div");
      div.className = "bg-gray-900/90 border border-gray-800 rounded-2xl p-4 shadow-lg space-y-2";
      
      // Marcar duplicados por defecto
      group.duplicates.forEach(d => selectedCleanerIds.add(d.id));

      div.innerHTML = `
        <div class="flex items-center justify-between text-xs border-b border-gray-800 pb-2">
          <div class="flex items-center gap-2">
            <span class="text-emerald-400 font-bold">📄 Original:</span>
            <span class="text-white font-medium">${group.original.name}</span>
          </div>
          <span class="font-mono text-gray-400">${group.size_formatted}</span>
        </div>
        <div class="space-y-1.5 pt-1">
          <span class="text-[11px] text-amber-400 font-semibold">Copias repetidas detectadas (${group.duplicates.length}):</span>
          <div class="space-y-1">
            ${group.duplicates.map(d => `
              <label class="flex items-center justify-between p-2 rounded-lg bg-gray-800/60 hover:bg-gray-800 border border-gray-700/60 text-xs cursor-pointer">
                <div class="flex items-center gap-2">
                  <input type="checkbox" checked onchange="toggleCleanerItem('${d.id}', this.checked)" class="rounded bg-gray-700 border-gray-600 text-rose-600 focus:ring-0 cursor-pointer" />
                  <span class="text-gray-300">${d.name}</span>
                </div>
                <span class="text-[10px] text-rose-300 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">Duplicado</span>
              </label>
            `).join('')}
          </div>
        </div>
      `;
      dupContainer.appendChild(div);
    });
  }

  // Renderizar Instaladores Antiguos
  const instContainer = document.getElementById("cleaner-installers-list");
  instContainer.innerHTML = "";
  if (cleanerAuditData.old_installers.length === 0) {
    instContainer.innerHTML = `<div class="p-4 rounded-xl bg-gray-900 border border-gray-800 text-xs text-emerald-400 col-span-2">✨ No hay instaladores viejos huérfanos (>30 días).</div>`;
  } else {
    cleanerAuditData.old_installers.forEach((item) => {
      const div = document.createElement("div");
      div.className = "bg-gray-900/90 border border-gray-800 rounded-2xl p-4 shadow-lg flex items-center justify-between text-xs";
      
      div.innerHTML = `
        <div class="flex items-center gap-2.5">
          <input type="checkbox" onchange="toggleCleanerItem('${item.file.id}', this.checked)" class="rounded bg-gray-700 border-gray-600 text-amber-600 focus:ring-0 cursor-pointer" />
          <div>
            <p class="font-medium text-white truncate max-w-xs">${item.file.name}</p>
            <p class="text-[10px] text-gray-500">Modificado hace ${item.days_old} días</p>
          </div>
        </div>
        <span class="font-mono text-gray-300">${item.file.size_formatted}</span>
      `;
      instContainer.appendChild(div);
    });
  }

  updateCleanerSelectedCount();
}

function toggleCleanerItem(id, checked) {
  if (checked) {
    selectedCleanerIds.add(id);
  } else {
    selectedCleanerIds.delete(id);
  }
  updateCleanerSelectedCount();
}

function updateCleanerSelectedCount() {
  const el = document.getElementById("cleaner-selected-count");
  if (el) el.innerText = selectedCleanerIds.size;
  const btn = document.getElementById("btn-execute-clean");
  if (btn) {
    btn.disabled = selectedCleanerIds.size === 0;
    btn.style.opacity = selectedCleanerIds.size === 0 ? "0.5" : "1";
  }
}

async function executeCleanerAction() {
  if (selectedCleanerIds.size === 0) return;

  const confirmed = confirm(
    `¿Limpiar ${selectedCleanerIds.size} archivos seleccionados?\n\nSe moverán de forma segura a la subcarpeta '_Limpieza_TidyDesk' y podrás recuperarlos en cualquier momento desde Historial.`
  );
  if (!confirmed) return;

  showLoading("Limpiando archivos...", "Moviendo duplicados e instaladores seleccionados de forma segura.");

  try {
    const res = await fetch("/api/cleaner/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_folder: currentTargetFolder,
        file_ids_to_clean: Array.from(selectedCleanerIds),
        destination_action: "archive",
      }),
    });

    if (!res.ok) throw new Error("Fallo al ejecutar limpieza");
    const data = await res.json();

    showToast(
      "Limpieza Exitosa",
      `Se limpiaron ${data.cleaned_count} archivos, recuperando ${data.freed_space_formatted}. Guardado para Rollback.`
    );

    await loadHistory();
    await startCleanerAudit();
  } catch (err) {
    showError("Fallo en limpieza", err.message);
  }
}

// ==========================================
// 11. MODO GUARDIÁN EN SEGUNDO PLANO (V1.4)
// ==========================================
let guardianRunning = false;

async function loadGuardianStatus() {
  try {
    const res = await fetch("/api/guardian/status");
    if (!res.ok) return;
    const status = await res.json();
    renderGuardianUI(status);
  } catch (err) {
    console.error("Error al consultar Guardián:", err);
  }
}

function renderGuardianUI(status) {
  guardianRunning = Boolean(status.running);

  const navDot = document.getElementById("guardian-nav-dot");
  const statusDot = document.getElementById("guardian-status-dot");
  const statusText = document.getElementById("guardian-status-text");
  const heroCard = document.getElementById("guardian-hero-card");
  const btnToggle = document.getElementById("btn-toggle-guardian");
  const btnIcon = document.getElementById("btn-toggle-guardian-icon");
  const btnLabel = document.getElementById("btn-toggle-guardian-label");
  const sessionCounter = document.getElementById("guardian-session-counter");

  if (navDot) {
    navDot.className = guardianRunning
      ? "w-2 h-2 rounded-full bg-emerald-400 animate-pulse"
      : "w-2 h-2 rounded-full bg-gray-500";
  }

  if (statusDot && statusText && btnToggle && heroCard) {
    if (guardianRunning) {
      statusDot.className = "w-3 h-3 rounded-full bg-emerald-400 animate-ping";
      statusText.innerHTML = `<span class="text-emerald-300 font-semibold">Vigilando activamente:</span> <code class="bg-gray-800 px-2 py-0.5 rounded text-gray-200">${status.watched_path}</code>. Cualquier archivo descargado será clasificado automáticamente.`;
      heroCard.className = "bg-emerald-950/20 border border-emerald-500/40 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all";
      btnToggle.className = "px-6 py-3 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 shadow-lg shadow-rose-600/20 transition-all flex items-center gap-2 shrink-0";
      btnIcon.innerText = "⏹️";
      btnLabel.innerText = "Detener Modo Guardián";
    } else {
      statusDot.className = "w-3 h-3 rounded-full bg-gray-500";
      statusText.innerText = "El Guardián está inactivo. Al activarlo, vigilará tu carpeta en segundo plano y organizará automáticamente cada archivo apenas termine de descargarse.";
      heroCard.className = "bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all";
      btnToggle.className = "px-6 py-3 rounded-xl font-bold text-xs text-white bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2 shrink-0";
      btnIcon.innerText = "▶️";
      btnLabel.innerText = "Activar Modo Guardián";
    }
  }

  // Sincronizar selectores con la configuración actual
  if (status.config) {
    const folderEl = document.getElementById("guardian-folder-type");
    const modeEl = document.getElementById("guardian-mode");
    const renameEl = document.getElementById("guardian-smart-rename");
    const notifyEl = document.getElementById("guardian-win-notify");

    if (folderEl && document.activeElement !== folderEl) folderEl.value = status.config.folder_type;
    if (modeEl && document.activeElement !== modeEl) modeEl.value = status.config.mode;
    if (renameEl) renameEl.checked = status.config.enable_smart_rename;
    if (notifyEl) notifyEl.checked = status.config.windows_notifications;
  }

  if (sessionCounter) {
    sessionCounter.innerText = `${status.total_processed_session || 0} organizados en esta sesión`;
  }

  // Renderizar bitácora en vivo
  const listEl = document.getElementById("guardian-events-list");
  const emptyEl = document.getElementById("guardian-events-empty");
  if (!listEl || !emptyEl) return;

  const events = status.events || [];
  if (events.length === 0) {
    listEl.innerHTML = "";
    emptyEl.classList.remove("hidden");
    return;
  }

  emptyEl.classList.add("hidden");
  listEl.innerHTML = "";

  events.forEach((ev) => {
    const item = document.createElement("div");
    item.className = "flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-gray-800/60 border border-gray-700/70 text-xs";

    const wasRenamed = ev.new_name && ev.new_name.toLowerCase() !== ev.original_name.toLowerCase();

    item.innerHTML = `
      <div class="space-y-1">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-[10px] font-mono bg-gray-900 text-gray-400 px-2 py-0.5 rounded">${ev.timestamp}</span>
          <span class="font-bold text-white">${ev.original_name}</span>
          ${wasRenamed ? `<span class="text-purple-300 font-medium">✏️ → ${ev.new_name}</span>` : ""}
          <span class="text-brand-400 font-semibold">📁 → ${ev.destination_folder}</span>
        </div>
        <p class="text-[11px] text-gray-400">${ev.reason}</p>
      </div>
      <div>
        ${
          ev.reverted
            ? `<span class="px-2.5 py-1 rounded-lg bg-gray-700/60 text-gray-400 text-[11px]">Revertido</span>`
            : `<button type="button" onclick="revertGuardianEvent('${ev.transaction_id}')" class="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-semibold transition-all">↩️ Deshacer</button>`
        }
      </div>
    `;
    listEl.appendChild(item);
  });
}

function getGuardianConfigFromInputs(enabledState) {
  const fType = document.getElementById("guardian-folder-type")?.value || "downloads";
  return {
    enabled: enabledState,
    folder_type: fType,
    custom_path: fType === "custom" ? guardianCustomFolderPath : null,
    mode: document.getElementById("guardian-mode")?.value || "all",
    enable_smart_rename: document.getElementById("guardian-smart-rename")?.checked ?? true,
    windows_notifications: document.getElementById("guardian-win-notify")?.checked ?? true,
  };
}

async function onGuardianFolderSelectChange() {
  const fType = document.getElementById("guardian-folder-type")?.value;
  if (fType === "custom" && !guardianCustomFolderPath) {
    await pickGuardianCustomFolder();
    return;
  }
  await onGuardianConfigChange();
}

async function pickGuardianCustomFolder() {
  try {
    const res = await fetch("/api/system/pick-folder?title=Seleccionar+carpeta+a+vigilar+con+Guardian");
    if (!res.ok) return;
    const data = await res.json();
    if (data.selected && data.path) {
      guardianCustomFolderPath = data.path;
      const sel = document.getElementById("guardian-folder-type");
      if (sel) sel.value = "custom";
      const lbl = document.getElementById("guardian-custom-path-label");
      if (lbl) {
        lbl.innerText = `📂 ${data.path}`;
        lbl.classList.remove("hidden");
      }
      await onGuardianConfigChange();
    }
  } catch (err) {
    console.error(err);
  }
}

async function toggleGuardian() {
  const targetState = !guardianRunning;
  const payload = getGuardianConfigFromInputs(targetState);

  try {
    const res = await fetch("/api/guardian/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("No se pudo cambiar el estado del Guardián");
    const status = await res.json();
    renderGuardianUI(status);

    if (status.running) {
      showToast("🛡️ Modo Guardián Activado", `Vigilando en tiempo real: ${status.watched_path}`);
    } else {
      showToast("Modo Guardián Detenido", "Se pausó el monitoreo automático en segundo plano.");
    }
  } catch (err) {
    showToast("Error en Guardián", err.message, true);
  }
}

async function onGuardianConfigChange() {
  if (!guardianRunning) return;
  const payload = getGuardianConfigFromInputs(true);
  try {
    const res = await fetch("/api/guardian/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      const status = await res.json();
      renderGuardianUI(status);
      showToast("Guardián Actualizado", "Se aplicaron los nuevos ajustes en caliente.");
    }
  } catch (err) {
    console.error(err);
  }
}

async function clearGuardianEvents() {
  try {
    const res = await fetch("/api/guardian/clear", { method: "POST" });
    if (res.ok) {
      const status = await res.json();
      renderGuardianUI(status);
    }
  } catch (err) {
    console.error(err);
  }
}

async function revertGuardianEvent(txId) {
  await triggerRollback(txId);
  await loadGuardianStatus();
}

// ==========================================
// 12. SELECTOR VISUAL DE CARPETAS Y AUTO-SETUP OLLAMA (V2.1)
// ==========================================

async function browseRuleDestFolder() {
  try {
    const res = await fetch("/api/system/pick-folder?title=Seleccionar+Carpeta+de+Destino+para+la+Regla");
    if (!res.ok) throw new Error("No se pudo abrir el selector de carpetas");
    const data = await res.json();
    if (data.selected && data.path) {
      const destInput = document.getElementById("rule-input-dest");
      if (destInput) {
        destInput.value = data.path;
      }
      showToast("Carpeta Elegida", data.path);
    }
  } catch (err) {
    showToast("Error al abrir explorador", err.message, "error");
  }
}

let ollamaPollTimer = null;

async function loadOllamaSetupStatus() {
  try {
    const res = await fetch("/api/ollama/setup-status");
    if (!res.ok) return;
    const st = await res.json();

    const diskBadge = document.getElementById("ollama-disk-badge");
    const titleEl = document.getElementById("ollama-setup-title");
    const descEl = document.getElementById("ollama-setup-desc");
    const btnEl = document.getElementById("btn-ollama-autosetup");
    const progWrap = document.getElementById("ollama-progress-wrap");
    const progBar = document.getElementById("ollama-progress-bar");
    const progTxt = document.getElementById("ollama-progress-text");

    if (diskBadge && st.free_disk_gb) {
      diskBadge.innerText = `Disco libre: ${st.free_disk_gb} GB`;
    }

    if (st.installed && st.running && st.models && st.models.length > 0 && !st.is_working) {
      if (titleEl) titleEl.innerText = "Ollama Activo en esta PC";
      if (descEl) descEl.innerText = `Modelos instalados (${st.models.length}). Podés descargar otro modelo ligero en 1 clic si querés:`;
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.innerText = "⬇️ Descargar Modelo";
      }
      if (progWrap && st.setup_state !== "ready") progWrap.classList.add("hidden");
    } else if (!st.installed && !st.is_working) {
      if (titleEl) titleEl.innerText = "Ollama no detectado en esta PC";
      if (descEl) descEl.innerText = "Instalá Ollama y descargá un modelo local automáticamente con 1 solo clic:";
      if (btnEl) {
        btnEl.disabled = false;
        btnEl.innerText = "⚡ Auto-Instalar IA";
      }
    }

    if (st.is_working || st.setup_state === "ready" || st.setup_state === "error") {
      if (progWrap) progWrap.classList.remove("hidden");
      if (progBar) progBar.style.width = `${st.setup_progress || 5}%`;
      if (progTxt) progTxt.innerText = st.setup_message || "Procesando...";

      if (st.is_working) {
        if (btnEl) {
          btnEl.disabled = true;
          btnEl.innerText = "Instalando...";
        }
        if (!ollamaPollTimer) {
          ollamaPollTimer = setInterval(loadOllamaSetupStatus, 1500);
        }
      } else {
        if (ollamaPollTimer) {
          clearInterval(ollamaPollTimer);
          ollamaPollTimer = null;
        }
        if (st.setup_state === "ready") {
          await checkHealth();
        }
      }
    }
  } catch (err) {
    console.error("Error consultando setup de Ollama:", err);
  }
}

async function triggerOllamaAutoSetup() {
  const modelSelect = document.getElementById("ollama-install-model-select");
  const chosenModel = modelSelect ? modelSelect.value : "llama3.2:1b";

  try {
    const res = await fetch("/api/ollama/auto-setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: chosenModel }),
    });
    if (!res.ok) throw new Error("No se pudo iniciar el instalador automático");
    showToast("Iniciando Instalación IA", `Configurando Ollama y el modelo ${chosenModel} en segundo plano...`);
    await loadOllamaSetupStatus();
    if (!ollamaPollTimer) {
      ollamaPollTimer = setInterval(loadOllamaSetupStatus, 1500);
    }
  } catch (err) {
    showToast("Error en Auto-Setup", err.message, "error");
  }
}
