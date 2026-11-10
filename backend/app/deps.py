from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_token, verify_init_data
from .config import settings
def get_current_user(authorization: str = Header(default=""), x_init_data: str = Header(default=""), db: Session = Depends(get_db)):
    # Try Telegram initData first
    if x_init_data and settings.BOT_TOKEN:
        u=verify_init_data(x_init_data, settings.BOT_TOKEN)
        if u:
            tid=str(u.get("id"))
            user=db.query(User).filter(User.telegram_id==tid).first()
            if not user:
                user=User(telegram_id=tid, username=u.get("username",""), first_name=u.get("first_name",""), last_name=u.get("last_name","")); db.add(user); db.commit(); db.refresh(user)
            return user
        raise HTTPException(401,"Invalid Telegram initData")
    # JWT
    if authorization.startswith("Bearer "):
        data=decode_token(authorization[7:])
        if data and data.get("role") in ("user","dev"):
            tid=data.get("telegram_id","dev-1")
            user=db.query(User).filter(User.telegram_id==str(tid)).first()
            if not user:
                user=User(telegram_id=str(tid), username=data.get("username","dev"), first_name=data.get("first_name","Dev")); db.add(user); db.commit(); db.refresh(user)
            return user
    # Dev fallback
    if settings.DEV_AUTH:
        user=db.query(User).filter(User.telegram_id=="dev-1").first()
        if not user:
            user=User(telegram_id="dev-1", username="dev_guest", first_name="Guest"); db.add(user); db.commit(); db.refresh(user)
        return user
    raise HTTPException(401,"Authentication required")
def require_admin(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "): raise HTTPException(401,"Admin login required")
    data=decode_token(authorization[7:])
    if not data or data.get("role") not in ("admin","manager","staff"): raise HTTPException(403,"Admin access required")
    return data
