from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from ..database import get_db
from ..models import Category, FoodItem, Coupon, CafeTable, Order, Payment, Setting, InventoryItem, AdminUser, OrderItem
from ..schemas import *
from ..security import verify_pw, create_token
from ..deps import require_admin
from .orders import order_dict, STATUSES
router=APIRouter(prefix="/api/admin",tags=["admin"])
@router.post("/login")
def login(body:AdminLogin, db:Session=Depends(get_db)):
    u=db.query(AdminUser).filter(AdminUser.username==body.username).first()
    if not u or not verify_pw(body.password, u.hashed_password): raise HTTPException(401,"Invalid credentials")
    return {"access_token":create_token(u.id, role=u.role, extra={"username":u.username}),"role":u.role,"username":u.username}
@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db), admin=Depends(require_admin)):
    total=db.query(Order).count(); today=db.query(Order).filter(func.date(Order.created_at)==date.today()).count()
    rev=db.query(func.coalesce(func.sum(Order.total),0)).filter(Order.status!="cancelled").scalar()
    pending=db.query(Order).filter(Order.status.in_(["placed","accepted","preparing"])).count()
    completed=db.query(Order).filter(Order.status=="completed").count()
    from ..models import OrderItem as OI
    pop=db.query(OI.name, func.sum(OI.quantity).label("qty")).group_by(OI.name).order_by(func.sum(OI.quantity).desc()).limit(5).all()
    recent=[order_dict(o) for o in db.query(Order).order_by(Order.id.desc()).limit(8).all()]
    txns=[{"id":p.id,"txn_ref":p.txn_ref,"amount":p.amount,"status":p.status,"provider":p.provider} for p in db.query(Payment).order_by(Payment.id.desc()).limit(8).all()]
    return {"total_orders":total,"today_orders":today,"total_revenue":float(rev),"pending_orders":pending,"completed_orders":completed,"popular_items":[{"name":n,"qty":int(q)} for n,q in pop],"recent_orders":recent,"recent_transactions":txns}
@router.get("/orders")
def all_orders(db:Session=Depends(get_db), admin=Depends(require_admin)):
    return [order_dict(o) for o in db.query(Order).order_by(Order.id.desc()).all()]
@router.patch("/orders/{oid}/status")
def update_status(oid:int, body:StatusUpdate, db:Session=Depends(get_db), admin=Depends(require_admin)):
    if body.status not in STATUSES: raise HTTPException(400,"Invalid status")
    o=db.query(Order).filter(Order.id==oid).first()
    if not o: raise HTTPException(404,"Not found")
    o.status=body.status; db.commit()
    # Best-effort: keep the staff-group message in sync with the dashboard.
    try:
        from ..notify import edit_group_order
        edit_group_order(o, updated_by="Admin Dashboard")
    except Exception as e:
        import logging; logging.warning(f"group sync failed: {e}")
    return order_dict(o)
