const state = {
  source: "live",
  theme: localStorage.getItem("cem501-theme") || "dark",
  reportAttachments: [],
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
  $("#resetDemoBtn").addEventListener("click", resetDemoState);
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
  setHeroStatus(`Refreshing ${source === "live" ? "live inbox and Telegram history" : "sample inbox snapshot"}...`);

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
  setHeroStatus(
    `${payload.overview.status_message} Last refresh: ${payload.overview.last_refresh || "not yet refreshed"}. Message History refreshed.`
  );
}

async function resetDemoState() {
  if (!confirm("Reset demo inbox and review queue to the original sample state?")) {
    return;
  }

  state.source = "sample";
  setHeroStatus("Resetting demo snapshot...");

  const response = await fetch("/api/demo/reset", { method: "POST" });
  const payload = await response.json();

  if (!payload.ok) {
    setHeroStatus(payload.error || "Demo reset failed.");
    return;
  }

  renderOverview(payload.overview);
  renderInbox(payload.inbox);
  renderQueue(payload.queue);
  await refreshAuxiliaryPanels();
}

async function refreshAuxiliaryPanels() {
  const query = $("#memorySearch").value || "";
  const [statusRes, logsRes, tasksRes, contactsRes, messagesRes] = await Promise.all([
    fetch("/api/status"),
    fetch("/api/logs"),
    fetch("/api/tasks"),
    fetch(`/api/contacts?q=${encodeURIComponent(query)}`),
    fetch(`/api/messages?q=${encodeURIComponent(query)}`),
  ]);

  const [statusPayload, logsPayload, tasksPayload, contactsPayload, messagesPayload] = await Promise.all([
    statusRes.json(),
    logsRes.json(),
    tasksRes.json(),
    contactsRes.json(),
    messagesRes.json(),
  ]);

  renderStatus(statusPayload.items);
  renderLogs(logsPayload.items);
  renderTasks(tasksPayload);
  renderContacts(contactsPayload.items || []);
  renderMessages(messagesPayload.items || []);
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
  renderDigestHistory(payload.history || []);
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
  renderArtifactHistories(payload.artifacts || {});
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
        <span class="pill archive">reason: ${escapeHtml(cleanReason(item.keyword))}</span>
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
    const dryRunButton = document.getElementById(`dryrun-${item.id}`);
    const rejectButton = document.getElementById(`reject-${item.id}`);
    const deleteButton = document.getElementById(`delete-${item.id}`);

    if (editButton) {
      editButton.addEventListener("click", () => saveDraft(item.id));
    }
    if (approveButton) {
      approveButton.addEventListener("click", () => approveDraft(item.id));
    }
    if (dryRunButton) {
      dryRunButton.addEventListener("click", () => approveDraft(item.id, true));
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
          <p class="microcopy">${escapeHtml(item.sender_name)} • ${escapeHtml(item.sender_email)} • reason: ${escapeHtml(cleanReason(item.keyword))}</p>
        </div>
        <div class="microcopy">${escapeHtml(item.last_action || item.updated_at || "")}</div>
      </div>

      <div class="queue-item-grid">
        <div class="message-block">
          <p class="eyebrow">Original Email</p>
          <p><strong>${escapeHtml(item.subject)}</strong></p>
          <p class="original-email-body">${escapeHtml(item.body)}</p>
          ${renderAttachments(item.attachments || [])}
        </div>

        <div class="draft-block">
          <p class="eyebrow">Proposed Draft</p>
          <div class="recipient-grid">
            <label>
              <span class="eyebrow">To</span>
              <input id="to-${item.id}" class="recipient-input" type="email" value="${escapeHtml(item.to_address || item.sender_email || "")}">
            </label>
            <label>
              <span class="eyebrow">Cc / Additional Recipient</span>
              <input id="cc-${item.id}" class="recipient-input" type="text" value="${escapeHtml(item.cc_address || "")}" placeholder="optional@example.com">
            </label>
          </div>
          <textarea id="draft-${item.id}" class="draft-input">${escapeHtml(item.draft)}</textarea>
          ${renderWarnings(item)}
          <div class="queue-actions">
            <button id="save-${item.id}" class="btn btn-secondary">Save Draft</button>
            <button id="dryrun-${item.id}" class="btn btn-secondary">Approve Dry Run</button>
            <button id="approve-${item.id}" class="btn btn-primary">Approve & Send</button>
            <button id="reject-${item.id}" class="btn btn-ghost">Reject</button>
            <button id="delete-${item.id}" class="btn btn-ghost" style="color: var(--color-urgent);">Delete</button>
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderAttachments(attachments) {
  if (!attachments.length) return "";
  return `
    <div class="attachment-list">
      <p class="eyebrow">Attachments</p>
      ${attachments
        .map(
          (attachment) => `
            <div class="attachment-chip">
              <span>${escapeHtml(attachment.filename || "attachment")}</span>
              <span class="microcopy">${escapeHtml(attachment.content_type || "file")}</span>
            </div>
          `
        )
        .join("")}
    </div>
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
  await persistQueueItem(queueId, true);
}

async function persistQueueItem(queueId, reload = false) {
  const draft = document.getElementById(`draft-${queueId}`).value;
  const toAddress = document.getElementById(`to-${queueId}`).value;
  const ccAddress = document.getElementById(`cc-${queueId}`).value;

  const response = await fetch(`/api/queue/${queueId}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft, to_address: toAddress, cc_address: ccAddress }),
  });
  const payload = await response.json();
  if (!payload.ok) {
    alert(payload.error || "Failed to save draft.");
    return false;
  }

  if (reload) {
    await loadDashboard($("#memorySearch").value || "");
  }
  return true;
}

