const state = {
  source: "live",
  theme: localStorage.getItem("cem501-theme") || "dark",
};

const $ = (selector) => document.querySelector(selector);

document.body.dataset.theme = state.theme;

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadDashboard();
});

function bindEvents() {
  $("#refreshLiveBtn").addEventListener("click", () => refreshInbox("live"));
  $("#refreshSampleBtn").addEventListener("click", () => refreshInbox("sample"));
  $("#probeBtn").addEventListener("click", probeSystems);
  $("#themeBtn").addEventListener("click", toggleTheme);
  $("#digestBtn").addEventListener("click", generateDigest);
  $("#generateReportBtn").addEventListener("click", generateDailyReport);
  $("#queueReportBtn").addEventListener("click", queueDailyReport);
  $("#memorySearch").addEventListener("input", debounce((event) => searchMemory(event.target.value), 250));
}

async function loadDashboard(query = "") {
  try {
    const response = await fetch(`/api/bootstrap?q=${encodeURIComponent(query)}`);
    const payload = await response.json();
    renderDashboard(payload);
  } catch (error) {
    $("#heroStatus").textContent = `Dashboard load failed: ${error.message}`;
  }
}

async function refreshInbox(source) {
  state.source = source;
  setHeroStatus(`Refreshing ${source === "live" ? "live" : "sample"} inbox snapshot...`);

  const response = await fetch("/api/inbox/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source }),
  });
  const payload = await response.json();

  if (!payload.ok) {
    setHeroStatus(payload.error || "Inbox refresh failed.");
    return;
  }

  renderOverview(payload.overview);
  renderInbox(payload.inbox);
  renderQueue(payload.queue);
  await refreshAuxiliaryPanels();
}

async function refreshAuxiliaryPanels() {
  const [statusRes, logsRes, tasksRes] = await Promise.all([
    fetch("/api/status"),
    fetch("/api/logs"),
    fetch("/api/tasks"),
  ]);

  const [statusPayload, logsPayload, tasksPayload] = await Promise.all([
    statusRes.json(),
    logsRes.json(),
    tasksRes.json(),
  ]);

  renderStatus(statusPayload.items);
  renderLogs(logsPayload.items);
  renderTasks(tasksPayload);
}

async function searchMemory(query) {
  const [contactsRes, messagesRes] = await Promise.all([
    fetch(`/api/contacts?q=${encodeURIComponent(query)}`),
    fetch(`/api/messages?q=${encodeURIComponent(query)}`),
  ]);

  const [contactsPayload, messagesPayload] = await Promise.all([
    contactsRes.json(),
    messagesRes.json(),
  ]);

  renderContacts(contactsPayload.items || []);
  renderMessages(messagesPayload.items || []);
}

async function probeSystems() {
  const response = await fetch("/api/status?probe=1");
  const payload = await response.json();
  renderStatus(payload.items || []);
}

async function generateDigest() {
  $("#digestPreview").textContent = "Generating digest preview...";

  const response = await fetch("/api/digest/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: state.source, use_llm: false }),
  });
  const payload = await response.json();
  $("#digestPreview").textContent = payload.text || "Digest preview unavailable.";
}

function toggleTheme() {
  state.theme = document.body.dataset.theme === "dark" ? "light" : "dark";
  document.body.dataset.theme = state.theme;
  localStorage.setItem("cem501-theme", state.theme);
}

function renderDashboard(payload) {
  if (!payload.ok) {
    setHeroStatus(payload.error || "Failed to load dashboard payload.");
    return;
  }

  renderOverview(payload.overview);
  renderInbox(payload.inbox);
  renderQueue(payload.queue);
  renderContacts(payload.memory.contacts || []);
  renderMessages(payload.memory.messages || []);
  renderTasks(payload.tasks);
  renderStatus(payload.status || []);
  renderLogs(payload.logs || []);
}

function renderOverview(overview) {
  state.source = overview.source || state.source;
  setHeroStatus(`${overview.status_message} Last refresh: ${overview.last_refresh || "not yet refreshed"}.`);

  const metrics = [
    { label: "Inbox Emails", value: overview.counts.emails },
    { label: "Pending Reviews", value: overview.counts.queue_pending },
    { label: "Overdue Tasks", value: overview.counts.overdue },
    { label: "Contacts", value: overview.counts.contacts },
  ];

  $("#metricGrid").innerHTML = metrics
    .map(
      (metric) => `
        <article class="metric-card">
          <span class="eyebrow">${metric.label}</span>
          <strong>${metric.value}</strong>
        </article>
      `
    )
    .join("");
}

