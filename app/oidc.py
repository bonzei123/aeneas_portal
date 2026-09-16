from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth

from app import settings

oauth = OAuth()


def _oidc(base: str, suffix: str) -> str:
    return f"{base}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/{suffix}"


def register() -> None:
    """Browser trifft Keycloak über Traefik (PUBLIC_URL), Token-Exchange intern."""
    issuer = f"{settings.KEYCLOAK_PUBLIC_URL}/realms/{settings.KEYCLOAK_REALM}"
    oauth.register(
        name="keycloak",
        client_id=settings.PORTAL_OIDC_CLIENT_ID,
        client_secret=settings.PORTAL_OIDC_CLIENT_SECRET,
        client_kwargs={
            "scope": "openid profile email",
            "code_challenge_method": "S256",
        },
        authorize_url=_oidc(settings.KEYCLOAK_PUBLIC_URL, "auth"),
        access_token_url=_oidc(settings.KEYCLOAK_URL, "token"),
        userinfo_endpoint=_oidc(settings.KEYCLOAK_URL, "userinfo"),
        jwks_uri=_oidc(settings.KEYCLOAK_URL, "certs"),
        server_metadata={"issuer": issuer},
    )


def callback_uri() -> str:
    return f"{settings.PORTAL_PUBLIC_URL}/auth/callback"


def logout_url(id_token: str | None) -> str:
    params = {
        "client_id": settings.PORTAL_OIDC_CLIENT_ID,
        "post_logout_redirect_uri": settings.PORTAL_PUBLIC_URL,
    }
    if id_token:
        params["id_token_hint"] = id_token
    return f"{_oidc(settings.KEYCLOAK_PUBLIC_URL, 'logout')}?{urlencode(params)}"


def groups_from_token(token: dict) -> list[str]:
    userinfo = token.get("userinfo") or {}
    groups = userinfo.get("groups")
    if isinstance(groups, list):
        return [str(g) for g in groups]
    return []
