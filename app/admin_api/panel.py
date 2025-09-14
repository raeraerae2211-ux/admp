import os, aiohttp, datetime as dt
from typing import Optional

# Греция
GR_BASE = os.getenv("PANEL_GR_API_BASE") or ""     # например: http(s)://host:8000
GR_AUTH = os.getenv("PANEL_GR_AUTH") or ""         # Bearer <jwt> (или Basic ...)

# Чехия
CZ_BASE = os.getenv("PANEL_CZ_API_BASE") or ""
CZ_AUTH = os.getenv("PANEL_CZ_AUTH") or ""

def _hdr(auth: str):
    return {"Authorization": auth} if auth else {}

async def _get_days(base: str, auth: str, tgid: int) -> Optional[int]:
    if not base: return None
    url = f"{base.rstrip('/')}/api/user/{tgid}"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=_hdr(auth), ssl=False) as r:
            if r.status != 200: return None
            j = await r.json()
    # Marzban отдаёт expire в секундах (unix). Считаем дни.
    exp = j.get("expire") or j.get("expiry_time") or j.get("expire_at")
    if not exp: return None
    # если iso-строка
    if isinstance(exp, str):
        try:
            exp_dt = dt.datetime.fromisoformat(exp.replace("Z","+00:00"))
            exp_ts = int(exp_dt.timestamp())
        except: return None
    else:
        exp_ts = int(exp)
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    left = max(0, (exp_ts - now) // 86400)
    return int(left)

async def _set_days(base: str, auth: str, tgid: int, days: int):
    if not base: return {"error": "no base"}
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    expire = now + int(days) * 86400
    url = f"{base.rstrip('/')}/api/user/{tgid}"
    body = {"expire": expire}
    async with aiohttp.ClientSession() as s:
        async with s.put(url, json=body, headers=_hdr(auth), ssl=False) as r:
            if r.status not in (200, 201): 
                return {"error": f"http {r.status}"}
            try: data = await r.json()
            except: data = {"ok": True}
    return data or {"ok": True}

# внешние функции под роутер
async def get_days_gr(tgid: int) -> Optional[int]: return await _get_days(GR_BASE, GR_AUTH, tgid)
async def set_days_gr(tgid: int, days: int):       return await _set_days(GR_BASE, GR_AUTH, tgid, days)
async def get_days_cz(tgid: int) -> Optional[int]: return await _get_days(CZ_BASE, CZ_AUTH, tgid)
async def set_days_cz(tgid: int, days: int):       return await _set_days(CZ_BASE, CZ_AUTH, tgid, days)