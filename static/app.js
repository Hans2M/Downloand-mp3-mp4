const state = { media: null, format: "mp4" };
const $ = (selector) => document.querySelector(selector);

function showMessage(text, kind = "") {
  const element = $("#message");
  element.textContent = text;
  element.className = `message ${kind}`;
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.success === false) throw new Error(data.error || "Error inesperado.");
  return data;
}

function updateQualityOptions() {
  const options = state.media?.[state.format === "mp3" ? "audio_qualities" : "video_qualities"] || [];
  $("#quality").innerHTML = options.map((item) =>
    `<option value="${item.quality}">${item.label} · ${item.estimated_size}</option>`
  ).join("");
}

function renderMedia(media) {
  state.media = media;
  $("#media-panel").classList.remove("hidden");
  $("#title").textContent = media.title;
  $("#metadata").textContent = `${media.uploader} · ${media.duration ? `${Math.floor(media.duration / 60)} min` : "Duración desconocida"}`;
  if (media.thumbnail) {
    $("#thumbnail").src = media.thumbnail;
    $("#thumbnail").classList.remove("hidden");
  }
  updateQualityOptions();
}

function renderTasks(tasks) {
  const container = $("#tasks");
  if (!tasks.length) {
    container.className = "empty";
    container.textContent = "No hay descargas activas.";
    return;
  }
  container.className = "";
  container.innerHTML = tasks.slice().reverse().map((task) => {
    const finished = task.status === "completed";
    const failed = task.status === "failed";
    return `<article class="task">
      <div class="task-line"><span class="task-title">${escapeHtml(task.title)}</span><strong>${task.progress}%</strong></div>
      <div class="task-meta">${task.format.toUpperCase()} · ${task.quality} · ${escapeHtml(task.status)}${task.error_message ? ` · ${escapeHtml(task.error_message)}` : ""}</div>
      <div class="progress"><div style="width:${task.progress}%"></div></div>
      <div class="task-line"><span class="task-meta">${escapeHtml(task.speed)} · ETA ${escapeHtml(task.eta)}</span>
        ${!finished && !failed && task.status !== "cancelled" ? `<button class="cancel" data-cancel="${task.id}">Cancelar</button>` : ""}</div>
    </article>`;
  }).join("");
}

function renderHistory(downloads) {
  const container = $("#history");
  if (!downloads.length) {
    container.className = "empty";
    container.textContent = "Todavía no hay archivos completados.";
    return;
  }
  container.className = "";
  container.innerHTML = downloads.map((item) =>
    `<div class="history-item"><div><strong>${escapeHtml(item.title)}</strong><div class="task-meta">${(item.format || "").toUpperCase()} · ${item.quality || ""}</div></div>
      ${item.status === "completed" ? `<a class="small-button" href="/api/files/${encodeURIComponent(item.id)}">Guardar</a>` : ""}</div>`
  ).join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  }[character]));
}

$("#analyze-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage("Analizando...");
  try {
    const media = await api("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ url: $("#url").value.trim() }),
    });
    renderMedia(media);
    showMessage("Contenido analizado. Elige formato y calidad.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

document.querySelectorAll(".format-button").forEach((button) => {
  button.addEventListener("click", () => {
    state.format = button.dataset.format;
    document.querySelectorAll(".format-button").forEach((item) => item.classList.toggle("active", item === button));
    updateQualityOptions();
  });
});

$("#download-button").addEventListener("click", async () => {
  if (!state.media) return;
  try {
    await api("/api/download", {
      method: "POST",
      body: JSON.stringify({
        url: state.media.url, title: state.media.title, format: state.format,
        quality: $("#quality").value, thumbnail: state.media.thumbnail, duration: state.media.duration,
      }),
    });
    showMessage("Descarga iniciada.", "success");
    refreshTasks();
  } catch (error) {
    showMessage(error.message, "error");
  }
});

async function refreshTasks() {
  try {
    renderTasks((await api("/api/tasks")).tasks);
  } catch (error) {
    showMessage(error.message, "error");
  }
}

async function refreshHistory() {
  try {
    renderHistory((await api("/api/history")).downloads);
  } catch (error) {
    showMessage(error.message, "error");
  }
}

$("#tasks").addEventListener("click", async (event) => {
  const taskId = event.target.dataset.cancel;
  if (!taskId) return;
  await api(`/api/tasks/${taskId}/cancel`, { method: "POST", body: "{}" });
  refreshTasks();
});
$("#refresh-button").addEventListener("click", refreshTasks);
$("#history-button").addEventListener("click", refreshHistory);
refreshTasks();
refreshHistory();
setInterval(refreshTasks, 1500);
setInterval(refreshHistory, 5000);
