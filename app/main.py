from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import oidc, settings

app = FastAPI(title="Aeneas Portal")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    same_site="lax",
    https_only=settings.PUBLIC_SCHEME == "https",
)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
oidc.register()


def _page(request: Request, status_code: int = 200) -> HTMLResponse:
    user = request.session.get("user")
    groups = (user or {}).get("groups") or []
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Aeneas",
            "user": user,
            "oidc_ready": settings.oidc_ready(),
            "tiles": settings.tiles(groups),
        },
        status_code=status_code,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return _page(request)


@app.get("/login")
async def login(request: Request):
    if not settings.oidc_ready():
        return _page(request, status_code=503)
    return await oidc.oauth.keycloak.authorize_redirect(request, oidc.callback_uri())


@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oidc.oauth.keycloak.authorize_access_token(request)
    userinfo = token.get("userinfo") or {}
    request.session["user"] = {
        "sub": userinfo.get("sub"),
        "username": userinfo.get("preferred_username") or userinfo.get("email") or "",
        "email": userinfo.get("email") or "",
        "groups": oidc.groups_from_token(token),
    }
    request.session["id_token"] = token.get("id_token")
    return RedirectResponse(url="/", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    id_token = request.session.get("id_token")
    request.session.clear()
    if settings.oidc_ready():
        return RedirectResponse(url=oidc.logout_url(id_token), status_code=302)
    return RedirectResponse(url="/", status_code=302)
