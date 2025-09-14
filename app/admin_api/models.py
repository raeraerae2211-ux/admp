from pydantic import BaseModel

class DaysResp(BaseModel):
    tgid: int
    supabase_days: int | None = None
    gr_days: int | None = None
    cz_days: int | None = None

class SetDaysBody(BaseModel):
    tgid: int
    supabase_days: int | None = None
    gr_days: int | None = None
    cz_days: int | None = None

class BroadcastBody(BaseModel):
    message: str
    tgid_list: list[int] | None = None
    protect: bool | None = False