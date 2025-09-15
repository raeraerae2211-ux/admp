from fastapi import APIRouter, Depends
from .deps import require_admin_tg
from .supa import get_days_by_tgid, set_days_by_tgid
from .panel import get_gr_by_tgid, get_cz_by_tgid, set_cz_by_tgid, set_gr_by_tgid
from .models import DaysInfo, DaysSetReq, BroadcastReq
import asyncio, os, aiohttp

router = APIRouter()

@router.get("/admin/user/{tgid}/days", response_model=DaysInfo)
async def admin_user_days(tgid: int, admin=Depends(require_admin_tg)):
    supa = await get_days_by_tgid(tgid)
    gr = await get_gr_by_tgid(tgid)   # всегда возвращает PanelDays (с error при проблеме)
    cz = await get_cz_by_tgid(tgid)   # всегда возвращает PanelDays (с error при проблеме)
    # ВАЖНО: возвращаем ключи gr / cz, иначе Pydantic выкинет поля
    return {"tgid": tgid, "supabase_days": supa, "gr": gr, "cz": cz}

@router.post("/admin/user/days/set")
async def admin_user_days_set(body: DaysSetReq, admin=Depends(require_admin_tg)):
    results = {}

    # Supabase
    if body.sync_supabase:
        await set_days_by_tgid(body.tgid, body.days)
        results["supabase"] = {"ok": True, "days": body.days}

    # Панели (GR/CZ) — ставим те же body.days
    tasks, labels = [], []
    if body.sync_gr and callable(set_gr_by_tgid):
        tasks.append(set_gr_by_tgid(body.tgid, body.days)); labels.append("gr")
    if body.sync_cz and callable(set_cz_by_tgid):
        tasks.append(set_cz_by_tgid(body.tgid, body.days)); labels.append("cz")

    if tasks:
        outs = await asyncio.gather(*tasks, return_exceptions=True)
        for lbl, r in zip(labels, outs):
            if isinstance(r, Exception):
                results[lbl] = {"error": str(r)}
            else:
                # r — это PanelDays; FastAPI сам сериализует в {days, raw, error}
                results[lbl] = r

    return {"ok": True, "results": results}

@router.post("/admin/broadcast")
async def admin_broadcast(body: BroadcastReq, admin=Depends(require_admin_tg)):
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        return {"error": "no bot token"}

    chat_ids = body.tgid_list
    if not chat_ids:
        # берём всех из Supabase
        from .supa import _client, TABLE, TG_COL
        cli = _client()
        if not cli:
            return {"error": "no supabase client"}
        rows = cli.table(TABLE).select(TG_COL).execute().data or []
        chat_ids = [int(r[TG_COL]) for r in rows if r.get(TG_COL)]

    sent, errors = 0, []
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    async with aiohttp.ClientSession() as s:
        for cid in chat_ids:
            payload = {
                "chat_id": cid,
                "text": body.text,
                "disable_web_page_preview": True,
                "protect_content": False,
            }
            try:
                async with s.post(url, json=payload) as r:
                    if r.status == 200:
                        sent += 1
                    else:
                        errors.append({"tgid": cid, "status": r.status, "body": await r.text()})
            except Exception as e:
                errors.append({"tgid": cid, "error": str(e)})

    return {"ok": True, "sent": sent, "errors": errors}