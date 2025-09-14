# app/admin_api/deps.py
import os, time, hmac, hashlib, json, urllib.parse
from fastapi import Header, HTTPException

from .config import TG_BOT_TOKEN, ADMIN_TG_WHITELIST

MAX_AGE = int(os.getenv("TG_INIT_MAX_AGE", "86400"))  # 24 часа по умолчанию

def _verify_init_data(init_data: str, bot_token: str):
    if not bot_token:
        raise HTTPException(status_code=401, detail="Bot token not set")

    # Разбираем "query string" из Telegram WebApp: key=value&key2=value2...
    try:
        pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        data = dict(pairs)
    except Exception:
        raise HTTPException(status_code=401, detail="Bad init data")

    hash_value = data.pop("hash", None)
    if not hash_value:
        raise HTTPException(status_code=401, detail="Bad init data")

    # Строка проверки (Telegram spec): отсортированные по ключу "k=v", соединённые \n
    check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data.keys()))

    # Секретный ключ: HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, hash_value):
        raise HTTPException(status_code=401, detail="Bad init data")

    # Доп.проверка "свежести" подписи (по умолчанию 24ч)
    try:
        auth_date = int(data.get("auth_date", "0"))
    except Exception:
        auth_date = 0
    if auth_date and (time.time() - auth_date) > MAX_AGE:
        raise HTTPException(status_code=401, detail="Init data too old")

    # tgid берём из user
    try:
        user = json.loads(data.get("user") or "{}")
        tgid = int(user.get("id") or 0)
    except Exception:
        tgid = 0
        user = {}

    if not tgid:
        raise HTTPException(status_code=401, detail="Bad user in init data")

    return {"tgid": tgid, "user": user}