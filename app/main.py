from pathlib import Path
import hmac
import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx

from app import oidc, settings, zammad

log = logging.getLogger("portal")


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
            "aufnahme_ready": settings.aufnahme_ready(),
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


@app.get("/aufnahme", response_class=HTMLResponse)
def aufnahme_get(request: Request) -> HTMLResponse:
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "aufnahme.html",
        {
            "request": request,
            "title": "Mitglied werden",
            "ok": False,
            "err": "" if settings.aufnahme_ready() else "Aufnahme ist nicht konfiguriert (ZAMMAD_API_TOKEN).",
            "name": "",
            "email": "",
            "verein": "",
            "note": "",
        },
        status_code=200 if settings.aufnahme_ready() else 503,
    )


@app.post("/aufnahme", response_class=HTMLResponse)
async def aufnahme_post(request: Request) -> HTMLResponse:
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)
    form = await request.form()
    # Honeypot: Bots füllen oft „website“. Menschen sehen das Feld nicht.
    if (form.get("website") or "").strip():
        return RedirectResponse(url="/aufnahme", status_code=303)
    name = str(form.get("name") or "").strip()
    email = str(form.get("email") or "").strip()
    verein = str(form.get("verein") or "").strip()
    note = str(form.get("note") or "").strip()
    ctx = {
        "request": request,
        "title": "Mitglied werden",
        "ok": False,
        "err": "",
        "name": name,
        "email": email,
        "verein": verein,
        "note": note,
    }
    if not settings.aufnahme_ready():
        ctx["err"] = "Aufnahme ist nicht konfiguriert."
        return templates.TemplateResponse("aufnahme.html", ctx, status_code=503)
    if not name or "@" not in email:
        ctx["err"] = "Name und gültige E-Mail angeben."
        return templates.TemplateResponse("aufnahme.html", ctx, status_code=400)
    try:
        zammad.create_aufnahme_ticket(name, email, verein, note)
    except Exception:
        log.exception("Zammad Aufnahme-Ticket")
        ctx["err"] = "Ticket ging nicht raus. Später nochmal oder Mail an den Verein."
        return templates.TemplateResponse("aufnahme.html", ctx, status_code=502)
    ctx["ok"] = True
    return templates.TemplateResponse("aufnahme.html", ctx)



@app.get("/login")
async def login(request: Request):
    if not settings.oidc_ready():
        return _page(request, status_code=503)
    try:
        return await oidc.oauth.keycloak.authorize_redirect(request, oidc.callback_uri())
    except Exception:
        log.exception("OIDC login")
        return _page(request, status_code=503)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oidc.oauth.keycloak.authorize_access_token(request)
    except Exception:
        log.exception("OIDC callback")
        return RedirectResponse(url="/login", status_code=302)
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


def _sync_admin_forbidden() -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><p>Kein Zugriff. Chat-Räume nur mit "
        "<code>admin:matrix</code>.</p>",
        status_code=403,
    )


@app.api_route("/sync-admin", methods=["GET", "POST"])
@app.api_route("/sync-admin/{rest:path}", methods=["GET", "POST"])
async def sync_admin(request: Request, rest: str = "") -> Response:
    """Worker-UI nur intern. Browser sieht Portal-Session (Keycloak), nicht Basic."""
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if not settings.can_manage_matrix(user.get("groups") or []):
        return _sync_admin_forbidden()
    path = "/sync-admin/" if not rest else f"/sync-admin/{rest}"
    if request.url.query:
        path = f"{path}?{request.url.query}"
    headers = {}
    if request.headers.get("content-type"):
        headers["content-type"] = request.headers["content-type"]
    auth = None
    if settings.MATRIX_ADMIN_PASSWORD:
        auth = (settings.MATRIX_ADMIN_USER, settings.MATRIX_ADMIN_PASSWORD)
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream = await client.request(
            request.method,
            f"{settings.MATRIX_ADMIN_URL}{path}",
            content=body or None,
            headers=headers,
            auth=auth,
            follow_redirects=False,
        )
    out = {}
    if loc := upstream.headers.get("location"):
        out["location"] = loc
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=out,
        media_type=upstream.headers.get("content-type"),
    )


@app.post("/hooks/zammad-aufnahme")
async def hook_zammad_aufnahme(request: Request) -> Response:
    """Zammad-Trigger: Tag freigabe auf einem Aufnahme-Ticket."""
    token = request.query_params.get("token") or ""
    expected = settings.ZAMMAD_WEBHOOK_TOKEN
    if not expected or len(token) != len(expected) or not hmac.compare_digest(token, expected):
        log.warning("Aufnahme-Hook: Token falsch oder fehlt")
        return Response(status_code=401)
    try:
        payload = await request.json()
    except Exception:
        log.warning("Aufnahme-Hook: kein JSON")
        return Response(status_code=204)
    ticket = payload.get("ticket") or payload
    title = str(ticket.get("title") or "")
    if "Aufnahme:" not in title:
        log.info("Aufnahme-Hook: Titel ohne Aufnahme: %s", title[:80])
        return Response(status_code=204)
    body = zammad.body_from_webhook(payload)
    name, email = zammad.parse_aufnahme_fields(body)
    if "@" not in email:
        log.warning("Aufnahme-Hook: keine E-Mail im Ticket %s", title[:80])
        return Response(status_code=204)
    ticket_id = ticket.get("id")
    ok = zammad.truthy(ticket.get("aufnahme_ok"))
    verein = zammad.parse_verein(body, ticket)
    if not ok or not verein:
        missing = []
        if not ok:
            missing.append("Haken „Konto anlegen“")
        if not verein:
            missing.append("Verein")
        zammad.add_internal_note(
            ticket_id,
            "Kein Keycloak-User. Noch offen: "
            + ", ".join(missing)
            + ". Danach Aktualisieren oder erneut Freigeben.",
        )
        log.info("Aufnahme-Hook wartet %s", missing)
        return Response(status_code=204)
    from app import keycloak_admin

    try:
        keycloak_admin.ensure_user(email, name or email, verein)
    except Exception:
        log.exception("Aufnahme-Hook Keycloak %s", email)
        return Response(status_code=500)
    log.info("Aufnahme-Hook ok %s verein=%s", email, verein)
    return Response(status_code=204)
