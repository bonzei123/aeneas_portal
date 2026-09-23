"""Zammad-Ticket für den Aufnahmeantrag. Kein Mitglieder-Login in Zammad."""
from __future__ import annotations

import httpx

from app import settings


def create_aufnahme_ticket(name: str, email: str, verein: str, note: str) -> None:
    if not settings.ZAMMAD_API_TOKEN:
        raise RuntimeError("ZAMMAD_API_TOKEN fehlt")
    body = (
        f"Name: {name}\n"
        f"E-Mail: {email}\n"
        f"Verein: {verein or '—'}\n\n"
        f"{note or '—'}\n\n"
        "Freigabe: Tag freigabe setzen. Dann legt das Portal den Keycloak-User "
        "an und schickt die Passwort-Mail."
    )
    payload = {
        "title": f"Aufnahme: {name}",
        "group": settings.ZAMMAD_TICKET_GROUP,
        "customer": settings.ZAMMAD_TICKET_CUSTOMER or email,
        "article": {
            "subject": f"Aufnahme: {name}",
            "body": body,
            "type": "note",
            "internal": True,
            "content_type": "text/plain",
        },
    }
    r = httpx.post(
        f"{settings.ZAMMAD_URL}/api/v1/tickets",
        headers={
            "Authorization": f"Token token={settings.ZAMMAD_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Zammad {r.status_code}: {r.text[:400]}")


def _api_headers() -> dict[str, str]:
    return {
        "Authorization": f"Token token={settings.ZAMMAD_API_TOKEN}",
        "Content-Type": "application/json",
    }


VEREIN_SLUGS = {
    "demo": "demo",
    "wanne-eickel": "wanne-eickel",
    "wanne eickel": "wanne-eickel",
    "worms": "worms",
}


def truthy(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1:
        return True
    return str(value).strip().lower() in ("true", "ja", "yes", "on", "1")


def parse_verein(text: str, ticket: dict) -> str:
    raw = str(ticket.get("aufnahme_verein") or "").strip().lower()
    if not raw:
        for line in text.splitlines():
            if line.lower().startswith("verein:"):
                raw = line.split(":", 1)[1].strip().lower()
                break
    raw = raw.replace("—", "").replace("–", "").strip()
    if raw in ("", "-", "nein"):
        return ""
    return VEREIN_SLUGS.get(raw, "")


def add_internal_note(ticket_id: object, body: str) -> None:
    if not settings.ZAMMAD_API_TOKEN or not ticket_id:
        return
    httpx.post(
        f"{settings.ZAMMAD_URL}/api/v1/ticket_articles",
        headers=_api_headers(),
        json={
            "ticket_id": ticket_id,
            "body": body,
            "type": "note",
            "internal": True,
            "content_type": "text/plain",
        },
        timeout=20,
    )


def parse_aufnahme_fields(text: str) -> tuple[str, str]:
    name, email = "", ""
    for line in text.splitlines():
        low = line.lower()
        if low.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif low.startswith("e-mail:") or low.startswith("email:"):
            email = line.split(":", 1)[1].strip()
    return name, email


def body_from_webhook(payload: dict) -> str:
    ticket = payload.get("ticket") or payload
    article = payload.get("article") or ticket.get("article") or {}
    if isinstance(article, dict) and article.get("body"):
        return str(article.get("body") or "")
    articles = ticket.get("articles") or payload.get("articles") or []
    if isinstance(articles, list):
        texts = [str(a.get("body") or "") for a in articles if isinstance(a, dict)]
        return "\n".join(texts)
    return str(ticket.get("title") or "")