async function approveDraft(queueId, dryRun = false) {
  const saved = await persistQueueItem(queueId, false);
  if (!saved) return;

  await fetch(`/api/queue/${queueId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dry_run: dryRun }),
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
    : "";

  $("#overdueTasks").innerHTML = tasks.overdue?.length
    ? tasks.overdue.map((task) => renderTaskCard(task, true)).join("")
    : emptyState("No overdue tasks.");

  bindTaskActions();
}

function renderTaskCard(task, isOverdue) {
  const isEmailOverdue = task.source === "email_overdue";
  const label = isEmailOverdue ? `Overdue ${task.category || "Email"}` : isOverdue ? "Overdue" : "Pending";
  const detail = isEmailOverdue
    ? `${task.contact_name || "Unknown sender"} • received ${task.due_at || "unknown date"}`
    : `${task.contact_name || "No linked contact"} • due ${task.due_at}`;
  const actions = task.actionable === false
    ? ""
    : `
      <div class="task-actions">
        <button data-task-complete="${task.id}" class="btn btn-secondary">Complete</button>
        <button data-task-skip="${task.id}" class="btn btn-ghost">Skip</button>
      </div>
    `;

  return `
    <article class="task-card">
      <p class="eyebrow">${escapeHtml(label)}</p>
      <h4>${escapeHtml(task.description)}</h4>
      <p class="microcopy">${escapeHtml(detail)}</p>
      ${actions}
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
    state.reportAttachments = payload.attachments || [];
    $("#queueReportBtn").style.display = "inline-block";
    renderReportHistory(payload.history || []);
  } else {
    state.reportAttachments = [];
    $("#reportContent").value = "Error generating report: " + payload.error;
  }
}

function renderArtifactHistories(artifacts) {
  renderReportHistory(artifacts.daily_reports || []);
  renderDigestHistory(artifacts.morning_digests || []);
}

function renderReportHistory(items) {
  const container = $("#reportsHistory");
  if (!container) return;

  container.innerHTML = items.length
    ? items.map(renderReportHistoryItem).join("")
    : emptyState("No saved reports yet.");

  items.forEach((item) => {
    const button = document.getElementById(`report-history-${item.id}`);
    if (!button) return;
    button.addEventListener("click", () => {
      $("#reportContent").value = item.content || "";
      state.reportAttachments = item.attachments || [];
      $("#queueReportBtn").style.display = item.content ? "inline-block" : "none";
    });
  });
}

function renderDigestHistory(items) {
  const container = $("#digestsHistory");
  if (!container) return;

  container.innerHTML = items.length
    ? items.map(renderDigestHistoryItem).join("")
    : emptyState("No saved digests yet.");

  items.forEach((item) => {
    const button = document.getElementById(`digest-history-${item.id}`);
    if (!button) return;
    button.addEventListener("click", () => {
      $("#digestPreview").textContent = item.text || "Digest preview unavailable.";
    });
  });
}

function renderReportHistoryItem(item) {
  const attachmentCount = (item.attachments || []).length;
  const attachmentLabel = attachmentCount ? ` - attachments: ${attachmentCount}` : "";
  return `
    <button id="report-history-${escapeHtml(item.id)}" class="artifact-item" type="button">
      <h4>${escapeHtml(item.title || "Daily Report")}</h4>
      <p class="microcopy">${escapeHtml(item.created_at || "")} - messages: ${item.selected_message_count || 0}${escapeHtml(attachmentLabel)}</p>
    </button>
  `;
}

function renderDigestHistoryItem(item) {
  return `
    <button id="digest-history-${escapeHtml(item.id)}" class="artifact-item" type="button">
      <h4>${escapeHtml(item.title || "Morning Digest")}</h4>
      <p class="microcopy">${escapeHtml(item.created_at || "")} • source: ${escapeHtml(item.source || "current")}</p>
    </button>
  `;
}

async function queueDailyReport() {
  const draft = $("#reportContent").value;
  if (!draft) return;
  
  $("#queueReportBtn").textContent = "Adding...";
  
  const response = await fetch("/api/queue/synthetic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft, attachments: state.reportAttachments || [] }),
  });
  
  const payload = await response.json();
  if (payload.ok) {
    const attachmentCount = (state.reportAttachments || []).length;
    const attachmentText = attachmentCount ? ` ${attachmentCount} photo attachment(s) included.` : "";
    alert(`Daily report added to Review Queue!${attachmentText} You can now review it and send it as an email.`);
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

function cleanReason(value) {
  let text = String(value || "review manually").trim();
  if (!text || text.toLowerCase() === "llm_error_review_manually") {
    return "review manually";
  }

  text = text.replace(/^llm:(?:(?:high|medium|low):)?/i, "").trim();
  if (!text || text.toLowerCase() === "review") {
    return "review manually";
  }
  return text;
}

function debounce(fn, wait) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), wait);
  };
}
