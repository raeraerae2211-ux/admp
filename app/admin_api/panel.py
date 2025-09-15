import os, time, aiohttp
from typing import Optional, Dict, Any
from .models import PanelDays

def _auth_header(raw: str) -> str:
    if not raw:
        return ""
    low = raw.strip().lower()
    return raw if low.startswith("bearer ") else f"Bearer {raw}"

def _ssl_flag() -> bool:
    # True = проверять SSL, False = не проверять
    return str(os.getenv("PANEL_VERIFY_SSL", "true")).lower() not in ("0", "false", "no")

def _days_left(expire: Optional[int]) -> Optional[int]:
    if not expire:
        return None
    left = int(expire) - int(time.time())
    return max(0, (left + 86399) // 86400)


async def _fetch_user(base: str | None, auth: str | None, tgid: int) -> PanelDays:
    # нет адреса/токена → возвращаем ошибку, а НЕ None
    if not base or not auth:
        return PanelDays(error="not configured: missing PANEL_*_API_BASE or PANEL_*_AUTH")

    try:
        verify_ssl = os.getenv("PANEL_VERIFY_SSL", "true").lower() != "false"
        headers = {"Authorization": auth}            # может быть 'Bearer ...' или просто JWT
        url = f"{base}/api/user/{tgid}"

        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers, ssl=verify_ssl) as r:
                raw = await r.json(content_type=None)
                if r.status != 200:
                    return PanelDays(error=f"{r.status}: {raw}")
                # если у панели нет поля days — оставим None, но raw вернём
                days = raw.get("days") if isinstance(raw, dict) else None
                return PanelDays(days=days, raw=raw)

    except Exception as e:
        return PanelDays(error=str(e))

async def get_gr_by_tgid(tgid: int) -> PanelDays:
    return await _fetch_user(os.getenv("PANEL_GR_API_BASE"), os.getenv("PANEL_GR_AUTH"), tgid)

async def get_cz_by_tgid(tgid: int) -> PanelDays:
    return await _fetch_user(os.getenv("PANEL_CZ_API_BASE"), os.getenv("PANEL_CZ_AUTH"), tgid)

# --- НОВОЕ: SET для панелей ---
async def _set_user_days(base: str, auth: str, tgid: int, days: int) -> PanelDays:
    base = (base or "").rstrip("/")
    if not base or not auth:
        return PanelDays(error="not configured")

    new_expire = int(time.time()) + int(days) * 86400
    payload = {"expire": new_expire}

    headers = {
        "Authorization": _auth_header(auth),
        "Content-Type": "application/json",
    }
    connector = aiohttp.TCPConnector(ssl=_ssl_flag())
    async with aiohttp.ClientSession(connector=connector) as s:
        r = await s.put(f"{base}/api/user/{tgid}", headers=headers, json=payload)
        if r.status not in (200, 201):
            return PanelDays(error=f"PUT {r.status}: {await r.text()}")
        raw: Dict = await r.json()
        return PanelDays(days=_days_left(raw.get("expire")), raw=raw)

async def set_gr_by_tgid(tgid: int, days: int) -> PanelDays:
    try:
        return await _set_user_days(
            os.getenv("PANEL_GR_API_BASE", ""),
            os.getenv("PANEL_GR_AUTH", ""),
            tgid, days,
        )
    except Exception as e:
        return PanelDays(error=str(e))

async def set_cz_by_tgid(tgid: int, days: int) -> PanelDays:
    try:
        return await _set_user_days(
            os.getenv("PANEL_CZ_API_BASE", ""),
            os.getenv("PANEL_CZ_AUTH", ""),
            tgid, days,
        )
    except Exception as e:
        return PanelDays(error=str(e))