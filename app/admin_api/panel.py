import time, requests
from typing import Optional, Dict, Any
from fastapi import HTTPException
from .config import panel_for_server, panel_headers, PANEL_VERIFY_SSL

def fetch_panel_user(server: str, username: str) -> Dict[str, Any]:
    base, token = panel_for_server(server)
    if not base:
        return {}
    url = f"{base.rstrip('/')}/user/{username}"
    r = requests.get(url, headers=panel_headers(token), timeout=15, verify=PANEL_VERIFY_SSL)
    if r.status_code == 404:
        return {}
    if r.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"{server} panel error: {r.status_code} {r.text}")
    try:
        return r.json() if "json" in (r.headers.get("content-type","").lower()) else {}
    except Exception:
        return {}

def extract_expire_ts(payload: Dict[str, Any]) -> Optional[int]:
    if not isinstance(payload, dict):
        return None
    cand = []
    for root in (payload, payload.get("user") if isinstance(payload.get("user"), dict) else {}):
        if not isinstance(root, dict):
            continue
        for k in ("expire", "expire_ts", "end", "end_ts"):
            if k in root and root[k] is not None:
                try:
                    cand.append(int(float(root[k])))
                except Exception:
                    pass
    return max(cand) if cand else None

def days_from_expire(expire_ts: Optional[int], now_ts: Optional[int] = None) -> int:
    if not expire_ts:
        return 0
    now = int(now_ts or time.time())
    left = int(expire_ts) - now
    return 0 if left <= 0 else (left + 86399) // 86400

def panel_create_or_update_user(server: str, username: str, expire_ts: int) -> None:
    base, token = panel_for_server(server)
    if not base:
        return
    url = f"{base.rstrip('/')}/user/{username}"
    # Try PUT first, fallback to POST
    data = {"expire": int(expire_ts)}
    h = panel_headers(token)
    r = requests.put(url, json=data, headers=h, timeout=20, verify=PANEL_VERIFY_SSL)
    if r.status_code in (404, 405):
        r = requests.post(url, json=data, headers=h, timeout=20, verify=PANEL_VERIFY_SSL)
    if r.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"{server} panel update failed: {r.status_code} {r.text}")
