"""Approval-gated Gmail and Google Calendar capabilities."""
from __future__ import annotations

from datetime import datetime, timedelta
from email.utils import parseaddr

from ..capabilities.risk import RiskClass
from .base import ToolDefinition


def _client(ctx):
    client = getattr(ctx, "google_workspace", None)
    if client is None:
        raise RuntimeError("Google is not connected. Run 'sol-lite google-connect' first.")
    return client


def _authorize(ctx, scope, operation, target, arguments, plan, approval_id=None):
    ctx.permission_engine.check(
        scope, approval_id=approval_id, operation=operation, target=target,
        arguments=arguments, plan=plan,
    )


def _timestamp(value, label):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone offset")
    return parsed


def _search_email(ctx, args):
    query = str(args.get("query") or "").strip()
    limit = int(args.get("limit") or 10)
    if not query or len(query) > 500:
        raise ValueError("query is required and must be at most 500 characters")
    _authorize(ctx, "google.read", "google_email_search", "Gmail",
               {"query": query, "limit": limit}, f"Search Gmail for: {query}", args.get("approval_id"))
    result = _client(ctx).search_email(query, limit)
    ctx.audit.record("google.email.search", result_count=len(result.get("messages", [])))
    return result


def _read_email(ctx, args):
    message_id = str(args.get("message_id") or "").strip()
    if not message_id or len(message_id) > 200:
        raise ValueError("A valid Gmail message_id is required")
    _authorize(ctx, "google.read", "google_email_read", message_id,
               {"message_id": message_id}, f"Read Gmail message {message_id}", args.get("approval_id"))
    result = _client(ctx).read_email(message_id)
    ctx.audit.record("google.email.read", message_id=message_id)
    return result


def _send_email(ctx, args):
    to = str(args.get("to") or "").strip()
    subject = str(args.get("subject") or "")
    body = str(args.get("body") or "")
    address = parseaddr(to)[1]
    if not address or "@" not in address or any(c in address for c in "\r\n"):
        raise ValueError("A valid recipient email address is required")
    if not subject.strip() or not body.strip() or len(body) > 100000:
        raise ValueError("subject and body are required (body limit 100000 characters)")
    arguments = {"to": address, "subject": subject, "body": body}
    _authorize(ctx, "google.send", "google_email_send", address, arguments,
               f"Send email to {address} with subject {subject}", args.get("approval_id"))
    result = _client(ctx).send_email(**arguments)
    ctx.audit.record("google.email.sent", recipient=address, message_id=result.get("id"))
    return {"sent": True, "id": result.get("id"), "thread_id": result.get("threadId")}


def _list_events(ctx, args):
    start, end = str(args.get("time_min") or ""), str(args.get("time_max") or "")
    if not start or not end or _timestamp(end, "time_max") <= _timestamp(start, "time_min"):
        raise ValueError("time_min and time_max must be ISO timestamps with time_max after time_min")
    limit = int(args.get("limit") or 20)
    arguments = {"time_min": start, "time_max": end, "limit": limit}
    _authorize(ctx, "google.read", "google_calendar_list", "primary calendar", arguments,
               f"List Google Calendar events from {start} to {end}", args.get("approval_id"))
    events = _client(ctx).list_events(**arguments)
    ctx.audit.record("google.calendar.list", result_count=len(events))
    return {"events": events}


