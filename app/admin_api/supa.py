import os
from typing import Optional, Any
from supabase import create_client, Client
import anyio

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

TABLE = os.getenv("SUPABASE_TABLE", "test")
TG_COL = os.getenv("SUPABASE_TGID_COLUMN", "tgid")
DAYS_COL = os.getenv("SUPABASE_DAYS_COLUMN", "days")

_cli: Optional[Client] = None
def _client() -> Optional[Client]:
    global _cli
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    if _cli is None:
        _cli = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _cli

async def get_days_by_tgid(tgid: int) -> Optional[int]:
    cli = _client()
    if not cli:
        return None

    def _q() -> Optional[int]:
        r = cli.table(TABLE).select(DAYS_COL).eq(TG_COL, tgid).limit(1).execute()
        data = getattr(r, "data", None)
        if not data: return None
        row = data[0] if isinstance(data, list) else data
        val = row.get(DAYS_COL) if isinstance(row, dict) else None
        try: return int(val) if val is not None else None
        except: return None

    return await anyio.to_thread.run_sync(_q)

async def set_days_by_tgid(tgid: int, days: int) -> dict[str, Any]:
    cli = _client()
    if not cli:
        return {"error": "no supabase client"}

    def _upsert() -> dict[str, Any]:
        r = cli.table(TABLE).upsert({TG_COL: tgid, DAYS_COL: int(days)}, on_conflict=TG_COL).execute()
        return {"ok": True, "rows": getattr(r, "data", None)}

    return await anyio.to_thread.run_sync(_upsert)