# Aeneas Portal

FastAPI-Einstieg: Login (OIDC), Kacheln, öffentliches Aufnahmeformular. Kein Ticketkern, kein LMS.

Image-Build: `aeneas_infra/compose.apps.yml`. Weg zum Stack: `aeneas_infra/SETUP.md`.

## Was es tut

| Pfad | Wer | Wirkung |
| --- | --- | --- |
| `/` | alle | Login oder Kacheln (Gruppen aus dem Token) |
| `/aufnahme` | ohne Login | Zammad-Ticket `Aufnahme: …` als Helpdesk |
| `/hooks/zammad-aufnahme` | Zammad-Webhook | Tag `freigabe` + Verein + „Konto anlegen“ → Keycloak-User + Passwort-Mail |
| `/sync-admin/` | `admin:matrix` | Proxy auf den Matrix-Worker |
| `/health` | ohne Auth | liveness |

Kacheln: Cloud bei `backoffice` oder `rolle:*`. Chat-Räume nur `admin:matrix`.

Aufnahme legt **kein** Keycloak-Konto beim Absenden an. Amt in Zammad: Feld `aufnahme_verein`, Boolean `aufnahme_ok`, Tag `freigabe`, dann **Aktualisieren**. Titel muss `Aufnahme:` enthalten. User bekommt `mitgliedschaft:aktiv` und `verein:<slug>`.

Fehlt Verein oder Haken: interne Notiz im Ticket, kein User. Token-Besitzer des API-Tokens ist Ticket-Ersteller — deshalb Funktionsuser Helpdesk, nicht das persönliche Konto.

Keycloak-Admin-API über denselben Client `matrix-sync` (`manage-users`). `execute-actions-email` nur mit `UPDATE_PASSWORD`, ohne `client_id`/`redirect_uri`.

`python-multipart` steht in `requirements.txt` (sonst `POST /aufnahme` 500). Nach Änderungen am Requirements-File Image neu bauen.

## Env (Compose reicht, Werte in `aeneas_infra/.env`)

`PORTAL_OIDC_CLIENT_SECRET`, `SESSION_SECRET`, `PORTAL_PUBLIC_URL`, `ZAMMAD_API_TOKEN`, `ZAMMAD_WEBHOOK_TOKEN`, `ZAMMAD_TICKET_CUSTOMER`, `KEYCLOAK_SYNC_CLIENT_SECRET`, `MATRIX_ADMIN_PASSWORD`.

## Lokal ohne Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

OIDC und Aufnahme brauchen Keycloak/Zammad aus der Infra.
