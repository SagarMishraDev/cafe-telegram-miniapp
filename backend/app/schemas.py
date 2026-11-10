from pydantic import BaseModel, Field
from typing import List, Optional, Any
class CategoryIn(BaseModel):
    name:str; slug:Optional[str]=""; icon:Optional[str]="🍽️"; image_url:Optional[str]=""; sort_order:int=0; is_active:bool=True
class FoodIn(BaseModel):
    category_id:int; name:str; description:str=""; price:float; image_url:str=""; is_veg:bool=True; is_available:bool=True; is_featured:bool=False; is_popular:bool=False; rating:float=4.5; prep_time_mins:int=15; sizes:List[Any]=[]; addons:List[Any]=[]
class CouponIn(BaseModel):
    code:str; type:str="percent"; value:float; min_order:float=0; max_discount:float=0; is_active:bool=True
class TableIn(BaseModel):
    number:str; capacity:int=4; is_active:bool=True
class CouponValidate(BaseModel):
    code:str; subtotal:float
class OrderItemIn(BaseModel):
    food_item_id:int; quantity:int=Field(default=1,ge=1,le=20); size:Optional[str]=""; addons:List[Any]=[]; instructions:Optional[str]=""; price:Optional[float]=None  # ignored, server recalculates
class OrderCreate(BaseModel):
    customer_name:str; phone:str=""; order_type:str="takeaway"; table_number:str=""; instructions:str=""; payment_method:str="cash"; coupon_code:str=""; items:List[OrderItemIn]
class AdminLogin(BaseModel):
    username:str; password:str
class StatusUpdate(BaseModel):
    status:str
class InventoryIn(BaseModel):
    name:str; quantity:float; unit:str="pcs"; low_stock_threshold:float=5
class SettingIn(BaseModel):
    key:str; value:str
class RazorpayOrderIn(BaseModel):
    order_id:int; amount:Optional[float]=None
class RazorpayVerify(BaseModel):
    razorpay_order_id:str; razorpay_payment_id:str; razorpay_signature:str; order_id:int
