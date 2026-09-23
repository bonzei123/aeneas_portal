"""Keycloak-User nach Zammad-Freigabe. Nutzt den Client matrix-sync (manage-users)."""
from __future__ import annotations

import re

import httpx

from app import settings

_USER_OK = re.compile(r"[^a-z0-9._-]")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def kc_token() -> str:
    r = httpx.post(
        f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.KEYCLOAK_SYNC_CLIENT_ID,
            "client_secret": settings.KEYCLOAK_SYNC_CLIENT_SECRET,
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def username_from_email(email: str) -> str:
    local = email.split("@", 1)[0].lower()
    name = _USER_OK.sub("-", local).strip(".-") or "mitglied"
    return name[:80]


def find_user(token: str, email: str) -> dict | None:
    r = httpx.get(
        f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
        headers=_headers(token),
        params={"email": email, "exact": "true"},
        timeout=20,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def find_group_id(token: str, name: str) -> str | None:
    r = httpx.get(
        f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/groups",
        headers=_headers(token),
        params={"search": name, "briefRepresentation": "true", "max": 50},
        timeout=20,
    )
    r.raise_for_status()
    for g in r.json():
        if g.get("name") == name:
            return g.get("id")
    return None


def ensure_user(email: str, name: str, verein: str = "") -> str:
    """Legt den User an oder nimmt den bestehenden. Gibt die Keycloak-ID zurück."""
    token = kc_token()
    existing = find_user(token, email)
    created = False
    if existing:
        uid = existing["id"]
    else:
        r = httpx.post(
            f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
            headers=_headers(token),
            json={
                "username": username_from_email(email),
                "email": email,
                "emailVerified": True,
                "enabled": True,
                "firstName": name.split(" ", 1)[0],
                "lastName": name.split(" ", 1)[1] if " " in name else "",
                "requiredActions": ["UPDATE_PASSWORD"],
            },
            timeout=20,
        )
        if r.status_code not in (201, 204):
            raise RuntimeError(f"Keycloak User: {r.status_code} {r.text[:300]}")
        loc = r.headers.get("Location") or ""
        uid = loc.rstrip("/").split("/")[-1]
        if not uid:
            again = find_user(token, email)
            if not again:
                raise RuntimeError("User angelegt, id fehlt")
            uid = again["id"]
        created = True
    names = ["mitgliedschaft:aktiv"]
    if verein:
        names.append(f"verein:{verein}")
    for gname in names:
        gid = find_group_id(token, gname)
        if not gid:
            continue
        httpx.put(
            f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{uid}/groups/{gid}",
            headers=_headers(token),
            timeout=20,
        ).raise_for_status()
    if not created:
        return uid
    # Nur Passwort-Link, kein OIDC-Redirect. client_id+redirect_uri ohne
    # laufende PKCE-Session macht in Keycloak 26 Internal Server Error.
    r = httpx.put(
        f"{settings.KEYCLOAK_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{uid}/execute-actions-email",
        headers=_headers(token),
        json=["UPDATE_PASSWORD"],
        timeout=20,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Keycloak Mail: {r.status_code} {r.text[:300]}")
    return uid
