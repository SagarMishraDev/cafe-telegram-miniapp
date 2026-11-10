export interface SizeOpt { name: string; delta: number }
export interface Addon { name: string; price: number }
export interface Food { id:number; category_id:number; category_name?:string; name:string; description:string; price:number; image_url:string; is_veg:boolean; is_available:boolean; is_featured:boolean; is_popular:boolean; rating:number; prep_time_mins:number; sizes:SizeOpt[]; addons:Addon[] }
export interface Category { id:number; name:string; slug:string; icon:string }
export const CATEGORIES: Category[] = [
 {id:1,name:"Burgers",slug:"burgers",icon:"🍔"},{id:2,name:"Pizza",slug:"pizza",icon:"🍕"},{id:3,name:"Sandwiches",slug:"sandwiches",icon:"🥪"},{id:4,name:"Pasta",slug:"pasta",icon:"🍝"},{id:5,name:"Momos",slug:"momos",icon:"🥟"},{id:6,name:"Snacks",slug:"snacks",icon:"🍟"},{id:7,name:"Coffee",slug:"coffee",icon:"☕"},{id:8,name:"Cold Coffee",slug:"cold-coffee",icon:"🧋"},{id:9,name:"Shakes",slug:"shakes",icon:"🥤"},{id:10,name:"Desserts",slug:"desserts",icon:"🍰"},{id:11,name:"Beverages",slug:"beverages",icon:"🍹"},
]
const U="https://images.unsplash.com/"
const SIZES=[{name:"Small",delta:0},{name:"Medium",delta:40},{name:"Large",delta:80}]
const ADD=[{name:"Extra Cheese",price:40},{name:"Extra Patty",price:70},{name:"Whipped Cream",price:30},{name:"Extra Sauce",price:20},{name:"Jalapenos",price:25}]
const mk=(id:number,cat:number,name:string,price:number,veg:boolean,img:string,desc:string,feat=false,pop=false,rating=4.5,sized=false):Food=>({id,category_id:cat,category_name:CATEGORIES[cat-1]?.name,name,price,is_veg:veg,image_url:U+img,description:desc,is_available:true,is_featured:feat,is_popular:pop,rating,prep_time_mins:15,sizes:sized?SIZES:(cat===1?[{name:"Regular",delta:0},{name:"Large",delta:50}]:[]),addons:ADD})
export const FOODS: Food[]=[
 mk(1,1,"Classic Cheese Burger",199,true,"photo-1568901346375-23c9450c58cd?w=800&q=80","Juicy veg patty, cheddar & house sauce in a toasted brioche bun.",true,true,4.6),
 mk(2,1,"Peri Peri Chicken Burger",249,false,"photo-1553979459-d2229ba7433b?w=800&q=80","Grilled chicken, peri peri mayo, crisp lettuce.",false,true,4.7),
 mk(3,2,"Wood-Fired Margherita",299,true,"photo-1574071318508-1cdbab80d002?w=800&q=80","San Marzano tomato, fresh mozzarella, basil.",true,true,4.8,true),
 mk(4,2,"Pepperoni Blast Pizza",449,false,"photo-1628840042765-356cda07504e?w=800&q=80","Double pepperoni, mozzarella, oregano.",false,false,4.6,true),
 mk(5,3,"Grilled Veg Sandwich",149,true,"photo-1528735602780-2552fd46c7af?w=800&q=80","Triple-layer, mint chutney, crunchy veggies.",false,true,4.4),
 mk(6,3,"Chicken Club Sandwich",199,false,"photo-1550507992-eb63ffee0847?w=800&q=80","Chicken, egg & cheese on toasted sourdough.",true,false,4.5),
 mk(7,4,"Alfredo White Pasta",279,true,"photo-1621996346565-e3dbc646d9a9?w=800&q=80","Creamy alfredo, exotic veggies, parmesan.",true,true,4.7,true),
 mk(8,4,"Arrabbiata Pasta",249,true,"photo-1563379926898-05f4575a45d8?w=800&q=80","Spicy tomato-basil sauce with penne.",false,false,4.4,true),
 mk(9,5,"Steamed Veg Momos",129,true,"photo-1496116218417-1a781b1c416c?w=800&q=80","8 pc steamed momos with spicy chutney.",false,true,4.5),
 mk(10,5,"Tandoori Chicken Momos",189,false,"photo-1534422298391-e4f8c172dddb?w=800&q=80","Charred tandoori momos, mint mayo.",true,false,4.6),
 mk(11,6,"Peri Peri Fries",129,true,"photo-1573080496219-bb080dd4f877?w=800&q=80","Crispy fries dusted with peri peri.",false,true,4.3),
 mk(12,6,"Loaded Nachos",199,true,"photo-1513456852971-30c0b8199d4d?w=800&q=80","Cheese sauce, salsa, jalapeños, beans.",true,false,4.5),
 mk(13,7,"Cappuccino",119,true,"photo-1572442388796-11668a67e53d?w=800&q=80","Double-shot espresso, velvety foam.",false,true,4.7,true),
 mk(14,7,"Cafe Latte",139,true,"photo-1561047029-3000c68339ca?w=800&q=80","Smooth espresso with steamed-milk art.",true,false,4.6,true),
 mk(15,8,"Iced Caramel Cold Coffee",179,true,"photo-1461023058943-07fcbe16d735?w=800&q=80","Cold brew, caramel, vanilla ice cream.",true,true,4.8,true),
 mk(16,8,"Mocha Frappe",189,true,"photo-1578314675249-a6910f80cc4e?w=800&q=80","Chocolate + coffee blended frappe.",false,false,4.6,true),
 mk(17,9,"KitKat Shake",219,true,"photo-1572490122747-3968b75cc699?w=800&q=80","Thick KitKat milkshake, whipped cream.",true,true,4.7,true),
 mk(18,9,"Mango Thick Shake",199,true,"photo-1623065422902-30a2d299bbe4?w=800&q=80","Alphonso mango, creamy thick shake.",false,false,4.5,true),
 mk(19,10,"Choco Lava Cake",99,true,"photo-1606313564200-e75d5e30476c?w=800&q=80","Molten chocolate centre, served warm.",true,true,4.8),
 mk(20,10,"New York Cheesecake",229,true,"photo-1533134242443-d4fd215305ad?w=800&q=80","Baked cheesecake, berry compote.",false,false,4.7),
 mk(21,11,"Virgin Mint Mojito",149,true,"photo-1551538827-9c037cb4f32a?w=800&q=80","Mint, lime & soda — super refreshing.",false,true,4.4,true),
 mk(22,11,"Fresh Orange Cooler",129,true,"photo-1600271886742-f049cd451bba?w=800&q=80","Fresh-pressed orange with mint.",true,false,4.3,true),
]
export const COUPONS=[{code:"WELCOME10",type:"percent",value:10,min_order:0},{code:"FIRST50",type:"flat",value:50,min_order:299}]
export const TABLES=[1,2,3,4,5,6,7,8].map(n=>({id:n,number:String(n),capacity:n%2?4:6}))
export function calcDiscount(code:string, subtotal:number){
  const c=COUPONS.find(x=>x.code===code.toUpperCase()); if(!c||subtotal<c.min_order) return 0
  return c.type==="percent"? Math.min(subtotal*c.value/100,150) : c.value
}
