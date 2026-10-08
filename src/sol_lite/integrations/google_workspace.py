"""Google Workspace OAuth and Gmail/Calendar client for SOL-Lite."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events.owned",
)
_PROVIDER = "SOL-Lite"
_KEY = "google-workspace"


def _google_modules():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Workspace support requires the optional dependencies. "
            "Install SOL-Lite with the 'google' extra."
        ) from exc
    return Credentials, InstalledAppFlow, build


@dataclass(slots=True)
class GoogleWorkspaceClient:
    """Provider adapter. OAuth tokens are stored only in the OS keyring."""

    credentials: Any
    credential_manager: Any

    @classmethod
    def connect(cls, client_secrets: str, credential_manager):
        Credentials, InstalledAppFlow, _ = _google_modules()
        secrets_path = os.path.expanduser(client_secrets)
        if not os.path.isfile(secrets_path):
            raise FileNotFoundError(
                "Google OAuth client JSON was not found. Set "
                "SOL_GOOGLE_OAUTH_CLIENT_SECRETS to its path."
            )
        flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
        credentials = flow.run_local_server(
            host="127.0.0.1", port=0, open_browser=True,
            authorization_prompt_message="Open this URL to connect Google: {url}",
            success_message="Google is connected to SOL-Lite. You may close this tab.",
            access_type="offline", prompt="consent",
        )
        credential_manager.store(
            credential_manager.reference(_PROVIDER, _KEY),
            credentials.to_json(),
        )
        return cls(credentials, credential_manager)

    @classmethod
    def from_keyring(cls, credential_manager):
        ref = credential_manager.reference(_PROVIDER, _KEY)
        try:
            raw = credential_manager.resolve(ref)
        except KeyError:
            return None
        Credentials, _, _ = _google_modules()
        credentials = Credentials.from_authorized_user_info(
            json.loads(str(raw)), SCOPES
        )
        # Google client libraries refresh lazily when an approved API request
        # is made. Never perform a network refresh while composing the runtime.
        return cls(credentials, credential_manager)

    @classmethod
    def disconnect(cls, credential_manager):
        ref = credential_manager.reference(_PROVIDER, _KEY)
        try:
            credential_manager.delete(ref)
        except Exception as exc:
            # Keyring providers differ in how a missing credential is reported.
            if not isinstance(exc, KeyError) and "not found" not in str(exc).casefold():
                raise

    def _service(self, api: str, version: str):
        _, _, build = _google_modules()
        return build(api, version, credentials=self.credentials, cache_discovery=False)

    def search_email(self, query: str, limit: int = 10):
        service = self._service("gmail", "v1")
        response = service.users().messages().list(
            userId="me", q=query, maxResults=max(1, min(limit, 50))
        ).execute()
        messages = []
        for item in response.get("messages", []):
            data = service.users().messages().get(
                userId="me", id=item["id"], format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ).execute()
            headers = {h["name"].casefold(): h["value"] for h in data.get("payload", {}).get("headers", [])}
            messages.append({
                "id": data.get("id"), "thread_id": data.get("threadId"),
                "from": headers.get("from", ""), "to": headers.get("to", ""),
                "subject": headers.get("subject", ""), "date": headers.get("date", ""),
                "snippet": data.get("snippet", ""),
            })
        return {"messages": messages, "result_size_estimate": response.get("resultSizeEstimate", 0)}

    def read_email(self, message_id: str):
        import base64

        message = self._service("gmail", "v1").users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()
        headers = {h["name"].casefold(): h["value"] for h in message.get("payload", {}).get("headers", [])}
        text_parts = []
        def collect(part):
            mime_type = str(part.get("mimeType") or "").casefold()
            data = (part.get("body") or {}).get("data")
            if mime_type == "text/plain" and data:
                text_parts.append(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace"))
            for child in part.get("parts", []) or []:
                collect(child)
        collect(message.get("payload", {}))
        return {
            "id": message.get("id"), "thread_id": message.get("threadId"),
            "from": headers.get("from", ""), "to": headers.get("to", ""),
            "subject": headers.get("subject", ""), "date": headers.get("date", ""),
            "snippet": message.get("snippet", ""), "body_text": "\n".join(text_parts)[:100000],
        }

    def send_email(self, *, to: str, subject: str, body: str):
        import base64
        from email.message import EmailMessage

        message = EmailMessage()
        message["To"], message["Subject"] = to, subject
        message.set_content(body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        return self._service("gmail", "v1").users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

    def list_events(self, *, time_min: str, time_max: str, limit: int = 20):
        return self._service("calendar", "v3").events().list(
            calendarId="primary", timeMin=time_min, timeMax=time_max,
            maxResults=max(1, min(limit, 100)), singleEvents=True,
            orderBy="startTime",
        ).execute().get("items", [])

    def create_event(self, *, summary: str, start: str, end: str,
                     description: str = "", attendees: list[str] | None = None,
                     reminder_minutes: int | None = None):
        event = {"summary": summary, "description": description,
                 "start": {"dateTime": start}, "end": {"dateTime": end}}
        if attendees:
            event["attendees"] = [{"email": address} for address in attendees]
        if reminder_minutes is not None:
            event["reminders"] = {"useDefault": False, "overrides": [
                {"method": "popup", "minutes": reminder_minutes}
            ]}
        return self._service("calendar", "v3").events().insert(
            calendarId="primary", body=event, sendUpdates="all" if attendees else "none"
        ).execute()


def credential_manager():
    from ..credentials.manager import CredentialManager, KeyringBackend
    return CredentialManager(KeyringBackend())
