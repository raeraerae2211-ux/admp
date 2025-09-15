# app/admin_api/panel.py
import os
import ssl as _ssl
import aiohttp
from datetime import datetime, timezone
from .models import PanelDays

VERIFY_SSL = os.getenv("PANEL_VERIFY_SSL", "true").lower() != "false"

def _ssl_ctx():
    if VERIFY_SSL:
        return None
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    return ctx

async def _fetch_user(base: str, auth: str, tgid: int) -> PanelDays:
    if not base or not auth:
        return PanelDays(error="not configured")

    url = f"{base.rstrip('/')}/user/{tgid}"
    headers = {"Authorization": auth}
    timeout = aiohttp.ClientTimeout(total=12)

    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.get(url, headers=headers, ssl=_ssl_ctx()) as r:
            raw = await r.json(content_type=None)
            if r.status != 200:
                return PanelDays(error=f"http {r.status}: {raw}")

            # вытаскиваем expire и считаем дни
            exp = raw.get("expire") or raw.get("expires_at") or raw.get("expired_at")
            days = None
            if exp:
                try:
                    if isinstance(exp, (int, float)):
                        ts = int(exp)
                    else:
                        # вдруг ISO-строка
                        ts = int(datetime.fromisoformat(str(exp)).replace(
                            tzinfo=timezone.utc).timestamp())
                    now = int(datetime.now(timezone.utc).timestamp())
                    days = max(0, (ts - now) // 86400)
                except Exception:
                    pass
            return PanelDays(days=days, raw=raw)

async def get_gr_by_tgid(tgid: int) -> PanelDays:
    try:
        return await _fetch_user(
            os.getenv("PANEL_GR_API_BASE", ""),
            os.getenv("PANEL_GR_AUTH", ""),
            tgid,
        )
    except Exception as e:
        return PanelDays(error=str(e))

async def get_cz_by_tgid(tgid: int) -> PanelDays:
    try:
        return await _fetch_user(
            os.getenv("PANEL_CZ_API_BASE", ""),
            os.getenv("PANEL_CZ_AUTH", ""),
            tgid,
        )
    except Exception as e:
        return PanelDays(error=str(e))