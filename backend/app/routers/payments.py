from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import hashlib, hmac, uuid
from ..database import get_db
from ..models import Order, Payment
from ..schemas import RazorpayOrderIn, RazorpayVerify
from ..config import settings
router=APIRouter(prefix="/api/payments",tags=["payments"])
@router.post("/razorpay/order")
def rzp_order(body:RazorpayOrderIn, db:Session=Depends(get_db)):
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return {"configured":False,"message":"Razorpay not configured on server. Use Cash / Pay at Cafe or UPI at counter.","order_id":body.order_id}
    o=db.query(Order).filter(Order.id==body.order_id).first()
    if not o: raise HTTPException(404,"Order not found")
    # In production, call Razorpay API here to create order; we return payload for checkout.js
    return {"configured":True,"key_id":settings.RAZORPAY_KEY_ID,"amount":int(o.total*100),"currency":"INR","razorpay_order_id":"order_"+uuid.uuid4().hex[:14],"order_id":o.id}
@router.post("/razorpay/verify")
def rzp_verify(body:RazorpayVerify, db:Session=Depends(get_db)):
    if not settings.RAZORPAY_KEY_SECRET: raise HTTPException(400,"Razorpay not configured")
    msg=f"{body.razorpay_order_id}|{body.razorpay_payment_id}"
    sig=hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, body.razorpay_signature): raise HTTPException(400,"Payment verification failed")
    o=db.query(Order).filter(Order.id==body.order_id).first()
    if o: o.payment_status="paid"
    p=db.query(Payment).filter(Payment.order_id==body.order_id).first()
    if p: p.status="paid"; p.provider_payment_id=body.razorpay_payment_id; p.provider_order_id=body.razorpay_order_id
    db.commit()
    return {"verified":True,"order_id":body.order_id}
@router.post("/razorpay/webhook")
async def webhook(request:Request, db:Session=Depends(get_db)):
    payload=await request.body()
    return {"received":True}