# Categories CRUD
@router.post("/categories")
def create_cat(body:CategoryIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    c=Category(**body.dict()); db.add(c); db.commit(); db.refresh(c); return {"id":c.id,"name":c.name}
@router.put("/categories/{cid}")
def upd_cat(cid:int, body:CategoryIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    c=db.query(Category).filter(Category.id==cid).first()
    if not c: raise HTTPException(404,"Not found")
    for k,v in body.dict().items(): setattr(c,k,v)
    db.commit(); return {"ok":True}
@router.delete("/categories/{cid}")
def del_cat(cid:int, db:Session=Depends(get_db), admin=Depends(require_admin)):
    c=db.query(Category).filter(Category.id==cid).first()
    if c: db.delete(c); db.commit()
    return {"ok":True}
# Food CRUD
@router.post("/items")
def create_item(body:FoodIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    f=FoodItem(**body.dict()); db.add(f); db.commit(); db.refresh(f); return {"id":f.id}
@router.put("/items/{fid}")
def upd_item(fid:int, body:FoodIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    f=db.query(FoodItem).filter(FoodItem.id==fid).first()
    if not f: raise HTTPException(404,"Not found")
    for k,v in body.dict().items(): setattr(f,k,v)
    db.commit(); return {"ok":True}
@router.delete("/items/{fid}")
def del_item(fid:int, db:Session=Depends(get_db), admin=Depends(require_admin)):
    f=db.query(FoodItem).filter(FoodItem.id==fid).first()
    if f: db.delete(f); db.commit()
    return {"ok":True}
@router.patch("/items/{fid}/availability")
def toggle_item(fid:int, db:Session=Depends(get_db), admin=Depends(require_admin)):
    f=db.query(FoodItem).filter(FoodItem.id==fid).first()
    if not f: raise HTTPException(404,"Not found")
    f.is_available=not f.is_available; db.commit(); return {"id":f.id,"is_available":f.is_available}
# Coupons
@router.get("/coupons")
def list_coupons(db:Session=Depends(get_db), admin=Depends(require_admin)):
    return [{"id":c.id,"code":c.code,"type":c.type,"value":c.value,"min_order":c.min_order,"is_active":c.is_active} for c in db.query(Coupon).all()]
@router.post("/coupons")
def create_coupon(body:CouponIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    c=Coupon(**body.dict()); db.add(c); db.commit(); return {"id":c.id}
@router.delete("/coupons/{cid}")
def del_coupon(cid:int, db:Session=Depends(get_db), admin=Depends(require_admin)):
    c=db.query(Coupon).filter(Coupon.id==cid).first()
    if c: db.delete(c); db.commit()
    return {"ok":True}
# Tables
@router.get("/tables")
def list_tables(db:Session=Depends(get_db), admin=Depends(require_admin)):
    return [{"id":t.id,"number":t.number,"capacity":t.capacity} for t in db.query(CafeTable).all()]
@router.post("/tables")
def create_table(body:TableIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    t=CafeTable(**body.dict()); db.add(t); db.commit(); return {"id":t.id}
@router.delete("/tables/{tid}")
def del_table(tid:int, db:Session=Depends(get_db), admin=Depends(require_admin)):
    t=db.query(CafeTable).filter(CafeTable.id==tid).first()
    if t: db.delete(t); db.commit()
    return {"ok":True}
# Settings
@router.get("/settings")
def get_settings(db:Session=Depends(get_db), admin=Depends(require_admin)):
    return {s.key:s.value for s in db.query(Setting).all()}
@router.post("/settings")
def set_setting(body:SettingIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    s=db.query(Setting).filter(Setting.key==body.key).first()
    if s: s.value=body.value
    else: db.add(Setting(key=body.key,value=body.value))
    db.commit(); return {"ok":True}
# Inventory
@router.get("/inventory")
def inventory(db:Session=Depends(get_db), admin=Depends(require_admin)):
    return [{"id":i.id,"name":i.name,"quantity":i.quantity,"unit":i.unit,"low_stock_threshold":i.low_stock_threshold} for i in db.query(InventoryItem).all()]
@router.post("/inventory")
def add_inv(body:InventoryIn, db:Session=Depends(get_db), admin=Depends(require_admin)):
    ex=db.query(InventoryItem).filter(InventoryItem.name==body.name).first()
    if ex:
        ex.quantity=body.quantity; ex.unit=body.unit
    else: db.add(InventoryItem(**body.dict()))
    db.commit(); return {"ok":True}
# Reports
@router.get("/reports/sales")
def sales(db:Session=Depends(get_db), admin=Depends(require_admin)):
    rows=db.query(func.date(Order.created_at).label("day"), func.count(Order.id), func.coalesce(func.sum(Order.total),0)).filter(Order.status!="cancelled").group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at).desc()).limit(30).all()
    return [{"date":str(d),"orders":int(c),"revenue":float(r)} for d,c,r in rows]
