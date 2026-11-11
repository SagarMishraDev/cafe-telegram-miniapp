from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_token, verify_init_data
from .config import settings
from .users import get_or_create_user
def get_current_user(authorization: str = Header(default=""), x_init_data: str = Header(default=""), db: Session = Depends(get_db)):
    # Try Telegram initData first
    if x_init_data and settings.BOT_TOKEN:
        u=verify_init_data(x_init_data, settings.BOT_TOKEN)
        if u:
            return get_or_create_user(db, u.get("id"), username=u.get("username",""), first_name=u.get("first_name",""), last_name=u.get("last_name",""))
        raise HTTPException(401,"Invalid Telegram initData")
    # JWT
    if authorization.startswith("Bearer "):
        data=decode_token(authorization[7:])
        if data and data.get("role") in ("user","dev"):
            tid=data.get("telegram_id","dev-1")
            return get_or_create_user(db, tid, username=data.get("username","dev"), first_name=data.get("first_name","Dev"))
    # Dev fallback
    if settings.DEV_AUTH:
        return get_or_create_user(db, "dev-1", username="dev_guest", first_name="Guest")
    raise HTTPException(401,"Authentication required")
def require_admin(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Admin login required")
    data=decode_token(authorization[7:])
    if not data or data.get("role") not in ("admin","manager","staff"): raise HTTPException(403,"Admin access required")
    return data
