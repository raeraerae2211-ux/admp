from pydantic import BaseModel, Field
from typing import Optional, List

class DaysInfo(BaseModel):
    tgid: int
    supabase_days: Optional[int] = None
    supabase_expire_ts: Optional[int] = None
    gr_expire_ts: Optional[int] = None
    cz_expire_ts: Optional[int] = None
    gr_days_left: int = 0
    cz_days_left: int = 0

class DaysSetReq(BaseModel):
    tgid: int
    days: int = Field(..., ge=0)
    push_to_panels: bool = True

class BroadcastReq(BaseModel):
    message: str
    tgid_list: Optional[List[int]] = None  # None => broadcast to all users
    protect: bool = True
