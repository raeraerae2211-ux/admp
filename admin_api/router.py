
from fastapi import APIRouter, Depends, HTTPException
import requests
from typing import Optional
from .deps import require_admin_tg
from .models import DaysInfo, DaysSetReq, BroadcastReq, PanelDays
from .supa import get_days_from_supabase, set_days_in_supabase, list_all_tgids
from .panel import gr_get, gr_set, cz_get, cz_set
from .config import TG_BOT_TOKEN, TG_BOT_API

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/user/{tgid}/days", response_model=DaysInfo)
def get_days(tgid: int, _: dict = Depends(require_admin_tg)):
    s_days, s_raw = get_days_from_supabase(tgid)
    gr = gr_get(str(tgid))
    cz = cz_get(str(tgid))
    return DaysInfo(
        tgid=tgid,
        supabase_days=s_days,
        supabase_raw=s_raw,
        gr=PanelDays(**gr),
        cz=PanelDays(**cz),
    )

@router.post("/user/days/set")
def set_days(req: DaysSetReq, _: dict = Depends(require_admin_tg)):
    result = {"supabase": None, "gr": None, "cz": None}
    if req.sync_supabase:
        result["supabase"] = set_days_in_supabase(req.tgid, req.days)
        if result["supabase"] is None:
            raise HTTPException(500, "Failed to update Supabase")
    if req.sync_gr:
        result["gr"] = gr_set(str(req.tgid), req.days)
    if req.sync_cz:
        result["cz"] = cz_set(str(req.tgid), req.days)
    return {"ok": True, "result": result}

def _send_bot_message(chat_id: int, text: str) -> Optional[dict]:
    if not TG_BOT_TOKEN:
        return None
    url = f"{TG_BOT_API}/bot{TG_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    try:
        return r.json()
    except Exception:
        return {"status_code": r.status_code, "text": r.text}

@router.post("/broadcast")
def broadcast(body: BroadcastReq, _: dict = Depends(require_admin_tg)):
    targets = body.tgid_list or list_all_tgids(limit=100000)
    sent = 0
    fails = 0
    for t in targets:
        res = _send_bot_message(t, body.text)
        if res and res.get("ok"):
            sent += 1
        else:
            fails += 1
    return {"ok": True, "sent": sent, "failed": fails, "total": len(targets)}
