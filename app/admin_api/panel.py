import os, aiohttp
from datetime import datetime, timezone, timedelta
from typing import Any

GR_BASE = os.getenv("PANEL_GR_API_BASE")
GR_AUTH = os.getenv("PANEL_GR_AUTH")      # 'Bearer ...'
CZ_BASE = os.getenv("PANEL_CZ_API_BASE")
CZ_AUTH = os.getenv("PANEL_CZ_AUTH")
TIMEOUT = int(os.getenv("PANEL_TIMEOUT", "10"))
INSECURE = os.getenv("PANEL_INSECURE_SSL") == "1"

def _now_s() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())

def _days_from_expire(exp: Any) -> int | None:
    if exp is None:
        return None
    try:
        exp = int(exp)
        # если пришли миллисекунды — переведём в секунды
        if exp > 10_000_000_000:  # > ~2286 года в секундах
            exp //= 1000
        delta = exp - _now_s()
        return max(0, delta // 86400)
    except Exception:
        return None

def _expire_from_days(days: int) -> int:
    return _now_s() + int(days) * 86400

async def _req(method: str, url: str, headers: dict | None = None, json: dict | None = None):
    if not url:
        return 0, {"error": "no url"}
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.request(method, url, headers=headers, json=json, ssl=not INSECURE) as r:
            ct = (r.headers.get("content-type") or "").lower()
            data = await (r.json() if "application/json" in ct else r.text())
            return r.status, data

# ===== ГРЕЦИЯ (по tgid) =====
async def get_days_gr(tgid: int) -> int | None:
    if not GR_BASE: return None
    st, data = await _req("GET", f"{GR_BASE}/api/user/{tgid}", {"Authorization": GR_AUTH})
    if isinstance(data, dict):
        # Marzban обычно отдаёт expire (unix seconds / ms)
        return _days_from_expire(data.get("expire") or data.get("expired_at") or data.get("expires"))
    return None

async def set_days_gr(tgid: int, days: int):
    if not GR_BASE: return None
    payload = {"expire": _expire_from_days(days)}
    st, data = await _req("PUT", f"{GR_BASE}/api/user/{tgid}", {"Authorization": GR_AUTH}, payload)
    return data if isinstance(data, dict) else {"status": st, "data": data}

# ===== ЧЕХИЯ (по tgid) =====
async def get_days_cz(tgid: int) -> int | None:
    if not CZ_BASE: return None
    st, data = await _req("GET", f"{CZ_BASE}/api/user/{tgid}", {"Authorization": CZ_AUTH})
    if isinstance(data, dict):
        return _days_from_expire(data.get("expire") or data.get("expired_at") or data.get("expires"))
    return None

async def set_days_cz(tgid: int, days: int):
    if not CZ_BASE: return None
    payload = {"expire": _expire_from_days(days)}
    st, data = await _req("PUT", f"{CZ_BASE}/api/user/{tgid}", {"Authorization": CZ_AUTH}, payload)
    return data if isinstance(data, dict) else {"status": st, "data": data}