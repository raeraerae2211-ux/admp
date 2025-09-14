import time, os, requests
from fastapi import APIRouter, Depends, HTTPException
from .deps import require_admin
from .models import DaysInfo, DaysSetReq, BroadcastReq
from .supa import sb_get_user_by_tgid, sb_update_user, sb_all_tgids
from .panel import fetch_panel_user, extract_expire_ts, days_from_expire, panel_create_or_update_user
from .config import TG_BOT_TOKEN

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/user/{tgid}/days", response_model=DaysInfo)
def get_days(tgid: int, _: str = Depends(require_admin)):
    user = sb_get_user_by_tgid(tgid)
    sup_days = None
    sup_exp = None

    if user:
        # prefer 'days' if present, else derive from 'expire'
        if user.get("days") is not None:
            try:
                sup_days = max(0, int(float(user["days"])))
            except Exception:
                sup_days = None
        if user.get("expire"):
            try:
                sup_exp = int(float(user["expire"]))
                if sup_days is None:
                    sup_days = days_from_expire(sup_exp)
            except Exception:
                sup_exp = None

    gr_payload = fetch_panel_user("Greece", str(tgid))
    cz_payload = fetch_panel_user("Czechia", str(tgid))
    gr_exp = extract_expire_ts(gr_payload)
    cz_exp = extract_expire_ts(cz_payload)

    return DaysInfo(
        tgid=tgid,
        supabase_days=sup_days,
        supabase_expire_ts=sup_exp,
        gr_expire_ts=gr_exp,
        cz_expire_ts=cz_exp,
        gr_days_left=days_from_expire(gr_exp),
        cz_days_left=days_from_expire(cz_exp),
    )

@router.post("/user/days/set")
def set_days(req: DaysSetReq, _: str = Depends(require_admin)):
    now = int(time.time())
    new_exp = now + int(req.days) * 86400
    user = sb_get_user_by_tgid(req.tgid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found in Supabase")
    sb_update_user(req.tgid, {"days": int(req.days), "expire": new_exp})

    if req.push_to_panels:
        for srv in ("Greece", "Czechia"):
            panel_create_or_update_user(srv, str(req.tgid), new_exp)

    return {"ok": True, "tgid": req.tgid, "new_expire": new_exp}

@router.post("/broadcast")
def broadcast(body: BroadcastReq, _: str = Depends(require_admin)):
    if not TG_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="TG_BOT_TOKEN is not set")
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    if body.tgid_list:
        ids = sorted({int(x) for x in body.tgid_list if int(x) > 0})
    else:
        ids = sb_all_tgids()

    sent = 0
    errors = 0
    for i, uid in enumerate(ids):
        try:
            requests.get(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                params={"chat_id": uid, "text": msg, "disable_web_page_preview": True},
                timeout=8,
            )
            sent += 1
        except Exception:
            errors += 1
        if i % 25 == 0:
            time.sleep(0.6)

    return {"ok": True, "targets": len(ids), "sent": sent, "errors": errors}
