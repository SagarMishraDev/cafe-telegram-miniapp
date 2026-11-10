from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..security import verify_init_data, create_token
from ..config import settings
router=APIRouter(prefix="/api/auth",tags=["auth"])
class TgAuth(BaseModel):
    initData: str = ""
@router.post("/telegram")
def telegram_auth(body:TgAuth, db:Session=Depends(get_db)):
    if settings.BOT_TOKEN and body.initData:
        u=verify_init_data(body.initData, settings.BOT_TOKEN)
        if not u: raise HTTPException(401,"Invalid initData")
        tid=str(u.get("id"))
        user=db.query(User).filter(User.telegram_id==tid).first()
        if not user:
            user=User(telegram_id=tid, username=u.get("username",""), first_name=u.get("first_name",""), last_name=u.get("last_name","")); db.add(user); db.commit(); db.refresh(user)
        return {"access_token":create_token(user.id, role="user", extra={"telegram_id":tid,"username":user.username,"first_name":user.first_name}),"user":{"id":user.id,"telegram_id":tid,"first_name":user.first_name,"username":user.username}}
    if settings.DEV_AUTH:
        user=db.query(User).filter(User.telegram_id=="dev-1").first()
        if not user:
            user=User(telegram_id="dev-1", username="dev_guest", first_name="Guest"); db.add(user); db.commit(); db.refresh(user)
        return {"access_token":create_token(user.id, role="dev", extra={"telegram_id":"dev-1","first_name":"Guest"}),"user":{"id":user.id,"telegram_id":"dev-1","first_name":"Guest","username":"dev_guest"},"dev_mode":True}
    raise HTTPException(401,"No auth method available")
