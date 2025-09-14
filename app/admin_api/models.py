from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class PanelDays(BaseModel):
    days: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DaysInfo(BaseModel):
    tgid: int
    supabase_days: Optional[int] = None
    supabase_raw: Optional[Dict[str, Any]] = None
    gr: Optional[PanelDays] = None
    cz: Optional[PanelDays] = None

class DaysSetReq(BaseModel):
    tgid: int
    days: int = Field(ge=0)
    sync_supabase: bool = True
    sync_gr: bool = False
    sync_cz: bool = False

class BroadcastReq(BaseModel):
    text: str
    tgid_list: Optional[List[int]] = None

# --- алиасы для совместимости со старым роутером ---
DaysResp      = DaysInfo
SetDaysBody   = DaysSetReq
BroadcastBody = BroadcastReq