import os
from supabase import create_client, Client

# Environment config
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")  # keep server-side only!

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN", "dev-admin-token")

PANEL_GR_URL = os.getenv("PANEL_GR_URL", "")
PANEL_GR_TOKEN = os.getenv("PANEL_GR_TOKEN", "")
PANEL_CZ_URL = os.getenv("PANEL_CZ_URL", "")
PANEL_CZ_TOKEN = os.getenv("PANEL_CZ_TOKEN", "")
PANEL_VERIFY_SSL = os.getenv("PANEL_VERIFY_SSL", "true").lower() not in ("0", "false", "no")

_sb_client: Client | None = None

def supabase() -> Client:
    global _sb_client
    if _sb_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Supabase env is missing (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).")
        _sb_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _sb_client

def panel_for_server(server: str) -> tuple[str | None, str | None]:
    name = server.strip().lower()
    if name.startswith("gr") or name == "greece":
        return PANEL_GR_URL, PANEL_GR_TOKEN
    if name.startswith("cz") or name in ("czechia", "czech"):
        return PANEL_CZ_URL, PANEL_CZ_TOKEN
    return None, None

def panel_headers(token: str | None) -> dict:
    h = {}
    if token:
        # try both styles, most panels accept one of them
        h["Authorization"] = f"Bearer {token}"
        h["X-API-Key"] = token
    return h
