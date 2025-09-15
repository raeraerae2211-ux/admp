from fastapi import APIRouter, Depends
from .deps import require_admin_tg
from .supa import get_days_by_tgid, set_days_by_tgid
from .panel import get_days_gr, set_days_gr, get_days_cz, set_days_cz
from .models import DaysInfo, DaysSetReq, BroadcastReq
import asyncio, os, aiohttp

router = APIRouter()

@router.get("/admin/user/{tgid}/days", response_model=DaysInfo)
async def admin_user_days(tgid: int, admin=Depends(require_admin_tg)):
    supa = await get_days_by_tgid(tgid)
    gr = await get_days_gr(tgid)
    cz = await get_days_cz(tgid)
    return {"tgid": tgid, "supabase_days": supa, "gr_days": gr, "cz_days": cz}

@router.post("/admin/user/days/set")
async def admin_user_days_set(body: DaysSetReq, admin=Depends(require_admin_tg)):
    results = {}
    if body.supabase_days is not None:
        await set_days_by_tgid(body.tgid, body.supabase_days)
        results["supabase"] = {"ok": True, "days": body.supabase_days}
    tasks, labels = [], []
    if body.gr_days is not None:
        tasks.append(set_days_gr(body.tgid, body.gr_days)); labels.append("gr")
    if body.cz_days is not None:
        tasks.append(set_days_cz(body.tgid, body.cz_days)); labels.append("cz")
    if tasks:
        outs = await asyncio.gather(*tasks, return_exceptions=True)
        for lbl, r in zip(labels, outs):
            results[lbl] = (r if isinstance(r, dict) else {"error": str(r)}) or {"ok": True}
    return {"ok": True, "results": results}

@router.post("/admin/broadcast")
async def admin_broadcast(body: BroadcastReq, admin=Depends(require_admin_tg)):
    import os, aiohttp
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
                "text": body.text,                 # <-- ВАЖНО: body.text
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