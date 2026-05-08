"""
dashboard_app.py -- Flask dashboard for the CEM501 communication agent.

Run:
    flask --app dashboard_app run --debug
or:
    python dashboard_app.py
"""

from __future__ import annotations

import imaplib
import os
import smtplib

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

from dashboard_store import (
    approve_queue_item,
    dashboard_overview,
    digest_snapshot,
    grouped_inbox,
    load_dashboard_state,
    mark_task_done,
    mark_task_skipped,
    memory_snapshot,
    parse_log_lines,
    queue_metrics,
    refresh_inbox_state,
    reject_queue_item,
    search_contacts,
    search_messages,
    tasks_snapshot,
    update_queue_draft,
)


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "web", "templates"),
    static_folder=os.path.join(BASE_DIR, "web", "static"),
)


def json_error(message: str, status_code: int = 400):
    """Return a compact JSON error payload."""
    return jsonify({"ok": False, "error": message}), status_code


def status_badge(label: str, state: str, detail: str) -> dict:
    """Format a status card consistently for the UI."""
    return {"label": label, "state": state, "detail": detail}


def passive_system_status() -> list[dict]:
    """Configuration-level health indicators without network calls."""
    email_address = os.getenv("EMAIL_ADDRESS", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    imap_state = "configured" if email_address and email_password else "missing"
    smtp_state = "configured" if email_address and email_password else "missing"
    openai_state = "configured" if openai_key else "missing"

    return [
        status_badge("IMAP", imap_state, "Credentials loaded." if imap_state == "configured" else "Missing email credentials."),
        status_badge("SMTP", smtp_state, "Ready for reviewed sends." if smtp_state == "configured" else "Missing email credentials."),
        status_badge("OpenAI", openai_state, "API key present." if openai_state == "configured" else "Missing OPENAI_API_KEY."),
    ]


def active_system_status() -> list[dict]:
    """Optional active probes for IMAP, SMTP, and OpenAI."""
    statuses = passive_system_status()
    email_address = os.getenv("EMAIL_ADDRESS", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com").strip() or "imap.gmail.com"
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip() or "smtp.gmail.com"
    smtp_port = int(os.getenv("SMTP_PORT", "587").strip() or "587")
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if email_address and email_password:
        try:
            with imaplib.IMAP4_SSL(imap_server) as client:
                client.login(email_address, email_password)
            statuses[0] = status_badge("IMAP", "healthy", f"Connected to {imap_server}.")
        except Exception as exc:
            statuses[0] = status_badge("IMAP", "error", str(exc))

        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=8) as client:
                client.starttls()
                client.login(email_address, email_password)
            statuses[1] = status_badge("SMTP", "healthy", f"Authenticated to {smtp_server}:{smtp_port}.")
        except Exception as exc:
            statuses[1] = status_badge("SMTP", "error", str(exc))

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            client.models.list()
            statuses[2] = status_badge("OpenAI", "healthy", "API probe succeeded.")
        except Exception as exc:
            statuses[2] = status_badge("OpenAI", "error", str(exc))

    return statuses


def dashboard_payload(query: str = "") -> dict:
    """Aggregate the data needed to render the dashboard."""
    state = load_dashboard_state()
    if not state.get("emails") and not state.get("last_refresh"):
        state = refresh_inbox_state("sample")
    inbox = grouped_inbox(state.get("emails", []))

    return {
        "ok": True,
        "overview": dashboard_overview(state),
        "inbox": inbox,
        "queue": {
            "items": state.get("queue", []),
            "metrics": queue_metrics(state.get("queue", [])),
        },
        "memory": memory_snapshot(query),
        "tasks": tasks_snapshot(),
        "status": passive_system_status(),
        "logs": parse_log_lines(limit=24),
    }


@app.get("/")
def index():
    """Serve the main dashboard shell."""
    return render_template("dashboard.html")


@app.get("/api/bootstrap")
def bootstrap():
    """Return the initial dashboard payload."""
    query = request.args.get("q", "")
    return jsonify(dashboard_payload(query))


@app.post("/api/inbox/refresh")
def refresh_inbox():
    """Refresh inbox state from live IMAP or sample data."""
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "live")
    state = refresh_inbox_state(source)
    return jsonify(
        {
            "ok": True,
            "overview": dashboard_overview(state),
            "inbox": grouped_inbox(state.get("emails", [])),
            "queue": {
                "items": state.get("queue", []),
                "metrics": queue_metrics(state.get("queue", [])),
            },
        }
    )


