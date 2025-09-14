
import os

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
ADMIN_TG_WHITELIST = {
    int(x) for x in os.getenv("ADMIN_TG_WHITELIST", "").replace(" ", "").split(",") if x.isdigit()
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "test")
SUPABASE_TGID_COLUMN = os.getenv("SUPABASE_TGID_COLUMN", "tgid")
SUPABASE_DAYS_COLUMN = os.getenv("SUPABASE_DAYS_COLUMN", "days")
SUPABASE_EXPIRE_COLUMN = os.getenv("SUPABASE_EXPIRE_COLUMN", "expire")

PANEL_GR_URL = os.getenv("PANEL_GR_URL", "").rstrip("/")
PANEL_GR_TOKEN = os.getenv("PANEL_GR_TOKEN", "")
PANEL_CZ_URL = os.getenv("PANEL_CZ_URL", "").rstrip("/")
PANEL_CZ_TOKEN = os.getenv("PANEL_CZ_TOKEN", "")
PANEL_VERIFY_SSL = os.getenv("PANEL_VERIFY_SSL", "true").lower() == "true"

TG_BOT_API = "https://api.telegram.org"

def supabase_rest_url(table: str) -> str:
    if not SUPABASE_URL:
        return ""
    return f"{SUPABASE_URL}/rest/v1/{table}"
