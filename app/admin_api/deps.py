# app/admin_api/deps.py
import os
import time
import hmac
import json
import hashlib
import urllib.parse
from fastapi import Header, HTTPException

from .config import TG_BOT_TOKEN, ADMIN_TG_WHITELIST

# сколько времени считаем подпись «свежей» (по умолчанию 24ч)
MAX_AGE = int(os.getenv("TG_INIT_MAX_AGE", "86400"))


def _parse_whitelist(s: str | None) -> set[int]:
    ids: set[int] = set()
    for part in (s or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            pass
    return ids


def _verify_init_data(init_data: str, bot_token: str) -> dict:
    if not bot_token:
        raise HTTPException(status_code=401, detail="Bot token not set")

    # Разбираем querystring из Telegram WebApp
    try:
        pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        data = dict(pairs)
    except Exception:
        raise HTTPException(status_code=401, detail="Bad init data")

    hash_value = data.pop("hash", None)
    if not hash_value:
        raise HTTPException(status_code=401, detail="Bad init data")

    # Строка проверки: сортируем ключи и склеиваем "k=v" через \n
    check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data.keys()))

    # Секрет: HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, hash_value):
        raise HTTPException(status_code=401, detail="Bad init data")

    # Свежесть подписи
    try:
        auth_date = int(data.get("auth_date", "0"))
    except Exception:
        auth_date = 0
    if auth_date and (time.time() - auth_date) > MAX_AGE:
        raise HTTPException(status_code=401, detail="Init data too old")

    # TGID берём из user
    try:
        user = json.loads(data.get("user") or "{}")
        tgid = int(user.get("id") or 0)
    except Exception:
        user, tgid = {}, 0

    if not tgid:
        raise HTTPException(status_code=401, detail="Bad user in init data")

    return {"tgid": tgid, "user": user}


def require_admin_tg(init_data: str | None = Header(default=None, alias="X-Tg-Init-Data")) -> dict:
    """
    Зависимость FastAPI: валидирует initData, проверяет whitelist.
    Для отладки поддерживает DEV_SKIP_TG_CHECK/DEV_TGID.
    """
    # Временный обход проверки (для дебага)
    if os.getenv("DEV_SKIP_TG_CHECK") == "1":
        fake_id = int(os.getenv("DEV_TGID", "0") or 0)
        if not fake_id:
            raise HTTPException(status_code=403, detail="DEV_TGID not set")
        return {"tgid": fake_id, "user": {"id": fake_id}}

    # Реальная проверка подписи
    res = _verify_init_data((init_data or ""), TG_BOT_TOKEN)

    # Проверяем, что админ
    wl_env = os.getenv("ADMIN_TG_WHITELIST", ADMIN_TG_WHITELIST)
    wl = _parse_whitelist(wl_env)
    if wl and res["tgid"] not in wl:
        raise HTTPException(status_code=403, detail="Not allowed")

    return res