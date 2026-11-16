// TidyDesk AI - Frontend Controller

let currentFolderType = "desktop";
let currentTargetFolder = "";
let scannedFiles = [];
let currentPlan = [];
let defaultFolders = {};

// Inicialización al cargar la página
document.addEventListener("DOMContentLoaded", async () => {
  loadSavedGeminiKey();
  await checkHealth();
  await loadHistory();
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

// 2. Navegación por Pestañas
function switchTab(tab) {
  const viewOrganizer = document.getElementById("view-organizer");
  const viewHistory = document.getElementById("view-history");
  const btnOrganizer = document.getElementById("tab-organizer-btn");
  const btnHistory = document.getElementById("tab-history-btn");

  if (tab === "organizer") {
    viewOrganizer.classList.remove("hidden");
    viewHistory.classList.add("hidden");
    btnOrganizer.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all";
    btnHistory.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all flex items-center gap-1.5";
  } else {
    viewOrganizer.classList.add("hidden");
    viewHistory.classList.remove("hidden");
    btnHistory.className = "px-3.5 py-1.5 rounded-lg bg-brand-600 text-white shadow-sm transition-all flex items-center gap-1.5";
    btnOrganizer.className = "px-3.5 py-1.5 rounded-lg text-gray-400 hover:text-white transition-all";
    loadHistory();
  }
}

// 3. Selección de Carpeta (Escritorio / Descargas)
function selectFolder(type) {
  currentFolderType = type;
  const btnDesktop = document.getElementById("btn-folder-desktop");
  const btnDownloads = document.getElementById("btn-folder-downloads");

  if (type === "desktop") {
    btnDesktop.className = "folder-select-btn active p-4 rounded-xl border-2 border-brand-500 bg-brand-500/10 text-left transition-all";
    btnDownloads.className = "folder-select-btn p-4 rounded-xl border border-gray-800 bg-gray-800/40 text-left hover:border-gray-700 transition-all";
    currentTargetFolder = defaultFolders.desktop || "";
  } else {
    btnDownloads.className = "folder-select-btn active p-4 rounded-xl border-2 border-brand-500 bg-brand-500/10 text-left transition-all";
    btnDesktop.className = "folder-select-btn p-4 rounded-xl border border-gray-800 bg-gray-800/40 text-left hover:border-gray-700 transition-all";
    currentTargetFolder = defaultFolders.downloads || "";
  }

  // Ocultar planes anteriores para obligar nuevo escaneo
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

function onShortcutsToggleChange() {
  hideAllStates();
}

// 6. Proceso Principal: Escaneo + Plan de IA (Dry-Run)
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

    // Paso B: Generar Plan con el Motor seleccionado
    showLoading(
      "Consultando al Asistente de IA...",
      `Analizando ${scannedFiles.length} archivos para sugerir las mejores carpetas.`
    );

    const provider = document.getElementById("select-ai-provider").value;
    const model = provider === "ollama" ? document.getElementById("select-ollama-model").value : null;
    const apiKey = provider === "gemini" ? document.getElementById("input-gemini-key").value : null;

    const planRes = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_folder: currentTargetFolder,
        provider: provider,
        model: model,
        api_key: apiKey,
        files: scannedFiles,
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
    if (nameLower.endsWith(".lnk") || nameLower.endsWith(".url")) {
      if (item.suggested_folder.includes("Juegos")) fileIcon = "🎮";
      else if (item.suggested_folder.includes("Desarrollo")) fileIcon = "💻";
      else if (item.suggested_folder.includes("Diseño")) fileIcon = "🎨";
      else if (item.suggested_folder.includes("Navegadores")) fileIcon = "🌐";
      else if (item.suggested_folder.includes("Multimedia")) fileIcon = "🎧";
      else fileIcon = "🔗";
    } else if (nameLower.endsWith(".exe")) {
      fileIcon = "⚙️";
    } else if (nameLower.endsWith(".pdf")) {
      fileIcon = "📕";
    }

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
          <span class="text-xs text-brand-400">📁</span>
          <input type="text" value="${item.suggested_folder}" 
                 onchange="updateSuggestedFolder(${index}, this.value)"
                 class="bg-gray-800/80 border border-gray-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:border-brand-500 w-48 sm:w-64" />
        </div>
      </td>
      <td class="py-3 px-4">
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-gray-800 border border-gray-700 text-[11px] text-gray-300">
          💡 ${item.reason}
        </span>
      </td>
      <td class="py-3 px-4 text-right font-mono text-[11px] text-gray-400">
        ${file.size_formatted || "-"}
      </td>
    `;
    tbody.appendChild(tr);
  });
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

  showLoading("Organizando tus archivos...", "Moviendo elementos a sus nuevas carpetas con seguridad.");

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

    // Actualizar historial y volver a escanear
    await loadHistory();
    await startScanAndPlan();

  } catch (err) {
    showError("Fallo al organizar", err.message);
  }
}

// 9. Historial y Rollback (Undo)
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

// 10. Sistema de Toast Notifications
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
