
import time, datetime, requests
from typing import Optional, Tuple, Dict, Any, List
from .config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_TABLE,
    SUPABASE_TGID_COLUMN, SUPABASE_DAYS_COLUMN, SUPABASE_EXPIRE_COLUMN,
    supabase_rest_url
)

HEADERS = {}
if SUPABASE_SERVICE_ROLE_KEY:
    HEADERS = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _infer_days(row: Dict[str, Any]) -> Optional[int]:
    if SUPABASE_DAYS_COLUMN in row and isinstance(row[SUPABASE_DAYS_COLUMN], (int, float)):
        try:
            return int(row[SUPABASE_DAYS_COLUMN])
        except Exception:
            pass
    exp = row.get(SUPABASE_EXPIRE_COLUMN)
    if exp is None:
        return None
    try:
        if isinstance(exp, (int, float)):
            sec = int(exp)
        elif isinstance(exp, str):
            if exp.isdigit():
                sec = int(exp)
            else:
                dt = datetime.datetime.fromisoformat(exp.replace("Z","+00:00"))
                sec = int(dt.timestamp())
        else:
            return None
        now = int(time.time())
        if sec <= now:
            return 0
        return (sec - now) // 86400
    except Exception:
        return None

def get_user_row(tgid: int) -> Optional[Dict[str, Any]]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    url = supabase_rest_url(SUPABASE_TABLE)
    params = {f"{SUPABASE_TGID_COLUMN}": f"eq.{tgid}", "select": "*", "limit": "1"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    return data[0] if data else None

def list_all_tgids(limit: int = 10000) -> List[int]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return []
    url = supabase_rest_url(SUPABASE_TABLE)
    params = {"select": SUPABASE_TGID_COLUMN, "limit": str(limit)}
    r = requests.get(url, headers=HEADERS, params=params, timeout=60)
    if r.status_code != 200:
        return []
    return [int(x[SUPABASE_TGID_COLUMN]) for x in r.json() if SUPABASE_TGID_COLUMN in x]

def get_days_from_supabase(tgid: int) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    row = get_user_row(tgid)
    if not row:
        return None, None
    days = _infer_days(row)
    return days, row

def set_days_in_supabase(tgid: int, days: int) -> Optional[Dict[str, Any]]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    current = get_user_row(tgid)
    url = supabase_rest_url(SUPABASE_TABLE)
    import json as _json
    if current:
        r = requests.patch(f"{url}?{SUPABASE_TGID_COLUMN}=eq.{tgid}", headers=HEADERS, data=_json.dumps({SUPABASE_DAYS_COLUMN: days}), timeout=30)
        if r.status_code in (200, 204):
            return r.json()[0] if r.content else current
        return None
    else:
        payload = {SUPABASE_TGID_COLUMN: tgid, SUPABASE_DAYS_COLUMN: days}
        r = requests.post(url, headers=HEADERS, data=_json.dumps(payload), timeout=30)
        if r.status_code in (201, 200):
            return r.json()[0] if r.content else payload
        return None
