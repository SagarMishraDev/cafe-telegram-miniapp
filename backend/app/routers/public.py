from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Category, FoodItem, CafeTable, Setting, Coupon
from ..pricing import calc_discount
from ..schemas import CouponValidate
router=APIRouter(prefix="/api",tags=["public"])
def food_dict(f):
    return {"id":f.id,"category_id":f.category_id,"category_name":f.category.name if f.category else "","name":f.name,"description":f.description,"price":f.price,"image_url":f.image_url,"is_veg":f.is_veg,"is_available":f.is_available,"is_featured":f.is_featured,"is_popular":f.is_popular,"rating":f.rating,"prep_time_mins":f.prep_time_mins,"sizes":f.sizes or [],"addons":f.addons or []}
@router.get("/categories")
def categories(db:Session=Depends(get_db)):
    return [{"id":c.id,"name":c.name,"slug":c.slug,"icon":c.icon,"image_url":c.image_url} for c in db.query(Category).filter(Category.is_active==True).order_by(Category.sort_order).all()]
@router.get("/menu")
def menu(search:str="", category_id:int=0, veg_only:bool=False, db:Session=Depends(get_db)):
    q=db.query(FoodItem)
    if category_id: q=q.filter(FoodItem.category_id==category_id)
    if veg_only: q=q.filter(FoodItem.is_veg==True)
    if search: q=q.filter(FoodItem.name.ilike(f"%{search}%"))
    return [food_dict(f) for f in q.all()]
@router.get("/menu/{item_id}")
def menu_detail(item_id:int, db:Session=Depends(get_db)):
    from fastapi import HTTPException
    f=db.query(FoodItem).filter(FoodItem.id==item_id).first()
    if not f: raise HTTPException(404,"Item not found")
    return food_dict(f)
@router.get("/tables")
def tables(db:Session=Depends(get_db)):
    return [{"id":t.id,"number":t.number,"capacity":t.capacity} for t in db.query(CafeTable).filter(CafeTable.is_active==True).all()]
@router.get("/settings")
def public_settings(db:Session=Depends(get_db)):
    return {s.key:s.value for s in db.query(Setting).all()}
@router.get("/coupons")
def coupons(db:Session=Depends(get_db)):
    return [{"code":c.code,"type":c.type,"value":c.value,"min_order":c.min_order} for c in db.query(Coupon).filter(Coupon.is_active==True).all()]
@router.post("/coupons/validate")
def validate_coupon(body:CouponValidate, db:Session=Depends(get_db)):
    d,c=calc_discount(db, body.code, body.subtotal)
    if not c: return {"valid":False,"discount":0,"message":"Coupon not valid for this amount"}
    return {"valid":True,"discount":d,"code":c.code,"message":f"Saved ₹{d}"}
