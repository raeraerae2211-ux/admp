
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Admin API", version="1.0")

ALLOWED = os.getenv("ADMIN_ALLOWED_ORIGINS", "").split(",")
ALLOWED = [o.strip() for o in ALLOWED if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED or ["http://localhost:5173"],
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["Content-Type","X-Tg-Init-Data"],
)

from app.admin_api.router import router as admin_router  # noqa: E402
app.include_router(admin_router, prefix="")

@app.get("/healthz")
def healthz():
    return {"ok": True}
