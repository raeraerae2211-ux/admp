from fastapi.middleware.cors import CORSMiddleware
from app.admin_api.router import router as admin_router

app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",             # дев
        "https://<project>.web.app",         # firebase
        "https://<project>.firebaseapp.com"  # firebase
    ],
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["Content-Type","X-Tg-Init-Data"],
)

@app.get("/healthz")
def healthz(): return {"ok": True}