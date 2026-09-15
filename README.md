# Aeneas Portal

Startseite nach dem Login: Linktree (Chat, CAV, Support, Schulung, Cloud nur für Ämter) und später Mein Konto.

Noch ohne Keycloak-Login — das kommt als Nächstes, sobald der Realm in der Infra steht. Jetzt: eine HTML-Seite und `/health`, damit Compose etwas zum Weiterleiten hat.

Lokal ohne Docker:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Produktion: Image wird von `aeneas_infra/compose.apps.yml` gebaut.
