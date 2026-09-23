# Aeneas Portal

FastAPI: Einstiegsseite nach OIDC-Login (Kacheln zu CAV, Zammad, Frappe, Matrix; Nextcloud nur für Amtsgruppen) und später Konto-Selbstbedienung.

OIDC gegen Keycloak (Realm `aeneas`, Client `portal`). `GET /health` bleibt ohne Auth. `/` zeigt Login bzw. Einstiegsseite plus Gruppen aus dem Token.

Lokal ohne Docker:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Image-Build: `aeneas_infra/compose.apps.yml`.
