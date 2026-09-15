from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Aeneas Portal")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    # Login und echte URLs kommen mit Keycloak. Die Links sind Platzhalter.
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Aeneas",
            "links": [
                {"href": "/#chat", "label": "Chat (Element)", "hint": "später Matrix"},
                {"href": "/#cav", "label": "Verein (CAV)", "hint": "später cav.DOMAIN"},
                {"href": "/#help", "label": "Support (Zammad)", "hint": "ohne Login möglich"},
                {"href": "/#learn", "label": "Schulungen (Moodle)", "hint": "Mitwirkung"},
            ],
        },
    )
