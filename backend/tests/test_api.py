import os, sys
os.environ["DATABASE_URL"]=""
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# Use isolated test DB
import tempfile
os.environ["DEV_AUTH"]="1"
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Patch DB to sqlite memory file before importing app
import app.database as dbmod
test_engine = create_engine(f"sqlite:///{tempfile.mktemp(suffix='.db')}", connect_args={"check_same_thread": False})
dbmod.engine = test_engine
dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
from app.database import Base
Base.metadata.create_all(bind=test_engine)
from app.seed import seed
# seed uses its own engine - monkey: call seed logic via test session manually by temporarily swapping
import app.seed as seedmod
orig_engine = seedmod.engine
seedmod.engine = test_engine
import app.database as adb
adb_engine_orig = None
seedmod.SessionLocal = dbmod.SessionLocal
seed()

from fastapi.testclient import TestClient
from app.main import app
# Override get_db to use test session
from app.database import get_db
def override_db():
    db = dbmod.SessionLocal()
    try: yield db
    finally: db.close()
app.dependency_overrides[get_db] = override_db
client = TestClient(app)

def test_health():
    r = client.get("/health"); assert r.status_code==200 and r.json()["status"]=="ok"

def test_menu_and_categories():
    cats = client.get("/api/categories").json(); assert len(cats)==11
    menu = client.get("/api/menu").json(); assert len(menu)>=22

def test_initdata_valid_and_tampered():
    from app.security import verify_init_data, make_init_data
    token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    data=make_init_data({"id":999,"first_name":"Test","username":"testuser"}, token)
    u=verify_init_data(data, token); assert u and u["id"]==999
    assert verify_init_data(data+"tamper", token) is None
    assert verify_init_data(data, "wrong:token") is None

def test_price_calc_ignores_client_price_and_coupon_gst():
    menu = client.get("/api/menu").json()
    item = menu[0]
    # Tampered price 1 rupee should be ignored; server uses DB price
    r = client.post("/api/orders", json={"customer_name":"Test","phone":"9999999999","order_type":"takeaway","payment_method":"cash","coupon_code":"WELCOME10","items":[{"food_item_id":item["id"],"quantity":2,"price":1}]})
    assert r.status_code==200, r.text
    o=r.json()
    expected_subtotal=item["price"]*2
    assert o["subtotal"]==expected_subtotal
    expected_discount=min(expected_subtotal*0.10,150)
    taxable=expected_subtotal-expected_discount
    assert abs(o["discount"]-expected_discount)<0.01
    assert abs(o["gst_amount"]-round(taxable*0.05,2))<0.01
    assert abs(o["total"]-round(taxable+o["gst_amount"],2))<0.01

def test_coupon_validate():
    r=client.post("/api/coupons/validate", json={"code":"FIRST50","subtotal":500}); assert r.json()["valid"]==True and r.json()["discount"]==50
    r2=client.post("/api/coupons/validate", json={"code":"FIRST50","subtotal":100}); assert r2.json()["valid"]==False

def test_order_lifecycle_and_admin_auth():
    # admin required
    assert client.get("/api/admin/dashboard").status_code in (401,403)
    login=client.post("/api/admin/login", json={"username":"admin","password":"admin123"}); assert login.status_code==200, login.text
    tok=login.json()["access_token"]; h={"Authorization":f"Bearer {tok}"}
    dash=client.get("/api/admin/dashboard", headers=h); assert dash.status_code==200
    orders=client.get("/api/admin/orders", headers=h).json(); assert len(orders)>=1
    oid=orders[0]["id"]
    for st in ["accepted","preparing","ready","completed"]:
        rr=client.patch(f"/api/admin/orders/{oid}/status", json={"status":st}, headers=h); assert rr.status_code==200 and rr.json()["status"]==st
    bad=client.patch(f"/api/admin/orders/{oid}/status", json={"status":"bogus"}, headers=h); assert bad.status_code==400

def test_dinein_requires_table():
    menu=client.get("/api/menu").json()
    r=client.post("/api/orders", json={"customer_name":"T","order_type":"dine-in","payment_method":"cash","items":[{"food_item_id":menu[0]["id"],"quantity":1}]})
    assert r.status_code==400
