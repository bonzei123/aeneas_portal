import os


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).rstrip("/")


KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "aeneas")
KEYCLOAK_URL = _env("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_PUBLIC_URL = _env("KEYCLOAK_PUBLIC_URL", "https://id.aeneas-solutions.de")
PORTAL_PUBLIC_URL = _env("PORTAL_PUBLIC_URL", "https://portal.aeneas-solutions.de")
PORTAL_OIDC_CLIENT_ID = os.environ.get("PORTAL_OIDC_CLIENT_ID", "portal")
PORTAL_OIDC_CLIENT_SECRET = os.environ.get("PORTAL_OIDC_CLIENT_SECRET", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "changeme-portal-session")
DOMAIN = os.environ.get("DOMAIN", "aeneas-solutions.de").strip().lower()
PUBLIC_SCHEME = os.environ.get("PUBLIC_SCHEME", "https").strip().lower()


MATRIX_ADMIN_URL = _env("MATRIX_ADMIN_URL", "http://matrix-admin:8090")
MATRIX_ADMIN_USER = os.environ.get("MATRIX_ADMIN_USER", "admin")
MATRIX_ADMIN_PASSWORD = os.environ.get("MATRIX_ADMIN_PASSWORD", "")

ZAMMAD_URL = _env("ZAMMAD_URL", "http://zammad-nginx:8080")
ZAMMAD_API_TOKEN = os.environ.get("ZAMMAD_API_TOKEN", "")
ZAMMAD_TICKET_GROUP = os.environ.get("ZAMMAD_TICKET_GROUP", "Users")
# Ticket-Kunde in Zammad = Funktionspostfach, damit der Antragsteller keine Auto-Mail bekommt.
ZAMMAD_TICKET_CUSTOMER = os.environ.get("ZAMMAD_TICKET_CUSTOMER", "help@aeneas-solutions.de")
ZAMMAD_WEBHOOK_TOKEN = os.environ.get("ZAMMAD_WEBHOOK_TOKEN", "")
KEYCLOAK_SYNC_CLIENT_ID = os.environ.get("KEYCLOAK_SYNC_CLIENT_ID", "matrix-sync")
KEYCLOAK_SYNC_CLIENT_SECRET = os.environ.get("KEYCLOAK_SYNC_CLIENT_SECRET", "")


def oidc_ready() -> bool:
    return bool(PORTAL_OIDC_CLIENT_SECRET)


def aufnahme_ready() -> bool:
    return bool(ZAMMAD_API_TOKEN)


def service_url(sub: str) -> str:
    return f"{PUBLIC_SCHEME}://{sub}.{DOMAIN}"


def is_amt(groups: list[str]) -> bool:
    """Cloud: backoffice oder Amt (rolle:*)."""
    return any(g == "backoffice" or g.startswith("rolle:") for g in groups)


def can_manage_matrix(groups: list[str]) -> bool:
    """Chat-Räume / Worker-UI. Technik-Recht, kein Vereinsamt."""
    return "admin:matrix" in groups


def tiles(groups: list[str]) -> list[dict]:
    items = [
        {"href": service_url("cav"), "title": "Verein", "sub": "CAV"},
        {"href": service_url("help"), "title": "Support", "sub": "Tickets"},
        {"href": service_url("learn"), "title": "Schulung", "sub": "bald"},
        {"href": service_url("chat"), "title": "Chat", "sub": "bald"},
    ]
    if is_amt(groups):
        items.append({"href": service_url("cloud"), "title": "Cloud", "sub": "Amt"})
    if can_manage_matrix(groups):
        items.append({"href": "/sync-admin/", "title": "Chat-Räume", "sub": "admin:matrix"})
    return items
