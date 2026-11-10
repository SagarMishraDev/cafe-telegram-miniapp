from .models import FoodItem, Coupon, Setting
def get_gst(db):
    s=db.query(Setting).filter(Setting.key=="gst_percent").first()
    return float(s.value) if s else 5.0
def calc_discount(db, code, subtotal):
    if not code: return 0.0, None
    c=db.query(Coupon).filter(Coupon.code==code.upper(), Coupon.is_active==True).first()
    if not c or subtotal < c.min_order: return 0.0, None
    if c.type=="percent":
        d=subtotal*c.value/100
        if c.max_discount: d=min(d,c.max_discount)
    else: d=c.value
    return round(min(d, subtotal),2), c
def calculate_order(db, items_in, coupon_code=""):
    """Server-side recalculation. Ignores client prices completely."""
    subtotal=0.0; lines=[]
    for it in items_in:
        food=db.query(FoodItem).filter(FoodItem.id==it.food_item_id).first()
        if not food: raise ValueError(f"Item {it.food_item_id} not found")
        if not food.is_available: raise ValueError(f"{food.name} is unavailable")
        size_delta=0.0; size_name=it.size or ""
        for s in (food.sizes or []):
            if s.get("name")==size_name: size_delta=float(s.get("delta",0))
        addon_total=0.0; addon_snapshot=[]
        # addons can be [{name,price}] from client or [name strings] — price always from DB config
        db_addons={a.get("name"): float(a.get("price",0)) for a in (food.addons or [])}
        for a in (it.addons or []):
            aname=a.get("name") if isinstance(a,dict) else str(a)
            if aname in db_addons:
                addon_total+=db_addons[aname]; addon_snapshot.append({"name":aname,"price":db_addons[aname]})
        unit=food.price+size_delta+addon_total
        line=unit*it.quantity; subtotal+=line
        lines.append({"food":food,"quantity":it.quantity,"size":size_name,"size_delta":size_delta,"addons":addon_snapshot,"unit_price":food.price,"line_total":round(line,2),"instructions":it.instructions or ""})
    discount,_=calc_discount(db, coupon_code, subtotal)
    taxable=subtotal-discount
    gst_pct=get_gst(db); gst=round(taxable*gst_pct/100,2)
    total=round(taxable+gst,2)
    return {"subtotal":round(subtotal,2),"discount":discount,"gst_percent":gst_pct,"gst_amount":gst,"total":total,"lines":lines}
