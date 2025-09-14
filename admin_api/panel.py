
from typing import Optional, Dict, Any
import time, requests
from .config import PANEL_GR_URL, PANEL_GR_TOKEN, PANEL_CZ_URL, PANEL_CZ_TOKEN, PANEL_VERIFY_SSL

def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def _get_panel(base: str, token: str, username: str) -> Optional[Dict[str, Any]]:
    if not base or not token:
        return None
    try:
        r = requests.get(f"{base}/user/{username}", headers=_auth_headers(token), timeout=30, verify=PANEL_VERIFY_SSL)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "raw": r.text}
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def _set_panel_days(base: str, token: str, username: str, days: int) -> Optional[Dict[str, Any]]:
    if not base or not token:
        return None
    try:
        import json as _json
        payload = {"days": days}
        r = requests.put(f"{base}/user/{username}", headers=_auth_headers(token), data=_json.dumps(payload), timeout=30, verify=PANEL_VERIFY_SSL)
        if r.status_code not in (200, 204):
            return {"error": f"HTTP {r.status_code}", "raw": r.text}
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}

def _to_days_from_panel(obj: Dict[str, Any]) -> Optional[int]:
    if not obj or "error" in obj:
        return None
    exp = obj.get("expire") or obj.get("expires_at") or obj.get("expiry")
    if exp is None:
        d = obj.get("days")
        return int(d) if isinstance(d, int) else None
    try:
        now = int(time.time())
        if isinstance(exp, (int, float)): sec = int(exp)
        elif isinstance(exp, str):
            if exp.isdigit(): sec = int(exp)
            else:
                import datetime
                dt = datetime.datetime.fromisoformat(exp.replace("Z","+00:00"))
                sec = int(dt.timestamp())
        else: return None
        if sec <= now: return 0
        return (sec - now)//86400
    except Exception:
        return None

def gr_get(username: str) -> Dict[str, Any]:
    data = _get_panel(PANEL_GR_URL, PANEL_GR_TOKEN, username)
    return {"days": _to_days_from_panel(data), "raw": data, "error": data.get("error") if isinstance(data, dict) else None} if isinstance(data, dict) else {"days": None, "raw": data}

def gr_set(username: str, days: int) -> Dict[str, Any]:
    res = _set_panel_days(PANEL_GR_URL, PANEL_GR_TOKEN, username, days)
    return res or {"error": "panel not configured"}

def cz_get(username: str) -> Dict[str, Any]:
    data = _get_panel(PANEL_CZ_URL, PANEL_CZ_TOKEN, username)
    return {"days": _to_days_from_panel(data), "raw": data, "error": data.get("error") if isinstance(data, dict) else None} if isinstance(data, dict) else {"days": None, "raw": data}

def cz_set(username: str, days: int) -> Dict[str, Any]:
    res = _set_panel_days(PANEL_CZ_URL, PANEL_CZ_TOKEN, username, days)
    return res or {"error": "panel not configured"}
