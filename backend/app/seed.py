from .database import SessionLocal, Base, engine
from .models import *
from .security import hash_pw
from .config import settings
UNS="https://images.unsplash.com/"
CATS=[
 ("Burgers","burgers","🍔"),("Pizza","pizza","🍕"),("Sandwiches","sandwiches","🥪"),("Pasta","pasta","🍝"),("Momos","momos","🥟"),("Snacks","snacks","🍟"),("Coffee","coffee","☕"),("Cold Coffee","cold-coffee","🧋"),("Shakes","shakes","🥤"),("Desserts","desserts","🍰"),("Beverages","beverages","🥤"),
]
# name, cat_slug, price, veg, img, desc, featured, popular, rating
ITEMS=[
 ("Classic Cheese Burger","burgers",199,True,"photo-1568901346375-23c9450c58cd?w=800&q=80","Juicy veg patty, cheddar, house sauce in brioche bun",True,True,4.6),
 ("Peri Peri Chicken Burger","burgers",249,False,"photo-1553979459-d2229ba7433b?w=800&q=80","Grilled chicken, peri peri mayo, lettuce",False,True,4.7),
 ("Wood-Fired Margherita","pizza",299,True,"photo-1574071318508-1cdbab80d002?w=800&q=80","San Marzano tomato, fresh mozzarella, basil",True,True,4.8),
 ("Pepperoni Blast Pizza","pizza",449,False,"photo-1628840042765-356cda07504e?w=800&q=80","Double pepperoni, mozzarella, oregano",False,False,4.6),
 ("Grilled Veg Sandwich","sandwiches",149,True,"photo-1528735602780-2552fd46c7af?w=800&q=80","Triple-layer, mint chutney, crunchy veggies",False,True,4.4),
 ("Chicken Club Sandwich","sandwiches",199,False,"photo-1550507992-eb63ffee0847?w=800&q=80","Chicken, egg, cheese, toasted sourdough",True,False,4.5),
 ("Alfredo White Pasta","pasta",279,True,"photo-1621996346565-e3dbc646d9a9?w=800&q=80","Creamy alfredo, exotic veggies, parmesan",True,True,4.7),
 ("Arrabbiata Pasta","pasta",249,True,"photo-1563379926898-05f4575a45d8?w=800&q=80","Spicy tomato basil sauce, penne",False,False,4.4),
 ("Steamed Veg Momos","momos",129,True,"photo-1496116218417-1a781b1c416c?w=800&q=80","8 pc steamed momos, spicy chutney",False,True,4.5),
 ("Tandoori Chicken Momos","momos",189,False,"photo-1534422298391-e4f8c172dddb?w=800&q=80","Charred tandoori momos, mint mayo",True,False,4.6),
 ("Peri Peri Fries","snacks",129,True,"photo-1573080496219-bb080dd4f877?w=800&q=80","Crispy fries, peri peri dust",False,True,4.3),
 ("Loaded Nachos","snacks",199,True,"photo-1513456852971-30c0b8199d4d?w=800&q=80","Cheese sauce, salsa, jalapenos, beans",True,False,4.5),
 ("Cappuccino","coffee",119,True,"photo-1572442388796-11668a67e53d?w=800&q=80","Double shot espresso, velvety foam",False,True,4.7),
 ("Cafe Latte","coffee",139,True,"photo-1561047029-3000c68339ca?w=800&q=80","Smooth espresso with steamed milk art",True,False,4.6),
 ("Iced Caramel Cold Coffee","cold-coffee",179,True,"photo-1461023058943-07fcbe16d735?w=800&q=80","Cold brew, caramel, vanilla ice cream",True,True,4.8),
 ("Mocha Frappe","cold-coffee",189,True,"photo-1578314675249-a6910f80cc4e?w=800&q=80","Chocolate + coffee blended frappe",False,False,4.6),
 ("KitKat Shake","shakes",219,True,"photo-1572490122747-3968b75cc699?w=800&q=80","Thick KitKat milkshake, whipped cream",True,True,4.7),
 ("Mango Thick Shake","shakes",199,True,"photo-1623065422902-30a2d299bbe4?w=800&q=80","Alphonso mango, creamy thick shake",False,False,4.5),
 ("Choco Lava Cake","desserts",99,True,"photo-1606313564200-e75d5e30476c?w=800&q=80","Molten chocolate centre, warm cake",True,True,4.8),
 ("New York Cheesecake","desserts",229,True,"photo-1533134242443-d4fd215305ad?w=800&q=80","Baked cheesecake, berry compote",False,False,4.7),
 ("Virgin Mint Mojito","beverages",149,True,"photo-1551538827-9c037cb4f32a?w=800&q=80","Mint, lime, soda — super refreshing",False,True,4.4),
 ("Fresh Orange Cooler","beverages",129,True,"photo-1600271886742-f049cd451bba?w=800&q=80","Fresh pressed orange, mint",True,False,4.3),
]
SIZES=[{"name":"Small","delta":0},{"name":"Medium","delta":40},{"name":"Large","delta":80}]
ADDONS=[{"name":"Extra Cheese","price":40},{"name":"Extra Patty","price":70},{"name":"Whipped Cream","price":30},{"name":"Extra Sauce","price":20},{"name":"Jalapenos","price":25}]
def seed():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        if db.query(Category).count()>0:
            return
        cat_map={}
        for i,(n,s,ic) in enumerate(CATS):
            c=Category(name=n,slug=s,icon=ic,sort_order=i); db.add(c); db.flush(); cat_map[s]=c.id
        for name,slug,price,veg,img,desc,feat,pop,rating in ITEMS:
            sizes=SIZES if slug in ("pizza","coffee","cold-coffee","shakes","pasta","beverages") else ([{"name":"Regular","delta":0},{"name":"Large","delta":50}] if slug=="burgers" else [])
            addons=ADDONS if slug in ("burgers","pizza","sandwiches","shakes","cold-coffee","desserts") else ADDONS[:2]
            db.add(FoodItem(category_id=cat_map[slug],name=name,description=desc,price=price,is_veg=veg,image_url=UNS+img,is_featured=feat,is_popular=pop,rating=rating,sizes=sizes,addons=addons))
        db.add_all([Coupon(code="WELCOME10",type="percent",value=10,min_order=0,max_discount=150),Coupon(code="FIRST50",type="flat",value=50,min_order=299)])
        for i in range(1,9): db.add(CafeTable(number=str(i),capacity=4 if i%2 else 6))
        defaults={"gst_percent":"5","cafe_name":"Brew & Bite Cafe","cafe_tagline":"Good vibes, great bites — served fresh in Jaipur","cafe_phone":"+91 98765 43210","cafe_address":"MG Road, Jaipur","business_hours":"9:00 AM – 11:00 PM","is_open":"true"}
        for k,v in defaults.items(): db.add(Setting(key=k,value=v))
        db.add(AdminUser(username=settings.ADMIN_USERNAME,hashed_password=hash_pw(settings.ADMIN_PASSWORD),role="admin"))
        for n,q,u in [("Coffee Beans",18,"kg"),("Milk",42,"litre"),("Burger Buns",120,"pcs"),("Cheese Slices",200,"pcs"),("Potatoes",35,"kg")]:
            db.add(InventoryItem(name=n,quantity=q,unit=u))
        db.commit()
    finally: db.close()
