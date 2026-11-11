from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time, logging
from collections import defaultdict
from .config import settings
from .database import Base, engine
from .seed import seed
from .routers import public, orders, admin, payments, auth
logging.basicConfig(level=logging.INFO)
app=FastAPI(title="Brew & Bite Cafe — Telegram Mini App API", version="1.0.0")
origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
# Simple rate limit: 60 req/min per IP on orders/auth
_hits=defaultdict(list)
@app.middleware("http")
async def rate_limit(request:Request, call_next):
    if request.url.path.startswith("/api/orders") or request.url.path.startswith("/api/auth"):
        ip=request.client.host if request.client else "unknown"; now=time.time()
        _hits[ip]=[t for t in _hits[ip] if now-t<60]
        if len(_hits[ip])>=60: return JSONResponse({"detail":"Too many requests, please slow down"}, status_code=429)
        _hits[ip].append(now)
    return await call_next(request)
def _ensure_columns():
    """Tiny forward-migration for pre-existing local DBs (create_all does
    not add columns to tables that already exist)."""
    try:
        from sqlalchemy import inspect, text
        insp = inspect(engine)
        if "orders" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("orders")]
            if "group_message_id" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE orders ADD COLUMN group_message_id INTEGER"))
                logging.info("migrated: orders.group_message_id added")
    except Exception as e:
        logging.warning(f"column check: {e}")
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    # Config visibility for the staff-group notification feature — booleans
    # only, never the token value or the chat-id digits.
    logging.info(
        "notify config: BOT_TOKEN set=%s, GROUP_CHAT_ID set=%s",
        "YES" if settings.BOT_TOKEN else "NO",
        "YES" if (settings.GROUP_CHAT_ID or "").strip() else "NO",
    )
    try: seed()
    except Exception as e: logging.warning(f"seed: {e}")
@app.get("/health")
def health(): return {"status":"ok","cafe":"Brew & Bite Cafe"}
app.include_router(public.router); app.include_router(auth.router); app.include_router(orders.router); app.include_router(payments.router); app.include_router(admin.router)