function renderInbox(inbox) {
  const categories = ["URGENT", "ACTION", "FYI", "ARCHIVE"];
  $("#inboxColumns").innerHTML = categories
    .map((category) => {
      const items = inbox[category] || [];
      return `
        <article class="inbox-column">
          <div class="section-header">
            <h3>${category}</h3>
            <span class="pill ${category.toLowerCase()}">${items.length}</span>
          </div>
          <div class="inbox-stack">
            ${items.length ? items.map(renderInboxCard).join("") : emptyState()}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderInboxCard(item) {
  return `
    <article class="inbox-card">
      <div class="meta-row">${escapeHtml(item.sender_name || item.sender)} • ${escapeHtml(item.date || "")}</div>
      <h4>${escapeHtml(item.subject)}</h4>
      <p>${escapeHtml(item.preview || item.body || "")}</p>
      <div class="legend">
        <span class="pill ${item.category.toLowerCase()}">${escapeHtml(item.category)}</span>
        <span class="pill archive">keyword: ${escapeHtml(item.keyword || "default")}</span>
      </div>
    </article>
  `;
}

function renderQueue(queue) {
  const metrics = queue.metrics || {};
  $("#queueMetrics").innerHTML = `
    <span class="pill action">Pending ${metrics.pending || 0}</span>
    <span class="pill fyi">Approved ${metrics.approved || 0}</span>
    <span class="pill urgent">Rejected ${metrics.rejected || 0}</span>
  `;

  const items = queue.items || [];
  $("#queueList").innerHTML = items.length ? items.map(renderQueueCard).join("") : emptyState("No drafts waiting for review.");

  items.forEach((item) => {
    const editButton = document.getElementById(`save-${item.id}`);
    const approveButton = document.getElementById(`approve-${item.id}`);
    const rejectButton = document.getElementById(`reject-${item.id}`);
    const deleteButton = document.getElementById(`delete-${item.id}`);

    if (editButton) {
      editButton.addEventListener("click", () => saveDraft(item.id));
    }
    if (approveButton) {
      approveButton.addEventListener("click", () => approveDraft(item.id));
    }
    if (rejectButton) {
      rejectButton.addEventListener("click", () => rejectDraft(item.id));
    }
    if (deleteButton) {
      deleteButton.addEventListener("click", () => deleteDraft(item.id));
    }
  });
}

function renderQueueCard(item) {
  return `
    <article class="queue-item">
      <div class="section-header">
        <div>
          <div class="legend">
            <span class="pill ${item.category.toLowerCase()}">${escapeHtml(item.category)}</span>
            <span class="pill archive">${escapeHtml(item.status.toUpperCase())}</span>
          </div>
          <h4>${escapeHtml(item.reply_subject)}</h4>
          <p class="microcopy">${escapeHtml(item.sender_name)} • ${escapeHtml(item.sender_email)} • keyword: ${escapeHtml(item.keyword)}</p>
        </div>
        <div class="microcopy">${escapeHtml(item.last_action || item.updated_at || "")}</div>
      </div>

      <div class="queue-item-grid">
        <div class="message-block">
          <p class="eyebrow">Original Email</p>
          <p><strong>${escapeHtml(item.subject)}</strong></p>
          <p>${escapeHtml(item.body)}</p>
        </div>

        <div class="draft-block">
          <p class="eyebrow">Proposed Draft</p>
          <textarea id="draft-${item.id}" class="draft-input">${escapeHtml(item.draft)}</textarea>
          ${renderWarnings(item)}
          <div class="queue-actions">
            <button id="save-${item.id}" class="btn btn-secondary">Edit Draft</button>
            <button id="approve-${item.id}" class="btn btn-primary">Approve & Send</button>
            <button id="reject-${item.id}" class="btn btn-ghost">Reject</button>
            <button id="delete-${item.id}" class="btn btn-ghost" style="color: var(--color-urgent);">Delete</button>
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderWarnings(item) {
  const warnings = item.warnings || [];
  const error = item.error ? `<li>${escapeHtml(item.error)}</li>` : "";
  if (!warnings.length && !item.error) {
    return `<p class="microcopy">No validation warnings.</p>`;
  }

  return `
    <ul class="warning-list">
      ${warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}
      ${error}
    </ul>
  `;
}

async function saveDraft(queueId) {
  const draft = document.getElementById(`draft-${queueId}`).value;
  await fetch(`/api/queue/${queueId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft }),
  });
  await loadDashboard($("#memorySearch").value || "");
}

async function approveDraft(queueId) {
  await fetch(`/api/queue/${queueId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dry_run: false }),
  });
  await loadDashboard($("#memorySearch").value || "");
}

async function rejectDraft(queueId) {
  await fetch(`/api/queue/${queueId}/reject`, { method: "POST" });
  await loadDashboard($("#memorySearch").value || "");
}

async function deleteDraft(queueId) {
  if (!confirm("Are you sure you want to completely delete this item from the queue?")) return;
  await fetch(`/api/queue/${queueId}/delete`, { method: "POST" });
  await loadDashboard($("#memorySearch").value || "");
}

function renderContacts(items) {
  $("#contactsList").innerHTML = items.length
    ? items
        .map(
          (item) => `
            <article class="contact-card">
              <p class="eyebrow">${escapeHtml(item.role || "Contact")}</p>
              <h4>${escapeHtml(item.name)}</h4>
              <p>${escapeHtml(item.company || "Independent")}</p>
              <p class="microcopy">${escapeHtml(item.email || "No email")} • messages: ${item.message_count || 0}</p>
            </article>
          `
        )
        .join("")
    : emptyState("No contacts found.");
}

function renderMessages(items) {
  $("#messagesList").innerHTML = items.length
    ? items
        .map(
          (item) => `
            <article class="message-card" style="display: flex; gap: 10px;">
              <input type="checkbox" class="message-select" value="${item.id}" style="margin-top: 5px; cursor: pointer;">
              <div style="flex-grow: 1;">
                <div class="meta-row">${escapeHtml(item.contact_name || "Unknown")} • ${escapeHtml(item.sent_at || "")}</div>
                <h4>${escapeHtml(item.subject || "(no subject)")}</h4>
                <p>${escapeHtml(item.body || "")}</p>
                <div class="legend">
                  <span class="pill ${item.direction === "sent" ? "action" : "fyi"}">${escapeHtml(item.direction)}</span>
                  <span class="pill archive">${escapeHtml(item.channel || "email")}</span>
                </div>
              </div>
            </article>
          `
        )
        .join("")
    : emptyState("No messages found.");
}

function renderTasks(tasks) {
  $("#pendingTasks").innerHTML = tasks.pending?.length
    ? tasks.pending.map((task) => renderTaskCard(task, false)).join("")
    : emptyState("No pending tasks.");

  $("#overdueTasks").innerHTML = tasks.overdue?.length
    ? tasks.overdue.map((task) => renderTaskCard(task, true)).join("")
    : emptyState("No overdue tasks.");

  bindTaskActions();
}

function renderTaskCard(task, isOverdue) {
  return `
    <article class="task-card">
      <p class="eyebrow">${isOverdue ? "Overdue" : "Pending"}</p>
      <h4>${escapeHtml(task.description)}</h4>
      <p class="microcopy">${escapeHtml(task.contact_name || "No linked contact")} • due ${escapeHtml(task.due_at)}</p>
      <div class="task-actions">
        <button data-task-complete="${task.id}" class="btn btn-secondary">Complete</button>
        <button data-task-skip="${task.id}" class="btn btn-ghost">Skip</button>
      </div>
    </article>
  `;
}

function bindTaskActions() {
  document.querySelectorAll("[data-task-complete]").forEach((button) => {
    button.addEventListener("click", async () => {
      await fetch(`/api/tasks/${button.dataset.taskComplete}/complete`, { method: "POST" });
      const tasksRes = await fetch("/api/tasks");
      renderTasks(await tasksRes.json());
    });
  });

  document.querySelectorAll("[data-task-skip]").forEach((button) => {
    button.addEventListener("click", async () => {
      await fetch(`/api/tasks/${button.dataset.taskSkip}/skip`, { method: "POST" });
      const tasksRes = await fetch("/api/tasks");
      renderTasks(await tasksRes.json());
    });
  });
}

function renderStatus(items) {
  $("#statusList").innerHTML = items
    .map(
      (item) => `
        <article class="status-card">
          <p class="eyebrow">${escapeHtml(item.label)}</p>
          <h4>${escapeHtml(item.detail)}</h4>
          <div class="status-indicator state-${escapeHtml(item.state)}">
            <span class="status-dot"></span>
            <span>${escapeHtml(item.state.toUpperCase())}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderLogs(items) {
  $("#logFeed").innerHTML = items.length
    ? items
        .map(
          (item) => `
            <article class="log-entry">
              <span class="log-level">${escapeHtml(item.level)}</span>
              <strong>${escapeHtml(item.timestamp || "recent")}</strong>
              <span>${escapeHtml(item.message)}</span>
            </article>
          `
        )
        .join("")
    : emptyState("No recent log entries.");
}

async function generateDailyReport() {
  const checkboxes = document.querySelectorAll('.message-select:checked');
  const message_ids = Array.from(checkboxes).map(cb => parseInt(cb.value));
  
  if (message_ids.length === 0) {
    alert("Please select at least one message from the Message History first.");
    return;
  }
  
  $("#reportContent").value = "Generating daily report using OpenAI, please wait...";
  $("#queueReportBtn").style.display = "none";
  
  const response = await fetch("/api/reports/daily", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_ids }),
  });
  const payload = await response.json();
  
  if (payload.ok) {
    $("#reportContent").value = payload.report;
    $("#queueReportBtn").style.display = "inline-block";
  } else {
    $("#reportContent").value = "Error generating report: " + payload.error;
  }
}

async function queueDailyReport() {
  const draft = $("#reportContent").value;
  if (!draft) return;
  
  $("#queueReportBtn").textContent = "Adding...";
  
  const response = await fetch("/api/queue/synthetic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft }),
  });
  
  const payload = await response.json();
  if (payload.ok) {
    alert("Daily report added to Review Queue! You can now review it and send it as an email.");
    loadDashboard();
    $("#queueReportBtn").textContent = "Add to Review Queue (Prepare Email)";
  } else {
    alert("Failed to queue report: " + payload.error);
    $("#queueReportBtn").textContent = "Add to Review Queue (Prepare Email)";
  }
}

function setHeroStatus(message) {
  $("#heroStatus").textContent = message;
}

function emptyState(message = "Nothing to show yet.") {
  return `<div class="empty-state"><p>${escapeHtml(message)}</p></div>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function debounce(fn, wait) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), wait);
  };
}
