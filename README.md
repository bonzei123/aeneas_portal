# Aeneas Portal

FastAPI: Einstiegsseite nach OIDC-Login (Links zu Element, CAV, Zammad, Moodle; Nextcloud nur für Backoffice-Gruppen) und später Konto-Selbstbedienung.

Aktuell ohne OIDC. Vorhanden: HTML-Stub und `GET /health` als Ziel für Compose/Traefik.

Lokal ohne Docker:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Image-Build: `aeneas_infra/compose.apps.yml`.
