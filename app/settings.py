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


def oidc_ready() -> bool:
    return bool(PORTAL_OIDC_CLIENT_SECRET)


def service_url(sub: str) -> str:
    return f"{PUBLIC_SCHEME}://{sub}.{DOMAIN}"


def tiles(groups: list[str]) -> list[dict]:
    items = [
        {"href": service_url("cav"), "title": "Verein", "sub": "CAV"},
        {"href": service_url("help"), "title": "Support", "sub": "Tickets"},
        {"href": service_url("learn"), "title": "Schulung", "sub": "bald"},
        {"href": service_url("chat"), "title": "Chat", "sub": "bald"},
    ]
    if any(g == "backoffice" or g.startswith("rolle:") for g in groups):
        items.append({"href": service_url("cloud"), "title": "Cloud", "sub": "Amt"})
    return items
