from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from .config import ADMIN_API_TOKEN

_bearer = HTTPBearer(auto_error=True)

def require_admin(creds: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not ADMIN_API_TOKEN or creds.credentials != ADMIN_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return "admin"
