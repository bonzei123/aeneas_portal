import os


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).rstrip("/")


KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "aeneas")
KEYCLOAK_URL = _env("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_PUBLIC_URL = _env("KEYCLOAK_PUBLIC_URL", "http://id.aeneas.test")
PORTAL_PUBLIC_URL = _env("PORTAL_PUBLIC_URL", "http://www.aeneas.test")
PORTAL_OIDC_CLIENT_ID = os.environ.get("PORTAL_OIDC_CLIENT_ID", "portal")
PORTAL_OIDC_CLIENT_SECRET = os.environ.get("PORTAL_OIDC_CLIENT_SECRET", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "changeme-portal-session")


def oidc_ready() -> bool:
    return bool(PORTAL_OIDC_CLIENT_SECRET)
