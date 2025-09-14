# Backend admin router (FastAPI)

## Files
- `app/admin_api/config.py` — env + Supabase/panel helpers
- `app/admin_api/deps.py` — admin auth (Bearer token)
- `app/admin_api/models.py` — pydantic schemas
- `app/admin_api/supa.py` — Supabase helpers
- `app/admin_api/panel.py` — VPN panel helpers
- `app/admin_api/router.py` — endpoints (`/admin/*`)

## Enable in your FastAPI app
In your existing `backend/app/main.py`, add after you create `app = FastAPI()`:
```py
from app.admin_api.router import router as admin_router
app.include_router(admin_router)
```

## Required env
```env
ADMIN_API_TOKEN=supersecret_admin_token
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...   # service role (server-side only)

TG_BOT_TOKEN=123456:ABC...

PANEL_GR_URL=https://gr-panel.example.com/api
PANEL_GR_TOKEN=your_gr_token
PANEL_CZ_URL=https://cz-panel.example.com/api
PANEL_CZ_TOKEN=your_cz_token
PANEL_VERIFY_SSL=true
```

## Endpoints
- `GET /admin/user/{tgid}/days` → returns Supabase + Greece + Czechia day counts
- `POST /admin/user/days/set` `{ tgid, days, push_to_panels }` → updates Supabase and panels
- `POST /admin/broadcast` `{ message, tgid_list? }` → Telegram broadcast (all or subset)
