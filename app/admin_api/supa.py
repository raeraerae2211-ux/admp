from .config import supabase
from typing import Any, Dict, Optional, List

USERS_TABLE = "users_app"   # adjust to your actual table name

def sb_get_user_by_tgid(tgid: int) -> Optional[Dict[str, Any]]:
    r = supabase().table(USERS_TABLE).select("*").eq("tgid", tgid).limit(1).execute()
    data = r.data or []
    return (data[0] if data else None)

def sb_update_user(tgid: int, patch: Dict[str, Any]) -> None:
    supabase().table(USERS_TABLE).update(patch).eq("tgid", tgid).execute()

def sb_all_tgids(limit: int = 500000) -> List[int]:
    r = supabase().table(USERS_TABLE).select("tgid").limit(limit).execute()
    return [int(x["tgid"]) for x in (r.data or []) if x.get("tgid") is not None]
