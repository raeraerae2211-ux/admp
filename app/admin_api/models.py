from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
import re

class BroadcastReq(BaseModel):
    text: str = Field(min_length=1)
    tgid_list: Optional[List[int]] = None

    # совместимость: принимаем "message", строковые списки и пр.
    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs):  # pydantic v2
        if isinstance(obj, dict):
            data: Dict[str, Any] = dict(obj)
            if "text" not in data and "message" in data:
                data["text"] = data.pop("message")

            if "tgid_list" in data and isinstance(data["tgid_list"], str):
                parts = re.split(r"[, \n\r\t]+", data["tgid_list"])
                data["tgid_list"] = [int(x) for x in parts if x.isdigit()]

            if "tgids" in data and "tgid_list" not in data:
                v = data["tgids"]
                if isinstance(v, str):
                    parts = re.split(r"[, \n\r\t]+", v)
                    data["tgid_list"] = [int(x) for x in parts if x.isdigit()]
                elif isinstance(v, list):
                    data["tgid_list"] = [int(x) for x in v if str(x).isdigit()]

            obj = data
        return super().model_validate(obj, *args, **kwargs)