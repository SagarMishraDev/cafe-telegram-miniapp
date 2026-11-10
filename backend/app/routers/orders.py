from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging, uuid
from ..database import get_db
from ..models import Order, OrderItem, Payment, User
from ..schemas import OrderCreate
from ..pricing import calculate_order
from ..deps import get_current_user
router=APIRouter(prefix="/api/orders",tags=["orders"])
STATUSES=["placed","accepted","preparing","ready","completed","cancelled"]
@router.post("")
def create_order(body:OrderCreate, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    if body.order_type=="dine-in" and not body.table_number: raise HTTPException(400,"Table number required for dine-in")
    try: calc=calculate_order(db, body.items, body.coupon_code)
    except ValueError as e: raise HTTPException(400,str(e))
    code="BB"+uuid.uuid4().hex[:8].upper()
    order=Order(order_code=code,user_id=user.id,telegram_id=user.telegram_id,customer_name=body.customer_name,phone=body.phone,order_type=body.order_type,table_number=body.table_number,instructions=body.instructions,payment_method=body.payment_method,payment_status="paid" if body.payment_method in ("cash","upi") else "pending",subtotal=calc["subtotal"],gst_amount=calc["gst_amount"],discount=calc["discount"],total=calc["total"],coupon_code=body.coupon_code.upper() if body.coupon_code else "",eta_mins=25)
    # Cash at counter / pay at cafe are pay-later, mark pending collection but order confirmed
    if body.payment_method in ("cash","cod"): order.payment_status="pay_at_cafe"
    db.add(order); db.flush()
    for line in calc["lines"]:
        db.add(OrderItem(order_id=order.id,food_item_id=line["food"].id,name=line["food"].name,price=line["unit_price"],quantity=line["quantity"],size=line["size"],size_delta=line["size_delta"],addons=line["addons"],instructions=line["instructions"],line_total=line["line_total"]))
    db.add(Payment(order_id=order.id,provider=body.payment_method,txn_ref="TXN-"+uuid.uuid4().hex[:12].upper(),amount=calc["total"],status="pending" if body.payment_method=="razorpay" else "initiated"))
    db.commit(); db.refresh(order)
    # Best-effort staff-group notification — never fails the order.
    try:
        from ..notify import send_group_order
        mid = send_group_order(order)
        if mid:
            order.group_message_id = mid; db.commit()
    except Exception as e:
        logging.warning(f"group notification failed (order placed anyway): {e}")
    return order_dict(order)
def order_dict(o):
    return {"id":o.id,"order_code":o.order_code,"customer_name":o.customer_name,"phone":o.phone,"order_type":o.order_type,"table_number":o.table_number,"instructions":o.instructions,"status":o.status,"payment_method":o.payment_method,"payment_status":o.payment_status,"subtotal":o.subtotal,"gst_amount":o.gst_amount,"discount":o.discount,"total":o.total,"coupon_code":o.coupon_code,"eta_mins":o.eta_mins,"created_at":o.created_at.isoformat() if o.created_at else None,"items":[{"name":i.name,"price":i.price,"quantity":i.quantity,"size":i.size,"addons":i.addons,"line_total":i.line_total} for i in o.items]}
@router.get("/my")
def my_orders(db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    return [order_dict(o) for o in db.query(Order).filter(Order.user_id==user.id).order_by(Order.id.desc()).all()]
@router.get("/{order_id}/track")
def track(order_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    o=db.query(Order).filter(Order.id==order_id).first()
    if not o: raise HTTPException(404,"Order not found")
    return {"order":order_dict(o),"status":o.status,"steps":STATUSES,"current_index":STATUSES.index(o.status) if o.status in STATUSES else 0,"eta_mins":o.eta_mins}