@app.get("/api/queue")
def get_queue():
    """Return the current review queue."""
    state = load_dashboard_state()
    return jsonify({"ok": True, "items": state.get("queue", []), "metrics": queue_metrics(state.get("queue", []))})


@app.post("/api/queue/<queue_id>/edit")
def edit_queue(queue_id: str):
    """Persist an edited draft from the dashboard."""
    payload = request.get_json(silent=True) or {}
    draft = (payload.get("draft") or "").strip()
    if not draft:
        return json_error("Draft body cannot be empty.", 422)

    try:
        item = update_queue_draft(queue_id, draft)
    except KeyError:
        return json_error("Draft not found.", 404)

    return jsonify({"ok": True, "item": item})


@app.post("/api/queue/<queue_id>/approve")
def approve_queue(queue_id: str):
    """Approve and send a reviewed draft."""
    payload = request.get_json(silent=True) or {}
    dry_run = bool(payload.get("dry_run", False))

    try:
        item = approve_queue_item(queue_id, dry_run=dry_run)
    except KeyError:
        return json_error("Draft not found.", 404)

    return jsonify({"ok": True, "item": item})


@app.post("/api/queue/<queue_id>/reject")
def reject_queue(queue_id: str):
    """Reject a draft from the review queue."""
    try:
        item = reject_queue_item(queue_id)
    except KeyError:
        return json_error("Draft not found.", 404)

    return jsonify({"ok": True, "item": item})


@app.get("/api/contacts")
def contacts():
    """Search the memory contact list."""
    query = request.args.get("q", "")
    return jsonify({"ok": True, "items": search_contacts(query)[:20]})


@app.get("/api/messages")
def messages():
    """Search the recent message audit trail."""
    query = request.args.get("q", "")
    try:
        limit = int(request.args.get("limit", "40"))
    except ValueError:
        limit = 40
    return jsonify({"ok": True, "items": search_messages(query, limit=limit)})


@app.get("/api/tasks")
def tasks():
    """Return pending and overdue tasks."""
    return jsonify({"ok": True, **tasks_snapshot()})


@app.post("/api/tasks/<int:task_id>/complete")
def complete_task_route(task_id: int):
    """Complete a scheduled task."""
    snapshot = mark_task_done(task_id)
    return jsonify({"ok": True, **snapshot})


@app.post("/api/tasks/<int:task_id>/skip")
def skip_task_route(task_id: int):
    """Skip a scheduled task."""
    snapshot = mark_task_skipped(task_id)
    return jsonify({"ok": True, **snapshot})


@app.post("/api/digest/preview")
def digest_preview():
    """Generate digest previews for the digest panel."""
    payload = request.get_json(silent=True) or {}
    source = payload.get("source")
    use_llm = bool(payload.get("use_llm", False))
    snapshot = digest_snapshot(source=source, use_llm=use_llm)
    return jsonify({"ok": True, **snapshot})


@app.get("/api/status")
def status():
    """Return passive or active system health indicators."""
    probe = request.args.get("probe", "0") == "1"
    return jsonify({"ok": True, "items": active_system_status() if probe else passive_system_status()})


@app.get("/api/logs")
def logs():
    """Return recent agent log entries."""
    try:
        limit = int(request.args.get("limit", "24"))
    except ValueError:
        limit = 24
    return jsonify({"ok": True, "items": parse_log_lines(limit=limit)})


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
