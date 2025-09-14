# app/admin_api/models.py
from pydantic import BaseModel

# Ответ для /admin/user/{tgid}/days
class DaysResp(BaseModel):
    tgid: int
    supabase_days: int | None = None
    gr_days: int | None = None
    cz_days: int | None = None

# Тело запроса для /admin/user/days/set
class SetDaysBody(BaseModel):
    tgid: int
    supabase_days: int | None = None   # поставить дни в Supabase (если указан)
    gr_days: int | None = None         # поставить дни в панели Греции (если указан)
    cz_days: int | None = None         # поставить дни в панели Чехии (если указан)

# Тело запроса для /admin/broadcast
class BroadcastBody(BaseModel):
    message: str
    tgid_list: list[int] | None = None   # если None — отправка всем
    protect: bool | None = False         # без предпросмотра/защиты (оставим флаг на будущее)