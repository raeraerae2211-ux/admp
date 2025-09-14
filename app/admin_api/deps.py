
import hmac, hashlib, json, urllib.parse, time
from fastapi import Depends, HTTPException, Header
from .config import TG_BOT_TOKEN, ADMIN_TG_WHITELIST

def _parse_init_data(raw: str) -> dict:
    pairs = urllib.parse.parse_qsl(raw, keep_blank_values=True)
    return {k: v for k, v in pairs}

def _verify_init_data(raw: str, bot_token: str) -> dict:
    if not raw or not bot_token:
        raise HTTPException(401, "No init data or bot token")
    data = _parse_init_data(raw)
    hash_ = data.pop("hash", None)
    if not hash_:
        raise HTTPException(401, "No hash in init data")

    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calc = hmac.new(secret_key, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, hash_):
        raise HTTPException(401, "Bad init data")

    try:
        auth_date = int(data.get("auth_date", "0"))
        if time.time() - auth_date > 60 * 60 * 24:
            raise HTTPException(401, "Init data expired")
    except Exception:
        pass

    user = {}
    if "user" in data:
        try:
            user = json.loads(data["user"])
        except Exception:
            pass
    return user

def require_admin_tg(init_data: str | None = Header(default=None, alias="X-Tg-Init-Data")):
    user = _verify_init_data(init_data or "", TG_BOT_TOKEN)
    tgid = int(user.get("id") or 0)
    if not tgid:
        raise HTTPException(401, "No Telegram user")
    if ADMIN_TG_WHITELIST and tgid not in ADMIN_TG_WHITELIST:
        raise HTTPException(403, "Not allowed")
    return {"tgid": tgid, "user": user}
