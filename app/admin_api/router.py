from fastapi import APIRouter, Depends
from .deps import require_admin_tg
from .supa import get_days_by_tgid, set_days_by_tgid
from .panel import get_days_gr, set_days_gr, get_days_cz, set_days_cz
from .models import DaysResp, SetDaysBody, BroadcastBody
import asyncio, os

router = APIRouter()

@router.get("/admin/user/{tgid}/days", response_model=DaysResp)
async def admin_user_days(tgid: int, admin=Depends(require_admin_tg)):
    supa = await get_days_by_tgid(tgid)
    gr = await get_days_gr(tgid) if (os.getenv("PANEL_GR_API_BASE") or os.getenv("PANEL_GR_GET_URL")) else None
    cz = await get_days_cz(tgid) if (os.getenv("PANEL_CZ_API_BASE") or os.getenv("PANEL_CZ_GET_URL")) else None
    return {"tgid": tgid, "supabase_days": supa, "gr_days": gr, "cz_days": cz}

@router.post("/admin/user/days/set")
async def admin_user_days_set(body: SetDaysBody, admin=Depends(require_admin_tg)):
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