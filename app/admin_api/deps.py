import os, hmac, hashlib, urllib.parse
from fastapi import Header, HTTPException, status

BOT_TOKEN = os.getenv("TG_BOT_TOKEN") or ""
ADMIN_WHITELIST = {int(x) for x in (os.getenv("ADMIN_TG_WHITELIST") or "").replace(";", ",").split(",") if x.strip().isdigit()}

def _check_init_data(init_data: str) -> dict:
    if not BOT_TOKEN:
        raise HTTPException(status_code=401, detail="No bot token")
    if not init_data:
        raise HTTPException(status_code=401, detail="No init data")

    parts = dict(x.split("=", 1) for x in init_data.split("&") if "=" in x)
    data_check_string = "\n".join(f"{k}={urllib.parse.unquote_plus(v)}"
                                  for k, v in sorted(parts.items()) if k != "hash")
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if calc_hash != parts.get("hash"):
        raise HTTPException(status_code=401, detail="Bad init data")
    return parts

async def require_admin_tg(x_tg_init_data: str = Header(default="")):
    data = _check_init_data(x_tg_init_data)
    user_str = data.get("user", "")
    # выдёргиваем id пользователя из JSON в user=
    uid = None
    try:
        import json
        uid = json.loads(urllib.parse.unquote_plus(user_str)).get("id")
    except Exception:
        pass
    if not uid or int(uid) not in ADMIN_WHITELIST:
        raise HTTPException(status_code=403, detail="Not allowed")
    return {"tgid": int(uid)}