def _create_event(ctx, args):
    summary, start, end = (str(args.get(key) or "").strip() for key in ("summary", "start", "end"))
    description = str(args.get("description") or "")
    attendees = [str(item).strip() for item in args.get("attendees", [])]
    if not summary or not start or not end or _timestamp(end, "end") <= _timestamp(start, "start"):
        raise ValueError("summary, start, and end are required; end must be later than start")
    if any(not parseaddr(item)[1] or "@" not in parseaddr(item)[1] for item in attendees):
        raise ValueError("Every attendee must be a valid email address")
    reminder = args.get("reminder_minutes")
    if reminder is not None and not 0 <= int(reminder) <= 40320:
        raise ValueError("reminder_minutes must be from 0 to 40320")
    arguments = {"summary": summary, "start": start, "end": end,
                 "description": description, "attendees": attendees,
                 "reminder_minutes": reminder}
    _authorize(ctx, "google.calendar_write", "google_calendar_create", summary,
               arguments, f"Create Google Calendar event: {summary}", args.get("approval_id"))
    result = _client(ctx).create_event(**arguments)
    ctx.audit.record("google.calendar.created", event_id=result.get("id"), summary=summary)
    return {"created": True, "event": result}


def _create_reminder(ctx, args):
    title = str(args.get("title") or "").strip()
    when = str(args.get("time") or "").strip()
    notes = str(args.get("notes") or "")
    moment = _timestamp(when, "time")
    if not title:
        raise ValueError("title is required")
    arguments = {"title": title, "time": when, "notes": notes}
    _authorize(ctx, "google.calendar_write", "google_calendar_reminder", title,
               arguments, f"Create Google Calendar reminder: {title} at {when}", args.get("approval_id"))
    result = _client(ctx).create_event(
        summary=f"Reminder: {title}", start=when,
        end=(moment + timedelta(minutes=1)).isoformat(), description=notes,
        reminder_minutes=0,
    )
    ctx.audit.record("google.calendar.reminder_created", event_id=result.get("id"), title=title)
    return {"created": True, "reminder": result}


def google_workspace_tools():
    read_risk = (RiskClass.READ_ONLY, RiskClass.NETWORK)
    write_risk = (RiskClass.MUTATING, RiskClass.NETWORK)
    approval = {"approval_id": {"type": "string", "description": "Exact approval token returned by SOL-Lite."}}
    return [
        ToolDefinition("google_email_search", "Search connected Gmail messages; message body is not returned.",
            {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}, **approval}, "required": ["query"]},
            _search_email, permissions=("google.read",), risk=read_risk, locality="network"),
        ToolDefinition("google_email_read", "Read the headers, snippet, and plain-text body of a specific Gmail message.",
            {"type": "object", "properties": {"message_id": {"type": "string"}, **approval}, "required": ["message_id"]},
            _read_email, permissions=("google.read",), risk=read_risk, locality="network"),
        ToolDefinition("google_email_send", "Send an email using the connected Gmail account after exact user approval.",
            {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}, **approval}, "required": ["to", "subject", "body"]},
            _send_email, permissions=("google.send",), risk=write_risk, mutability=True, locality="network"),
        ToolDefinition("google_calendar_list", "List events in the connected primary Google Calendar within an ISO timestamp range.",
            {"type": "object", "properties": {"time_min": {"type": "string"}, "time_max": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}, **approval}, "required": ["time_min", "time_max"]},
            _list_events, permissions=("google.read",), risk=read_risk, locality="network"),
        ToolDefinition("google_calendar_create", "Create a Google Calendar event, optionally invite attendees and add a popup reminder; requires exact approval.",
            {"type": "object", "properties": {"summary": {"type": "string"}, "start": {"type": "string"}, "end": {"type": "string"}, "description": {"type": "string"}, "attendees": {"type": "array", "items": {"type": "string"}}, "reminder_minutes": {"type": "integer", "minimum": 0, "maximum": 40320}, **approval}, "required": ["summary", "start", "end"]},
            _create_event, permissions=("google.calendar_write",), risk=write_risk, mutability=True, locality="network"),
        ToolDefinition("google_calendar_reminder", "Create a private popup reminder in the primary Google Calendar at a specific ISO 8601 time; requires exact approval.",
            {"type": "object", "properties": {"title": {"type": "string"}, "time": {"type": "string"}, "notes": {"type": "string"}, **approval}, "required": ["title", "time"]},
            _create_reminder, permissions=("google.calendar_write",), risk=write_risk, mutability=True, locality="network"),
    ]
