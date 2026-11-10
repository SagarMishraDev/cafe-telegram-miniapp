from sqlalchemy import Column,Integer,String,Float,Boolean,ForeignKey,Text,DateTime,JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
class Category(Base):
    __tablename__="categories"
    id=Column(Integer,primary_key=True); name=Column(String,unique=True,nullable=False); slug=Column(String,unique=True); icon=Column(String,default="🍽️"); image_url=Column(String,default=""); sort_order=Column(Integer,default=0); is_active=Column(Boolean,default=True)
    items=relationship("FoodItem",back_populates="category",cascade="all, delete-orphan")
class FoodItem(Base):
    __tablename__="food_items"
    id=Column(Integer,primary_key=True); category_id=Column(Integer,ForeignKey("categories.id")); name=Column(String,nullable=False); description=Column(Text,default=""); price=Column(Float,nullable=False); image_url=Column(String,default=""); is_veg=Column(Boolean,default=True); is_available=Column(Boolean,default=True); is_featured=Column(Boolean,default=False); is_popular=Column(Boolean,default=False); rating=Column(Float,default=4.5); prep_time_mins=Column(Integer,default=15); sizes=Column(JSON,default=list); addons=Column(JSON,default=list)
    category=relationship("Category",back_populates="items")
class Coupon(Base):
    __tablename__="coupons"
    id=Column(Integer,primary_key=True); code=Column(String,unique=True); type=Column(String,default="percent"); value=Column(Float); min_order=Column(Float,default=0); max_discount=Column(Float,default=0); is_active=Column(Boolean,default=True)
class CafeTable(Base):
    __tablename__="tables"
    id=Column(Integer,primary_key=True); number=Column(String,unique=True); capacity=Column(Integer,default=4); is_active=Column(Boolean,default=True)
class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True); telegram_id=Column(String,unique=True,index=True); username=Column(String,default=""); first_name=Column(String,default=""); last_name=Column(String,default=""); phone=Column(String,default="")
class Order(Base):
    __tablename__="orders"
    id=Column(Integer,primary_key=True); order_code=Column(String,unique=True,index=True); user_id=Column(Integer,ForeignKey("users.id"),nullable=True); telegram_id=Column(String,default=""); customer_name=Column(String); phone=Column(String,default=""); order_type=Column(String,default="takeaway"); table_number=Column(String,default=""); instructions=Column(Text,default=""); status=Column(String,default="placed"); payment_method=Column(String,default="cash"); payment_status=Column(String,default="pending"); subtotal=Column(Float,default=0); gst_amount=Column(Float,default=0); discount=Column(Float,default=0); total=Column(Float,default=0); coupon_code=Column(String,default=""); eta_mins=Column(Integer,default=25); group_message_id=Column(Integer,nullable=True); created_at=Column(DateTime,default=datetime.utcnow)
    items=relationship("OrderItem",back_populates="order",cascade="all, delete-orphan")
    payments=relationship("Payment",back_populates="order")
class OrderItem(Base):
    __tablename__="order_items"
    id=Column(Integer,primary_key=True); order_id=Column(Integer,ForeignKey("orders.id")); food_item_id=Column(Integer); name=Column(String); price=Column(Float); quantity=Column(Integer,default=1); size=Column(String,default=""); size_delta=Column(Float,default=0); addons=Column(JSON,default=list); instructions=Column(Text,default=""); line_total=Column(Float,default=0)
    order=relationship("Order",back_populates="items")
class Payment(Base):
    __tablename__="payments"
    id=Column(Integer,primary_key=True); order_id=Column(Integer,ForeignKey("orders.id")); provider=Column(String,default="cash"); txn_ref=Column(String,unique=True); amount=Column(Float); status=Column(String,default="pending"); provider_order_id=Column(String,default=""); provider_payment_id=Column(String,default=""); created_at=Column(DateTime,default=datetime.utcnow)
    order=relationship("Order",back_populates="payments")
class Setting(Base):
    __tablename__="settings"
    id=Column(Integer,primary_key=True); key=Column(String,unique=True); value=Column(Text,default="")
class AdminUser(Base):
    __tablename__="admin_users"
    id=Column(Integer,primary_key=True); username=Column(String,unique=True); hashed_password=Column(String); role=Column(String,default="admin")
class InventoryItem(Base):
    __tablename__="inventory"
    id=Column(Integer,primary_key=True); name=Column(String,unique=True); quantity=Column(Float,default=0); unit=Column(String,default="pcs"); low_stock_threshold=Column(Float,default=5)
